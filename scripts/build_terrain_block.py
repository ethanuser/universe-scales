#!/usr/bin/env python3
"""Turn a heightmap terrain GLB into a solid block diagram standing on sea level.

    python3 scripts/build_terrain_block.py TERRAIN.glb OUT.glb --summit 8848

The terrain is assumed to be in meters with its highest vertex at the summit.
Opaque rock walls, shaded as strata, drop from every open boundary edge to the
terrain's lowest point and a floor closes them. Below that, a faint translucent
plinth continues down to sea level (summit - elevation), so the model's full
height is the true elevation while the mountain itself stays readable. Nodes
with glTF `extras.label` mark the summit and sea level; the explorer draws them
as upright labels (three.js copies extras into userData).
"""

import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_model_assets import pack_glb, read_glb  # noqa: E402
from texture_padding import accessor_array  # noqa: E402

STRATA_METERS = 350  # wall rows; alternate bands read as rock layers


def append_view(document, binary, array, target=None):
    data = np.ascontiguousarray(array).tobytes()
    binary.extend(b"\0" * (-len(binary) % 4))
    view = {"buffer": 0, "byteOffset": len(binary), "byteLength": len(data)}
    if target:
        view["target"] = target
    document["bufferViews"].append(view)
    binary.extend(data)
    return len(document["bufferViews"]) - 1


def append_accessor(document, binary, array, kind, component, target=None, bounds=False):
    accessor = {"bufferView": append_view(document, binary, array, target), "componentType": component,
                "count": len(array), "type": kind}
    if bounds:
        accessor["min"] = array.min(axis=0).tolist()
        accessor["max"] = array.max(axis=0).tolist()
    document["accessors"].append(accessor)
    return len(document["accessors"]) - 1


def build(source, output, summit_height):
    document, payload = read_glb(source.read_bytes())
    binary = bytearray(payload)
    primitive = document["meshes"][0]["primitives"][0]
    positions = accessor_array(document, binary, primitive["attributes"]["POSITION"]).astype(np.float64)
    triangles = accessor_array(document, binary, primitive["indices"]).reshape(-1, 3)
    top = positions[:, 1].max()
    base = top - summit_height
    floor = positions[:, 1].min()

    # Open boundary edges appear in exactly one triangle.
    counts = {}
    for a, b, c in triangles:
        for u, v in ((a, b), (b, c), (c, a)):
            key = (min(u, v), max(u, v))
            counts[key] = counts.get(key, 0) + 1
    boundary = [key for key, count in counts.items() if count == 1]
    centroid = positions[:, [0, 2]].mean(axis=0)

    wall_positions, wall_normals, wall_colors, wall_indices = [], [], [], []
    rock_top, rock_bottom = np.array([0.46, 0.41, 0.36]), np.array([0.25, 0.22, 0.2])
    for a, b in boundary:
        pa, pb = positions[a], positions[b]
        direction = pb[[0, 2]] - pa[[0, 2]]
        normal = np.array([direction[1], 0.0, -direction[0]])
        if np.dot(normal[[0, 2]], (pa[[0, 2]] + pb[[0, 2]]) / 2 - centroid) < 0:
            normal, (pa, pb) = -normal, (pb, pa)
        normal /= np.linalg.norm(normal) or 1
        # Rows at fixed elevations so strata line up around the block.
        levels = np.arange(floor, max(pa[1], pb[1]), STRATA_METERS)
        rows = [(level, level) for level in levels] + [(pa[1], pb[1])]
        start = len(wall_positions)
        for left_y, right_y in rows:
            for point, y in ((pa, min(left_y, pa[1])), (pb, min(right_y, pb[1]))):
                wall_positions.append([point[0], y, point[2]])
                wall_normals.append(normal)
                depth = (top - y) / summit_height
                band = 0.86 + 0.14 * (int((y - base) // STRATA_METERS) % 2)
                wall_colors.append((rock_top + (rock_bottom - rock_top) * depth) * band)
        for row in range(len(rows) - 1):
            i = start + 2 * row
            wall_indices += [i, i + 1, i + 3, i, i + 3, i + 2]
    # Floor under the terrain, over the footprint's bounding rectangle.
    (x0, z0), (x1, z1) = positions[:, [0, 2]].min(axis=0), positions[:, [0, 2]].max(axis=0)
    start = len(wall_positions)
    for x, z in ((x0, z0), (x1, z0), (x1, z1), (x0, z1)):
        wall_positions.append([x, floor, z])
        wall_normals.append([0.0, -1.0, 0.0])
        wall_colors.append(rock_bottom)
    wall_indices += [start, start + 1, start + 2, start, start + 2, start + 3]

    wall_positions = np.array(wall_positions, dtype=np.float32)
    attributes = {
        "POSITION": append_accessor(document, binary, wall_positions, "VEC3", 5126, 34962, bounds=True),
        "NORMAL": append_accessor(document, binary, np.array(wall_normals, dtype=np.float32), "VEC3", 5126, 34962),
        "COLOR_0": append_accessor(document, binary, np.array(wall_colors, dtype=np.float32), "VEC3", 5126, 34962),
    }
    indices = append_accessor(document, binary, np.array(wall_indices, dtype=np.uint32), "SCALAR", 5125, 34963)
    document["materials"].append({"name": "rock_strata", "doubleSided": True,
                                  "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1],
                                                           "metallicFactor": 0, "roughnessFactor": 0.95}})
    document["meshes"][0]["primitives"].append({"attributes": attributes, "indices": indices, "mode": 4,
                                                "material": len(document["materials"]) - 1})
    # Translucent plinth from the terrain floor down to sea level.
    corners = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    plinth = [[x, y, z] for y in (floor, base) for x, z in corners]
    faces = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]
    plinth_indices = [i for a, b, c, d in faces for i in (a, b, c, a, c, d)]
    plinth = np.array(plinth, dtype=np.float32)
    document["materials"].append({"name": "crust_to_sea_level", "doubleSided": True, "alphaMode": "BLEND",
                                  "pbrMetallicRoughness": {"baseColorFactor": [0.42, 0.37, 0.33, 0.2],
                                                           "metallicFactor": 0, "roughnessFactor": 1}})
    document["meshes"][0]["primitives"].append({
        "attributes": {"POSITION": append_accessor(document, binary, plinth, "VEC3", 5126, 34962, bounds=True)},
        "indices": append_accessor(document, binary, np.array(plinth_indices, dtype=np.uint32), "SCALAR", 5125, 34963),
        "mode": 4, "material": len(document["materials"]) - 1})
    summit = positions[positions[:, 1].argmax()]
    document["nodes"] += [
        {"name": "summit-label", "translation": [float(summit[0]), float(top + 250), float(summit[2])],
         "extras": {"label": f"Summit {summit_height:,.0f} m"}},
        {"name": "sea-level-label", "translation": [float((x0 + x1) / 2), float(base + 350), float(z1)],
         "extras": {"label": "Sea level"}},
    ]
    document["scenes"][0]["nodes"] += [len(document["nodes"]) - 2, len(document["nodes"]) - 1]
    document.setdefault("asset", {})["generator"] = "Universe Scales terrain block"
    output.write_bytes(pack_glb(document, bytes(binary)))
    print(json.dumps({"output": str(output), "bytes": output.stat().st_size, "boundary_edges": len(boundary),
                      "terrain_low_m": float(positions[:, 1].min() - base), "summit_m": summit_height}))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("terrain", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--summit", type=float, required=True, help="Summit elevation above sea level, meters")
    args = parser.parse_args()
    build(args.terrain, args.output, args.summit)


if __name__ == "__main__":
    main()
