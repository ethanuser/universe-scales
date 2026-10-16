# Victoria Falls: elevation and map geometry

The present Zambezi gorge and upstream terrain around the falls, with a 2 km east-west context window. Calibration is the published 1,708 m width, not the DEM relief. SRTM smooths the narrow gorge; this is terrain, not a reconstruction of the seasonally changing water curtain. No invented waterfall surface is added. Horizontal coordinates are not normalized to the catalog size. Colors are illustrative. The opaque sides and flat underside are arbitrary display cuts, not real cliffs or geological strata. Mapzen / Tilezen; SRTM, GMTED2010 and United States 3DEP terrain courtesy of the U.S. Geological Survey; ETOPO1 ocean bathymetry courtesy of NOAA; Natural Earth public-domain map data; adaptation by Universe Scales.

## Pinned source and processing

`terrain3d/victoria-falls/provenance.json` records every tile URL, SHA-256, provider header, grid bounds and elevation range, plus the original vector download hashes. The compact `terrain.npz` stores 129 × 145 original sampled elevations and longitude/latitude. The mesh retains every 1 grid vertex along each axis (129 × 145), while the elevation-shading texture retains the full input grid. `vectors.geojson.gz` retains losslessly compressed source fragments independently. Global land is pinned as a derived crop mask, not distributed as a world dataset. Source grid spacing is a sampling choice, not a claim of DEM resolution. Small scenes use local east/up/south coordinates with spherical WGS84-radius distances; regional scenes use a spherical Earth of radius 6371.0088 km in a local tangent frame. Large-scene curvature is retained; no map projection rescales the footprint to fit the quantity. Geographic approximation differs slightly from ellipsoidal surveying. Vertical gain: **1×**. No extreme-point correction or procedural terrain is added.

Normal offline rebuild: `./venv/bin/python scripts/build_terrain3d_models.py victoria-falls`. Optional network source refresh: add `--prepare --cache /tmp/terrain3d`. Registration: `python3 scripts/register_model.py handoff/terrain3d/terrain3d-victoria-falls.entry.json content/visualizations/models/terrain3d-victoria-falls.glb`.

## Sources and rights

- https://registry.opendata.aws/terrain-tiles/
- https://github.com/tilezen/joerd/blob/master/docs/data-sources.md
- https://github.com/tilezen/joerd/blob/master/docs/attribution.md
- https://www.naturalearthdata.com/about/terms-of-use/
- https://whc.unesco.org/en/list/509/

Source pages were opened during preparation on 2026-10-16. Mapzen attribution applies alongside provider rights; the Joerd software license alone is not a license for elevation data. USGS SRTM/GMTED/3DEP and NOAA ETOPO1 are U.S. government data; Natural Earth states its data are public domain. No aerial photography, proprietary map tiles, invented survey traces or external runtime dependencies are used.
