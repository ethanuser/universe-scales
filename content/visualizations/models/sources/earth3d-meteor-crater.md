# Meteor Crater: 3D model provenance

Meteor Crater in real terrain, sampled from Mapzen Terrarium elevation tiles on a 12 m grid. Horizontal and vertical metres use the same scale: no exaggerated relief, synthetic bowl or depth correction. The 1.44 km square includes context around the catalog’s approximately 1.19 km crater diameter; the square is not the crater rim. Sandstone colors are an authored elevation palette, not satellite imagery or mapped geological strata. The flat underside is an arbitrary display cut, not a subsurface boundary. Mapzen / Tilezen; United States 3DEP (formerly NED) and global GMTED2010 and SRTM terrain data courtesy of the U.S. Geological Survey.

- Source: https://registry.opendata.aws/terrain-tiles/
- Credit: Mapzen Terrain Tiles / Tilezen; terrain data courtesy of the U.S. Geological Survey; adaptation by Universe Scales
- License of the delivered model: Mapzen Terrain Tiles attribution; underlying USGS public-domain terrain data (https://github.com/tilezen/joerd/blob/master/docs/attribution.md)
- Dimensional/scientific basis: https://pubs.usgs.gov/publication/ofr20241062/full

## Calibration

Runtime presentation (angles in degrees): `{"reference_size": 1186, "yaw": 0, "pitch": 48, "layout_width_factor": 1.25, "focus_scale_factor": 1.2}`.

Scaling is uniform on all three axes. The catalog value calibrates the stated axis or explicit reference size; it does not certify the source as a surveyed specimen. The per-item note above states the extent and representation.

## Rebuild and review

Builder: `scripts/build_meteor_crater.py`. See `handoff/earth3d/REPORT.md` for commands, source preparation, checks and remaining production-browser work.

The rest/side images in `handoff/earth3d/previews/` are CPU orthographic previews. They include geometry, base-color textures and approximate lighting; they do not verify WebGL materials, reflections, perspective, picking, neighboring-item spacing, labels, the explorer or mobile behavior.

## Terrain data and rights

Opened on 2026-10-16:

- [AWS Terrain Tiles registry](https://registry.opendata.aws/terrain-tiles/).
- [Tilezen source resolution and compositing](https://github.com/tilezen/joerd/blob/master/docs/data-sources.md).
- [Tilezen attribution and USGS public-domain status](https://github.com/tilezen/joerd/blob/master/docs/attribution.md).
- [USGS Open-File Report 2024-1062](https://pubs.usgs.gov/publication/ofr20241062/full), describing an approximately 1.2 km-wide, 180 m-deep crater.

United States 3DEP (formerly NED) and global GMTED2010 and SRTM terrain data courtesy of the U.S. Geological Survey. Mapzen Terrain Tiles / Tilezen. USGS government elevation facts are public domain; credit and this processing statement are retained. No other countries' terrain datasets are included in this small Arizona crop. Tilezen lists approximately 10 m US 3DEP sources at zoom 14. The downloaded AWS responses omitted `X-Imagery-Sources`, so the exact underlying source granule/epoch cannot be certified; do not label this as a particular lidar survey.

The builder samples four zoom-14 Terrarium tiles bilinearly onto a 121 × 121 local metric grid (12 m spacing). The local east/south conversion uses the same Earth-radius convention as the repository's other geographic builders. This is an authored 1.44 km viewing aperture around 35.0273 N, 111.0225 W, not a claim that the crater boundary is square. The public source describes the crater approximately; the existing 1,186 m catalog value remains unchanged and calibrates an explicit reference length, never the full aperture.

`earth3d-meteor-crater/terrain.npz` is the small derived offline height grid. `provenance.json` records all original tile URLs/hashes, the grid hash and measured grid extrema. Source minimum 1562.6501 m and maximum 1749.6655 m give about 187.02 m of sampled relief; this is not forced to the published rounded 180 m crater depth. No smoothing, artificial bowl, peak correction or vertical exaggeration is applied. Colors are an authored height palette. The display underside is 30 m below the lowest sample, with opaque sides; it is not an observed layer, excavation, sea level or subsurface interpretation.
