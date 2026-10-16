# bio3d handoff — 2026-10-16

Implemented **nine** of the 22 requested Length items with CC0 structural-coordinate assets. All are registered on `codex/bio3d`, with individual provenance pages, pinned offline inputs and final `*.entry.json` files in this directory. No existing models were replaced; these entries do not need a `replaces` field.

No `dataset/raw/legacy_yaml/length.yaml`, dataset exports, `data/`, `images/`, runtime JS or CSS were edited. No packages were installed. The pre-existing untracked `venv` symlink was left alone. Work remains **uncommitted** as requested for the known sandbox restriction. `./handoff/bio3d/commit.sh` prepares the scoped local commit outside the sandbox, with the required Codex coauthor trailer; it never pushes or changes branches.

## Assets

| Item | Structural source | GLB size | Triangles | Rest geometry / catalog value |
| --- | --- | ---: | ---: | ---: |
| Graphene Layer Spacing | COD 9011577 | 18 kB | 672 | 1.262× |
| Nucleosome | 1KX5 | 1101 kB | 54,972 | 1.105× |
| Tobacco Mosaic Virus | 2TMV | 964 kB | 50,501 | 0.945× |
| Ribosome | 4V88 | 1083 kB | 54,770 | 0.984× |
| Buckminsterfullerene | 5ET3 | 78 kB | 3,600 | 1.005× |
| Actin Filament | 6BNO | 1097 kB | 54,940 | 1.203× |
| Microtubule | 6DPU | 1097 kB | 54,872 | 1.244× |
| SARS-CoV-2 Spike | 6VXX | 1100 kB | 54,886 | 0.816× |
| Nuclear Pore Complex | 7R5K | 1032 kB | 54,216 | 1.185× |

The last column is a browser-free orthographic geometry check using the actual vendored GLTFLoader and the registry rest pose. It is **not** the production `model_lab` perspective size audit. All nine also pass the configured layout-width bound. Native extents and loader results are in [loader-audit.json](loader-audit.json).

One GLB unit is one nanometre. Atomic coordinates are converted from angstroms by dividing by ten, then rigidly positioned. `presentation.reference_size` explicitly represents the current item's value in nm; there is no bounding-box fit. **If the items job changes a value, update this reference to the same value in nm before integration**, otherwise the runtime will rescale the coordinates.

## Scientific choices and limitations

- **C60:** actual 60C ligand from 5ET3; 60 sites and 90 bonds, each site of degree three. Thin bond tubes mark nuclear positions. This respects the existing nucleus-to-nucleus cage definition rather than silently adding an electron-cloud diameter.
- **Graphite spacing:** natural-crystal cell from COD 9011577, Trucano & Chen (1975). The two AB-stacked hexagonal windows retain c/2 = 0.33555 nm, consistent with the approximate 0.335 nm item. A tick-ended ruler and runtime label identify the plane separation. The small sheet windows keep lateral context within the size rule.
- **Nucleosome:** both 147-base DNA strands and all eight histones of 1KX5, including resolved tails. Gold uniquely identifies DNA; histone chains use other colors. The 11 nm item measures the disc, with tails extending beyond it; the default pose keeps the full structure within the framing limit.
- **Spike:** the complete deposited 6VXX closed trimer and deposited glycan residues. About 16.2 nm of resolved ectodomain is retained against the generic 20 nm spike marker. The flexible stalk, anchor and unresolved glycan canopy are absent. The display heading qualifies it as a resolved ectodomain.
- **Actin:** a flat-cut 7 nm axial window through the actual 6BNO rabbit filament. Its structural width is about 8.6 nm; the generic catalog diameter remains 7 nm. It shows partial neighboring subunits, not a full helical crossover. Cuts are labeled in the heading/note.
- **Microtubule:** a flat-cut 20 nm axial window in a reconstructed **14-protofilament** 6DPU GMPCPP lattice. Alpha/beta colors are teal/violet. Rigid matching of deposited A→C and A→K C-alpha coordinates gives lateral and longitudinal fits below 0.004 Å RMSD. Seam-specific conformation is not known. The outer envelope is about 29.9 nm, wider than the generic 25 nm marker; native dimensions are retained and the display heading states 14 protofilaments. The reconstruction method is also described by [Sahoo & Hanson (2025)](https://doi.org/10.1093/pnasnexus/pgaf202); their displayed rotation/rise labels are transposed, so the builder derives the transforms directly from coordinates.
- **Ribosome:** author-defined assembly 1 of 4V88, a single yeast 80S ribosome with deposited Stm1. The deposited asymmetric unit has two particles; only one biological particle is rendered. Gold uniquely identifies RNA; protein chains use other colors. Native envelope is about 29 nm.
- **NPC:** all eight deposited assembly operations of constricted human pore 7R5K. This is an integrative cryo-ET/prediction-based scaffold, shown with a deliberately coarse C-alpha envelope. Its central channel and eightfold organization remain open. Disordered barrier, membranes and unresolved basket/filaments are absent. The full lateral envelope including protrusions is about 146.7 nm versus the approximate 120 nm catalog marker.
- **TMV:** deposited 2TMV protein/RNA subunit and deposited screw symmetry, repeated into a representative 300 nm rod. The central channel follows the coordinates. End planes are authored cuts through the repeated lattice, not experimentally determined virion end structures.

Surface radius, smoothing, grid spacing and color are display choices, individually recorded in each entry. These are molecular display envelopes, not measured electron-density maps, solvent-accessible surfaces or hard boundaries. Surfaces are simplified with glTF Transform 4.5.0 and outward, counterclockwise normals; collapsed opposing duplicate faces are removed so tiny cavities cannot leave canceled normals. GLBs contain no decoder extensions or external resources.

PDB CC0 rights were verified on the [official wwPDB usage policy](https://www.wwpdb.org/about/usage-policies); COD CC0 rights were verified on the [official COD information-card footer](https://www.crystallography.net/cod/9000046.html). Each source page links its original structure and primary paper. Retained NPZ coordinate files, assembly operations, publication metadata and original/derivative hashes live in `content/visualizations/models/sources/bio3d/`.

## Visual review

Looked at all nine final assets in rest **and** side CPU previews, iterating on winding, normals, surface detail, color separation, rod reconstruction, cut segments and framing. Previews read the final GLBs and use the same Euler ordering as Three.js. They use orthographic projection and approximate triangle lighting; their faceting is not a WebGL-material assessment.

- [Rest contact sheet](previews/contact-rest.jpg)
- [Side contact sheet](previews/contact-side.jpg)
- Individual 1000×800 PNGs: `previews/<model-id>-rest.png` and `-side.png`.
- [CPU geometry audit](previews/geometry-audit.json)

Chromium / production screenshots, actual explorer navigation, hover, perspective size audit and mobile checks remain **pending**. The job brief explicitly says Chromium is sandbox-blocked and not to spend effort retrying it, so no browser launch was attempted in this session. CPU previews are labeled accordingly.

## Verification

- `node --test tests/*.test.cjs tests/*.test.mjs`: **224 passing**.
- `./venv/bin/python -m unittest discover -s tests -p 'test_*.py'`: **90 run, 89 passing, one existing skip**. Includes nine new meaningful regressions for source pins, C60 topology, one-particle ribosome selection, full NPC assembly, rigid tubulin transforms, graphite plane spacing, outward winding, cut positions, collapsed faces and final physical calibration.
- `python3 scripts/fetch_model_assets.py --verify`: **73 self-contained GLBs, 83 exact-name matches verified**.
- `python3 scripts/bump_versions.py --check`: **0 stale references**. No app JS/CSS changes require cache-busting edits.
- `node scripts/audit_bio3d_models.mjs`: **all nine load through the actual vendored GLTFLoader and pass physical-rest/layout bounds**.
- Khronos glTF Validator **2.0.0-dev.3.10**: **all nine new GLBs have zero errors and zero warnings**. Targeted results: [gltf-validation.json](gltf-validation.json).
- The required full command `node content/visualizations/models/validate-models.cjs <cached-gltf-validator>` exits 1 because the existing **`em-mitochondrion-jurkat`** has **17 `ACCESSOR_VECTOR3_NON_UNIT` errors**. Its registry entry and SHA-256 are unchanged from HEAD (`eed2b81cd6cdab7732c045bdc0223d8dfa0ef7dee74dc2b42310baa4f41bda11`). This belongs to the mitochondrion job. Existing unrelated asset warnings are also retained. The refreshed full report is `content/visualizations/models/validation.json`.
- Baseline ResourceWarnings remain in the Python suite; scikit-image also reports NumPy shape-assignment deprecation warnings. Tests pass.

## Remaining 13 requested items

Quality was prioritized over count. These remain photo-only; this is not a claim that suitable sources do not exist:

| Items | Remaining sourcing work |
| --- | --- |
| Cell Membrane | Need a redistributable, calibrated lipid-bilayer coordinate/MD snapshot, including a thickness definition. No generic hand-built bilayer was registered. |
| Bacteriophage T4 | Need a defensible complete head/tail/fiber assembly and its calibration; isolated PDB components do not establish a whole virion. |
| Mimivirus | Need an envelope/capsid/fiber reconstruction matching the 600 nm definition; capsid-only coordinates would omit the measured fibers. |
| Human Platelet; Budding Yeast Cell; Chloroplast; Neutrophil; Paramecium | Need suitable whole-cell/organelle segmentation or specimen meshes with verified licenses, voxel calibration and representative size definitions. No such asset was selected in this batch. |
| Tardigrade; Dust Mite; Honeybee; Cat Flea | Need verified specimen geometry plus scale/measurement landmarks; no scan was approved in this batch. |
| Fruit Fly | Investigated and CPU-reviewed ETAIN's [adult female Drosophila CT scan](https://sketchfab.com/models/ad29b897bd2b4e27bb04ab9d31baa117). Official API confirms **CC BY 4.0**, downloadable, author **etainproject**. It was staged outside the repo and simplified for review. Public metadata lacks a physical voxel/model calibration; leg/wing span also differs from the item's 2.5 mm body-length definition. Not registered until a defensible body reference or scan calibration is supplied. Candidate UID: `ad29b897bd2b4e27bb04ab9d31baa117`. |

## Dataset changes

**None required for these nine entries.** Existing definitions/values remain unchanged. Exact-name matches and deep links are retained; display headings and notes qualify structural constructs and segment windows. The source notes explicitly state approximate generic dimensions versus actual modeled extents. If the owner wants a specific structural specimen/construct to replace a generic item definition, coordinate that decision with the items job and update the model's physical reference at the same time.

## Integrating on main

1. Copy each new GLB, its provenance page and the `sources/bio3d/` inputs; copy the builders, audit/preview scripts and tests.
2. Register each final JSON (all are additions):

   ```sh
   for entry in handoff/bio3d/*.entry.json; do
     model=$(basename "$entry" .entry.json)
     python3 scripts/register_model.py "$entry" "content/visualizations/models/$model.glb"
   done
   ```

3. Run `model_lab.cjs shot` for each exact item name in the table (`--views rest,side --bg dark`), inspect the shots, then `explorer`, whole-Length `audit` and `mobile`. Check the graphite ruler label, thin TMV rod, nucleosome tails, microtubule lumen and NPC channel at normal explorer size.
4. Resolve the independent mitochondrion normal errors with its owning job, rerun the full validator and commit the scoped changes. No push/merge/rebase was performed here.
