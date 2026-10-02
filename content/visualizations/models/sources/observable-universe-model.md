# Observable Universe Causal-Horizon Diagram

## Observed sky data

The shell texture is derived from the NASA/LAMBDA [WMAP nine-year Internal
Linear Combination map](https://lambda.gsfc.nasa.gov/product/wmap/dr5/ilc_map_info.html).
The source product is a full-sky Galactic-coordinate HEALPix FITS map in
NESTED ordering (`Nside=512`; thermodynamic mK). The direct source file is
[wmap_ilc_9yr_v5.fits](https://lambda.gsfc.nasa.gov/data/map/dr5/dfp/ilc/wmap_ilc_9yr_v5.fits).
LAMBDA describes it as a foreground-minimized estimate of CMB temperature
anisotropy and cautions that the full-sky estimate is most reliable on angular
scales larger than about 10 degrees. It is not a map of matter density or the
cosmic web.

The reproducible builder reads the original Nside=512 FITS directly; it does
not require the previously staged Nside=64 derivative. It averages each
contiguous group of 64 NESTED children into one Nside=64 parent, then samples
those values by Galactic longitude and latitude into an embedded 512x256
equirectangular JPEG. NESTED indexing and the angular-to-pixel convention follow
the [official HEALPix angular/pixel conversion reference](https://healpix.sourceforge.io/html/idl_pix2xxx_ang2xxx_vec2xxx_nes.htm);
the [HEALPix Primer](https://healpix.sourceforge.io/html/intro.htm) describes
the hierarchical ordering. The FITS validator accepts an explicit `COORDSYS=G`
or, for this WMAP product whose FITS header omits `COORDSYS`, checks the WMAP
all-sky header and relies on LAMBDA's published Galactic frame. LAMBDA also
provides [NESTED Galactic pixel-coordinate FITS maps](https://lambda.gsfc.nasa.gov/toolbox/pixelcoords.html)
for independent coordinate inspection.

The original WMAP ILC product is documented at approximately 1-degree
resolution. Its Nside=64 child averaging is an additional low-resolution
display derivative, not a claim that the source beam/PSF changed to a known
new value. LAMBDA cautions that its full-sky ILC estimate is most reliable on
scales larger than about 10 degrees. The color stretch is linear and saturates
outside +/-0.25 mK; those assigned sRGB colors are not literal microwave
colors. The builder records the hash of the original FITS, original and target
Nside, averaging factor, and texture hash in `entry.json`. The resulting GLB has
no external image or decoder dependency.

Credit: NASA/WMAP Science Team; data hosted by NASA LAMBDA. NASA scientific
data are generally public-domain, subject to exceptions for third-party works.
See [NASA media usage guidance](https://www.nasa.gov/nasa-brand-center/images-and-media/).
NASA is credited, not represented as endorsing this authored diagram. The
texture derivative and geometry are not NASA-authored products.

## Meaning and scale

This is a rotatable causal-horizon **diagram**, not a literal universe wall.
The textured shell marks the approximate present-distance CMB last-scattering
sphere at 45.6 billion light-years radius. The larger three-circle wire guide
marks an approximate particle-horizon radius of 46.5 billion light-years.
Their ratio is preserved (46.5/45.6); the small gap is not exaggerated. NASA's
WMAP materials explain that the present horizon distance is close to 45 billion
light-years and show the CMB at about 45.6 billion light-years, while NASA
estimates the observable universe at roughly 92 billion light-years across:

- [WMAP glossary: horizon distance](https://wmap.gsfc.nasa.gov/site/glossary.html)
- [WMAP Inflatable Universe: CMB distance versus lookback time](https://wmap.gsfc.nasa.gov/resources/edactivity1LD.html)
- [NASA expert: observable universe about 92 billion light-years across](https://www.nasa.gov/science-research/astrophysics/how-big-is-space-we-asked-a-nasa-expert-episode-61/)
- [NASA WMAP overview: CMB emitted about 375,000 years after the Big Bang](https://science.nasa.gov/mission/wmap/wmap-overview/)

The listing's approximate 8.8e26 m diameter (about 93 billion light-years) is
consistent with that scale. The CMB emission epoch is about 13.8 billion years
of lookback time, not a 13.8-billion-light-year present distance; expansion
accounts for the larger present-distance radius.

A 30-degree cone centered on the observer-facing +Z direction is omitted from
the CMB shell to expose the observer at the origin. This is a viewing cutaway,
not a physical hole or edge. Its smooth amber rim marks the authored cut, not
an observed boundary. The opening uses a +Z-polar mesh; UVs are reprojected into
Galactic longitude/latitude and locally unwrapped across the longitude seam.
Back-face culling makes the diagram opening legible instead of filling it with
the shell's far-side image. The great circles are geometric guides for the
particle-horizon radius, not observed material. Neither surface is a wall or
the boundary of the entire universe.

Rebuild with:

```sh
python3 scripts/build_observable_universe_model.py \
  --fits /private/tmp/us-next-models/wmap_ilc_9yr_v5.fits \
  --output-dir /private/tmp/observable-universe-model
```

To stage the original input again, download `wmap_ilc_9yr_v5.fits` from the
direct NASA LAMBDA URL above before running the command.
