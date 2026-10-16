# Space3d2 — second space-model batch

Prepared on branch `codex/space3d2`, 16 October 2026. Changes are **uncommitted**,
as requested for the known sandbox limitations. No commit/browser attempt, push,
merge, rebase or other-worktree edit was made. The existing untracked `venv`
symlink was present at the start and is not a deliverable.

## Delivered

Fourteen new exact-name Length registry entries, plus one measured Hyperion moon
asset/entry awaiting a distinct dataset item. All fifteen GLBs total 6.28 MB;
the largest is 886 kB. See [asset-table.md](asset-table.md) for IDs, individual
sizes, registration status and orthographic rest extents.

- Reused NASA VTAD's Saturn globe and rings. The ringed system is shown for
  `Saturn's Rings`; `Saturn` shows the original oblate globe. True-sized rings
  span about 2.4 mean globe diameters, so a ringed body item cannot also meet
  the required 1.3× extent ceiling. No ring proportions were compressed to hide
  that conflict. The existing angular Saturn asset/entry was not changed.
- Cassini's false-color hexagon image now occupies a circular, pole-on shallow
  cap. Juno's credited CC BY Great Red Spot mosaic occupies a curved patch.
  Both are explicitly image drapes, not reconstructed cloud relief. The hexagon
  registration is approximate. The GRS texture is from 2019, while its display
  uses the catalog's representative 2017 width; this mismatch is explicit.
- Actual Hayabusa2 Ryugu SfM geometry and final pre-impact DART Dimorphos v004
  geometry retain their source triangles and topography. Neutral gray materials
  are authored, not measured reflectance maps. Only unused source vertices are
  removed. Closed topology is checked before equivalent-volume calibration.
- Eris, PSR J0437-4715, Sirius B and Proxima are smooth, sourced diameter spheres.
  No resolved surface maps, fictional craters, stellar spots or jets are claimed.
  The neutron star heading identifies the catalog's **2024 NICER estimate**;
  source/model notes discuss the differing newer analysis.
- Vega uses a solved Roche equipotential and the coherent Monnier et al. CHARA
  concordance parameters, retaining the measured equatorial/polar radius ratio.
  Qualitative gravity darkening exposes the oblate shape. Its inspection pose
  is deliberately oblique, with the actual nearly pole-on Earth view explained.
- Halley's and Sedna's diagrams solve Kepler's equation from pinned JPL elements.
  Rulers distinguish the **whole major axis** from **Sun-to-aphelion distance**.
  Enlarged endpoint/Sun markers are labeled as locations. No orbit is stretched
  to match an older catalog value, and no current comet location is implied.
- Kuiper Belt shows **4,615 real source-object locations**, selected from 4,747
  JPL SBDB records and propagated to one display epoch. Every point has a retained
  primary designation. No synthetic filler points are used. Selection, discovery
  bias, source epochs and two-body propagation limits are documented.

Each asset has its own provenance note at
`content/visualizations/models/sources/<id>.md` and a final entry JSON here.
None replaces another registry entry, so there are no `replaces` fields.
No dataset, export, images-directory, runtime JS or CSS file was edited.

## Pending Hyperion integration and skipped Dinkinesh

`cassini-hyperion-shape.glb` is the real Cassini/Thomas 30k-plate moon model.
It validates and has reviewed CPU rest/quarter previews. It is **not registered**:
the existing exact name `Hyperion` is the redwood tree, at 116.2 m.

Ask the items job to add a distinct item, without changing the tree:

```yaml
- name: Hyperion Moon
  value: 270000
  source: https://science.nasa.gov/saturn/moons/hyperion/
  description: Saturn's moon Hyperion has a mean diameter of about 270 kilometers,
    though its irregular body is longer in some directions than others. Cassini
    images reveal a heavily cratered surface, while its changing spin makes it an
    unusual example of chaotic rotation. The value is a representative mean
    diameter, rather than the longest dimension of its measured shape.
```

The NASA source quotes mean radius about 135 km. The retained digital mesh has
equivalent-volume diameter 272.51 km; its uniformly calibrated inspection extent
is 1.207×. Older axis estimates on the NASA overview differ from this mesh; the
mesh is not deformed to those older values. After the item exists in exports:

```sh
python3 scripts/register_model.py handoff/space3d2/cassini-hyperion-shape.entry.json content/visualizations/models/cassini-hyperion-shape.glb
```

Dinkinesh is unchanged. The authoritative papers describe a shape model and
promise it through PDS, but UMD PDS downloads timed out in this session; NASA
NAIF's accessible Lucy DSK directory contained Donaldjohanson, not Dinkinesh.
The PSI shape index did not provide Dinkinesh. A published figure or a fabricated
top-shaped asteroid is not a substitute for the requested model. Useful leads:
[Levison et al.](https://arxiv.org/abs/2406.19337),
[Preusker et al.](https://elib.dlr.de/211156/), and the Lucy PDS archive.

## Exact data corrections for the items job to consider

These are not applied here. All existing entries work against the current data.

**Sedna:** the pinned JPL solution is epoch JD 2461200.5 TDB (9 June 2026),
`a=543.7195289104732 AU`, `e=0.8598824585187618`,
`Q=1011.254414174674 AU`. The current catalog's 937 AU estimate is older.
The source is the retained `sources/space3d2/sedna.json` and its exact API URL in
the manifest. If adopting this solution, set `value: 151281507096507.12` meters
(display rounded appropriately), replace the source with
`https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=90377&full-prec=1`, and replace only
the first sentence with:

> Sedna's June 2026 heliocentric osculating orbit reaches an aphelion of about
> 1,011 astronomical units from the Sun, roughly 151 billion kilometers.

Retain the rest of the plaque. If the dataset is updated, **also update the
builder** `build_orbit` Sedna calibration from `140000000000000` to the new
value, remove the old-value comparison from the note and rebuild/re-register.
The current version intentionally preserves the old catalog calibration and
unmodified native ellipse; its full resting extent is 1.165×.

**Neutron-star wording:** preserve `value: 22720` only if explicitly retaining the
2024 Choudhury estimate. Replace the opening sentence with:

> A 2024 analysis of NASA NICER data inferred an equatorial diameter of about
> 22.7 kilometers for PSR J0437-4715; a later analysis found a larger, broader range.

Retain the rest of the plaque, but change the later `The measurement constrains`
to `Such measurements constrain`. The newer
[Miller et al. study, published 2026](https://arxiv.org/abs/2512.08790) gives a
68% radius interval of 11.8–15.1 km and discusses a previously unmodeled nonthermal
component. Do not silently replace the catalog estimate with a uniquely settled
radius. The model already names its 2024 basis.

## Reproduction, inputs and rights

Offline rebuild and review:

```sh
./venv/bin/python scripts/build_space3d2_models.py
node scripts/audit_space3d2_models.mjs
./venv/bin/python scripts/preview_space3d2_cpu.py
```

The source cache is checked against `models/sources/space3d2/manifest.json`.
It contains compressed original shape coordinates, original texture JPEGs, full
JPL response snapshots, JPL reference planet elements and point-to-designation
mapping. There is no runtime source/API request. `--only` supports smaller rebuilds.
The builder always prepares Hyperion without registering it; use the explicit
registration command above after adding the item.

`scripts/prepare_space3d2_sources.py` refreshes inputs separately. It accepts a
download cache with `--cache /tmp/space3d2`; omit that argument for network refresh.
The DSK extraction requires **spiceypy 8.3.0**, installed only under
`/tmp/space3d2-deps` via `pip --target`, along with NumPy 2.5.4 as its dependency.
The shared venv was not modified. To repeat that preparation, install these in a
temporary directory and expose it with `PYTHONPATH`; the offline builder needs
only the repository's existing NumPy/Pillow environment.

Rights were opened and checked at source. Ryugu uses ISAS/JAXA open-data terms
compatible with CC BY 4.0, with source and modification credits. Hyperion's NASA
catalog declares `us-pd`. DART data come from the public NASA NAIF archive under
its SPICE use terms. Juno PIA23606 explicitly credits Kevin M. Gill CC BY; its
license version is not guessed. NASA VTAD/Cassini credits are retained. New
spheres, Roche geometry and implementation are original CC0 contributions.
See `models/licenses/space3d2-rights.md` and each source note for links and hashes.

## Verification and remaining review

- `node --test tests/*.test.cjs tests/*.test.mjs`: **225 passed**.
- Python unittest discovery: **103 tests, one existing skip, no failures**.
  Six new tests check Roche endpoints/equipotential, Kepler distances/handedness/
  inclination, and unique real source selections.
- `fetch_model_assets.py --verify`: **132 self-contained registered GLBs,
  143 exact-name matches**, all valid; Hyperion is separately validated.
- `bump_versions.py --check`: **0 stale references**. No JS/CSS changed.
- Full requested glTF validator command: **0 errors** in this branch; 1,867
  existing warnings are summarized in `full-validation-summary.json`. The global
  generated report was restored to its original contents to avoid an unrelated
  report diff. Final validation of all fifteen new assets: **0 errors/warnings**,
  recorded in [gltf-validation.json](gltf-validation.json).
- The actual vendored GLTFLoader parses all fifteen assets, checks registration
  hashes, hierarchy and precise rest bounds: **all pass**, 0.953–1.280× extent.
  Image decoding is stubbed for this geometry-only check, explicitly not material
  verification. Details: [loader-audit.json](loader-audit.json).
- All fifteen CPU rest/quarter-camera sheets were opened and viewed, including
  the revised circular cap. [Overview](previews/overview.jpg),
  [review 1](previews/review-1.jpg), [review 2](previews/review-2.jpg),
  [review 3](previews/review-3.jpg). Individual full-size sheets and geometry
  measurements are in `previews/`. The quarter-camera orbit/patch views naturally
  compress close to edge-on; CPU captions can overlap there.

Per the brief, Chromium and git sandbox limitations were not retried. These CPU
images and loader bounds are **not** production model-lab approval: WebGL material
appearance, the actual explorer, perspective size audit, SVG labels, mobile/touch
and performance remain for the lead to review outside the sandbox. Preserve the
scientific qualification notes during that review. If merging registry changes
onto main conflicts, retain main's registry and run [integrate.py](integrate.py)
to re-register these fourteen entries. Hyperion remains a separate opt-in step.

Suggested lead commit message: `Add sourced second-round space models` with the
required final trailer `Co-Authored-By: Codex <noreply@openai.com>`. No git action
has been attempted here.
