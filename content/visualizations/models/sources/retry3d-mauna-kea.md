# Mauna Kea: unexaggerated NOAA topography and bathymetry

**Unregistered review candidate.** Its regional footprint is much wider than
the item's height. Do not scale its bounding box to 10,211 m. Read
`handoff/retry3d/REPORT.md` before integration.

Geometry comes directly from [NOAA ETOPO 2022](https://www.ncei.noaa.gov/products/etopo-global-relief-model),
tile [N30W165](https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/15s/15s_surface_elev_gtif/ETOPO_2022_v1_15s_N30W165_surface.tif).
The pinned subset retains every third native cell center within the declared
geographic aperture. Source heights are unchanged. There is no vertical
exaggeration, smoothing, added base, side wall, underside, sea surface, or inferred
geological boundary. Vertex colors encode source elevation. They are not aerial
photography or a reconstruction of underwater natural colors.

The aperture includes Mauna Kea, Kohala and the offshore northeastern flank of
Hawaiʻi. It excludes Mauna Loa's summit; it does not isolate Mauna Kea's full
edifice or identify a uniquely defined base. The crop boundaries are display
choices. [USGS's quantity definition](https://www.usgs.gov/faqs/how-big-are-hawaiian-volcanoes)
gives 4,205 m above sea level, about 6,000 m below, and nearly 10,211 m total.
Coarse ETOPO cells smooth the summit; source heights are never adjusted to reach
those nominal values. The full source release is documented by
[MacFerrin et al. (2025)](https://essd.copernicus.org/articles/17/1835/2025/).

Coordinates use a local equidistant cylindrical projection centered at
155.375° W, 20.25° N; X is east, Y source elevation and Z south, all in metres.
The projection uses the [WGS84 semi-major radius](https://epsg.io/7030-ellipsoid).
East-west scale relative to the true local parallel varies by less than 0.5%
over this aperture; no horizontal axis is compressed to satisfy framing.
Earth curvature is not added to this local map surface. The modeled vertical
range is therefore geodetic elevation range, not a summit-to-base chord.

Inputs/hashes/acquisition details: `retry3d/mauna-kea/provenance.json` and `grid.npz`.
Rights: [NOAA metadata and extracted rights](retry3d/etopo-rights.md), CC0 1.0.
Offline rebuild: `./venv/bin/python scripts/build_retry3d_models.py`.
Optional source refresh: add `--prepare`. The full GeoTIFF is cached outside the
repo; the small pinned numeric subset is sufficient to reproduce the GLB.

