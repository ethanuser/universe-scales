# length3d3 — additional public-source review

2026-10-29, branch `codex/length3d3`. **No new model qualified.** Current
coverage remains **212/258 modeled, 46 photo-only**. This is a bounded search
and source-inspection result, not a claim of internet-wide exhaustion.

Read the length-source-completion ledger and earth3d4, terrain3d2, deepsky3d,
retry3d and upgrade3d reports first. Existing rejected binaries, known NC/ND
assets, anti-bot endpoints, the empty GLM prefix and unregistered terrain/BAO
candidates were not restaged or re-registered. No runtime, registry, dataset,
export, `images/`, model-review, model-lab or GLB file changed. No dependency
was installed. No curator/author messages were sent.

## Inventory and per-item decisions

[coverage.json](coverage.json) inventories the current Length export against
the actual imported `proceduralLength` overrides and exact registry matches,
with their production precedence. All 46 names and their order equal the
previous ledger. The input files' hashes are saved. This is the instructed
browser-free fallback; Chromium/model_lab was **not retried** under the brief's
known-sandbox exception. It does not certify rendering or model accuracy.

[ledger.json](ledger.json) has one disposition for every current photo-only
item, exact search queries, source links, and evidence levels:

- **40 items received targeted web searches**, including one whose results
  returned the already known Hunga stereo-data family.
- **Six items carry forward explicit prior representation/definition blockers**:
  Contiguous US Longest Distance, TON 618 Event Horizon, Distance to the Virgo
  Cluster, Baryon Acoustic Oscillation Scale, Hubble Radius and JADES-GS-z14-0.
  These rows have empty query arrays and do not claim fresh searches.
- Of the 40 searched items, **two numeric deposits were downloaded and decoded**,
  nine rows include opened source pages, and 28 are search-result screening only.
  The remaining row identifies the previously reviewed Hunga data. Search-only
  rows are not full license, anatomy or geometry audits.

New channels included maker-site searches, Europeana/Smithsonian/Naturalis
queries, Open Heritage 3D, Zenodo/Figshare/Dryad, university literature and
public GitHub route/LiDAR projects. No absence claim extends beyond those
queries. The prior ledger now links this continuation without rewriting its
historical findings.

## Numerical source inspection

### Spider Silk Fiber: actual AFM arrays, wrong surface scope

The new [Peter et al. deposit](https://zenodo.org/records/14283026) supplies six
`.spm` height arrays. The record API explicitly reports `cc-by-4.0`; all downloaded
files match its published MD5 checksums and have pinned SHA-256 hashes.

The [paper's methods and Figure 3](https://pmc.ncbi.nlm.nih.gov/articles/PMC11836930/)
identify resin-embedded, cut fiber cross-sections and visible cutting artifacts.
Those polished end faces do not provide the intact strand's outside surface or
its longitudinal shape. Converting them to a new cylinder or extruding their
outline would invent geometry. **Keep the photo.**

[The decoded overview](previews/silk-afm-scope.png) was opened and inspected.
The export headers give overview widths of 12 and 15 micrometers, with smaller
0.3/1 micrometer detail scans. Individual heights are retained; each panel uses
its own percentile grayscale solely for inspection. These are processed ISO SPM
exports: the header explicitly warns that acquisition parameters are software
placeholders. No original instrument acquisition provenance is inferred from
those placeholder fields. Credit: Karolina Peter and colleagues, CC BY 4.0.

### Milky Way Central Bar: real distance catalog, unresolved long-bar selection

The new [Iwanek et al. table](https://zenodo.org/records/7472598) is CC BY 4.0
according to its record API. The downloaded table has **65,981 distinct source
IDs** and agrees with its published MD5. It contains actual Galactic sky
positions, photometric distance estimates and uncertainties; it is substantially
more useful than the previously reviewed analytic density functions.

The [authors' page](https://ogle.astrouw.edu.pl/cont/4_main/str/3dgal_miras/)
documents a mixed bulge/disk sample; the
[paper](https://doi.org/10.3847/1538-4365/acad7a) discusses incomplete fields.
A diagnostic selects
positive distances/errors with relative error below 20%, then a central
12 × 12 × 8 kpc display window. It contains **52,816 source rows**, plotted at
their catalog positions using the authors' 7.66 kpc Sun–GC distance. There is
no random scatter, sampled analytic density, symmetry completion or hole filling.

[Top/edge diagnostic views](previews/mira-catalog-scope.png) were opened and
inspected. They retain survey gaps and surrounding populations; this selection
does **not** establish a full long-bar member list or its endpoints. The current
item's 10 kpc long bar is based on red-clump counts, and merely choosing a box
near that size would not validate its identity. **Keep the photo.** A future
scientifically justified tracer selection/completeness treatment could make
this deposit worth revisiting. Credit: Patryk Iwanek and colleagues, CC BY 4.0.

## Other useful new leads and their limits

| Item | Source inspected or screened | Why skipped |
| --- | --- | --- |
| Meganeura | [LambOfCAD printable](https://www.cgtrader.com/3d-print-models/science/biology/meganeura-giant-prehistoric-dragonfly) | The source lists a custom license, not CC BY/CC0. No file downloaded. |
| Lituya Bay Megatsunami | [Franco's simulation deposit](https://zenodo.org/records/3831448) | Source description lists simulation video/code and solid-body STL terrain, not an observed run-up boundary or measured wave surface. Archive not acquired. |
| Trans-Siberian Railway | [World Train Map Atlas](https://worldtrainmap.com/dataset/) | Its license note distinguishes CC BY waypoint-era geometry from ODbL OSM traces. Waypoint joins are not a measured railway alignment; a CC BY facts label does not establish the live geometry's license. |
| Mammoth Cave | [ionajo/maca](https://github.com/ionajo/maca) | The project explicitly maps the entrance and above-ground features, not the accumulated underground passage network. |
| One-Nanometer Transistor Gate | [DOE explanation](https://www.energy.gov/science/bes/articles/smallest-transistor-ever) | Schematic and TEM image; no reusable complete numerical gate geometry established. |
| Earth's Inner Core | [NASA interior graphic](https://science.nasa.gov/photojournal/earth-interior-graphic/) | Its downloads are JPEG/TIFF, not a 3D mesh. |
| Blu-ray/DVD Track Pitch | [NNCI activity](https://nnci.net/node/5375) | Current downloads are teaching PDFs; no verified compatible numerical height arrays with vertical calibration acquired. NSF support is not itself a redistribution grant. |

Other per-item searches, including those yielding no new qualifying lead, are
recorded separately in the ledger. Rejected source leads are not bundled as
models, and no entry JSON is supplied because **nothing was registered**.

## Reproduction and verification

Raw numerical downloads remain outside the repository under
`/tmp/length3d3-sources` (and the initial `/tmp/length3d3-silk` and
`/tmp/length3d3-miras` caches). [Source pins](research/source-pins.json) record
the exact seven files, public URLs, checksums and directly checked license IDs.
Only small diagnostic images and numeric results are delivered.

```sh
node handoff/length3d3/inventory.mjs
# Offline with the existing cache; --prepare fetches missing pinned public files.
./venv/bin/python handoff/length3d3/audit_sources.py
```

For a clean cache, add `--prepare --cache /tmp/length3d3-sources`. Changed
upstream bytes are rejected rather than silently accepted. The audit creates
no geometry and never writes the registry or dataset.

- Node suite: **262 passing**, zero failures (`/tmp/length3d3-node-tests.log`).
- Python suite: **169 run, OK, one existing skip**
  (`/tmp/length3d3-python-tests.log`). Existing NumPy/SQLite warnings remain.
- Asset/hash verification: **212 entries / 223 exact matches**, pass.
- Version check: **zero stale references**. No JS/CSS change required a bump.
- Inventory equality, all seven source hashes, numeric array dimensions and
  unique source IDs verified; JSON parsing and `git diff --check` pass.
- glTF validation is inapplicable: **no GLB changed**. No production WebGL,
  size/picking/explorer or mobile result is claimed. The images are source-scope
  diagnostics, not production screenshots.

**Dataset changes needed: none.** Work remains uncommitted for the lead,
following the explicit known-sandbox exception; no git commit, push, merge,
rebase or branch change was attempted. The pre-existing untracked `venv`
symlink is untouched. Suggested lead commit:

```text
Document remaining Length source searches and numeric scope audits

Co-Authored-By: Codex <noreply@openai.com>
```
