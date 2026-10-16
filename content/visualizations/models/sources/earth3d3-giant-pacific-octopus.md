# Giant Pacific octopus: prepared but unregistered

[CC0 North Pacific Giant Octopus by ffishAsia-and-floraZia](https://sketchfab.com/3d-models/7fb48f6cbcd54149bb23837a3ac09b2e).
The [direct API record](https://api.sketchfab.com/v3/models/7fb48f6cbcd54149bb23837a3ac09b2e)
identifies Enteroctopus dofleini and explicitly states CC0; downloadable status
and identity/license evidence are pinned in
`earth3d3-imports/7fb48f6cbcd54149bb23837a3ac09b2e.json`.

The preserved specimen has arms swept in one direction. Its longest posed extent
includes the mantle and is **not a 4.3 m fully spread arm span**. The source has no
physical calibration metadata establishing arm length. No uniform physical scale
has therefore been assigned and there is no registry entry or dataset edit.

The final candidate and metadata are under `handoff/earth3d3/pending/`. Offline
preparation is included in `scripts/prepare_earth3d3_imports.mjs`: remove the
disconnected calibration cube, preserve both textured anatomy meshes, flatten,
join/weld, attribute-aware permissive simplification, integer atlas-U translation
(lossless under REPEAT wrapping), 16-bit geometry/UV quantization and 1024 px JPEGs.
No invented arms, anatomy, terrain or synthetic replacement shape is added.

The source's unlit material preserves photographed color. The CPU preview tool
was corrected to respect repeating UVs and unlit materials; its earlier clamped
UV preview was wrong. The final candidate has been viewed dorsally and ventrally.

To activate this asset, establish a defensible arm-span calibration or explicitly
choose a different item definition with an independent source. Do not silently
calibrate the mantle-to-arm-tip posed extent as an arm-tip-to-arm-tip span.

Sources opened 2026-10-16. The candidate is not a browser-approved model.
