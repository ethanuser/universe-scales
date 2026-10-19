# Mount Thor Cliff: direct public data conversion

Public Mapzen elevation tiles in a 1.4 km east-west by 1.0 km north-south aperture across the west face of Thor Peak. Tilezen documents ArcticDEM and Canadian elevation as sources at this latitude; per-tile provider headers are absent, so their precise local mix is not asserted. Horizontal distances and elevations retain metre units; vertical exaggeration is 1×. A single-valued DEM cannot represent the overhang and rounds the steep face. This is a cropped terrain surface, not a complete rock-face scan or a surveyed 1,200 m cliff-height measurement. No summit-height adjustment or gap filling is performed by this builder. A separate direct ArcticDEM service trial had major no-data holes and was rejected. No crop walls, underside, stand, independent ruler or schematic geometry is included. Mapzen/Tilezen; Polar Geospatial Center / ArcticDEM; Natural Resources Canada / CDEM. ArcticDEM support: NSF-OPP awards 1043681, 1559691, 1542736, 1810976 and 2129685.

## Source and processing

Pinned numerical inputs, SHA-256 hashes, exact requests and selection metadata: `terrain3d2/mount-thor/provenance.json`. `data.npz` retains the numerical source subset in native metric values and longitude/latitude. Where present, `vectors.geojson.gz` retains original unmodified survey geometry and selected nonpersonal attributes, not an authored tracing. All model geometry is a direct triangulation of these numerical data. Missing data incident triangles are removed. Only palettes, viewing aperture and pose are authored. No geometry is stretched to the catalog number. Local scenes use the existing terrain builder's east/up/south metric coordinates; the regional trail uses its spherical Earth frame with curvature retained. These open surfaces make no enclosed-volume claim.

Offline rebuild: `./venv/bin/python scripts/build_terrain3d2_models.py mount-thor`. Refresh sources with `--prepare --cache /tmp/terrain3d2`; NASA preparation needs `netCDF4` (not needed to build pinned inputs). Register: `python3 scripts/register_model.py handoff/terrain3d2/terrain3d2-mount-thor.entry.json content/visualizations/models/terrain3d2-mount-thor.glb`.

## Rights and citations

- https://registry.opendata.aws/terrain-tiles/
- https://geonames.nrcan.gc.ca/search-place-names/unique?id=OAQLW&wbdisable=true
- https://github.com/tilezen/joerd/blob/master/docs/attribution.md
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/14/5218/4092.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/14/5218/4093.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/14/5219/4092.png
- https://elevation-tiles-prod.s3.amazonaws.com/terrarium/14/5219/4093.png
- https://www.pgc.umn.edu/guides/stereo-derived-elevation-models/pgc-dem-products-arcticdem-rema-and-earthdem/
- https://www.pgc.umn.edu/guides/user-services/acknowledgement-policy/
- https://github.com/tilezen/joerd/blob/master/docs/data-sources.md
- https://open.canada.ca/en/open-government-licence-canada

Source data, metadata and reuse statements were opened on 2026-10-18. Credit and modifications are stated above; no endorsement is implied. CPU previews and vendored-loader bounds checks are approximations, not WebGL, production explorer, mobile or size-audit approval.
