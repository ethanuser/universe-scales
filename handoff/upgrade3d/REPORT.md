# upgrade3d — source-backed replacement review

2026-10-23. Branch: `codex/upgrade3d`. Starting commit:
`f5f8f733b79465268e499bdce4220f75a47d8afb`.

## Result

Reviewed all **32 requested items**. **One replacement** met the source,
license, presentation and scope criteria: **Basketball**. The other **31 retain
their current runtime models**. No new mesh was authored or generated from
invented geometry. No dataset, descriptions, images, runtime JS/CSS, HTML or
model-review files were edited. No shared-venv dependencies were installed.

The replacement is [robin.sculac's Rugged Basketball photoscan](https://sketchfab.com/3d-models/rugged-basketball-008e9eacb9044b11b358a0c2bdae1934),
captured with 3DF Zephyr. Its photographed wear, seams and pebbling replace the
dimensioned ball illustration. The selected source's
[model-detail API](https://api.sketchfab.com/v3/models/008e9eacb9044b11b358a0c2bdae1934)
reports `license.slug: by` and `isDownloadable: true`. The compact snapshot is
`content/visualizations/models/sources/upgrade3d-basketball-scan.source.json`.

| Field | Final delivery |
| --- | --- |
| ID | `upgrade3d-basketball-scan` |
| Replaces | `earth3d-basketball` |
| License / credit | CC BY 4.0 / robin.sculac on Sketchfab |
| GLB | `content/visualizations/models/upgrade3d-basketball-scan.glb` |
| Size / triangles | 433,972 bytes / 16,472 triangles |
| SHA-256 | `7ea82620c57a5e141da30ca64caa2993b1651b19ed0624e7116a228ffa26437f` |
| CPU resting extent | 1.0000× catalog diameter |
| CPU quarter-turn extent | 0.9968× catalog diameter |
| Validator | Zero errors, zero warnings |
| Handoff entry | `upgrade3d-basketball-scan.entry.json`, including `replaces` |

The catalog's **239 mm representative diameter is unchanged**. The
[Wilson guide](https://au.wilson.com/pages/how-to-choose-a-basketball/1000)
specifies 29.5 inches circumference for size 7, giving approximately 238.51 mm
diameter. **The photographed specimen's size is not documented by its creator**:
the note explicitly says it is uniformly calibrated to the catalog value, not
evidence that the scanned ball itself is size 7. Source proportions, colors and
minor scan irregularities are retained. `display_label` is unset; no caveat text
or other labels are embedded in the model.

## Processing and visual selection

`scripts/prepare_upgrade3d_imports.mjs` verifies pinned archive/staged hashes,
converts the legacy specular/glossiness material to standard PBR, deduplicates,
flattens, joins, welds, prunes and quantizes. There is no decimation, filling,
reconstruction, reshaping or recoloring. Staging resizes the source texture to
1024 pixels. No Draco, Meshopt, KTX2 or WebP compression is used.

Downloaded and CPU-rendered two permitted ball scans:

- **Selected:** [Rugged Basketball](https://sketchfab.com/models/008e9eacb9044b11b358a0c2bdae1934),
  robin.sculac, API `by`. Its worn surface is readable and its silhouette remains
  consistent through the inspected rotations. Final asset is smaller than the
  retired 1,054,024-byte illustration.
- **Rejected:** [Basketball](https://sketchfab.com/models/e4850557b63446acab091cd6bf31041c),
  akaro96, API `by`. Good pebbled texture, but its underside has incomplete scan
  coverage visible at some rotations. Its optimized version was also larger.

Both candidates were viewed from four yaw angles. The selected final asset was
then reviewed side by side with the old model at the registry rest pose and a
quarter turn, and rasterized directly at small canvas sizes. These final images
were opened and visually inspected:

- `previews/basketball-rest.png`
- `previews/basketball-quarter-turn.png`
- `previews/basketball-small.png` — 48 / 96 / 160 pixel canvases, about 84% occupied.
- `previews/titanic-existing-black-hull.png` — unchanged special-case reference.

The CPU renderer uses base-color textures, approximate diffuse lighting and a
depth buffer. **These are not production WebGL, perspective, material,
neighbor-spacing, hover/picking, explorer or mobile approvals.**

## Search audit — all requested items

`research/search-audit.json` records each item, exact Sketchfab API query,
returned/eligible counts and relevant candidate IDs/license labels. Searches
were the first page of up to 24 downloadable results per query, with additional
targeted web/data research below. These are scoped search findings, **not a
claim that no suitable asset exists anywhere**. Only the two basketball
candidates were downloaded as 3D assets. Rejected candidate thumbnail/source
inspection is not presented as a full geometry audit.

| Item | Search / strongest candidate or source | Decision |
| --- | --- | --- |
| Human Platelet | Sketchfab `platelet`; [NIH platelet-em](https://bio3d-vision.github.io/platelet-description.html) and [Guay et al. dense-cell release](https://leapmanlab.github.io/dense-cell/), both original releases downloaded and labels examined | Retain. No platelet-sized complete interior instance in the 24/50-slice instance labels. The longer test crop supplies semantic classes, with touching cells joined into a boundary-reaching component; it does not identify an unambiguous complete cell instance. Do not close a cropped surface or invent a new segmentation. Details below. |
| Chloroplast | Sketchfab `chloroplast`; [EMD-52542](https://www.ebi.ac.uk/emdb/EMD-52542), [EMPIAR-11830 segmentation tutorial](https://mgflast.github.io/Ais/tutorials/chloroplasts/), and published electron-tomography reconstructions | Retain. Ready-model results did not establish scan provenance; tomography sources describe imaged subvolumes/lamellae rather than a readily reusable, complete representative chloroplast with a verified envelope. No full replacement extracted. |
| Human Capillary | Sketchfab `capillary`, including [perivascular adipose confocal data](https://sketchfab.com/models/8f7c6cd4dcb84bdb99e5be9621de941d); human capillary tomography/segmentation searches | Retain. The confocal scene does not establish an isolated human capillary's outer diameter and complete wall geometry. Network/tissue views do not directly replace the current calibrated diameter example. |
| Neutrophil | Sketchfab `neutrophil`; [Neutrophil LLS7 example](https://bioimageanalysiscorewehi.github.io/napari_lattice/examples/neutrophil/) | Retain. Ready meshes are educational illustrations rather than documented whole-cell scans. The microscopy example labels nuclei; that cannot supply the missing whole-cell/granule geometry. |
| Human Cone Cell | Sketchfab `cone cell`; human cone OCT and EM reconstruction searches | Retain. Returned ready assets were schematic. No complete, openly reusable human cone-cell surface with documented outer/inner segments and calibration was obtained; OCT reflectivity is not a segmented full cell. |
| Human Egg Cell | Sketchfab `oocyte`; whole-oocyte segmentation searches; [Tactiles teaching model](https://tactiles.eu/tactiles/human-egg-cell/) | Retain. Identified ready objects are educational constructions; 2D contour and mouse-oocyte datasets do not provide a ready complete human oocyte reconstruction matching this item. |
| Human Eye | Sketchfab `human eye`, `human eye scan`; [Auzoux eye model scan](https://sketchfab.com/models/e94ef889864045c1a971facce4c65e73); [BodyParts3D](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/desc.html) | Retain. Auzoux is NC and is a scan of a teaching model. BodyParts3D's current [archive license is CC BY 4.0](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html), not grounds for a blanket license rejection; however, an atlas eyeball without photographed external detail is not established as a visual upgrade to the current eye. No BodyParts3D geometry downloaded. |
| Human Hair | Sketchfab `human hair scan`, `hair micro CT`; [2025 micro-CT study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11733847/) | Retain the runtime illustration. Search results largely concern full human/head scans. The micro-CT paper carries NC-ND terms; no permitted strand-surface dataset with resolved cuticle detail was acquired. |
| Table Tennis Ball | Sketchfab `table tennis ball scan`, `ping pong ball`; [Used Paddle & Ball](https://sketchfab.com/models/f509fb43ad4647238cb4c74b38ab9c8a) | Retain. The actual paddle/ball scan is ND. Other relevant returns were tables or paddles, not a usable complete permitted ball scan. |
| Tennis Ball | Sketchfab `tennis ball`, `tennis ball scan`; [Polycam tennis ball](https://sketchfab.com/models/1c4dea9a63a64ef994c1f757ad3204a9), [dog's tennis ball](https://sketchfab.com/models/25cc6bcb3a15453398dafc1b74a81a4f), [Everypoint scene](https://sketchfab.com/models/6da5ede54a3a43eea44f311b02eeb136) | Retain. The first has NC-SA terms, the second a Free Standard license rather than the allowed licenses, and the third is a coarse scene/point cloud containing a ball and shoe, not an isolated full ball. |
| Credit Card | Sketchfab `credit card`, `credit card scan`, targeted scan search | Retain. No actual permitted photoscan of an unpersonalized ID-1 card was identified that improves on the dimensioned standard envelope. Do not introduce account data or an invented new card. |
| Smartphone | Sketchfab `smartphone`, `smartphone scan`, targeted photogrammetry search | Retain. Most scan hits mean objects captured *with* a phone. No clearly better source-backed scan of the item’s current phone envelope was established; ordinary artist phone models are not a scan upgrade. |
| Basketball | Sketchfab `basketball scan`, `basket ball`; two source-verified, downloaded photoscans compared | **Replace** with robin.sculac's scan, as above. |
| A4 Paper | Sketchfab `A4 paper`, `A4 paper scan`, exact scan search | Retain. Relevant dimensional geometry is already the standard trimmed sheet. No useful full sheet scan identified; arbitrary curl/thickness would not improve measurement fidelity. |
| Silicon Wafer | Sketchfab `silicon wafer`; exact wafer 3D scan/data search | Retain. No permitted full bare-wafer scan identified. Surface-metrology plots of etched areas do not provide a complete bare-wafer replacement, and invented circuitry is outside the brief. |
| Rafflesia | Sketchfab `rafflesia`; [Gunung Gading Scaniverse flower](https://sketchfab.com/models/af22b00c74be4dd589b0ab14ce0da82c) | Retain. This is a genuine BY scan, but its description gives approximately 55 cm and a Gunung Gading location without identifying it as *R. arnoldii*. The catalog explicitly describes *R. arnoldii*. Do not silently substitute a different/undetermined species. |
| Komodo Dragon | Sketchfab `komodo dragon`; [NHM Vienna scan](https://sketchfab.com/models/09a82ad5c86e44abbcc1f37c2f862042), [Digital Life adaptation](https://sketchfab.com/models/3116cc16e8aa4871898a6dfb982b2611), [Florida specimen](https://sketchfab.com/models/c6602993155a45858c310ef57b2bda80) | Retain. Vienna's specimen and Digital Life adaptation are NC. The Florida BY scan is only a skull, as visually checked. The Weta Cave BY scan is a bronze sculpture, not a more accurate specimen surface. |
| Lolong the Crocodile | Sketchfab `saltwater crocodile`, `crocodylus porosus`; [Dundee skull](https://sketchfab.com/models/7ab8c721e8724897a6d1b8b9c54d4016), [conjoined hatchlings](https://sketchfab.com/models/09493ca87c94408ca140c6275d526665) | Retain. Skull is NC-SA and incomplete for total length; hatchlings are NC-ND and the wrong life stage/anatomy for Lolong. No permitted complete adult saltwater-crocodile scan obtained. |
| Giant Squid | Sketchfab `giant squid`; [3DScannerApp hit](https://sketchfab.com/models/62b115df53e04bd4a81f775b80a63451); [NHM specimen discussion](https://www.nhm.ac.uk/discover/giant-and-colossal-squid-revealing-secrets-largest-invertebrates.html) | Retain. The apparent BY scan is a LEGO squid, confirmed visually. Other ready models are artist meshes; museum specimen pages did not yield a permitted complete 3D specimen. |
| Very Large Telescope Mirror | Sketchfab `VLT mirror`, `VLT Unit telescope`; [ESO unit-telescope model](https://eso.org/public/products/models3d/3dmodel_002/) | Retain. A real agency model lead exists, but its page/download could not be retrieved here (503/cache failure). An isolated, more detailed mirror was not verified. A broader telescope assembly also cannot simply be scaled as the mirror diameter. |
| Boeing 747-8 | Sketchfab `Boeing 747 scan`; [Creaform's Lufthansa 747-8 scanning case study](https://www.creaform3d.com/en/resources/blog/lufthansas-jumbo-747-8-digitalized-18-hours) | Retain. Actual scanning exists, but the case study provides no permitted downloadable full exterior dataset. No source-verified scan improvement over the current 747-8 import obtained. |
| Hyperion | Sketchfab `redwood scan`; [Muir Woods base scan](https://sketchfab.com/models/a779106caffd475fa910bfa424e30bde), [Eldridge scan](https://sketchfab.com/models/5f61ba354d964a889629a3e89051522a); targeted lidar search | Retain. Permitted scans found were bases, bark or truncated trunks rather than complete coast-redwood crowns. Eldridge has NC-ND terms. No complete suitable tree dataset obtained; do not extend a partial trunk into an invented tree. |
| Gateway Arch | Sketchfab `Gateway Arch`, `Gateway Arch scan`; [St. Louis scan](https://sketchfab.com/models/5015279eea634a0aa2822103c8e52fcd) | Retain. The preview is a broad low-detail city scene with the arch a small part. Its description does not establish capture/measurement provenance, and it was not a clear upgrade to the current calibrated arch exterior. No city mesh downloaded. |
| Hoover Dam | Sketchfab `Hoover Dam`, `Hoover Dam scan`; [home-video reconstruction](https://sketchfab.com/models/3a19a6a0344141d9bfe9ec7c3171566c), [Google Maps extraction](https://sketchfab.com/models/e253f88e7d82451a8c93554b67faba99), USGS lidar references | Retain. Home-video coverage does not establish full foundation-to-crest geometry for the item's structural-height definition. Google-derived imagery/geometry has no verified upstream redistribution grant from Google. No suitable calibrated dam surface extracted from public lidar. |
| Hindenburg | Sketchfab `Hindenburg`; Zeppelin-museum reconstruction and model searches | Retain the current licensed import and its already-patched tail. No better publicly reusable full source-data model obtained; historical display/interior reconstructions do not provide the full exterior. **Existing plus signs are preserved.** |
| Titanic | Sketchfab `Titanic`; museum/scan searches; current GLB material and CPU visual inspection | Retain. No permitted measured full intact ship model found. **The current upper hull already renders black**; its black material includes `Color_009` with RGB `[0,0,0]`, and the lower hull is red. No recoloring is needed. CPU proof is supplied. |
| Arecibo Telescope | Sketchfab `Arecibo`; [collapsed telescope reconstruction](https://sketchfab.com/models/a6a84919914c4cb194ef43b614308036), targeted point-cloud search | Retain. The available reconstruction explicitly uses low-resolution drone footage and depicts the collapsed telescope. It is not a better model of the current intact reflector example, and the original footage rights were not established. |
| Ever Given | Sketchfab `Ever Given`; ship model/scan search and [artist project](https://www.thesittinghun.com/projects/freeing-the-ever-given) | Retain. LEGO/artist reconstruction or client work rather than a permitted real scan/shipyard dataset. No eligible full exterior source established. |
| Prelude FLNG | Sketchfab `Prelude FLNG`; [J3D technical visualization](https://www.j3d.co.uk/index.html), commercial model search | Retain. Client engineering/visualization work and paid artist models do not supply an openly reusable measured mesh. No permitted public full geometry obtained. |
| FAST Radio Telescope | Sketchfab `FAST telescope`; exact telescope model search | Retain. Relevant detailed model leads were commercial illustrations, not a permitted public scan or measured panel dataset. Do not invent a new reflector/panel layout. |
| Golden Gate Bridge Main Span | Sketchfab `Golden Gate Bridge scan`; [south-west pillar scan](https://sketchfab.com/models/1b99d26280d14dbc9af585988cf7c0ef), [walking-deck fragment](https://sketchfab.com/models/5ab9ad84c07948d1bde691cb4772ebab); [OpenTopography collection](https://portal.opentopography.org/datasetMetadata?otCollectionID=OT.112012.26910.1) | Retain. Handheld scans cover fragments, not the full main span (one is also NC-SA). The cited NCALM terrain area is northwest of the bridge, not a full bridge scan. A USGS published lidar figure is a possible future lead, but no complete, licensed, renderable main-span subset was obtained in this review. |
| Football Field | Sketchfab `football field scan`; inspected existing Milton Frank registry scan and runtime selection | Retain the current runtime field. `models.js` selects `proceduralLength` before registry matches; the stored `sketchfab-football-field` GLB is therefore **not the active explorer model**. New scan hits did not establish a clearer, correctly calibrated NFL field. No runtime override edited. |

## Platelet data scope evidence

The source [platelet-em description](https://bio3d-vision.github.io/platelet-description.html)
identifies human SBF-SEM data with approximate voxel spacing 40 × 10 × 10 nm.
Both original instance-label volumes were decoded using the published RLE
convention. All platelet-sized instances meet an image boundary. The largest
fully interior labeled fragment has 592 voxels and extents only
0.08 × 0.25 × 0.20 µm; presenting it as a 2.5 µm platelet would be wrong.

The later [dense-cell original archive](https://leapmanlab.github.io/dense-cell/)
was also checked. The test label volume has shape 121 × 609 × 400; unioning its
semantic classes produces one connected foreground component spanning both
z boundaries. **That does not prove that the image contains no whole cells**;
it means its semantic labels cannot directly isolate one complete cell without
additional segmentation. No such segmentation or invented boundary was made.

Raw archives remain outside the repository. `research/platelet-sources.json`
pins their URLs, byte counts and SHA-256 values. `platelet-boundaries.json` and
`platelet-dense-components.json` contain the numeric scope checks.

## Checks and limitations

- `node --test tests/*.test.cjs tests/*.test.mjs`: **236 passing**.
- `./venv/bin/python -m unittest discover -s tests -p 'test_*.py'`:
  **161 run, OK, one existing skip**. Existing NumPy deprecation and SQLite
  ResourceWarnings remain. The original earth3d delivery test now follows an
  item's active replacement, and its exact-sphere test covers only the remaining
  spherical illustrations; the photoscan is not forced into an ideal sphere.
- `node scripts/audit_upgrade3d_models.mjs`: vendored production GLTFLoader
  loads the final asset; registry, handoff and file hashes agree; exact resting
  geometry is **1.0000×**, within 0.6–1.3×. Textures are stub-decoded in this
  loader audit and reviewed separately in CPU images. See `loader-audit.json`.
- `node content/visualizations/models/validate-models.cjs <cached validator>`:
  **all 202 current GLBs have zero errors**. The replacement has zero warnings.
  Existing warnings remain in nine unchanged assets. `validation.json` also
  picks up the two existing clock/deck imports absent from its prior snapshot;
  those assets were not edited. Full output: `full-validation.log`.
- `python3 scripts/fetch_model_assets.py --verify`: **202 self-contained GLBs /
  212 exact-name matches**, pass.
- `python3 scripts/bump_versions.py --check`: **zero stale references**.
- `git diff --check`: pass.

Chromium/model_lab and git commit attempts were **not retried**, as expressly
instructed by the lead's known-sandbox-limits section. Changes are uncommitted
for the lead. Browser/rest/rotated/explorer/mobile validation remains pending
outside this sandbox; CPU preview approval is not a substitute for it.

## Lead integration and review

The registry already contains the replacement in this worktree. To resolve a
registry merge conflict, keep main's registry and re-register the supplied entry
against the new GLB; the entry's `replaces` removes the old model. The old
unreferenced GLB is intentionally deleted. No dataset changes are needed.

```sh
python3 scripts/register_model.py \
  handoff/upgrade3d/upgrade3d-basketball-scan.entry.json \
  content/visualizations/models/upgrade3d-basketball-scan.glb

node scripts/model_lab.cjs shot /tmp/upgrade3d-webgl Basketball --views rest,side --bg dark
node scripts/model_lab.cjs explorer /tmp/upgrade3d-webgl Basketball
node scripts/model_lab.cjs audit
node scripts/model_lab.cjs mobile /tmp/upgrade3d-mobile
```

The source preparation command is in
`content/visualizations/models/sources/upgrade3d-basketball-scan.md`.
Reproduce the CPU comparisons by first retrieving the previous GLB:

```sh
git show f5f8f733b79465268e499bdce4220f75a47d8afb:content/visualizations/models/earth3d-basketball.glb > /tmp/upgrade3d-old-basketball.glb
./venv/bin/python scripts/preview_upgrade3d_cpu.py --old-model /tmp/upgrade3d-old-basketball.glb
node scripts/audit_upgrade3d_models.mjs
```

**Open questions:** only whether the lead prefers the real worn scan after
production lighting/mobile review. The species-unverified Rafflesia and the
licensed but incomplete biological/telescope candidates were not promoted.
Commit on `codex/upgrade3d` when reviewed, ending the commit message with
`Co-Authored-By: Codex <noreply@openai.com>`. Do not push or change branches.
