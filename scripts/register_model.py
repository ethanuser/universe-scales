#!/usr/bin/env python3
"""Register a processed GLB in the model registry, replacing an older model if asked.

    python3 scripts/register_model.py ENTRY.json MODEL.glb [--dimension length]

ENTRY.json is a registry entry (id, source, author, license, license_url, matches,
geometry, presentation, note, processing, ...). An optional "replaces": "<old id>"
removes that entry and deletes its GLB when nothing else uses it. File stats
(bytes, sha256, triangle_count, ...) are recomputed from MODEL.glb. When the entry
has a "sketchfab_uid", the curated Sketchfab manifest entry for the same item is
updated so `sketchfab_models.py` stays consistent with the registry.
"""

import argparse
import json
import shutil
from pathlib import Path

from fetch_model_assets import check_matches, inspect_glb, write_json

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "content/visualizations/models.json"
MODELS = ROOT / "content/visualizations/models"
LICENSE_SLUGS = {"CC-BY-4.0": "by", "CC0-1.0": "cc0"}
DEFAULTS = {"license_files": ["licenses/CC-BY-4.0.txt"], "geometry": "mesh",
            "volume_semantics": "cubic_linear_equivalent_approximation", "closed_volume_checked": False}


def register(entry_path, glb_path, dimension):
    entry = json.loads(Path(entry_path).read_text())
    data = Path(glb_path).read_bytes()
    replaces = entry.pop("replaces", None)
    model_id = entry["id"]
    destination = MODELS / f"{model_id}.glb"
    entry["src"] = str(destination.relative_to(ROOT))
    for key, value in DEFAULTS.items():
        entry.setdefault(key, value)
    if entry.get("license") == "CC0-1.0":
        entry["license_files"] = ["licenses/CC0-1.0.txt"]
    entry.update(inspect_glb(data))

    registry = json.loads(REGISTRY.read_text())
    old = {model["id"]: model for model in registry["models"]}
    removed = [old[replaces]] if replaces in old else []
    models = [model for model in registry["models"] if model["id"] not in {model_id, replaces}]
    position = next((index for index, model in enumerate(registry["models"])
                     if model["id"] in {model_id, replaces}), len(registry["models"]))
    models.insert(min(position, len(models)), entry)
    check_matches(models)

    if Path(glb_path).resolve() != destination.resolve():
        shutil.copyfile(glb_path, destination)
    for model in removed:
        stale = ROOT / model["src"]
        if stale != destination and stale.exists() and not any(m["src"] == model["src"] for m in models):
            stale.unlink()
            print(f"Deleted unused {stale.relative_to(ROOT)}")
    registry["models"] = models
    write_json(REGISTRY, registry)
    print(f"Registered {model_id}: {entry['bytes']:,} bytes, {entry['triangle_count']:,} triangles"
          + (f" (replaced {replaces})" if removed else ""))

    uid = entry.get("sketchfab_uid")
    manifest_path = MODELS / f"sketchfab-{dimension}.json"
    if uid and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        name = entry["matches"][dimension][0]
        curated = {"id": model_id, "name": name, "uid": uid,
                   "author": entry["author"].removesuffix(" on Sketchfab"),
                   "license": LICENSE_SLUGS.get(entry["license"], entry["license"])}
        if entry.get("presentation"):
            curated["presentation"] = entry["presentation"]
        curated["note"] = entry["note"]
        index = next((i for i, item in enumerate(manifest["models"]) if item["name"] == name), None)
        if index is None:
            manifest["models"].append(curated)
        else:
            manifest["models"][index] = curated
        write_json(manifest_path, manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("entry")
    parser.add_argument("glb")
    parser.add_argument("--dimension", default="length")
    args = parser.parse_args()
    register(args.entry, args.glb, args.dimension)


if __name__ == "__main__":
    main()
