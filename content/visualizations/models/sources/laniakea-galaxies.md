# Laniakea region from the 2MASS Redshift Survey

Catalog: Huchra, J. P. et al. 2012, ApJS 199, 26, "The 2MASS Redshift Survey: Description and
Data Release", https://doi.org/10.1088/0067-0049/199/2/26, via VizieR J/ApJS/199/26 (table3:
GLON, GLAT, Ktmag, cz for 44,599 galaxies). Used with citation under the CDS/VizieR terms.
Laniakea: Tully, R. B., Courtois, H., Hoffman, Y. & Pomarède, D. 2014, Nature 513, 71,
https://doi.org/10.1038/nature13674 (about 160 Mpc across).

Galaxies are placed at cz / H0 (H0 = 75 km/s/Mpc) along their galactic directions, rotated to
supergalactic coordinates (pole at l = 47.37, b = 6.32; SGL = 0 at l = 137.37, b = 0), and shown
with SGZ up. Kept: galaxies within 80 Mpc (soft edge to 86) of 0.55 x the Norma cluster's
position, a point between the Milky Way and the Great Attractor. Brightness follows absolute K
magnitude (compressed); a second, faint wide-sprite layer traces the cosmic web.

Limits: positions are in redshift space (clusters elongate along the line of sight); the
Galactic plane hides a wedge of sky (Zone of Avoidance); 2MRS is magnitude-limited, so distant
regions look sparser. Laniakea is a basin of galaxy flows; this model shows galaxies, not flows or
a membership boundary. Cluster labels use literature RA/Dec/cz values in the builder.

Rebuild: `./venv/bin/python scripts/build_laniakea_galaxies.py 2mrs.tsv OUT.glb` (catalog hash in
models.json).
