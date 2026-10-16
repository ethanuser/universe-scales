# Light-Year

A straight one-light-year ruler, derived exactly from c = 299,792,458 m/s and one Julian year = 365.25 days of 86,400 s. Twelve equal marks divide the distance into twelfths of a Julian year, not calendar months. Endpoints and the line are authored measurement aids, not a wave, photon size, or an observed trajectory.

## Scientific basis and calibration

- Primary source: https://iauarchive.eso.org/public/themes/measuring/
- Parameter citations: `space3d3/parameters.json` (each group has its primary URL).
- Native units: ly.
- One catalog length is 1 native units.
- Inspection pose: {"yaw": 12} degrees, Three.js XYZ.
- Parameters and downloaded inputs are pinned by SHA-256 in `space3d3/manifest.json`.
- Source-specific numerical facts and operations: see the entry's `processing` record
  and `handoff/space3d3/space3d3-light-year-distance.entry.json`.

## Credit and rights

Universe Scales; scientific teams credited in source notes. CC0-1.0. https://creativecommons.org/publicdomain/zero/1.0/
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
