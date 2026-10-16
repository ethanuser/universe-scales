#!/bin/sh
# Run outside the restricted agent sandbox. Never pushes or changes branches.
set -eu
cd "$(dirname "$0")/../.."
test "$(git branch --show-current)" = 'codex/neuron'
git add -- AGENTS.md \
  content/visualizations/models.json \
  content/visualizations/models/sources/neuron-model.md \
  content/visualizations/models/sources/neuron \
  content/visualizations/models/neuromorpho-feldmeyer-neuron-109111.glb \
  content/visualizations/models/validation.json \
  index.html js/experiences/models.js js/experiences/neuron-animation.js \
  js/experiences/organelle-models.js js/experiences/procedural-models.js \
  js/model-review.js model-review.html \
  scripts/build_reconstructed_neuron.py scripts/prepare_neuron_source.py \
  scripts/preview_neuron_cpu.py tests/neuron-animation.test.mjs \
  tests/test_reconstructed_neuron.py handoff/neuron
git diff --cached --check
git -c user.name=Codex -c user.email=noreply@openai.com commit \
  -m 'Replace stylized neuron with complete archived morphology and axonal pulse' \
  -m 'Import CC BY NeuroMorpho NMO_109111 with measured radii, traced soma outline, offline provenance and path-distance electrical annotation. Record the required 0.8 mm dataset update and blocked browser verification in the handoff.' \
  -m 'Co-Authored-By: Codex <noreply@openai.com>'
