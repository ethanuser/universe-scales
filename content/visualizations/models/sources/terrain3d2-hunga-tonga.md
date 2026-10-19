# Hunga Tonga Eruption Plume: direct public data conversion

A direct mesh of measured cloud-top stereo heights in a 64 km aperture near the eruption, from NASA nominal 04:30 UTC retrievals (actual line observation times about 04:36–04:37 UTC) on 15 January 2022. Only native neighboring retrieval pixels with quality rating at least 1 are connected; missing or low-confidence pixels remain holes. All 449 retained observations are also shown as point markers at their measured positions; marker size is a visibility symbol, not a droplet size. The selected source reaches 58.357 km, without height correction or vertical exaggeration. The lower separate surface is historical NOAA ETOPO1 ocean bathymetry at geographic scale, not a post-eruption seafloor survey. Cloud-top brightness uses the co-recorded Himawari-8 infrared brightness temperature, not true-color imagery. This is the observed upper surface at one time, not a reconstructed plume volume, density, eruption column or full umbrella-cloud extent. No stem, skirts, sides or particles are invented. No crop walls, underside, stand, independent ruler or schematic geometry is included. Kristopher Bedka and Konstantin Khlopenkov, NASA Langley Research Center; GOES-17/Himawari-8 stereo retrievals, 15 January 2022; NOAA ETOPO1 ocean-floor elevations.

## Source and processing

Pinned numerical inputs, SHA-256 hashes, exact requests and selection metadata: `terrain3d2/hunga-tonga/provenance.json`. `data.npz` retains the numerical source subset in native metric values and longitude/latitude. Where present, `vectors.geojson.gz` retains original unmodified survey geometry and selected nonpersonal attributes, not an authored tracing. All model geometry is a direct triangulation of these numerical data. Missing data incident triangles are removed. Only palettes, viewing aperture and pose are authored. No geometry is stretched to the catalog number. Local scenes use the existing terrain builder's east/up/south metric coordinates; the regional trail uses its spherical Earth frame with curvature retained. These open surfaces make no enclosed-volume claim.

Offline rebuild: `./venv/bin/python scripts/build_terrain3d2_models.py hunga-tonga`. Refresh sources with `--prepare --cache /tmp/terrain3d2`; NASA preparation needs `netCDF4` (not needed to build pinned inputs). Register: `python3 scripts/register_model.py handoff/terrain3d2/terrain3d2-hunga-tonga.entry.json content/visualizations/models/terrain3d2-hunga-tonga.glb`.

## Rights and citations

- https://science-data.larc.nasa.gov/LaRC-SD-Publications/2022-11-22-001-KMB/
- https://science-data.larc.nasa.gov/LaRC-SD-Publications/2022-11-22-001-KMB/data/A2022015.0430.stereo_CTH.nc
- https://gis.ngdc.noaa.gov/arcgis/rest/services/DEM_mosaics/ETOPO1_ice_surface/ImageServer/exportImage?bbox=-175.71197713270993%2C-20.931952467338846%2C-175.08802286729008%2C-20.348047532661155&bboxSR=4326&imageSR=4326&size=65%2C65&format=tiff&pixelType=F32&interpolation=RSP_BilinearInterpolation&renderingRule=%7B%22rasterFunction%22%3A+%22None%22%7D&adjustAspectRatio=false&f=image

Source data, metadata and reuse statements were opened on 2026-10-18. Credit and modifications are stated above; no endorsement is implied. CPU previews and vendored-loader bounds checks are approximations, not WebGL, production explorer, mobile or size-audit approval.
