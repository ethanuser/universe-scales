# Sirius B — model source and limitations

A smooth white-dwarf sphere calibrated to the catalog’s approximate 11,300 km diameter. Bond et al. (2017) infer a radius of 0.008098 solar radii. The blue-white tint is illustrative; no resolved surface texture, accretion disk or surrounding halo is claimed. Brightness is adjusted for inspection, not compared photometrically with other stars.

## Scientific and geometric basis

Bond et al. (2017), [section 8.1](https://arxiv.org/html/1703.10625v1), gives the 0.008098 solar-radius estimate. Using the IAU nominal solar radius yields a diameter about 11,268 km, consistent with the catalog's approximate 11,300 km. The model uses that rounded catalog diameter. Blue-white color and inspection lighting are conventions, not a resolved photosphere or a cross-model luminosity comparison.

## Source, credit and rights

- Source: [https://arxiv.org/abs/1703.10625](https://arxiv.org/abs/1703.10625)
- Credit: Universe Scales
- Rights: CC0-1.0; [source terms](https://creativecommons.org/publicdomain/zero/1.0/).

## Reproduction and review

Run `./venv/bin/python scripts/build_space3d2_models.py` from the repository root. Inputs are pinned under `content/visualizations/models/sources/space3d2/`; they are not fetched at runtime. The preparation script refreshes inputs separately. No decoder extensions or external texture dependencies are used.

Units and calibration are recorded in the final entry JSON under `handoff/space3d2/`. Original sphere/Roche geometry uses km; small-body meshes retain source km; orbit coordinates preserve their AU relationships before a uniform catalog-reference conversion. Nominal solar radius and AU conversions follow [IAU 2015 B3](https://arxiv.org/html/1510.07674v1) and [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html).

CPU rest and quarter-camera previews are in `handoff/space3d2/previews/`. These are orthographic approximations, not WebGL/material, production explorer, mobile or model-lab approval. See `handoff/space3d2/REPORT.md` for the exact checks and outstanding integration work.
