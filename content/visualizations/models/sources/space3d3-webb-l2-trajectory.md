# James Webb Space Telescope Orbit

JPL Horizons JWST_merged geometric Earth-centered vectors for 1 January 2024–1 January 2025, sampled every two TDB days and rotated at each epoch into a Sun–Earth co-rotating frame. The real non-closing trajectory is preserved, with no fabricated halo ellipse or amplified depth. The ruler spans NASA’s approximate 1.5 million km Earth-to-L2 distance, not the halo diameter or a constant telescope range. A faint circular lunar mean-distance guide is context, not lunar ephemeris. Location glyphs are enlarged; the Earth and Moon have physical radii.

## Scientific basis and calibration

- Primary source: https://science.nasa.gov/mission/webb/orbit/
- Parameter citations: `space3d3/parameters.json` (each group has its primary URL).
- Native units: reference distance.
- One catalog length is 1 native units.
- Inspection pose: {"pitch": 22, "yaw": -55} degrees, Three.js XYZ.
- Parameters and downloaded inputs are pinned by SHA-256 in `space3d3/manifest.json`.
- Source-specific numerical facts and operations: see the entry's `processing` record
  and `handoff/space3d3/space3d3-webb-l2-trajectory.entry.json`.

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
