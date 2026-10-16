# Grand Canyon Length: elevation and map geometry

Regional terrain sampled directly from the USGS 3DEP elevation service and a clipped Natural Earth Colorado River centerline. Relief is exaggerated 5 times; the cyan line is widened for visibility and draped on the mesh, not a water-depth survey. The map window includes context beyond the canyon and does not define its rim or exact Lees Ferry-to-Grand Wash endpoints. The independent 446 km ruler represents the published river-course length; the geographic map is not stretched to that route length. Horizontal coordinates are not normalized to the catalog size. Colors are illustrative. The opaque sides and flat underside are arbitrary display cuts, not real cliffs or geological strata. Mapzen / Tilezen; SRTM, GMTED2010 and United States 3DEP terrain courtesy of the U.S. Geological Survey; ETOPO1 ocean bathymetry courtesy of NOAA; Natural Earth public-domain map data; adaptation by Universe Scales.

## Pinned source and processing

`terrain3d/grand-canyon/provenance.json` records every tile URL, SHA-256, provider header, grid bounds and elevation range, plus the original vector download hashes. The compact `terrain.npz` stores 161 × 257 original sampled elevations and longitude/latitude. The mesh retains every 2 grid vertex along each axis (81 × 129), while the elevation-shading texture retains the full input grid. `vectors.geojson.gz` retains losslessly compressed source fragments independently. Global land is pinned as a derived crop mask, not distributed as a world dataset. Source grid spacing is a sampling choice, not a claim of DEM resolution. Small scenes use local east/up/south coordinates with spherical WGS84-radius distances; regional scenes use a spherical Earth of radius 6371.0088 km in a local tangent frame. Large-scene curvature is retained; no map projection rescales the footprint to fit the quantity. Geographic approximation differs slightly from ellipsoidal surveying. Vertical gain: **5×**. No extreme-point correction or procedural terrain is added.

Normal offline rebuild: `./venv/bin/python scripts/build_terrain3d_models.py grand-canyon`. Optional network source refresh: add `--prepare --cache /tmp/terrain3d`. Registration: `python3 scripts/register_model.py handoff/terrain3d/terrain3d-grand-canyon.entry.json content/visualizations/models/terrain3d-grand-canyon.glb`.

## Sources and rights

- https://registry.opendata.aws/terrain-tiles/
- https://github.com/tilezen/joerd/blob/master/docs/data-sources.md
- https://github.com/tilezen/joerd/blob/master/docs/attribution.md
- https://www.naturalearthdata.com/about/terms-of-use/
- https://www.nps.gov/grca/faqs.htm
- https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage?bbox=-114.20537109375%2C35.545625%2C-111.44462890625%2C36.954375&bboxSR=4326&imageSR=4326&size=257%2C161&format=tiff&pixelType=F32&interpolation=RSP_BilinearInterpolation&renderingRule=%7B%22rasterFunction%22%3A+%22None%22%7D&adjustAspectRatio=false&f=image
- https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_rivers_lake_centerlines.geojson

Source pages were opened during preparation on 2026-10-16. Mapzen attribution applies alongside provider rights; the Joerd software license alone is not a license for elevation data. USGS SRTM/GMTED/3DEP and NOAA ETOPO1 are U.S. government data; Natural Earth states its data are public domain. No aerial photography, proprietary map tiles, invented survey traces or external runtime dependencies are used.
