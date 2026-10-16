# Suez Canal: elevation and map geometry

The generalized Natural Earth Suez Canal centerlines, including their separate mapped branches, over sampled terrain between the Mediterranean and Red seas. Relief is exaggerated 3 times; line width is a visibility symbol, not canal width. The source is generalized cartography, not a current engineering plan or full port-approach inventory. The independent 193.3 km ruler marks the catalog navigation-route length; neither map nor centerlines are stretched to it. Horizontal coordinates are not normalized to the catalog size. Colors are illustrative. The opaque sides and flat underside are arbitrary display cuts, not real cliffs or geological strata. Mapzen / Tilezen; SRTM, GMTED2010 and United States 3DEP terrain courtesy of the U.S. Geological Survey; ETOPO1 ocean bathymetry courtesy of NOAA; Natural Earth public-domain map data; adaptation by Universe Scales. Ocean depths are sampled explicitly from NOAA ETOPO1 (1 arc-minute), using Natural Earth coastlines to select ocean samples; coastlines and land/ocean source transitions are generalized.

## Pinned source and processing

`terrain3d/suez/provenance.json` records every tile URL, SHA-256, provider header, grid bounds and elevation range, plus the original vector download hashes. The compact `terrain.npz` stores 257 × 129 original sampled elevations and longitude/latitude. The mesh retains every 2 grid vertex along each axis (129 × 65), while the elevation-shading texture retains the full input grid. `vectors.geojson.gz` retains losslessly compressed source fragments independently. Global land is pinned as a derived crop mask, not distributed as a world dataset. Source grid spacing is a sampling choice, not a claim of DEM resolution. Small scenes use local east/up/south coordinates with spherical WGS84-radius distances; regional scenes use a spherical Earth of radius 6371.0088 km in a local tangent frame. Large-scene curvature is retained; no map projection rescales the footprint to fit the quantity. Geographic approximation differs slightly from ellipsoidal surveying. Vertical gain: **3×**. No extreme-point correction or procedural terrain is added.

Normal offline rebuild: `./venv/bin/python scripts/build_terrain3d_models.py suez`. Optional network source refresh: add `--prepare --cache /tmp/terrain3d`. Registration: `python3 scripts/register_model.py handoff/terrain3d/terrain3d-suez.entry.json content/visualizations/models/terrain3d-suez.glb`.

## Sources and rights

- https://registry.opendata.aws/terrain-tiles/
- https://github.com/tilezen/joerd/blob/master/docs/data-sources.md
- https://github.com/tilezen/joerd/blob/master/docs/attribution.md
- https://www.naturalearthdata.com/about/terms-of-use/
- https://www.suezcanal.gov.eg/English/About/SuezCanal/Pages/CanalCharacteristics.aspx
- https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_rivers_lake_centerlines.geojson
- https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson
- https://gis.ngdc.noaa.gov/arcgis/rest/services/DEM_mosaics/ETOPO1_ice_surface/ImageServer/exportImage?bbox=31.9466796875%2C29.796679687500003%2C32.8033203125%2C31.5033203125&bboxSR=4326&imageSR=4326&size=129%2C257&format=tiff&pixelType=F32&interpolation=RSP_BilinearInterpolation&renderingRule=%7B%22rasterFunction%22%3A+%22None%22%7D&adjustAspectRatio=false&f=image

Source pages were opened during preparation on 2026-10-16. Mapzen attribution applies alongside provider rights; the Joerd software license alone is not a license for elevation data. USGS SRTM/GMTED/3DEP and NOAA ETOPO1 are U.S. government data; Natural Earth states its data are public domain. No aerial photography, proprietary map tiles, invented survey traces or external runtime dependencies are used.
