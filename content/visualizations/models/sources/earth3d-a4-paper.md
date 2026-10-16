# A4 Paper: 3D model provenance

ISO 216 A4: 210 × 297 mm. A flat, double-sided sheet surface; thickness is deliberately not modeled because ISO 216 defines the trimmed edges, not a paper stock. No exaggerated curl or thickness.

- Source: https://preview.sist.si/sist-preview/4087/9050e9a6768b43e2bcdedca70c895c61/ISO-216-1975.pdf
- Credit: Universe Scales
- License of the delivered model: CC0-1.0 (https://creativecommons.org/publicdomain/zero/1.0/)
- Dimensional/scientific basis: https://preview.sist.si/sist-preview/4087/9050e9a6768b43e2bcdedca70c895c61/ISO-216-1975.pdf

## Calibration

Runtime presentation (angles in degrees): `{"reference_size": 0.297, "yaw": -15, "pitch": 9, "roll": 0}`.

Scaling is uniform on all three axes. The catalog value calibrates the stated axis or explicit reference size; it does not certify the source as a surveyed specimen. The per-item note above states the extent and representation.

## Rebuild and review

Builder: `scripts/build_everyday_models.py`. See `handoff/earth3d/REPORT.md` for commands, source preparation, checks and remaining production-browser work.

The rest/side images in `handoff/earth3d/previews/` are CPU orthographic previews. They include geometry, base-color textures and approximate lighting; they do not verify WebGL materials, reflections, perspective, picking, neighboring-item spacing, labels, the explorer or mobile behavior.
