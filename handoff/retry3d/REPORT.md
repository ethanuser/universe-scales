# retry3d — second pass on photo-only Length items

2026-10-23, branch `codex/retry3d`. **One observed-data map registered; two
unexaggerated terrain candidates prepared but unregistered; 22 targets skipped.**
All 25 requested names were checked against the current registry before work.

No application JS/CSS/HTML, `model-review*`, dataset values/descriptions, frontend
exports, photographs or other branches were edited. No dependencies were
installed. The pre-existing untracked `venv` symlink was left alone.
Work remains **uncommitted**, following the brief's explicit known-sandbox
exception. Neither a git commit nor Chromium was attempted.

## Registered: M87 Jet

`retry3d-m87-hst-map.glb`: **156,184 bytes**, **9,689 original observed pixels**,
zero triangles, one point primitive. Vendored-loader resting extent is
**1.04076×** the existing listed value. It has no display-label override,
in-model caveat, ruler, particle animation or invented depth.

The new source is the [XJET archive's original Hubble WFPC2 F555W FITS image](https://hea-www.harvard.edu/XJET/data/m87_hst_f555w.fits),
with [observer/image documentation](https://hea-www.harvard.edu/XJET/data/m87_hst_f555w.txt),
[M87 angular-to-physical scale](https://hea-www.harvard.edu/XJET/source-d.cgi?M87),
and an [explicit public-domain/acknowledgement policy](https://hea-www.harvard.edu/XJET/image_policy.txt).
The archive's policy requires contributors to have the owner's permission;
it is not a Creative Commons grant inferred from an image thumbnail.
Credit: NASA/ESA HST/WFPC2, original PI Sparks, contributor E. Perlman,
Perlman et al. (1999), AJ 117, 2185, and XJET.

This is an **observed sky-plane intensity map**. Every vertex is a measured
FITS pixel's WCS tangent-plane position; its third coordinate is exactly zero.
It uses the brief's allowance for observed sky positions on a stated plane.
Rotation reveals the plane edge-on. This scope is explicit in the registry and
[source notes](../../content/visualizations/models/sources/retry3d-m87-hst-map.md).
The original FITS is losslessly pinned, so it can be reprocessed without a
Harvard network request.

Physical coordinates retain XJET's historical **0.077 kpc/arcsec** scale. The
actual rotated FITS CD matrix is used rather than the descriptor's rounded
pixel scale; no extra cos(declination) is applied. There is no stretching to
5,000 light-years. A fixed rectangular image aperture, native-value threshold
and connected-pixel display filter remove most of the noisy outer field. They
are not a scientific jet-boundary determination or a noise-significance claim.
The cuts, transfer function and every original pixel identity are reproducible.

The source descriptor dates the observation 1995-02-04 while the FITS header
says 1995-02-03; public text says February 1995. The source also cautions that the
WCS is not registered to accurate radio maps. No multi-band alignment is claimed.

CPU rest/side/small previews were opened and inspected. An initial sprite size
made the original pixel lattice too visible; the final shared screen-space
kernel blends it without changing any vertex coordinates. Source gaps between
knots remain visible. The false-color blue-white intensity palette is not
natural RGB photography. These previews **do not certify WebGL blending**.

## Prepared terrain: framing proposals, not live additions

Unlike the earlier ambiguous GFZ license and generic GEBCO availability checks,
this pass downloaded the actual NOAA **ETOPO 2022 15-arcsecond GeoTIFFs**.
NOAA's [collection metadata](https://www.ngdc.noaa.gov/metadata/published/NOAA/NESDIS/NGDC/MGG/DEM/iso/xml/etopo_2022.xml)
explicitly applies **CC0 worldwide**. The metadata hash, extracted grant,
original tile hashes and exact numeric subsets are pinned. The
[release paper](https://essd.copernicus.org/articles/17/1835/2025/), section 3.1
and Table 3, confirms Baikal's incorporated GEBCO bathymetry.

| Candidate | Bytes / triangles | Native vertical extent / listed quantity | Overall resting extent / listed quantity |
| --- | ---: | ---: | ---: |
| `retry3d-mauna-kea` | 553,928 / 27,306 | 9,866.52 m / 10,211 m = **0.9663×** | **18.5270×** |
| `retry3d-baikal-depth` | 208,252 / 10,001 | 1,653.79 m / 1,642 m = **1.0072×** | **26.2934×** |

All geometric vertices are original source-grid samples, selected at fixed
strides. Adjacent samples form triangles. There are no side walls, bottoms,
water surfaces, invented rulers, vertical exaggeration, added shore vertices,
hole filling or normalized footprints. Colors encode source elevation/depth.
The local map projection and its small scale variation are documented.

Mauna Kea includes the northeastern edifice, Kohala and the offshore flank;
it does not identify a unique geological base. It excludes Mauna Loa's summit.
The [USGS summit-to-ocean-floor definition](https://www.usgs.gov/faqs/how-big-are-hawaiian-volcanoes)
remains the quantity basis. ETOPO smooths the summit; its heights are never
adjusted to the USGS nominal numbers.

Baikal is a local lake-bed aperture southeast of Olkhon, not the whole lake.
A nominal **456 m** lake level comes from the
[historical ILEC record](https://wldb.ilec.or.jp/Display/html/3544).
It is not a contemporaneous level measured in the ETOPO datum. The source
minimum is -1,198 m, giving 1,654 m nominal depth; the selected mesh's actual
range is slightly smaller. This does not revise or independently establish the
catalog's 1,642 m maximum. Native samples above the nominal surface are excluded;
small disconnected source-grid patches remain. ILEC's older depth estimate is
not used.

**Proposed exception:** retain `presentation.measure_axis: "y"` and explicit
physical `reference_size` (10,211 or 1,642 native metres), and assess the listed
vertical quantity separately from the whole object's projected footprint.
Both fields are already in the candidate entry JSONs. Existing `measure_axis`
selects calibration; it does **not** make the current max(width,height) audit
measure a vertical quantity. With explicit `reference_size`, it is redundant
for current calibration. A renderer/audit change or an explicit exception is
still required; no runtime change was made here. Layout/focus factors in the
candidate entries are conservative review starting points, not production approval.

The CPU previews show shallow terrain relative to its wide footprint, especially
edge-on. I recommend retaining the photos until the lead judges whether these
faithful surfaces improve the radial explorer. The report's vertical ratios
must not be presented as passes of the current overall size rule. The actual
loader audit records both failures and confirms that neither is registered.

## Search audit: 22 skipped targets

The three earlier reports were read first. Known NC/ND assets, the old GFZ
contours, the old empty 2017 GLM S3 prefix, OSM tunnel guesses, generic Natural
Earth route selection, and earlier shape-model queries were not used as fresh
acquisition attempts. Searches are finite acquisition results, not claims that
no suitable source exists anywhere.

| Target | New source/check in this pass | Result |
| --- | --- | --- |
| Dust Mite | Confocal-stack teaching resources at [MyScope](https://myscope.training/); Zenodo/Figshare/BioImage Archive searches for Dermatophagoides | Teaching illustrations and taxonomic/allergen records were found; no openly reusable calibrated whole-mite stack or mesh was acquired. No depth inferred from microscopy photos. |
| Cat Flea | [Zenodo Cat flea heads](https://zenodo.org/records/15614748), public record API, Dryad and CT searches; MorphoSource query | The CC BY Zenodo record supplies an XLSX workbook, not a downloadable whole-animal CT/mesh. MorphoSource returned its anti-bot page. The prior NC UF scan was not restaged. |
| Paedophryne Amauensis | [Paluh et al. frog CT dataset route](https://elifesciences.org/articles/66926), LSUMZ specimen/deposit searches, MorphoSource | A general CT archive route exists, but the media search returned an anti-bot page and no verified accessible complete admissible surface was acquired. No partial pelvis was substituted. |
| Bumblebee Bat | [DigiMorph's whole USNM 528306 specimen](https://digimorph.geo.utexas.edu/specimens/Craseonycteris_thonglongyai/whole/), newer nasal-CT publication, MorphoSource | The whole-animal page provides slice/rotation movies but lists both STL and CT download as unavailable. Head/nasal anatomy does not supply a body-length surface. No movie frames were treated as a calibrated raw volume. |
| Bee Hummingbird | [Smithsonian hummingbird resources](https://nationalzoo.si.edu/migratory-birds/hummingbirds), Mellisuga searches across Smithsonian 3D, Phenome10K and MorphoSource | No accessible, licensed, species-identified whole-body geometry was obtained. The MorphoSource route returned its anti-bot page. |
| Titan Beetle | [Smithsonian specimen resource](https://www.si.edu/collections/snapshot/titan-beetle), Korean-language 3D specimen-index lead, public-deposit/CT searches | Smithsonian result supplies a photograph. The Korean catalog lead was not accompanied by a verifiable downloadable mesh and permitted reuse grant. No different beetle species was substituted. |
| Queen Alexandra's Birdwing | [Kagawa University specimen collection](https://www.ag.kagawa-u.ac.jp/birdwingbutterflies/ornithoptera/straatmana/alexandrae/012-00097/), museum/deposit searches | Dorsal/ventral specimen photographs were available; no measured 3D data obtained. The previously rejected Adobe/NHM licensing route was not used. |
| Meganeura | [MNHN/ISYEB museum reconstruction](https://isyeb.mnhn.fr/fr/actualites/les-libellules-geantes-du-paleozoique-sont-elles-encore-parmi-nous-4450), [Cardiff Bioimaging's physical-print account](https://blogs.cardiff.ac.uk/bioimaging/in-focus-winging-it-in-paleobiology-strange-tails-from-a-strange-time/) | Real museum reconstruction/printing projects exist, but no source mesh with a qualifying reuse grant was acquired. No new fossil reconstruction authored. |
| Wandering Albatross | [Phenome10K Diomedea exulans](https://www.phenome10k.org/diomedea-exulans), scanned-wing morphology literature | The accessible species scan is a cranium. Isolated wing/bone measurements do not supply a complete bird at documented wingspan. No wings repositioned or mirrored into a whole bird. |
| Giant Pacific Octopus | Smithsonian/public-deposit and source-measurement searches for Enteroctopus dofleini | No arm-span calibration tied to the known folded CC0 scan was obtained. The prior scan was not restaged; a generic maximum span was not assigned to its folded bounding box. |
| Titanosaur Cast | University/museum and newer titanosaur CT/surface-data deposit searches | Newly found fossil studies concern isolated or incomplete anatomy, not the complete cast's measured span. No complete qualifying Patagotitan cast mesh was obtained; no bones assembled into a new skeleton. |
| Great Pyramid of Giza | New [gabriele.l Meshroom scan](https://sketchfab.com/3d-models/giza-plateau-drone-video-20fa1b7c608a43e1814c3744641732a4), API license verification, authenticated stage and CPU crop; Arqueomodel3D API check | New scan is downloadable CC BY. Its source gaps and weak metric provenance failed review; no filling, restored cap or anisotropic correction was made. Arqueomodel3D's complex is non-downloadable/standard-licensed. Cropped rejection evidence is in `rejected/`; no new pyramid GLB registered or bundled. |
| Dinkinesh | Actual [NAIF Lucy DSK directory](https://naif.jpl.nasa.gov/pub/naif/LUCY/kernels/dsk/) and its PDS4 counterpart, [newer geology/shape paper](https://doi.org/10.3847/PSJ/ae1968) | Curl reached NAIF despite the earlier Python TLS problem. The available DSK is for Donaldjohanson, not Dinkinesh. The newer paper describes a revised model, but no usable authoritative Dinkinesh mesh release was obtained. No web-fan shape substituted. |
| Lituya Bay Megatsunami | [USGS 2015 lidar data release between Lituya Bay and Icy Point](https://www.usgs.gov/data/digital-elevation-models-glacier-bay-national-park-between-lituya-bay-and-icy-point-alaska), newer lidar/landslide releases | The new lead concerns coastal terrain; no georeferenced historical maximum-runup survey geometry was acquired for this item. A terrain scene was not labeled as a measured wave or a fabricated runup marker. |
| Channel Tunnel | [Archaeology Data Service Channel Tunnel Rail Link archive](https://archaeologydataservice.ac.uk/archives/view/ctrl/downloads.cfm?group=1036), engineering/deposit searches | Archive concerns surface rail-link archaeology, not an admissible surveyed alignment of the bored cross-Channel tunnel. No tunnel alignment obtained. |
| Trans-Siberian Railway | [Transsib route-map collection](https://transsib.ru/cat-map.htm), transport repository/vector-export searches | Map references were found, but no verified through-route coordinate export with an admissible reuse grant was obtained. No guessed station joins or Natural Earth feature choices repeated. |
| Large Hadron Collider Ring | [CERN survey/alignment publications](https://cds.cern.ch/record/2849060), CERN Open Data and lattice/survey export searches | Public reports describe coordinate databases and alignment methods; no complete permitted ring-coordinate export was acquired. Collision-event open data are unrelated to ring geometry. No circular primitive or home-generated lattice path was imported. |
| Mammoth Cave | [PANGAEA's CC BY Mammoth Cave-area potentiometric dataset](https://doi.pangaea.de/10.1594/PANGAEA.931870), cave-survey deposit searches | Acquired source description identifies groundwater contours/interpolated hydraulic surface, not cave-passage coordinates. It cannot represent the cave's accumulated passage length. |
| Typhoon Tip | New [NII Digital Typhoon 1978–1979 archive](https://agora.ex.nii.ac.jp/digital-typhoon/notice/20080412.html.en), storm data/reuse/projection searches | Historic imagery exists, but an admissibly licensed, georeferenced Tip subset with verified mapping was not acquired. A cloud image was not converted into a measured wind-field boundary or cloud depth. |
| Longest Lightning Flash | [NASA NTRS record and download inventory](https://ntrs.nasa.gov/citations/20250007235), certified-event data searches | The new record exposes the certification paper PDF, not a downloadable certified event-coordinate dataset. No event/group set acquired. The old empty S3-prefix attempt was not repeated and no channels digitized by eye. |
| Milky Way Central Bar | [New analytic-density model release route](https://academic.oup.com/mnrasl/article/514/1/L1/6576782), observational catalog/grid searches | The accessible release is an analytic density approximation in AGAMA, not an acquired measured full-bar grid or member-coordinate dataset. Sampling that function into a new cloud would violate this brief. |
| Magellanic Stream | [Chandra et al. stellar-stream discovery](https://doi.org/10.3847/1538-4357/acf7bf), newer stellar/distance-data searches | Stellar tracers provide new constraints but do not recover the catalog item's full gaseous-stream geometry. No suitable complete measured spatial product acquired. HI velocity was not used as spatial depth. |

MorphoSource endpoints for Paedophryne, Ctenocephalides, Mellisuga, Craseonycteris
and Titanus returned anti-bot pages to public JSON searches. No login, media
request, access restriction or robot check was bypassed. No requests were sent
to curators or other people.

## Reproduce and integrate

```sh
# Offline; registers only the M87 entry.
./venv/bin/python scripts/build_retry3d_m87.py
# Offline; explicitly builds the two unregistered candidates only.
./venv/bin/python scripts/build_retry3d_models.py
./venv/bin/python scripts/preview_retry3d_cpu.py
node scripts/audit_retry3d_models.mjs
```

Add `--prepare` to either builder to intentionally refresh its external cache.
The NOAA tile/source hashes are preserved in each provenance file; a refresh
must be reviewed before accepting a changed source. No original remote URL is
needed at runtime. The new scripts use only existing venv dependencies and curl.

To integrate after copying files while keeping main's registry:

```sh
python3 scripts/register_model.py handoff/retry3d/retry3d-m87-hst-map.entry.json \
  content/visualizations/models/retry3d-m87-hst-map.glb
```

No `replaces` field is needed. **Do not bulk-register all entry JSONs:** the
Baikal/Mauna entries are proposals. Their default builder never registers them.
No dataset edit is required or proposed for this batch.

Lead's deferred production review:

```sh
node scripts/model_lab.cjs shot /tmp/retry3d-review "M87 Jet" --views rest,side --bg dark
node scripts/model_lab.cjs explorer /tmp/retry3d-review "M87 Jet"
node scripts/model_lab.cjs audit
node scripts/model_lab.cjs mobile /tmp/retry3d-mobile
```

Inspect the point map on light/dark backgrounds, near the radial readability
threshold, during rotation and under mobile point handling. The exact edge-on
line is intentional observational scope. The lead can reject a flat projection
if the photograph communicates the item better; no 3D depth should be added.

## Verification

- Node: **236 passing** (`node-tests.log`).
- Python: **167 run, one existing skip, OK** (`python-tests.log`), including six
  new source-registration, physical-coordinate, source-only topology, normal,
  FITS date/WCS, observed-pixel identity and zero-depth tests.
- Actual vendored GLTFLoader: all three new files load; registered M87 passes
  0.6–1.3× and declared layout width. Terrain overall-size failures are recorded
  explicitly; both are unregistered (`loader-audit.json`).
- Khronos glTF Validator: **all three new files have zero errors and zero
  warnings** (`validation.json`). Full registry run: **203 files, zero errors**,
  1,867 existing warnings (`gltf-validator.log`). The global validation file
  preserves every previous record and appends only M87's result; full-run logs
  also cover two previously absent clock/deck records.
- Asset verification: **203 self-contained GLBs / 213 exact-name matches** pass
  (`asset-check.log`). The two candidate assets are additionally covered by the
  dedicated loader/validator checks.
- Content versions: **zero stale references** (`version-check.log`). No runtime
  file was changed, so no bump was needed.
- Offline rebuild hashes, final source/entry consistency and `git diff --check`
  were checked. No Chromium, WebGL, radial-explorer or mobile result is claimed.

Final CPU evidence is in `previews/`: all three rest/side pairs, 120-pixel
reference-size previews and `overview.png`. `rejected/giza-crop.png` records the
source-only crop rejected during this pass. It is not a proposed live model.

Suggested lead commit message:

```text
Add calibrated HST M87 sky map and public-data retry audit

Co-Authored-By: Codex <noreply@openai.com>
```
