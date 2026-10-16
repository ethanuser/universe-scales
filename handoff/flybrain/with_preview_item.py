#!/usr/bin/env python3
"""Run a lab command with a temporary Fruit Fly Brain item, restoring exact bytes.

The items job owns the actual dataset. This helper permits reviewing the pending
model without committing dataset changes or invoking the broken full builder.
  ./venv/bin/python handoff/flybrain/with_preview_item.py -- \
      node scripts/model_lab.cjs shot /tmp/flybrain "Fruit Fly Brain" --views rest,side,top --bg dark
"""
import json
import math
from pathlib import Path
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
ITEM = {"name": "Fruit Fly Brain", "value": 0.0008,
        "source": "https://zenodo.org/records/10877326",
        "description": "Approximately 800 micrometres across the FlyWire v783 sampled neuronal processes, including both optic lobes and lamina. This is a small morphology sample, not the full synapse graph."}


def main(command):
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("Pass a command after --")
    originals = {}
    try:
        for relative in ["exports/json/dimensions/length.json", "exports/frontend/length.yaml", "data/length.yaml"]:
            path = ROOT / relative
            payload = path.read_bytes()
            doc = json.loads(payload) if path.suffix == ".json" else yaml.safe_load(payload)
            existing = next((item for item in doc["items"] if item["name"] == ITEM["name"]), None)
            if existing is not None:
                if not math.isclose(float(existing["value"]), ITEM["value"], rel_tol=1e-9):
                    raise ValueError("Existing Fruit Fly Brain value differs from the model's 800 µm reference; resolve calibration before review")
                continue
            originals[path] = payload
            doc["items"].append(ITEM)
            path.write_text(json.dumps(doc, indent=2) + "\n" if path.suffix == ".json" else yaml.safe_dump(doc, sort_keys=False))
        return subprocess.run(command, cwd=ROOT, check=False).returncode
    finally:
        for path, payload in originals.items():
            path.write_bytes(payload)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
