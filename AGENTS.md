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
| 3D models (loading, calibration, rotation, picking, overlays) | `js/experiences/models.js` |
| Procedural models (hydrogen, molecules, hair, light wave, solar system) and the distance bracket | `js/experiences/procedural-models.js` |
| Other explorers | `motion.js`, `perception.js`, `audio.js` (+ `*-math.js`) |
| Model registry (runtime + provenance) | `content/visualizations/models.json` |
| Model files and licenses | `content/visualizations/models/` (see its README) |
| Dataset source of truth | `dataset/raw/` → built into `exports/` and `data/` (see `DATASET_PIPELINE.md`) |

Scripts: `scripts/sketchfab_models.py` (search/stage/import Sketchfab), `scripts/preview_glb.cjs`
(headless textured GLB preview), `scripts/screenshot_explorer.cjs` (headless screenshots of explorer
items after the camera settles), `scripts/register_model.py` (add/replace a registry entry),
`scripts/audit_glb_geometry.mjs` (bounds), `scripts/build_earth_moon_model.py` (orbital diagrams),
`scripts/build_terrain_block.py` (terrain → block diagram on sea level), `scripts/texture_padding.py`
(fix atlas seams), `scripts/fetch_model_assets.py --verify` (offline registry check).

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
  under two named sphere nodes: vertical lines drop from each body's center (distances are
  center to center) to a joining line below. It is part of the model, so it rotates with it.

Overlay conventions (set on any node's `userData`, including glTF `extras`):
`screenLine: {axis, length}` draws a box at a constant 1.4 px width; `label` (+ `labelClass`)
draws upright SVG text at the node; `outline` + `sphere` circle a unit-sphere node with a thin
line (so sub-pixel planets stay findable); `pointSize: {max, perPixel}` scales a point cloud
with the drawn model. See the header of `procedural-models.js`.

The model's projected convex hull (including the bracket) is its hover/drag/click area.

## Adding or replacing a model (proven workflow)

1. Find candidates: `SSL_CERT_FILE=/etc/ssl/cert.pem python3 scripts/sketchfab_models.py search 'query'`
   (CC-BY or CC0, downloadable). Prefer scientific sources (NIH 3D, PDB, scans) when they look good.
2. Stage outside the repo with the owner's token file (never commit or print the token):
   `... sketchfab_models.py stage --token-file ~/.config/universe-scales/sketchfab-token --uid UID --output-dir /tmp/x`
3. Clean and simplify with `npx @gltf-transform/cli@4.5.0` (weld, simplify, prune, resize, quantize).
   Do not use Draco/Meshopt/KTX2/WebP: the vendored GLTFLoader has no decoders.
   Budget: ideally ≤ 1.5 MB, ≤ 60k triangles, textures ≤ 1024 px.
4. Look at it: `node scripts/preview_glb.cjs model.glb out.png` (then view the PNG), and after
   registering, `node scripts/screenshot_explorer.cjs /tmp/shots "Item name"` with the site served.
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
  animations do not settle there; use `scripts/screenshot_explorer.cjs` instead.
- `models.js` imports `./procedural-models.js?v=N`: bump N (and `models.js?v=` in `index.html`)
  when the procedural module changes.
- Import policy is CC-BY/CC0 only (`ALLOWED_LICENSES` in `sketchfab_models.py`). The owner's chosen
  sand grain (Sketchfab 8e7caaef…, "Sand Grain scaled to 75mm") is CC BY-NC-SA, so it was not imported;
  the CC-BY Sand Atlas scan remains. Lincoln Financial Field and the suggested Everest model are not
  downloadable, so CC-BY alternatives were used.

## Session log

- 2026-09-26 (Claude): 3D distance bracket for Earth-Moon/AU (replacing the SVG overlay), `?item=`
  deep links, red blood cell rests unrotated, metallic Eiffel Tower (`environment`), procedural
  light wave for Visible Light Wavelength, recolored-Sun Betelgeuse, Virus → SARS-CoV-2 (91 nm),
  Football Field corrected to 91.44 m (100 yd), `scripts/preview_glb.cjs`, junk files removed.
  Later the same day: bracket lines switched to center-to-center with thin body outlines; hydrogen
  cloud cut at its 95% sphere (3.15 Bohr radii) with the Bohr radius marked; light wave with E (red)
  and B (blue) arrows and labels; SEM-style procedural hair; date-accurate procedural solar system
  (JPL elements); weathered Eiffel Tower; football field (Milton Frank Stadium scan); Everest as a
  block diagram on sea level; DNA deduplicated (3.4 → 0.37 MB); new Statue of Liberty item (46.05 m)
  with a cropped replica scan (`scripts/crop_glb.py`). See the git log for details.

## Open work (as of 2026-09-26)

- Owner still wants a higher-quality bacterium (more pili/flagella), a more accurate mitochondrion
  (more cristae), and a neuron model (item is 100 µm, described as a cell body). A sourcing run was
  in progress; its candidates (if finished) are in the session scratchpad under `models/cells2/`,
  otherwise redo the search with `scripts/preview_glb.cjs` comparisons and register with
  `scripts/register_model.py`.
- Owner's chosen sand grain is CC BY-NC-SA; import only if the owner accepts that license.
- The owner's last message ended with "the neuron" (cut off); confirm what was wanted.
