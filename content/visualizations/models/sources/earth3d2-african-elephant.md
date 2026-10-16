# African Bush Elephant — credited exterior, shoulder-height calibration

- **African Elephant**, by **jimmyho905**, [original model](https://sketchfab.com/3d-models/african-elephant-b960467b14f34cfc84feeb3361a21f54).
- [Direct API metadata](https://api.sketchfab.com/v3/models/b960467b14f34cfc84feeb3361a21f54),
  retrieved 2026-10-16 with the importer's Python HTTP client: downloadable,
  license slug **`by`**, **CC BY 4.0**. Evidence and source/archive hashes:
  [`earth3d2-imports/b960467b14f34cfc84feeb3361a21f54.json`](earth3d2-imports/b960467b14f34cfc84feeb3361a21f54.json).
- [San Diego Zoo, Elephant](https://animals.sandiegozoo.org/animals/elephant),
  opened 2026-10-16: male African shoulder height averages 3–3.2 m. Its
  morphology account distinguishes the broad African ears, swayed back and
  trunk from Asian elephants. The unchanged **3.2 m** catalog marker is a
  representative male shoulder height, not maximum body length.

## Calibration and representation

The artist calls this an “African Elephant”; its savanna-elephant appearance
is illustrative. It is not a scan, a taxonomically verified specimen,
identified individual, or measured male.

The **highest source-mesh point is the dorsal withers above the forelegs**,
near the midline and just forward of the body's center; the head/ear/trunk
vertices are lower. Thus Y extent in this particular neutral pose really is
foot-to-shoulder height. This is checked on the source geometry, not assumed
from a general whole-animal bounding box. In centered source-world units the
withers have X near zero and Z between 0 and 0.007; the full foot-to-withers
extent after quantization is approximately 0.032761811 source units. These
are derived mesh coordinates, not biological measurements.

`measure_axis: y` uniformly maps that extent to 3.2 m. The initial almost
frontal pose fits the size rule while leaving the whole long body intact
for rotation. A side view naturally exceeds 1.3× the shoulder height; no body
shortening, independent-axis stretch, hidden anatomy or camera-dependent
resizing is used. Lead review should check neighboring-model clearance
during drag rotation as well as the valid resting view.

## Preparation

Use the same Python skin-bind-pose bake as the sperm whale, then run the JS
preparation with the final `elephant` argument. Source colors and both
1024-pixel JPEG textures are retained; no triangles need simplification.
Deduplicate, flatten, join, weld, regenerate MikkTSpace tangents, prune unused
rig/accessors, and quantize. The large staged GLB contained unused rig data;
pruning reduces it to a small self-contained asset without truncating the body.

```sh
./venv/bin/python scripts/prepare_earth3d2_imports.py /tmp/earth3d2/stage/b960467b14f34cfc84feeb3361a21f54.glb /tmp/earth3d2/elephant-static.glb
node scripts/prepare_earth3d2_imports.mjs /tmp/earth3d2/elephant-static.glb content/visualizations/models/earth3d2-african-elephant.glb /PATH/TO/node_modules elephant
```

The original cached stage happened to be under `/tmp/earth3d-stage`; the
example uses this job's staging directory for a fresh download. Required
offline JS tools are glTF Transform 4.5.0, meshoptimizer and mikktspace.
The license remains CC BY 4.0; adaptation by Universe Scales. CPU rest and
quarter-camera previews were inspected; production WebGL review is pending.
