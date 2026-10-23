# Basketball: 3D model provenance

Superseded by the licensed photoscan documented in
[`upgrade3d-basketball-scan.md`](upgrade3d-basketball-scan.md). This file records
the previous illustration; its original builder is not the current import path.

Representative size-7 basketball. Wilson specifies 29.5 inches circumference (238.51 mm derived diameter), rounded to the catalog’s 239 mm. Original pebble texture and eight-panel channel pattern are illustrative.

- Source: https://au.wilson.com/pages/how-to-choose-a-basketball/1000
- Credit: Universe Scales
- License of the delivered model: CC0-1.0 (https://creativecommons.org/publicdomain/zero/1.0/)
- Dimensional/scientific basis: https://au.wilson.com/pages/how-to-choose-a-basketball/1000

## Calibration

Runtime presentation (angles in degrees): `{"reference_size": 0.239, "yaw": 20, "pitch": 12, "roll": 0}`.

Scaling is uniform on all three axes. The catalog value calibrates the stated axis or explicit reference size; it does not certify the source as a surveyed specimen. The per-item note above states the extent and representation.

## Rebuild and review

Builder: `scripts/build_everyday_models.py`. See `handoff/earth3d/REPORT.md` for commands, source preparation, checks and remaining production-browser work.

The rest/side images in `handoff/earth3d/previews/` are CPU orthographic previews. They include geometry, base-color textures and approximate lighting; they do not verify WebGL materials, reflections, perspective, picking, neighboring-item spacing, labels, the explorer or mobile behavior.
