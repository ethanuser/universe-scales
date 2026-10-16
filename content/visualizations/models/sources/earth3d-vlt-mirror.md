# Very Large Telescope Mirror: 3D model provenance

VLT M1 dimensioned optical illustration: 8.2 m outer diameter, 1 m central hole, nominal 175 mm meniscus thickness. Concave surface follows the published 28.8 m radius and conic constant −1.004616. Back surface is a constant axial offset, not a measured rear surface. Cell and actuators omitted; reflections are a studio environment.

- Source: https://www.eso.org/sci/facilities/paranal/telescopes/ut/m1unit.html
- Credit: Universe Scales
- License of the delivered model: CC0-1.0 (https://creativecommons.org/publicdomain/zero/1.0/)
- Dimensional/scientific basis: https://www.eso.org/sci/facilities/paranal/telescopes/ut/m1unit.html

## Calibration

Runtime presentation (angles in degrees): `{"reference_size": 8.2, "yaw": -20, "pitch": 16, "roll": 0, "environment": 0.9}`.

Scaling is uniform on all three axes. The catalog value calibrates the stated axis or explicit reference size; it does not certify the source as a surveyed specimen. The per-item note above states the extent and representation.

## Rebuild and review

Builder: `scripts/build_everyday_models.py`. See `handoff/earth3d/REPORT.md` for commands, source preparation, checks and remaining production-browser work.

The rest/side images in `handoff/earth3d/previews/` are CPU orthographic previews. They include geometry, base-color textures and approximate lighting; they do not verify WebGL materials, reflections, perspective, picking, neighboring-item spacing, labels, the explorer or mobile behavior.
