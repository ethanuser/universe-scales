# Carina Nebula: VISTA sky field

Image credit: **ESO/J. Emerson/M. Irwin/J. Lewis**. Adapted from
[ESO eso1828b](https://www.eso.org/public/images/eso1828b/) under
[CC BY 4.0](https://www.eso.org/public/outreach/copyright/). No ESO endorsement
is implied. The unmodified screen-size image is a build input, not an additional
runtime download; its SHA-256 is recorded in the registry.

## Calibration

The published field is 88.49 by 71.78 arcminutes. At the approximate 7,500-light-year
distance in [NASA's account](https://science.nasa.gov/missions/hubble/hubbles-sparkling-new-view-of-the-carina-nebula/),
`2 * distance * tan(field_angle / 2)` gives 193.06 by 156.60 light-years. The image
uses Z (880 nm), J (1.25 um), and Ks (2.15 um) bands; these assigned colors are
not an optical human-eye view. Its north-up orientation is retained.

NASA gives about 300 light-years for the whole nebula. The dataset now uses
`300 * 9.4607304725808e15 = 2.83821914177424e18 m`, replacing the incorrect
`3e20 m` (over 31,000 light-years). The bracket represents this approximate
whole-region span. The smaller photographed field is never stretched to fill it.

## Interpretation

The observed image is mapped onto a gently bowed, feather-edged sheet, including
foreground/background stars. Its embedded JPEG is at most 1024 pixels wide.
The bow is a presentation cue, not recovered depth: this is explicitly a 2.5D
illustration, not a gas-density volume or catalog of member stars. It preserves
the photograph's filaments and dark lanes better than a sparse point cloud.
The bracket is a context cue, not a physical edge. No unseen structures are
invented outside the photograph.

Reproduce with `scripts/build_carina_model.py --reference-image eso1828b.jpg`.
