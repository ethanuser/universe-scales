# Helium Nucleus Charge Diameter - micro3d

Helium-4 measurement diagram. Three thin guides mark twice the CODATA 2022 rms charge radius 1.6785(21) fm: 3.357 fm. An rms radius is a moment of the charge distribution, not a hard outer boundary. Four overlapping colored nucleon glyphs show two protons and two neutrons; their radii, positions, colors and static tetrahedral arrangement are authored symbols, not measured nucleon surfaces or a nuclear-structure reconstruction. No electron cloud is shown.

## Sources opened 2026-10-16

- [CODATA 2022 alpha-particle rms charge radius](https://physics.nist.gov/cgi-bin/cuu/Value?ral%7Csearch_for=charge). 1.6785 fm, standard uncertainty 0.0021 fm; twice the radius is 3.357 fm.
- [Krauth et al., 2021, independent muonic-helium determination](https://www.nature.com/articles/s41586-021-03183-1). The 1.67824(83) fm result is a particular experiment, not the CODATA central value used here.

## Authorship, rights and calibration

Original geometry and display materials by Universe Scales, released CC0-1.0. Only numerical facts and qualitative observations are used from the linked publications; no source figures, scans, textures or article text are redistributed. A publication license is not being substituted for the asset license.

Model units: **femtometres**. `reference_size` is **3.357** in those units. Equal X/Y/Z units; no anisotropic scaling. Arbitrary crop limits, annotation widths, colors and schematic geometry are display choices, not sourced measurements.

Pinned dimensions / display choices:

```json
{
  "rms_charge_radius_fm": 1.6785,
  "rms_uncertainty_fm": 0.0021,
  "diameter_fm": 3.357,
  "nucleon_glyphs": "schematic only"
}
```

## Rebuild and review

`./venv/bin/python scripts/build_micro3d_models.py` rebuilds all ten models offline and writes the final handoff entry JSONs. Re-register them with `scripts/register_model.py` after rebuilding. `scripts/audit_micro3d_models.mjs` checks the actual vendored GLTFLoader without a browser. `scripts/preview_micro3d_cpu.py` renders rest and quarter-camera geometry plus approximate labels.

CPU images are not approval of WebGL lighting/materials, production SVG placement, perspective, explorer framing, touch interaction or mobile performance. Those checks remain with the lead because this job was explicitly instructed not to retry the documented Chromium restriction.
