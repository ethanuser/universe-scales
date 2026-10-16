# Silicon Wafer: 3D model provenance

Bare polished 300 mm silicon wafer, using SVM SV031 nominal 775 µm thickness and a 1 mm-deep 90° notch. No invented chip layout or enlarged circuitry; violet-gray appearance is illustrative.

- Source: https://svmi.com/wp-content/uploads/2020/09/SV031.pdf
- Credit: Universe Scales
- License of the delivered model: CC0-1.0 (https://creativecommons.org/publicdomain/zero/1.0/)
- Dimensional/scientific basis: https://svmi.com/wp-content/uploads/2020/09/SV031.pdf

## Calibration

Runtime presentation (angles in degrees): `{"reference_size": 0.3, "yaw": -15, "pitch": 9, "roll": 0, "environment": 0.8}`.

Scaling is uniform on all three axes. The catalog value calibrates the stated axis or explicit reference size; it does not certify the source as a surveyed specimen. The per-item note above states the extent and representation.

## Rebuild and review

Builder: `scripts/build_everyday_models.py`. See `handoff/earth3d/REPORT.md` for commands, source preparation, checks and remaining production-browser work.

The rest/side images in `handoff/earth3d/previews/` are CPU orthographic previews. They include geometry, base-color textures and approximate lighting; they do not verify WebGL materials, reflections, perspective, picking, neighboring-item spacing, labels, the explorer or mobile behavior.
