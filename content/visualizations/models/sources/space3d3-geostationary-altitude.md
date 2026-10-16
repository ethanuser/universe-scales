# Geostationary Orbit

A 35,786 km surface-to-orbit radial altitude, with the Earth at the same physical scale. The nearby cyan arc is only a 24-degree segment of the circular equatorial geostationary orbit, not its full diameter. The center-to-orbit radius is Earth’s equatorial radius plus the listed altitude. The spacecraft point is a location glyph. The inspection pose foreshortens the radial ruler slightly; no coordinates are stretched.

## Scientific basis and calibration

- Primary source: https://www.esa.int/ESA_Multimedia/Images/2020/03/Geostationary_orbit
- Parameter citations: `space3d3/parameters.json` (each group has its primary URL).
- Native units: reference distance.
- One catalog length is 1 native units.
- Inspection pose: {"pitch": 25, "yaw": 40} degrees, Three.js XYZ.
- Parameters and downloaded inputs are pinned by SHA-256 in `space3d3/manifest.json`.
- Source-specific numerical facts and operations: see the entry's `processing` record
  and `handoff/space3d3/space3d3-geostationary-altitude.entry.json`.

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
