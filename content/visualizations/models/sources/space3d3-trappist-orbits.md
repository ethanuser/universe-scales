# TRAPPIST-1 System

Seven coplanar circular reference orbits use Agol et al. (2021) semimajor axes, planet radii and 0.1192-solar-radius star. The circular approximation omits their small measured eccentricities; planet phases and the inspection view are authored, not ephemeris. Planet/star radii share the AU orbit scale; thin outline markers keep tiny planets findable. Colors are illustrative and do not assert surface maps, oceans or habitability. The outer orbit’s 0.12378 AU diameter is close to the catalog’s rounded 0.1238 AU.

## Scientific basis and calibration

- Primary source: https://arxiv.org/html/2010.01074v2
- Parameter citations: `space3d3/parameters.json` (each group has its primary URL).
- Native units: AU.
- One catalog length is 0.1238 native units.
- Inspection pose: {"pitch": 30, "roll": -14} degrees, Three.js XYZ.
- Parameters and downloaded inputs are pinned by SHA-256 in `space3d3/manifest.json`.
- Source-specific numerical facts and operations: see the entry's `processing` record
  and `handoff/space3d3/space3d3-trappist-orbits.entry.json`.

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
