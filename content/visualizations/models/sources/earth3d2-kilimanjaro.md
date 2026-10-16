# Kilimanjaro — Kibo summit window above sea level

Derived public-domain terrain, credited to **Mapzen / Tilezen; global SRTM and
GMTED2010 terrain data courtesy of the U.S. Geological Survey**. Original
display adaptation by Universe Scales. No Google Maps mesh or imagery is used.

## Sources (opened 2026-10-16)

- [Tanzania National Parks, About Kilimanjaro](https://www.tanzaniaparks.go.tz/kilimanjaro/about):
  Kibo **5,895 m above mean sea level**. The page was successfully retrieved
  with Python requests after the research browser timed out.
- [Mapzen Terrain Tiles on AWS](https://registry.opendata.aws/terrain-tiles/):
  public elevation tiles. Exact tile URLs and SHA-256 hashes are retained in
  [`earth3d2-kilimanjaro/provenance.json`](earth3d2-kilimanjaro/provenance.json).
- [Tilezen source attribution](https://github.com/tilezen/joerd/blob/master/docs/attribution.md):
  USGS global SRTM/GMTED2010 data attribution and public-domain status. The
  individual AWS responses omit `x-imagery-sources`; no precise acquisition
  year or particular source granule is claimed.

## Geometry and limitations

The **authored crop** is 6.4 km square, centered at approximately 3.0674° S,
37.3556° E. It surrounds the Kibo summit crater, not the whole massif, Mawenzi
or Shira. These are display-window choices, not measured mountain boundaries.
The source is bilinearly sampled to a 129 × 129 grid at 50 m spacing; its
approximately 5,885.668 m maximum is left uncorrected. No synthetic crater,
summit adjustment, smoothing, snow, glacier map or vertical exaggeration.

East/south offsets are converted to latitude/longitude using a local metric
approximation with the WGS84 equatorial radius and central-latitude cosine.
Terrarium samples use pixel centers. At this crop size, this approximation
is adequate for an illustrative, 50 m sampling grid; it is not a survey.

The sides extend to a **sea-level display datum**, preserving the listed
altitude. They are arbitrary vertical cuts, not real cliffs or the mountain's
geological base. The whole volcano extends far beyond the crop. The flat
underside and elevation palette do not depict underground geology, observed
strata or present-day vegetation/ice. Display label and on-model annotations
preserve these distinctions. The height marker is not redefined as local relief.

Normal builds are offline: `./venv/bin/python scripts/build_earth3d2_terrain.py`.
Optional source preparation: append `--prepare --tile-dir /tmp/earth3d2/terrain-tiles`.
The bundled grid is enough to reproduce the final GLB. Production browser
review remains pending; CPU previews are explicitly labeled.
