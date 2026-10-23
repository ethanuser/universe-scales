# Lake Baikal: measured-grid lake-bed aperture

**Unregistered review candidate.** The footprint is much wider than the listed
maximum depth. Do not normalize the footprint to the depth or mistake it for the
whole lake. Read `handoff/retry3d/REPORT.md` before integration.

Geometry comes directly from [NOAA ETOPO 2022](https://www.ncei.noaa.gov/products/etopo-global-relief-model),
tile [N60E105](https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/15s/15s_surface_elev_gtif/ETOPO_2022_v1_15s_N60E105_surface.tif).
The [release paper, section 3.1 and Table 3](https://essd.copernicus.org/articles/17/1835/2025/)
explicitly identifies Baikal as a lake whose approximate bathymetry is incorporated
from GEBCO. This avoids asserting a reuse license for the independently hosted
GFZ contour archive that blocked the earlier attempt. NOAA's own release carries
an explicit CC0 dedication; see [the pinned rights extract](retry3d/etopo-rights.md).

All native cell centers in the geographic aperture are retained. A rigid
vertical translation uses a nominal lake surface of 456 m; this is the rounded
lake-level reference described in the
[International Lake Environment Committee's Baikal record](https://wldb.ilec.or.jp/Display/html/3544).
It is not a contemporaneous water-level measurement registered to the ETOPO
vertical datum. The difference matters at metre-level precision. Only original
adjacent triangles with all vertices at or below this nominal level are kept.
No new shoreline vertices, interpolated boundary, land, water surface, walls,
underside or lake volume are created. The few disconnected patches and jagged
shoreline are preserved source-grid effects, not filled holes.

The patch lies southeast of Olkhon near the deep central basin. Its minimum
source elevation is -1,198 m. Relative to the nominal 456 m level this is
1,654 m deep, close to, but not a new determination of, the existing 1,642 m
catalog maximum. The highest retained sample is about 0.215 m below nominal water level,
so the mesh's actual vertical extent is about 1,653.8 m. No height is stretched or
shifted to force the listed maximum. Blue colors represent depth, not a view
through transparent lake water.

The X/Z map uses a local equidistant cylindrical projection centered at
107.375° E, 53.075° N; X is east, Y elevation relative to the nominal lake level,
Z south, in metres. Projection scale variation over this small aperture is below
0.3%; Earth curvature is not modeled. The projection uses the
[WGS84 semi-major radius](https://epsg.io/7030-ellipsoid).

Input values/hashes: `retry3d/baikal-depth/grid.npz` and `provenance.json`.
Offline rebuild: `./venv/bin/python scripts/build_retry3d_models.py`.
The geometry is an approximate regional grid surface, not a detailed new sonar
survey or a survey-quality depth measurement.

