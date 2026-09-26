# Agent Handoff Guide

Start here if you are an AI agent (Codex, Claude, ...) or a new contributor picking
up this repo. It is the shortest path to being productive; the longer READMEs linked
below hold the details. Keep this file current when you change workflows.

## What this is

A static site (no build step, GitHub Pages) that visualizes quantities across many
dimensions. Each dimension has a log plot plus, for some, an interactive "explorer".
Current focus: the **Length size explorer**, a continuous camera from the Planck
length to the observable universe that shows each item as a calibrated 3D model,
a procedural model, or a photo.

Run it locally from the repo root:

```sh
python3 -m http.server 8000
# open http://localhost:8000/?dimension=length&item=Astronomical%20Unit
```

`?item=<exact item name>` deep-links to one item (first load only).
Bump the `?v=` query of any JS/CSS file you change in `index.html`; browsers cache hard.

## Map of the code

| Area | Files |
| --- | --- |
| App shell, plot, units, images, URL | `js/script.js`, `js/plot.js`, `js/formatting.js`, `js/constants.js`, `js/editor.js` |
| Explorer framework (mode registry, detail panel, picker, deep link) | `js/experiences/controller.js`, `controls.js`, `math.js` |
| Length/Area/Volume explorer (camera, layout, SVG labels) | `js/experiences/spatial.js`, `journey.js` |
| 3D models (loading, calibration, rotation, picking, bracket, labels) | `js/experiences/models.js` |
| Other explorers | `motion.js`, `perception.js`, `audio.js` (+ `*-math.js`) |
| Model registry (runtime + provenance) | `content/visualizations/models.json` |
| Model files and licenses | `content/visualizations/models/` (see its README) |
| Dataset source of truth | `dataset/raw/` → built into `exports/` and `data/` (see `DATASET_PIPELINE.md`) |

Scripts: `scripts/sketchfab_models.py` (search/stage/import Sketchfab), `scripts/preview_glb.cjs`
(headless textured preview), `scripts/audit_glb_geometry.mjs` (bounds), `scripts/build_earth_moon_model.py`
(orbital diagrams), `scripts/fetch_model_assets.py --verify` (offline registry check).

## How a Length model is drawn

`models.js` picks a registry entry whose `matches.length` contains the exact item name
(or a procedural entry in `proceduralLength`). On load it removes `remove_nodes`,
applies `pre_rotation`, measures the bounding box, and scales so the calibrated extent
equals the item's value:

- `measure_axis` `x|y|z` chooses the extent (default: longest). `measure_fraction` says the
  calibrated part is that fraction of it (e.g. 0.8 for a body without its tail).
  `reference_size` overrides both with an explicit model-unit length.
- `yaw`/`pitch`/`roll` set the resting pose (degrees). Users can drag-rotate; the model
  springs back. The lowest point sits on the ground line.
- `layout_width_factor`, `focus_scale_factor`, `display_extent_factor` adjust spacing and framing
  for models much wider than their calibrated length.
- Material overrides: `tint`, `color_gain`, `roughness`, `metalness`, `opaque`, `double_sided`,
  `emissive` (+ `emissive_intensity`), and `environment` (reflection strength from a studio
  room map; metals look black without it).
- `distance_bracket: {"bodies": [A, B]}` (orbital diagrams) adds a white U-shaped bracket
  under two named sphere nodes: vertical lines tangent to the facing edges and a joining
  line below, part of the model so it rotates with it, drawn at a constant 1.4 px width.
  Body names are SVG labels projected above each body, so they stay upright.

The model's projected convex hull (including the bracket) is its hover/drag/click area.

## Adding or replacing a model (proven workflow)

1. Find candidates: `SSL_CERT_FILE=/etc/ssl/cert.pem python3 scripts/sketchfab_models.py search 'query'`
   (CC-BY or CC0, downloadable). Prefer scientific sources (NIH 3D, PDB, scans) when they look good.
2. Stage outside the repo with the owner's token file (never commit or print the token):
   `... sketchfab_models.py stage --token-file ~/.config/universe-scales/sketchfab-token --uid UID --output-dir /tmp/x`
3. Clean and simplify with `npx @gltf-transform/cli@4.5.0` (weld, simplify, prune, resize, quantize).
   Do not use Draco/Meshopt/KTX2/WebP: the vendored GLTFLoader has no decoders.
   Budget: ideally ≤ 1.5 MB, ≤ 60k triangles, textures ≤ 1024 px.
4. Look at it: `node scripts/preview_glb.cjs model.glb out.png` (then view the PNG).
5. Copy the GLB to `content/visualizations/models/`, add a registry entry (copy an existing
   Sketchfab entry's shape; `bytes`/`sha256`/stats come from `inspect_glb` in
   `scripts/fetch_model_assets.py`), write an honest `note`, and credit the author.
6. Check it in the browser with `?item=`, run the checks below, commit.

## Checks

```sh
node --test tests/*.test.cjs tests/*.test.mjs
python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/fetch_model_assets.py --verify
```

## Known issues and traps

- **Dataset rebuild drift.** `scripts/dataset/build_dataset.py` no longer reproduces the committed
  exports: a full rebuild removes items from about 11 other dimensions (e.g. FLOPs loses the
  PS3 Cell processor). `verify_dataset.py` also fails on a clean checkout (`torque.yaml selected count
  mismatch`). Until someone investigates, after editing one dimension, keep only that dimension's
  outputs plus the three `exports/json/*.jsonl` diffs, and `git checkout` the rest.
  The 2026-09-26 Virus/Football Field edits patched their two rows into the SQLite files directly.
- The repo is ~720 MB, mostly `images/` originals (some over 30 MB). Runtime loads thumbnails, but
  GitHub's recommended repo limit is 1 GB.
- `models.json` mixes runtime fields with provenance (hashes, processing). Keep both; the
  site only reads a few fields.
- The browser pane in Claude's desktop app pauses `requestAnimationFrame` while hidden, so camera
  animations do not settle there; screenshots can show mid-flight framing.

## Session log

- 2026-09-26 (Claude): 3D distance bracket for Earth-Moon/AU (replacing the SVG overlay), `?item=`
  deep links, red blood cell rests unrotated, metallic Eiffel Tower (`environment`), procedural
  light wave for Visible Light Wavelength, recolored-Sun Betelgeuse, Virus → SARS-CoV-2 (91 nm),
  Football Field corrected to 91.44 m (100 yd), `scripts/preview_glb.cjs`, junk files removed.
  See the git log for the rest of this session's model replacements.
