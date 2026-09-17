# Downloaded 3D Models

Six real, freely reusable source models are downloaded and adapted here, not
replaced with generated stand-ins. The runtime registry is `../models.json`.
Paths in its `src` field are relative to the site root. All models are binary
glTF 2.0 (`.glb`) with embedded textures and buffers. No Draco, Meshopt, Basis/KTX2,
USDZ conversion, external textures, or decompression setup is required.

| Runtime file | Source | License | Geometry |
| --- | --- | --- | --- |
| `nasa-earth.glb` | [NASA Earth](https://science.nasa.gov/resource/earth-3d-model/) | NASA media guidelines | Unit sphere |
| `nasa-moon.glb` | [NASA original GLB](https://assets.science.nasa.gov/content/dam/science/psd/solar/2023/09/m/Moon_1_3474.glb) | NASA media guidelines | Unit sphere |
| `nasa-jupiter.glb` | [NASA Jupiter](https://science.nasa.gov/resource/jupiter-3d-model/) | NASA media guidelines | Unit sphere |
| `nasa-sun.glb` | [NASA Sun](https://science.nasa.gov/learn/heat/resource/sun-3d-model/) | NASA media guidelines | Unit sphere |
| `wine-bottle.glb` | [Poly Haven Wine Bottles 01](https://polyhaven.com/a/wine_bottles_01) | CC0-1.0 | Single Bordeaux bottle |
| `rigged-human.glb` | [Khronos Rigged Figure](https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/RiggedFigure) | CC-BY-4.0 | Static human bind-pose derivative |

## Renderer Contract

- `matches` contains case-sensitive names verified against the three JSON exports.
  There are 13 matches: four length, four area, and five volume entries.
- NASA geometry is explicitly adapted to centered unit spheres, including removal
  of the source bodies' oblateness and the Sun's 1000x node scale. Original
  topology, UVs, material roles, and texture orientation are retained. Source
  bounds and texture changes are recorded in each registry entry. These are
  idealized spherical visualizations, not geodetic models.
- A sphere's radius is `cbrt(3 * volume / (4 * Math.PI))` for a volume item,
  `sqrt(area / (4 * Math.PI))` for a total-surface-area item, and `diameter / 2`
  for a diameter item. If the renderer first normalizes largest extent to 1,
  its input size must be the resulting **diameter**, not radius.
- For `geometry: "mesh"`, use the application's same cubic-linear equivalent
  approximation. Neither human nor bottle has a checked, calibrated closed
  volume. Bottle capacity is not glass volume; the human is not an anatomical
  scan. Do not advertise the rendered mesh's enclosed volume as the dataset value.
- The human asset is static and Y-up despite its historical `rigged-human` name.
  It has no skins or animations, so ordinary scene cloning is sufficient.
- The bottle uses optional `KHR_materials_transmission` for glass. A normal modern
  GLTFLoader supports it without a decoder. Lighting/environment affects glass
  visibility. Its original 1k JPEG textures are embedded without re-encoding.
- Earth and bottle normal maps rely on runtime-generated tangent space, as the
  upstream assets do. Khronos validation reports warnings for this, not errors.
  NASA textures are 1024x768 atlas images: non-power-of-two dimensions are normal
  for WebGL2, and must not be reinterpreted as equirectangular maps.

## Attribution And Provenance

Keep `licenses/` and the registry with redistributed files. Credit NASA for its
four models; Earth and Jupiter source pages specifically credit NASA VTAD. The
current Moon/Sun download metadata does not identify an individual artist.
NASA's media guidelines are preserved in full: educational/informational use is
permitted, but this is not a CC0 grant or an endorsement. NASA insignia and third-
party works have separate restrictions; no NASA logo is part of these models.

Wine bottle: Rico Cilliers (modeling), Jurita Burger (graphic design), Poly Haven,
CC0-1.0. Original `wine_bottles_01_bordeaux` extracted from the four-bottle scene.

Human: Cesium (2017), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Adapted by Universe Scales to static bind pose and Y-up. Display this attribution
where model credits are shown; do not claim Cesium endorsement.

The registry records runtime SHA-256, original-source SHA-256, byte counts,
processing, material extensions, and exact matches. `sources/downloads.json`
records every downloaded asset/texture/license URL and hash. Source HTML and
Poly Haven's original JSON metadata are preserved for audit, not loaded at runtime.
The saved upstream `sources/wine-bottles.gltf` is provenance only, not a second
runtime asset; its external references are embedded into `wine-bottle.glb`.

## Rebuild And Verify

From the repository root:

```sh
python3 scripts/fetch_model_assets.py --verify
python3 scripts/fetch_model_assets.py
```

Verification is offline, read-only, and uses only the Python standard library.
Rebuilding requires network access and Pillow (build used 12.1.1). Binary and
texture downloads are checked against the saved SHA-256 lock; Poly Haven's MD5
checksums are also verified. Only use `--update-lock` after reviewing changed
upstream assets. Pillow/library versions can affect derivative output hashes.

On this macOS host, Python's default CA store was incomplete. A verified build
succeeded with the system CA bundle, without disabling TLS checks:

```sh
SSL_CERT_FILE=/etc/ssl/cert.pem python3 scripts/fetch_model_assets.py
```

`validation.json` records independent Khronos glTF Validator results for the
delivered GLBs. Regenerate that report if the runtime files change. The downloader
also validates GLB chunk/buffer structure, decoder independence, spherical radii,
source/license hashes, and exact-name matches. It does not claim mesh watertightness.

To regenerate the independent report, install `gltf-validator@2.0.0-dev.3.10` in a
temporary tool directory, then run:

```sh
node content/visualizations/models/validate-models.cjs /path/to/node_modules/gltf-validator
```

## Missing Coverage

No appropriate soda-can GLB was found in the reviewed Poly Haven/Khronos catalogs
or Smithsonian search. Food cans, cleaner cans, and reusable water bottles were
not mislabeled as soda cans. `Soda can` and `Soda can volume` remain uncovered.

The current dataset has no Jupiter volume or Moon diameter entry. Earth-Moon
Distance is not a Moon diameter, Earth's oceans is not Earth volume, and Human
skin area is not measured from this proxy. No speculative matches were added.

NASA's old Moon page returned 404. The Sun page currently exposes USDZ only.
Their original GLBs still returned HTTP 200 from NASA's own asset host and were
downloaded successfully. The NASA GitHub collection was also inspected, but its
Moon/Earth printing files and textures were not preferable to these working GLBs.
These outcomes are also recorded in the registry's `coverage_gaps` array.
