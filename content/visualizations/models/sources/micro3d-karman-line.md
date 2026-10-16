# Karman Line - micro3d

Local geometric altitude section: 100 km from sea level to the FAI Kármán-line convention, using equal horizontal and vertical kilometres. Two small spherical patches use the 6,371 km mean Earth radius used in PREM and radii 6,371 and 6,471 km. The upper cyan patch and gold ruler are measurement guides, not physical surfaces, a sharp atmosphere edge or a shell of air. The 68 by 18 km local window is an authored crop. No exponential-density scale, abrupt sky-color boundary, launch trajectory, topography or horizontally compressed globe is invented. The full Earth is omitted because its diameter is over 127 times the listed altitude.

## Sources opened 2026-10-16

- [FAI statement, 2018](https://www.fai.org/news/statement-about-karman-line). 100 km conventional altitude boundary.
- [Capozzi and Petcov, 2022, section 1](https://link.springer.com/article/10.1140/epjc/s10052-022-10399-6). PREM mean Earth radius 6,371 km, used solely for local spherical curvature.

## Authorship, rights and calibration

Original geometry and display materials by Universe Scales, released CC0-1.0. Only numerical facts and qualitative observations are used from the linked publications; no source figures, scans, textures or article text are redistributed. A publication license is not being substituted for the asset license.

Model units: **kilometres**. `reference_size` is **100.0** in those units. Equal X/Y/Z units; no anisotropic scaling. Arbitrary crop limits, annotation widths, colors and schematic geometry are display choices, not sourced measurements.

Pinned dimensions / display choices:

```json
{
  "conventional_altitude_km": 100.0,
  "mean_earth_radius_km": 6371.0,
  "radius_source": "https://link.springer.com/article/10.1140/epjc/s10052-022-10399-6",
  "local_crop_km": [
    68,
    18
  ],
  "vertical_exaggeration": 1
}
```

## Rebuild and review

`./venv/bin/python scripts/build_micro3d_models.py` rebuilds all ten models offline and writes the final handoff entry JSONs. Re-register them with `scripts/register_model.py` after rebuilding. `scripts/audit_micro3d_models.mjs` checks the actual vendored GLTFLoader without a browser. `scripts/preview_micro3d_cpu.py` renders rest and quarter-camera geometry plus approximate labels.

CPU images are not approval of WebGL lighting/materials, production SVG placement, perspective, explorer framing, touch interaction or mobile performance. Those checks remain with the lead because this job was explicitly instructed not to retry the documented Chromium restriction.
