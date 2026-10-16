# Halley's Comet Orbit — model source and limitations

JPL SBDB heliocentric osculating ellipse for 1P/Halley, at the returned 1968 epoch; the ruler measures the entire major axis, not a Sun-to-comet radius or traveled path. Faint Earth/Jupiter ellipses are JPL J2000 reference orbits for context. This is a static two-body orbital diagram, not a current comet position or a full N-body trajectory. The Sun and endpoint dots are enlarged location markers, not true body diameters.

## Scientific and geometric basis

The pinned API response gives epoch JD 2439875.5 TDB (20 January 1968), a = 17.92863504856923 AU, e = 0.9679359956953211, and full orientation elements. Its major axis is 35.8572701 AU; calibration retains the catalog 5.3068348652118e12 m rather than stretching this source ellipse. The Sun is at the focus. The ruler joins perihelion to aphelion, spanning the full major axis. The source's old comet epoch is explicit; no current Halley position is shown. Faint Earth–Moon-barycenter and Jupiter J2000 reference ellipses come from [JPL Table 1](https://ssd.jpl.nasa.gov/planets/approx_pos.html), not made-up circles. All body dots are enlarged location glyphs.

## Source, credit and rights

- Source: [https://ssd-api.jpl.nasa.gov/doc/sbdb.html](https://ssd-api.jpl.nasa.gov/doc/sbdb.html)
- Credit: NASA/JPL Solar System Dynamics; diagram by Universe Scales
- Rights: U.S. public-domain NASA media/data; credit the named science teams; [source terms](https://www.nasa.gov/nasa-brand-center/images-and-media/).
- Download: [https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=1P&full-prec=1](https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=1P&full-prec=1)
- Original SHA-256: `69353b4bb9ea975e250afa996b3da776b7db17096b534065982a872ff85bde54` (4,092 bytes).
- Additional rights record: [space3d2-rights.md](../licenses/space3d2-rights.md).

## Reproduction and review

Run `./venv/bin/python scripts/build_space3d2_models.py` from the repository root. Inputs are pinned under `content/visualizations/models/sources/space3d2/`; they are not fetched at runtime. The preparation script refreshes inputs separately. No decoder extensions or external texture dependencies are used.

Units and calibration are recorded in the final entry JSON under `handoff/space3d2/`. Original sphere/Roche geometry uses km; small-body meshes retain source km; orbit coordinates preserve their AU relationships before a uniform catalog-reference conversion. Nominal solar radius and AU conversions follow [IAU 2015 B3](https://arxiv.org/html/1510.07674v1) and [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html).

CPU rest and quarter-camera previews are in `handoff/space3d2/previews/`. These are orthographic approximations, not WebGL/material, production explorer, mobile or model-lab approval. See `handoff/space3d2/REPORT.md` for the exact checks and outstanding integration work.
