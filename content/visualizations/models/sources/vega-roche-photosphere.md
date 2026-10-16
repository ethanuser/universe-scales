# Vega Diameter — model source and limitations

An oblate Roche equipotential using Monnier et al. (2012) CHARA/MIRC concordance-model equatorial and polar radii, 2.726 and 2.418 solar radii. Latitude shading qualitatively illustrates gravity darkening (polar temperature 10,070 K, exponent 0.231); it is not an observed surface map or calibrated color photometry. The oblique inspection view deliberately exposes flattening. From Earth Vega is seen nearly pole-on (~6.2°), so this is not its sky orientation. Earlier Aufdenberg et al. (2006) modeling supports rapid rotation but gives different parameters.

## Scientific and geometric basis

[Monnier et al. (2012), Table 2, concordance model](https://arxiv.org/html/1211.6055v1) gives equatorial radius 2.726 solar radii, polar radius 2.418 solar radii, polar temperature 10,070 K and gravity-darkening exponent 0.231. The Roche potential is solved with these radius endpoints; analytic effective-gravity normals and a smooth latitude texture retain the predicted dimmer equator. Texture color/contrast are illustrative, not synthetic photometry. The authored oblique view exposes the flattening; Earth's line of sight is about 6.2° from the pole. [Aufdenberg et al. (2006)](https://arxiv.org/abs/astro-ph/0603327) independently support rapid pole-on rotation but give an earlier, different best fit. We use one coherent 2012 parameter set rather than mixing the two.

## Source, credit and rights

- Source: [https://arxiv.org/html/1211.6055v1](https://arxiv.org/html/1211.6055v1)
- Credit: Universe Scales
- Rights: CC0-1.0; [source terms](https://creativecommons.org/publicdomain/zero/1.0/).

## Reproduction and review

Run `./venv/bin/python scripts/build_space3d2_models.py` from the repository root. Inputs are pinned under `content/visualizations/models/sources/space3d2/`; they are not fetched at runtime. The preparation script refreshes inputs separately. No decoder extensions or external texture dependencies are used.

Units and calibration are recorded in the final entry JSON under `handoff/space3d2/`. Original sphere/Roche geometry uses km; small-body meshes retain source km; orbit coordinates preserve their AU relationships before a uniform catalog-reference conversion. Nominal solar radius and AU conversions follow [IAU 2015 B3](https://arxiv.org/html/1510.07674v1) and [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html).

CPU rest and quarter-camera previews are in `handoff/space3d2/previews/`. These are orthographic approximations, not WebGL/material, production explorer, mobile or model-lab approval. See `handoff/space3d2/REPORT.md` for the exact checks and outstanding integration work.
