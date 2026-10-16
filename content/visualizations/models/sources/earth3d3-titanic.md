# RMS Titanic

Asset: [Titanic by farhad.Guli](https://sketchfab.com/3d-models/titanic-fa41e6b093b84010a462ef190210d90b),
CC BY 4.0. Adaptation by Universe Scales. The direct
[Sketchfab API](https://api.sketchfab.com/v3/models/fa41e6b093b84010a462ef190210d90b)
was opened 2026-10-16 and confirms downloadable status, creator and license slug
`by`. Pinned evidence/archive hashes:
`earth3d3-imports/fa41e6b093b84010a462ef190210d90b.json`.

The source is an authored exterior with four funnels, hull, deck fittings,
superstructure and rigging. It is not a scan, original shipyard CAD or a verified
engineering reconstruction. Local detail, proportions and colors are illustrative.

[Atlantic Liners: Titanic particulars](https://atlanticliners.com/white_star_home/titanic_home/)
gives an overall length of 882 ft 9 in, or 269.0622 m using international feet.
The explorer calibrates the full bow-to-stern X extent uniformly to the existing
269.1 m catalog value. The complete hull remains; there is no waterline crop,
sinking pose or wreck geometry.

Prepare offline with `scripts/prepare_earth3d3_imports.mjs`: deduplicate, flatten,
join, weld, simplify toward 55k triangles with error limit 0.012, retain source
linework, prune and quantize. Texture maps are JPEG, up to 1024 px. The actual
result can exceed the simplification target where preserving topology limits
reduction. There are no decoder dependencies or external textures.

CPU previews verify textured geometry and calibration, not production lighting,
line widths, perspective, explorer framing or mobile behavior.
