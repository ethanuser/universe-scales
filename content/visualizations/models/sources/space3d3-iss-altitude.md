# ISS Orbital Altitude

A local Earth cap with true spherical curvature and a surface-normal ruler to NASA’s representative 250-mile (402.336 km) ISS altitude. The local cap is an arbitrary display window, not the whole Earth or an island boundary. Its 40 km underside is an authored cut, not crust depth. The ISS is a location glyph; its 109 m span is subpixel here. The altitude varies and this is not current telemetry. The ground imagery is the existing NASA global map with no invented terrain.

## Scientific basis and calibration

- Primary source: https://www.nasa.gov/international-space-station/
- Parameter citations: `space3d3/parameters.json` (each group has its primary URL).
- Native units: reference distance.
- One catalog length is 1 native units.
- Inspection pose: {"pitch": 20, "yaw": -12, "roll": -10} degrees, Three.js XYZ.
- Parameters and downloaded inputs are pinned by SHA-256 in `space3d3/manifest.json`.
- Source-specific numerical facts and operations: see the entry's `processing` record
  and `handoff/space3d3/space3d3-iss-altitude.entry.json`.

## Credit and rights

Universe Scales; scientific teams credited in source notes. U.S. public-domain NASA media/data; credit the named science teams. https://www.nasa.gov/nasa-brand-center/images-and-media/
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
