# Equal-Area Views

These are cartographic presentation assets, not new measured 3D surfaces or a
replacement for the observation dataset. The source registry is
`content/visualizations/area-maps.json`; each entry has attribution and an
explorer-only explanation. Existing item descriptions stay separate.

## Planetary Surfaces

Eleven existing NASA globe assets supply their own UV-mapped imagery. The offline
builder views each globe from its center, captures its actual texture mapping,
then samples that cube map through the inverse Equal Earth projection. This also
handles source textures stored as cube atlases; treating an atlas as an ordinary
longitude-latitude image would scramble the map. No new 3D geometry is delivered.

The projection is area-preserving on a sphere. For oblate bodies, these maps use
the dataset's stated spherical-area convention, not an ellipsoidal surface-area
measurement. Gas-planet textures depict atmosphere, the Sun depicts a photospheric
appearance, and Pluto has uneven imaging coverage. Source globe axes determine
north; there is no claim of a precise navigation grid or current weather.

The transparent PNG footprint covers one normalized area unit. Its enclosing
rectangle is larger than one unit, and must not be used to set the area. The
builder verifies the alpha footprint numerically. Runtime dimensions scale by
`sqrt(listed area)`, using the same unit conversion as the ruler.

Projection: [Equal Earth paper](https://doi.org/10.1080/13658816.2018.1504949),
[PROJ documentation](https://proj.org/en/stable/operations/projections/eqearth.html).
New planetary quantities derive from the equivalent-volume mean radii in
[JPL's physical parameters](https://ssd.jpl.nasa.gov/planets/phys_par.html):
`A = 4*pi*r^2` and `V = 4*pi*r^3/3`. Their input radii and formulas are in the raw
records. Surface areas are spherical approximations, not terrain-following areas.

## Geographic Outlines

Public-domain source polygons are prepared by `scripts/prepare_area_gis.py`.
Their coordinates, holes and islands are projected with D3 Equal Earth, centered
on each region using a spherical rotation (which preserves area), then
uniformly scaled so the filled polygon covers the catalog area. No independent
axis stretching is applied. Local centering reduces polar distortion, so Greenland
is not flattened as if cut from a global equatorial map. This does not assert that
the generalized boundary itself precisely measures the published statistic.
Per-item notes identify land/water/total-area conventions and generalization.

The source hashes and preparation details are in `../area-sources/manifest.json`
and `handoff/area-gis/REPORT.md`. The runtime loads local compact GeoJSONs, not
remote GIS services. It projects them once per Area explorer instance.

## Rebuild and Verify

From the repository root (the PNG builder needs the existing Playwright/Chromium
environment used by `preview_glb.cjs`):

```sh
node scripts/build_planet_area_maps.cjs
node scripts/register_area_maps.cjs
node scripts/register_planet_volumes.mjs --check
node scripts/prepare_planet_area_volume_images.cjs --check
node --test tests/area-maps.test.cjs
node scripts/model_lab.cjs area-maps /tmp/area-map-audit
node scripts/model_lab.cjs area-maps /tmp/area-map-mobile --mobile
```

`manifest.json` pins the planetary source GLB hashes, output PNG hashes, sizes,
licenses and numerical footprint coverage. Original source licenses apply to
these derivatives. The browser harness also checks filled geographic paths and
captures the production explorer; inspect the screenshots, not just the numbers.
