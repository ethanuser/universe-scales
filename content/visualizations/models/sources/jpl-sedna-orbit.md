# Sedna Aphelion — model source and limitations

JPL SBDB heliocentric osculating ellipse for Sedna at the pinned 2026 epoch. The ruler runs from the Sun’s focus to aphelion, not across the whole ellipse. This source solution gives Q about 1,011 AU, differing from the catalog’s older approximate 937 AU; coordinates are preserved without stretching. The diagram is a two-body snapshot, not a measured future trajectory. Sun and endpoint dots are enlarged location markers, not physical bodies.

## Scientific and geometric basis

The pinned source solution is epoch JD 2461200.5 TDB (9 June 2026), a = 543.7195289104732 AU, e = 0.8598824585187618; Q = 1011.254414174674 AU, about 1.512815071e14 m. The catalog remains 1.4e14 m (~937 AU). Calibration retains the catalog meters/AU reference while the native source ellipse is never stretched. The ruler starts at the Sun's focus and ends at aphelion; it does not measure the full ellipse. A two-body osculating ellipse does not predict the exact future trajectory under planetary perturbations.

## Source, credit and rights

- Source: [https://ssd-api.jpl.nasa.gov/doc/sbdb.html](https://ssd-api.jpl.nasa.gov/doc/sbdb.html)
- Credit: NASA/JPL Solar System Dynamics; diagram by Universe Scales
- Rights: U.S. public-domain NASA media/data; credit the named science teams; [source terms](https://www.nasa.gov/nasa-brand-center/images-and-media/).
- Download: [https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=90377&full-prec=1](https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=90377&full-prec=1)
- Original SHA-256: `9073e7e92d11f68758a0275e3b766f857647859d313aa2d2d5c4af488fa17152` (3,255 bytes).
- Additional rights record: [space3d2-rights.md](../licenses/space3d2-rights.md).

## Reproduction and review

Run `./venv/bin/python scripts/build_space3d2_models.py` from the repository root. Inputs are pinned under `content/visualizations/models/sources/space3d2/`; they are not fetched at runtime. The preparation script refreshes inputs separately. No decoder extensions or external texture dependencies are used.

Units and calibration are recorded in the final entry JSON under `handoff/space3d2/`. Original sphere/Roche geometry uses km; small-body meshes retain source km; orbit coordinates preserve their AU relationships before a uniform catalog-reference conversion. Nominal solar radius and AU conversions follow [IAU 2015 B3](https://arxiv.org/html/1510.07674v1) and [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html).

CPU rest and quarter-camera previews are in `handoff/space3d2/previews/`. These are orthographic approximations, not WebGL/material, production explorer, mobile or model-lab approval. See `handoff/space3d2/REPORT.md` for the exact checks and outstanding integration work.
