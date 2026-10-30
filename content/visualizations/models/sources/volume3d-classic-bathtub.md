# Bathtub: exterior capacity illustration

Source: [Classic Bathtub, renderartestudio](https://sketchfab.com/3d-models/classic-bathtub-7427e2c0c32c44b89deb058f6583742a).
The [source API](https://api.sketchfab.com/v3/models/7427e2c0c32c44b89deb058f6583742a)
was opened on 2026-10-29 and returned license slug `by` (CC BY 4.0), author
`renderartestudio`, and a downloadable glTF archive. The author describes a
classic gold-plated ceramic bathtub. There is no asserted scan, manufacturer,
metric scale, rated capacity or actual fill level. It is an existing authored
prop, not geometry created by this project.

The same GLB and entry serve the two existing observations `Bathtub` and
`Bathtub volume`, both representative 0.15 m³ (150 L) water-capacity examples.
The model depicts the exterior tub and empty basin. It does **not** depict
150 L of water, certify its basin capacity, or measure the ceramic/metal volume.
There is no added water surface, fill mark or container-volume claim.

As allowed by this job's fallback calibration, the longest native source span
(1.748028039932251 model units) is normalized to one. The runtime displays it
at V^(1/3), an **equivalent-volume span**. Thus its rendered dimensions are not
asserted to be the dimensions of a real 150 L bathtub. `closed_volume_checked`
is false and `volume_semantics` remains `cubic_linear_equivalent_approximation`.
The topology audit rejects this source as open/nonmanifold; using its signed
triangle sum to infer capacity would be invalid in any case.

Processing embeds source resources, resizes source textures to at most 1024 px,
deduplicates/welds and prunes unused data. Source proportions, colors and shapes
are preserved. The resting pose exposes the basin. No mesh geometry was authored.
Input/archive/output pins and rebuild instructions are in
[the volume3d handoff](../../../../handoff/volume3d/REPORT.md).
