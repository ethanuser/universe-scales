# Influenza: existing NIAID cutaway

Source: [Influenza Virion (PathogenAR), NIH 3D 3DPX-013373](https://3d.nih.gov/entries/3DPX-013373),
created by Kristen Browne / NIAID for PathogenAR. The
[entry API](https://3d.nih.gov/api/entries/3DPX-013373) was opened on 2026-10-29.
Submission 17244 explicitly lists license `CC-BY`, without a version number.
This entry records that source license without asserting a particular version.
The sanitized primary metadata snapshot is in the handoff research directory.

The NIH page identifies a scientific **cutaway illustration**, with red
hemagglutinin, yellow neuraminidase, M1/M2, nucleoproteins, RNA, polymerase and
other components. Its original colors and cutaway are retained. It is not an
unmodified cryo-EM reconstruction, and no specimen's measured volume is claimed.

Pinned download: [Influenza_0_NIH3D.glb](https://3d.nih.gov/api/submissions/17244/runs/2e7bbb59-6917-4533-b94e-a14afe44f578/output-files/385370),
5,997,144 bytes, SHA-256
`2fb62fa7544538e6d304901b0e690abfc8beffc9babf5b1772c67641eb2c54e8`.
The source's 300,022 triangles are reduced to 70,841 with glTF Transform
simplification (target ratio 0.24, error 0.01), preserving vertex colors and
source proportions. Its implicit white material is made explicit without
changing vertex colors; no new biological surface or internal part is invented.

The existing `Influenza virion volume` datum is a representative spherical
particle approximation. The source's cutaway and separate components do not
define that membrane-bounded volume. Instead, as permitted by this job, the
**longest native span is displayed at V^(1/3)**. This is an equivalent-volume
span, not an enclosed mesh-volume measurement, spike-to-envelope conversion,
or physical dimension inferred for this particular virion. The reference size
is 1.9759460091590881 source units; `closed_volume_checked` is false.

Source selection, rejected alternatives, output hash, CPU previews and pending
browser review are in [the handoff](../../../../handoff/volume3d/REPORT.md).
