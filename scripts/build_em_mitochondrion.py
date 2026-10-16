#!/usr/bin/env python3
"""Build a 3D model of one real mitochondrion from public FIB-SEM segmentation data.

Source: Janelia OpenOrganelle / CellMap (COSEM), dataset jrc_jurkat-1 (a Jurkat T cell
imaged by FIB-SEM at 4 x 4 x 3.44 nm voxels), bucket s3://janelia-cosem-datasets, CC BY 4.0.
Object 265 of the "mito_seg" instance segmentation is one elongated mitochondrion.

Two things are read from the public N5 volumes (gzip chunks, plain HTTPS, no credentials):
  labels/mito_seg/s0        instance labels (uint16): the organelle outline.
  labels/mito-mem_pred/s0   soft prediction (uint8) of the mitochondrial membranes by the
                            COSEM 3D U-Net: bright sheets are the outer membrane and the
                            inner membrane folded into cristae. (Stored mirrored in y.)

Geometry (all lengths nm, in the dataset's own axes):
  * Outer surface: marching cubes on the object mask (8 nm grid, lightly smoothed).
  * Cristae: ridges of the membrane prediction (local contrast over a 20 nm background)
    deeper than 45 nm inside the outline, so the inner boundary/outer membrane band is left
    to the translucent shell. Small fragments are dropped. Marching cubes at 4 nm, then
    Taubin smoothing and quadric-style decimation (meshoptimizer via gltf-transform).
The long axis (principal axis of the mask) is rotated to +X and the model is centred; the
GLB stays in nanometres. The cristae are a *machine-learning prediction* from EM: faint
cristae the network did not detect are absent, so the mesh is a lower bound on the folding.

Example (needs scikit-image + scipy from the repo venv, network, and npx with
@gltf-transform/cli@4.5.0 cached or online):
    ./venv/bin/python scripts/build_em_mitochondrion.py --output-dir /tmp/mito-em
"""

import argparse
import gzip
import hashlib
import json
import shutil
import ssl
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi
from scipy import sparse
from skimage import measure

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_model_assets import pack_glb, read_glb  # noqa: E402

BUCKET = "https://janelia-cosem-datasets.s3.amazonaws.com/"
DATASET = "jrc_jurkat-1"
N5 = f"{DATASET}/{DATASET}.n5/"
OBJECT_ID = 265
# s0 voxel box (x, y, z), half-open, including a 20-voxel margin around the object.
CROP_LO = (4644, 268, 5500)
CROP_HI = (5188, 724, 6692)
VOXEL_XYZ = (4.0, 4.0, 3.44)  # nm

DEPTH_MIN_NM = 45.0        # cristae start this far inside the outline (skips the membrane band)
RIDGE_CONTRAST = 7.0       # prediction minus its ~20 nm local background
RIDGE_LEVEL = 100.0        # and at least this absolute prediction level (0..~160)
MIN_FRAGMENT_VOXELS = 1500  # at 4 nm; drops specks
CRISTAE_TRIANGLES = 90_000
SHELL_TRIANGLES = 14_000

OUTER_COLOR = (0.80, 0.66, 0.43, 0.30)   # tan, translucent
CRISTAE_COLOR = (0.93, 0.34, 0.14, 1.0)  # orange-red

LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
CITATIONS = [
    "Heinrich, L. et al. Whole-cell organelle segmentation in volume electron microscopy. "
    "Nature 599, 141-146 (2021). https://doi.org/10.1038/s41586-021-03977-3",
    "Xu, C. S. et al. An open-access volume electron microscopy atlas of whole cells and "
    "tissues. Nature 599, 147-151 (2021). https://doi.org/10.1038/s41586-021-03992-4",
]


# ----------------------------------------------------------------------------- N5 access
def ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


class N5Array:
    """Minimal reader for a gzip-compressed N5 dataset served over HTTPS."""

    def __init__(self, path, cache):
        self.url, self.cache, self.ctx = BUCKET + path.rstrip("/") + "/", cache, ssl_context()
        self.attrs = json.loads(self.fetch("attributes.json"))
        if self.attrs["compression"]["type"] != "gzip":
            raise ValueError("Only gzip N5 chunks are supported")
        self.dims, self.block = self.attrs["dimensions"], self.attrs["blockSize"]
        self.dtype = {"uint8": ">u1", "uint16": ">u2"}[self.attrs["dataType"]]

    def fetch(self, name):
        local = self.cache / (self.url.replace("https://", "").replace("/", "_") + name.replace("/", "_"))
        if local.exists():
            return local.read_bytes()
        data = b""
        for attempt in range(8):
            try:
                data = urllib.request.urlopen(self.url + name, context=self.ctx, timeout=60).read()
                break
            except urllib.error.HTTPError as error:
                if error.code in (403, 404):
                    break  # absent chunk = fill value
                time.sleep(1 + attempt)
            except (urllib.error.URLError, OSError):
                time.sleep(1 + attempt)
        else:
            raise RuntimeError(f"download failed: {self.url + name}")
        local.write_bytes(data)
        return data

    def chunk(self, index):
        raw = self.fetch("/".join(map(str, index)))
        if not raw:
            return None
        mode, ndim = struct.unpack(">HH", raw[:4])
        shape = struct.unpack(">" + "I" * ndim, raw[4:4 + 4 * ndim])
        offset = 4 + 4 * ndim + (4 if mode == 1 else 0)
        data = np.frombuffer(gzip.decompress(raw[offset:]), dtype=self.dtype).astype(self.dtype[1:])
        return data.reshape(shape[::-1])  # (z, y, x)

    def read(self, lo, hi, workers=8):
        out = np.zeros([h - l for l, h in zip(lo[::-1], hi[::-1])], dtype=self.dtype[1:])
        first = [l // b for l, b in zip(lo, self.block)]
        last = [(h - 1) // b for h, b in zip(hi, self.block)]
        jobs = [(x, y, z) for x in range(first[0], last[0] + 1) for y in range(first[1], last[1] + 1)
                for z in range(first[2], last[2] + 1)]
        with ThreadPoolExecutor(workers) as pool:
            for index, chunk in zip(jobs, pool.map(self.chunk, jobs)):
                if chunk is None:
                    continue
                origin = [i * b for i, b in zip(index, self.block)]
                a = [max(l, o) for l, o in zip(lo, origin)]
                b = [min(h, o + chunk.shape[2 - k]) for k, (h, o) in enumerate(zip(hi, origin))]
                out[a[2] - lo[2]:b[2] - lo[2], a[1] - lo[1]:b[1] - lo[1], a[0] - lo[0]:b[0] - lo[0]] = \
                    chunk[a[2] - origin[2]:b[2] - origin[2], a[1] - origin[1]:b[1] - origin[1],
                          a[0] - origin[0]:b[0] - origin[0]]
        return out


def sha256(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


# --------------------------------------------------------------------------- volume work
def to_isotropic_z(volume, mask=False):
    """Linearly resample (z, y, x) from VOXEL_XYZ[2] to 4 nm z spacing."""
    nz = volume.shape[0]
    count = int(np.floor((nz - 1) * VOXEL_XYZ[2] / 4.0)) + 1
    pos = np.arange(count) * 4.0 / VOXEL_XYZ[2]
    i0 = np.floor(pos).astype(int)
    w = (pos - i0).astype(np.float32)
    i1 = np.minimum(i0 + 1, nz - 1)
    out = np.empty((count,) + volume.shape[1:], dtype=bool if mask else np.uint8)
    for k in range(count):
        blend = volume[i0[k]] * (1 - w[k]) + volume[i1[k]] * w[k]
        out[k] = blend >= 0.5 if mask else np.rint(blend)
    return out


def marching(field, level, spacing):
    verts, faces, _, _ = measure.marching_cubes(field, level, spacing=spacing, allow_degenerate=False)
    return verts[:, ::-1].astype(np.float64), faces[:, ::-1].astype(np.int64)  # (z,y,x)->(x,y,z), keep winding


def taubin(verts, faces, iterations=10, lam=0.5, mu=-0.53):
    n = len(verts)
    rows = np.concatenate([faces[:, 0], faces[:, 1], faces[:, 2], faces[:, 1], faces[:, 2], faces[:, 0]])
    cols = np.concatenate([faces[:, 1], faces[:, 2], faces[:, 0], faces[:, 0], faces[:, 1], faces[:, 2]])
    adjacency = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()
    adjacency.data[:] = 1.0
    degree = np.maximum(np.asarray(adjacency.sum(axis=1)).ravel(), 1.0)
    walk = sparse.diags(1.0 / degree) @ adjacency
    for _ in range(iterations):
        verts = verts + lam * (walk @ verts - verts)
        verts = verts + mu * (walk @ verts - verts)
    return verts


def vertex_normals(verts, faces):
    a, b, c = (verts[faces[:, k]] for k in range(3))
    face_normals = np.cross(b - a, c - a)
    normals = np.zeros_like(verts)
    for k in range(3):
        np.add.at(normals, faces[:, k], face_normals)
    length = np.linalg.norm(normals, axis=1, keepdims=True)
    return normals / np.maximum(length, 1e-12)


def mesh_area(verts, faces):
    a, b, c = (verts[faces[:, k]] for k in range(3))
    return 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum()


def accessor_values(document, binary, index):
    accessor = document["accessors"][index]
    view = document["bufferViews"][accessor["bufferView"]]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    dtype = {5126: "<f4", 5123: "<u2", 5125: "<u4"}[accessor["componentType"]]
    width = {"SCALAR": 1, "VEC3": 3}[accessor["type"]]
    return np.frombuffer(binary, dtype=dtype, count=accessor["count"] * width, offset=start).reshape(-1, width)


def decimate(verts, faces, target_triangles, error, work):
    """Weld + meshoptimizer simplify through the gltf-transform CLI (see AGENTS.md)."""
    binary = bytearray()
    binary += verts.astype("<f4").tobytes()
    binary += b"\0" * (-len(binary) % 4)
    offset = len(binary)
    binary += faces.astype("<u4").tobytes()
    document = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
                "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "mode": 4}]}],
                "accessors": [
                    {"bufferView": 0, "componentType": 5126, "count": len(verts), "type": "VEC3",
                     "min": verts.min(axis=0).tolist(), "max": verts.max(axis=0).tolist()},
                    {"bufferView": 1, "componentType": 5125, "count": faces.size, "type": "SCALAR"}],
                "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": verts.size * 4},
                                {"buffer": 0, "byteOffset": offset, "byteLength": faces.size * 4}]}
    source, welded, small = work / "in.glb", work / "welded.glb", work / "small.glb"
    source.write_bytes(pack_glb(document, bytes(binary)))
    cli = ["npx", "--no-install", "@gltf-transform/cli@4.5.0"]
    subprocess.run(cli + ["weld", str(source), str(welded)], check=True, capture_output=True)
    ratio = min(1.0, target_triangles / len(faces))
    subprocess.run(cli + ["simplify", str(welded), str(small), "--ratio", f"{ratio:.5f}",
                          "--error", f"{error}"], check=True, capture_output=True)
    document, binary = read_glb(small.read_bytes())
    primitive = document["meshes"][0]["primitives"][0]
    out_verts = accessor_values(document, binary, primitive["attributes"]["POSITION"]).astype(np.float64)
    out_faces = accessor_values(document, binary, primitive["indices"]).astype(np.int64).reshape(-1, 3)
    return out_verts, out_faces


def long_axis_frame(mask):
    """Principal axes of the mask in nm (x, y, z) coordinates; returns mean and 3x3 rows."""
    coords = np.argwhere(mask)[:, ::-1].astype(np.float64) * 4.0
    mean = coords.mean(axis=0)
    _, _, vt = np.linalg.svd(coords - mean, full_matrices=False)
    if np.linalg.det(vt) < 0:
        vt[2] *= -1
    return mean, vt


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ------------------------------------------------------------------------------- build
def build(args):
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    cache = args.cache_dir or out / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    def log(message):
        print(f"[{time.time() - t0:6.1f}s] {message}", flush=True)

    seg_array = N5Array(N5 + "labels/mito_seg/s0", cache)
    pred_array = N5Array(N5 + "labels/mito-mem_pred/s0", cache)
    seg = seg_array.read(CROP_LO, CROP_HI)
    ny = pred_array.dims[1]
    # The prediction volume is stored mirrored in y relative to the other volumes.
    pred = pred_array.read((CROP_LO[0], ny - CROP_HI[1], CROP_LO[2]), (CROP_HI[0], ny - CROP_LO[1], CROP_HI[2]))[:, ::-1, :]
    log(f"downloaded crops seg={seg.shape} pred={pred.shape}")
    mask = seg == OBJECT_ID
    voxel_volume_nm3 = np.prod(VOXEL_XYZ)
    inside = pred[mask].mean()
    assert inside > 30, "prediction/segmentation misaligned (y mirror?)"
    crop_hashes = {"mito_seg_crop_uint16": sha256(seg), "mito-mem_pred_crop_uint8": sha256(pred)}

    pred_iso, mask_iso = to_isotropic_z(pred), to_isotropic_z(mask.astype(np.uint8), mask=True)
    del seg, pred
    log(f"isotropic 4 nm grid {pred_iso.shape}")

    # -- outer surface (8 nm grid) ------------------------------------------------------
    cut = [(n // 2) * 2 for n in mask_iso.shape]
    coarse = mask_iso[:cut[0], :cut[1], :cut[2]].reshape(cut[0] // 2, 2, cut[1] // 2, 2, cut[2] // 2, 2)
    coarse = coarse.mean(axis=(1, 3, 5)).astype(np.float32)
    coarse = ndi.gaussian_filter(np.pad(coarse, 2), 1.0)
    shell_v, shell_f = marching(coarse, 0.5, (8.0, 8.0, 8.0))
    # Undo the 2-cell pad; an 8 nm cell averages 4 nm samples j=2i, 2i+1, so its centre is i*8 + 2 nm.
    shell_v = taubin(shell_v - 2 * 8.0 + 2.0, shell_f, iterations=6)
    log(f"outer surface {len(shell_f):,} triangles")

    # -- cristae ------------------------------------------------------------------------
    depth_coarse = ndi.distance_transform_edt(mask_iso[::2, ::2, ::2]) * 8.0
    depth = ndi.zoom(depth_coarse, 2, order=1)[:pred_iso.shape[0], :pred_iso.shape[1], :pred_iso.shape[2]]
    values = pred_iso.astype(np.float32)
    smooth = ndi.gaussian_filter(values, 1.0)
    contrast = smooth - ndi.gaussian_filter(values, 5.0)
    del values
    ridge = (contrast > RIDGE_CONTRAST) & (smooth > RIDGE_LEVEL) & (depth > DEPTH_MIN_NM) & mask_iso
    del contrast, smooth, depth
    labels, count = ndi.label(ridge, structure=np.ones((3, 3, 3)))
    sizes = np.bincount(labels.ravel())
    keep = sizes >= MIN_FRAGMENT_VOXELS
    keep[0] = False
    ridge = keep[labels]
    del labels
    log(f"cristae voxels kept: {ridge.sum():,} in {int(keep.sum())} fragments (of {count})")
    zs, ys, xs = np.nonzero(ridge)
    lo = np.array([zs.min(), ys.min(), xs.min()]) - 4
    hi = np.array([zs.max(), ys.max(), xs.max()]) + 5
    box = tuple(slice(max(0, int(a)), int(b)) for a, b in zip(lo, hi))
    field = ndi.gaussian_filter(ridge[box].astype(np.float32), 0.8)
    field = np.pad(field, 1)
    raw_v, raw_f = marching(field, 0.45, (4.0, 4.0, 4.0))
    origin = (np.array([b.start for b in box])[::-1] - 1) * 4.0
    raw_v = raw_v + origin
    log(f"cristae marching cubes {len(raw_f):,} triangles")
    raw_v = taubin(raw_v, raw_f, iterations=8)
    cr_v, cr_f = decimate(raw_v, raw_f, args.cristae_triangles, 0.006, out)
    log(f"cristae decimated {len(cr_f):,} triangles")
    sh_v, sh_f = decimate(shell_v, shell_f, args.shell_triangles, 0.004, out)
    log(f"shell decimated {len(sh_f):,} triangles")

    # -- orient: long axis -> +X, centre ---------------------------------------------------
    mean, frame = long_axis_frame(mask_iso)
    def reframe(v):
        return (v - mean) @ frame.T
    # reframe's rows: x = long axis, y = middle axis, z = short axis (right-handed)
    sh_v, cr_v = reframe(sh_v), reframe(cr_v)
    low, high = sh_v.min(axis=0), sh_v.max(axis=0)
    centre = (low + high) / 2
    sh_v, cr_v = sh_v - centre, cr_v - centre
    extent = (high - low)
    area_shell = mesh_area(sh_v, sh_f)
    area_cristae = mesh_area(cr_v, cr_f)
    mask_volume_um3 = float(mask_iso.sum() * 64 / 1e9)
    stats = {
        "length_nm": float(extent[0]), "width_nm": float(extent[1]), "depth_nm": float(extent[2]),
        "mask_volume_um3": mask_volume_um3,
        "outer_surface_area_um2": area_shell / 1e6, "cristae_two_sided_shell_area_um2": area_cristae / 1e6,
        "triangles_shell": int(len(sh_f)), "triangles_cristae": int(len(cr_f)),
    }
    log(json.dumps(stats))

    # -- write GLB ------------------------------------------------------------------------
    document = {"asset": {"version": "2.0", "generator": "Universe Scales scripts/build_em_mitochondrion.py"},
                "scene": 0, "scenes": [{"nodes": [0, 1]}], "nodes": [], "meshes": [], "materials": [],
                "accessors": [], "bufferViews": []}
    binary = bytearray()

    def add(array, component, kind, bounds=False):
        binary.extend(b"\0" * (-len(binary) % 4))
        document["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": array.nbytes})
        binary.extend(array.tobytes())
        entry = {"bufferView": len(document["bufferViews"]) - 1, "componentType": component,
                 "count": int(len(array) if kind != "SCALAR" else array.size), "type": kind}
        if bounds:
            entry["min"], entry["max"] = array.min(axis=0).tolist(), array.max(axis=0).tolist()
        document["accessors"].append(entry)
        return len(document["accessors"]) - 1

    def add_mesh(name, verts, faces, color, extras, roughness):
        normals = vertex_normals(verts, faces).astype(np.float32)
        verts32 = verts.astype(np.float32)
        position = add(verts32, 5126, "VEC3", bounds=True)
        normal = add(normals, 5126, "VEC3")
        index = add(faces.astype(np.uint16 if len(verts) < 65535 else np.uint32).ravel(),
                    5123 if len(verts) < 65535 else 5125, "SCALAR")
        material = {"name": name, "doubleSided": True,
                    "pbrMetallicRoughness": {"baseColorFactor": list(color), "metallicFactor": 0.0,
                                             "roughnessFactor": roughness}}
        if color[3] < 1:
            material["alphaMode"] = "BLEND"
        document["materials"].append(material)
        document["meshes"].append({"name": name, "primitives": [{
            "attributes": {"POSITION": position, "NORMAL": normal}, "indices": index,
            "material": len(document["materials"]) - 1, "mode": 4}]})
        document["nodes"].append({"name": name, "mesh": len(document["meshes"]) - 1, "extras": extras})

    # Opaque cristae first, then the translucent outer shell (it must not hide them).
    add_mesh("Cristae (inner membrane folds, predicted)", cr_v, cr_f, CRISTAE_COLOR,
             {"units": "nm", "source": "COSEM mito-mem_pred ridges"}, 0.55)
    add_mesh("Outer envelope", sh_v, sh_f, OUTER_COLOR,
             {"units": "nm", "source": f"COSEM mito_seg object {OBJECT_ID}"}, 0.7)
    document["buffers"] = [{"byteLength": len(binary)}]
    glb = pack_glb(document, bytes(binary))
    (out / "em-mitochondrion.glb").write_bytes(glb)
    log(f"wrote em-mitochondrion.glb {len(glb):,} bytes")

    record = {"stats": stats, "crop_hashes": crop_hashes, "crop_lo_xyz_voxels": list(CROP_LO),
              "crop_hi_xyz_voxels": list(CROP_HI), "voxel_xyz_nm": list(VOXEL_XYZ),
              "mean_prediction_inside_object": float(inside)}
    (out / "em-mitochondrion-build.json").write_text(json.dumps(record, indent=1))
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--cristae-triangles", type=int, default=CRISTAE_TRIANGLES)
    parser.add_argument("--shell-triangles", type=int, default=SHELL_TRIANGLES)
    build(parser.parse_args())


if __name__ == "__main__":
    main()
