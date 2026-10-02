#!/usr/bin/env python3
"""Drop geometry below a height in a single-primitive GLB (e.g. a display base).

    python3 scripts/crop_glb.py IN.glb OUT.glb --below -0.77

`--below` is in the primitive's POSITION space after normalization (so -1..1 for
a normalized, quantized accessor). Triangles with any vertex below it are
removed, and only the vertex records still referenced are kept, so bounds and
the explorer's calibration see the cropped shape. Supports primitives whose
attributes share one interleaved buffer view (glTF Transform's quantize output)
or use one tightly packed view per attribute.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_model_assets import pack_glb, read_glb  # noqa: E402
from texture_padding import COMPONENTS, WIDTH, accessor_array  # noqa: E402

NORMALIZED_MAX = {5120: 127, 5121: 255, 5122: 32767, 5123: 65535}


def element_bytes(accessor):
    return np.dtype(COMPONENTS[accessor["componentType"]]).itemsize * WIDTH[accessor["type"]]


def crop(source, output, below):
    document, payload = read_glb(source.read_bytes())
    binary = bytearray(payload)
    if len(document["meshes"]) != 1 or len(document["meshes"][0]["primitives"]) != 1:
        raise ValueError("Expected one mesh with one primitive")
    primitive = document["meshes"][0]["primitives"][0]
    position_accessor = document["accessors"][primitive["attributes"]["POSITION"]]
    positions = accessor_array(document, binary, primitive["attributes"]["POSITION"]).astype(np.float64)
    if position_accessor.get("normalized"):
        positions /= NORMALIZED_MAX[position_accessor["componentType"]]
    triangles = accessor_array(document, binary, primitive["indices"]).reshape(-1, 3)
    kept_triangles = triangles[(positions[triangles, 1] >= below).all(axis=1)]
    used = np.unique(kept_triangles)
    remap = np.full(len(positions), -1, dtype=np.int64)
    remap[used] = np.arange(len(used))

    views = {document["accessors"][index]["bufferView"] for index in primitive["attributes"].values()}
    new_views = {}
    for view_index in views:
        view = document["bufferViews"][view_index]
        members = [document["accessors"][i] for i in primitive["attributes"].values()
                   if document["accessors"][i]["bufferView"] == view_index]
        stride = view.get("byteStride") or element_bytes(members[0])
        start = view.get("byteOffset", 0)
        records = np.frombuffer(bytes(binary[start:start + stride * members[0]["count"]]), dtype=np.uint8)
        data = records.reshape(-1, stride)[used].tobytes()
        binary.extend(b"\0" * (-len(binary) % 4))
        new_views[view_index] = {"buffer": 0, "byteOffset": len(binary), "byteLength": len(data),
                                 **({"byteStride": view["byteStride"]} if "byteStride" in view else {})}
        binary.extend(data)
    for view_index, view in new_views.items():
        document["bufferViews"][view_index] = view
    for index in primitive["attributes"].values():
        document["accessors"][index]["count"] = len(used)
    raw = accessor_array(document, binary, primitive["attributes"]["POSITION"])
    position_accessor["min"] = raw.min(axis=0).tolist()
    position_accessor["max"] = raw.max(axis=0).tolist()

    index_type, component = (np.uint16, 5123) if len(used) < 65536 else (np.uint32, 5125)
    data = remap[kept_triangles].astype(index_type).reshape(-1).tobytes()
    binary.extend(b"\0" * (-len(binary) % 4))
    document["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(data)})
    binary.extend(data)
    document["accessors"][primitive["indices"]] = {"bufferView": len(document["bufferViews"]) - 1,
                                                   "componentType": component, "count": len(kept_triangles) * 3,
                                                   "type": "SCALAR"}
    # Old vertex and index bytes are now unreferenced; repack only live views.
    live = sorted({accessor["bufferView"] for accessor in document["accessors"]}
                  | {image["bufferView"] for image in document.get("images", []) if "bufferView" in image})
    packed = bytearray()
    mapping = {}
    for old_index in live:
        view = document["bufferViews"][old_index]
        chunk = binary[view.get("byteOffset", 0):view.get("byteOffset", 0) + view["byteLength"]]
        packed.extend(b"\0" * (-len(packed) % 4))
        mapping[old_index] = len(mapping)
        view["byteOffset"] = len(packed)
        packed.extend(chunk)
    document["bufferViews"] = [document["bufferViews"][i] for i in live]
    for accessor in document["accessors"]:
        accessor["bufferView"] = mapping[accessor["bufferView"]]
    for image in document.get("images", []):
        if "bufferView" in image:
            image["bufferView"] = mapping[image["bufferView"]]
    output.write_bytes(pack_glb(document, bytes(packed)))
    print(f"Kept {len(kept_triangles):,} of {len(triangles):,} triangles and {len(used):,} of "
          f"{len(positions):,} vertices; {output.stat().st_size:,} bytes")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--below", type=float, required=True)
    args = parser.parse_args()
    crop(args.source, args.output, args.below)


if __name__ == "__main__":
    main()
