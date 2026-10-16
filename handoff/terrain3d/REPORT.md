# terrain3d — real geographic data, 2026-10-16

Nine new Length models are registered on `codex/terrain3d`. All preserve geographic
horizontal scale; vertical gain is explicit below and in each registry note.
No existing model is replaced. No dataset, frontend export, `images/`, runtime
JavaScript or CSS was changed. No dataset changes are required for integration.
Work remains **uncommitted**, as the job's specific sandbox instruction requests.
No push, branch change, merge, rebase, browser-launch retry or git-commit retry was
attempted. No packages were installed and the shared venv was not modified.

## Delivered models

Every ID below has a GLB under `content/visualizations/models/`, a source note
`content/visualizations/models/sources/<id>.md`, and its complete final registry
entry in this folder as `<id>.entry.json`. There are no `replaces` fields because
these are additions.

| Exact dataset item | ID suffix after `terrain3d-` | Bytes | Triangles | Vertical gain | CPU rest extent / value |
| --- | --- | ---: | ---: | ---: | ---: |
| Angel Falls | angel-falls | 786,372 | 30,240 | 1× | 1.215 |
| Victoria Falls | victoria-falls | 974,356 | 38,496 | 1× | 1.171 |
| Strait of Gibraltar | gibraltar | 615,172 | 25,658 | 1× | 1.268 |
| Lake Tanganyika | tanganyika | 563,644 | 17,536 | 4× | 0.958 |
| Grand Canyon Length | grand-canyon | 741,700 | 23,756 | 5× | 1.002 |
| Suez Canal | suez | 552,396 | 18,284 | 3× | 0.995 |
| San Andreas Fault | san-andreas | 1,784,128 | 43,672 | 5× | 0.936 |
| Great Barrier Reef | great-barrier-reef | 839,676 | 25,920 | 8× | 0.698 |
| Sahara | sahara | 714,360 | 24,432 | 12× | 1.104 |

The nine assets total 7,571,804 bytes. All are self-contained, use ordinary glTF
meshes/materials and embedded JPEG textures, require no decoder, and are below
1.8 MB and 44,000 triangles each. Their on-screen names remain the exact dataset
names; `display_label` is unset. Only the separate length rulers have in-model
text. Caveats remain in registry notes and source documents.

## What the representations mean

- **Angel Falls:** real, unexaggerated terrain at the published waterfall
  coordinate in a 1.1 km square. The resting camera looks toward the escarpment.
  The sampled relief is about 827 m; it is not forced to the catalog's 979 m
  total descent. The crop and coarse SRTM surface do not resolve every lower
  cascade, a vertical/overhanging rock face, or falling water. This is a terrain
  locator and escarpment view, not a waterfall scan.
- **Victoria Falls:** a 2 km east-west terrain crop around the present gorge,
  calibrated against the catalog's 1,708 m falls width. SRTM smooths the narrow
  gorge and does not provide the water curtain. This is the weakest visual
  candidate; the lead should assess the terrain-only view alongside the photo.
  A trial Natural Earth river overlay was removed after visual inspection: its
  regional cartographic centerline was too coarse for this small crop.
- **Gibraltar:** an 18 km square around the narrow continental crossing. Actual
  NOAA ETOPO1 depth is combined with Mapzen land elevation using a Natural Earth
  coastline mask. A partially transparent sea-level surface is at zero metres.
  The crop is larger than the catalog's 14.2 km crossing and its edges are not
  purported crossing endpoints. Coarse coastline/bathymetry cannot support
  navigation or precise coastal measurements.
- **Tanganyika:** Natural Earth's actual lake outline in East African Rift
  terrain. Water color marks the sampled lake surface, with no lake-floor
  reconstruction. It is a length model, not a depth model.
- **Grand Canyon:** terrain sampled directly from the USGS 3DEP elevation service,
  plus the clipped Natural Earth Colorado centerline. The river line is a
  widened visibility symbol draped on the actual rendered mesh. The map crop
  includes context; it does not identify the canyon rim or precisely delimit
  Lees Ferry/Grand Wash. An independent 446 km ruler shows the catalog's
  river-course distance. The geographic footprint is not stretched to it.
- **Suez:** two original generalized Natural Earth canal line features, with
  their separate source paths retained, over terrain and coastal bathymetry.
  The 193.3 km ruler is independent of the mapped path; the line width is a
  display symbol. This is not a current engineering plan or a full port-approach
  inventory.
- **San Andreas:** 8,042 source features selected by the USGS database's
  `fault_name LIKE '%San Andreas%'`. Section names, source fragments and gaps
  remain pinned. Display simplification retains original vertices with a 300 m
  horizontal tolerance, separately for each fragment; no missing reach is
  joined. Orange width is a symbol, not a physical chasm. The 1,210 km ruler
  represents the catalog system length, not a sum over all branching traces.
- **Great Barrier Reef:** 3,811 actual Reef Authority polygon features whose
  `FEAT_NAME` is `Reef` and which intersect the viewing aperture. This is a
  rectangular geographic selection, not an exact park-boundary inventory or a
  claim of 3,811 distinct biological reefs. Measured footprints are rasterized
  in turquoise over regional terrain/ETOPO1; no individual coral heights or
  reef surface geometry is invented. The full pinned source geometries and
  license snapshot are supplied.
- **Sahara:** real northern African relief on a curved Earth. The authored
  rectangular aperture is not asserted to be the desert's climatic boundary;
  elevation colors are not satellite imagery, dunes, vegetation or lithology.
  The catalog's approximate 4,800 km east-west span is the calibration reference.

All opaque sides and undersides are arbitrary display cuts. They are not
observed cliffs, stratigraphy, geological bases or subsurface boundaries. The
regional scenes retain spherical Earth curvature; small scenes use an east/up/
south local metric frame. These are geographic approximations, not ellipsoidal
survey products. Large scenes retain every second original grid vertex in each
direction while preserving the full source elevation-shading texture. Reef
footprints are rasterized independently at 1024 pixels, so small reefs do not
disappear into the coarser mesh sampling.

Two source checks materially changed the implementation: high-zoom Mapzen oceans
were nearly flat zero around Gibraltar, so coastal models now request signed,
unrendered NOAA ETOPO1 elevations explicitly. The first Grand Canyon Mapzen draft
had an implausible −37 m sample near Lake Mead. The final grid comes directly from
USGS 3DEP and spans approximately 330–2,783 m. No bump, clamping of that anomaly,
manual extreme correction or invented relief was used.

## Provenance and rights

The compact offline inputs are in
`content/visualizations/models/sources/terrain3d/<suffix>/`. `provenance.json`
records exact crop/grid dimensions, all source requests and download SHA-256s,
derived-file hashes, sampled elevation range and processing. `terrain.npz` pins
the elevations and coordinates; `vectors.geojson.gz` is lossless compression of
the selected original geometry. Global Natural Earth land is supplied as a
derived crop mask rather than repeatedly vendoring the whole world. Tile provider
headers were recorded when offered; this endpoint returned no provider header
for these requests, so no per-tile provider identification is claimed.

Sources opened during this work include:

- [Mapzen Terrain Tiles, AWS](https://registry.opendata.aws/terrain-tiles/),
  [provider attribution](https://github.com/tilezen/joerd/blob/master/docs/attribution.md)
  and [source documentation](https://github.com/tilezen/joerd/blob/master/docs/data-sources.md).
  The global SRTM/GMTED and U.S. 3DEP components used here are USGS government data;
  Mapzen/Tilezen attribution is retained. Joerd's software license is not treated
  as the license for all terrain providers.
- [USGS 3DEP bare-earth elevation service](https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer),
  exported with raster function `None`, signed float TIFF and bilinear sampling.
- [NOAA ETOPO1 elevation service](https://gis.ngdc.noaa.gov/arcgis/rest/services/DEM_mosaics/ETOPO1_ice_surface/ImageServer),
  likewise exported as signed elevations rather than a rendered map. Its native
  one arc-minute cells are much coarser than some output grids.
- [Natural Earth rights](https://www.naturalearthdata.com/about/terms-of-use/)
  and [river/canal documentation](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-rivers-lake-centerlines/).
  Natural Earth states that its data are public domain. Exact original GitHub
  GeoJSON download URLs and hashes are in each relevant provenance file.
- [USGS Quaternary Fault and Fold Database](https://www.usgs.gov/programs/earthquake-hazards/faults)
  and [its feature service](https://earthquake.usgs.gov/arcgis/rest/services/haz/Qfaults/MapServer/21).
  The selection was paged through the complete response, rather than accepting
  the first truncated 2,000 records.
- [Reef Authority spatial-data page](https://www.gbrmpa.gov.au/about-us/spatial-data-information-services)
  and [official feature layer](https://services-ap1.arcgis.com/8gXWSCxaJlFIfiTr/arcgis/rest/services/Great_Barrier_Reef_Features_20/FeatureServer/64).
  The actual publisher item `816f4d747cd94d84acfd924b27f581d8` explicitly grants
  CC BY 4.0; the relevant fields are pinned in `great-barrier-reef/reef-license.json`.
  Credit: Great Barrier Reef Marine Park Authority 2023. Selection/rasterization
  are disclosed modifications. No endorsement is implied.

Dimension/context references are linked individually in each model's source note:
UNESCO for Victoria Falls, NPS for the Grand Canyon, Suez Canal Authority for
193.3 km, NASA MODIS for the Sahara span, and opened geographic references for
Angel Falls, Gibraltar and Tanganyika. Existing dataset values were retained;
the source geometry is never fitted to make their numbers appear exact.

## Verification and visual review

- `node --test tests/*.test.cjs tests/*.test.mjs`: **228 pass**.
- `./venv/bin/python -m unittest discover -s tests -p 'test_*.py'`:
  **122 run, one existing skip, no failures**. The six new tests cover real-grid
  preservation, winding/normal direction, source hashes, license snapshots,
  signed bathymetry/sea level, source feature identities, triangle-based path
  draping, asset budgets, registry equality and orthographic rest scale.
- `python3 scripts/fetch_model_assets.py --verify`: **161 GLBs / 172 exact-name
  matches verify**.
- `python3 scripts/bump_versions.py --check`: **zero stale references**.
  No runtime JS/CSS changed, so no version rewrite was needed.
- `node scripts/audit_terrain3d_models.mjs`: all nine load through the actual
  vendored GLTFLoader and satisfy the CPU rest extent and layout-width limits.
  The loader uses placeholder image decoding; it does not certify textures.
  Machine-readable results: `loader-audit.json`.
- Khronos glTF validator via the required `validate-models.cjs` invocation:
  **all nine new models have zero errors and zero warnings**. The complete
  registry has zero errors and 1,867 warnings in nine inherited models, mainly
  the unchanged giraffe/blue-whale imports. Per-delivery reports:
  `validation.json`; full registry report remains in the usual model directory.
- Repeated offline generation produced identical GLB hashes. Normal generation
  does not fetch URLs; only the explicit `--prepare` path accesses the network.

`previews/<id>.png` contains the resting pose and a quarter-camera view for each
model. All pairs were opened and inspected; the final `previews/overview.png`
was also opened after reducing mesh density. A preliminary Angle Falls pose
showed too much display-cut wall; its final pose exposes the escarpment. Several
regional models naturally show a flat display side when viewed edge-on.

**These are CPU orthographic approximations.** The rasterizer omits production
lighting, tone mapping, shadows, perspective, real SVG label collision/opacity,
constant-pixel guide widths, picking/grounding/UI, and hardware performance.
Its separate line pass can show a centerline through a terrain side in a quarter
view. Chromium/model-lab and git commits are documented sandbox limits and were
not retried, per the brief. Production `shot`, `audit`, `explorer`, `mobile` and
frame-rate review remain for the lead outside the sandbox. Browser certification
is not claimed by the table above.

## Integration and rebuild

Keep main's model registry when resolving a registry conflict, copy this job's
GLBs/scripts/sources/handoff, then run:

```sh
sh handoff/terrain3d/register.sh
./venv/bin/python scripts/build_terrain3d_models.py
node scripts/audit_terrain3d_models.mjs
./venv/bin/python scripts/preview_terrain3d_cpu.py
```

`register.sh` is idempotent and only registers the nine entries. The normal
builder uses the pinned sources; optional source preparation is:

```sh
./venv/bin/python scripts/build_terrain3d_models.py --prepare --cache /tmp/terrain3d
```

Use a fresh cache to acquire a new upstream snapshot. A particular model can be
built/prepared by adding its suffix, for example `grand-canyon --prepare`.
Source refresh can change upstream data and should receive a new review.

Outside the sandbox, review with the production renderer before publishing:

```sh
node scripts/model_lab.cjs shot /tmp/terrain3d-lab "Great Barrier Reef" --views rest,side --bg dark
node scripts/model_lab.cjs shot /tmp/terrain3d-lab "Victoria Falls" --views rest,side --bg dark
node scripts/model_lab.cjs audit
node scripts/model_lab.cjs explorer /tmp/terrain3d-lab "Grand Canyon Length"
node scripts/model_lab.cjs mobile /tmp/terrain3d-mobile
```

Suggested commit subject: `Add nine geography models from elevation and map data`.
Use the requested `Co-Authored-By: Codex <noreply@openai.com>` trailer when the lead
commits. The pre-existing untracked `venv` symlink is not part of this delivery.

## Deferred targets and open limitations

These are deliberately absent, rather than represented by invented geometry:

| Target | Reason / useful next source |
| --- | --- |
| Mount Thor Cliff | A single-valued DEM cannot reconstruct the claimed overhang. A properly licensed measured/photogrammetric cliff mesh would be needed for the rock face. |
| Mauna Kea including submerged edifice | USGS confirms the approximate 10,211 m base-to-summit definition, but the full edifice's horizontal footprint is far larger than that height. A whole-footprint terrain model at true horizontal scale conflicts with the explorer's 1.3× extent rule. No narrowed or vertically stretched substitute was added. |
| Lake Baikal Depth | No authoritative bathymetric grid and verified maximum-depth location were acquired. A surface-elevation tile or fabricated bowl cannot represent the 1,642 m depth. |
| Lituya Bay Megatsunami | No adequately verified georeferenced 524 m run-up scar boundary/point was acquired. An arbitrary marker on the modern slope would misstate the historical measurement. |
| Chicxulub Crater | No suitable redistribution-ready local gravity-anomaly grid was acquired. Modern surface terrain is not the buried crater, and gravity anomalies must retain their physical units/interpretation rather than becoming invented crater relief. |
| Channel Tunnel | No compatible-licensed tunnel alignment plus vertical profile was acquired. A straight line below the strait would imply an unsupported surveyed path/depth. |
| Large Hadron Collider Ring | No verified compatible-licensed actual ring alignment was acquired. A mathematically perfect circle over Geneva terrain was not substituted for map geometry. |
| Mammoth Cave | No compatible-licensed georeferenced surveyed passage network was acquired. The catalog is accumulated branching passage length, not the footprint diameter. |
| Appalachian Trail | Found the official NPS/ATC centerline service and its joint 2023 credit, but did not establish the explicit CC BY/CC0/public-domain status required by this brief for all contributions. It was not bundled. This is a sourcing follow-up, not a claim that use is prohibited. |
| Contiguous US Longest Distance | The exact endpoints and the catalog's entirely-within-country geodesic definition were not independently pinned. A convenient diagonal was not invented. |
| Trans-Siberian Railway | No complete, compatible-licensed Moscow–Vladivostok alignment was acquired. City-to-city straight segments would not represent the railway route. |

The Mauna Kea source opened was
[USGS: How big are the Hawaiian volcanoes?](https://www.usgs.gov/faqs/how-big-are-hawaiian-volcanoes).
The Appalachian lead is the official `ANST_Centerline` feature service, ArcGIS
item `71975f7fc14347c7a6c1059fdb593f91`; its publisher metadata points to NPS IRMA
reference `2319082`. No trail data were committed.
