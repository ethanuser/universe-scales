# Great Red Spot — model source and limitations

An enhanced-color Juno cloud image (12 February 2019) draped over an idealized shallow cloud-top patch. The storm is shown at the catalog’s representative April 2017 width of 16,350 km. This is an illustrative size comparison using later imagery, not a measured 2019 map or a claim that the storm’s size stayed constant. The surrounding collar is context. Curvature is schematic; neither cloud heights nor storm depth are reconstructed. Credit NASA/JPL-Caltech/SwRI/MSSS; processing Kevin M. Gill, CC BY; cropped and draped by Universe Scales.

## Scientific and geometric basis

PIA23606 is a 2,793 × 1,156 enhanced-color mosaic. We crop pixels (1740, 80) to (2760, 1000), retaining the complete storm and surrounding collar. The 12 February 2019 image is used as a qualitative texture at the catalog's representative 2017 width, not as contemporaneous astrometry. The [NASA 2017 size report](https://www.nasa.gov/image-article/jupiters-great-red-spot-swallows-earth/) supplies 16,350 km. Approximate spherical cloud-top curvature uses the [NASA Jupiter equatorial radius](https://nssdc.gsfc.nasa.gov/planetary/factsheet/jupiterfact.html) of 71,492 km. No depth measurement is implied.

## Source, credit and rights

- Source: [https://science.nasa.gov/photojournal/the-great-red-spot/](https://science.nasa.gov/photojournal/the-great-red-spot/)
- Credit: NASA/JPL-Caltech/SwRI/MSSS; image processing Kevin M. Gill; adapted by Universe Scales
- Rights: CC BY (image processing); NASA public-domain image data; [source terms](https://science.nasa.gov/photojournal/the-great-red-spot/).
- Download: [https://assets.science.nasa.gov/content/dam/science/psd/photojournal/pia/pia23/pia23606/PIA23606.jpg](https://assets.science.nasa.gov/content/dam/science/psd/photojournal/pia/pia23/pia23606/PIA23606.jpg)
- Original SHA-256: `68c42665d4edc8da87d9baa481b0f2192a3d5f9cadc20db5be3023682fe0f8dc` (520,993 bytes).
- Additional rights record: [space3d2-rights.md](../licenses/space3d2-rights.md).

## Reproduction and review

Run `./venv/bin/python scripts/build_space3d2_models.py` from the repository root. Inputs are pinned under `content/visualizations/models/sources/space3d2/`; they are not fetched at runtime. The preparation script refreshes inputs separately. No decoder extensions or external texture dependencies are used.

Units and calibration are recorded in the final entry JSON under `handoff/space3d2/`. Original sphere/Roche geometry uses km; small-body meshes retain source km; orbit coordinates preserve their AU relationships before a uniform catalog-reference conversion. Nominal solar radius and AU conversions follow [IAU 2015 B3](https://arxiv.org/html/1510.07674v1) and [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html).

CPU rest and quarter-camera previews are in `handoff/space3d2/previews/`. These are orthographic approximations, not WebGL/material, production explorer, mobile or model-lab approval. See `handoff/space3d2/REPORT.md` for the exact checks and outstanding integration work.
