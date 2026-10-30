# SARS-CoV-2: exact-object reuse with an equivalent-volume span

Source: [SARS CoV-2 Virion (NIAID), NIH 3D 3DPX-013323](https://3d.nih.gov/entries/3DPX-013323),
Kristen Browne / NIAID. This Volume entry reuses the already registered
`coronavirus-sars-cov-2.glb` byte for byte. There is no copied binary, recoloring,
geometry modification or change to its separate Length entry. Existing download,
processing and attribution metadata are inherited.

The [NIH entry API](https://3d.nih.gov/api/entries/3DPX-013323), opened on
2026-10-29, explicitly identifies submission 17182 as `CC-BY`. The NIH page
describes an imaging-informed teaching model: a segmented particle was reshaped,
the envelope was regularized and displaced, and PDB-based spikes were distributed
using authored placement. It is not an untouched single-particle reconstruction.
The source also provides a thickened membrane variant for printing, used by the
existing asset. Its source limitations remain applicable.

The existing `SARS-CoV-2 virion volume` datum is a representative spherical
particle approximation. Its membrane boundary must not be confused with the
spiky exterior. The reused GLB fails the strict mesh-volume helper on duplicate
triangles; no enclosed-volume claim is made or inferred from its triangle sum.

For this job's explicitly permitted fallback, **the complete model's longest
native span**, including spikes, **is displayed at V^(1/3)**. Reference size is
107.39584732055664 model units. This equivalent-volume span does not assert a
physical virion diameter, a calibrated lipid-envelope volume, or the model's
material volume. `closed_volume_checked` is false and the note discloses this
convention. The original Length entry retains its 91 nm envelope calibration.

Reused binary SHA-256:
`00a3ea0417a8425d284383085cebd8e36af5135e46811551f2b8f46d48d2e5c2`.
Reproduction and CPU/loader review are in
[the volume3d handoff](../../../../handoff/volume3d/REPORT.md).
