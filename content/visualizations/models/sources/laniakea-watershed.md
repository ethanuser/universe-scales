# Laniakea CF4 Watershed Isosurface (Staged)

## Data and scientific interpretation

This staged mesh is derived from `CF4_new_128-z008_BoA.fits` in the
author-provided Cosmicflows watershed archive. It uses the ungrouped CF4
`BoA` reconstruction and selects voxel label `1` (Laniakea), which contains
4,079 cells in the supplied 128 x 128 x 128 grid. The grouped reconstruction
does not isolate Laniakea; it merges it into Shapley.

The [Cosmicflows data page](https://projets.ip2i.in2p3.fr/cosmicflows/) says
users of the data should cite the paper above. The corresponding reference is
Dupuy & Courtois (2023), “Dynamic cosmography of the local Universe: Laniakea
and five more watershed superclusters,” *Astronomy & Astrophysics* 678, A176,
[doi:10.1051/0004-6361/202346802](https://doi.org/10.1051/0004-6361/202346802).
The article reports an approximate segmented volume of `1.9e6 (Mpc h^-1)^3`.
The source page does not state redistribution terms for the grid; the article's
CC BY 4.0 status is not treated as a license for this separate data product.
The staged entry records that rights question as unresolved and is marked
ineligible for production registration pending confirmation.

The surface is the label-1/other-label boundary at an occupancy threshold of
0.5. It is a velocity-defined watershed from a reconstructed flow field, not
a solid mass, gravitationally bound object, galaxy catalog, or unique physical
wall. Marching cubes uses the supplied voxel membership without morphological
closing, invented streamlines, or added galaxies. Face-connected voxel
components are meshed independently so cells touching only at edges or corners
do not create non-manifold surface edges.

The FITS header provides array dimensions but no WCS. The displayed mesh is
centered, retains the native isotropic grid axes, and makes no SGX/SGY/SGZ
orientation claim. With the published 1,000 Mpc h^-1 grid width and `h=0.746`
(`H0=74.6 km s^-1 Mpc^-1`), one voxel edge is about 10.4725 Mpc. The
voxel-center counts along native x/y/z are 36/26/31 cells, giving surface
extents about 377.011/272.286/324.648 Mpc. The longest-axis mesh extent is
the staged comparison scale; it does not change the pending dataset item value.

The 4,079 occupied voxels imply about `1.944e6 (Mpc h^-1)^3`, roughly 2.3%
above the paper's rounded `1.9e6` value. This is a voxel-count comparison, not
an independent measurement or a reason to alter the surface. It may differ from
the authors' volume integration and boundary treatment. The soft-blue translucent
surface marks only the reconstructed basin boundary; no additional labels or
axes imply member selection or absolute orientation.

## Rebuild and validation

The original archive is an external build input and is not included in the
repository. With the scientific Python dependencies installed, stage a
self-contained GLB and its registry-style provenance entry outside the repo:

```sh
PYTHONPATH=/private/tmp/universe-mesh-deps ./venv/bin/python \
  scripts/build_laniakea_watershed.py \
  --archive /private/tmp/laniakea-watersheds.zip \
  --output /private/tmp/laniakea-scientific/laniakea-cf4-watershed.glb \
  --entry /private/tmp/laniakea-scientific/laniakea-cf4-watershed.json
PYTHONPATH=/private/tmp/universe-mesh-deps ./venv/bin/python \
  -m unittest tests.test_laniakea_watershed
```

The builder records archive and FITS SHA-256 hashes, FITS shape/header facts,
voxel count, connected-component policy, h conversion, native-axis extents,
voxel-volume comparison, normal orientation, and reconstruction caveats. It
enforces 1.5 MB and 60,000-triangle ceilings. The GLB embeds all geometry and
materials and has no external resources. The JSON is staged evidence, not a
registry update; neither file should be imported until the data redistribution
terms and the item's intended Length definition are resolved.
