# PSR J0437-4715 Neutron Star — model source and limitations

A true-size smooth sphere at the catalog’s 22.72 km equatorial-diameter estimate, twice the 11.36 km radius inferred by Choudhury et al. (2024) from NICER pulse-profile modeling and radio timing. It is not a resolved surface photograph. Sphericity and blue-white color are display conventions; hot spots, beams, atmosphere and gravitational lensing are not simulated. The 2024 radius has a 68% interval of -0.63/+0.95 km. A newer NICER analysis (arXiv:2512.08790) finds a broader, larger range, so this is explicitly the catalog’s 2024 estimate, not a unique established radius.

## Scientific and geometric basis

The 2024 primary study is [Choudhury et al.](https://arxiv.org/abs/2407.06789); [NASA NICER's explanation](https://heasarc.gsfc.nasa.gov/docs/nicer/science_nuggets/20240822.html) states the 11.36 km equatorial-radius estimate. This gives 22.72 km diameter. The source radius's 16–84% credible interval is −0.63/+0.95 km. [Miller et al., published 2026](https://arxiv.org/abs/2512.08790) model an additional nonthermal component and give a symmetric 68% radius interval of 11.8–15.1 km. The catalog and model are explicitly labeled as the 2024 estimate; the later result is not silently ignored. The sphere does not simulate rotational oblateness, a hot-spot map, beams or relativistic ray tracing.

## Source, credit and rights

- Source: [https://arxiv.org/abs/2407.06789](https://arxiv.org/abs/2407.06789)
- Credit: Universe Scales
- Rights: CC0-1.0; [source terms](https://creativecommons.org/publicdomain/zero/1.0/).

## Reproduction and review

Run `./venv/bin/python scripts/build_space3d2_models.py` from the repository root. Inputs are pinned under `content/visualizations/models/sources/space3d2/`; they are not fetched at runtime. The preparation script refreshes inputs separately. No decoder extensions or external texture dependencies are used.

Units and calibration are recorded in the final entry JSON under `handoff/space3d2/`. Original sphere/Roche geometry uses km; small-body meshes retain source km; orbit coordinates preserve their AU relationships before a uniform catalog-reference conversion. Nominal solar radius and AU conversions follow [IAU 2015 B3](https://arxiv.org/html/1510.07674v1) and [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html).

CPU rest and quarter-camera previews are in `handoff/space3d2/previews/`. These are orthographic approximations, not WebGL/material, production explorer, mobile or model-lab approval. See `handoff/space3d2/REPORT.md` for the exact checks and outstanding integration work.
