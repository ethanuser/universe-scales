# M87* Shadow

The real 2017 EHT reconstructed radio sky image (EHT Collaboration; ESO eso1907a), on a flat circular sky-plane aperture. The intensity ridge is registered approximately to the reported 42 ± 3 microarcsec emission-ring diameter at 16.8 Mpc (~105.6 billion km). The catalog’s ~103 billion km refers to this ring/shadow scale, not the event horizon. A feathered aperture cuts the outskirts at 1.24 ring diameters, preserving the intensity ridge. No 3D plasma, accretion geometry, or solid hole is inferred; rotation exposes a flat image. Orange is the published radio-intensity color mapping, not visible-light fire.

## Scientific basis and calibration

- Primary source: https://www.eso.org/public/images/eso1907a/
- Parameter citations: `space3d3/parameters.json` (each group has its primary URL).
- Native units: km.
- One catalog length is 103000000000 native units.
- Inspection pose: {} degrees, Three.js XYZ.
- Parameters and downloaded inputs are pinned by SHA-256 in `space3d3/manifest.json`.
- Source-specific numerical facts and operations: see the entry's `processing` record
  and `handoff/space3d3/space3d3-m87-eht-ring.entry.json`.

## Credit and rights

EHT Collaboration; registered image aperture assembled by Universe Scales. CC-BY-4.0. https://creativecommons.org/licenses/by/4.0/
Original authored diagram geometry is CC0. Scientific paper text/figures are not
redistributed. NASA textures retain NASA credit and usage terms. The EHT color
image, where present, retains EHT Collaboration credit under CC BY 4.0, verified
on ESO's source page and copyright policy. Radcliffe numerical cloud coordinates
are from the authors' supplement and its CC0 cloud database (DataCite rights
record retained at `space3d3/radcliffe-data-rights.json`); the Plotly code/graphic
and fitted/posterior cloud samples are not redistributed.

## Rebuild and limitations

Run `./venv/bin/python scripts/build_space3d3_models.py` offline. Refreshing inputs
is separate: `scripts/prepare_space3d3_sources.py`. No runtime data service is used.
The handoff contains rest and quarter-camera CPU previews and loader checks.
These do not certify WebGL appearance, perspective, production SVG label handling,
the actual explorer, mobile, or the production model-lab audit.
