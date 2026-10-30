# Sugar cube: scanned exterior, bulk-volume calibration

Source: [Sugar Cube 3D Scan (No Texture), arkify](https://sketchfab.com/3d-models/sugar-cube-3d-scan-no-texture-0227084e92ed4dc79e48e0bf271edd32).
The [Sketchfab API](https://api.sketchfab.com/v3/models/0227084e92ed4dc79e48e0bf271edd32)
was opened on 2026-10-29 and returned license slug `by` (CC BY 4.0), author
`arkify`, and a downloadable glTF archive. The author describes a 0.6 by 0.8 inch
sugar cube scanned/processed at 0.2 mm resolution, without a color texture.
The source's white appearance and original proportions are retained.

This is a different, larger specimen, uniformly rescaled to the existing
representative `Sugar cube volume` quantity of 1e-6 m³. No claim is made that
the original specimen was 1 cm³, or that sucrose has no pores. The scale refers
to the **bulk exterior envelope**, including internal air, rather than the
volume of solid sucrose alone.

The staged source has five consistently closed connected surfaces: the outside
(107,320 triangles) and four very small reverse-wound internal shells
(122, 52, 52 and 8 triangles). The internal shells are excluded from this
exterior-envelope view. The outer scanned surface is retained and decimated to
53,660 triangles, without adding caps, fillers, primitives or surface detail.
The new enclosed volume is 3866.2990517839316 model-unit³, and its cube root
15.695138326976915 is the Volume entry's `reference_size`. The rendered,
normalized exterior therefore encloses one unit³ before the item's V^(1/3)
display scaling. The source scan's Length calibration is not used.

`scripts/mesh_volume.mjs` verifies a single connected, consistently wound closed
shell, with no boundary edges, duplicate faces or degenerate triangles. This
does not certify absence of self-intersections. The bulk-envelope convention
avoids summing the source's interior pore shells as positive solids.

Reproduction, source/staged/output SHA-256 pins, final entry, exact loader
measurements and CPU previews are in [the volume3d handoff](../../../../handoff/volume3d/REPORT.md).
Build with `scripts/prepare_volume3d_imports.mjs`, then
`scripts/register_volume3d.mjs`. CPU previews do not certify production WebGL.
