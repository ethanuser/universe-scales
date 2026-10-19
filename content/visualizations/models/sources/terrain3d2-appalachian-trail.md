# Appalachian Trail: direct public data conversion

All 30 original NPS A.T. Treadway features (June 2023 version, GPS surveys from 1998–2022 plus supplemental information) are drawn over eastern-US relief. Separate club sections, source bends and gaps are retained. The bright line is a widened map symbol rasterized onto the terrain, not the width of the footpath. Relief is exaggerated 8×; horizontal coordinates and Earth curvature retain geographic scale. The regional aperture supplies context and its edges do not measure trail length. The 3,536.4 km catalog quantity is accumulated walking distance, not map extent; the source is not claimed to be the 2024 alignment. This is not a navigation or property-access map. No crop walls, underside, stand, independent ruler or schematic geometry is included. National Park Service Appalachian National Scenic Trail and Appalachian Trail Conservancy, 2023 treadway GPS data; Mapzen/Tilezen terrain, USGS SRTM/GMTED2010/3DEP and NOAA ETOPO1 bathymetry.

## Source and processing

Pinned numerical inputs, SHA-256 hashes, exact requests and selection metadata: `terrain3d2/appalachian-trail/provenance.json`. `data.npz` retains the numerical source subset in native metric values and longitude/latitude. Where present, `vectors.geojson.gz` retains original unmodified survey geometry and selected nonpersonal attributes, not an authored tracing. All model geometry is a direct triangulation of these numerical data. Missing data incident triangles are removed. Only palettes, viewing aperture and pose are authored. No geometry is stretched to the catalog number. Local scenes use the existing terrain builder's east/up/south metric coordinates; the regional trail uses its spherical Earth frame with curvature retained. These open surfaces make no enclosed-volume claim.

Offline rebuild: `./venv/bin/python scripts/build_terrain3d2_models.py appalachian-trail`. Refresh sources with `--prepare --cache /tmp/terrain3d2`; NASA preparation needs `netCDF4` (not needed to build pinned inputs). Register: `python3 scripts/register_model.py handoff/terrain3d2/terrain3d2-appalachian-trail.entry.json content/visualizations/models/terrain3d2-appalachian-trail.glb`.

## Rights and citations

- https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/ANST_Facilities/FeatureServer/7
- https://www.nps.gov/appa/planyourvisit/maps.htm
- https://www.nps.gov/aboutus/disclaimer.htm
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/33/43.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/33/44.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/33/45.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/33/46.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/33/47.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/33/48.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/33/49.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/33/50.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/33/51.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/33/52.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/34/43.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/34/44.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/34/45.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/34/46.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/34/47.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/34/48.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/34/49.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/34/50.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/34/51.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/34/52.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/35/43.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/35/44.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/35/45.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/35/46.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/35/47.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/35/48.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/35/49.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/35/50.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/35/51.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/35/52.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/36/43.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/36/44.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/36/45.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/36/46.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/36/47.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/36/48.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/36/49.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/36/50.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/36/51.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/36/52.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/37/43.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/37/44.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/37/45.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/37/46.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/37/47.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/37/48.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/37/49.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/37/50.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/37/51.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/37/52.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/38/43.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/38/44.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/38/45.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/38/46.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/38/47.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/38/48.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/38/49.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/38/50.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/38/51.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/38/52.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/39/43.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/39/44.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/39/45.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/39/46.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/39/47.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/39/48.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/39/49.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/39/50.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/39/51.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/39/52.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/40/43.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/40/44.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/40/45.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/40/46.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/40/47.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/40/48.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/40/49.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/40/50.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/40/51.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/40/52.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/41/43.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/41/44.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/41/45.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/41/46.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/41/47.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/41/48.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/41/49.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/41/50.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/41/51.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/7/41/52.png
- https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/ANST_Facilities/FeatureServer/7/query?where=1%3D1&outFields=OBJECTID%2CName%2CTrail_Club%2CSource%2CVersion&outSR=4326&f=geojson&returnGeometry=true&orderByFields=OBJECTID&resultRecordCount=2000
- https://registry.opendata.aws/terrain-tiles/
- https://github.com/tilezen/joerd/blob/master/docs/attribution.md
- https://www.arcgis.com/sharing/rest/content/items/2739a451a90c4a3283be4ccd6a6a12a9?f=json

Source data, metadata and reuse statements were opened on 2026-10-18. Credit and modifications are stated above; no endorsement is implied. CPU previews and vendored-loader bounds checks are approximations, not WebGL, production explorer, mobile or size-audit approval.
