# Eris — model source and limitations

An idealized untextured icy sphere at the 2,326 km diameter measured by Sicardy et al. (2011) from a stellar occultation (about ±12 km). It is not a spacecraft-derived terrain model: no resolved surface map of Eris is available here. Bright neutral material suggests its high reflectivity without inventing craters or albedo markings. Dysnomia is omitted.

## Scientific and geometric basis

The ESO source reports the Sicardy et al. (2011) stellar-occultation diameter 2,326 ±12 km and a very reflective surface. This original CC0 sphere uses that diameter without invented terrain, landforms, textures or a model of Dysnomia. The paper is [doi:10.1038/nature10550](https://doi.org/10.1038/nature10550).

## Source, credit and rights

- Source: [https://www.eso.org/public/news/eso1142/](https://www.eso.org/public/news/eso1142/)
- Credit: Universe Scales
- Rights: CC0-1.0; [source terms](https://creativecommons.org/publicdomain/zero/1.0/).

## Reproduction and review

Run `./venv/bin/python scripts/build_space3d2_models.py` from the repository root. Inputs are pinned under `content/visualizations/models/sources/space3d2/`; they are not fetched at runtime. The preparation script refreshes inputs separately. No decoder extensions or external texture dependencies are used.

Units and calibration are recorded in the final entry JSON under `handoff/space3d2/`. Original sphere/Roche geometry uses km; small-body meshes retain source km; orbit coordinates preserve their AU relationships before a uniform catalog-reference conversion. Nominal solar radius and AU conversions follow [IAU 2015 B3](https://arxiv.org/html/1510.07674v1) and [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html).

CPU rest and quarter-camera previews are in `handoff/space3d2/previews/`. These are orthographic approximations, not WebGL/material, production explorer, mobile or model-lab approval. See `handoff/space3d2/REPORT.md` for the exact checks and outstanding integration work.
