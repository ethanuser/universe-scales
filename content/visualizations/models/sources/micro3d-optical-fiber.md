# Optical Fiber Cladding - micro3d

Original cross-section of a Corning SMF-28 Ultra type fiber: 8.2 µm nominal core diameter, 125 µm glass cladding diameter and 242 µm coating diameter. The core is not the 9.2 µm mode-field diameter. A quarter of the cladding and most of the coating are cut away. The surviving 10-degree coating sector preserves the full 121 µm outer radius; its thickness is not compressed to fit the glass diameter. Segment length (45 µm), cut orientations and opaque contrasting colors are authored presentation choices. No refractive-index profile, internal polymer-layer subdivision, propagating light ray or material transparency is simulated. The listed quantity measures glass diameter only.

## Sources opened 2026-10-16

- [Corning family specification 0396_EMEA_BEN, page 3, 2017-10-18](https://www.corning.com/catalog/coc/documents/product-family-specifications/0396_EMEA_BEN.pdf). SMF-28 Ultra core 8.2, cladding 125, coating 242 micrometres. The 9.2 micrometre mode-field diameter at 1310 nm is a different quantity.

## Authorship, rights and calibration

Original geometry and display materials by Universe Scales, released CC0-1.0. Only numerical facts and qualitative observations are used from the linked publications; no source figures, scans, textures or article text are redistributed. A publication license is not being substituted for the asset license.

Model units: **micrometres**. `reference_size` is **125** in those units. Equal X/Y/Z units; no anisotropic scaling. Arbitrary crop limits, annotation widths, colors and schematic geometry are display choices, not sourced measurements.

Pinned dimensions / display choices:

```json
{
  "core_diameter_um": 8.2,
  "cladding_diameter_um": 125,
  "coating_diameter_um": 242,
  "displayed_coating_angles_deg": [
    130,
    140
  ],
  "axial_crop_um": 45
}
```

## Rebuild and review

`./venv/bin/python scripts/build_micro3d_models.py` rebuilds all ten models offline and writes the final handoff entry JSONs. Re-register them with `scripts/register_model.py` after rebuilding. `scripts/audit_micro3d_models.mjs` checks the actual vendored GLTFLoader without a browser. `scripts/preview_micro3d_cpu.py` renders rest and quarter-camera geometry plus approximate labels.

CPU images are not approval of WebGL lighting/materials, production SVG placement, perspective, explorer framing, touch interaction or mobile performance. Those checks remain with the lead because this job was explicitly instructed not to retry the documented Chromium restriction.
