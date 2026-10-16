# Sun-Galactic Center Distance

A Sun-to-Galactic-center measurement diagram spanning the 2019 GRAVITY geometric distance of 8,178 pc. The only local cloud context is the same 141 measured Alves et al. (2020) Radcliffe cloud locations, drawn in true heliocentric Galactic Cartesian parsecs at the same scale. X points toward the Galactic Center; Galactic north is up. Endpoint glyphs are location aids, not the dimensions of the Sun or black hole. No Milky Way outline, star density or galactic bar is invented.

## Scientific basis and calibration

- Primary source: https://arxiv.org/html/1904.05721v1
- Parameter citations: `space3d3/parameters.json` (each group has its primary URL).
- Native units: pc.
- One catalog length is 8178 native units.
- Inspection pose: {"pitch": 20, "yaw": -10} degrees, Three.js XYZ.
- Parameters and downloaded inputs are pinned by SHA-256 in `space3d3/manifest.json`.
- Source-specific numerical facts and operations: see the entry's `processing` record
  and `handoff/space3d3/space3d3-galactic-center-distance.entry.json`.

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
