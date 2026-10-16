# Sagittarius A* Event Horizon

A Schwarzschild reference horizon calculated as r_s = 2GM/c² from the 2019 GRAVITY noise-model mass of 4.152 million solar masses. Its Euclidean drawing diameter is about 24.52 million km, close to the catalog’s approximate 25.4 million km. This is a mass-based nonrotating reference boundary, not an observed black surface, EHT shadow, accretion disk, or embedding of curved space. Violet great circles and the rim are authored guides to the causal boundary; their thickness is not physical. Spin and mass uncertainty are not modeled.

## Scientific basis and calibration

- Primary source: https://arxiv.org/html/1904.05721v1
- Parameter citations: `space3d3/parameters.json` (each group has its primary URL).
- Native units: km.
- One catalog length is 25400000 native units.
- Inspection pose: {"pitch": 15, "yaw": 18} degrees, Three.js XYZ.
- Parameters and downloaded inputs are pinned by SHA-256 in `space3d3/manifest.json`.
- Source-specific numerical facts and operations: see the entry's `processing` record
  and `handoff/space3d3/space3d3-sgr-a-horizon.entry.json`.

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
