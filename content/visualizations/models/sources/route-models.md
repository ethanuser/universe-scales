# Geographic Route Models

These Length models distinguish **path or inventory length** from geographic
span. Longitude and latitude are mapped onto a sphere of mean radius
6,371.0088 km in a local east/up/south frame. No river, course or wall network
is multiplied to fill the catalog length. The separate straight ruler is a
straightened length comparison, not a line between geographic endpoints.
All models use kilometers internally; `reference_size` calibrates the ruler
to the corresponding item value in meters. Model notes appear only in the
explorer, alongside geographic-source and scientific-basis links.

## Boston Marathon Example

- Geometry: [OpenStreetMap relation 11680552](https://www.openstreetmap.org/relation/11680552),
  retrieved 2026-09-30. The relation's 265 unique ways were ordered and oriented
  by their shared endpoints, not their initially discontinuous member order.
  They form one connected start-to-finish path, with no branches, repeated exact
  segments, invented connectors or alternate loops.
- The spherical segment sum is **42.417 km**, not 42.195 km. Road centerlines,
  map generalization and certification's shortest permitted running line are
  different measurements. The actual coordinate envelope is about 36.20 km
  east-west and 13.36 km north-south. It is not stretched.
- Definition: [World Athletics marathon](https://worldathletics.org/disciplines/road-running-event/marathon)
  specifies 42.195 km. [B.A.A. course](https://www.baa.org/races/boston-marathon/the-course/)
  describes the Hopkinton-to-Copley Square course. No B.A.A. artwork, logo or
  copyrighted map is copied. The example is not an official race map.
- Terrain: Mapzen Terrarium z11 elevation, roughly 57 m native pixel spacing
  at this latitude, sampled into a 145 by 65 mesh. Relief is exaggerated **12x**.
  This is bare-earth context, not a surveyed road-deck profile or runner-grade
  hill gradients. The course ribbon is draped onto the rendered triangles so
  finer DEM samples cannot disappear below coarse faces. Its 140 m display width
  is exaggerated. Earth curvature remains in the geometry.
- Endpoints are the mapped Hopkinton start and the Boylston Street finish.
  Blue is a graphic route highlight; green/brown is elevation tint, not imagery.
- Explorer labels identify only the two course endpoints; relief interpretation
  stays in the model note rather than floating over the terrain. The comparison
  ruler is a subdued, independent reference, not a geographic route.

## Amazon River System

- Source: [Natural Earth 1:10m rivers and lake centerlines](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-rivers-lake-centerlines/),
  [original archive](https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_rivers_lake_centerlines.zip).
  The first feature is Amazonas record NE_ID **1159116655**, geometry part 2
  (zero-based index 1), 675 unchanged vertices, about **3,053.3 km** along the
  generalized centerline. Other named rivers are separate context-only features.
- The selected reach runs from the Ucayali/Maranon confluence
  (-73.488623, -4.444854) to (-52.711768, -1.583820), inland upstream of the
  Xingu confluence region. **It does not reach the Atlantic.** Missing reaches
  are not drawn or bridged, and tributaries are not added to its length.
- Natural Earth explicitly warns that some Amazon-basin alignments are suspect.
  Treat this as a partial regional locator, not a channel survey or navigation.
  Context lines are clipped to the geographic window, without joining gaps.
- The full-length ruler uses the approximate **6,400 km** estimate published by
  [NASA MODIS](https://modis.gsfc.nasa.gov/gallery/individual.php?db_date=2018-10-26)
  and [ESA](https://www.esa.int/ESA_Multimedia/Images/2020/09/Amazon_River),
  replacing the legacy unsupported 7,000 km value. Definitions vary:
  [FAO, The Inland Waters of Latin America](https://www.fao.org/4/ad770b/AD770B05.htm)
  gives about 6,437 km including the Maranon and 6,300 km via the Ucayali/Apurimac.
  None is a measurement of this partial mapped reach.
- Terrain: Mapzen z5 regional elevation, **16x** exaggerated relief. Cartographic
  river width and elevation tint are illustrative; no channel depth or flow is
  modeled. The bright trunk is distinct from muted context tributaries.

## Great Wall Network

- Geometry: [OpenStreetMap relation 318110](https://www.openstreetmap.org/relation/318110),
  retrieved 2026-09-30. After removing two repeated member references there are
  **9,542 unique ways**, 158,369 vertices and about 6,064 km of summed linework.
  This is incomplete community mapping, not the official heritage inventory.
- Only degree-two shared endpoints were joined. Branch junctions and gaps remain
  separate. Douglas-Peucker simplification at 500 m, followed by five-decimal-degree
  rounding, retains 8,078 chains and 16,678 vertices. The resulting sum is about
  5,304 km; generalization reduces that sum, **not the surveyed wall length**.
- The paths sit on the same [NASA Earth](https://science.nasa.gov/resource/earth-3d-model/)
  mesh, color atlas, normal map and material used by Earth Diameter.
  The globe has a diameter of about 12,742 km, not 21,196 km. Coastlines are
  imagery context, not a surveyed basemap. Orange paths are widened to 100 km and raised 5 km for
  visibility; neither represents physical wall dimensions.
- The independent ruler follows the State Administration of Cultural Heritage's
  2012 result, **21,196.18 km** of wall and trench remains across periods and
  branches. See its [report submitted to UNESCO](https://whc.unesco.org/document/157507/)
  (PDF pages 5-11) and the [China Great Wall Museum survey summary](https://www.greatwallheritage.cn/CCMCMS/html/1/54/index.html).
  This is not a single Shanhai Pass-to-Jiayu Pass corridor, not the length of
  visible surviving masonry, and not a claim of meter-level survey accuracy.

## Reuse And Rebuild

Contains information from **OpenStreetMap contributors**, available under the
[Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
The two OSM derivative databases are supplied in machine-readable form under
ODbL, separate from the project's CC0 quantitative dataset:
[Boston](routes/boston-marathon-course.geojson) and
[Great Wall](routes/great-wall-network-globe.geojson).
Their notices must remain; [a full license copy](../licenses/ODbL-1.0.txt) is included.
These terms permit commercial reuse, with attribution and derivative-database
share-alike obligations. They do not replace the project's other asset licenses.

[Amazon source geometry](routes/amazon-river-geography.geojson) and
`content/visualizations/land.geojson` are Natural Earth public-domain data;
[terms](https://www.naturalearthdata.com/about/terms-of-use/).
Elevation comes from [Mapzen Terrain Tiles](https://registry.opendata.aws/terrain-tiles/),
with [Mapzen/Tilezen and source-provider attribution](https://github.com/tilezen/joerd/blob/master/docs/attribution.md).
Tile URLs and input hashes are recorded in each registry entry. Colors, line
widths, terrain cuts and the ruler layout are project-authored illustrations,
not downloaded photogrammetry or official survey reconstructions.

Rebuild from the bundled source geometry, using the existing `venv` with NumPy
and Pillow. Elevation downloads are cached outside the repo. For example:

```sh
for kind in marathon amazon wall; do
  case "$kind" in
    marathon) id=boston-marathon-course ;;
    amazon) id=amazon-river-geography ;;
    wall) id=great-wall-network-globe ;;
  esac
  SSL_CERT_FILE=/etc/ssl/cert.pem ./venv/bin/python scripts/build_route_models.py "$kind" \
    --geometry "content/visualizations/models/sources/routes/$id.geojson" \
    --land content/visualizations/land.geojson \
    --cache /private/tmp/us-route-models/tiles \
    --output /private/tmp/taste-routes
done
```

The output directory contains staged GLBs and sidecars only; it does not update
the runtime registry or assets. All delivered GLBs embed their textures and
buffers and need no decoder or runtime source-data fetch. Run `model_lab.cjs
shot` and `explorer` before keeping a change; the exactly edge-on side view
naturally compresses terrain and rulers and is not the intended geographic
reading angle.
