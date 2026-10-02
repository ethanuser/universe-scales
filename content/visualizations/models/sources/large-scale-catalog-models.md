# Large-Scale Catalog Window Diagrams

These are compact diagrams of public SDSS DR17 spectroscopic catalog rows. A
point is an observed galaxy position; it is not an assertion that the galaxy
belongs to the named structure. The wireframes show the cuts used to select the
displayed rows. They are not measured structure boundaries. Positions are
converted to comoving Cartesian coordinates and shifted by one common origin;
the shift changes neither distances nor shape. Galaxy markers are enlarged point
symbols, not galaxy diameters.

The stage is intentionally quiet: a faint open selection-window guide and
catalog points, with no floating explanatory label. The guide remains a
selection aid only; membership and definition caveats belong in the detail
text, not as a purported structural outline.

## Data source and reuse

The underlying measurements are `SpecObj` rows from [SDSS Data Release 17](https://www.sdss4.org/dr17/), downloaded as CSV from the official [SDSS DR17 SQL service](https://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch). The query requires `sciencePrimary=1` and conditionally selects classification, redshift, and warning fields: `CLASS_NOQSO`, `Z_NOQSO`, and `ZWARNING_NOQSO` for `survey` in `boss`/`eboss`; otherwise the legacy `CLASS`, `Z`, and `ZWARNING` fields. It retains right ascension, declination, effective spectroscopic redshift, and `specObjID`. This follows the [official DR17 optical spectra guidance](https://www.sdss4.org/dr17/spectro/catalogs/), which identifies the no-QSO fields as preferable for BOSS/eBOSS galaxy targets and recommends `sciencePrimary` for unique spectra. SDSS says public-release data are public domain. The project's selection, coordinate transforms, point styling, and GLB assembly are authored derivatives. Cite the DR17 data-release paper, Abdurro'uf et al. 2022, [ApJS 259, 35](https://doi.org/10.3847/1538-4365/ac4414), as well as the structure-specific paper below. [SDSS data-use and credit policy](https://www.sdss.org/collaboration/image-use-policy/).

The GLB coordinates are in comoving Mpc. Registry `reference_size` is the
Length item's characteristic value converted to those native units (30.66 Mpc
for Virgo; 450 Mpc for Sloan), not the survey-window bounding-box extent. This
keeps runtime calibration tied to the named quantity; window dimensions remain
available in the staged processing metadata. Both entries use
`representation: catalog_diagram` and
`volume_semantics: not_a_volume_measurement`.
The staged presentation pose rotates the Sloan long axis into the horizontal
view before calibration, then tilts the slice obliquely; the Virgo view uses a
small pitch/yaw. These are camera-facing model rotations, not geometric
stretching. The position data remain actual 3D comoving catalog coordinates;
only the selection window is an authored visual guide.

The exact source CSV snapshots are `content/visualizations/models/sources/catalogs/sdss-dr17-virgo-window.csv` and `sdss-dr17-sloan-window.csv`. They are public-domain SDSS DR17 data; the [SDSS data-use policy](https://www.sdss.org/collaboration/image-use-policy/) requests appropriate scientific attribution, supplied above. CSVs are build provenance only, not runtime dependencies. Each staged entry records the repository-relative snapshot path, SHA-256, catalog query, release, and selection count.

## Virgo Supercluster / Local Supercluster

The Length value should represent the historical Virgo/Local Supercluster, not
the larger Laniakea basin. Tully's primary analysis describes a non-spherical
system with a Virgo core, an irregular flattened disk and a halo of discrete
clouds; the disk has approximate axial ratios 6:3:1. It does not define a sharp
enclosing surface ([Tully 1982, *The Local Supercluster*, ApJ 257, 389](https://doi.org/10.1086/159999)). NASA's educational account gives a rough overall diameter of 100 million light-years and describes the Local Group as near one edge ([NASA GSFC](https://imagine.gsfc.nasa.gov/features/cosmic/local_supercluster_info.html)).

**Selection:** SDSS DR17 galaxies with `175 <= RA <= 200` degrees, `-5 <= Dec <= 25` degrees, and `0 <= z <= 0.008`, after the common quality cuts above. This is a deliberately explicit SDSS sky/redshift window centered broadly on the Virgo direction, not a published membership list, a complete all-sky census, or a proposed Virgo boundary. The finite lower redshift cut and SDSS footprint omit nearby systems and galaxies outside the survey. The window limit is a selection choice, not inferred membership.

**Distance basis and limitations:** redshift is mapped to comoving distance with the stated flat-LCDM integral and `H0=71 km s^-1 Mpc^-1`, `Omega_m=0.27`, and `Omega_Lambda=0.73`. These are the cosmological parameters used by Gott et al. for the companion Sloan diagram; at Virgo's low redshift, peculiar velocities are important, and this visualization makes no flow correction. The angular and redshift cuts should be read as a sampled region around the Local Supercluster, not a 3D reconstruction of its disk or halo.

**Dataset definition:** the Length dataset uses `9.46e23 m` (about 100 million light-years, three significant figures), replacing the former `1e23 m` (about 10.6 million light-years). This rounds NASA's roughly 100-million-light-year characteristic diameter and carries an approximate-span qualifier, not a precise boundary measurement. The builder itself does not edit dataset files.

## Sloan Great Wall

**Selection:** SDSS DR17 galaxies with `8.7 h <= RA <= 14 h` (130.5-210 degrees), `-2 <= Dec <= 2` degrees, and a comoving radial distance from 215 to 370 Mpc, after the common quality cuts above. The published angular slice, distance range, and its WMAP-era cosmology follow Gott et al. ([2005, *A Map of the Universe*, ApJ 624, 463](https://doi.org/10.1086/428890); [full text](https://arxiv.org/html/astro-ph/0310571v2)). Their source describes a 4-degree equatorial SDSS slice; the 215-370 Mpc interval is a plotting window, not exact membership bounds. We convert those distance limits to redshift by inverting the flat-LCDM comoving-distance integral. The queried DR17 catalog is a later release than the DR data plotted in that paper, so the result is a modern catalog sample through the same published geometric window, not a reproduction of its original member list.

Gott et al. estimate the Great Wall's total curved length as about **450 Mpc comoving** at the present epoch, or about 419 Mpc / 1.365 billion light-years at the observed epoch (`z=0.073`). Thus 450 Mpc is about 1.47 billion light-years, not 450 million light-years. This model and the Length dataset use the present-epoch comoving definition, `1.3885549116711151e25 m` (450 Mpc), replacing the materially low `4e24 m`. The digits specify a unit conversion, not measurement precision. Later morphology/percolation analyses resolve the apparent wall into connected sub-superclusters at density thresholds, emphasizing that its identification depends on the adopted method. No artificial connecting web or hard-edged wall volume is drawn.

**Distance basis and limitations:** the same flat-LCDM parameters used by Gott et al. (`H0=71 km s^-1 Mpc^-1`, `Omega_m=0.27`, `Omega_Lambda=0.73`). Spectroscopic redshifts are used as radial coordinates without peculiar-velocity corrections. A translucent open wireframe marks the published angular/radial sample window only. The displayed points are all quality-selected SDSS galaxies within it; no point-level SGW membership is claimed.

## Rebuild

From the repository root, with network access to the public SDSS endpoint:

```sh
python3 scripts/build_large_scale_catalog_models.py --output-dir /private/tmp/length-catalogs
```

To rebuild offline from bundled CSV snapshots, pass
`--catalog-dir content/visualizations/models/sources/catalogs`; missing snapshots
in this mode fail instead of falling back to a network query. Use `--refresh`
without `--catalog-dir` to fetch the source CSVs again. Generated GLBs are self-contained
glTF 2.0 with no external resources or decoder extensions; the builder rejects
assets larger than 1.5 MB. The output directory contains the downloaded catalog
CSVs, two GLBs, per-model entry JSON files, and `entries.json`. No shared model
registry, dataset, or version hash is modified.
