# Direct public catalogs: deepsky3d

Offline conversion: `scripts/build_deepsky3d_models.py`. Source refresh:
`scripts/prepare_deepsky3d_sources.py` and `scripts/prepare_deepsky3d_dust.py`.
The adjacent `deepsky3d/manifest.json`
records complete query URLs, selections, original input SHA-256, compact snapshot
SHA-256, columns and row counts. Numeric records are retained in deterministic
gzip files. Source IDs stay decimal strings, avoiding 64-bit identity loss.
The dust cube is a compact NPZ, with the original FITS mean-grid header's numeric
WCS fields and SHA-256 per acquired byte range; no whole-file SHA-256 is claimed
for that partially downloaded 15.66-GB source.

Every GLB vertex is a selected catalog record. No stars, galaxies, depth scatter,
shells, glyphs, rulers, interpolation points or noise were added. Soft sprites are
the existing renderer's display convention, not measured stellar/galaxy radii.
All coordinates remain in physical units. Calibration divides by the item value
in those units; the bounding box is never stretched to the listed value.

## Sources and reuse

- **Gaia DR3**: ESA/Gaia/DPAC. The [official credit instructions](https://gea.esac.esa.int/archive/documentation/GDR3/Miscellaneous/sec_credit_and_citation_instructions/)
  explicitly permit free use with credit (final paragraph). This is the Gaia
  open-data permission, not an invented CC license. Mission/release citations:
  [Gaia Collaboration 2016](https://doi.org/10.1051/0004-6361/201629272) and
  [Gaia Collaboration 2023](https://doi.org/10.1051/0004-6361/202243940).
- **Omega membership catalog**: Eugene Vasiliev and Holger Baumgardt,
  [Zenodo 4891252, version 2](https://zenodo.org/records/4891252),
  [Gaia EDR3 view on Galactic globular clusters](https://arxiv.org/abs/2102.09568).
  The record API explicitly identifies `cc-by-4.0`. Numeric data are extracted
  from `clusters.zip/catalogues/NGC_5139_oCen.txt` (not the separate radial-profile
  file with the same basename). ESA/Gaia/DPAC credit also applies.
- **2MRS**: Huchra et al. 2012, ApJS 199, 26,
  [publication](https://doi.org/10.1088/0067-0049/199/2/26),
  [CfA public data announcement](https://lweb.cfa.harvard.edu/~dfabricant/huchra/2mass/),
  [table at CDS](https://cdsarc.cds.unistra.fr/viz-bin/cat/J/ApJS/199/26).
  The producer describes the completed survey as public. Used as a public
  scientific catalog with citation, consistent with the existing Laniakea and
  Virgo models and this job's explicit permission to reuse 2MRS. No CC0 or CC BY
  license is asserted for this catalog. [CDS terms](https://cds.unistra.fr/vizier-org/licences_vizier.html)
  defer commercial permissions to data origin; the CfA announcement is a public
  release, not a separate explicit commercial redistribution grant. This limit
  remains visible here for the lead's review.
- **SDSS DR17 / BOSS**: [release documentation](https://www.sdss4.org/dr17/).
  [SDSS policy](https://www.sdss.org/collaboration/image-use-policy/) explicitly
  places public-release data in the public domain. Credit: Sloan Digital Sky
  Survey / Baryon Oscillation Spectroscopic Survey. Survey citations:
  [Abdurro'uf et al. 2022](https://doi.org/10.3847/1538-4365/ac4414),
  [Dawson et al. 2013](https://doi.org/10.1088/0004-6256/145/1/10).
- **Local 3D dust**: Edenhofer, Zucker, Frank, Saydjari, Speagle, Finkbeiner and
  Ensslin, [Zenodo 8187943](https://zenodo.org/records/8187943), explicitly
  `cc-by-4.0` in the record API; [paper](https://arxiv.org/abs/2308.01295).
  The source ReadMe makes all data products public and documents the Cartesian
  mean grid as an interpolation at 2-pc voxel spacing of their inferred dust map.

The small GLB encoding and conversion code do not change the underlying data's
terms. Brightness is compressed; palettes are display mappings. Observed BP-RP
orders the stellar colors, while galaxy colors are either neutral or encode
redshift. None is a calibrated full-spectrum RGB reconstruction.

## Large Magellanic Cloud

`lmc-gaia-disk`: 23,420 records selected from 26,510 Gaia query results.
The full ADQL is pinned in the manifest. A 7-degree cone centered at
RA=81.28, Dec=-69.78 degrees uses G<19.5, finite BP-RP, proper motion
0.8<pmra<2.9 and -0.7<pmdec<1.4 mas/yr, and -0.2<parallax<0.2 mas.
The inclusive `random_index` range 0..10,000,000 provides a catalog-defined
spatial sample. These are broad **candidate** cuts, not a claim of definitive
membership. Small residual Galactic contamination and spatial incompleteness
remain; the query is not the Gaia Collaboration's complete member selection.

The measured positions define sightlines. Each intersects a zero-thickness disk
with inclination 34.7 degrees and line-of-nodes PA=122.5 degrees east of north,
with the northeastern side nearer, from
[van der Marel & Cioni 2001](https://arxiv.org/abs/astro-ph/0105339).
The distance is 49.59 kpc from
[Pietrzynski et al. 2019](https://arxiv.org/abs/1903.08096).
The center follows [Gaia Collaboration 2021](https://arxiv.org/abs/2012.01771).
Combining these published ensemble estimates is a plane approximation, not
individual stellar distance measurements. Real disk warping, thickness and
population-dependent orientation are not reconstructed.

The radial aperture is half the existing 3.042478095350488e20-m item value
(9.86 kpc diameter). This is a declared extraction window, not a measured outer
edge. Native extent is 9.319 by 8.638 by 5.601 kpc. Native axes are west, north,
toward the observer. Resting projected extent is approximately 0.945 of the item
value. The bar and density variations are the catalog's measured sky positions.

## Orion Arm

`orion-arm-edenhofer-dust`: 15,707 selected **grid samples**, not stars or
individual clouds, from Edenhofer et al.'s public three-dimensional mean
extinction-density reconstruction. This is a local window within the Orion/Local
Arm, not an extraction of the entire arm or a new measurement of its width.

The original `mean_and_std_xyz.fits` MEAN image has 1,251 samples per axis,
2-pc spacing, CRPIX=1 and CRVAL=-1,250 pc on all three axes, in heliocentric
Galactic X/Y/Z. The preparation command checks these header fields and requests
68 strips by HTTP byte range, indexing 357..893 inclusive with stride 8 on every
axis. The 68-cubed pinned grid has centers from -536 through +536 pc in 16-pc
steps. Values are sampled directly, without new interpolation, noise or depth.

The extraction covers 1,072 pc (~3,496 light-years) along each axis, closely
matching the existing 3,500-light-year scale. Rest is a view down Galactic Z
(X horizontal, Y up). A quarter turn exposes the vertical distribution. All
coordinates retain pc units; the physical item value supplies reference_size.

The display selects finite values at or above the cube's 95th percentile,
0.000383948775 in the source map's extinction-density units. It retains the
original 304 unavailable samples as NaN in the pinned grid; they are omitted,
not replaced with zero. The resulting 15,707 coordinates are unmodified voxel
centers, with log-density false colors and low-opacity soft sprites. Their
sprite widths are a display kernel, not measured cloud diameters. Below-threshold
or unavailable regions must not be interpreted as empty space. Extinction density
is not gas emission or an optical view of glowing nebulae.

The original grid itself is a statistical inference using stellar information,
not an exact tomography of every cloud. The conversion adds no reconstruction
assumptions beyond the explicitly stated sampling, density threshold and window.

## Omega Centauri

`omega-centauri-gaia-members`: 7,313 actual stars, membership probability >0.99,
finite BP-RP and G<16. A faint-star version produced a spurious central hole
from crowding, so the final display uses a brighter, more complete population.
No missing core stars are synthesized. The catalog quality flags are preserved
but not used to exclude sky positions: those flags reject most central faint
stars and would worsen the density bias. Membership remains a probabilistic
astrometric estimate, including for stars without the catalog's quality bit.

Distance 5.43 kpc, center RA=201.69699, Dec=-47.47947 degrees, from
[Baumgardt's structural parameter table](https://people.smp.uq.edu.au/HolgerBaumgardt/globular/parameter.html),
which attributes most distances to Baumgardt & Vasiliev (2021).
Directions are projected gnomonically onto a common-distance plane. Uncertain
individual parallaxes are **not** inverted. Depth is exactly zero, deliberately
exposed by rotation; a spherical depth distribution would be invented.

An aperture of 75 light-years radius follows the existing 150-light-year marker;
the source includes members farther out. Native extent is approximately 45.43 by
45.88 pc, 0.998 of the marker. The bright-member sample is neither all cluster
stars nor its full tidal diameter. Colors use actual BP-RP, and G sets brightness.

## Local Void

`local-void-2mrs-slice`: 471 actual 2MRS galaxies. The pinned table has 43,533
numeric rows with a redshift. Catalog row numbers plus original RA/Dec preserve
identity; the requested 2MASX column was not returned by CDS and is not invented.
Positive cz is converted to cz/75 Mpc, using the distance convention of
[Tully et al. 2019](https://arxiv.org/abs/1905.08329).
The existing Laniakea builder supplies the established Galactic-to-supergalactic
rotation. This is redshift space, not a peculiar-velocity reconstruction.

Extraction bounds: SGX=-11..49, SGZ=-15..45, SGY=-16..4 Mpc. These contain
the paper's Aquila (-3,-3,+9), Lacerta (+22,-9,+22) and Andromeda
(+28,-9,-4) Mpc density minima. The 60 by 60 by 20 Mpc window is an authored
**selection**, not authored point geometry or a void boundary. The coordinates
are untouched apart from a rigid translation and axis mapping. No points were
removed based on desired emptiness. Projection is SGX horizontal and SGZ up;
SGY is depth. Native projected width is 59.962 Mpc (~0.999 of the 60-Mpc marker).

Near-infrared magnitude limits, Galactic obscuration and peculiar velocities
complicate the apparent emptiness. In particular, an unobserved region is not
proof of a void. This sample is shown with the same catalog limitations as the
existing local large-scale models; it does not reproduce the paper's density field.

## Bootes Void

`bootes-void-sdss-slice`: 1,343 actual SDSS DR17 primary galaxy spectra with
zWarning=0, from the 31,614-row query snapshot. The selection is a 150 by 150 by
40 Mpc observer-facing slice around cz=15,500 km/s and the center published by
[Kirshner et al. 1987](https://articles.adsabs.harvard.edu/pdf/1987ApJ...314..493K).
The paper's B1950 RA=14h50m, Dec=+46 degrees is converted to ICRS
RA=222.9458392059863, Dec=45.795532678784106 degrees using Astropy FK4.

**The source's 62-Mpc radius assumes H0=50 km/s/Mpc**, stated in section III.
The conversion therefore retains cz/50; using H0=70 would imply ~89 Mpc for
the diameter, rather than the current item's 124 Mpc. This is a historical
distance convention, explicitly disclosed. No dataset was edited.
The displayed 150-Mpc square includes surrounding context and is ~1.209 of the
listed diameter. The 40-Mpc depth cut makes the underdensity legible without
removing individual galaxies or fabricating a spherical empty interior.

The center is visible as a deficit in this slice, not a literal black object.
There are no boundary meshes or background stars. Colors encode redshift over
the query's range. The model does not assert a uniform completeness correction.

## Baryon acoustic oscillation scale

`bao-boss-galaxy-slice`: 141 actual BOSS primary galaxy spectra with zWarning=0
from the 6,432-row SDSS query. The observer-facing section measures 150 by 150 by
40 comoving Mpc, centered at RA=180, Dec=20 degrees and z=0.475. The extraction
position is a declared sample window, not a special BAO site. Comoving radial
distance integrates flat LCDM with H0=70 km/s/Mpc, Omega_m=0.27,
Omega_Lambda=0.73, also used by the
[Giant Arc paper](https://arxiv.org/abs/2201.06875).
Native projected extent is 148.864 Mpc (~0.992 of the 150-Mpc marker).

BAO is a statistical excess in galaxy pair separations, not a visible single
shell or a structure boundary. This small patch illustrates the physical scale
with actual positions; it cannot independently measure or visually demonstrate
the BAO correlation. The larger data/statistical result is described by
[Eisenstein et al. 2005](https://arxiv.org/abs/astro-ph/0501171).
Colors encode catalog redshift, not galaxy color.

## Review limits

The CPU previews use the actual GLB POINTS arrays and approximate soft-sprite
appearance. The loader audit uses the vendored production GLTFLoader. Neither
is a WebGL, perspective, mobile, touch-picking or actual explorer review.
Chromium and git sandbox limits were not retried, as instructed in this job.
