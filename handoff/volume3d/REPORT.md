# volume3d: public-source Volume models

Date: 2026-10-29. Branch: `codex/volume3d`. Work remains uncommitted for the lead,
as instructed by the round's known git/Chromium sandbox restriction. No commit,
browser launch, push, merge, rebase or other branch operation was attempted.

Added four registry entries covering five of the previous 31 gaps. Production
coverage is now **29 of 55 Volume observations**, leaving 26 photo-only. The
complete bounded review is in [ledger.json](ledger.json), with one disposition
for every previous gap, including reused-source rejections and new searches.
The earlier source-completion ledger remains a historical snapshot.

| Entry / observations | Source and geometry | Calibration | New GLB |
| --- | --- | --- | --- |
| `volume3d-sugar-scan` / Sugar cube volume | Arkify sugar-cube scan, exterior surface | Closed exterior bulk-envelope volume | 982,808 B; 53,660 triangles |
| `volume3d-nih-influenza` / Influenza virion volume | NIAID PathogenAR colored cutaway | Explicit equivalent-volume span | 1,035,680 B; 70,841 triangles |
| `volume3d-nih-coronavirus` / SARS-CoV-2 virion volume | Existing NIAID GLB, unchanged | Explicit equivalent-volume span | Reused 682,504 B binary; 50,522 triangles |
| `volume3d-classic-bathtub` / Bathtub, Bathtub volume | renderartestudio ceramic clawfoot tub | Explicit capacity illustration / equivalent-volume span | 1,182,256 B; 57,391 triangles |

The three new binaries total 3,200,744 bytes. Each is below 1.2 MB and has no
Draco, meshopt, KTX2, WebP or external resource requirement. No model geometry
was created from scratch. Only source selection, internal-shell exclusion,
decimation, standard resource embedding/cleanup and runtime uniform scaling were
used. Source colors and proportions are retained; no decorative recoloring or
in-model caveat labels were added. `display_label` is unset on all four entries.

## Measurement conventions

**Only the sugar cube is enclosed-volume calibrated.** Its source has a large
exterior shell and four tiny reverse-wound interior pore shells. The importer
checks all 204 removed source vertices are inside the exterior by ray parity,
checks opposite winding, and checks the removed signed volume is only
0.00007209940995768923 of the exterior volume (about 0.00721%). It retains the
outside surface and reduces 107,320 to 53,660 triangles. No holes are patched,
no caps are introduced and no replacement shape is synthesized.

The simplified exterior is a consistently oriented single closed shell with
no boundary edges, duplicate faces or degenerate triangles. Its enclosed volume
is 3866.2990517839316 source units³; `reference_size` is its cube root,
15.695138326976915. The normalized enclosed volume is
0.9999999999999918. This is a **bulk envelope including internal pore air**, not
solid-sucrose material volume, and the original scanned specimen was larger
than the catalog's representative 1 cm³ example. Topology and vertex containment
checks do not certify absence of all self-intersections.

The current brief explicitly allows an existing public model to use an
equivalent-volume span when an enclosed-volume calibration is unavailable.
This resolves the earlier ledger's missing-scale obstacle for **illustration**,
without claiming a new measurement: each proxy's longest native span is
normalized to one, so its displayed span is V^(1/3). Notes and source files
state this convention. The strict helper rejects the existing SARS-CoV-2 mesh
on duplicate triangles and the tub on open/nonmanifold topology; the influenza
cutaway likewise is not a membrane-bounded solid suitable for the datum.

The tub shows an empty exterior prop, not a measured 150 L water body. Its
ceramic/metal volume and basin capacity are not inferred. The two virus entries
are teaching illustrations, not unmodified single-particle reconstructions;
neither spike extent nor cutaway material volume is equated with particle
envelope volume. These three entries have `closed_volume_checked: false` and
`cubic_linear_equivalent_approximation` semantics. No browser audit should treat
them as unit-enclosed-volume meshes.

## Primary sources and rights

- Sugar scan: [Arkify source](https://sketchfab.com/3d-models/sugar-cube-3d-scan-no-texture-0227084e92ed4dc79e48e0bf271edd32),
  [API](https://api.sketchfab.com/v3/models/0227084e92ed4dc79e48e0bf271edd32).
  License slug `by`, author `arkify`, checked at acquisition. Source description
  documents a 0.6 by 0.8 inch specimen and 0.2 mm scan/processing resolution.
- Tub: [renderartestudio source](https://sketchfab.com/3d-models/classic-bathtub-7427e2c0c32c44b89deb058f6583742a),
  [API](https://api.sketchfab.com/v3/models/7427e2c0c32c44b89deb058f6583742a).
  License slug `by`, checked at acquisition. No capacity or metric dimensions
  are asserted by the author; its educational capacity-proxy scope is explicit.
- Influenza: [NIH 3DPX-013373](https://3d.nih.gov/entries/3DPX-013373),
  [entry API](https://3d.nih.gov/api/entries/3DPX-013373),
  [selected GLB](https://3d.nih.gov/api/submissions/17244/runs/2e7bbb59-6917-4533-b94e-a14afe44f578/output-files/385370).
  NIH metadata explicitly identifies the selected submission as `CC-BY` without
  a version number; the new entry preserves that uncertainty instead of asserting
  a license version. The cutaway's original scientific colors remain intact.
- Coronavirus: [NIH 3DPX-013323](https://3d.nih.gov/entries/3DPX-013323),
  [entry API](https://3d.nih.gov/api/entries/3DPX-013323). Existing binary and
  original import provenance are retained. The new Volume entry records the
  source's `CC-BY` wording without a version assumption; the older Length entry
  is unchanged. The primary page describes segmentation-informed reshaping,
  envelope regularization and authored spike placement.

All four have separate notes at
`content/visualizations/models/sources/<id>.md`. Source/license detail-API
snapshots in `research/` contain only relevant public metadata; account contact
fields and temporary download credentials are excluded. `imports.json` pins
archive/staged/source/output hashes; the final `.entry.json` files include final
asset hashes and the exact runtime settings.

Influenza alternatives are recorded in the ledger: the
[Glasgow Visualising Viruses collection](https://researchdata.gla.ac.uk/1220/)
has an explicit CC BY 4.0 grant, but range-reading its ZIP central directories
showed 3ds Max scenes and a roughly 345 MB uncompressed print STL. No model
member was acquired. A small CC BY student influenza model was staged and
CPU-previewed outside the repo; the colored NIH scientific cutaway was selected
for clearer presentation. Neither rejected alternative is bundled.

## Reproduction

No packages were installed into the shared venv or elsewhere. Existing cached
glTF Transform 4.5.0, meshoptimizer and glTF Validator were used from
`/Users/ethan/.npm/_npx/a6797f7ff67bb1f2/node_modules` (`MODULE_ROOT` below).

Stage the two Sketchfab assets outside the repository using the existing tool:

```sh
SSL_CERT_FILE=/etc/ssl/cert.pem ./venv/bin/python scripts/sketchfab_models.py stage --token-file ~/.config/universe-scales/sketchfab-token --uid 0227084e92ed4dc79e48e0bf271edd32 --output-dir /tmp/volume3d-stage --texture-size 1024
SSL_CERT_FILE=/etc/ssl/cert.pem ./venv/bin/python scripts/sketchfab_models.py stage --token-file ~/.config/universe-scales/sketchfab-token --uid 7427e2c0c32c44b89deb058f6583742a --output-dir /tmp/volume3d-stage --texture-size 1024
```

Download the selected NIH GLB above as `/tmp/volume3d-stage/nih-influenza.glb`.
Its SHA-256 must be
`2fb62fa7544538e6d304901b0e690abfc8beffc9babf5b1772c67641eb2c54e8`.
The importer rejects any unreviewed input hash.

```sh
node scripts/prepare_volume3d_imports.mjs /tmp/volume3d-stage MODULE_ROOT
node scripts/register_volume3d.mjs
node scripts/register_volume3d.mjs --check
node scripts/audit_volume3d.mjs
./venv/bin/python scripts/render_earth3d_previews.py handoff/volume3d/previews --entry handoff/volume3d/volume3d-sugar-scan.entry.json --entry handoff/volume3d/volume3d-nih-influenza.entry.json --entry handoff/volume3d/volume3d-nih-coronavirus.entry.json --entry handoff/volume3d/volume3d-classic-bathtub.entry.json --size 600
./venv/bin/python scripts/preview_volume3d_small.py
```

For integration, prefer copying the assets/source files and running
`node scripts/register_volume3d.mjs`: it preserves unrelated registry text and
reuses the coronavirus binary. The final `.entry.json` files are also supplied
for the lead's merge helper. Do not use `register_model.py` on the coronavirus
reuse entry: that tool copies a GLB to a new ID-based filename. Both tub labels
belong to the same entry and binary. No entry replaces an existing model.

## Validation and visual review

- **262 Node tests passed.** Python: **169 run, one existing skip**, successful.
- Full registry glTF Validator 2.0.0-dev.3.10: **zero errors**, including all four
  entries. All three new GLBs and reused coronavirus have **zero warnings**.
  Nine unchanged assets retain existing warnings. See `validation-summary.json`.
  The shared full-site `validation.json` was left byte-identical to HEAD.
- Asset verification passes for **216 registry asset entries / 228 exact-name
  matches**; some entries intentionally share binaries. Version check reports
  zero stale references. No runtime JS/CSS changed, so no version bump needed.
- `loader-audit.json` uses the vendored production GLTFLoader, exact per-vertex
  bounds, registry scaling and resting poses. All four pass the 0.6–1.3 extent
  rule and declared layout width. Sugar normalized enclosed volume is one;
  proxy native-longest-span normalization is one. NIH sources omit explicit
  normals, and the loader correctly supplies its glTF flat-shading fallback.
- Rest/side CPU previews and direct 48/96/160 px CPU canvases are in `previews/`.
  All were visually inspected. The tub pose exposes its empty basin; influenza
  exposes the source cutaway. The influenza simplification was refined to retain
  more source surface detail while keeping its GLB near 1 MB.
- These are **CPU orthographic previews**, not production screenshots. They do
  not certify browser lighting, perspective, picking, explorer overlap, mobile
  gestures or actual device performance. Per the brief, known Chromium/git
  sandbox failures were not retried. The lead should run:

```sh
node scripts/model_lab.cjs spatial-models OUT "Sugar cube volume" "SARS-CoV-2 virion volume" "Influenza virion volume" "Bathtub" "Bathtub volume" --dimension volume
```

Repeat with `--mobile`; inspect rest/rotated views and notes in the redesigned
runtime before publishing.

## Remaining scope

All original registry entries are structurally unchanged; this is an additive
four-entry patch. Dataset values, descriptions/plaques, exports, photos, runtime
JS/CSS, index, model-review files and model_lab were not changed. **No dataset
change is required for these entries.** The pre-existing untracked `venv` symlink
was left alone. No sub-agents were used.

The remaining 26 decisions are itemized in `ledger.json`; this is a bounded
review, not a claim of internet-wide exhaustion. Existing authored Length
diagrams, the Sun used as Betelgeuse, arbitrary terrain clipping blocks and
catalog galaxy glyphs do not become eligible Volume surfaces merely because
their files are already registered. Prior rejected pyramid and bathtub leads
were not reacquired. New USGS Tahoe bathymetry and NOAA ETOPO leads are recorded,
but no unreviewed scientific mesh or artificial depth exaggeration was added.
