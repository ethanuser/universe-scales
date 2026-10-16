#!/usr/bin/env python3
"""Replace the swastikas on the Hindenburg model's tail fins with plus signs.

    ./venv/bin/python scripts/patch_hindenburg_markings.py content/visualizations/models/earth3d-hindenburg.glb

The source model reproduces LZ 129's historical tail markings: a black swastika on a
white disk on a red band, on both faces of the upper and lower fins. This removes the
black triangles lying on those four disks (408 triangles, 102 per face) and adds a
black plus sign of the same span on each face. Nothing else changes.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_model_assets import pack_glb, read_glb  # noqa: E402
from texture_padding import accessor_array  # noqa: E402

BLACK_NODE = "Object_3"
DISK_CENTERS_YZ = [(2.37, -7.14), (0.23, -7.14)]   # world units, from the white-disk mesh
DISK_RADIUS = 0.22
ARM = 0.13            # half-span of each bar (the swastikas span 0.26)
BAR = 0.034           # half-thickness of each bar


def quat_matrix(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def append(document, binary, array, component, kind, target, minmax=False):
    binary.extend(b"\0" * (-len(binary) % 4))
    view = {"buffer": 0, "byteOffset": len(binary), "byteLength": array.nbytes, "target": target}
    binary.extend(array.tobytes())
    document["bufferViews"].append(view)
    accessor = {"bufferView": len(document["bufferViews"]) - 1, "componentType": component,
                "count": int(len(array)), "type": kind}
    if minmax:
        accessor["min"] = array.min(axis=0).astype(float).tolist()
        accessor["max"] = array.max(axis=0).astype(float).tolist()
    document["accessors"].append(accessor)
    return len(document["accessors"]) - 1


def patch(path):
    document, binary = read_glb(path.read_bytes())
    binary = bytearray(binary)
    node_index = next(i for i, n in enumerate(document["nodes"]) if n.get("name") == BLACK_NODE)
    node = document["nodes"][node_index]
    primitive = document["meshes"][node["mesh"]]["primitives"][0]
    material = primitive["material"]
    position = accessor_array(document, binary, primitive["attributes"]["POSITION"]).astype(float) / 32767
    indices = accessor_array(document, binary, primitive["indices"]).reshape(-1, 3)
    world = (quat_matrix(node["rotation"]) @ (position * node["scale"]).T).T + node["translation"]
    centroid = world[indices].mean(axis=1)
    on_disk = np.zeros(len(indices), bool)
    faces = []
    for y, z in DISK_CENTERS_YZ:
        near = (np.abs(centroid[:, 0]) < 0.08) & (np.hypot(centroid[:, 1] - y, centroid[:, 2] - z) < DISK_RADIUS)
        for side in (1, -1):
            hit = near & (np.sign(centroid[:, 0]) == side)
            if hit.any():
                faces.append((side, centroid[hit, 0].max() if side > 0 else centroid[hit, 0].min(), y, z))
            on_disk |= hit
    if len(faces) != 4 or on_disk.sum() != 408:
        raise SystemExit(f"Unexpected markings: {len(faces)} faces, {on_disk.sum()} triangles (already patched?)")

    # Keep the remaining black triangles (lettering, gondola windows) in place.
    kept = indices[~on_disk].astype(np.uint16).ravel()
    accessor = document["accessors"][primitive["indices"]]
    view = document["bufferViews"][accessor["bufferView"]]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    binary[start:start + kept.nbytes] = kept.tobytes()
    accessor["count"] = int(kept.size)

    # Plus signs: two bars per face, slightly proud of the disk, wound to face outward.
    positions, normals, triangles = [], [], []
    for side, x, y, z in faces:
        x += side * 0.0015
        for dy, dz in ((ARM, BAR), (BAR, ARM)):
            base = len(positions)
            corners = [(y - dy, z - dz), (y + dy, z - dz), (y + dy, z + dz), (y - dy, z + dz)]
            positions += [(x, cy, cz) for cy, cz in corners]
            normals += [(side, 0.0, 0.0)] * 4
            quad = [(0, 1, 2), (0, 2, 3)] if side > 0 else [(0, 2, 1), (0, 3, 2)]
            triangles += [tuple(base + k for k in tri) for tri in quad]
    pos_acc = append(document, binary, np.array(positions, np.float32), 5126, "VEC3", 34962, True)
    nrm_acc = append(document, binary, np.array(normals, np.float32), 5126, "VEC3", 34962)
    idx_acc = append(document, binary, np.array(triangles, np.uint16).ravel(), 5123, "SCALAR", 34963)
    document["meshes"].append({"name": "tail-plus-signs", "primitives": [
        {"attributes": {"POSITION": pos_acc, "NORMAL": nrm_acc}, "indices": idx_acc, "material": material}]})
    document["nodes"].append({"name": "tail-plus-signs", "mesh": len(document["meshes"]) - 1})
    document["scenes"][document.get("scene", 0)]["nodes"].append(len(document["nodes"]) - 1)
    document["buffers"][0]["byteLength"] = len(binary)
    path.write_bytes(pack_glb(document, bytes(binary)))
    return {"removed_triangles": int(on_disk.sum()), "plus_faces": len(faces)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("glb", type=Path)
    print(json.dumps(patch(parser.parse_args().glb)))


if __name__ == "__main__":
    main()
