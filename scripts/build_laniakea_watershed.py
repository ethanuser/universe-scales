#!/usr/bin/env python3
"""Build a native-scale surface from the author-provided ungrouped CF4 grid."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
from scipy.ndimage import label
from skimage.measure import marching_cubes

from fetch_model_assets import inspect_glb, pack_glb
from geo_glb_common import GLB

MEMBER = "CF4_new_128-z008_BoA.fits"
SOURCE = "https://projets.ip2i.in2p3.fr/cosmicflows/"
PAPER = "https://doi.org/10.1051/0004-6361/202346802"
H0 = 74.6
H = H0 / 100
GRID_MPC_H = 1000.0
GRID_SIZE = 128
PAPER_VOLUME_MPC_H3 = 1.9e6
DEFAULT_ARCHIVE = Path("/private/tmp/laniakea-watersheds.zip")
DEFAULT_OUTPUT = Path("/private/tmp/laniakea-scientific/laniakea-cf4-watershed.glb")
DEFAULT_ENTRY = Path("/private/tmp/laniakea-scientific/laniakea-cf4-watershed.json")


def read_primary_fits(data):
    """Read the archive's simple 3D big-endian float64 primary image HDU."""
    card_size = 80
    block_size = 2880
    header = {}
    header_bytes = 0
    found_end = False
    while header_bytes < len(data) and not found_end:
        block = data[header_bytes:header_bytes + block_size]
        if len(block) != block_size:
            raise ValueError("Truncated FITS header block")
        for offset in range(0, block_size, card_size):
            card = block[offset:offset + card_size].decode("ascii")
            key = card[:8].strip()
            if key == "END":
                found_end = True
                break
            if key and card[8:10] == "= ":
                raw = card[10:80].split("/", 1)[0].strip()
                if raw.startswith("'"):
                    value = raw.strip().strip("'").strip()
                elif raw in {"T", "F"}:
                    value = raw == "T"
                else:
                    try:
                        value = int(raw)
                    except ValueError:
                        value = float(raw)
                header[key] = value
        header_bytes += block_size
    if not found_end:
        raise ValueError("FITS primary header has no END card")
    if header.get("SIMPLE") is not True or header.get("BITPIX") != -64 or header.get("NAXIS") != 3:
        raise ValueError("Expected a 3D, SIMPLE, float64 primary FITS image")
    axes = tuple(int(header[f"NAXIS{i}"]) for i in range(1, 4))
    count = int(np.prod(axes))
    payload_size = count * 8
    end = header_bytes + payload_size
    padded_end = header_bytes + ((payload_size + block_size - 1) // block_size) * block_size
    if len(data) != padded_end:
        raise ValueError("FITS payload length does not match its declared dimensions")
    if any(data[end:padded_end]):
        raise ValueError("Nonzero bytes found in FITS block padding")
    array = np.frombuffer(data, dtype=">f8", count=count, offset=header_bytes).reshape(tuple(reversed(axes)))
    if not np.isfinite(array).all():
        raise ValueError("FITS image contains non-finite values")
    return array, header, header_bytes


def component_surface(mask, spacing_mpc):
    """Extract separate closed surfaces for face-connected voxel components."""
    structure = np.zeros((3, 3, 3), dtype=bool)
    structure[1, 1, 1] = True
    structure[0, 1, 1] = structure[2, 1, 1] = True
    structure[1, 0, 1] = structure[1, 2, 1] = True
    structure[1, 1, 0] = structure[1, 1, 2] = True
    components, component_count = label(mask, structure=structure)
    if component_count == 0:
        raise ValueError("Watershed mask is empty")

    vertices, faces = [], []
    vertex_offset = 0
    domain_center = (np.asarray(mask.shape, dtype=float) - 1) / 2
    for component_id in range(1, component_count + 1):
        occupied = np.argwhere(components == component_id)
        low, high = occupied.min(axis=0), occupied.max(axis=0) + 1
        crop = components[tuple(slice(a, b) for a, b in zip(low, high))] == component_id
        verts_zyx, tris, _, _ = marching_cubes(
            np.pad(crop.astype(np.uint8), 1), 0.5, method="lewiner", allow_degenerate=False,
        )
        # FITS array order is z,y,x. The output axes are intentionally native and unlabeled.
        verts_xyz = (verts_zyx[:, ::-1] + low[::-1] - 1 - domain_center[::-1]) * spacing_mpc
        signed_volume = np.einsum(
            "ij,ij->i", verts_xyz[tris[:, 0]],
            np.cross(verts_xyz[tris[:, 1]], verts_xyz[tris[:, 2]]),
        ).sum() / 6
        if abs(signed_volume) < 1e-12:
            raise ValueError(f"Component {component_id} has a degenerate zero-volume surface")
        if signed_volume < 0:
            tris = tris[:, [0, 2, 1]]
        vertices.append(verts_xyz.astype(np.float32))
        faces.append(tris.astype(np.uint32) + vertex_offset)
        vertex_offset += len(verts_xyz)

    return np.concatenate(vertices), np.concatenate(faces), component_count


def vertex_normals(vertices, faces):
    normals = np.zeros_like(vertices, dtype=np.float64)
    face_normals = np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]],
                            vertices[faces[:, 2]] - vertices[faces[:, 0]])
    for corner in range(3):
        np.add.at(normals, faces[:, corner], face_normals)
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    if np.any(lengths == 0):
        raise ValueError("Surface contains vertices without a defined outward normal")
    return (normals / lengths).astype(np.float32)


def build_glb(vertices, faces):
    normals = vertex_normals(vertices, faces)
    glb = GLB("Cosmicflows-4 Laniakea watershed surface")
    material = glb.material("CF4 velocity-basin boundary", color=(0.35, 0.68, 0.86, 0.24),
                            rough=0.8, blend=True, double_sided=True)
    indices = faces.reshape(-1)
    glb.mesh_node("Ungrouped CF4 Laniakea voxel-boundary isosurface", [
        glb.primitive(vertices, indices, material, normals=normals)
    ])
    return pack_glb(glb.doc, bytes(glb.bin))


def create_model(archive_bytes):
    with zipfile.ZipFile(__import__("io").BytesIO(archive_bytes)) as archive:
        try:
            fits_bytes = archive.read(MEMBER)
        except KeyError as error:
            raise ValueError(f"Archive is missing {MEMBER}") from error
    data, header, header_bytes = read_primary_fits(fits_bytes)
    if data.shape != (GRID_SIZE,) * 3:
        raise ValueError(f"Expected {GRID_SIZE}^3 grid; found {data.shape}")
    if not np.equal(data, np.rint(data)).all():
        raise ValueError("Watershed labels must be integer-valued")
    mask = data == 1
    voxel_count = int(mask.sum())
    if voxel_count == 0:
        raise ValueError("CF4 label 1 (Laniakea) is absent")

    spacing_mpc_h = GRID_MPC_H / GRID_SIZE
    spacing_mpc = spacing_mpc_h / H
    vertices, faces, component_count = component_surface(mask, spacing_mpc)
    extents = vertices.max(axis=0) - vertices.min(axis=0)
    reference_extent = float(extents.max())
    glb_bytes = build_glb(vertices, faces)
    stats = inspect_glb(glb_bytes)
    if len(glb_bytes) > 1_500_000 or stats["triangle_count"] > 60_000:
        raise ValueError("Generated model exceeds the 1.5 MB / 60,000 triangle budget")
    source_stats = {
        "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "fits_member": MEMBER,
        "fits_sha256": hashlib.sha256(fits_bytes).hexdigest(),
        "fits_header_bytes": header_bytes,
        "fits_bitpix": header["BITPIX"],
        "fits_shape_zyx": list(data.shape),
        "watershed_label": 1,
        "watershed_voxel_count": voxel_count,
        "face_connected_components": component_count,
    }
    voxel_volume_mpc_h3 = voxel_count * spacing_mpc_h ** 3
    metadata = {
        "id": "laniakea-cf4-ungrouped-watershed",
        "representation": "velocity_watershed_isosurface",
        "production_registry_eligible": False,
        "redistribution_status": "not stated for this author-provided grid; confirm before production use",
        "source": SOURCE,
        "link_label": "Cosmicflows-4 watershed data",
        "basis_url": PAPER,
        "basis_label": "Dupuy & Courtois 2023 CF4 watershed reconstruction",
        "author": "Cosmicflows-4 watershed grid by the Cosmicflows authors; mesh derived by Universe Scales",
        "license": "Author-provided grid; site requests citation to Dupuy & Courtois (2023); separate redistribution terms not stated",
        "note": "This translucent surface is the label-1 Laniakea velocity watershed from the ungrouped Cosmicflows-4 CF4 reconstruction. It is a boundary in a reconstructed velocity field, not a solid mass, gravitationally bound object, or catalog of member galaxies. The grouped CF4 product merges Laniakea into Shapley. Native voxel axes are shown without SGX/SGY/SGZ orientation claims because the grid header provides no WCS. The 2023 paper reports an approximate 1.9e6 (Mpc h^-1)^3 segmented volume; the occupied-voxel estimate is recorded in provenance and need not match the paper's integration exactly. Redistribution terms for the grid are not stated on its source page; this staged asset is not approved for production until rights are confirmed.",
        "presentation": {
            "measure_axis": "longest",
            "reference_size": reference_extent,
            "reference_unit": "Mpc",
            "axis_extents_mpc_native_xyz": extents.astype(float).tolist(),
        },
        "processing": {
            **source_stats,
            "grid_extent_mpc_h": GRID_MPC_H,
            "H0_km_s_Mpc": H0,
            "h": H,
            "voxel_spacing_mpc_h": spacing_mpc_h,
            "voxel_spacing_mpc": spacing_mpc,
            "voxel_volume_mpc_h3": voxel_volume_mpc_h3,
            "paper_segmented_volume_mpc_h3_approx": PAPER_VOLUME_MPC_H3,
            "relative_volume_difference_from_paper": voxel_volume_mpc_h3 / PAPER_VOLUME_MPC_H3 - 1,
            "isosurface": "Marching cubes at 0.5 between label 1 and other labels, padded with background; voxel membership unchanged",
            "component_policy": "Extract 6-face-connected components independently so diagonal contacts do not create non-manifold shared edges",
            "coordinate_policy": "FITS axes x,y,z mapped to native model x,y,z; origin centered on the 128^3 grid; axes are not assigned SGX/SGY/SGZ",
            "normal_orientation": "Positive signed volume per component; area-weighted outward vertex normals",
            "uncertainty": "Grid discretization and the published velocity reconstruction define this surface; it is not a uniquely measured physical wall",
        },
        "volume_semantics": "not_a_solid_volume_measurement",
        "closed_volume_checked": False,
        "staged_asset_path": str(DEFAULT_OUTPUT),
        **stats,
    }
    return glb_bytes, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--entry", type=Path, default=DEFAULT_ENTRY)
    args = parser.parse_args()
    archive_bytes = args.archive.read_bytes()
    glb_bytes, metadata = create_model(archive_bytes)
    metadata["staged_asset_path"] = str(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(glb_bytes)
    args.entry.parent.mkdir(parents=True, exist_ok=True)
    args.entry.write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Wrote {args.output}: {len(glb_bytes):,} bytes, {metadata['triangle_count']:,} triangles")
    print(f"Wrote staged entry {args.entry}; longest native extent {metadata['presentation']['reference_size']:.3f} Mpc")


if __name__ == "__main__":
    main()
