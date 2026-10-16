# Hyperion: generic redwood illustration

Asset: [Redwood Tree 2 by rhcreations](https://sketchfab.com/3d-models/redwood-tree-2-2c34fb28a756474eb8072a450c8f632b),
CC BY 4.0. Adaptation by Universe Scales. The direct
[Sketchfab API record](https://api.sketchfab.com/v3/models/2c34fb28a756474eb8072a450c8f632b)
was opened on 2026-10-16 and confirms `isDownloadable: true`, author `rhcreations`
and license slug `by`. Pinned identity/license/archive-hash evidence is in
`earth3d3-imports/2c34fb28a756474eb8072a450c8f632b.json`.

This is the creator's redwood illustration, **not Hyperion's measured geometry**.
The source's branch architecture, foliage and trunk proportions are preserved,
then uniformly calibrated on its vertical axis to the current catalog height,
116.2 m. The job brief specifies 116.22 m, a 0.02 m rounding difference.

[Guinness](https://www.guinnessworldrecords.com/world-records/tallest-tree-living)
records 116.07 m in 2019. That dated measurement does not independently verify the
catalog's 2026 figure. [NPS](https://home.nps.gov/redw/planyourvisit/hyperion.htm)
identifies Hyperion as an off-trail coast redwood; it supplies context only.
No coordinates or claim to reproduce its crown, trunk diameter or present health
is included. No dataset change was made.

Offline preparation: `scripts/prepare_earth3d3_imports.mjs`. Legacy
specular/glossiness materials are converted to metallic/roughness; foliage uses
alpha testing rather than blended-card sorting. Foliage is a 512 px PNG and other
textures are JPEG at up to 1024 px. Source geometry is static and small; the
billboard foliage remains flat when inspected edge-on. This is an artistic tree,
not a botanical survey.
