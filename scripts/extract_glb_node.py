#!/usr/bin/env python3
"""Keep one named GLB subtree, retaining its ancestors' authored transforms.

Run glTF Transform `prune` on the result to remove unused meshes and buffers.
This selects existing geometry; it does not infer or manufacture missing parts.
"""

import argparse
from pathlib import Path

from fetch_model_assets import pack_glb, read_glb


def extract(source, output, name):
    document, binary = read_glb(source.read_bytes())
    if document.get("skins") or document.get("animations"):
        raise ValueError("Animated or skinned assets need a rig-aware extraction")
    matches = [i for i, node in enumerate(document["nodes"]) if node.get("name") == name]
    if len(matches) != 1:
        raise ValueError(f"Expected one node named {name!r}, got {len(matches)}")
    parents = {child: i for i, node in enumerate(document["nodes"]) for child in node.get("children", [])}
    current = matches[0]
    while current in parents:
        parent = parents[current]
        document["nodes"][parent]["children"] = [current]
        document["nodes"][parent].pop("mesh", None)
        current = parent
    document["scenes"] = [{"nodes": [current]}]
    document["scene"] = 0
    output.write_bytes(pack_glb(document, binary))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("name")
    args = parser.parse_args()
    extract(args.source, args.output, args.name)
