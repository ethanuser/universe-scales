# Paramecium - micro3d

Original external morphology illustration of Paramecium caudatum, using a representative 250 µm cell-body length. Martin Kreutz’s microscopy observations document 170–300 µm cells, a rounded anterior, narrower posterior, an anteriorly widening oral groove, 80–120 longitudinal rows of paired cilia, and a tuft of 10–20 µm caudal cilia. This diagram uses 80 rows; ordinary 8 µm cilia and 14 µm caudal cilia, their static bend, spacing, diameter, the body width/depth and precise oral-groove profile are authored simplifications. Cilia extend beyond the calibrated 250 µm body. The cell is opaque for small-scale legibility; internal organelles, trichocysts and refractive contents are omitted. No source photograph is copied, and this is not a scan, measured specimen surface or reconstructed 3D microscopy volume.

## Sources opened 2026-10-16

- [Martin Kreutz, Paramecium caudatum microscopy observations](https://realmicrolife.com/paramecium-caudatum/). Diagnosis: 170-300 micrometre cells, rounded anterior/narrow posterior, oral groove widening toward anterior, 80-120 rows of paired cilia. Observed caudal cilia 10-20 micrometres. Fig. 3 shows a 250 micrometre cell; no photograph or outline is copied.

## Authorship, rights and calibration

Original geometry and display materials by Universe Scales, released CC0-1.0. Only numerical facts and qualitative observations are used from the linked publications; no source figures, scans, textures or article text are redistributed. A publication license is not being substituted for the asset license.

Model units: **micrometres**. `reference_size` is **250** in those units. Equal X/Y/Z units; no anisotropic scaling. Arbitrary crop limits, annotation widths, colors and schematic geometry are display choices, not sourced measurements.

Pinned dimensions / display choices:

```json
{
  "representative_body_length_um": 250,
  "observed_length_range_um": [
    170,
    300
  ],
  "observed_ciliary_row_range": [
    80,
    120
  ],
  "illustrated_ciliary_rows": 80,
  "observed_caudal_cilia_um": [
    10,
    20
  ],
  "geometry": "original morphology illustration"
}
```

## Rebuild and review

`./venv/bin/python scripts/build_micro3d_models.py` rebuilds all ten models offline and writes the final handoff entry JSONs. Re-register them with `scripts/register_model.py` after rebuilding. `scripts/audit_micro3d_models.mjs` checks the actual vendored GLTFLoader without a browser. `scripts/preview_micro3d_cpu.py` renders rest and quarter-camera geometry plus approximate labels.

CPU images are not approval of WebGL lighting/materials, production SVG placement, perspective, explorer framing, touch interaction or mobile performance. Those checks remain with the lead because this job was explicitly instructed not to retry the documented Chromium restriction.
