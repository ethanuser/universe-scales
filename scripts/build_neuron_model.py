#!/usr/bin/env python3
"""Build a micrometer-scale local neuron crop from an Allen Cell Types SWC.

Example:
  python3 scripts/build_neuron_model.py \
    --swc /private/tmp/neuron-scientific/allen-specimen-480114344.swc \
    --markers /private/tmp/neuron-scientific/allen-specimen-480114344-marker.swc \
    --output-dir /private/tmp/neuron-scientific

SWC coordinates and radii are retained in micrometers. The crop is centered on
the soma and clipped to +/-50 um on each axis; it is not stretched to fit.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

from fetch_model_assets import pack_glb, write_json

SPECIMEN_ID = 480114344
RECONSTRUCTION_ID = 491771446
SWC_FILE_ID = 491771448
MARKER_FILE_ID = 496606365
HALF_CROP_UM = 50.0
MAX_GLB_BYTES = 1_500_000
CELL_PAGE = f"https://celltypes.brain-map.org/mouse/experiment/electrophysiology/{SPECIMEN_ID}"
SWC_URL = f"https://api.brain-map.org/api/v2/well_known_file_download/{SWC_FILE_ID}"
MARKER_URL = f"https://api.brain-map.org/api/v2/well_known_file_download/{MARKER_FILE_ID}"
TERMS_URL = "https://alleninstitute.org/terms-of-use/"
CITATION_URL = "https://alleninstitute.org/legal/citation-policy"
PAPER_URL = "https://doi.org/10.1038/s41593-019-0417-0"


def read_swc(path):
    """Parse Allen's seven-column SWC, validating ids and parent references."""
    nodes = {}
    for line_number, line in enumerate(Path(path).read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) != 7:
            raise ValueError(f"SWC line {line_number}: expected 7 columns")
        node_id, kind, x, y, z, radius, parent_id = fields
        node_id, kind, parent_id = int(node_id), int(kind), int(parent_id)
        values = tuple(float(value) for value in (x, y, z, radius))
        if node_id in nodes or not all(math.isfinite(value) for value in values):
            raise ValueError(f"SWC line {line_number}: duplicate id or non-finite value")
        if values[3] < 0:
            raise ValueError(f"SWC line {line_number}: radius must be nonnegative")
        nodes[node_id] = {"id": node_id, "type": kind, "xyz": values[:3],
                          "radius": values[3], "parent": parent_id}
    if not nodes:
        raise ValueError("SWC contains no compartments")
    roots = [node for node in nodes.values() if node["parent"] < 0]
    if len(roots) != 1 or roots[0]["type"] != 1:
        raise ValueError("Expected one type-1 soma root")
    for node in nodes.values():
        if node["parent"] >= 0 and node["parent"] not in nodes:
            raise ValueError(f"SWC node {node['id']} has a missing parent")
    return nodes, roots[0]


def clip_segment(start, end, half_extent=HALF_CROP_UM):
    """Liang-Barsky clip a segment to the soma-centered micrometer cube."""
    low, high = 0.0, 1.0
    for axis in range(3):
        delta = end[axis] - start[axis]
        if abs(delta) < 1e-12:
            if start[axis] < -half_extent or start[axis] > half_extent:
                return None
            continue
        a = (-half_extent - start[axis]) / delta
        b = (half_extent - start[axis]) / delta
        low = max(low, min(a, b))
        high = min(high, max(a, b))
        if low > high:
            return None
    return low, high


def _lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _tube_segment(positions, indices, start, end, radius_start, radius_end, sides=6):
    delta = tuple(end[i] - start[i] for i in range(3))
    length = math.sqrt(sum(value * value for value in delta))
    if length < 1e-8:
        return
    tangent = tuple(value / length for value in delta)
    reference = (0.0, 0.0, 1.0) if abs(tangent[2]) < 0.9 else (0.0, 1.0, 0.0)
    normal = (tangent[1] * reference[2] - tangent[2] * reference[1],
              tangent[2] * reference[0] - tangent[0] * reference[2],
              tangent[0] * reference[1] - tangent[1] * reference[0])
    norm = math.sqrt(sum(value * value for value in normal))
    normal = tuple(value / norm for value in normal)
    binormal = (tangent[1] * normal[2] - tangent[2] * normal[1],
                tangent[2] * normal[0] - tangent[0] * normal[2],
                tangent[0] * normal[1] - tangent[1] * normal[0])
    base = len(positions) // 3
    for point, radius in ((start, radius_start), (end, radius_end)):
        for side in range(sides):
            angle = 2 * math.pi * side / sides
            positions.extend(point[i] + radius * (normal[i] * math.cos(angle)
                                                    + binormal[i] * math.sin(angle))
                             for i in range(3))
    for side in range(sides):
        a, b = base + side, base + (side + 1) % sides
        indices.extend((a, a + sides, b, b, a + sides, b + sides))


def _sphere_mesh(center, radius, rings=10, sides=16):
    positions, indices = [], []
    for ring in range(rings + 1):
        latitude = -math.pi / 2 + math.pi * ring / rings
        for side in range(sides):
            longitude = 2 * math.pi * side / sides
            positions.extend((center[0] + radius * math.cos(latitude) * math.cos(longitude),
                              center[1] + radius * math.sin(latitude),
                              center[2] + radius * math.cos(latitude) * math.sin(longitude)))
    for ring in range(rings):
        for side in range(sides):
            a = ring * sides + side
            b = ring * sides + (side + 1) % sides
            indices.extend((a, a + sides, b, b, a + sides, b + sides))
    return positions, indices


def read_markers(path, soma_xyz):
    """Read Allen marker CSV rows (10=truncated dendrite, 20=no reconstruction)."""
    markers = []
    if path is None:
        return markers
    for line_number, line in enumerate(Path(path).read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = [field.strip() for field in line.split(",")]
        if len(fields) < 7:
            raise ValueError(f"marker line {line_number}: expected Allen marker columns")
        xyz = tuple(float(fields[index]) - soma_xyz[index] for index in range(3))
        marker_type = int(fields[5])
        if marker_type in (10, 20) and all(abs(value) <= HALF_CROP_UM for value in xyz):
            markers.append({"xyz": xyz, "type": marker_type})
    return markers


def _glb(document, binary):
    document["buffers"] = [{"byteLength": len(binary)}]
    return pack_glb(document, bytes(binary))


def build(swc_path, marker_path=None):
    nodes, soma = read_swc(swc_path)
    origin = soma["xyz"]
    local = {node_id: tuple(node["xyz"][axis] - origin[axis] for axis in range(3))
             for node_id, node in nodes.items()}
    by_type = {2: ([], []), 3: ([], []), 4: ([], [])}
    retained = 0
    clipped = 0
    for child in nodes.values():
        if child["parent"] < 0:
            continue
        parent = nodes[child["parent"]]
        if child["type"] not in by_type:
            continue
        interval = clip_segment(local[parent["id"]], local[child["id"]])
        if interval is None or interval[1] - interval[0] < 1e-9:
            continue
        t0, t1 = interval
        start = _lerp(local[parent["id"]], local[child["id"]], t0)
        end = _lerp(local[parent["id"]], local[child["id"]], t1)
        # The soma is represented by its measured SWC radius; the centerline
        # branch enters that sphere at its own measured dendrite radius.
        parent_radius = child["radius"] if parent["type"] == 1 else parent["radius"]
        radius_start = parent_radius + (child["radius"] - parent_radius) * t0
        radius_end = parent_radius + (child["radius"] - parent_radius) * t1
        positions, indices = by_type[child["type"]]
        _tube_segment(positions, indices, start, end, radius_start, radius_end)
        retained += 1
        if t0 > 0 or t1 < 1:
            clipped += 1

    soma_center = (0.0, 0.0, 0.0)
    soma_positions, soma_indices = _sphere_mesh(soma_center, soma["radius"])
    markers = read_markers(marker_path, origin)
    document = {"asset": {"version": "2.0", "generator": "Universe Scales Allen SWC crop"},
                "scene": 0, "scenes": [{"nodes": []}], "nodes": [], "meshes": [],
                "materials": [], "accessors": [], "bufferViews": [],
                "extensionsUsed": ["KHR_materials_unlit"]}
    binary = bytearray()

    def accessor(values, item_type, target, components):
        while len(binary) % 4:
            binary.append(0)
        offset = len(binary)
        code = "f" if item_type == 5126 else "I"
        binary.extend(struct.pack("<" + code * len(values), *values))
        view_index = len(document["bufferViews"])
        document["bufferViews"].append({"buffer": 0, "byteOffset": offset,
                                        "byteLength": len(binary) - offset, "target": target})
        result = {"bufferView": view_index, "componentType": item_type,
                  "count": len(values) // components,
                  "type": {1: "SCALAR", 3: "VEC3"}[components]}
        if item_type == 5126 and components == 3:
            result["min"] = [min(values[i::3]) for i in range(3)]
            result["max"] = [max(values[i::3]) for i in range(3)]
        accessor_index = len(document["accessors"])
        document["accessors"].append(result)
        return accessor_index

    palette = {1: (0.91, 0.65, 0.35), 2: (0.95, 0.65, 0.31),
               3: (0.28, 0.69, 0.66), 4: (0.44, 0.76, 0.84)}

    def add_mesh(name, positions, indices, kind, extras=None):
        if not indices:
            return
        pos_accessor = accessor(positions, 5126, 34962, 3)
        index_accessor = accessor(indices, 5125, 34963, 1)
        material = len(document["materials"])
        color = palette[kind]
        document["materials"].append({"pbrMetallicRoughness": {
            "baseColorFactor": [*color, 1], "metallicFactor": 0, "roughnessFactor": 0.8},
            "extensions": {"KHR_materials_unlit": {}}})
        mesh = len(document["meshes"])
        document["meshes"].append({"name": name, "primitives": [{
            "attributes": {"POSITION": pos_accessor}, "indices": index_accessor,
            "material": material, "mode": 4}]})
        node = len(document["nodes"])
        document["nodes"].append({"name": name, "mesh": mesh, "extras": extras or {}})
        document["scenes"][0]["nodes"].append(node)

    add_mesh("Soma (Allen SWC radius)", soma_positions, soma_indices, 1,
             {"allenSwcType": 1, "units": "micrometers"})
    names = {2: "Axon (Allen SWC)", 3: "Basal dendrites (Allen SWC)",
             4: "Apical dendrites (Allen SWC)"}
    for kind, (positions, indices) in by_type.items():
        add_mesh(names[kind], positions, indices, kind,
                 {"allenSwcType": kind, "units": "micrometers"})
    if markers:
        marker_positions, marker_colors = [], []
        for marker in markers:
            marker_positions.extend(marker["xyz"])
            marker_colors.extend((1.0, 0.58, 0.22) if marker["type"] == 10
                                 else (0.95, 0.8, 0.45))
        pos_accessor = accessor(marker_positions, 5126, 34962, 3)
        color_accessor = accessor(marker_colors, 5126, 34962, 3)
        material = len(document["materials"])
        document["materials"].append({"pbrMetallicRoughness": {
            "baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0},
            "extensions": {"KHR_materials_unlit": {}}})
        mesh = len(document["meshes"])
        document["meshes"].append({"name": "Allen reconstruction markers", "primitives": [{
            "attributes": {"POSITION": pos_accessor, "COLOR_0": color_accessor},
            "material": material, "mode": 0}]})
        node = len(document["nodes"])
        document["nodes"].append({"name": "Allen truncation and unreconstructed-process markers",
                                  "mesh": mesh,
                                  "extras": {"pointSize": {"max": 5, "perPixel": 1 / 200},
                                             "markerTypes": {"10": "truncated dendrite",
                                                             "20": "no reconstruction"}}})
        document["scenes"][0]["nodes"].append(node)

    document["extras"] = {"units": "micrometers", "specimenId": SPECIMEN_ID,
                          "crop": {"center": "soma", "halfExtentUm": HALF_CROP_UM},
                          "retainedSwcSegments": retained, "cropIntersectedSegments": clipped}
    model = _glb(document, binary)
    if len(model) >= MAX_GLB_BYTES:
        raise ValueError(f"GLB is {len(model):,} bytes; exceeds {MAX_GLB_BYTES:,}-byte limit")
    return model, {"source_nodes": len(nodes), "retained_segments": retained,
                   "crop_intersected_segments": clipped, "included_markers": len(markers),
                   "soma_radius_um": soma["radius"], "crop_half_extent_um": HALF_CROP_UM,
                   "bytes": len(model)}


def build_entry(model, stats, swc_path, marker_path):
    processing = {**stats, "script": "scripts/build_neuron_model.py",
                  "source_swc_sha256": hashlib.sha256(Path(swc_path).read_bytes()).hexdigest(),
                  "source_swc_file_id": SWC_FILE_ID,
                  "source_reconstruction_id": RECONSTRUCTION_ID,
                  "specimen_id": SPECIMEN_ID,
                  "crop_semantics": "soma-centered axis-aligned cube; no geometry scaling"}
    if marker_path:
        processing["source_marker_sha256"] = hashlib.sha256(Path(marker_path).read_bytes()).hexdigest()
        processing["source_marker_file_id"] = MARKER_FILE_ID
    return {
        "id": "allen-celltypes-neuron-480114344",
        "source": CELL_PAGE,
        "download_url": SWC_URL,
        "link_label": "Allen Cell Types specimen and SWC reconstruction",
        "author": "Allen Institute for Brain Science; crop and mesh conversion by Universe Scales",
        "license": "Allen Institute Terms of Use; noncommercial use with attribution, not CC-BY/CC0",
        "license_url": TERMS_URL,
        "license_files": ["sources/neuron-model.md"],
        "matches": {"length": ["Neuron"]},
        "geometry": "mesh",
        "presentation": {"reference_size": 100, "pitch": 12, "yaw": -18,
                         "layout_width_factor": 1.05, "focus_scale_factor": 1.3},
        "basis_url": PAPER_URL,
        "basis_label": "Gouwens et al. (2019), Allen Cell Types Database",
        "note": "A micrometer-faithful local crop of Allen specimen 480114344, an Rorb-IRES2-Cre mouse visual-cortex dendrite-only reconstruction. Original SWC centerlines, radii and apical/basal types are retained inside a soma-centered +/-50 micrometer crop; branches crossing the crop are cut, not rescaled. The soma is represented as a sphere using the SWC root radius. Allen's in-crop markers identify traced dendrite truncations and a location where no reconstruction was made. This specimen has no reconstructed axon, and this local crop is not a complete neuron.",
        "processing": processing,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--swc", type=Path, required=True, help="Downloaded Allen 3DNeuronReconstruction SWC")
    parser.add_argument("--markers", type=Path, help="Optional Allen 3DNeuronMarker CSV")
    parser.add_argument("--output-dir", type=Path, default=Path("/private/tmp/neuron-scientific"))
    args = parser.parse_args()
    model, stats = build(args.swc, args.markers)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    model_path = args.output_dir / "allen-neuron-local-100um.glb"
    model_path.write_bytes(model)
    entry = build_entry(model, stats, args.swc, args.markers)
    write_json(args.output_dir / "entry.json", entry)
    print(f"{model_path}: {len(model):,} bytes; {stats['retained_segments']:,} SWC segments; "
          f"{stats['crop_intersected_segments']:,} crop intersections")


if __name__ == "__main__":
    main()
