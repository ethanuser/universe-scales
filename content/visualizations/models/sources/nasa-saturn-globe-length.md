# Saturn — model source and limitations

NASA VTAD’s original oblate textured Saturn globe. The catalog mean diameter is calibrated against the source’s equatorial-diameter scale, preserving polar flattening. Rings are shown at their true relative scale under the separate Saturn’s Rings item; including them here would exceed the explorer’s 1.3× body-diameter extent rule. The texture is an illustrative global mosaic, not current weather.

## Scientific and geometric basis

The [NASA Saturn fact sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/saturnfact.html) gives equatorial radius 60,268 km and mean radius 58,232 km. The source equator is 1,000 model units. Thus reference_size = 1,000 × 116,464 / 120,536. The source flattening is retained, with no independent rescaling of the polar axis.

## Source, credit and rights

- Source: [https://science.nasa.gov/resource/saturn-3d-model/](https://science.nasa.gov/resource/saturn-3d-model/)
- Credit: NASA Visualization Technology Applications and Development (VTAD)
- Rights: U.S. public-domain NASA media/data; credit the named science teams; [source terms](https://www.nasa.gov/nasa-brand-center/images-and-media/).
- Additional rights record: [space3d2-rights.md](../licenses/space3d2-rights.md).

## Reproduction and review

Run `./venv/bin/python scripts/build_space3d2_models.py` from the repository root. Inputs are pinned under `content/visualizations/models/sources/space3d2/`; they are not fetched at runtime. The preparation script refreshes inputs separately. No decoder extensions or external texture dependencies are used.

Units and calibration are recorded in the final entry JSON under `handoff/space3d2/`. Original sphere/Roche geometry uses km; small-body meshes retain source km; orbit coordinates preserve their AU relationships before a uniform catalog-reference conversion. Nominal solar radius and AU conversions follow [IAU 2015 B3](https://arxiv.org/html/1510.07674v1) and [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html).

CPU rest and quarter-camera previews are in `handoff/space3d2/previews/`. These are orthographic approximations, not WebGL/material, production explorer, mobile or model-lab approval. See `handoff/space3d2/REPORT.md` for the exact checks and outstanding integration work.
