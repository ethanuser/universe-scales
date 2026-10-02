# Hercules-Corona Borealis GRB catalog view

## What the model shows

This is an information diagram of gamma-ray burst (GRB) observations, not a
3D model of a confirmed galaxy wall. Dots are Swift catalog events with
explicitly identified spectroscopic redshifts in the inclusive
`1.6 <= z <= 2.1` interval. Their observed directions are plotted in a
dimensionless, equal-area Mollweide sky chart in Galactic coordinates. The map
panel has no physical length or depth; it is not positioned at a comoving
distance and is not rescaled to imply a structure boundary.

Amber marks the broad Galactic quadrant highlighted as likely in Horvath et
al. (2020) Figure 1 (`0 <= l <= 180 deg`, `b >= 0 deg`); blue marks other events
in this Swift slice. This quadrant covers one quarter of the full sky. It is
not the original 2014 paper's approximately one-eighth-sky concentration cap,
and these current Swift events are not the original 2014 membership list. The
exact one-eighth cap is not encoded as a fixed boundary in this diagram. The
October 1, 2026 Swift export yields 42 selected bursts, 16 in the 2020 figure's
broad guide; that count is a catalog extraction, not a replication of either
paper's significance analysis.

A one-dimensional inset places each burst along `chi(z)`, radial comoving
distance under a flat Planck-2018 reference cosmology (`H0 = 67.4 km s^-1
Mpc^-1`, `Omega_m = 0.315`). Small vertical offsets in the strip are display
jitter only. Redshift-derived distance is model-dependent, and the bursts on
this light cone are observed at different cosmic times, not on one simultaneous
spatial slice. A literal observer-centered placement of the 42 catalog events
spans about 35.0 Gly pairwise; the full `z=2` shell is about 34.7 Gly across.
Those are properties of the plotted catalog/light cone, not an extent of the
putative concentration, and would render several times larger than the item's
claimed size. They are therefore not used as GLB geometry.

The detached 10 Gly bar is the only dimension-bearing element. It represents a
rounded literature inference (about 2,000-3,000 Mpc, roughly 6.5-9.8 Gly), not
a measured edge or mapped galaxy distribution. The complete diagram is
explicitly schematic; its sky-chart dimensions do not correspond to distance.
The bursts are sparse tracers, not a census of galaxies or matter.

The stage keeps only the angular chart, a small redshift-distance strip, and a
single `10 Gly` scale label for the reported extent. Chart title, sample count,
cosmology range, and qualifications are omitted from the model surface to
avoid overlapping prose; this detail note is the interpretation key. The sky
map remains an equal-area 2D projection embedded in the GLB, not a 3D spatial
model. No defensible simultaneous 3D structure geometry or calibration is
available from this sparse, disputed light-cone sample.

The extraction is deliberately conservative: a row is plotted only when the
NASA Swift GRB Table's redshift cell explicitly identifies an absorption,
emission, or spectroscopic measurement. Photometric values, limits, and
redshifts without a measurement-type marker are excluded. The Swift table is
live; reproducible builds use the exact October 1, 2026 TSV snapshot bundled at
`sources/catalogs/swift-grb-full-2026-10-01.tsv` beside this document. The registry
records its retrieval date and SHA-256. It is build provenance, not a runtime
download. The builder also records the input
SHA-256 and selection/cosmology parameters in `build-metadata.json` beside the
staged GLB. Swift full-view decimal RA values are degrees (for example,
132.475 deg is also shown as 08:49:54.0); explicit colon-delimited RA is parsed
as hours. UTF-8 is attempted first; legacy Latin-1 exports are supported as a
fallback.

## Claim and counter-evidence

Horvath, Hakkila & Bagoly (2014) reported that 14 of 31 GRBs in a redshift bin
`1.6 < z < 2.1` fell in roughly one eighth of the sky and interpreted the
excess as a possible structure about 2,000-3,000 Mpc across. Horvath et al.
(2015) reported a larger sample supporting the clustering. These are
statistical inferences from sparse GRB locations, not a resolved wall or galaxy
filament.

Horvath et al. (2020) Figure 1 uses a *different, broader visual guide* for
bursts that “likely belong” to the feature: Galactic `0 <= l <= 180 deg`,
`b >= 0 deg`. Its solid-angle fraction is one quarter of the sky, not one
eighth. The figure does not establish this quadrant as the original 2014 cap or
as a physical boundary; the amber points and this note identify it only as
that 2020 figure's broad guide.

Ukwatta & Wozniak (2016) argued that redshift-dependent angular clustering can
be explained by Swift exposure and Galactic extinction selection effects.
Christian (2020) found that Monte Carlo tests can reproduce the original
statistics and that an updated sample is less significant. Horvath et al.
(2020) reanalyzed a carefully curated redshift sample, defended the clustering
against those critiques, but also emphasized possible observational bias and
concluded that more homogeneous data are needed to decide whether the feature
exists. The literature is therefore disputed; neither “definitively largest”
nor “confirmed galaxy wall” is warranted.

## Data, rights, and rebuild

The event table is the NASA Swift GRB Table full-view tab-separated export,
which contains burst names, coordinates, redshifts, measurement type, and
references. The table is public-access NASA/HEASARC data; the U.S. government
catalog record identifies government works as its license. The model contains
only transformed coordinate/redshift samples, no NASA logo, third-party image,
or external runtime asset. Retain NASA/Swift attribution. The per-event
redshift references in the input table remain the provenance for measurements.

Rebuild from the bundled snapshot, writing generated output outside the
repository. A new snapshot can be obtained using the official table's export
link at <https://swift.gsfc.nasa.gov/archive/grb_table/fullview/>:

```sh
python3 scripts/build_grb_structure_model.py \
  --catalog content/visualizations/models/sources/catalogs/swift-grb-full-2026-10-01.tsv \
  --output-dir /private/tmp/length-grb
```

The script writes a self-contained GLB with no Draco, meshopt, or external
resources. It fails closed if selected redshift strings do not explicitly
identify spectroscopy or if the spectroscopic redshift slice is empty. The
2020 broad quadrant may contain zero selected events without invalidating the
all-sky angular chart.

## References

- Horvath, Hakkila & Bagoly (2014), “Possible structure in the GRB sky
  distribution at redshift two,” *Astronomy & Astrophysics* 561, L12,
  <https://doi.org/10.1051/0004-6361/201323020>.
- Horvath et al. (2015), “New data support the existence of the
  Hercules-Corona Borealis Great Wall,” *Astronomy & Astrophysics* 584, A48,
  <https://doi.org/10.1051/0004-6361/201424829>.
- Ukwatta & Wozniak (2016), “Investigation of redshift- and duration-dependent
  clustering of gamma-ray bursts,” *MNRAS* 455, 703,
  <https://doi.org/10.1093/mnras/stv2350>.
- Christian (2020), “Re-examining the evidence of the Hercules-Corona Borealis
  Great Wall,” *MNRAS* 495, 4291, <https://doi.org/10.1093/mnras/staa1448>.
- Horvath et al. (2020), “The clustering of gamma-ray bursts in the
  Hercules-Corona Borealis Great Wall: the largest structure in the Universe?,”
  *MNRAS* 498, 2544, <https://doi.org/10.1093/mnras/staa2460>.
- NASA Swift GRB Table and field definitions:
  <https://swift.gsfc.nasa.gov/archive/grb_table/fullview/> and
  <https://swift.gsfc.nasa.gov/archive/grb_table/swgrbtable_help.html>.
- NASA Open Data catalog record for the Swift GRB Catalog, public access and
  government-works license: <https://catalog.data.gov/dataset/swift-gamma-ray-bursts-catalog>.

## Dataset definition

The former `1e25 m` value was about 1.06 billion light-years, not 10 billion.
The Length dataset now uses `9.4607304725808e25 m` (10 Gly) as a rounded reported
extent, with a disputed-structure quality flag and explicit qualifiers. This
conversion precision is not measurement precision. The explorer's display title
is “Putative Hercules-Corona Borealis structure”; the existing exact item name
is retained for selection and deep links. No confirmed wall geometry or
billions-of-galaxies population is asserted. The builder itself does not edit
the dataset or registry.
