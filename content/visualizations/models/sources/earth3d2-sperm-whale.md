# Sperm Whale — credited artistic exterior

- Model: **Animated Sperm Whale**, by **AneesAnimates**.
- [Original Sketchfab model](https://sketchfab.com/3d-models/animated-sperm-whale-3076676b30294c119ec2065c3bf3dc47).
- [Sketchfab API license/source endpoint](https://api.sketchfab.com/v3/models/3076676b30294c119ec2065c3bf3dc47),
  opened 2026-10-16: downloadable, license slug **`by`**, CC BY 4.0.
- [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- Retained evidence and staging/archive hashes:
  [`earth3d2-imports/3076676b30294c119ec2065c3bf3dc47.json`](earth3d2-imports/3076676b30294c119ec2065c3bf3dc47.json).
- [NOAA Fisheries, Sperm Whale](https://www.fisheries.noaa.gov/species/sperm-whale),
  opened 2026-10-16: representative male length **52 ft** (15.8496 m), matching
  the unchanged dataset. This does not assert the artist modeled a measured male.

## Adaptation

Downloaded with the existing Sketchfab staging tool, outside the repository.
`scripts/prepare_earth3d2_imports.py` freezes the supplied neutral bind pose:
for each vertex it applies the weighted joint-world/inverse-bind transforms
in mesh-local coordinates; normals use the inverse transpose. It then removes
skin weights/joint indices and the rig binding. No invented swim pose or
animation is added.

`scripts/prepare_earth3d2_imports.mjs` uses glTF Transform **4.5.0** and
MeshoptSimplifier offline: deduplicate, flatten, join, weld, simplify toward
45,000 triangles with 0.01 error, regenerate MikkTSpace tangents, prune and
quantize. Meshoptimizer is only an
offline simplifier; no meshopt/Draco decoder or compressed texture is needed.
The source has no base-color map; gray-blue base color is authored, while
source normal/roughness maps and sculpted details remain. Color and skin
detail are illustrative. The final GLB is self-contained and static.

The long **Z axis** is calibrated nose to fluke, uniformly, then turned into
a predominantly side-on resting pose. No independent-axis scaling, scan
claim, known-individual identity or quantitative anatomy claim. It is an
artist's exterior, including interpreted wrinkles, fins and flukes.

Reproduction (download UID above into `/tmp/earth3d2/stage` first):

```sh
./venv/bin/python scripts/prepare_earth3d2_imports.py /tmp/earth3d2/stage/3076676b30294c119ec2065c3bf3dc47.glb /tmp/earth3d2/whale-static.glb
node scripts/prepare_earth3d2_imports.mjs /tmp/earth3d2/whale-static.glb content/visualizations/models/earth3d2-sperm-whale.glb /PATH/TO/node_modules
```

The module directory needs glTF Transform core/extensions/functions 4.5.0 and
meshoptimizer and mikktspace. Production lighting, overlays, picking, explorer framing and
mobile performance still require the lead's model-lab review. CPU previews
were viewed, but do not constitute that approval.
