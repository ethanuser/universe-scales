# Current Length photo-only source ledger

**Checked:** 2026-10-29 against `/private/tmp/length-coverage-current.json`,
Main's saved production coverage output. Its `.photoOnly` array has **46 names**;
the JSON ledger has the exact same 46-name set and order, with no missing or
extra names. The underlying coverage reports **212/258 modeled, 46 photo-only,
no errors**. This saved production output is the authority for the inventory.

This is a reconciliation of current gaps with existing handoff audits, plus the
six bounded candidate searches documented for the 2026-10-29 source-review pass.
Prior evidence is cited as prior; it is not presented as a new search in this
continuation. No source asset was acquired and no source passed for a new model.
No registry/runtime/dataset/export/image/AGENTS files were changed by this
coverage reconciliation. `ledger.json` is the machine-readable equivalent.

Validation: JSON parse, exact array equality, sorted-set equality, and
`git diff --check` pass. The comparison reads Main's saved coverage file and
does not launch a browser or repeat source searches.

## Bounded candidate checks

These six targeted searches are the fresh checks documented for the dated source-
review pass. Search-result leads are not equivalent to downloaded or approved
assets. Other item rows in the complete ledger cite repository-only prior audits
or explicitly say no item-specific audit was found; they do not imply a fresh
internet search or internet-wide exhaustion.

| Item | Finding | Disposition |
|---|---|---|
| Giant Pacific Octopus | Species-specific commercial models found are under standard paid terms. The previously inspected ffishAsia-and-floraZia CC0 scan is folded/elongated and its bounding width does not encode the catalog's fully spread arm span ([prior review](/Users/ethan/Documents/GitHub/universe-scales/handoff/earth3d/REPORT.md)). | No acquisition. Need a redistributable scan of a spread specimen with measured arm-span landmarks, or a model mapped to a matching body-length definition. |
| Wandering Albatross | The species-identified Phenome10K surface result is cranial, not a complete bird; Museums Victoria exposes CC BY specimen photography rather than a downloadable mesh. | No acquisition. Need whole-body 3D geometry in a documented wingspan pose with measured wingtip distance. |
| Cat Flea | The previously checked CC BY Zenodo record contains a workbook, not whole-body CT/mesh. Fresh results surfaced species imagery, not qualifying complete geometry. | No acquisition. Need an adult whole-specimen scan with compatible terms and voxel/landmark calibration. |
| Bumblebee Bat | DigiMorph's USNM 528306 page lists STL and CT downloads as unavailable; head/nasal data cannot represent the full body-length item. | No acquisition. Need authorized downloadable full-body scan and body-axis calibration. |
| Titanosaur Cast | The targeted search did not identify a downloadable, compatible-licensed scan of the named complete cast. Fossil anatomy and generic reconstructions are not that cast. | No acquisition. Need the actual cast's complete scan, explicit grant, and measured length. |
| Great Pyramid of Giza | The fresh CC BY Sketchfab candidate is photogrammetry from YouTube footage, has 360k triangles and lacks reliable metric/completeness evidence. The prior retry3d candidate also failed source completeness/metric review. A complete upright pyramid's footprint is about 1.57x the listed height. | No acquisition. Need a metrically controlled complete scan and a separate owner decision on measure-axis/framing or Volume mapping; do not distort, crop, or tilt it to evade Length extent checks. |

Fresh result pages actually inspected: [Phenome10K albatross](https://www.phenome10k.org/diomedea-exulans),
[Museums Victoria specimen 6441](https://collections.museumsvictoria.com.au/specimens/429112),
[DigiMorph bat specimen](https://digimorph.geo.utexas.edu/specimens/Craseonycteris_thonglongyai/whole/),
[Sketchfab pyramid candidate](https://sketchfab.com/3d-models/the-great-pyramid-of-giza-4a251113722f4d969b6cf2ca5f35c502),
and [octopus model results](https://www.turbosquid.com/FullPreview/1983823). The Cat Flea and Titanosaur searches did not produce a new source suitable to cite as a lead; their specific result is recorded above without suggesting a new acquisition.

## Complete current list

“Prior audit” points to existing repo evidence; no claim of a repeated search is implied. The blocker is the qualification needed before this task can propose a reusable, calibrated model, not a claim that no source exists anywhere.

| # | Current photo-only item | Prior audit / evidence | Concrete qualification blocker |
|---:|---|---|---|
| 1 | One-Nanometer Transistor Gate | No source-model candidate recorded in the reviewed source handoffs; current production coverage confirms photo-only. | Need a redistributable measured gate cross-section or device metrology with scale and a definition matching gate length, not a generic transistor illustration. |
| 2 | Blu-ray Track Pitch | `handoff/earth3d4/REPORT.md`; `handoff/images3/REPORT.md`. | AFM/SEM images exist, but no verified licensed numerical height map was obtained; image contrast is not surface topography. Need calibrated height data and adjacent-track spacing. |
| 3 | DVD Track Pitch | `handoff/earth3d4/REPORT.md`; `handoff/images3/REPORT.md`; `handoff/images4/REPORT.md` records a schematic image, not measured pit geometry. | Open AFM material reviewed did not expose raw calibrated height arrays. Need numerical AFM/SEM topography with scale; do not infer relief from figures. |
| 4 | Spider Silk Fiber | `handoff/earth3d4/REPORT.md`. | Published AFM study provides images/statistics, not a complete licensed fiber surface; need a diameter-calibrated numerical scan. No cylinder proxy. |
| 5 | Dust Mite | `handoff/source3d-bio/REPORT.md`; `handoff/retry3d/REPORT.md`; latest rejection summarized in root `AGENTS.md`. | Reviewed CC BY candidates are stylized or fragmented/artifact-heavy. Need a complete species-identified specimen scan with body-length calibration. |
| 6 | Cat Flea | `handoff/retry3d/REPORT.md` plus the bounded check above. | The cited CC BY record is a workbook rather than a whole-animal mesh/CT. Need a licensed adult specimen volume/surface with scale. |
| 7 | Paedophryne Amauensis | `handoff/retry3d/REPORT.md`. | Prior accessible CT lead did not yield a verified complete admissible surface; other frog species are not interchangeable. Need exact-species whole-body geometry and calibration. |
| 8 | Bumblebee Bat | `handoff/retry3d/REPORT.md` plus the bounded check above. | DigiMorph rotation/slice views are not downloadable raw scan data; skull/head does not measure whole-body length. Need permitted full-body scan. |
| 9 | Bee Hummingbird | `handoff/retry3d/REPORT.md`. | No accessible licensed species-identified whole-body geometry found in the prior pass. Need complete scan and physical length reference. |
| 10 | Titan Beetle | `handoff/earth3d2/REPORT.md`; `handoff/retry3d/REPORT.md`. | No verified complete downloadable Titanus mesh. Need actual species, not another stag beetle, with reusable rights and scale. |
| 11 | Vivian Hailstone | `handoff/earth3d4/REPORT.md`; `handoff/source3d-hail/REPORT.md`. | The real scan is documented, but an openly licensed STL/PLY or numeric shape grid was not found; UCAR's terms are noncommercial/educational. Need an explicit compatible grant and source geometry. |
| 12 | Queen Alexandra's Birdwing | `handoff/earth3d2/REPORT.md`; `handoff/retry3d/REPORT.md`. | Prior sources were specimen photos, not 3D. Need a female, species-identified model with calibrated wingspan and compatible license. |
| 13 | Meganeura | `handoff/earth3d2/REPORT.md`; `handoff/retry3d/REPORT.md`. | Candidate reuploads lacked resolved original rights or anatomical provenance. Need a rights-clear source mesh with documented fossil reconstruction and span. |
| 14 | Wandering Albatross | `handoff/retry3d/REPORT.md` plus the bounded check above. | Available species scan is cranium-only; photos do not provide 3D. Need whole-body geometry in a measured spread-wing pose. |
| 15 | Giant Pacific Octopus | `handoff/earth3d/REPORT.md`; `handoff/retry3d/REPORT.md` plus the bounded check above. | Existing CC0 scan is folded; its bounds cannot calibrate fully spread arm span. Need suitable scan/pose and landmark measurement. |
| 16 | Titanosaur Cast | `handoff/earth3d/REPORT.md`; `handoff/retry3d/REPORT.md` plus the bounded check above. | No scan of the named complete cast under qualifying terms. Fossil parts or generic life reconstructions cannot stand in for the cast. |
| 17 | Giant Siphonophore | `handoff/earth3d4/REPORT.md`; `handoff/images3/REPORT.md`. | Actual Praya/Apolemia scans have NC-SA terms; CC BY Nanomia is a different, small colony, not the 45.7 m specimen. Need compatible full-colony data; do not repeat zooids. |
| 18 | Great Pyramid of Giza | `handoff/retry3d/REPORT.md` plus the bounded check above. | Scans reviewed failed metric/completeness requirements; a full base also exceeds the listed height extent. Need verified complete scan and owner-approved Length framing decision. |
| 19 | Lituya Bay Megatsunami | `handoff/terrain3d2/REPORT.md`; `handoff/retry3d/REPORT.md`. | Available terrain does not itself locate/measure the 1958 maximum run-up. Need georeferenced historic survey geometry; do not make an arbitrary marker or water surface. |
| 20 | Dinkinesh | `handoff/space3d2/REPORT.md`; `handoff/retry3d/REPORT.md`; `handoff/source3d-space/REPORT.md`. | Papers describe shape solutions, but no verified numerical revised mesh with source/version/frame/coverage and compatible reuse rights was obtained. |
| 21 | Mount Thor Cliff | `handoff/terrain3d/REPORT.md`; `handoff/terrain3d2/REPORT.md`. | A single-valued terrain DEM cannot recover the overhang. Need compatible-licensed measured cliff-face geometry with preserved overhang. |
| 22 | Lake Baikal Depth | `handoff/terrain3d/REPORT.md`; `handoff/terrain3d2/REPORT.md`; `handoff/retry3d/REPORT.md`. | Prior bathymetry record had no established reuse grant and did not map maximum depth to the full lake footprint. Need licensed bathymetry, pinned deepest point and depth-focused framing decision. |
| 23 | Mauna Kea | `handoff/terrain3d/REPORT.md`; `handoff/terrain3d2/REPORT.md`; `handoff/retry3d/REPORT.md`. | Public land/bathymetry exist, but full edifice footprint is much wider than listed base-to-summit height at true scale. Needs explicit framing/measurement-axis decision; no narrowing or vertical stretch. |
| 24 | Kola Superdeep Borehole | `handoff/earth3d4/REPORT.md`. | Bore depth is underground, not the surface cap's size. Need permitted, semantically valid depth representation; do not scale a wellhead to 12,262 m or fabricate a shaft. |
| 25 | Large Hadron Collider Ring | `handoff/terrain3d/REPORT.md`; `handoff/terrain3d2/REPORT.md`; `handoff/retry3d/REPORT.md`. | No compatible-licensed complete surveyed ring-coordinate export; CERN GIS access is restricted. Need actual alignment and circumference calibration, not a circle or diameter. |
| 26 | Channel Tunnel | `handoff/terrain3d/REPORT.md`; `handoff/terrain3d2/REPORT.md`; `handoff/retry3d/REPORT.md`. | Rail/ferry features are not the tunnel alignment; no compatible-licensed surveyed path/profile obtained. Need tunnel alignment and vertical profile, not a terminal-to-terminal line. |
| 27 | Hunga Tonga Eruption Plume | `handoff/terrain3d2/REPORT.md` records an unregistered data-derived terrain candidate; `handoff/images4/REPORT.md` identifies the correct licensed image frame. | Existing evidence is a measured upper surface plus 449 samples but not an integrated current Length model; requires main-owner review/integration and extent/calibration verification. It is not a new source gap. |
| 28 | Danyang-Kunshan Grand Bridge | `handoff/earth3d4/REPORT.md`; `handoff/images4/REPORT.md`. | Existing visual is explicitly schematic; map candidates were CC BY-SA or lacked verified reuse rights. Need compatible licensed route geometry with documented endpoints/calibration. |
| 29 | Mammoth Cave | `handoff/terrain3d/REPORT.md`; `handoff/terrain3d2/REPORT.md`; `handoff/retry3d/REPORT.md`. | Groundwater/contour products are not cave passages. Need licensed georeferenced surveyed passage network matching accumulated route length. |
| 30 | Longest Lightning Flash | `handoff/terrain3d2/REPORT.md`; `handoff/retry3d/REPORT.md`; `handoff/images4/REPORT.md` has an explanatory diagram, not event coordinates. | Certified event coordinates/groups were not obtained. Need verified event membership and compatible coordinate data; channel glyphs remain conceptual. |
| 31 | Typhoon Tip | `handoff/terrain3d/REPORT.md`; `handoff/terrain3d2/REPORT.md`; `handoff/retry3d/REPORT.md`. | Historic imagery exists, but no compatible licensed georeferenced storm subset/boundary matching the wind-field diameter. Do not infer wind extent from cloud pixels. |
| 32 | Earth's Inner Core | No item-specific source-model candidate in the reviewed handoff source audits; production coverage confirms photo-only. | A scientific 3D geometry must match the listed inner-core diameter definition; a generic sphere would be authored geometry. Need reusable numerical seismic/structural product or a user-approved representation boundary. |
| 33 | Contiguous US Longest Distance | `handoff/terrain3d/REPORT.md`; `handoff/terrain3d2/REPORT.md`. | Endpoint pair and entirely-within-US geodesic convention unresolved. Need authoritative endpoints and calculation before mapping any geometry. |
| 34 | Trans-Siberian Railway | `handoff/terrain3d/REPORT.md`; `handoff/terrain3d2/REPORT.md`; `handoff/retry3d/REPORT.md`. | Generic rail vectors/maps do not identify a verified through-route; no compatible coordinate export. Need Moscow–Vladivostok route selection with gaps preserved. |
| 35 | TON 618 Event Horizon | `handoff/deepsky3d/REPORT.md`; `handoff/images3/REPORT.md`. | Spectroscopy constrains mass, not a measured 3D horizon surface; an authored Schwarzschild sphere is not admissible under this source-only model task. |
| 36 | Milky Way Central Bar | `handoff/deepsky3d/REPORT.md`; `handoff/source3d-space/REPORT.md`. | Analytic density models are not measured member coordinates; prior available grids cover a smaller central region. Need a released full-bar catalog/grid and documented selection. |
| 37 | Fermi Bubbles | `handoff/deepsky3d/REPORT.md`. | Public FITS products are angular gamma-ray intensities/templates without emitter distances. Need independent spatial constraints; do not extrude sky maps into 3D lobes. |
| 38 | Magellanic Stream | `handoff/deepsky3d/REPORT.md`; `handoff/retry3d/REPORT.md`. | HI position-position-velocity is not distance geometry and stellar tracers are incomplete. Need spatial data with distances for the full gaseous stream. |
| 39 | IC 1101 | `handoff/deepsky3d/REPORT.md`. | Published edge derives from 2D surface-brightness/stellar-density profiles, not volumetric geometry. Need measured 3D distribution; do not fit a sphere/ellipsoid. |
| 40 | Andromeda Gas Halo | `handoff/deepsky3d/REPORT.md`; `handoff/images4/REPORT.md` has an explicitly labeled illustration. | Project AMIGA's sparse integrated sightlines do not determine a volumetric boundary. Need public measured 3D halo product; retain the image as illustration only. |
| 41 | Porphyrion | `handoff/deepsky3d/REPORT.md`. | Author-specific radio data were not obtained; general LoTSS service has CC BY-SA terms, outside allowed license policy. Need source data under compatible terms and depth/geometry support. |
| 42 | Distance to the Virgo Cluster | `handoff/deepsky3d/REPORT.md`. | This is observer-to-cluster distance, not cluster size. Existing Virgo catalogs cannot be scaled to it; need owner-approved non-diagram representation or keep photo-only. |
| 43 | Baryon Acoustic Oscillation Scale | `handoff/deepsky3d/REPORT.md` already contains a BOSS galaxy-slice model; `handoff/images3/REPORT.md` records its pair-separation image. | It remains photo-only in current production despite prior candidate entry. Needs owner integration/review of existing candidate, not a new source search; verify the catalog selection and not falsely show a bubble. |
| 44 | Putative Giant Arc | `handoff/deepsky3d/REPORT.md`. | Public absorber catalogs exist, but exact cleaned membership was not reproduced and terms for author-derived measurements were unverified. Need cleaned membership and compatible rights, not an exploratory hand-selected group. |
| 45 | Hubble Radius | `handoff/deepsky3d/REPORT.md`; `handoff/images3/REPORT.md`. | Derived cosmological distance scale, not a measured 3D surface. Need an owner-approved representation change; do not author a sphere or ruler model under the current source-only criteria. |
| 46 | JADES-GS-z14-0 | `handoff/deepsky3d/REPORT.md`. | Public imaging/spectroscopy does not provide genuine 3D galaxy geometry or a source model for the observer distance. Need a real spatial product; no primitive galaxy or distance diagram. |

## Scope and next step

`ledger.json` contains exactly these 46 names, in production coverage order. No
additional items from stale lists are included. `Oort Cloud`, `Solar System`,
and the accepted biological models are not photo-only gaps. The present pass
found no new asset to acquire. Existing unregistered candidates (notably the
Hunga Tonga terrain work and BAO model) are called out as integration/review
items rather than falsely described as absent source data. Continue only with
qualified source releases or owner decisions on representation conflicts;
this ledger does not claim all internet sources have been exhausted.
