# earth3d handoff — 2026-10-16

Branch: `codex/earth3d`. Changes are intentionally **uncommitted** for the lead. No push, merge, rebase, branch changes or writes to sibling worktrees were performed. The lead explicitly documented Chromium and git-commit sandbox failures and asked not to spend time retrying them, so neither was retried here.

## Delivered

Fourteen new self-contained GLBs, 10.03 MB total; largest 2.53 MB. All scale uniformly. No dataset, exports, data, images or runtime JS/CSS were edited. No Python or npm packages were installed. The existing `venv` symlink was already untracked when work began and is not part of this delivery.

Eight dimensioned original illustrations cover balls, card, phone, paper, silicon and the VLT mirror. Four models are real licensed downloads: RISD's reconstructed egg scan, AF267's 747-8, denys4624's Komodo, and hank2's Hindenburg. Only the egg is a specimen scan; the others are explicitly authored illustrations. License and public author fields were verified directly against each Sketchfab API model endpoint and retained under `sources/earth3d-imports/`.

The Gateway Arch is an original exterior loft from NPS's weighted-catenary centroid and tapered triangular cross sections. It is not the simplified downloaded arch candidate. Meteor Crater is an actual elevation grid, with equal horizontal and vertical metres and a clearly identified display crop. No synthetic bowl, depth correction or vertical exaggeration was added.

| Item | Final ID / entry JSON | kB | Triangles |
| --- | --- | ---: | ---: |
| A4 Paper | [earth3d-a4-paper.entry.json](earth3d-a4-paper.entry.json) | 1.4 | 4 |
| Basketball | [earth3d-basketball.entry.json](earth3d-basketball.entry.json) | 1054.0 | 16,128 |
| Boeing 747-8 | [earth3d-boeing-747-8.entry.json](earth3d-boeing-747-8.entry.json) | 1302.1 | 45,018 |
| Credit Card | [earth3d-credit-card.entry.json](earth3d-credit-card.entry.json) | 64.3 | 208 |
| Elephant Bird Egg | [earth3d-elephant-bird-egg.entry.json](earth3d-elephant-bird-egg.entry.json) | 937.6 | 44,994 |
| Gateway Arch | [earth3d-gateway-arch.entry.json](earth3d-gateway-arch.entry.json) | 167.4 | 3,082 |
| Hindenburg | [earth3d-hindenburg.entry.json](earth3d-hindenburg.entry.json) | 2531.1 | 69,340 |
| Komodo Dragon | [earth3d-komodo-dragon.entry.json](earth3d-komodo-dragon.entry.json) | 874.0 | 16,264 |
| Meteor Crater | [earth3d-meteor-crater.entry.json](earth3d-meteor-crater.entry.json) | 637.3 | 29,762 |
| Silicon Wafer | [earth3d-silicon-wafer.entry.json](earth3d-silicon-wafer.entry.json) | 97.7 | 2,056 |
| Smartphone | [earth3d-smartphone.entry.json](earth3d-smartphone.entry.json) | 120.4 | 980 |
| Table Tennis Ball | [earth3d-table-tennis.entry.json](earth3d-table-tennis.entry.json) | 366.4 | 16,128 |
| Tennis Ball | [earth3d-tennis.entry.json](earth3d-tennis.entry.json) | 1174.5 | 16,128 |
| Very Large Telescope Mirror | [earth3d-vlt-mirror.entry.json](earth3d-vlt-mirror.entry.json) | 701.5 | 37,632 |

All entries are additions; none replaces an existing model, so no `replaces` field is required. Existing registry entries and source assets were retained. `sketchfab-length.json` has the four corresponding curated additions. A small `register_model.py` change supports an explicit `sketchfab_author` username so full display credits remain in the registry while the import manifest retains the exact API username required for source verification. The license-evidence test checks that mapping.

## Scientific and representation limits

- Sporting-ball diameters follow ITTF / ITF standards or a manufacturer's size-7 circumference. Texture, felt seams and leather channels are original illustrative artwork; they do not claim measured manufacturing details.
- Credit Card uses the 85.60 × 53.98 × 0.76 mm ID-1 envelope. Decorative artwork is fictitious and unpersonalized. No bank branding, account numbers or personal information was added.
- Smartphone uses Apple's iPhone 16 body envelope, 147.6 × 71.6 × 7.8 mm. The simplified camera protrusions, corners, screen graphics and colors are authored details; body depth excludes the camera protrusion, as in Apple's body specification. No interior is claimed.
- A4 is a double-sided, zero-thickness sheet surface, exactly 210 × 297 mm. ISO 216 does not specify a paper stock. Adding a fictitious or enlarged thickness would misrepresent the standard; this version makes no thickness claim.
- Silicon wafer is bare silicon, not an invented chip layout. SVM SV031 supplies 300 mm diameter, 775 µm nominal thickness, 1 mm notch depth and 90° included angle. The subtle notch is intentionally tiny at normal viewing sizes. Reflections require the production studio environment and cannot be verified by the CPU renderer.
- VLT M1 uses ESO's 8.2 m diameter, 1 m bore, 175 mm nominal meniscus thickness, 28.8 m curvature radius and −1.004616 conic constant. Rear geometry is a constant axial offset, explicitly approximate. There is no invented support-cell or actuator geometry. Studio reflections are illustrative.
- RISD accession 132.32 is reassembled from fragments and **presumed** to be an elephant-bird egg. The model note preserves those qualifications. Its surface-area-weighted principal long axis is rigidly aligned before calibration. It is uniformly scaled to the catalog's representative 33 cm; that does not claim this specimen was measured as 33 cm or definitively assigned to a species.
- The 747's span/length ratio is ~0.898, close to Boeing's 68.4/76.3. This is an artist's GeoFS exterior; local details and livery are illustrative. No independent axis stretching.
- Komodo is an authored 3DS Max animal, calibrated to the existing 2.6 m representative adult-male nose-to-tail length. It is not a scan, measured individual or anatomical reconstruction.
- Hindenburg's original neutral envelope material is brightened for legibility. Its historical tail markings remain contextual parts of the source. No crash vignette was imported. Internal framework/gas bags remain artist-authored, not a certified structural survey. Overall length follows the original U.S. Commerce Department report (803.8 ft, approximately 245 m).
- The Arch's numerical loft yields about 192.0236 m width and 192.0240 m height, agreeing with NPS's 630 ft. Section dimensions, equations, alignment and ground clipping are documented in its source note. Foundations, interior, seams and observation windows are omitted.
- Meteor Crater has a 1.44 km context aperture around the existing 1,186 m reference. The square is not the crater boundary. The bundled 121 × 121 terrain grid is sampled at 12 m; sampled relief is ~187 m, without forcing it to the published rounded ~180 m depth. Source URLs/hashes and sampling method are retained. AWS omitted source-granule headers, so do not describe this as a specific lidar survey or epoch. Palette colors and flat display underside do not claim observed strata or subsurface geometry.

Each model has an individual provenance document at `content/visualizations/models/sources/<id>.md`, with primary dimensional sources, credits, license and limitations. Original generated geometry/artwork is CC0; downloaded models remain CC BY 4.0. USGS terrain retains its public-domain status and Mapzen/Tilezen/USGS credit.

## Visual review and verification

Viewed every delivered model at rest and with the orthographic camera rotated a quarter turn, using `scripts/render_earth3d_previews.py`. That renderer reads actual GLB hierarchy/transforms, normalized quantized attributes, normals, base-color textures and a depth buffer. It applies the registry's calibration and resting pose. The quarter-camera view retains the resting pose; it is not an exact reproduction of model-lab's `side` preset. CPU previews do not implement production PBR/environment reflections, perspective, overlays, interaction or UI.

- [All-model CPU contact sheet](previews/overview.png).
- Individual full-size rest/quarter-camera pairs: `previews/<id>.png`.
- Exact CPU bounds and normalized resting extents: [previews/geometry-audit.json](previews/geometry-audit.json). All 14 resting extents lie inside 0.6–1.3×. This is an orthographic geometry check, **not** production `model_lab audit` or browser approval.
- Node: `node --test tests/*.test.cjs tests/*.test.mjs` — **224 passed**.
- Python: `./venv/bin/python -m unittest discover -s tests -p 'test_*.py'` — **88 tests, OK, one existing skip**. Seven new tests check isotropic spheres, card proportions, mirror bore/curvature/normals, Arch height/span, terrain scale and side-wall winding, all delivered extents/budgets/hashes, and retained license/author evidence. Existing NumPy/skimage deprecation and SQLite ResourceWarnings remain.
- `python3 scripts/fetch_model_assets.py --verify` — **passes**, 78 registry models / 88 exact-name matches.
- `python3 scripts/bump_versions.py --check` — **0 stale references**. No JS/CSS edits, so a version rewrite was unnecessary.
- Khronos validator, run through the required `validate-models.cjs` command: **all 14 new GLBs have zero errors and zero warnings**. [gltf-validation.json](gltf-validation.json) retains their complete reports. The full command exits 1 because the pre-existing `em-mitochondrion-jurkat` model has 17 errors; other pre-existing model warnings also remain. That asset belongs to the mito job and was not changed. The command's unrelated aggregate `validation.json` rewrite was restored to its exact starting bytes; this handoff retains only this job's validation results.
- `git diff --check` — passes.

**Production review is still required:** model-lab rest/side shots, the settled explorer with neighbors, production size/picking/grounding audit, environment reflections and mobile performance. Chromium and git commits were not retried because of the lead's explicit sandbox instruction. No screenshot here is represented as a browser screenshot, and these models should receive that review before publishing.

## Rebuild and integrate

Original models, fully offline:

```sh
./venv/bin/python scripts/build_everyday_models.py
./venv/bin/python scripts/build_gateway_arch.py
./venv/bin/python scripts/build_meteor_crater.py
```

The meteor builder normally reads the bundled grid. Optional source re-preparation downloads the four credited tiles, records their hashes, and regenerates the derived grid:

```sh
SSL_CERT_FILE=/etc/ssl/cert.pem ./venv/bin/python scripts/build_meteor_crater.py --prepare --tile-dir /tmp/earth3d-meteor-tiles
```

To reproduce the four downloads, stage outside the repo using `scripts/sketchfab_models.py stage`, UIDs recorded in the entry/evidence JSON, `--max-archive-mb 65 --max-glb-mb 90 --texture-size 1024`, and the owner's existing token-file option. Keep the token file outside the repository. Then run:

```sh
node scripts/prepare_earth3d_imports.mjs /tmp/earth3d-stage content/visualizations/models /PATH/TO/node_modules
```

The module directory must contain glTF Transform core/functions/extensions **4.5.0** and meshoptimizer. This session used the already cached npx directory; nothing was installed. `MeshoptSimplifier` is an offline simplifier only: its decoder is not needed, and no compressed-mesh extension is emitted. The pipeline deduplicates/flattens/joins/welds, simplifies toward 45k triangles with error 0.0008, prunes, and quantizes positions/normals/in-range UVs. Material boundaries can keep the Hindenburg above that triangle target; its final size is 2.53 MB and ~69k triangles. Textures remain PNG/JPEG, at most 1024 px.

For main integration, copy this job's GLBs, source documents/evidence, scripts, tests and handoff folder, then register the final entries against the copied GLBs. Do not replace main's entire models registry or Sketchfab manifest with the versions from this worktree:

```sh
for entry in handoff/earth3d/*.entry.json; do
  model="content/visualizations/models/$(basename "$entry" .entry.json).glb"
  ./venv/bin/python scripts/register_model.py "$entry" "$model"
done
```

The final egg entry includes its long-axis pre-rotation; retain it. All 14 GLBs and entries are already registered on this worktree. Before committing, exclude the pre-existing untracked `venv` symlink. Requested commit trailer: `Co-Authored-By: Codex <noreply@openai.com>`.

Outside the sandbox, run the production lab across all 14 names, including actual explorer views, then the normal audit/mobile checks. Example commands:

```sh
node scripts/model_lab.cjs shot /tmp/earth3d-browser "Elephant Bird Egg" "Boeing 747-8" "Komodo Dragon" "Hindenburg" "Gateway Arch" "Meteor Crater" --views rest,side --bg dark
node scripts/model_lab.cjs shot /tmp/earth3d-browser "Table Tennis Ball" "Tennis Ball" "Basketball" "Credit Card" "Smartphone" "A4 Paper" "Silicon Wafer" "Very Large Telescope Mirror" --views rest,side --bg dark
node scripts/model_lab.cjs explorer /tmp/earth3d-explorer "Table Tennis Ball" "Tennis Ball" "Basketball" "Credit Card" "Smartphone" "A4 Paper" "Silicon Wafer" "Very Large Telescope Mirror" "Elephant Bird Egg" "Boeing 747-8" "Komodo Dragon" "Hindenburg" "Gateway Arch" "Meteor Crater"
node scripts/model_lab.cjs audit
node scripts/model_lab.cjs mobile /tmp/earth3d-mobile
```

## Dataset changes requested

**None required for these 14 models.** Exact item names, values, plaques, images and exports remain untouched. No new item is proposed. The pre-existing neuron integration request remains owned by that job.

Optional future editorial clarification, if desired: the egg scan's individual identity is presumed and reconstructed from fragments, and 33 cm remains a representative catalog length. The model detail note already states both; no dataset edit is needed for integration. Meteor Crater's 1,186 m remains an existing approximate diameter; the source's rounded ~1.2 km does not justify inventing greater precision or resizing the terrain aperture to that diameter.

## Targets not delivered

Quality over count was applied. These are deferred, not a claim that no suitable models exist:

- Titanic: the first inspected CC-BY candidate (`fa41e6b093b84010a462ef190210d90b`, farhad.Guli) had an approximately 33.5 m rendered beam when uniformly calibrated to 269.1 m length, versus the catalog's 28.2 m beam. A second candidate (`f0a6aa63294f45a2bf330c28502b2b67`, krprom) was much larger after conservative simplification. Neither was imported. Candidate previews remain under `/tmp/earth3d-candidates/titanic/` for the first; staging is temporary, not part of the handoff.
- Giant Pacific Octopus: a real CC0 scan (`7fb48f6cbcd54149bb23837a3ac09b2e`, ffishAsia-and-floraZia) shows an elongated folded specimen with an external color target. Its overall bounding width is not the catalog's fully spread 4.3 m arm span. Mapping that bound to the span would mislead. Not imported. CPU preview: `/tmp/earth3d-candidates/octopus/overview.png`.
- The first Hindenburg (`fb1b3dc752d94bfaaf8525391929618b`, hoiman74) includes a duplicate crash vignette. It was rejected in favor of the credited single-airship model delivered here. The downloaded Arch (`8c65370f50844fea88c0d8236579e858`, 16874uy) has simplified proportions/constant-depth geometry and was replaced by the original NPS-based loft before registration; there is no registered asset to remove.
- African Bush Elephant has a shoulder-height reference that makes a whole horizontal animal exceed the resting-size rule. The staged rigged animal was not baked or imported. A future representation must handle that framing without distorting anatomy or pretending body length equals shoulder height.
- Great Pyramid: a 230.33 m base against a 146.6 m height is already ~1.57× in the narrowest frontal base view, before a corner-on view. A whole true-scale pyramid cannot meet the current 1.3× display rule under that height definition. No distorted or truncated pyramid was added.
- Titan Beetle, Queen Alexandra's Birdwing, Meganeura, Wandering Albatross, Tyrannosaurus Rex SUE, Sperm Whale and Giant Squid: source discovery did not produce a sufficiently verified, appropriate model for this batch. Do not substitute a generic species, a commercial model reupload, a tooth/skull, or a posed bounding box for the named measurement. No such import was made.
- Ever Given, Golden Gate Bridge Main Span, Hoover Dam, Arecibo Telescope, FAST Radio Telescope and Large Hadron Collider Ring were not developed. Their named extents need a component-specific calibration; a whole facility or a ring diameter must not be relabeled as a span/circumference. Arecibo additionally needs an explicit historic state.
- Mount Kilimanjaro, Mauna Kea, Grand Canyon Length, Victoria Falls, Angel Falls and Chicxulub Crater were not developed. Preserve elevation-vs-relief, route-length-vs-extent, and buried-structure definitions. In particular, a present-day surface DEM must not be presented as Chicxulub's buried crater geometry.
