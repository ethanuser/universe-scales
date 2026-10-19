# terrain3d2 — public geography and measured Earth-event data

2026-10-18, branch `codex/terrain3d2`. **Five new models are registered; ten
targets are skipped.** No existing entry is replaced. No dataset, frontend
export, `images/`, application JavaScript, CSS or HTML was changed. There are no
required dataset changes for these five integrations.

Every geometric vertex comes from a public elevation grid or NASA stereo-height
retrieval. NPS trail and NOAA damage vectors are rasterized onto the corresponding
terrain textures. No hand-authored cliff, crater, funnel, cloud volume, ruler,
display block, crop wall, underside, invented trace or random point is included.
All models retain geographic horizontal metre coordinates. The gravity model's
vertical axis is explicitly an anomaly plot, not physical relief.

Work is **uncommitted**, as explicitly requested in the brief's known-sandbox
exception. Chromium and git staging/commit were not retried. The pre-existing
`.DS_Store` modification and untracked `venv` symlink are not part of this job.

## New entries

| Item / final model ID | Source and interpretation | Bytes | Triangles | CPU rest extent / listed value |
| --- | --- | ---: | ---: | ---: |
| Mount Thor Cliff / `terrain3d2-mount-thor` | Public Mapzen elevation tiles; 1.4 × 1.0 km west-face aperture; **1×** vertical scale | 995,508 | 36,864 | 1.248× |
| Appalachian Trail / `terrain3d2-appalachian-trail` | All **30** original June-2023 NPS treadway features over eastern-US terrain; **8×** relief | 1,193,772 | 32,768 | 0.675× |
| El Reno Tornado / `terrain3d2-el-reno` | Named NWS `ElReno_Poly` survey polygon, cropped over USGS 3DEP and public NAIP imagery; **1×** relief | 2,339,436 | 41,472 | 1.219× |
| Hunga Tonga Eruption Plume / `terrain3d2-hunga-tonga` | NASA GOES-17/Himawari-8 measured upper surface and **449** observed sample locations; NOAA ETOPO1 below; **1×** height | 306,932 | 8,549 | 1.138× |
| Chicxulub Crater / `terrain3d2-chicxulub` | Scripps V33.1 gravity-anomaly grid; vertical plotting scale **500 display m/mGal**, not crater depth | 924,092 | 28,084 | 1.143× |

All are self-contained, below 3 MB / 60k triangles, and require no decoder.
`display_label` is unset. Hunga's single in-model label is the short measured
height `58.36 km`; scope and limitations remain in registry notes and source files.

### Interpretation and review limits that matter

- **Thor:** A single-valued DEM cannot capture an overhang. The complete terrain
  tile conversion rounds the face and is not a rock-face scan. Tilezen documents
  ArcticDEM and Canadian elevation sources here, but provider headers were absent;
  the precise per-tile mix is not asserted. A separate direct ArcticDEM service
  export had large zero/no-data holes and was rejected after viewing its CPU
  preview. No gap was filled by this builder. The final crop is an actual subset,
  not geometry adjusted to reach the gazetteer summit elevation or the catalog
  cliff-height number. Sources: [Tilezen datasets](https://github.com/tilezen/joerd/blob/master/docs/data-sources.md),
  [Canadian gazetteer](https://geonames.nrcan.gc.ca/search-place-names/unique?id=OAQLW&wbdisable=true),
  [ArcticDEM rights](https://www.pgc.umn.edu/guides/stereo-derived-elevation-models/pgc-dem-products-arcticdem-rema-and-earthdem/).
- **Trail:** The 2023 survey layer is not the catalog's 2024 walking-length
  inventory. Accumulated route distance is different from geographic extent.
  Neither the route nor the surrounding map is stretched; the regional aperture
  keeps the resting extent inside the size rule. Source bends, separate club
  features and gaps are retained, with no connector invented between fragments.
  The line's texture width is cartographic. Source: [NPS A.T. maps](https://www.nps.gov/appa/planyourvisit/maps.htm),
  whose webmap links the [actual treadway service](https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/ANST_Facilities/FeatureServer/7).
- **El Reno:** The source damage polygon is not the instantaneous tornado
  envelope or a precise maximum-width measurement. Its whole original geometry
  is pinned, while the model shows a local 5.1 km aperture south of the airport.
  Its historical `EF3+` attribute is preserved without changing the event rating.
  The aerial background is later geographic context: the center catalog tile is
  USDA NAIP, acquired **2021-05-29**. No claim is made that this is a 2013 damage
  photograph, or that every mosaic tile has the same date. Sources:
  [NWS event account](https://www.weather.gov/oun/events-20130531),
  [NWS DAT polygon layer](https://services.dat.noaa.gov/arcgis/rest/services/nws_damageassessmenttoolkit/DamageViewer/FeatureServer/2),
  [USGS NAIP-only imagery service and public-domain statement](https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer).
- **Hunga:** The source is nominal **04:30 UTC** on 2022-01-15, with actual line
  observations **04:36:44–04:37:32 UTC**. Native samples inside a 64 km aperture
  range from **32.503 to 58.357 km** after the documented quality filter
  (rating ≥ 1). Missing data remain holes. This intentionally sparse measured
  top is not a complete mushroom cloud or reconstructed column; no stem or
  enclosed body was invented. The texture uses the simultaneous recorded
  Himawari-8 IR brightness temperature. Point markers denote observations, not
  droplets. Historical ETOPO1 seabed data provide geographic height context,
  without claiming to be a post-eruption bathymetric survey.
  Source: [NASA data and study index](https://science-data.larc.nasa.gov/LaRC-SD-Publications/2022-11-22-001-KMB/),
  [actual NetCDF](https://science-data.larc.nasa.gov/LaRC-SD-Publications/2022-11-22-001-KMB/data/A2022015.0430.stereo_CTH.nc).
- **Chicxulub:** This shows an observed gravity field, not the buried crater's
  physical surface or an inferred rim. A gravity plotting gain is not vertical
  exaggeration of a geological elevation. The extractor identifies V33.1 even
  though newer files coexist in the download directory. Sampling at one minute
  does not imply one-minute effective resolution; the provider documents a
  marine low-pass filter with half gain at 16 km. Land and marine fields differ
  in information content. Sources: [extractor](https://topex.ucsd.edu/cgi-bin/get_data.cgi),
  [V33 documentation](https://topex.ucsd.edu/pub/global_grav_1min/README_V33.txt),
  [scientific references](https://topex.ucsd.edu/marine_grav/mar_grav.html).
  The provider's [data-management plan](https://topex.ucsd.edu/pub/sandwell/SF_geodesy_proposal.pdf),
  page 38, describes unrestricted distribution of its global gravity/bathymetry
  grids. This is the reuse basis, **not** the adjacent GPL statement about
  MB-System software and not an invented CC license. The source snapshot and PDF
  hash are in `sources/terrain3d2/chicxulub/rights-and-grid.json`.

## Skipped targets and searches

These keep their existing photo. “Skipped” means this pass did not establish a
usable and correctly calibrated source, not that no relevant data exist anywhere.

| Target | Sources inspected / why not registered |
| --- | --- |
| Lituya Bay Megatsunami | Checked USGS Miller PP 354-C references and the [2020 reconstruction paper](https://nhess.copernicus.org/articles/20/2255/2020/). The latter discusses published run-up surveys but also simulated/simplified geometry, which was not imported. The USGS report endpoint was unavailable to this session. No independently usable georeferenced maximum-run-up survey coordinate was obtained. A whole-bay terrain scene also cannot satisfy the 524 m extent rule at true geographic scale; it must not be normalized to wave height. No invented run-up marker or water surface was made. |
| Lake Baikal Depth | Found [GFZ De Batist/Charlet bathymetry](https://dataservices.gfz-potsdam.de/SDDB/showshort.php?id=escidoc%3A76654) and its [contour archive directory](https://datapub.gfz-potsdam.de/download/10.1594.GFZ.SDDB.1204/). The record displays an empty license field and an “in review” status; an applicable redistribution grant was not established. A generic lake-bottom bowl would violate the hard rule. The whole lake footprint also does not measure its 1,642 m maximum depth. |
| Mauna Kea | Inspected [GEBCO grid availability](https://www.gebco.net/data-products/gridded-bathymetry-data) and [USGS's summit-to-seafloor definition](https://www.usgs.gov/faqs/how-big-are-hawaiian-volcanoes). Real land/bathymetry data exist, but a scene including the summit and the offshore base has a geographic width far larger than the listed height. No complete true-scale scene meeting the 0.6–1.3× resting size rule was established; no narrow invented mountain or compressed footprint was substituted. This needs a framing/quantity decision before integration. |
| Large Hadron Collider Ring | Inspected [CERN GIS access documentation](https://sce-dep.web.cern.ch/knowledge-centre/geographic-information-system-gis/) and survey/alignment publication search results. CERN's engineering GIS requires a CERN account. A public, reusable surveyed ring-coordinate export and its terrain registration were not established. No circular primitive or traced illustration was substituted. |
| Channel Tunnel | Searched published GIS/engineering alignments and inspected the public Natural Earth rail vectors near the crossing. The apparent crossing candidate `rwdb_rr_id=9559` is classified **Railroad ferry** and joins rail-network junctions, so it cannot be asserted to be the measured tunnel alignment. [OSM's tunnel documentation](https://wiki.openstreetmap.org/wiki/Channel_Tunnel) discusses alignment uncertainty; ODbL data are also outside this job's requested license set. Bathymetry alone does not supply tunnel geometry. No line between terminals was invented. |
| Mammoth Cave | Inspected [NPS cave-mapping documentation](https://www.nps.gov/maca/learn/cave-mapping.htm), the NPS geologic/GIS catalog and cave-research dataset searches. Found mapping explanations, surface geology and groundwater products, but no openly licensed, downloadable passage-survey dataset usable for this scene. Those products are not underground passage coordinates. No branching tunnel network was invented. |
| Contiguous US Longest Distance | Checked the existing item's Florida–Washington definition and source trail. No authoritative measured endpoint pair defining the claimed entirely-within-US great-circle maximum was established. General relief and coastlines do not establish that extremum. No guessed endpoints or schematic great-circle line were added. The items job should resolve the definition and cite endpoint coordinates before a model is attached. |
| Trans-Siberian Railway | Downloaded and inspected [Natural Earth railroads](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/railroads/) (`ne_10m_railroads.geojson`, 25,413 world features). The attributes do not identify a Trans-Siberian through-route. A verified Moscow–Vladivostok feature selection, retaining actual route choices and gaps, was not established. No city-to-city segments or arbitrary joins were drawn. |
| Typhoon Tip | Found the [public NOAA GIBBS full-disc image credited on Commons](https://commons.wikimedia.org/wiki/File:Typhoon_Tip_and_Typhoon_Sarah_(1979).png). A navigated/georeferenced storm subset with a verified image-to-Earth mapping was not obtained. The 2,220 km wind-field diameter is not the cloud image's visible boundary. An arbitrary photo-on-disk or guessed cloud-size drape would not meet the hard rule or true-scale requirement. |
| Longest Lightning Flash | Located the [WMO certification paper](https://journals.ametsoc.org/view/journals/bams/aop/BAMS-D-25-0037.1/BAMS-D-25-0037.1.xml?tab_body=fulltext-display), identifying the 2017-10-22 08:56:45.834 UTC event. The full article endpoint denied access in this session. The NOAA GOES-16 public S3 listing for `GLM-L2-LCFA/2017/295/08/` with the relevant 08:56 file prefix returned no objects. No certified event/group-coordinate subset was obtained. A hand-drawn flash or unrelated GLM event would be misleading. |

No dataset changes are required for the registered five. For the skipped
US-distance item, an exact replacement value or description is **not proposed**:
the endpoint definition remains unverified. The Mauna Kea and Lituya issues are
quantity-versus-footprint conflicts, not requests to change their existing values.

## Rebuild and integration

Builder: `scripts/build_terrain3d2_models.py`. It reuses the first-round terrain
coordinate, raster sampling, tile sampling, polygon rasterization and GLB helpers.
Normal builds are offline:

```sh
./venv/bin/python scripts/build_terrain3d2_models.py
```

`--prepare --cache /tmp/terrain3d2` acquires or reuses cached sources and pins
compact numerical subsets. NASA preparation alone needs `netCDF4`; ordinary
builds use existing NumPy/Pillow dependencies. Full original terrain/imagery files
remain in `/tmp`, while source subsets, raw vector features, hashes and precise
request URLs are preserved under `content/visualizations/models/sources/terrain3d2/`.

Each final entry JSON is in this folder, with no `replaces` field because no old
entry was replaced. After keeping main's registry during merge, register all five:

```sh
for entry in handoff/terrain3d2/*.entry.json; do
  id=$(basename "$entry" .entry.json)
  python3 scripts/register_model.py "$entry" "content/visualizations/models/$id.glb"
done
```

The existing CPU preview and loader audit scripts now accept this handoff as well
as the original terrain3d handoff; their original default behavior is preserved:

```sh
node scripts/audit_terrain3d_models.mjs terrain3d2
./venv/bin/python scripts/preview_terrain3d_cpu.py --job terrain3d2
```

Source notes for every model are `content/visualizations/models/sources/terrain3d2-<name>.md`.

## Verification and deferred browser work

- Node: **228 passed**, zero failures.
- Python: **145 run**, one skip, zero failures. Five new tests verify pinned hashes,
  registry/asset consistency, native metric vertices, absence of invented display
  volumes, original survey identities, gravity units, and Hunga native-neighbor
  triangles/quality gaps/measured sample positions.
- `fetch_model_assets.py --verify`: **195 GLBs / 206 exact-name matches**, passed.
- `bump_versions.py --check`: **zero stale references**. No runtime JS/CSS changed.
- Full Khronos validation completed for all 195 registered GLBs: **zero errors**.
  All five additions have **zero warnings**; warnings remain in nine unchanged
  existing assets. `validation.json` is the actual complete validator output.
- Actual vendored GLTFLoader parsed all five new assets. Orthographic resting
  geometry and layout widths pass the size rule: see `loader-audit.json`.
- CPU rest/quarter-camera renders were viewed for every final model; see
  `previews/terrain3d2-*.png`, `previews/overview.png` and
  `previews/geometry-audit.json`. El Reno imagery and the Thor pose were refined
  after visual review. Full-resolution numerical inputs remain pinned even when
  the Appalachian mesh keeps every second sampled terrain vertex.

**These checks do not certify WebGL, real materials/lighting, perspective,
production model-lab size audit, SVG label collision, radial explorer, picking,
grounding, fullscreen or mobile behavior.** The lead must run the production
`model_lab.cjs shot`, `audit`, `explorer` and mobile review outside this sandbox.
CPU side views can be edge-on because these are open measured surfaces, with no
invented thickness or walls. Hunga's data gaps are intentional; if that sparse
observational appearance is unsuitable, keep its photo rather than filling them.

Temporary preparation-only packages were installed under `/tmp/terrain3d2-deps`,
**not** into the shared venv: netCDF4 1.7.5, cftime 1.6.6, certifi 2026.10.18,
pypdf 6.21.1 and pypdfium2 5.14.0. The PDF packages were used to inspect the
gravity provider's data-use page. No runtime or repository dependency was added.

Test/verification logs are copied into `checks/`. A local commit helper contains
only this job's explicit paths and the requested co-author trailer; it was not run.
