# Flybrain handoff

Branch: `codex/flybrain`. No push, merge, rebase or other branch changes.

**Commit blocked by the sandbox.** The completed files are present in this
worktree, but `git add` failed before staging with:
`Unable to create '.../.git/worktrees/flybrain/index.lock': Operation not permitted`.
The approval policy is `never`, so I could not request an escalation or create
the requested commit. No Git configuration or permissions were changed.
In the lead's environment, stage the files listed below and commit with the title
`Add calibrated FlyWire fruit fly brain skeleton model` and final trailer
`Co-Authored-By: Codex <noreply@openai.com>`.

```sh
git add content/visualizations/models.json \
  content/visualizations/models/fruit-fly-brain-flywire.glb \
  content/visualizations/models/sources/flybrain.md \
  content/visualizations/models/sources/flybrain \
  scripts/build_flybrain_model.py tests/test_flybrain_model.py handoff/flybrain
git commit -m 'Add calibrated FlyWire fruit fly brain skeleton model' \
  -m 'Co-Authored-By: Codex <noreply@openai.com>'
```

Do not stage the pre-existing untracked `venv` symlink or dataset files.

## Delivered

- Registered `fruit-fly-brain-flywire` for the exact new item `Fruit Fly Brain`.
  Final asset: **2,536,220 bytes**, 30,768 envelope triangles, six draw calls,
  **2,200 real neurons / 137,209 simplified neuronal path segments**. No texture,
  external file, decoder, fabricated fibre, synapse or activity is required.
- Blue optic, amber central, violet visual projection and pink visual centrifugal
  superclasses from the **published 2024 annotation supplement**. Sampling visits
  both sides and many cell types; it is not a population-proportional census.
- Translucent context is an explicitly labeled **sampled-skeleton density
  envelope**, not a segmented brain surface. Paths depict morphology; crossing
  lines do not assert synaptic contacts. The full synaptic adjacency graph is
  not bundled. Short twigs are omitted; retained chains are simplified.
- `scripts/build_flybrain_model.py`: verifies source checksums, streams the full
  Parquet, selects IDs, simplifies real trees and writes the calibrated GLB and
  entry JSON. `sources/flybrain/` retains the 2,200 selected IDs/classes/sides,
  processing metadata and the separately deposited license metadata.
- Complete provenance and rebuild commands:
  [`../../content/visualizations/models/sources/flybrain.md`](../../content/visualizations/models/sources/flybrain.md).
  Re-register on main with the included **final**
  [`fruit-fly-brain-flywire.entry.json`](fruit-fly-brain-flywire.entry.json).
  This is a new model; there is no `replaces` entry.

## Dataset dependency — coordinate with the items job

**Recommended value: `0.0008 m` (approximately 800 µm).**

Define this as the approximate lateral span of reconstructed neuronal processes
including both optic lobes and lamina in the FlyWire v783 specimen, rather than
an anatomical membrane diameter. It is measured directly from the cited source
skeleton coordinates: retained paths span 802.55 µm laterally; envelope-inclusive
production-loader bounds span 805.97 µm. It should not be described as a universal
fruit-fly brain size. Source: <https://zenodo.org/records/10877326>.

The model preserves µm coordinates and includes a **100 µm ruler**. Its registry
`reference_size` is **800**. Attaching it unchanged to a 500/600 µm item would
rescale its physical coordinates and make the ruler incorrect. Agree on this
definition/value with the items job before integration.

Suggested factual description for that job to adapt to its plaque style:

> The FlyWire reconstruction maps an adult female fruit fly's brain, including
> its two optic lobes. This visualization samples 2,200 reconstructed neurons
> across an approximately 800-micrometre lateral span. Colours distinguish broad
> anatomical classes. The paths are simplified neuronal morphologies, not the
> complete synapse graph; crossing fibres do not necessarily connect.

Schlegel et al. (2024) describes the whole-brain resource and annotation hierarchy:
<https://doi.org/10.1038/s41586-024-07686-5>. Co-cite Dorkenwald et al.:
<https://doi.org/10.1038/s41586-024-07558-y>.

**No dataset, frontend export, image or plaque change is committed.** I first
added a temporary source-YAML item and attempted the prescribed Length-only
rebuild. The existing builder failed at `build_dataset.py:561`,
`KeyError: 'symbol'`, before merging any outputs. I restored that YAML exactly
and used temporary JSON/frontend preview fixtures instead, also restored exactly.
The registry therefore intentionally depends on the new item from the items job.
Before that integration, ordinary registry verification reports the missing exact
dataset name. `with_preview_item.py` can supply the temporary item during review,
restoring the exact original bytes even if its child command fails.

## Licenses — exact scope

The general <https://home.flywire.ai/guidelines> page says **CC BY-NC 4.0** for
the public release. I did **not** import direct FlyWire/Codex meshes or relabel
that general release CC BY.

The actual skeleton source is the authors' **separately deposited**
<https://zenodo.org/records/10877326>, explicitly **CC BY 4.0** in the live
Zenodo API metadata. The 2024 Nature annotation supplement is likewise covered
by the article's explicit **CC BY 4.0** grant, without a contrary credit line
found on the supplement. Those are the grants relied upon for this adaptation;
the general FlyWire NC terms and this distinction are recorded in provenance.
No GPL/uncertain template mesh or NC/ND asset is included.

The complete 5.4 GB skeleton input passed the publisher's MD5
`a4c104776f33ec539ef859064c4de3df`. The earlier attempt's assembled file was
incomplete: I rebuilt a new copy from its staged chunks plus the missing tail
in `/tmp`, verified it, and processed that verified copy. No earlier scratch
file was edited. The 2024 annotations were freshly downloaded and SHA-256 pinned.

## Verification and visual review

- `node --test tests/*.test.cjs tests/*.test.mjs`: **209 passing**.
- `./venv/bin/python -m unittest discover -s tests -p 'test_*.py'`:
  **79 tests, OK, one existing skip**. Six new tests cover coordinate scale and
  handedness, forks/components, missing parents, cycles, RDP bends, reproducible
  sampling and fragment exclusion. Existing SQLite ResourceWarnings remain.
- Ran the requested full Khronos validator command against every registered
  GLB. **The new asset has zero errors, warnings, infos or hints**; see
  [`validation.json`](validation.json). The generated global validation file
  was restored to avoid unrelated changes.
- `node handoff/flybrain/audit.mjs` loads the actual GLB using the site's
  **vendored production GLTFLoader** under Node, measures per-vertex bounds,
  applies the entry's resting Euler pose and 800 µm normalization, and checks
  the 0.6–1.3 rule. **Rest extent: 0.979×**; see
  [`loader-audit.json`](loader-audit.json). This is not a GPU/frame-rate test.
- Asset verification with the temporary exact-name fixture confirmed the new
  asset's hash/stats and absence of a decoder. Its overall command still exits
  nonzero for the known, unchanged **Kenney license checksum mismatch**.
- Content-hash version check: **0 stale references**. No JS/CSS was changed.
- `git diff --check`: clean.

**Browser limitation:** `node scripts/model_lab.cjs shot ... --views rest,side,top
--bg dark` was attempted. Chromium dies at startup with
`bootstrap_check_in ... MachPortRendezvousServer ... Permission denied (1100)`.
The sandbox's approval policy is `never`, so there is no authorized escalation.
The full audit/production explorer has the same browser prerequisite. No
production screenshot, touch, GPU, performance or hardware result is claimed.

I inspected software renders of the **actual decoded final GLB geometry** in
rest, side, top and light-background views. These are clearly marked as software
reviews and are included for convenient inspection:

- [`reviews/rest.png`](reviews/rest.png)
- [`reviews/side.png`](reviews/side.png)
- [`reviews/top.png`](reviews/top.png)
- [`reviews/rest-light.png`](reviews/rest-light.png)

The first unrestricted extraction was ~12 MB. I tightened per-neuron branching
budgets and coarsened only the faint envelope to produce the final 2.54 MB asset,
then visually inspected all views and checked the light palette. Real coordinate
positions, bilateral structure and major tracts remain. Software reviews do not
reproduce Three.js lighting, GPU depth handling or SVG label culling. Please
complete the production browser review in the lead's environment before shipping:

```sh
./venv/bin/python handoff/flybrain/with_preview_item.py -- \
  node scripts/model_lab.cjs shot /tmp/flybrain-lab 'Fruit Fly Brain' --views rest,side,top --bg dark
./venv/bin/python handoff/flybrain/with_preview_item.py -- \
  node scripts/model_lab.cjs explorer /tmp/flybrain-explorer 'Fruit Fly Brain'
./venv/bin/python handoff/flybrain/with_preview_item.py -- \
  node scripts/model_lab.cjs audit
```

## Environment

Used `./venv/bin/python` and `node`. Installed **pyarrow 26.0.0 only into
`/tmp/flybrain-deps`** with `--target --no-deps`; the shared venv was not modified.
Reused the pre-existing temporary Khronos validator installation. No secrets,
token, private user information or raw multi-gigabyte source data were committed.
The original untracked `venv` symlink was left as found.
