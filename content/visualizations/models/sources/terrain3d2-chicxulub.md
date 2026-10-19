# Chicxulub Crater: direct public data conversion

A direct conversion of the Scripps 1-minute global gravity-anomaly grid V33.1 around Chicxulub. Horizontal coordinates retain geographic metre scale. The vertical coordinate plots gravity anomaly at 500 display metres per mGal, relative to 0 mGal: it is not elevation, crater depth, geological relief or seismic topography. Colors also encode the recorded anomaly, with no radial template, ring, crater rim or inferred crater surface added. The 205 km authored aperture is geographic context for the approximately 180 km catalog diameter, not a measured crater boundary. Marine gravity and the EGM2008 land field have different information content; the landward crater signature is comparatively coarse. No crop walls, underside, stand, independent ruler or schematic geometry is included. Scripps Institution of Oceanography / UC San Diego, Sandwell et al. (2014), global gravity V33.1; EGM2008 contribution over land.

## Source and processing

Pinned numerical inputs, SHA-256 hashes, exact requests and selection metadata: `terrain3d2/chicxulub/provenance.json`. `data.npz` retains the numerical source subset in native metric values and longitude/latitude. Where present, `vectors.geojson.gz` retains original unmodified survey geometry and selected nonpersonal attributes, not an authored tracing. All model geometry is a direct triangulation of these numerical data. Missing data incident triangles are removed. Only palettes, viewing aperture and pose are authored. No geometry is stretched to the catalog number. Local scenes use the existing terrain builder's east/up/south metric coordinates; the regional trail uses its spherical Earth frame with curvature retained. These open surfaces make no enclosed-volume claim.

Offline rebuild: `./venv/bin/python scripts/build_terrain3d2_models.py chicxulub`. Refresh sources with `--prepare --cache /tmp/terrain3d2`; NASA preparation needs `netCDF4` (not needed to build pinned inputs). Register: `python3 scripts/register_model.py handoff/terrain3d2/terrain3d2-chicxulub.entry.json content/visualizations/models/terrain3d2-chicxulub.glb`.

## Rights and citations

- https://topex.ucsd.edu/cgi-bin/get_data.cgi
- https://topex.ucsd.edu/marine_grav/mar_grav.html
- https://topex.ucsd.edu/pub/sandwell/SF_geodesy_proposal.pdf
- https://topex.ucsd.edu/cgi-bin/get_data.cgi?north=22.22077316622251&south=20.37922683377749&west=-90.53828145952245&east=-88.56171854047754&mag=0.1
- https://topex.ucsd.edu/pub/global_grav_1min/README_V33.txt

Source data, metadata and reuse statements were opened on 2026-10-18. Credit and modifications are stated above; no endorsement is implied. CPU previews and vendored-loader bounds checks are approximations, not WebGL, production explorer, mobile or size-audit approval.
