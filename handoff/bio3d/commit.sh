#!/bin/sh
# Lead-only convenience: run outside the restricted sandbox. No push/branch change.
set -eu
cd "$(dirname "$0")/../.."
test "$(git branch --show-current)" = 'codex/bio3d'
git add -- AGENTS.md content/visualizations/models.json \
  content/visualizations/models/validation.json \
  content/visualizations/models/cod-9011577-graphene-spacing.glb \
  content/visualizations/models/pdb-*.glb \
  content/visualizations/models/sources/cod-9011577-graphene-spacing.md \
  content/visualizations/models/sources/pdb-*.md \
  content/visualizations/models/sources/bio3d \
  scripts/prepare_bio3d_sources.py scripts/build_bio3d_models.py \
  scripts/build_graphene_spacing.py scripts/preview_bio3d_cpu.py \
  scripts/audit_bio3d_models.mjs tests/test_bio3d_models.py handoff/bio3d
git diff --cached --check
git -c user.name=Codex -c user.email=noreply@openai.com commit \
  -m 'Add nine calibrated molecular and lattice models from structural coordinates' \
  -m 'Preserve CC0 PDB/COD coordinates, biological assemblies and physical nm calibration; add offline builders, provenance, geometry previews and integration handoff.' \
  -m 'Co-Authored-By: Codex <noreply@openai.com>'
