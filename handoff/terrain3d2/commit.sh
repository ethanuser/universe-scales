#!/bin/sh
# Run outside the sandbox after the lead's browser review. No push or branch change.
set -eu
cd "$(dirname "$0")/../.."
test "$(git branch --show-current)" = codex/terrain3d2
git add -- AGENTS.md content/visualizations/models.json \
  content/visualizations/models/validation.json \
  content/visualizations/models/terrain3d2-*.glb \
  content/visualizations/models/sources/terrain3d2-*.md \
  content/visualizations/models/sources/terrain3d2 \
  scripts/build_terrain3d2_models.py scripts/audit_terrain3d_models.mjs \
  scripts/preview_terrain3d_cpu.py tests/test_terrain3d2_models.py handoff/terrain3d2
git commit -m "Add five terrain and Earth-event models from public scientific data" \
  -m "Preserve native geographic scale, surveyed vector identities and stereo retrieval gaps; document ten skipped targets and pending browser review.

Co-Authored-By: Codex <noreply@openai.com>"
