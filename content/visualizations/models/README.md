# Downloaded 3D Models

The runtime registry is `../models.json`. Most registered models are downloaded
source assets. The Length explorer also renders explicitly labeled procedural
objects, including hydrogen's probability cloud and ball-and-stick molecules.
The curated Sketchfab manifests are `sketchfab-length.json` and
`sketchfab-volume.json`; a manifest entry does not imply that it has been imported.
Paths in its `src` field are relative to the site root. All models are binary
glTF 2.0 (`.glb`) with embedded textures and buffers. No Draco, Meshopt, Basis/KTX2,
USDZ conversion, external textures, or decompression setup is required.

| Runtime file | Source | License | Geometry |
| --- | --- | --- | --- |
| `nasa-earth.glb` | [NASA Earth](https://science.nasa.gov/resource/earth-3d-model/) | NASA media guidelines | Unit sphere |
| `nasa-moon.glb` | [NASA original GLB](https://assets.science.nasa.gov/content/dam/science/psd/solar/2023/09/m/Moon_1_3474.glb) | NASA media guidelines | Unit sphere |
| `nasa-jupiter.glb` | [NASA Jupiter](https://science.nasa.gov/resource/jupiter-3d-model/) | NASA media guidelines | Unit sphere |
| `nasa-sun.glb` | [NASA Sun](https://science.nasa.gov/learn/heat/resource/sun-3d-model/) | NASA media guidelines | Unit sphere |
| `nasa-earth-moon-distance.glb` | NASA Earth and Moon; [mean-distance figures](https://science.nasa.gov/moon/by-the-numbers/) | NASA media guidelines | Center spacing and radii at one scale |
| `nasa-sun-earth-au.glb` | NASA Sun and Earth; [IAU astronomical unit](https://ssd.jpl.nasa.gov/faq.html) | NASA media guidelines | Center spacing and radii at one scale |
| `wine-bottle.glb` | [Poly Haven Wine Bottles 01](https://polyhaven.com/a/wine_bottles_01) | CC0-1.0 | Single Bordeaux bottle |
| `rigged-human.glb` | [Khronos Rigged Figure](https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/RiggedFigure) | CC-BY-4.0 | Static human bind-pose derivative |
| `coffee-mug.glb` | [Kenney Food Kit](https://kenney.nl/assets/food-kit) | CC0-1.0 | Representative cup |
| `soda-can.glb` | [Kenney Food Kit](https://kenney.nl/assets/food-kit) | CC0-1.0 | Soda can |
| `wine-glass.glb` | [Kenney Food Kit](https://kenney.nl/assets/food-kit) | CC0-1.0 | Stemmed glass |
| `family-car.glb` | [Kenney Car Kit](https://kenney.nl/assets/car-kit) | CC0-1.0 | Sedan envelope proxy |
| `bucket.glb` | [Poly Haven Wooden Bucket 02](https://polyhaven.com/a/wooden_bucket_02) | CC0-1.0 | Open wooden bucket |
| `freight-train-car.glb` | [Kenney Train Kit](https://kenney.nl/assets/train-kit) | CC0-1.0 | Open cargo railcar |
| `shipping-container.glb` | [Kenney City Kit Industrial](https://kenney.nl/assets/city-kit-industrial) | CC0-1.0 | Intermodal container |
| `sketchfab-housefly-v2.glb` | [Schmoldt5000's housefly](https://sketchfab.com/3d-models/housefly-5fe7cbd25f9a446d8bae005893d010dd) | CC-BY-4.0 | Adult *Musca domestica*, display pedestal hidden |
| `sketchfab-bacterium-piliated-v3.glb` | [andrewfrueh's bacterium](https://sketchfab.com/3d-models/bacterium-75ae189551e94d59aedce00104217533) | CC-BY-4.0 | Illustrative pilose rod; species unverified; body-length calibration |
| `coronavirus-sars-cov-2.glb` | [NIAID SARS-CoV-2 virion, NIH 3D 3DPX-013323](https://3d.nih.gov/entries/3DPX-013323) | CC-BY-4.0 | Vertex-colored virion simplified to 50k triangles; envelope calibrated |
| `sketchfab-mitochondrion-v2.glb` | [brianj.seely's mitochondria](https://sketchfab.com/3d-models/mitochondria-7445a425050e49daa881070ca6917a91) | CC-BY-4.0 | Retained as an unused licensed asset; the Length explorer currently prefers a procedural cristae cutaway |
| `mapzen-everest-dem.glb` | [Mapzen Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) | [Mapzen/USGS attribution](https://github.com/tilezen/joerd/blob/master/docs/attribution.md) | Sampled summit terrain and opaque sea-level block |
| `sketchfab-liberty-gravity-jack.glb` | [Gravity Jack's Statue of Liberty](https://sketchfab.com/3d-models/statue-of-liberty-84094e8d5e724b5c882cf576ca12e44e) | CC-BY-4.0 | Hand-modeled statue; runtime adds a simplified pedestal |
| `sketchfab-isuzu-city-bus.glb` | [own.guest's Isuzu Erga Mio](https://sketchfab.com/3d-models/isuzu-erga-mio-bus-050e8acd0bbc4da0902a8a874ef10fca) | CC-BY-4.0 | Japanese city bus envelope proxy |
| `sketchfab-teaspoon.glb` | [LordOfTheSnow's teaspoon](https://sketchfab.com/3d-models/teaspoon-96467926442342eab2c797de0ed80e6a) | CC-BY-4.0 | Uncalibrated 5 mL teaspoon proxy |
| `ceiling-fan.glb` | [Poly Haven Ceiling Fan](https://polyhaven.com/a/ceiling_fan) | CC0-1.0 | Fan with separate blades |
| `orion-hubble-blister.glb` | [Hubble Orion image](https://science.nasa.gov/asset/hubble/hubbles-sharpest-view-of-the-orion-nebula/), [O'Dell et al. 2009](https://doi.org/10.1088/0004-6256/137/1/367) | Credited NASA/ESA image guidelines; project-authored geometry | 672 kB point-cloud illustration; 13 ly photographed field inside the listed whole-nebula span; inferred depth |
| `tarantula-eso-cloud.glb` | [ESO/R. Fosbury (ST-ECF), eso0650a](https://www.eso.org/public/images/eso0650a/) | CC-BY-4.0 | 810 kB observed-color cloud in a calibrated ~951 ly aperture; authored depth, not tomography |
| `boston-marathon-course.glb` | [OSM Boston course](https://www.openstreetmap.org/relation/11680552), Mapzen/USGS | ODbL geometry; terrain attribution; authored diagram CC-BY | 638 kB course-and-terrain diagram; 12x bare-earth relief, separate 42.195 km ruler |
| `amazon-river-geography.glb` | [Natural Earth rivers](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-rivers-lake-centerlines/), Mapzen elevation | Public-domain geometry; terrain attribution; authored diagram CC-BY | 880 kB partial mainstem and context tributaries; separate approximate 6,400 km ruler |
| `great-wall-network-globe.glb` | [OSM Great Wall](https://www.openstreetmap.org/relation/318110), Natural Earth | ODbL geometry; public-domain land; authored diagram CC-BY | 1.15 MB mapped fragment network on a real-sized Earth; separate survey-inventory ruler |

The route models deliberately **do not stretch geography to route length**.
Their straightened rulers represent the catalog quantity; model notes identify
partial coverage, cartographic uncertainty and exaggerated display dimensions.
Build with `scripts/build_route_models.py`; [references, licensing and bundled
machine-readable geometry](sources/route-models.md) preserve the distinction
between ODbL geographic inputs and the CC0 quantitative dataset.

`js/experiences/nearby-space-models.js` also supplies two small authored scenes:
Proxima Centauri's Sun-to-star distance bracket, and a 16-member Local Group map
from catalog coordinates. Both keep distances calibrated while explicitly
enlarging stellar/galaxy markers for visibility. Their source checks and
assumptions are recorded in [nearby-space-models.md](sources/nearby-space-models.md).
The Orion build is reproducible with `scripts/build_orion_model.py`; see
[its provenance](sources/orion-model.md). None of these authored scenes claims
to be a downloaded scientific reconstruction.

The next batch adds the Tarantula cloud, built with
`scripts/build_tarantula_model.py` ([provenance](sources/tarantula-model.md)),
and two AU-coordinate scenes in `js/experiences/outer-solar-models.js`:
the hypothesized Oort reservoir and a nose-side heliosphere cutaway
([references and definitions](sources/outer-solar-models.md)). Their listed
sizes are explicit proxies: an upper-range 200,000 AU Oort diameter and a
240 AU heliosphere nose-region diameter, not an unknown full-tail length.
Diffuse samples opt into a shared 32px soft sprite through `softPoints: true`;
it is generated locally by `model-points.js`, not an external texture.

## Quick Workflow

`AGENTS.md` at the repo root has the short version. The tools: `scripts/preview_glb.cjs`
renders a textured multi-view PNG headlessly with the explorer's lighting;
`scripts/register_model.py ENTRY.json MODEL.glb` copies a processed GLB into place,
recomputes its stats, replaces an older entry (deleting its unused file), updates the
Sketchfab manifest, and checks exact-name matches. Model URLs carry `?v=<sha256 prefix>`,
so a changed file is never served stale from the browser cache.

## Sketchfab Imports

The public search API can find candidates without authentication. The curated
manifests pin each candidate's exact dimension item name, Sketchfab UID, creator,
license, and interpretation note. Some entries remain deferred pending geometry
or editorial review. The imported DNA segment is calibrated by its transverse
width rather than its segment length; its many static atom meshes are merged
by material in the browser to reduce draw calls. Audit candidate identity and
licensing before importing:

```sh
SSL_CERT_FILE=/etc/ssl/cert.pem python3 scripts/sketchfab_models.py audit
SSL_CERT_FILE=/etc/ssl/cert.pem python3 scripts/sketchfab_models.py search 'monarch butterfly'
```

To choose a model yourself, generate a shortlist in a directory separate from
your token file. The review page shows thumbnails, a live rotatable Sketchfab
preview, creator, license, source archive size (when publicly listed), and mesh
face count. It does not download a model or change the site:

```sh
SSL_CERT_FILE=/etc/ssl/cert.pem python3 scripts/sketchfab_models.py review \
  --id sketchfab-domestic-cat --query 'cat' --query 'Bengal Cat' \
  --output /private/tmp/universe-scales-review/cat.html
python3 -m http.server 8123 --bind 127.0.0.1 \
  --directory /private/tmp/universe-scales-review
```

Open `http://127.0.0.1:8123/cat.html`, inspect several candidates from all
sides, then use **Copy approval command** and paste it into a terminal. The
generated command uses absolute paths, so it works from any directory on this
macOS host. You can
also add a known candidate with `--uid UID` when search misses it. Approval
updates only the curated manifest; import is a separate step. The currently
selected [cat](https://sketchfab.com/3d-models/cat-in-motion-3d-model-free-baa1120483c844e6bce9744f3f868c63)
and [Eiffel Tower](https://sketchfab.com/3d-models/free-la-tour-eiffel-8553f94d06e24cb4b0fde1080f281674)
are imported and optimized. For another approved model, run `import --only ID`
with your private token file or `--token-env` and inspect the result locally before publishing. The importer
replaces the previous exact-name match only after the new asset passes checks.

Sketchfab's Download API requires your account's API token. On Sketchfab, open
**My Settings > Password** to find it. Save the token as a single line in a file
outside the repository, for example
`~/.config/universe-scales/sketchfab-token`, and restrict that file to your user
(`chmod 600`). Never commit or paste it into an issue or chat. Import with:

```sh
SSL_CERT_FILE=/etc/ssl/cert.pem python3 scripts/sketchfab_models.py import \
  --token-file ~/.config/universe-scales/sketchfab-token
python3 scripts/fetch_model_assets.py --verify
```

`--token-env` reads `SKETCHFAB_TOKEN` from the process environment instead.
Keep it out of shell history, logs, the repository, and copied commands.
The DNA import used a 3.39 MB GLB, so its per-file import limit was raised to
4 MB only after reviewing the archive and geometry; the normal 2 MB limit remains.
The small-protein example is a 0.49 MB human insulin monomer, not a universal
protein shape. Both new GLBs passed Khronos validation with no errors or warnings.

The import script requests a fresh short-lived URL for each approved model,
embeds its glTF resources in a GLB, discards unused animations for static
presentation, and resizes textures to at most 512 pixels,
retrying at 256 and 128 pixels if the delivered file exceeds the size cap.
Default limits are 15 MB per source archive, 2 MB per delivered GLB, and 20 MB
for the batch. Unsupported decoders, unsuitable licenses, changed author
identities, mismatched identities, and over-budget files are rejected. Import is
idempotent for names already in the registry. The site only loads a matching
model when needed; visitors do not need Sketchfab accounts.

To review multiple licensed candidates before adding them to the site, use
`stage --token-env --uid UID --output-dir /private/tmp/universe-scales-candidates`.
Staging saves self-contained GLBs and source metadata outside the repository.
Use `scripts/render_glb_preview.py` for a quick local shape check and
`scripts/audit_glb_geometry.mjs` to inspect bounds and node names; the preview
is untextured and does not replace an in-browser material/lighting review.
After visual review, import a Volume candidate without another network request
or token:

```sh
python3 scripts/sketchfab_models.py import --dimension volume \
  --staged-dir /private/tmp/universe-scales-candidates --only ID
```

The importer rechecks the manifest UID, creator,
license, source size, and delivered GLB SHA-256. The source token and expiring
download URL are never saved in the repository. For Length, omit `--dimension`.

The chosen cat's source exceeded the default limits, so it and the tower were
first staged with larger import limits, then simplified, texture-resized, and
quantized with glTF Transform 4.5.0. Their delivered sizes are 1.52 MB and
2.11 MB. The registry records the exact source and delivered hashes and
processing steps. For future replacements, inspect the staged size before
raising `--max-archive-mb`, `--max-glb-mb`, or `--max-total-mb`; an import with
raised limits is not ready to publish until optimized and revalidated. The
optimized files use `KHR_mesh_quantization`, which the bundled GLTFLoader
handles without an external decoder.

The renderer links the model creator's Sketchfab page and license beside the
selected item's description. The registry preserves the model UID, source
archive hash, processing steps, delivered hash, and file size. The token and
expiring download URLs are not saved. Review the imported geometry in the
explorer, then regenerate `validation.json` with the Khronos validator below.
The last validated Sketchfab GLBs had zero Khronos validator errors; new imports
must be validated before publication. The Giraffe and
Blue Whale source rigs retain many zero-weight-joint warnings; they are rendered
as static models, and their source animations were discarded.

## Molecular Geometry

`../molecules.json` is the small geometry-only companion to the dataset. Water
uses the [NIST experimental gas-phase geometry](https://cccbdb.nist.gov/expgeom2x.asp?casno=7732185)
(0.958 angstrom O-H bonds, 104.4776 degree H-O-H angle). Alpha-D-glucose uses
[PubChem CID 79025](https://pubchem.ncbi.nlm.nih.gov/compound/79025) atom
coordinates and bonds. Regenerate the local file with:

```sh
python3 scripts/build_molecule_data.py
```

The ball radii and bond rods are visual conventions, not atomic surfaces.
These two procedural models and their geometry-source links appear only in the
Length explorer; the numeric observations remain in the ordinary dataset.

The Virus observation is a SARS-CoV-2 virion: 91 nm, the mean envelope diameter
measured by cryo-electron tomography ([Ke et al. 2020](https://www.nature.com/articles/s41586-020-2665-2)).
The NIAID model from NIH 3D (566k triangles, one vertex-colored surface) was
welded and simplified to about 50k triangles with glTF Transform. Its envelope is
about 0.68 of the full spike-to-spike extent (measured by classifying vertex
colors), so `measure_fraction: 0.68` calibrates the envelope, not the spikes.
The bacterium is a generic illustrative rod rather than a verified *E. coli*
specimen. Its body is calibrated to the 2 micrometer Bacteria marker; pili and
flagella extend beyond the measurement. The mitochondrion now uses an explicitly
schematic procedural cutaway with opaque membranes and cristae; the older GLB is
kept in the registry for provenance but is not selected by the Length explorer.

## Landmarks And Terrain

The football field uses a procedural regulation-sized diagram: the 100 yd
(91.44 m) goal-line span is the dataset length, with 10 yd end zones at each end.
The older stadium scan remains registered but is not loaded in the Length explorer.

`scripts/build_everest_dem.py` samples public Mapzen Terrarium elevation tiles
around Everest into a compact, opaque block down to sea level. The DEM has about
30 m native resolution here and undershoots the surveyed summit, so a localized
height correction anchors the peak to 8,848.86 m. This is an explanatory terrain
diagram, not a navigational or survey model. Mapzen and USGS attribution is kept
in the registry. The source tiles are not committed; the script can fetch them.

The authored Statue of Liberty mesh is licensed CC BY 4.0. A simplified pedestal
is appended at runtime using the [NPS heights](https://www.nps.gov/stli/learn/statue-of-liberty-facts.htm):
46.05 m for the statue, about 46.94 m below it. The listed item value remains
the statue alone; the focus scale is widened to show the full approximately 93 m
monument.

## Orbital Distance Diagrams

`scripts/build_earth_moon_model.py` rebuilds the two distance diagrams from the
already downloaded NASA sphere assets. Earth-Moon uses a representative mean
384,400 km center separation; Sun-Earth uses the exactly defined astronomical
unit of 149,597,870,700 m. Sphere radii and center separation share a single
scale. Earth-Moon distance changes over the lunar orbit, and the actual
Sun-Earth distance is not always one au. These are spatial diagrams, not
time-specific orbital snapshots. The source textures and model credits remain
in the registry; the generator checks their hashes before merging them.
`presentation.distance_bracket` makes the renderer add a white U-shaped bracket
under the two bodies (lines drop from each body's center, matching the
center-to-center distance), upright SVG body labels, and thin outline circles
so bodies smaller than a pixel stay findable; see `addDistanceBracket` in
`js/experiences/procedural-models.js`.

```sh
python3 scripts/build_earth_moon_model.py
python3 -m unittest tests/test_orbital_distance_models.py
```

## Renderer Contract

- `matches` contains case-sensitive names verified against the JSON exports.
  The current registry has 40 GLB entries (Betelgeuse reuses the Sun file with an
  orange emissive tint) and 48 exact-name matches across dimensions. Length and Volume imports share that registry.
- NASA geometry is explicitly adapted to centered unit spheres, including removal
  of the source bodies' oblateness and the Sun's 1000x node scale. Original
  topology, UVs, material roles, and texture orientation are retained. Source
  bounds and texture changes are recorded in each registry entry. These are
  idealized spherical visualizations, not geodetic models. Their cube-cross
  texture atlases have white gutters; `scripts/texture_padding.py` fills them
  with nearest island colors so mipmaps do not draw white seams.
- A sphere's radius is `cbrt(3 * volume / (4 * Math.PI))` for a volume item,
  `sqrt(area / (4 * Math.PI))` for a total-surface-area item, and `diameter / 2`
  for a diameter item. If the renderer first normalizes largest extent to 1,
  its input size must be the resulting **diameter**, not radius.
- For Length models, `presentation.measure_axis` can pin which mesh bound
  represents the recorded value (for example, height for a giraffe or tower).
  The default is the longest bound. `presentation.measure_fraction` can
  calibrate a known measured part of that bound, such as the cat's body excluding
  its tail; this remains an illustrative estimate. A default pose and removable non-subject
  scene nodes are also declared in `presentation`; these change the display,
  not the source GLB. Dragging a model rotates it independently of camera travel.
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

The soda-can items now use an actual Kenney soda-can mesh rather than a food can
or reusable water bottle. Capacity, cargo space, and exterior envelope entries
remain illustrative: none of these meshes is a calibrated watertight measurement.

The current dataset has no Jupiter volume or Moon diameter entry. Earth-Moon
Distance is not a Moon diameter, Earth's oceans is not Earth volume, and Human
skin area is not measured from this proxy. No speculative matches were added.

NASA's old Moon page returned 404. The Sun page currently exposes USDZ only.
Their original GLBs still returned HTTP 200 from NASA's own asset host and were
downloaded successfully. The NASA GitHub collection was also inspected, but its
Moon/Earth printing files and textures were not preferable to these working GLBs.
These outcomes are also recorded in the registry's `coverage_gaps` array.

## Nebula Reference Models

The Orion and Tarantula clouds and the Carina surface use credited telescope
images with published angular fields or physical spans. Observed image colors
and sky-plane locations are preserved; their authored depth cues are **not**
tomographic reconstructions. Carina uses a 735 kB, 1024-pixel textured, gently
bowed 2.5D surface to preserve VISTA's fine structures without granular particles.
Its photographed 193 by 157 ly field sits inside a 300 ly context span; the
photograph is not stretched to the larger dataset value.

Rebuild recipes and exact image credits are in `sources/orion-model.md`,
`sources/tarantula-model.md`, and `sources/carina-model.md`. Their builders take
the documented source images as inputs and embed all runtime resources in GLBs.

## Observable Universe Diagram

`observable-universe-wmap.glb` embeds a sky-coordinate-correct WMAP nine-year
ILC temperature map, not an imagined density field. Its smooth cutaway exposes
the observer, while distinct guides mark the last-scattering and particle-horizon
radii at their approximate present distances. Neither is a material wall.

The 750 kB GLB has 9,120 triangles and needs no external texture or decoder.
`scripts/build_observable_universe_model.py` builds from NASA LAMBDA's original
NESTED FITS; the 24 MB scientific input is not served by the site. Scientific
meaning, downsampling, assigned colors, NASA attribution and the reproducible
build command are documented in `sources/observable-universe-model.md`.

## Coverage And Review

`node scripts/model_lab.cjs coverage --gap 1 --json` inventories production
models, provenance and adjacent logarithmic gaps. It is a planning tool, not
scientific approval. An object count alone is not a useful quality target:
retain familiar anchors, precise definitions and documented uncertainty rather
than inventing objects to fill theoretically inaccessible ranges.

For each addition, check the listed quantity against the calibrated model part,
record source/reuse terms, inspect rest and rotated views plus the real explorer,
and run the existing asset/hash, dataset and rendering tests. Public voting can
prioritize candidate objects; it cannot validate physical values or asset rights.

The five particle-scale scenes in `particle-scale-models.js` are explicit
measurement diagrams. Their rulers represent a derived Planck scale, a HERA
effective-quark-radius bound, a proton rms charge radius, a classical electron
radius and an energy-defined neutrino wavelength. They are not solid particle
models. Definitions and primary references are in `sources/particle-scale-models.md`.

Virgo and Sloan use actual SDSS DR17 galaxy samples with explicit survey-window
wireframes, not invented member catalogs or solid walls. Their public-domain
CSV snapshots, selection queries, cosmology and native-Mpc calibration are
documented in `sources/large-scale-catalog-models.md`. The disputed Hercules-Corona
Borealis scene is a Swift angular evidence chart plus a reported-extent ruler,
not a physical wall mesh; see `sources/grb-structure-model.md`.

Laniakea deliberately remains a photo fallback. Its reference-preview builder
does not produce a registry entry: reusing a published figure does not grant
permission to redistribute the underlying grid, nor turn the figure into
calibrated 3D geometry. See `sources/laniakea-model.md` before attempting an import.
