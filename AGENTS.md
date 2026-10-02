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
| Particle-scale measurement diagrams (not hard particle boundaries) | `js/experiences/particle-scale-models.js` |
| Catalog-positioned nearby-space diagrams | `js/experiences/nearby-space-models.js` |
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
- `display_label` optionally qualifies an explorer/review heading without renaming the
  dataset item or breaking exact-name matches and deep links (e.g. a putative structure).
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
with the drawn model. `softPoints: true` opts into a shared, locally generated soft
circular sprite (`model-points.js`); hover overlays preserve it. Other clouds and
their shared materials are unchanged. See the header of `procedural-models.js`.

The model's projected convex hull (including the bracket) is its hover/drag/click area.

## Model lab (use this to see what you changed)

`scripts/model_lab.cjs` serves the repo itself and drives the production renderer in
headless Chromium, so no dev server or visible browser is needed:

```sh
node scripts/model_lab.cjs audit                       # every Length item: size vs listed value, load, triangles
node scripts/model_lab.cjs coverage --gap 1 --json      # provenance, photo fallbacks and logarithmic gaps
node scripts/model_lab.cjs shot /tmp/lab "Carbon Atom" --views rest,front,side --bg dark --time 1.5
node scripts/model_lab.cjs sheet /tmp/lab/all.png      # contact sheet of all models, red = flagged
node scripts/model_lab.cjs explorer /tmp/lab "Solar System"   # the real explorer after the camera settles
```

`audit` reports each model's on-screen extent (the larger of width and height at its resting
pose) in units of its listed value (1.00x means it renders at the listed size) and flags anything over 1.3x, under 0.6x, wider than its
`layout_width_factor`, or failing to load, plus 404s and page errors. **Rule: a model should
render close to its listed size**; models much larger than their value overlap neighbours
and break framing while scrolling. Where a quantity is a radius (e.g. an atom's radius),
list the diameter the model shows. `model-review.html` is the same view for humans
(`?item=&view=&bg=&time=&zoom=`), and `window.modelLab` is its automation API.

`coverage` uses the production registry but does not load every mesh or certify
accuracy. It lists absent models, missing references/notes, unclassified
`representation` fields, large assets and adjacent gaps in decades. Use it to
plan new anchors, then run `audit` and inspect actual explorer screenshots.
A survey-window diagram is not a member catalog or a measured structure boundary;
a measurement diagram must not be labeled as a literal particle surface.

After editing JS/CSS run `python3 scripts/bump_versions.py`; it sets every `?v=` to the
file's content hash (HTML and nested module imports), so nothing is served stale and no
module loads twice under two version strings. It also adds missing hashes to local
first-party ES imports; vendored imports stay unchanged. `--check` fails if any are stale.

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

## 2026-09-29 (Claude)

- Camera hops between items now `glide` (fixed 0.75-1.7 s smootherstep by pixel distance) instead of the
  spring; similar-sized neighbors previously slid a whole object width almost instantly. Similar-sized
  items keep a 0.2 (was 0.08) clearance. The renderer's near plane now hugs the nearest model, which
  removes z-fighting on thin decals.
- Football field: `football-model.js` (yard numbers, goalposts, dimension brackets), merged by material.
- Procedural `organelle-models.js`: lengthwise-cut mitochondrion (17 lamellar cristae) and a pyramidal
  neuron with an animated action potential (animation registry: `model-animation.js`; live mV readout).
  The Neuron dataset text now describes the neuron plus local dendrites (about 100 um), which is what the
  model spans.
- E and B labels carry vector arrows. Pillars of Creation (NASA/STScI) added.
- Sourcing results: no usable public model exists for Orion, Tarantula or Carina nebulae, Proxima, the
  Heliosphere or the Oort Cloud (build procedurally). Geography: Manhattan (OSM + Mapzen, value corrected to 21.6 km) and
  the Panama Canal strip (8x vertical exaggeration) were added via `scripts/build_manhattan_block.py` and
  `build_panama_canal_block.py`. Skipped as inaccurate at the size rule: Great Wall (route ~3,000 km of
  21,196), Amazon, Marathon.

## 2026-09-30 (Codex)

- Goalposts now have connecting gooseneck elbows, closed ground pads and protective
  sleeves; the old support stopped short of the crossbar and stood outside the turf.
- Added Proxima's distance diagram (Gaia DR3 distance quoted by Lauer et al. 2025)
  and a 16-member Local Group scene from McConnachie's catalog. Galaxy glyphs are
  enlarged eightfold, not physically sized. Reviewed the Jan-2021 FITS subset and
  corrected WLM/NGC 6822 distances and Leo I's coordinates. References and assumptions:
  `content/visualizations/models/sources/nearby-space-models.md`.
- Added a 672 kB Orion GLB sampled from the credited NASA/ESA Hubble field. The image
  stays 13 ly across within the listed ~25 ly region; a lower bracket indicates that
  full span. Only sky-plane color/position is observed; the shallow blister depth
  is authored from O'Dell et al. 2009, not NASA's inaccessible fly-through geometry.
  Rebuild with `scripts/build_orion_model.py`; provenance is `sources/orion-model.md`.
- Fixed optional callout offsets/leader lines keep Local Group labels from collapsing
  over the central galaxies. `labelAxis: {axis, length, minPixelLength}` hides depth
  annotations until their projected span is legible; Orion uses a side-on depth cue.
- GLB packing now handles valid nonindexed point/line primitives. Model source and
  separate scientific-basis links both appear in explorer details when provided.
- Visually inspected rest/side and actual-explorer views with the model lab. All
  157 Node tests and 21 Python tests passed; model asset/hash verification passed.
  No Length data/plaque text was changed. The audit has no page/load errors; its only
  flagged resting poses remain the documented DNA/virus size exceptions.
- Luna critic final execution/accuracy scores after three visual refinement passes:
  Proxima 8/9, Local Group 7/8, Orion 9/8. Local Group's central satellite callouts
  remain somewhat crowded; inferred nebula depth is explicitly not measured geometry.

## 2026-09-30 next model batch (Codex)

- Added an 810 kB Tarantula point cloud from ESO/R. Fosbury (ST-ECF)'s CC-BY image.
  The published angular field and distance calibrate a ~951 ly viewing aperture;
  sky-plane color/position is observed, depth is explicitly authored, not tomography.
  Rebuild with `scripts/build_tarantula_model.py`; provenance is `sources/tarantula-model.md`.
- Added AU-coordinate Oort Cloud and heliosphere scenes in `outer-solar-models.js`.
  Oort shows a flattened inner component and a diffuse outer sample, not cataloged
  comets. Heliosphere is a nose-side cutaway with a radial ruler and upwind arrow;
  no downstream boundary or physical tail length is claimed. References/assumptions:
  `content/visualizations/models/sources/outer-solar-models.md`.
- Corrected two mismatched Length definitions and values: Oort now explicitly uses
  the representative upper-range 200,000 AU diameter (2.991957414e16 m); heliosphere
  uses a 240 AU nose-region proxy (3.5903488968e13 m), not a full-tail extent.
  Existing plaque prose was retained except the necessary definition fixes.
  `scripts.dataset.rebuild_dimension length` regenerated Length only.
- Diffuse clouds opt into a generated 32px soft point sprite (`model-points.js`).
  Shader/texture behavior is local and tested; the rest of the model materials remain unchanged.
- Visually reviewed rest/side and actual-explorer screenshots. The whole-Length
  audit reports 52/66 modeled, 14 photo-only, no page/load errors. Node tests: 163;
  Python tests: 24; asset verification: 45 GLBs/53 exact-name registry matches.
- Researched Cosmicflows/SDSS/Virgo scientific catalogs; no new supercluster data
  were bundled because usable selection/redistribution rights remain unresolved.
- Independent Luna critic scores (execution/accuracy): Tarantula 8/8; after a
  second visual refinement, Oort 9/8 and heliosphere 9/8. All reached the requested
  8/10 threshold. Ruler-label separation in the heliosphere is optional remaining polish.

## 2026-09-30 Carina and horizon batch (Codex)

- Added Carina as a 735 kB, 10,400-triangle image-derived surface from ESO/J. Emerson/
  M. Irwin/J. Lewis's CC-BY VISTA field. The 193 by 157 ly image stays calibrated
  within a 300 ly context bracket. It is explicitly a gently bowed 2.5D sheet,
  not a reconstructed gas-density volume; a granular point-cloud prototype was
  replaced after visual review. Rebuild: `scripts/build_carina_model.py`;
  provenance: `sources/carina-model.md`.
- Corrected Carina's erroneous 3e20 m span to an approximate 300 ly
  (2.83821914177424e18 m) from NASA, retaining its plaque except the opening
  size definition. Only Length outputs were rebuilt.
- Added a 750 kB, 9,120-triangle Observable Universe cutaway with actual WMAP
  nine-year ILC sky data. `scripts/build_observable_universe_model.py` validates
  the original Galactic NESTED FITS, averages 64 child pixels into Nside=64,
  and samples an embedded equirectangular texture with tested HEALPix mapping.
  The original 24 MB FITS is a temporary build input, not a hosted asset.
- The textured 45.6 Gly last-scattering shell and ~46.5 Gly particle-horizon
  guides retain proportional present-distance radii. The smooth amber-rimmed
  cone is an authored viewing cut, not a hole or edge in the universe. Polar
  mesh UVs preserve Galactic directions and unwrap the longitude seam. Reference:
  `sources/observable-universe-model.md`. The existing diameter is unchanged;
  qualifiers and the plaque's misleading superluminal-recession explanation
  were corrected without a wholesale prose rewrite.
- Visually inspected rest/side and actual-explorer views and iterated with Luna
  critics: Carina execution/accuracy 8/8 after three passes; horizon 8/9 after
  two. Audit: 54/66 modeled, 12 photo-only; no page/load errors. All 163 Node
  and 34 Python tests pass. Asset verification: 47 GLBs/55 exact-name matches;
  content-hash version check passes. Baseline SQLite ResourceWarnings remain.
- A CC-BY scientist-authored CF2 nearby-Universe mesh was staged outside the repo,
  but not imported: its +/-80 Mpc/h density field is not Laniakea's boundary.
  No verified CC-BY/CC0 geometry for the original 2014 basin was found. Do not
  calibrate the wider field as a Laniakea model or invent a boundary around it.

## Open work (as of 2026-09-30, after the horizon batch)

- Intentional size exceptions flagged by `model_lab audit`: DNA (one helical turn is 1.7x its
  2 nm width) and the virus (spikes beyond the 91 nm envelope).
- The CC BY-NC-SA sand grain was declined; keep the existing CC-BY grain.
- Photo-only Length items include large-scale structures, route-length geography
  and subatomic cases without well-defined hard sizes. Carina and Observable
  Universe now have explicitly diagrammatic, calibrated assets.
- Cosmicflows-4 has a downloadable Laniakea watershed grid, but its data-reuse terms
  need confirmation. Virgo/Sloan need a documented member selection and distance basis.
- Investigate the full-build dataset drift (use `scripts.dataset.rebuild_dimension` meanwhile).

## 2026-09-30 route batch (Codex)

- Added three rotatable geographic GLBs with `scripts/build_route_models.py`:
  Boston Marathon course/terrain (638 kB), partial Amazon mainstem/basin (880 kB),
  and the mapped Great Wall network on a true-sized Earth (1.15 MB). Each is
  below 1.5 MB and 34k triangles, embeds its textures, and has no decoder/runtime
  source-data dependency. Inspect with `model_lab.cjs shot` and `explorer`.
- Route/inventory length is not geographic extent. No coordinate geometry is
  stretched to the catalog value: each has a separate straightened total-length
  ruler. The Amazon's selected 3,053 km reach ends inland, not at the Atlantic;
  tributaries are separate context. The Great Wall data is incomplete community
  mapping, not the official heritage inventory or one continuous wall.
- Boston's OSM relation has one connected 265-way start-to-finish path. Its
  42.417 km road-centerline sum is not the certified 42.195 km shortest running
  line. Drape on the rendered terrain triangles, not finer DEM samples that can
  be buried by the coarse mesh. Relief is 12x and bare-earth, not road grade.
- Minimum Length definition/source fixes only: Amazon now uses the NASA/ESA
  approximate 6,400 km estimate; Great Wall uses the reported 21,196.18 km
  combined walls-and-trenches survey total, explicitly not meter-level precision.
  Marathon remains 42,195 m. Only Length outputs were rebuilt.
- Geometry/source/license/rebuild details: `sources/route-models.md`. Compact
  GeoJSON inputs live under `content/visualizations/models/sources/routes/`.
  OSM-derived inputs retain ODbL and their machine-readable derivative databases;
  these are separate from the project's CC0 quantitative facts. Natural Earth
  land is the existing `content/visualizations/land.geojson`, public domain.
- Three visual refinement passes and separate Luna critics: all final execution
  and accuracy scores 8/10. Remaining limitation: exactly edge-on terrain/rulers
  compress naturally; Amazon's inland-end label is culled in the smaller scrolling
  view but remains visible in the isolated/rest review and stated in the note.
- Verification: 163 Node tests, 42 Python tests, 50 self-contained GLBs/58 exact-name
  matches. Length audit: 57/66 modeled, no page/load errors; only the previously
  documented DNA/virus resting-size exceptions. Content-hash check passes.

## 2026-10-01 remaining Length batch (Codex)

- Added five explicit particle-scale measurement diagrams in
  `particle-scale-models.js`: derived Planck length, HERA effective quark-radius
  upper limit, proton rms charge radius, classical electron radius, and a 1 MeV
  neutrino wavelength. They do not claim solid particle boundaries. The proton
  profile is schematic and continues beyond its rms marker. Definitions and
  primary sources: `sources/particle-scale-models.md`.
- Added SDSS DR17 catalog windows for Virgo (937 galaxies, 30 kB) and Sloan
  (7,998 galaxies, 200 kB). Native coordinates stay in comoving Mpc; calibration
  uses the item's reference length, not a stretched bounding box. The cuts are
  survey windows, not structure/member boundaries, explicitly labeled on stage.
  BOSS/eBOSS use the recommended NOQSO classification/redshift/warning fields;
  legacy spectra use their regular fields. Source CSVs and exact queries are
  retained. Rebuild offline with `build_large_scale_catalog_models.py
  --catalog-dir content/visualizations/models/sources/catalogs --output-dir /tmp/x`.
- Added a 40 kB Hercules-Corona Borealis evidence diagram: actual Swift
  spectroscopic GRB directions (42 at z=1.6-2.1), a separate comoving-distance
  inset, and a calibrated reported-extent ruler. It is not invented wall geometry.
  The 16 amber events are inside the broad 2020 sky guide, not the original
  2014 one-eighth-sky membership. The explorer title says "Putative ... structure".
  The immutable October 1 catalog snapshot and extraction/bias qualifications
  are in `sources/catalogs/` and `sources/grb-structure-model.md`.
- Corrected mismatched Length definitions/values for Virgo, Laniakea, Sloan,
  the putative GRB structure and particle scales; retained existing plaque prose
  except fact/definition corrections. Renamed the misleading intrinsic
  "Neutrino" size to "1 MeV Neutrino Wavelength" and copied its original/thumbnail
  to the new slug. Rebuilt Length only, not unrelated dimensions.
- Laniakea remains photo-only. `build_laniakea_model.py` can stage the credited
  CC-BY CF4 figure as a reference preview, but its metadata is intentionally
  non-importable. A flat article figure is not a calibrated 3D basin; the public
  grid's redistribution terms remain unverified. See `sources/laniakea-model.md`.
- Added `model_lab.cjs coverage --gap 1 --json` and `model_coverage.cjs` for
  model/provenance inventory and largest adjacent log gaps. `window.modelLab.catalog()`
  exposes the same inventory. This supports planning 200-300 meaningful anchors,
  not scientific approval or artificial gap-filling. Review source rights,
  quantity definitions, calibration, rest/rotated views and actual explorer views
  before importing; popularity/votes cannot replace those checks.
- Independent Luna critics after two refinement passes: all five particle
  diagrams execution/accuracy 8/9, Virgo and Sloan 8/8, GRB diagram 8/9.
  Own visual checks used isolated/rest/side and settled production explorers.
  Corrected a caption-transform bug: Python uses Three.js intrinsic XYZ ordering
  and maps pitch/yaw/roll explicitly; regression-tested with mixed-axis rotation.
- Verification: all 170 Node and 65 Python tests pass; 53 self-contained GLBs
  and 61 exact-name registry matches verify. Whole-Length audit: 65/66 visualized,
  only Laniakea photo-only, no load/page errors. Only the documented DNA/virus
  size exceptions remain flagged. Content hashes and diff whitespace pass.
  Pre-existing SQLite ResourceWarnings and full-dataset torque drift remain.
