# Radcliffe Wave

All 141 measured cloud locations selected as Radcliffe Wave members in Alves et al. (2020), extracted from the authors’ interactive supplement. Heliocentric Galactic Cartesian parsecs remain isotropic: no vertical exaggeration, fitted sine wave, synthetic cloud fill, or invented connecting tube. Colors and finite point sprites are authored identification aids, not gas extent, density, or individual stars. The inspection frame aligns the observed long axis horizontally with Galactic north up. The Sun is a location glyph. The 500 pc bar is a physical ruler; the catalog’s ~8,800 ly is an approximate chain length.

## Scientific basis and calibration

- Primary source: https://doi.org/10.1038/s41586-019-1874-z
- Parameter citations: `space3d3/parameters.json` (each group has its primary URL).
- Native units: pc.
- One catalog length is 2698.09226531 native units.
- Inspection pose: {"pitch": 18, "roll": -6} degrees, Three.js XYZ.
- Parameters and downloaded inputs are pinned by SHA-256 in `space3d3/manifest.json`.
- Source-specific numerical facts and operations: see the entry's `processing` record
  and `handoff/space3d3/space3d3-radcliffe-clouds.entry.json`.

## Credit and rights

João Alves, Catherine Zucker, Alyssa Goodman and collaborators; CC0 cloud data; assembly by Universe Scales. CC0-1.0. https://creativecommons.org/publicdomain/zero/1.0/
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
