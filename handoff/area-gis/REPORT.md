# Area GIS preparation handoff

## Prepared outlines

Six source-derived, compact GeoJSON outlines are in
`content/visualizations/area-sources/`. `entries.json` is a JSON array; each
entry has exactly `id`, `name`, `geojson`, `central_longitude`, `source`,
`author`, `license`, `license_url`, and `note`. There is no runtime, dataset,
global registry, or export integration in this handoff.

| Item | Source selection | Listed quantity | Prepared geometry |
| --- | --- | --- | --- |
| Lake Tahoe surface | Natural Earth 1:10m Lakes, `name=Lake Tahoe` | 496 km² water surface | Source lake polygon, unchanged |
| New York City | Five U.S. Census 2024 cartographic county boundaries, unioned and clipped to Natural Earth land | 784 km² land area | 1:500,000 county boundaries clipped to 1:10m land; simplified at 0.0002 degrees |
| Caspian Sea surface | Natural Earth 1:10m Geography Marine Polygons, `name=Caspian Sea` | 371,000 km² water surface | Source marine polygon, unchanged |
| Texas | Natural Earth 1:10m Admin-1, `iso_3166_2=US-TX` | 696,200 km² total area | Generalized state outline, unchanged |
| Greenland | Natural Earth 1:10m Admin-0 Countries, `ADMIN=Greenland` | 2,166,000 km² land area | Generalized dependency outline, unchanged |
| Australia | Natural Earth 1:10m Admin-0 Countries, `ADMIN=Australia` | 7,690,000 km² land area | Generalized country outline, unchanged |

The 2024 Census county `ALAND` attributes sum to 778.181 km² for the five
boroughs; the listed 784 km² is a rounded land-area statistic. The NYC outline
has a spherical cylindrical equal-area estimate (R=6378137 m) of 736.005 km²
after the land overlay and topology-preserving simplification,
6.1% below the listed figure (5.4% below the Census land-attribute sum). The
overlay supplies a coast-clipped cartographic outline, not a cadastral or
hydrographic shoreline. Its mixed source scales and remaining area difference
are material limitations; visual calibration uniformly scales the outline to
the listed 784 km² and does not correct the source coastline.

Manhattan was dropped. Census New York County is only a proxy for Manhattan,
and clipping its 1:500,000 county boundary to Natural Earth 1:10m land yields
49.578 km² in the same spherical equal-area estimate, versus the Census county
`ALAND` value of 58.684 km²
(59.1 km² rounded). That approximately 15.5% omission is too large to present
as a defensible island outline at the requested value. The county also has
29.010 km² of Census `AWATER`; the old county polygon was not a land-only
Manhattan shape.

For scale context, the other uncalibrated source geometries measure about
486.093 km² (Tahoe), 379,604.994 km² (Caspian), 2,834.621 km² (Rhode Island),
687,439.202 km² (Texas), 2,142,676.780 km² (Greenland), and 7,723,177.020 km²
(Australia) in the same spherical equal-area estimate. These are measurements of generalized source
polygons, not replacement curated statistics. In particular, the Natural Earth
state outlines do not encode all surrounding water implied by the Rhode Island
total-area figure. Rhode Island is therefore excluded: the available Natural
Earth outline is land-like, its spherical equal-area estimate is 2,834.621 km²,
and scaling it
to the 4,000 km² total-area statistic would mismatch quantity and boundary. No
new source search was undertaken. The renderer should uniformly calibrate each
included outline to its listed statistic and preserve aspect ratio; do not
independently stretch axes.

Natural Earth data are public domain under its
[terms](https://www.naturalearthdata.com/about/terms-of-use/). Census TIGER
cartographic boundaries are U.S. Government works and public domain; the source
license rationale is documented in the linked
[TIGER technical documentation](https://www2.census.gov/geo/pdfs/maps-data/data/tiger/tgrshp2022/TGRSHP2022_TechDoc_Ch1.pdf).
No ODbL, noncommercial, or unclear-license geometry is included. The rejected
Manhattan result is not bundled. Source URLs, authors, license links, pinned
SHA-256 hashes for source snapshots and output features, selected feature
attributes, feature counts, simplification, geometry vertex counts, output
byte counts, quantity definitions, and
per-feature notes are in `content/visualizations/area-sources/manifest.json`.

The six output GeoJSON files total 855,165 bytes; each has one valid feature
and fewer than 100,000 vertices. They are direct GIS operations on cited source
polygons (selection, union, clipping, and topology-preserving simplification),
not hand-authored or generated substitute geometry.

## Reproduction and checks

The preparer downloads missing snapshots and refuses any source whose SHA-256
does not match the pinned values in `scripts/prepare_area_gis.py`. It requires
Python 3, Shapely 2.x, and pyshp for the Census ZIP. Rebuild with:

```sh
python3 -m pip install shapely pyshp
python3 scripts/prepare_area_gis.py --work-dir /tmp/area-gis/raw
```

Run the handoff integrity checks with:

```sh
python3 -m unittest handoff/area-gis/test_prepared_area_gis.py
```

The tests verify the exact six-entry array schema and item set, source hashes
against the script pins, public-domain license labels, one-feature GeoJSON
validity, compact size/vertex limits, and the NYC source/area caveat. Browser,
renderer, and integration checks are outside this handoff and remain with the
main integration task.
