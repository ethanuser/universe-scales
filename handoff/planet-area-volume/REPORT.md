# Planet Area and Volume Handoff

## Integrated 2026-10-29

The main integration now registers all seven Volume entries with
`reference_size = cbrt(enclosed mesh volume)`, including the approximately
spherical source globes. No GLB was modified or duplicated. All seven pass
closed-shell checks and production normalization/ruler checks on desktop and
mobile. Surface imagery is reprojected through the actual source UVs into Equal
Earth maps; see `content/visualizations/area-maps/README.md`. Fourteen new records
are displayed, and the Volume target was raised to retain prior anchors. The
original handoff scope below describes the agent's raw-data-only changes, not
the final integrated diff.

## Scope

Added paired Area and Volume records for Mercury, Venus, Mars, Saturn, Uranus,
Neptune and Pluto. No model registry, runtime, index, exports, database, deployment
copy or existing description was changed. Eris and Ceres were excluded: the
available Eris entry is a prior idealized sphere without a sourced texture, and
Ceres is an oblate body whose treatment merits a separate geometry/texture review.

## Sources and convention

The primary radius source is JPL Solar System Dynamics, [Planetary Physical
Parameters](https://ssd.jpl.nasa.gov/planets/phys_par.html), consulted 2026-10-28.
Its Mean Radius column explicitly defines the value as the radius of a sphere
with the planet's equivalent volume. Values used (km): Mercury 2439.4, Venus
6051.8, Mars 3389.50, Saturn 58232, Uranus 25362, Neptune 24622, Pluto 1188.3.
JPL reports uncertainties in the source table; the raw records retain the table
central values and the plaque text avoids implying greater precision.

Each Area is the **surface area of the sphere** `4*pi*r^2`; each Volume is the
**volume of the equivalent-volume sphere** `(4/3)*pi*r^3`, using radius converted
from km to m. This is intentionally a consistent spherical comparison, not an
assertion that every body's physical surface is spherical. Saturn's physical
oblate-globe volume is independently tabulated by JPL using this equivalent
radius. Area records for oblate planets are explicitly sphere-derived, not exact
ellipsoid surface integrals. Values are stored in SI base units and rounded to
six significant digits.

## Models and integration

`area-texture-sources.json` maps each new subject to its existing registered
source asset ID for the main Equal Earth texture/reprojection implementation.
No Eris proxy texture is supplied. All these model assets remain as-is.

`entries.json` records the seven Volume mappings. Each now uses enclosed-volume
normalization; Saturn uses the existing standalone oblate body mesh without
rings. The vendored
loader audit measured the Saturn GLB at 470340454.7817766 source-units^3, hence
777.6856969870922 source units. It is closed, consistently oriented and a single
connected shell; this does not test self-intersection. Main integration should
confirm each source asset ID, normalize dimensions against the associated
dataset value, inspect the Volume ruler and Equal Earth projections, then add
registry mappings only after review.

## Verification

JPL radius inputs and model IDs were checked against the live primary source and
the checked-in registry. `node scripts/mesh_volume.mjs
content/visualizations/models/nasa-saturn-globe-length.glb` passed. No full dataset
rebuild was run, as requested.
