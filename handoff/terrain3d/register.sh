#!/bin/sh
# Re-register this delivery after retaining main's models.json during integration.
set -eu
cd "$(dirname "$0")/../.."
for entry in handoff/terrain3d/*.entry.json; do
    model_id=$(basename "$entry" .entry.json)
    python3 scripts/register_model.py "$entry" "content/visualizations/models/$model_id.glb"
done
