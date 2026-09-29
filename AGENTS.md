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
| Procedural models (molecules, hair, solar system, field), distance bracket | `js/experiences/procedural-models.js` |
| Orbital atom and animated electromagnetic-wave models | `js/experiences/atomic-models.js`, `wave-models.js` |
| Other explorers | `motion.js`, `perception.js`, `audio.js` (+ `*-math.js`) |
| Model registry (runtime + provenance) | `content/visualizations/models.json` |
| Model files and licenses | `content/visualizations/models/` (see its README) |
| Dataset source of truth | `dataset/raw/` → built into `exports/` and `data/` (see `DATASET_PIPELINE.md`) |

Scripts: `scripts/sketchfab_models.py` (search/stage/import Sketchfab), `scripts/preview_glb.cjs`
(headless textured GLB preview), `scripts/model_lab.cjs` (audit, screenshots and contact
sheets of the production renderer; see Model lab), `scripts/register_model.py` (add/replace a registry entry),
`scripts/audit_glb_geometry.mjs` (bounds), `scripts/build_earth_moon_model.py` (orbital diagrams),
`scripts/build_everest_dem.py` (Mapzen elevation tiles → opaque sea-level block), `scripts/texture_padding.py`
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

## Model lab (use this to see what you changed)

`scripts/model_lab.cjs` serves the repo itself and drives the production renderer in
headless Chromium, so no dev server or visible browser is needed:

```sh
node scripts/model_lab.cjs audit                       # every Length item: size vs listed value, load, triangles
node scripts/model_lab.cjs shot /tmp/lab "Carbon Atom" --views rest,front,side --bg dark --time 1.5
node scripts/model_lab.cjs sheet /tmp/lab/all.png      # contact sheet of all models, red = flagged
node scripts/model_lab.cjs explorer /tmp/lab "Solar System"   # the real explorer after the camera settles
```

`audit` reports each model's rendered extent in units of its listed value (1.00x means it
renders at the listed size) and flags anything over 1.3x, under 0.6x, wider than its
`layout_width_factor`, or failing to load, plus 404s and page errors. **Rule: a model should
render close to its listed size**; models much larger than their value overlap neighbours
and break framing while scrolling. Where a quantity is a radius (e.g. an atom's radius),
list the diameter the model shows. `model-review.html` is the same view for humans
(`?item=&view=&bg=&time=&zoom=`), and `window.modelLab` is its automation API.

After editing JS/CSS run `python3 scripts/bump_versions.py`; it sets every `?v=` to the
file's content hash (HTML and nested module imports), so nothing is served stale and no
module loads twice under two version strings. `--check` fails if any are stale.

## Adding or replacing a model (proven workflow)

1. Find candidates: `SSL_CERT_FILE=/etc/ssl/cert.pem python3 scripts/sketchfab_models.py search 'query'`
   (CC-BY or CC0, downloadable). Prefer scientific sources (NIH 3D, PDB, scans) when they look good.
2. Stage outside the repo with the owner's token file (never commit or print the token):
   `... sketchfab_models.py stage --token-file ~/.config/universe-scales/sketchfab-token --uid UID --output-dir /tmp/x`
3. Clean and simplify with `npx @gltf-transform/cli@4.5.0` (weld, simplify, prune, resize, quantize).
   Do not use Draco/Meshopt/KTX2/WebP: the vendored GLTFLoader has no decoders.
   Budget: ideally ≤ 1.5 MB, ≤ 60k triangles, textures ≤ 1024 px.
4. Look at it: `node scripts/preview_glb.cjs model.glb out.png` (then view the PNG), and after
   registering, `node scripts/model_lab.cjs shot /tmp/lab "Item name" --views rest,side` and `audit`.
5. Copy the GLB to `content/visualizations/models/`, add a registry entry (copy an existing
   Sketchfab entry's shape; `bytes`/`sha256`/stats come from `inspect_glb` in
   `scripts/fetch_model_assets.py`), write an honest `note`, and credit the author.
6. Check it in the browser with `?item=`, run the checks below, commit.

## Checks

```sh
node --test tests/*.test.cjs tests/*.test.mjs
./venv/bin/python -m unittest discover -s tests -p "test_*.py"   # venv deps: requirements.txt
python3 scripts/fetch_model_assets.py --verify
python3 scripts/bump_versions.py --check
node scripts/model_lab.cjs audit
```

## Known issues and traps

- **Dataset rebuild drift.** The full builder still changes unrelated dimensions, and
  `verify_dataset.py` fails on the pre-existing `torque.yaml` selected-count mismatch.
  Use `./venv/bin/python -m scripts.dataset.rebuild_dimension length` for a Length-only
  edit; it stages a full build and merges only the requested dimension. Do not use a
  full rebuild or restore unrelated outputs as a workaround.
- The repo is ~720 MB, mostly `images/` originals (some over 30 MB). Runtime loads thumbnails, but
  GitHub's recommended repo limit is 1 GB.
- `models.json` mixes runtime fields with provenance (hashes, processing). Keep both; the
  site only reads a few fields.
- Hidden browser panes can pause `requestAnimationFrame`; inspect the visible explorer
  after the page and camera settle, not immediately after navigation.
- Never hand-edit `?v=` numbers; run `python3 scripts/bump_versions.py`.
- Import policy is CC-BY/CC0 only (`ALLOWED_LICENSES` in `sketchfab_models.py`). The owner's chosen
  sand grain (Sketchfab 8e7caaef…, "Sand Grain scaled to 75mm") is CC BY-NC-SA, so it was not imported;
  the CC-BY Sand Atlas micro-CT grain remains. Lincoln Financial Field and the suggested Everest
  model were not downloadable. The field is now a procedural NFL-sized diagram; Everest is derived
  from Mapzen elevation tiles with Mapzen/USGS attribution.

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

## 2026-09-27 continuation

- SI-prefix notation is capped at three significant figures; the notation toggle
  cycles through scientific, mathematical, human-readable, and SI modes.
- Hydrogen is bounded at one Bohr radius (about 32.3% enclosed probability), and
  carbon has a labeled independent-electron 1s²2s²2p² orbital diagram. Seven
  wavelength anchors were added to Length, with separate Markdown plaques.
- The animated EM wave uses E/B unit-vector labels. The bacterium is a CC-BY
  illustrative pilose rod, with species uncertainty stated. The mitochondrion
  and football field use procedural illustrations instead of the prior cartoon
  cutaway/stadium scan. Everest uses a 602 kB DEM-derived opaque terrain block.
  The Statue of Liberty now uses a hand-modeled CC-BY asset with an illustrative
  pedestal; its 46.05 m data value still measures the statue alone.
- `node --test tests/*.test.cjs tests/*.test.mjs` passes, as does model verification.
  Python dataset and Sketchfab tests pass separately under `venv` and system
  Python respectively; the combined invocation lacks Pillow or PyYAML in one
  environment. Full dataset verification still fails on the baseline torque drift.

## 2026-09-28 (Claude)

- Model lab + content-hash versioning (see above). Precise bounds for calibration/grounding.
- Size rule applied: hydrogen and carbon are listed as diameters (106 pm, 140 pm) and drawn
  inside those spheres (32.3% and 53.8% of electron probability inside); EM waves show one
  wavelength; Statue of Liberty is e-sfera's whole monument at 92.99 m ground to torch.
  Remaining intentional exceptions: DNA (one helical turn is 1.7x its 2 nm width) and the
  virus (spikes beyond the calibrated 91 nm envelope).
- New procedural models: iron-56 nucleus (Atomic Nucleus), Milky Way (Galaxy Diameter),
  Milky Way-Andromeda distance diagram. Andromeda Distance corrected to 2.37e22 m (2.5 Mly).
- Data note for the owner: Heliosphere is listed at 2.4e14 m (about 1,600 au) although the
  heliopause is about 120 au out; left unchanged pending a decision on the definition.
- Planet labels are placed at fixed offsets and hidden by priority (no per-frame shuffling);
  model annotations fade out below 240 px and item names below 12 px text.

## Open work (as of 2026-09-27)

- Improve the schematic mitochondrion's internal folds if a small CC-BY/CC0
  scientific model is found. The current procedural cutaway is intentionally not
  claimed to be a specimen reconstruction.
- Consider a neuron model if the owner still wants it; no new neuron asset was
  imported in this session.
- Investigate the full-build drift and make the Python test dependencies coherent.
