# Reused, volume-calibrated models

2026-10-28. No new geometry or duplicate binary files. The registry points to
existing licensed GLBs, with distinct calibration entries for Volume so Length
and Angular Velocity keep their original presentation.

## Sand

[The Sand Atlas Caicos ooids](https://sand-atlas.scigem.com/sands/caicos-0000001/)
provides micro-CT surface meshes for 117 grains at 1 micrometer voxel resolution,
contributed by Max Wiebicke. The existing CC BY 4.0 `sand-atlas-caicos-ooid-80.glb`
is particle 00080, lightly smoothed by an earlier import. It represents a
carbonate ooid, not quartz or an average of all sand particles.

Its delivered surface encloses approximately 3.77110e-11 native cubic meters.
We rescale it uniformly to the **representative** Volume datum of 5e-10 m^3;
that datum is not a measurement of this specimen. All source coordinates and
topology in the binary remain unchanged. Its Volume rendering no longer treats
the cube root of a volume as the grain's maximum span.

## Red blood cell

[IMU eLearning's RBC Morphology model](https://sketchfab.com/3d-models/rbc-morphology-red-blood-cell-1a1bbd5e3cd746888232fefa46b3f7d1)
is a CC BY 4.0 educational biconcave surface, **not measured cell geometry**.
We retain this existing asset's shape and resting pose and normalize its
enclosed volume to the dataset's representative 90 fL. Shape and volume vary
between cells; this is a scale illustration, not a specimen reconstruction.
Length's independent diameter calibration is unaffected.

## Jupiter

The [NASA VTAD Jupiter asset](https://science.nasa.gov/resource/jupiter-3d-model/)
was already bundled and used in Length and Angular Velocity, but its Volume
match was empty. It now also serves `Jupiter volume`. The existing idealized
sphere convention uses diameter `(6V/pi)^(1/3)`. This is not an oblate geodetic
surface or a newly downloaded model. NASA's credited media terms still apply.

## Reproduce and limitations

```sh
node scripts/mesh_volume.mjs content/visualizations/models/sand-atlas-caicos-ooid-80.glb content/visualizations/models/sketchfab-red-blood-cell.glb
node scripts/register_volume_reuse.mjs --check
```

The vendored GLTFLoader decodes the actual geometry. Native transforms are
included; every edge must have two oppositely oriented incident faces; duplicate
or degenerate faces, multiple disconnected shells and deformable meshes are
rejected. Coincident UV-seam vertices are identified for analysis only. The
signed tetrahedral sum is evaluated about the bounding-box center to avoid
translation cancellation. The calibration is `reference_size = cbrt(V_mesh)`.
The runtime then multiplies by `cbrt(V_item)`, giving exactly `V_item` enclosed
mesh volume up to floating-point precision.

This is a closed, oriented topology check, **not a general self-intersection
test**, a material-volume measurement or proof of biological accuracy. Only the
two named, visually inspected single surfaces are opted in. Containers and
their capacity values, overlapping virion spikes and diffuse astronomical
regions are not automatically assigned this convention. Texture decoding is
stubbed in the offline measurement script; appearance is checked separately
with the real production browser renderer.
