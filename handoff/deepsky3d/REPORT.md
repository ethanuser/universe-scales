# deepsky3d handoff, 2026-10-18

Six new Length assets are registered, entirely from public measured catalogs or
the published 3D dust grid. All source positions retain physical coordinates;
none is normalized to its bounding box. There are no invented stars, galaxy
positions, depth scatter, primitive bodies, rulers, schematic glyphs or shells.
No previously modeled item was redone. No dataset, exports, images, runtime JS,
CSS or HTML was edited. Changes are **uncommitted**, as instructed for this
sandbox; git writes and Chromium were not retried.

## Delivered models

| Item | Final id / entry | Actual records | GLB bytes | Orthographic rest / item |
| --- | --- | ---: | ---: | ---: |
| Large Magellanic Cloud | [lmc-gaia-disk](lmc-gaia-disk.entry.json) | 23,420 Gaia candidate stars | 375,876 | 0.945 |
| Omega Centauri | [omega-centauri-gaia-members](omega-centauri-gaia-members.entry.json) | 7,313 bright Gaia members | 118,176 | 0.998 |
| Orion Arm | [orion-arm-edenhofer-dust](orion-arm-edenhofer-dust.entry.json) | 15,707 real dust-grid samples | 252,412 | 0.999 |
| Local Void | [local-void-2mrs-slice](local-void-2mrs-slice.entry.json) | 471 2MRS galaxies | 8,708 | 0.999 |
| Bootes Void | [bootes-void-sdss-slice](bootes-void-sdss-slice.entry.json) | 1,343 SDSS galaxies | 22,664 | 1.209 |
| Baryon Acoustic Oscillation Scale | [bao-boss-galaxy-slice](bao-boss-galaxy-slice.entry.json) | 141 BOSS galaxies | 3,424 | 0.992 |

Total runtime payload: **781,260 bytes** for 48,395 source records. Every asset
is one self-contained POINTS primitive, one draw call, zero triangles, zero lines,
and needs no decoder. Each final entry JSON is copied here, with recomputed
hashes/statistics. These are additions, so none has a `replaces` field.

Full source citations, permissions, cuts, coordinates and limitations:
[shared source notes](../../content/visualizations/models/sources/deepsky3d-models.md).
Each id also has its own `sources/<id>.md`. Pinned numeric data, queries,
original-source hashes and density-grid range hashes:
[manifest](../../content/visualizations/models/sources/deepsky3d/manifest.json).
[Reuse evidence](../../content/visualizations/models/sources/deepsky3d/reuse-evidence.json)
records the inspected source permissions without storing contact details or tokens.

## Important interpretation details

- **LMC** uses measured Gaia sky positions and observed BP-RP on a published
  disk plane: inclination 34.7 degrees, position angle 122.5 degrees,
  D0=49.59 kpc. It is a plane approximation with a declared diameter aperture,
  not measured individual stellar depths, a full member catalog or a gas volume.
  Broad proper-motion/parallax cuts leave possible foreground contamination.
  A fixed catalog `random_index` interval provides the sparse spatial sample.
- **Omega Centauri** is explicitly a flat measured-distance sky map. The full
  faint Gaia member sample made a misleading central ring from crowding, so the
  final model selects G<16 and membership probability >0.99. The observed
  BP-RP colors are retained; no synthetic core fills the missing data. Rotation
  exposes the absence of individual distance measurements as an edge-on line.
- **Orion Arm** is a local window of Edenhofer et al.'s CC BY 4.0 statistical
  3D extinction-density reconstruction. The 1,072-pc cube around the Sun is
  sampled at original grid coordinates, every eighth 2-pc sample (16-pc spacing).
  Its densest 5% of finite values are displayed with low-opacity, density-colored
  sprites. The 304 unavailable cells are kept as NaN, never replaced with zero.
  It is not the entire arm or an independent measurement of its width. Only
  approximately 183 MB of exact source byte ranges were acquired, not the entire
  15.66-GB Cartesian FITS; every response is hashed in the manifest.
- **Local Void** is a real 60 by 60 by 20 Mpc galaxy section through the
  Aquila/Lacerta/Andromeda minima of Tully et al. (2019), not a fitted boundary.
  It reuses the existing Laniakea coordinate transform and its H0=75 distance
  convention. The producer calls 2MRS public, and this job explicitly authorizes
  2MRS reuse. No additional CC or commercial redistribution grant is invented;
  the exact permission distinction is retained in the source notes. Galactic
  obscuration must not be read as physical emptiness.
- **Bootes** retains the original paper's **H0=50** distance convention because
  that is the basis of the current 124-Mpc marker. A 150 by 150 by 40 Mpc section
  includes surrounding galaxies; it is not a synthetic empty sphere. The paper's
  B1950 sky center is converted to ICRS before applying it to SDSS positions.
- **BAO** is an actual 150 by 150 by 40 comoving-Mpc BOSS section at z=0.475.
  It illustrates that separation scale, **not** an identified acoustic shell.
  The BAO pair-correlation excess requires a substantially larger statistical
  sample and is not demonstrated by eye in this patch.

All caveats live in registry notes/source documents. No caveat labels, short
display-name replacements, rulers or other authored annotations are in the GLBs.

## Verification and visual review

- Node: **228 passing**. [Complete log](node-tests.log).
- Python: **149 tests run, one existing skip, no failures**. Includes nine new
  coordinate, source-identity, physical calibration, missing-data and GLB checks.
  [Complete log](python-tests.log).
- Actual vendored production GLTFLoader: all six load, exact point counts,
  one draw each, no triangles/lines, all resting geometry extents within
  0.6–1.3 times the item value. [Loader audit](loader-audit.json).
- Khronos glTF Validator: **all six new GLBs have zero errors and zero warnings**.
  The complete registry has 196 GLBs, zero errors and 1,867 unchanged pre-existing
  warnings. The original 190 validation records compare exactly equal to HEAD;
  `validation.json` only appends these six records. [Log](gltf-validator.log).
- Asset/hash check passes: **196 self-contained GLBs, 207 exact-name matches**.
  [Log](asset-check.log). Content-hash version check passes with zero stale
  references. [Log](version-check.log). No runtime files required version changes.
- `git diff --check` passes.

Viewed the CPU rest and quarter-turn preview for every model and the small views.
The Omega selection and point presentation were revised after visual inspection;
the dust sprite kernel was enlarged and its opacity reduced to make the measured
grid read as density rather than a field of stars. Coordinates were unchanged.

Previews: [overview](previews/overview.png),
[LMC](previews/lmc-gaia-disk.png),
[Omega](previews/omega-centauri-gaia-members.png),
[Orion/local dust](previews/orion-arm-edenhofer-dust.png),
[Local Void](previews/local-void-2mrs-slice.png),
[Bootes](previews/bootes-void-sdss-slice.png),
[BAO](previews/bao-boss-galaxy-slice.png).
Individual `*-small.png` files show a 120-pixel reference size.

**These are CPU soft-point approximations, not WebGL screenshots.** Chromium,
the production `model_lab audit`, actual radial explorer, perspective, hover/touch
picking, point LOD on phones and mobile review remain for the lead outside this
sandbox. None was retried or represented as passed. The orthographic loader audit
does not certify those production behaviors. In particular, verify readability
of the sparse BAO sample and the dust grid on both dark and light backgrounds.

## Skipped targets and searches

| Item | Public sources checked | Why no model was registered |
| --- | --- | --- |
| Milky Way Central Bar | [Wegg & Gerhard 2013](https://arxiv.org/abs/1308.0593), [Wegg et al. 2015](https://arxiv.org/abs/1504.01401), MPE Milky Way pages and later Portail density-model discussion | Found the star-count/density studies, but did not acquire a usable published grid covering the full approximately 10-kpc long bar. The measured inner bulge grid covers only a 4.4-kpc long central region, which must not be stretched to this item. No fitted ellipsoid or synthetic red-clump distribution was substituted. |
| Fermi Bubbles | [Fermi-LAT public bubble FITS products](https://glast4.stanford.edu/pub_data/891/FermiBubblesPublicFiles/), [2014 morphology paper](https://arxiv.org/abs/1407.7905), NASA LAT data access | The public products are angular gamma-ray intensity/templates. They do not supply spatial distances per emitting voxel; turning them into a pair of three-dimensional lobes would invent the geometry. |
| Magellanic Stream | [HI4PI release paper](https://arxiv.org/abs/1610.06175), [Bonn HI/GASS survey server](https://www.astro.uni-bonn.de/hisurvey/) | HI position-position-velocity cubes do not provide distances along this extragalactic stream. Velocity is not a spatial axis; placing it on an assumed 55-kpc shell or extruding it would impose geometry absent from the data. |
| Andromeda Gas Halo | [Project AMIGA](https://arxiv.org/abs/2002.07818), its 43 background-quasar absorption measurements and later AMIGA work | Sparse integrated sightlines do not determine a volumetric halo boundary. No public measured 3D halo product was acquired; no sphere or filled halo was authored. |
| M87 Jet | [NASA's optical jet image/measurement](https://science.nasa.gov/asset/hubble/galaxy-m87-jet-annotated/), VLA/MOJAVE radio-data searches and the recent Chandra product | Did not acquire a suitable openly reusable, WCS-calibrated radio product spanning this item's visible-jet length. The optical photograph was not converted into invented depth, and parsec-scale VLBI data were not mislabeled as the full jet. |
| IC 1101 | [2026 ultra-deep imaging study](https://arxiv.org/abs/2607.15340), including its full HTML | The reported edge is based on two-dimensional surface-brightness and stellar-density profiles. No public volumetric stellar geometry was found; a profile-fitted sphere/ellipsoid would violate the rule. |
| Porphyrion | [Discovery paper](https://www.nature.com/articles/s41586-024-07879-y), its publicly downloadable author PDF, [LoTSS DR2](https://lofar-surveys.org/dr2_release.html), ASTRON mosaic service, Code Ocean capsule 3908804 | Author-specific radio data were not acquired: the public Code Ocean interface returned 403; the preprint offers those data on request. The inspected general ASTRON LoTSS DR2 service explicitly says CC BY-SA 3.0, outside this brief's allowed CC BY/CC0 licenses. No radio-image depth or schematic jets were invented. Also found the dataset-definition correction below. |
| Distance to the Virgo Cluster | Existing modeled Virgo/Local Supercluster catalogs and [Tully's local structure study](https://arxiv.org/abs/1905.08329) | This item is an observer-to-cluster distance, not the cluster's size. A galaxy distribution scaled to 16.5 Mpc or a pair of marker bodies/ruler would be a forbidden distance diagram or misleading geometry. Existing Virgo models were left alone. |
| Putative Giant Arc | [Lopez et al. 2022](https://arxiv.org/abs/2201.06875), [Zhu & Menard's public DR7/DR12 absorber FITS catalogs](https://www.guangtunbenzhu.com/jhu-sdss-metal-absorber-catalog); downloaded both trimmed catalogs outside the repo | The underlying absorber catalog **is public**. An exploratory 95-Mpc connected-component calculation on the raw catalogs gave 46+12 candidate points in the arc field rather than the published cleaned sample's 44+11. The authors' quasar cross-matches and exact cleaned membership were not reproduced, and explicit redistribution terms for the author-derived absorber measurements were not verified. It would be misleading to register the approximate group as the published arc. No hand-picked arc or filler connections were added. This is a sourcing/selection limit of this job, not a claim that the catalog is unavailable. |
| TON 618 Event Horizon | [Shemmer et al. 2004 spectroscopy](https://arxiv.org/abs/astro-ph/0406559), horizon/shape-product searches | Spectroscopic mass estimates are not a measured 3D event-horizon product. A Schwarzschild sphere would be an authored primitive, expressly excluded here. |
| Hubble Radius | [NASA/LAMBDA expansion-rate context](https://lambda.gsfc.nasa.gov/resources/graphic_history/hubb_const.html), cosmological-scale/geometry searches | It is a cosmological derived distance scale. No measured 3D surface product was found; a sphere or ruler would be a forbidden scale diagram. |
| JADES-GS-z14-0 | [JADES data releases](https://jades-survey.github.io/scientists/data.html), [MAST/JADES public archive](https://registry.opendata.aws/mast-jades/), JWST and ALMA spectroscopy studies | Imaging/spectral and redshift products exist, but no genuine 3D geometry for the galaxy or the observer-to-galaxy distance marker was acquired. No primitive galaxy or distance diagram was substituted. |
| Dinkinesh | [Lucy shape paper](https://arxiv.org/html/2406.19337v1), [PDS Lucy landing page](https://pds-smallbodies.astro.umd.edu/data_sb/missions/lucy/index.shtml), PDS search and DLR shape-model abstract | The paper promises a PDS digital shape model, but the currently retrieved landing page lists instrument products without a shape product. PDS query `Dinkinesh AND (shape OR dsk)` returned zero records. NAIF endpoints also encountered TLS-chain failures. No usable authoritative mesh was obtained. This does not establish that no release exists elsewhere; no asteroid shape was invented. |

Also inspected the scientist-authored CC BY Local Void Sketchfab model
`78885b3d303d4b6e99cfe099b43929fb`, API license slug `by`, and staged it outside
the repo. It contains multiple void isosurfaces, direction arrows and minima
markers. It was not registered or bundled: the requested galaxy-position section
was available, and that avoids treating a much wider multi-void surface model as
the listed 60-Mpc quantity. No other worktree or branch was touched.

## Dataset text corrections for the items job

No numeric changes are required by these six additions. Two source-based wording
corrections should accompany integration; this job did **not** edit the dataset.

1. **Bootes Void**: retain value `3.8262402010492955e24` m only if its historical
   convention stays explicit. Suggested replacement for the first sentence:

   > The Bootes Void has a historical diameter estimate of about 124 megaparsecs
   > using a radius of 62 megaparsecs and H0 = 50 km/s/Mpc; the same redshift span
   > corresponds to about 89 megaparsecs for H0 = 70 km/s/Mpc.

   Basis: [Kirshner et al. 1987, section III](https://articles.adsabs.harvard.edu/pdf/1987ApJ...314..493K).
   Leave the rest of the current plaque intact.

2. **Porphyrion**: the current opening calls seven Mpc a projected measurement.
   The [source paper](https://arxiv.org/abs/2411.08630) gives a directly projected
   length **6.43 ± 0.05 Mpc**, with a statistically inferred total length of about
   seven Mpc. Retain current value `2.159974307043957e23` m if defining the marker
   as that approximate inferred total. Suggested replacement opening:

   > Porphyrion's two black-hole jets have an estimated total extent of about
   > seven megaparsecs, or twenty-three million light-years; their directly
   > measured projected span is about 6.43 megaparsecs.

   Leave the rest of the current plaque intact. If the owner prefers the directly
   measured projected quantity instead, change the value to `6.43 * 3.0856775814913673e22`
   m and its opening text consistently; do not call seven Mpc the measured projection.

## Rebuild and integrate

Offline, with no added Python dependencies:

```sh
./venv/bin/python scripts/build_deepsky3d_models.py
./venv/bin/python scripts/preview_deepsky3d_cpu.py
node scripts/audit_deepsky3d_models.mjs
```

Refresh catalog sources only when intentionally updating the pinned selections:

```sh
./venv/bin/python scripts/prepare_deepsky3d_sources.py --cache /tmp/deepsky3d-source-cache
./venv/bin/python scripts/prepare_deepsky3d_dust.py --cache /tmp/deepsky3d-dust-cache
```

The preparation cache is outside the repo. The Gaia range query succeeded; an
initial modulo-based query timed out and is not part of the final preparation.
Both source-preparation commands are dependency-free beyond the existing NumPy
environment. FITS parsing in the dust command is limited to checked standard
header cards and big-endian float32 image strips.

Re-register on main **after** copying the GLBs/source docs/scripts, preserving
main's registry and all other jobs' entries:

```sh
python3 scripts/register_model.py handoff/deepsky3d/lmc-gaia-disk.entry.json content/visualizations/models/lmc-gaia-disk.glb
python3 scripts/register_model.py handoff/deepsky3d/omega-centauri-gaia-members.entry.json content/visualizations/models/omega-centauri-gaia-members.glb
python3 scripts/register_model.py handoff/deepsky3d/orion-arm-edenhofer-dust.entry.json content/visualizations/models/orion-arm-edenhofer-dust.glb
python3 scripts/register_model.py handoff/deepsky3d/local-void-2mrs-slice.entry.json content/visualizations/models/local-void-2mrs-slice.glb
python3 scripts/register_model.py handoff/deepsky3d/bootes-void-sdss-slice.entry.json content/visualizations/models/bootes-void-sdss-slice.glb
python3 scripts/register_model.py handoff/deepsky3d/bao-boss-galaxy-slice.entry.json content/visualizations/models/bao-boss-galaxy-slice.glb
```

Lead browser review should run the production audit and rest/side/explorer
screenshots for all six exact names, plus mobile. Example:

```sh
node scripts/model_lab.cjs shot /tmp/deepsky3d "Large Magellanic Cloud" --views rest,side --bg dark
node scripts/model_lab.cjs shot /tmp/deepsky3d "Orion Arm" --views rest,side --bg dark
node scripts/model_lab.cjs explorer /tmp/deepsky3d "Bootes Void"
node scripts/model_lab.cjs audit
node scripts/model_lab.cjs mobile /tmp/deepsky3d-mobile
```

No packages were installed in the shared venv. Research-only packages were placed
under `/tmp/deepsky3d-python`: astropy 8.0.2, astropy-iers-data
0.2026.10.19.0.52.1, pyerfa 2.0.1.5, pypdf 6.21.1, PyMuPDF 1.28.2 and
fonttools 4.67.0. They supported source FITS/PDF inspection and the B1950-to-ICRS
center conversion; none is needed for the final builders or test suite.
The validator was already present under a temporary directory and was reused.

Pre-existing `.DS_Store` changes and the untracked `venv` symlink were left alone
and must not be included in this job's commit. Suggested commit message:

```text
Add six public-data galactic and cosmological visualizations

Co-Authored-By: Codex <noreply@openai.com>
```
