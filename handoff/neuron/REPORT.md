# Neuron job handoff — 2026-10-15

Branch: `codex/neuron`. **Implementation is ready but uncommitted:** the sandbox
denied creation of this worktree's Git index lock, despite the advertised Git
metadata writable root. `git add` failed before staging anything. No push or
branch integration was performed. No dependencies were installed. The untracked
`venv` symlink belongs to the provided environment and is not committed.

Commit blocker:

```text
fatal: Unable to create
'/Users/ethan/Documents/GitHub/universe-scales/.git/worktrees/neuron/index.lock':
Operation not permitted
```

The current approval policy is `never`; no escalation or alternate Git
metadata workaround was attempted. Run [commit.sh](commit.sh) outside the
sandbox to stage exactly this job's files and create the requested local
commit (including the required Codex co-author trailer). It checks that the
current branch is `codex/neuron`, excludes the environment's `venv` symlink,
and does not push or change branches.

## Delivered

- Replaced the runtime stylized procedural neuron with **NeuroMorpho.Org
  NMO_109111 / BC140212B_21**, Feldmeyer archive: a real, local-projecting,
  non-Martinotti-like rat layer-4 barrel-cortex interneuron.
- The archive explicitly classifies **dendrites and axon complete**, with
  measured diameters. The entire archived arbor is retained: **65,332 source
  nodes, 65,329 process edges, 785 maximal branches**, without a spatial crop.
  The two extra SWC soma edges are represented by the soma surface instead.
- Continuous smooth-normal tubes retain true-scale SWC radii with documented
  interpolation error limits (0.35 µm centerline; 0.08 µm radius), without a
  visibility thickness multiplier. Irregular soma shape comes from the original
  traced contour; its unmeasured depth is an explicitly authored rounded loft.
- Copper axon, jade dendrites, pale soma; three sparse upright labels. No
  invented myelin, spines, nucleus or terminal boutons.
- A glowing **action-potential annotation** starts at an assumed proximal AIS
  location and follows original axonal tree distances through branches. Vertex
  emission plus a soft screen-sized halo makes the wave visible. This uses
  `registerAnimation`, GLTF extras and the existing reduced-motion/visibility
  handling. Speed, width and AIS location are illustrative, not recordings.
- The 2,694,356-byte GLB has 127,038 triangles, no textures, external resources
  or decoder dependency. It uses four draw primitives: soma, axon, dendrites,
  electrical halo. The halo opts out of whole-model hover highlighting through
  `extras.hoverOverlay: false`, so hover cannot reveal the entire inactive halo.
- Removed the Neuron procedural metadata override that otherwise takes
  precedence over registry entries. The legacy procedural constructor remains
  as a test fixture; it is not selected for the Length item.
- Offline source derivative, original soma outline, metadata and download
  hashes are bundled under `content/visualizations/models/sources/neuron/`.
  The GLB builder is deterministic and works without network access.

The earlier Allen dendrite-only crop documented in this branch was a staged
experiment, not the registered runtime model. Its noncommercial terms did not
meet the brief. MouseLight was also excluded after its source terms showed
CC BY-NC. NeuroMorpho's own terms explicitly license its material CC BY 4.0.

Source/provenance and all required credits:
[neuron-model.md](../../content/visualizations/models/sources/neuron-model.md).
Original lab/paper: **Emmenegger, Qi, Wang & Feldmeyer (2018)**,
[doi:10.1093/cercor/bhx352](https://doi.org/10.1093/cercor/bhx352).
Repository: **NeuroMorpho.Org (RRID:SCR_002145)**, plus Tecuatl, Ljungquist &
Ascoli (2024), [doi:10.1096/fba.2024-00048](https://doi.org/10.1096/fba.2024-00048).
[Source reuse terms](https://neuromorpho.org/useterm.jsp) were opened 2026-10-15.

## Required dataset change — items job / lead

**Apply this before publishing the registered model.** I did not edit the
items job's dataset, frontend exports or images. Keeping the old 100 µm value
would make the renderer shrink the reconstruction eightfold, even though a
normalized size audit could still pass. The `presentation.reference_size` is
**800 µm**, not 100 µm.

Replace the existing `Neuron` entry's value, source and description exactly:

```yaml
name: Neuron
value: 8e-4
source: https://neuromorpho.org/neuron_info.jsp?neuron_name=BC140212B_21
description: >-
  A reconstructed rat cortical interneuron spans roughly 0.8 millimeters
  along its original vertical axis, including its dendrites and local axonal
  arbor. The explorer shows NeuroMorpho.Org NMO_109111 (BC140212B_21), a
  layer-4 barrel-cortex interneuron from Emmenegger and colleagues. The
  archive classifies the dendrites and axon as complete, although this
  brain-slice preparation may have severed some biological processes. Its
  full traced geometry is retained. The electrical glow illustrates an
  action potential starting in the proximal axon and spreading through its
  branches; its position, speed and width are explanatory, not measured
  for this cell.
```

Basis: the exact archived numeric coordinates yield **571.67 × 791.52 ×
437.20 µm**; the approximate 0.8 mm value rounds the original Y extent.
This is one reconstruction's spatial span, not total cable length, axon path
length, a typical soma diameter, or a claim about all neurons. The longest
traced axon root-to-tip path is 965.470 µm. Keep `name: Neuron` for existing
deep links and exact registry matching. Rebuild Length only with
`./venv/bin/python -m scripts.dataset.rebuild_dimension length`.
If main has a separate Neuron plaque, align its opening definition with this
description; there is no separate Neuron plaque in this worktree.

## Integration instructions

1. Bring over this branch's implementation/source files and remove the old
   Neuron procedural override in `organelleModelMetadata`. That removal is
   essential: the procedural map otherwise shadows `models.json`.
2. The final entry copy is
   [neuromorpho-feldmeyer-neuron-109111.entry.json](neuromorpho-feldmeyer-neuron-109111.entry.json).
   It includes `replaces: pyramidal-neuron-action-potential`, the old runtime ID.
   The old procedural model has no GLB for the registrar to delete.
   If main separately registered the earlier Allen crop, remove that exact
   Neuron match before registering; do not retain two registry matches.
3. Re-register the entry with the included GLB using `register_model.py`, apply
   the dataset change above, then run `bump_versions.py` on main after combining
   the other jobs. Hash changes to shell/import files in this branch are solely
   produced by that script.
4. Run the browser review below before deployment. This branch is **not
   visually certified in the production renderer** because Chromium cannot
   launch under the current sandbox.

## Verification completed

- `node --test tests/*.test.cjs tests/*.test.mjs`: **214 passed**.
- `./venv/bin/python -m unittest discover -s tests -p 'test_*.py'`:
  **78 run, OK, one existing skip**; existing SQLite ResourceWarnings remain.
- New Python checks prove every source process edge appears once, all original
  centerline/radius samples stay within simplification budgets, source tree
  distance is conserved, and tube radii/normals are correct.
- New Node checks cover launch/travel/repeat timing, clone-isolated shader
  uniforms, pulse-halo alpha, registry precedence, and actual production
  `GLTFLoader.parseAsync` loading of this binary. It confirms `_PATH_DISTANCE`
  survives as `_path_distance` and dispatches through the existing wave/
  animation registry with the glTF root nested inside a cloned scene.
- `node content/visualizations/models/validate-models.cjs
  /Users/ethan/.npm/_npx/d659fe5fabadba55/node_modules/gltf-validator` completed.
  **Neuron: zero errors, zero warnings.** The prepared global validation
  report adds only this model's record, preserving baseline records for other
  jobs. A standalone neuron report is [validation.json](validation.json).
- `python3 scripts/fetch_model_assets.py --verify`: the new GLB passes bytes,
  SHA-256 and decoder/resource checks; the command still exits nonzero on
  the pre-existing `licenses/kenney-food-kit.txt` provenance checksum mismatch.
- `python3 scripts/bump_versions.py --check` and `git diff --check`: pass.
- Direct GLB geometry audit confirms **571.889 × 791.786 × 437.424 µm** mesh
  bounds (including true tube surfaces). CPU projection at the resting pose
  gives **1.170×** the 800 µm reference; layout width factor is 1.25. This is
  an orthographic estimate, not a successful `model_lab audit` result.
- No Python/Node packages were installed; the existing temporary npm cache
  supplied the Khronos validator.

## Visual inspection and blocked browser checks

Attempted production commands:

```sh
node scripts/model_lab.cjs shot /tmp/neuron-review/t0 Neuron --views rest,side --bg dark --time 0
node scripts/model_lab.cjs audit
node scripts/model_lab.cjs mobile /tmp/neuron-mobile
```

All fail at browser launch, before loading the site:

```text
FATAL:base/apple/mach_port_rendezvous_mac.cc:155
bootstrap_check_in org.chromium.Chromium.MachPortRendezvousServer...
Permission denied (1100)
```

Approval policy is `never`, so there was no permitted escalation. No production
screenshots, GPU shader compilation, actual mobile interaction, measured frame
rate or browser label-collision verification is claimed. Logs are in
`/tmp/neuron-audit.log`, `/tmp/neuron-mobile.log`; a launch-error excerpt is
also included in [browser-blocked.txt](browser-blocked.txt).

I rendered and **looked at all six** offline CPU geometry previews from the
final GLB. These exposed a poorer initial diagonal pose and nearby callouts;
I rotated the resting pose to expose the long collateral and moved the axon
callout away from the dendrites. They show actual mesh triangles at t=0,
1.2, 2.8 and 4.8 s, side-on, and at a 393 px canvas width. The moving
membrane highlight follows different branches over time. These previews use
approximate lighting and omit the GPU point halo; they are explicitly labeled
as geometry previews, **not browser screenshots or mobile validation**.

Handoff copies are in [previews/](previews/); originals:

- `/tmp/neuron-cpu/neuron-rest-0.png`
- `/tmp/neuron-cpu/neuron-rest-1.2.png`
- `/tmp/neuron-cpu/neuron-rest-2.8.png`
- `/tmp/neuron-cpu/neuron-rest-4.8.png`
- `/tmp/neuron-cpu/neuron-side.png`
- `/tmp/neuron-cpu/neuron-small.png`

Recreate with `./venv/bin/python scripts/preview_neuron_cpu.py`.

Required follow-up outside the sandbox, after the dataset update:

```sh
node scripts/model_lab.cjs shot /tmp/neuron-rest Neuron --views rest,side --bg dark --time 0
node scripts/model_lab.cjs shot /tmp/neuron-pulse-early Neuron --bg dark --time 1.2
node scripts/model_lab.cjs shot /tmp/neuron-pulse-mid Neuron --bg dark --time 2.8
node scripts/model_lab.cjs shot /tmp/neuron-pulse-late Neuron --bg dark --time 4.8
node scripts/model_lab.cjs shot /tmp/neuron-light Neuron --views rest,side --bg light --time 2.8
node scripts/model_lab.cjs explorer /tmp/neuron-explorer Neuron
node scripts/model_lab.cjs explorer /tmp/neuron-small-explorer Neuron --size 393x852
node scripts/model_lab.cjs labels Neuron --views rest,side
node scripts/model_lab.cjs audit
node scripts/model_lab.cjs mobile /tmp/neuron-mobile
node scripts/model_lab.cjs performance Neuron --mobile
```

Also inspect this exact item on a touch device/emulated mobile page: rotate it,
watch the halo traverse the fine axon, and enable reduced motion. The generic
mobile lab primarily exercises other items; running it alone does not certify
this neuron's mobile appearance.

## Scientific limits / open questions

- “Complete” is the archive's integrity classification for this reconstruction.
  Slice-based data cannot prove the entire living axon survived. If the owner
  requires a verified uncut whole-brain cell, this specimen does not establish
  that stronger claim; obtain an explicitly permissive whole-brain dataset.
- The soma contour is observed, while its depth is a proxy. Exact volumetric
  soma surface data were not present in the source.
- AIS position and all pulse display parameters are authored. The animation is
  educational, not a cell-specific electrophysiology simulation.
- True-caliber axons are very fine on small screens. The electrical halo helps
  only the active wave; do not inflate the whole anatomy to conceal that.
- The asset meets the byte budget but has 127k triangles. Mobile performance
  and visual clarity must still be measured in the real renderer.
