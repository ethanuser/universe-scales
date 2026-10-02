# Tarantula Nebula: observed emission, illustrative depth

Credit: **ESO/R. Fosbury (ST-ECF)**. Adaptation: Universe Scales.
The photographic input and derived colors are CC BY 4.0 under
[ESO's media terms](https://www.eso.org/public/outreach/copyright/).
The adaptation does not imply ESO endorsement.

## Reference and scale

- [ESO image eso0650a](https://www.eso.org/public/images/eso0650a/), published
  21 December 2006: MPG/ESO 2.2-metre WFI mosaic in B, V, H-alpha and [O III].
- The unmodified screen-size JPEG is downloaded from
  `https://cdn.eso.org/images/screen/eso0650a.jpg`.
- The published field spans 62.40 by 62.31 arcminutes. We use that release's
  170,000-light-year distance and `2 D tan(theta/2)` to convert pixels to length.
  The distance is approximate; this is not a new astrometric fit.
- [The accompanying ESO release](https://www.eso.org/public/news/eso0650/)
  describes a nebula nearly 1,000 light-years across. A circular viewing aperture
  around the observed bright R136 region spans the dataset's 9e18 m (951 ly).
  The aperture is a crop, **not an inferred spherical gas boundary**.

## Depth and limitations

Sky-plane positions and colors are sampled from the crop. The shallow curved
layer and randomized thickness are **authored illustrative depth**. There is no
measured line-of-sight coordinate, velocity-to-distance conversion, or density
reconstruction in this model. Brightness does not set depth. The samples are
emission samples, not cataloged stars or a count of gas particles. No unobserved
gas is fabricated outside the aperture.

The GLB has float position and linear-color attributes, no textures or external
resources, and no compression decoder requirement. Reproduce it with:

```sh
./venv/bin/python scripts/build_tarantula_model.py \
  --reference-image /tmp/eso0650a.jpg --output-dir /tmp/tarantula-model
```

The generated registry entry records the input hash, crop, distance, field of
view, and point count. Inspect the registered model's rest and side views with
`scripts/model_lab.cjs`; do not treat the side view as an observed nebular shape.
