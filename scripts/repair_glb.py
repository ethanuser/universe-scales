#!/usr/bin/env python3
"""Fix common glTF validator errors in place and refresh registry stats.

    python3 scripts/repair_glb.py content/visualizations/models/X.glb [...]

Removes empty top-level arrays (EMPTY_ENTITY), adds min/max to POSITION accessors
that lack them, and renormalizes float NORMALs (zero-length ones from degenerate
triangles become +Y). Positions and materials are unchanged.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_model_assets import inspect_glb, pack_glb, read_glb, write_json  # noqa: E402
from texture_padding import accessor_array  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "content/visualizations/models.json"


def repair(path):
    document, binary = read_glb(path.read_bytes())
    changes = []
    for key in [key for key, value in document.items() if isinstance(value, list) and not value]:
        del document[key]
        changes.append(f"removed empty {key}")
    for mesh in document.get("meshes", []):
        for primitive in mesh["primitives"]:
            index = primitive["attributes"].get("POSITION")
            accessor = document["accessors"][index] if index is not None else None
            if accessor is not None and ("min" not in accessor or "max" not in accessor):
                values = accessor_array(document, binary, index).astype(np.float64)
                accessor["min"] = values.min(axis=0).tolist()
                accessor["max"] = values.max(axis=0).tolist()
                changes.append(f"bounds for accessor {index}")
    binary = bytearray(binary)
    fixed = set()
    for mesh in document.get("meshes", []):
        for primitive in mesh["primitives"]:
            index = primitive["attributes"].get("NORMAL")
            if index is None or index in fixed or document["accessors"][index]["componentType"] != 5126:
                continue
            accessor = document["accessors"][index]
            values = accessor_array(document, binary, index).astype(np.float64)
            length = np.linalg.norm(values, axis=1)
            bad = np.abs(length - 1) > 5e-4
            if not bad.any():
                continue
            values[bad & (length > 1e-6)] /= length[bad & (length > 1e-6), None]
            values[length <= 1e-6] = (0.0, 1.0, 0.0)
            view = document["bufferViews"][accessor["bufferView"]]
            stride = view.get("byteStride", 12)
            offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
            for row, vector in zip(np.flatnonzero(bad), values[bad].astype("<f4")):
                start = offset + int(row) * stride
                binary[start:start + 12] = vector.tobytes()
            fixed.add(index)
            changes.append(f"normalized {int(bad.sum())} normals in accessor {index}")
    if changes:
        path.write_bytes(pack_glb(document, bytes(binary)))
    return changes


def main(paths):
    registry = json.loads(REGISTRY.read_text())
    for name in paths:
        path = Path(name).resolve()
        changes = repair(path)
        print(f"{path.name}: {', '.join(changes) or 'no changes'}")
        if not changes:
            continue
        relative = str(path.relative_to(ROOT))
        for model in registry["models"]:
            if model.get("src") == relative:
                model.update(inspect_glb(path.read_bytes()))
    write_json(REGISTRY, registry)


if __name__ == "__main__":
    main(sys.argv[1:])
