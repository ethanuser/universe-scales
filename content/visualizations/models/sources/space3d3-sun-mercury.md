# Sun-Mercury Distance

NASA Sun and Mercury image maps on idealized spheres, separated by the NASA fact-sheet semimajor axis of 57,909,000 km. Body radii and distance use the same physical scale. This is a representative center-to-center separation equal to a, not an orbital snapshot or the diameter of the orbit. Subpixel body outlines are location aids. Faint inner reference ellipses, where present, use JPL J2000 elements and are not simultaneous planet positions.

## Scientific basis and calibration

- Primary source: https://nssdc.gsfc.nasa.gov/planetary/factsheet/mercuryfact.html
- Parameter citations: `space3d3/parameters.json` (each group has its primary URL).
- Native units: reference distance.
- One catalog length is 1 native units.
- Inspection pose: {"pitch": 32} degrees, Three.js XYZ.
- Parameters and downloaded inputs are pinned by SHA-256 in `space3d3/manifest.json`.
- Source-specific numerical facts and operations: see the entry's `processing` record
  and `handoff/space3d3/space3d3-sun-mercury.entry.json`.

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
