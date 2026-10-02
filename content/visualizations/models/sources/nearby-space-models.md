# Nearby Space Model References

These are authored diagrams, not downloaded meshes. The runtime definitions
and presentation assumptions are in `js/experiences/nearby-space-models.js`.

## Proxima Centauri Distance

[Lauer et al. (2025), A Demonstration of Interstellar Navigation Using New
Horizons](https://doi.org/10.3847/1538-3881/addabe), AJ 170, 22, Table 1, reports
Proxima at 1.301971(85) pc, the reciprocal of its Gaia DR3 parallax. At
3.0856775814913673e16 m per parsec, this is 4.01746e16 m or 4.24646 light-years.
The dataset's 4e16 m is a rounded approximation. The distance is calibrated,
but the Sun and Proxima markers are enlarged to 0.8% and 0.6% of the separation.
The bracket is center-to-center, not surface-to-surface.

## Local Group

[McConnachie (2012), The Observed Properties of Dwarf Galaxies in and around
the Local Group](https://doi.org/10.1088/0004-6256/144/1/4), AJ 144, 4, and the
[author's updated catalog listing](https://www2.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/community/nearby/)
provide sky positions and distance moduli. The Jan-2021 FITS was reviewed from
[this scientific mirror](https://users.flatironinstitute.org/~apricewhelan/data/surveys/misc/NearbyGalaxies_Jan2021_PUBLIC.fits)
because the original download host returned HTTP 403. Its SHA-256 is
`ae26374f5176ffe8822dd1dbe7eb055b5b240623082c0bf45ec8f95d3421af43`.

Catalog distance modulus is converted by `d_pc = 10^((mu + 5)/5)`. J2000 right
ascension and declination are converted to a Cartesian frame with +Y north,
+X toward RA 0, and +Z toward RA 90 degrees. Galaxy distances are rounded to
kpc. WLM and NGC 6822 use 933 and 459 kpc from the updated catalog; M31 uses
783 kpc from the paper's Table 2. The Milky Way is placed at the observer origin,
neglecting the Sun's small galactocentric offset at the scale of the group.

The 16 members are a representative subset, not an exhaustive membership list.
The three great circles indicate the dataset's approximate 1e23 m span; there
is no measured spherical edge. Galaxy radii now share the distance scale, with
no eightfold enlargement. The Milky Way uses the same radius and stellar-cloud
generator as Galaxy Diameter; M31 uses the Andromeda scene's generator. Their
spirals, dwarf shapes, disk orientations, colors, and synthetic stars are
illustrative, not a structural reconstruction. Small galaxies can legitimately
be subpixel at the group scale; fixed leader labels locate the main anchors
without increasing their physical diameters.
Only the Milky Way, M31, M33, LMC and SMC are labeled on stage to keep the
central catalog members legible; all 16 positions remain plotted.

Factual catalog measurements are credited above; authored visualization code
remains under the project code license.
