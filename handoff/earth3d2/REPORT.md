# earth3d2 handoff — 2026-10-16

Branch: **`codex/earth3d2`**. Changes are **uncommitted** for the lead. The brief
explicitly documents blocked Chromium/git commits and says not to retry; neither
was attempted. No push, merge, rebase, branch change or sibling-worktree write.
The pre-existing untracked `venv` symlink is not part of this delivery.

## Delivered

Seven new self-contained GLBs, approximately **8.32 MB total**, each under 3 MB.
No existing model is replaced or redone. No dataset, exports, data, images,
runtime JavaScript/CSS or HTML changes. `models.json` has only these seven
additions; `sketchfab-length.json` has the two corresponding curated additions.
Each final entry JSON below exactly matches the registered entry in this worktree.

| Item | Entry / model ID | kB | Triangles | Representation |
| --- | --- | ---: | ---: | --- |
| African Bush Elephant | [earth3d2-african-elephant.entry.json](earth3d2-african-elephant.entry.json) | 428.4 | 4,806 | Credited artistic exterior; shoulder height |
| Sperm Whale | [earth3d2-sperm-whale.entry.json](earth3d2-sperm-whale.entry.json) | 1,718.0 | 45,000 | Credited artistic exterior; total length |
| Ever Given | [earth3d2-ever-given.entry.json](earth3d2-ever-given.entry.json) | 2,018.6 | 28,546 | Original dimensioned exterior, illustrative cargo |
| Golden Gate Bridge Main Span | [earth3d2-golden-gate-main-span.entry.json](earth3d2-golden-gate-main-span.entry.json) | 1,743.3 | 22,288 | Original central-span exterior diagram |
| Arecibo Telescope | [earth3d2-arecibo-reflector.entry.json](earth3d2-arecibo-reflector.entry.json) | 821.7 | 32,512 | Idealized intact, pre-collapse reflector only |
| FAST Radio Telescope | [earth3d2-fast-reflector.entry.json](earth3d2-fast-reflector.entry.json) | 871.5 | 32,512 | Nominal spherical primary reflector only |
| Mount Kilimanjaro | [earth3d2-kilimanjaro.entry.json](earth3d2-kilimanjaro.entry.json) | 721.0 | 33,794 | Actual DEM summit crop above sea-level datum |

All seven scale **uniformly**. The elephant solves the round-one framing issue
with an almost frontal resting view, while preserving its whole body. Its dorsal
withers are the highest mesh point in this particular neutral pose, so Y extent
really measures foot to shoulder. It is not calibrated to body length or trunk
reach. The whale's supplied bind pose is frozen before pruning the rig. Both
animals retain honest artistic-reconstruction qualifications; neither is a scan
or a measured individual. Licenses were verified directly with the Sketchfab
API; retained evidence is under `sources/earth3d2-imports/`.

## Accuracy and presentation limits

- **Elephant:** artist jimmyho905 identifies an African Elephant; the savanna
  appearance is illustrative, not a verified taxonomic specimen or measured male.
  Source texture/geometry is retained. No simplification, body shortening or
  cropped anatomy. When rotated broadside, the whole animal naturally exceeds
  its shoulder height; the 1.3× rule is satisfied at rest. Review neighbor clearance
  while dragging in the production explorer.
- **Whale:** AneesAnimates's exterior, calibrated nose to fluke to NOAA's 52 ft
  (15.8496 m) male marker. It has no source base-color map: gray-blue skin is
  authored; source normal/roughness maps and sculpted details are retained.
  MikkTSpace tangents were regenerated to avoid runtime tangent generation.
- **Ever Given:** the Panama Maritime Authority report gives a 399.98 × 58.80 m
  hull envelope and 32.90 m moulded depth. The unchanged dataset uses 399.94 m;
  uniform calibration differs by about 0.01%, documented in the registry note.
  Hull curves, superstructure dimensions, colors, machinery and the partial
  above-deck cargo load are authored illustrations, not detailed shipyard or
  stowage data. The report's general-arrangement view was visually inspected.
  This is not a reconstruction of the 2021 grounding. No canal, water, interior,
  propeller or rudder is claimed. The model's original texture has no logos or IDs.
- **Golden Gate:** only the central span and towers, with tower centers 4,200 ft
  (1,280.16 m) apart. The catalog rounds to 1,280 m. Major deck/tower/cable dimensions
  and suspender spacing follow the Bridge District; the cable uses a parabolic
  approximation and the District-hosted statics chapter's 144 m sag. Tower taper,
  bracing, truss members and roadway details are authored exterior simplifications.
  No side spans, anchorages, terrain, underwater foundations or structural analysis.
- **Arecibo:** 305 m aperture, 265 m nominal spherical radius. The derived cap
  depth is 48.277 m; no independent stretching to the inconsistent rounded depth
  in Cornell's news article. The original rectangular texture approximates panel
  organization, not a survey. The complete facility, feed platform, towers,
  ground screen, support structure and terrain are omitted. Explicitly an intact
  **pre-collapse reflector**, not today's site.
- **FAST:** the 500 m physical aperture and 300 m curvature radius describe its
  **nominal sphere**, not its approximately 300 m actively deformed illuminated
  paraboloid. Panel pattern is illustrative, not measured inventory. Feed cabin,
  towers, actuators, cable net and terrain are omitted. Both telescope surfaces
  are zero thickness and double-sided; no solid-bowl or shell-thickness claim.
- **Kilimanjaro:** true metric relief in a 6.4 km square around the summit crater,
  sampled at 50 m from credited public-domain USGS/Mapzen terrain. The crop omits
  most of the massif. Its straight walls reach a sea-level display datum and are
  arbitrary cuts, not the mountain's base or real cliffs. DEM maximum is about
  5,885.668 m, retained without forcing the grid to TANAPA's 5,895 m altitude.
  No synthetic crater, vertical exaggeration or current glacier/snow map.

Display-label qualifiers are **top-level registry fields**, as required by the
existing explorer; on-model annotations also identify cropped/isolated parts.
Each model has a separate `content/visualizations/models/sources/<id>.md` with
opened source links, license, calibration and limitations; the entry's
`processing.source_note` points there. Original illustrations are CC0, imported
animals remain CC BY 4.0, and the DEM retains Mapzen/Tilezen/USGS attribution.

## Visual review and verification

Viewed all final rest and quarter-camera CPU pairs, including full-size individual
images. Refined poses so bridge, ship and whale show more of their full length in
both views. Geometry checks caught/repaired inward hull faces and a folded bow
section that a two-sided raster preview alone did not reveal. Both animal rigs
were baked before pruning; the elephant source's unused rig/accessors were large,
so it shrinks substantially without reducing its 4,806 triangles.

- [CPU contact sheet](previews/overview.png); individual pairs:
  `previews/<id>.png`. Generated with the existing
  `scripts/render_earth3d_previews.py`, using actual final GLB hierarchy, quantized
  positions, base-color textures, normals and a depth buffer. These are explicitly
  **CPU orthographic previews**, not browser screenshots. The view labeled SIDE
  rotates the camera a quarter turn while retaining the resting pose; it is not
  an exact reproduction of model-lab's `side` preset. The renderer does not implement
  production PBR/environment reflections, tangent normal maps, proper texture
  filtering, perspective, overlay labels, interaction or UI. Its nearest texture
  sampling produces visible moiré on Arecibo's small panel pattern; production
  mipmap/aliasing behavior still needs inspection. Its dark linear colors are not
  a measurement of production brightness.
- [CPU geometry audit](previews/geometry-audit.json): **all seven resting extents
  are within 0.6–1.3×**. This is not production `model_lab audit`. Side views may
  legitimately differ, particularly the shoulder-height elephant and summit block.
- **Node:** `node --test tests/*.test.cjs tests/*.test.mjs` — **225 passed**.
  [Log](node-tests.log).
- **Python:** `./venv/bin/python -m unittest discover -s tests -p 'test_*.py'` —
  **104 tests, OK, one existing skip**. Seven new tests check asset/entry/registry
  agreement, size budgets and resting extents, analytic cap curvature and concave
  winding, actual ship envelope/container dimensions and outward hull faces,
  main-span cable extent, unstretched DEM/grid hashes, animal license evidence,
  static geometry/tangents and elephant withers calibration. [Log](python-tests.log).
- **Asset verification:** passes, **125 self-contained GLBs / 136 exact-name
  registry matches**. [Log](asset-verification.log).
- **Content-hash check:** `python3 scripts/bump_versions.py --check` — zero stale
  references. No runtime JS/CSS changed, so no version rewrite was needed.
- **Khronos glTF Validator:** required full `validate-models.cjs` command exits
  **0** in this worktree; all seven new GLBs have **zero errors and zero warnings**.
  [This job's complete validation results](gltf-validation.json),
  [full-command log](full-validation.log). Existing models still have unrelated
  warnings. Unlike older handoff notes, this branch's current registry does not
  contain the previously failing mitochondrion asset. The validator's unrelated
  aggregate `validation.json` rewrite was restored to its original bytes.
- `git diff --check` — passes.

**Production review remains pending:** model-lab rest/side shots, actual explorer
with neighbors, size/picking/grounding audit, overlay label placement, reflections,
normal maps, texture aliasing and mobile performance. The explicit lead instruction
prohibited retrying known sandbox failures, so Chromium and git commits were not
attempted. These CPU images are not represented as WebGL approval.

No packages were installed into the shared venv. The only new temporary dependency
was **pypdfium2**, installed with pip `--target /tmp/earth3d2/pdf-tools` to render
report pages after Poppler and local PDF renderers proved unavailable. It is not a
project dependency. Existing cached glTF Transform 4.5.0, meshoptimizer, mikktspace
and gltf-validator were used; no npm install. The PDF skill was used to inspect the
Ever Given report. Temporary candidate downloads and PDF pages remain in `/tmp/earth3d2`;
the elephant source came from the earlier `/tmp/earth3d-stage` cache.

## Rebuild and integrate

Fully offline original/terrain builders:

```sh
./venv/bin/python scripts/build_earth3d2_structures.py
./venv/bin/python scripts/build_earth3d2_ship.py
./venv/bin/python scripts/build_earth3d2_terrain.py
```

Optional Kilimanjaro source re-preparation:

```sh
SSL_CERT_FILE=/etc/ssl/cert.pem ./venv/bin/python scripts/build_earth3d2_terrain.py --prepare --tile-dir /tmp/earth3d2/terrain-tiles
```

To reproduce imports, stage the UIDs in the animal entries outside the repo with
`scripts/sketchfab_models.py stage`, the owner's token-file option, texture size
1024, source archive limit 45 MB and staged GLB limit 65 MB. Never print/store the
token or signed download URLs. Follow each animal's source note for the Python
bind-pose bake and JS preparation (`whale` is the JS default; use `elephant` for
the second animal). The external module directory needs glTF Transform
core/functions/extensions **4.5.0**, meshoptimizer and mikktspace. These are build
tools only. All final assets use PNG/JPEG and require no mesh/texture decoder.

Copy this job's assets, source notes/evidence, new scripts, tests and handoff to
main, then re-register the entries individually. **Do not overwrite main's whole
registry or Sketchfab manifest.** All seven are already registered here:

```sh
for entry in handoff/earth3d2/*.entry.json; do
  model="content/visualizations/models/$(basename "$entry" .entry.json).glb"
  ./venv/bin/python scripts/register_model.py "$entry" "$model"
done
```

There are no `replaces` fields because all entries are additions. After production
review, the lead can commit the assets/handoff with the requested trailer:
`Co-Authored-By: Codex <noreply@openai.com>`. Exclude the pre-existing `venv` symlink.

Example browser checks outside the sandbox:

```sh
node scripts/model_lab.cjs shot /tmp/earth3d2-browser "African Bush Elephant" "Sperm Whale" "Ever Given" "Golden Gate Bridge Main Span" "Arecibo Telescope" "FAST Radio Telescope" "Mount Kilimanjaro" --views rest,side --bg dark
node scripts/model_lab.cjs explorer /tmp/earth3d2-explorer "African Bush Elephant" "Sperm Whale" "Ever Given" "Golden Gate Bridge Main Span" "Arecibo Telescope" "FAST Radio Telescope" "Mount Kilimanjaro"
node scripts/model_lab.cjs audit
node scripts/model_lab.cjs mobile /tmp/earth3d2-mobile
```

## Dataset changes needed

**None required.** No quantity, item name, description, plaque, image or export
was edited. The model notes preserve the Ever Given source/catalog difference and
the mountain's sampled/published altitude difference. The existing Neuron request
is unrelated and remains owned by that job.

## Requested targets deferred

These are limits of this batch, **not proof that suitable assets do not exist**.
No generic species, commercial reupload, cartoon, geological bowl or stretched
bounding box was substituted to increase the count.

| Target | Finding / reason not registered |
| --- | --- |
| Titan Beetle | Searches for the common and scientific names found no verified complete downloadable CC-BY/CC0 Titanus model. A Dorcus titanus stag beetle is a different animal and was not substituted. |
| Queen Alexandra's Birdwing | No verified female O. alexandrae model in the searched results. Rajah Brooke's birdwing and generic butterflies are different species/measurements. |
| Meganeura | Several apparent Dinoraul reuploads have nominal CC-BY labels but unresolved original rights; other candidates lacked sufficient provenance/anatomical confidence. |
| Bee Hummingbird | No verified Melisuga helenae candidate; generic hummingbirds, shorebird scans and unrelated plant models were rejected. |
| Bumblebee Bat | No verified Kitti's hog-nosed bat candidate. A generic flying bat would also confuse body length with wingspan. |
| Paedophryne Amauensis | The available diceCT result is P. verrucosa, a different species; it was not relabeled. |
| Wandering Albatross | No verified spread-wing D. exulans asset; several name hits were aircraft or butterflies. A folded taxidermy/other species cannot be calibrated by its bounding box as record wingspan. |
| Giant Pacific Octopus | Round-one's CC0 folded specimen scan cannot represent a fully spread arm-span measurement by calibrating its folded bound; no better verified replacement found. |
| Lolong the Crocodile | No verified Lolong scan/reconstruction under the allowed licenses. Generic crocodiles do not establish this individual's geometry. |
| Tyrannosaurus Rex SUE | [Field Museum's official full-cast scan](https://www.fieldmuseum.org/page/sue-3d-model) identifies **CC BY-NC 4.0**, excluded by the brief. Generic/game-model SUE uploads were not substituted. Its media-system link now redirects to a JavaScript portal. |
| Giant Squid | Inspected the CC-BY Heronzavr candidate `65067ab00ce04f0ba10bcc04a0b1da1b`; too crude and insufficiently verified to support a measured total-length comparison with two distinct feeding tentacles. Not imported. |
| Titanosaur Cast | Patagotitan life-size exterior replica and generic fleshed dinosaur hits are not AMNH's named skeletal cast. No verified complete cast scan found under allowed terms. |
| Titanic | Revisited the two previously staged candidates and a further upload. Conservative processing left the detailed candidates roughly 14.5–16.7 MB, and matching material/geometry patterns across uploads left original authorship unresolved. The earlier small candidate's beam mismatch remains. No forced distortion or poorly credited reupload. |
| Prelude FLNG | Shell's 488 × 74 m envelope is available, but no verified reusable facility mesh or sufficiently documented topside geometry was established. An invented industrial pipe layout would overstate knowledge. |
| Great Pyramid of Giza | The original-height definition makes an upright whole-pyramid base exceed the size rule; no truncated/distorted pyramid or tilted pose chosen solely to evade the rule. A future explicit height-measurement representation needs separate design. |
| Hoover Dam | The inspected CC-BY-labeled candidate `e253f88e7d82451a8c93554b67faba99` explicitly says it was ripped from Google Maps using RenderDoc. Its uploader's CC label does not establish reusable rights to those source assets. |
| Mauna Kea, submarine base | No adequately sourced/calibrated bathymetric base definition and full mountain representation satisfying the current height/extent rule was completed. No fictitious underwater cone or exaggerated vertical scale. |
| Grand Canyon Length | The USGS Colorado River centerline service was found, but currently returns no accessible layers. The latest NPS statistics also use 278 river miles rather than the catalog's older 277-mile convention. No unverified centerline/canonical endpoint choice or regional-width-as-river-length substitution. |
| Victoria Falls | No verified reusable detailed fall geometry; a coarse DEM alone does not measure the water curtain or its full width. No invented cliff/water surface. |
| Angel Falls | No verified reusable fall geometry. DEM escarpment relief is not automatically the named total drop or uninterrupted plunge, so no synthetic water ribbon was calibrated to it. |
| Chicxulub Crater | Scientific gravity maps/references were located, but no licensed numeric anomaly grid with fully established units/processing was bundled. Did not turn false-color pixels into purported elevation or invent a buried crater bowl. |
| Large Hadron Collider Ring | Located an OSM ring way, but ODbL is outside this job's explicit CC-BY/CC0/US-government list; the CC-BY Sketchfab path has no coordinate/survey basis. No georeferenced CERN path/terrain combination was established, and a ring diameter was not relabeled as its circumference. |

Useful primary-source follow-ups: [USGS centerline service](https://grandcanyon.usgs.gov/server/rest/services/basedata_pvector/ColoradoRiverCenterline/MapServer),
[NPS current canyon statistics](https://www.nps.gov/grca/learn/management/statistics.htm),
[Shell Prelude overview](https://www.shell.com.au/about-us/what-we-do/gas-and-lng/prelude-flng-facility/prelude-overview.html),
[Chicxulub geophysical evidence paper](https://www.nature.com/articles/s41467-020-15269-x),
and [CERN LHC definition](https://home.web.cern.ch/science/accelerators/large-hadron-collider/).
