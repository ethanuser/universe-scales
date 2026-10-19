# El Reno Tornado: direct public data conversion

A 5.1 km square terrain aperture south of El Reno airport with the clipped original NWS Damage Assessment Toolkit polygon identified as ElReno_Poly (31 May 2013). Orange marks mapped damage-survey coverage on unexaggerated USGS 3DEP terrain. Public USDA NAIP aerial imagery supplies later geographic context, not a photograph of the tornado or its 2013 damage; the catalog tile at the aperture center is dated 29 May 2021. The full polygon is pinned, but its longer eastward track lies outside this deliberately local aperture. The polygon is not an instantaneous funnel, a measured wind-field surface, or an exact outline of the published maximum 2.6-mile tornado width. No vortex, funnel, moving centerline or artificial width boundary is constructed. The polygon source retains its historical EF3+ attribute; this does not revise the NWS event rating. No crop walls, underside, stand, independent ruler or schematic geometry is included. NOAA National Weather Service Damage Assessment Toolkit, ElReno_Poly survey feature; USGS 3DEP terrain; USDA NAIP public-domain orthophotography via USGS The National Map.

## Source and processing

Pinned numerical inputs, SHA-256 hashes, exact requests and selection metadata: `terrain3d2/el-reno/provenance.json`. `data.npz` retains the numerical source subset in native metric values and longitude/latitude. Where present, `vectors.geojson.gz` retains original unmodified survey geometry and selected nonpersonal attributes, not an authored tracing. All model geometry is a direct triangulation of these numerical data. Missing data incident triangles are removed. Only palettes, viewing aperture and pose are authored. No geometry is stretched to the catalog number. Local scenes use the existing terrain builder's east/up/south metric coordinates; the regional trail uses its spherical Earth frame with curvature retained. These open surfaces make no enclosed-volume claim.

Offline rebuild: `./venv/bin/python scripts/build_terrain3d2_models.py el-reno`. Refresh sources with `--prepare --cache /tmp/terrain3d2`; NASA preparation needs `netCDF4` (not needed to build pinned inputs). Register: `python3 scripts/register_model.py handoff/terrain3d2/terrain3d2-el-reno.entry.json content/visualizations/models/terrain3d2-el-reno.glb`.

## Rights and citations

- https://services.dat.noaa.gov/arcgis/rest/services/nws_damageassessmenttoolkit/DamageViewer/FeatureServer/2
- https://www.weather.gov/oun/events-20130531
- https://www.weather.gov/disclaimer
- https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage?bbox=-97.98831476527444%2C35.42593388359005%2C-97.93168523472555%2C35.47206611640995&bboxSR=4326&imageSR=4326&size=145%2C145&format=tiff&pixelType=F32&interpolation=RSP_BilinearInterpolation&renderingRule=%7B%22rasterFunction%22%3A+%22None%22%7D&adjustAspectRatio=false&f=image
- https://services.dat.noaa.gov/arcgis/rest/services/nws_damageassessmenttoolkit/DamageViewer/FeatureServer/2/query?where=event_id%3D%27ElReno_Poly%27&outFields=objectid%2Cefscale%2Cevent_id%2Cstormdate%2Clength%2Cwidth&outSR=4326&f=geojson&returnGeometry=true
- https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer/exportImage?bbox=-97.98811949103117%2C35.42609296025495%2C-97.93188050896882%2C35.47190703974505&bboxSR=4326&imageSR=4326&size=1024%2C1024&format=jpg&bandIds=0%2C1%2C2&adjustAspectRatio=false&f=image
- https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer

Source data, metadata and reuse statements were opened on 2026-10-18. Credit and modifications are stated above; no endorsement is implied. CPU previews and vendored-loader bounds checks are approximations, not WebGL, production explorer, mobile or size-audit approval.
