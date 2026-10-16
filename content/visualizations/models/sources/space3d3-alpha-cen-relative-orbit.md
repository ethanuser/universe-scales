# Alpha Centauri A-B Orbit

Pourbaix & Boffin (2016) HARPS+ESO relative orbital solution: angular semimajor axis 17.66 arcsec / parallax 0.743 arcsec gives a = 23.7685 AU, e = 0.524 and P = 79.91 years. The blue ellipse is B’s relative orbit in a frame centered on A; it is not a pair of barycentric trajectories. The authored orbital-plane inspection view exposes the intrinsic ellipse rather than its nearly edge-on sky projection. A and B are location glyphs, with B shown at periastron; stellar diameters are not implied.

## Scientific basis and calibration

- Primary source: https://arxiv.org/html/1601.01636v1
- Parameter citations: `space3d3/parameters.json` (each group has its primary URL).
- Native units: AU.
- One catalog length is 46.8 native units.
- Inspection pose: {"pitch": 24, "roll": -8} degrees, Three.js XYZ.
- Parameters and downloaded inputs are pinned by SHA-256 in `space3d3/manifest.json`.
- Source-specific numerical facts and operations: see the entry's `processing` record
  and `handoff/space3d3/space3d3-alpha-cen-relative-orbit.entry.json`.

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
