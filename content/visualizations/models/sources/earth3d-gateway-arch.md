# Gateway Arch: 3D model provenance

Dimensioned exterior of the Gateway Arch, using the National Park Service weighted-catenary centroid equation and equilateral triangular sections tapering from 54 ft at the base to 17 ft at the crown. Cross-sectional area varies linearly with distance below the crown. Height and outer span are about 630 ft (192 m). Ground cuts follow the sloping legs. Interiors, foundations, panel joints and observation windows are omitted; steel finish and studio reflections are illustrative.

- Source: https://www.nps.gov/jeff/planyourvisit/mathematical-equation.htm
- Credit: Universe Scales, from National Park Service geometry
- License of the delivered model: CC0-1.0 (https://creativecommons.org/publicdomain/zero/1.0/)
- Dimensional/scientific basis: https://www.nps.gov/jeff/planyourvisit/gateway-arch-fact-sheet.htm

## Calibration

Runtime presentation (angles in degrees): `{"reference_size": 192.024, "yaw": -17, "pitch": 3, "environment": 0.85}`.

Scaling is uniform on all three axes. The catalog value calibrates the stated axis or explicit reference size; it does not certify the source as a surveyed specimen. The per-item note above states the extent and representation.

## Rebuild and review

Builder: `scripts/build_gateway_arch.py`. See `handoff/earth3d/REPORT.md` for commands, source preparation, checks and remaining production-browser work.

The rest/side images in `handoff/earth3d/previews/` are CPU orthographic previews. They include geometry, base-color textures and approximate lighting; they do not verify WebGL materials, reflections, perspective, picking, neighboring-item spacing, labels, the explorer or mobile behavior.

## Equation and cross section

NPS’s [published equation image](https://www.nps.gov/jeff/planyourvisit/images/equation.jpg), opened and visually read on 2026-10-16, specifies feet:

- Centroid height `H = 625.0925` and half-span `L = 299.2239`.
- `A = 68.7672`, `C = 3.0022`, crown drop `d(x) = A (cosh(C x/L) − 1)`.
- Centroid `y(x) = H − d(x)`.
- Base section area `1262.6651 ft²`; crown area `125.1406 ft²`.

The [NPS fact sheet](https://www.nps.gov/jeff/planyourvisit/gateway-arch-fact-sheet.htm), opened the same day, gives an equilateral triangular section, 54 ft sides at the base and 17 ft at the top, with 630 ft height and outer span. Area is interpolated linearly with crown drop; side length is its square-root equivalent. Sections lie normal to the centroid curve, with one triangle vertex facing inward and two outside. At the crown this places the exterior `17/(2√3)` ft above the centroid, giving 630 ft. The loft is extended slightly below ground then clipped at ground level, preserving the outer span rather than capping an inclined ring above the ground.

Result before nominal catalog rounding: 192.02363 m outer span and 192.02399 m height. These agree with 630 international feet (192.024 m); the runtime maps the source's 630 ft to the catalog's rounded 192 m. The builder's mesh sampling is an authored numerical approximation, not a construction survey. The source image is not a runtime texture and is not bundled.
