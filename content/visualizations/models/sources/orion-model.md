# Orion Nebula Model Provenance

This is an authored inferred-depth illustration, not a downloaded NASA 3D mesh.
Observed sky-plane colors come from the NASA/ESA Orion Treasury mosaic:

- [Image, credits, filters and downloads](https://science.nasa.gov/asset/hubble/hubbles-sharpest-view-of-the-orion-nebula/)
- [Downloaded 1024 px derivative](https://assets.science.nasa.gov/dynamicimage/assets/science/missions/hubble/releases/2006/01/STScI-01EVT7X0BR54ZWDP1AG2DA54RA.tif?w=1024)
- Credit: NASA, ESA, Hubble Space Telescope Orion Treasury Project Team,
  Massimo Robberto (STScI, ESA).
- [NASA media usage guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/)

The Hubble field is approximately 13 light-years square. It occupies that width
inside the dataset's approximately 25-light-year whole-region span. The lower
context bracket is not a measured gas boundary. No texture or external resources
are needed at runtime; sampled colors are embedded in the GLB.

The inferred central concavity is informed by [O'Dell et al. (2009), The Three
Dimensional Structure of the Orion Nebula](https://doi.org/10.1088/0004-6256/137/1/367)
([preprint](https://arxiv.org/abs/0810.4375)). The observed gas is on a main
ionization front behind the Trapezium; the central approximately 0.2 pc offset
and approximately 0.1 pc layer thickness motivate this illustration. A smooth
Gaussian depression, all outer-field depth assignments, and the four enlarged
stellar markers are authored assumptions. Image brightness is not interpreted
as volumetric density. No claim of exact tomographic reconstruction is made.

Reproduce from the credited source image with:

```sh
./venv/bin/python scripts/build_orion_model.py --reference-image /tmp/orion-hubble-1024.jpg
python3 scripts/register_model.py /private/tmp/orion-model/entry.json /private/tmp/orion-model/orion-hubble-blister.glb
```

The source-image hash and sampling settings are recorded in `models.json`.
The original NASA/ESA image is not relicensed as CC0 or under the project code license.
