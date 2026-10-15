#!/usr/bin/env python3
"""Group the CC0 Innerscene bicycle's existing wheel meshes at their axles.

No geometry is generated or altered. Both wheels rotate while the drivetrain
stays still, depicting freewheeling rather than a pedaling simulation.
"""

import argparse
import hashlib
from pathlib import Path

from fetch_model_assets import pack_glb, read_glb

SOURCE_SHA256 = "1c9f5b5f95a869b273c4e2023c37392d22872286efe8e0cd7f640146611ce802"


def rig(source, destination):
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError("Unexpected bicycle source; re-inspect its wheel geometry before rigging")
    document, binary = read_glb(data)
    nodes = document["nodes"]
    roots = document["scenes"][document.get("scene", 0)]["nodes"]
    if document.get("animations") or document.get("skins") or any(node.get("children") for node in nodes):
        raise ValueError("Expected the reviewed static, flat bicycle scene")
    wheels = []
    moved = set()
    for side in ("Front", "Rear"):
        parts = [i for i in roots if nodes[i].get("name", "") in
                 {f"{side} hub", f"{side} rim", f"{side} tire"}
                 or nodes[i].get("name", "").startswith(f"{side} spoke")]
        if len(parts) != 31:
            raise ValueError(f"Unexpected {side} wheel component count")
        hub = next(nodes[i] for i in parts if nodes[i]["name"] == f"{side} hub")
        pivot = hub["translation"].copy()
        for index in parts:
            node = nodes[index]
            if "matrix" in node:
                raise ValueError("Expected separate translation/rotation transforms")
            node["translation"] = [value - origin for value, origin in
                                   zip(node.get("translation", [0, 0, 0]), pivot)]
        wheels.append(len(nodes))
        nodes.append({"name": f"{side}WheelRotor", "translation": pivot, "children": parts})
        moved.update(parts)
    housing = len(nodes)
    nodes.append({"name": "Housing", "children": [i for i in roots if i not in moved]})
    document["scenes"] = [{"name": "Coasting bicycle", "nodes": [housing, *wheels]}]
    document["scene"] = 0
    destination.write_bytes(pack_glb(document, binary))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    rig(args.source, args.destination)
