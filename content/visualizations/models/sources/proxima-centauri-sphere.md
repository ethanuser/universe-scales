# Proxima Centauri Diameter — model source and limitations

A smooth red-dwarf sphere calibrated to the catalog diameter, from the 0.1542 solar-radius estimate of Kervella et al. (2017). Warm color and inspection lighting are illustrative; no resolved photospheric map, invented spots, flares or corona is implied. Apparent brightness is adjusted for visibility and is not a luminosity comparison.

## Scientific and geometric basis

[Kervella et al. (2017)](https://www.aanda.org/articles/aa/pdf/2017/02/aa29930-16.pdf) infer radius 0.1542 ±0.0045 solar radii from the radius–absolute-K-magnitude relation. It is not described here as a directly resolved surface measurement. Using the nominal solar radius 695,700 km gives catalog diameter 214,553.88 km. Geometry is smooth; spots, flares and coronal structures are omitted.

## Source, credit and rights

- Source: [https://www.aanda.org/articles/aa/pdf/2017/02/aa29930-16.pdf](https://www.aanda.org/articles/aa/pdf/2017/02/aa29930-16.pdf)
- Credit: Universe Scales
- Rights: CC0-1.0; [source terms](https://creativecommons.org/publicdomain/zero/1.0/).

## Reproduction and review

Run `./venv/bin/python scripts/build_space3d2_models.py` from the repository root. Inputs are pinned under `content/visualizations/models/sources/space3d2/`; they are not fetched at runtime. The preparation script refreshes inputs separately. No decoder extensions or external texture dependencies are used.

Units and calibration are recorded in the final entry JSON under `handoff/space3d2/`. Original sphere/Roche geometry uses km; small-body meshes retain source km; orbit coordinates preserve their AU relationships before a uniform catalog-reference conversion. Nominal solar radius and AU conversions follow [IAU 2015 B3](https://arxiv.org/html/1510.07674v1) and [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html).

CPU rest and quarter-camera previews are in `handoff/space3d2/previews/`. These are orthographic approximations, not WebGL/material, production explorer, mobile or model-lab approval. See `handoff/space3d2/REPORT.md` for the exact checks and outstanding integration work.
