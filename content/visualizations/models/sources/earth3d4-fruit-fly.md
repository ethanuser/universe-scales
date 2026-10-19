# Fruit fly: existing university micro-CT mesh

The displayed animal is an adult female **Drosophila melanogaster**, reared in
Herman Wijnen's laboratory at the University of Southampton. It is the existing
[ETAIN project model](https://sketchfab.com/3d-models/drosophila-adult-fruit-fly-ct-scan-ad29b897bd2b4e27bb04ab9d31baa117),
not geometry authored for Universe Scales. Orestis Katsamenis scanned the fixed,
iodine-stained specimen with a Nikon XTH225ST micro-CT system; Felipe Ribas
processed the source mesh in Blender. The orange, translucent CT material is
the source author's visualization, not the animal's natural coloration.

## License and pinned inputs

The [Sketchfab model API](https://api.sketchfab.com/v3/models/ad29b897bd2b4e27bb04ab9d31baa117)
was opened on 2026-10-18: `isDownloadable: true`, license slug `by`,
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The API license snapshot and staging manifest are in [earth3d4/](earth3d4/).
They contain no credentials or temporary authenticated download URLs.

- Original downloadable glTF archive SHA-256:
  `210b91eb9bb8bbb8bbbb69c9372cf954c53aca7c1428769af5c5766f07ef661e`.
- Packed staging GLB SHA-256:
  `00e14941b30e3a017426984ec45372972501235bc41d54e7e193f5ddccb7ef6e`.
- The archive itself is a temporary build input, not a hosted runtime asset.

## Measurement and processing

The catalog uses a representative **2.5 mm body length**. The University of
Leipzig's [Drosophila gap-crossing research page](https://www.lw.uni-leipzig.de/en/institut-fuer-biologie/departments/genetics/triphan-technische-verhaltensneurogenetik/lueckenueberwindung)
also describes a body size of approximately 2.5 mm. This is a representative
scale assignment, not a claim that this preserved individual was measured at
that length by its scanner.

Calibration uses two manually identified **vertices of the original CT mesh**:
the abdomen tip and anterior head surface. Their straight-line separation is
1.7721210623885464 source scene units. Vertex coordinates, source hash, and
method are recorded in `handoff/earth3d4/fly-calibration.json`; the annotated
side projection is `handoff/earth3d4/previews/fly-calibration.png`.
The full body, legs, wings and bristles are retained. The longest whole-animal
box is not mistaken for body length. No posture was changed or invented.

`scripts/prepare_earth3d4_imports.mjs` verifies both input hashes, merges static
mesh splits, welds/decimates the existing surface toward 90,000 triangles with
error limit 0.002, prunes and quantizes. No new geometry, recoloring, labels,
normal synthesis, or compression decoder is introduced. The imported source
material, including its transparency, is retained. This prepared specimen and
scan surface are not a flawless, living anatomical reconstruction.

CPU previews show geometry and approximate color only; they do not reproduce
WebGL transparency, lighting, perspective, the radial explorer or mobile behavior.
Production visual review remains for the lead outside the browser sandbox.
