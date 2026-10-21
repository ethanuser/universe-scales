#!/usr/bin/env python3
"""Rig reviewed CC0 imports using their existing parts and authored coordinates.

Usage: python3 scripts/prepare_angular_imports.py SOURCE_DIR OUTPUT_DIR
SOURCE_DIR contains angular-clock-source.glb and angular-walnut-spin-source.glb.
No vertex, triangle, material, texture, or source rest transform is changed.
"""

import argparse
import hashlib
from pathlib import Path

from fetch_model_assets import pack_glb, read_glb


SOURCES = {
    "clock": "9ee2b833e5f8fcd475a94cab28d6a77668298161082d83ef2a8cb07e32d1fa21",
    "walnut-spin": "2d674bc105e77743cd571fb6b0d75874c410109e626d64897a30242dde591107",
}


def pivot_parts(nodes, children, names, pivot, name):
    parts = [i for i in children if nodes[i].get("name") in names]
    if {nodes[i]["name"] for i in parts} != set(names):
        raise ValueError(f"Missing reviewed parts for {name}")
    for i in parts:
        if "matrix" in nodes[i]:
            raise ValueError("Expected source TRS transforms")
        nodes[i]["translation"] = [value - origin for value, origin in
                                   zip(nodes[i].get("translation", [0, 0, 0]), pivot)]
        children.remove(i)
    index = len(nodes)
    nodes.append({"name": name, "translation": list(pivot), "children": parts})
    return index


def prepare(source, output, kind):
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCES[kind]:
        raise ValueError(f"Source changed: re-inspect the {kind} asset before rigging")
    document, binary = read_glb(data)
    if document.get("animations") or document.get("skins"):
        raise ValueError("Expected reviewed static source")
    roots = document["scenes"][document.get("scene", 0)]["nodes"]
    if len(roots) != 1:
        raise ValueError("Expected one source assembly")
    nodes = document["nodes"]
    assembly = nodes[roots[0]]
    children = list(assembly["children"])
    by_name = {nodes[i].get("name"): nodes[i] for i in children}
    if kind == "clock":
        pivot = by_name["Clock hand hub"]["translation"]
        rotors = [pivot_parts(nodes, children, {f"{hand} hand"}, pivot, f"{hand}HandRotor")
                  for hand in ("Hour", "Minute")]
    else:
        pivot = by_name["Spindle"]["translation"]
        parts = {"Record centre label", "Vinyl record", "Rubber platter mat"}
        parts.update(name for name in by_name if name and name.startswith("Record groove"))
        if len(parts) != 10:
            raise ValueError("Unexpected source record component count")
        rotors = [pivot_parts(nodes, children, parts, pivot, "RecordRotor")]
    housing = len(nodes)
    nodes.append({"name": "Housing", "children": children})
    assembly["children"] = [housing, *rotors]
    output.write_bytes(pack_glb(document, binary))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for kind in SOURCES:
        destination = args.output_dir / f"innerscene-{kind}-angular.glb"
        prepare(args.source_dir / f"angular-{kind}-source.glb", destination, kind)
        print(f"{destination.name}: {destination.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
