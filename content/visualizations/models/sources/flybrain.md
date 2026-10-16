# Fruit fly brain: real FlyWire neuronal paths

`fruit-fly-brain-flywire.glb` contains a reproducible sample of **2,200 real
FlyWire v783 neuronal skeletons**, not authored lookalike fibres. The four colours
encode the published superclasses: 1,000 optic (blue), 700 central (amber), 400
visual projection (violet), and 100 visual centrifugal (pink). Colour variation
within a superclass is aesthetic. Positions and branching come from the data.

This is a **morphology sample from a connectome**, not a visualization of the
complete synaptic adjacency graph. Line crossings do not imply synapses. No
pairwise synaptic edges, synapse dots, activity or information flow are invented.
The faint surface is an authored isosurface of the unsimplified sample's cable
density, **not a neuropil segmentation or a measured brain membrane**. No JRC2018,
navis-flybrains, Codex, or FlyWire API mesh is included.

## Primary sources and exact licensing

1. Schlegel, P., Yin, Y., Bates, A. S. et al. (2024), *Whole-brain annotation and
   multi-connectome cell typing of Drosophila*, Nature 634, 139–152.
   <https://doi.org/10.1038/s41586-024-07686-5>.
2. Dorkenwald, S. et al. (2024), *Neuronal wiring diagram of an adult brain*,
   Nature 634, 124–138. <https://doi.org/10.1038/s41586-024-07558-y>.
3. **Actual geometry source:** Schlegel and Jefferis, *Supplemental Files for
   Schlegel et al., Nature (2024)*, Zenodo record 10877326, version v2.
   <https://zenodo.org/records/10877326>.
   The deposit explicitly labels its skeleton coordinates **nanometres**, states
   that they were generated from LOD1 meshes and downsampled 2×, and identifies
   root IDs with release 783. Its current machine-readable license is
   `{"id":"cc-by-4.0"}`:
   <https://zenodo.org/api/records/10877326>.
   The file `sk_lod1_783_healed_ds2.parquet` is 5,355,543,468 bytes; publisher MD5:
   `a4c104776f33ec539ef859064c4de3df`. The complete locally reconstructed input
   was checked against that MD5 before extraction. The earlier partial staging
   file did not pass; it was not used as the final input.
4. **Actual annotation source:** the published paper's Supplementary Data 1:
   <https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-024-07686-5/MediaObjects/41586_2024_7686_MOESM5_ESM.tsv>.
   This uses the 2024 supplement, rather than the subsequently updated GitHub
   annotations. SHA-256:
   `30be6c73975a70c56d930e27911f36455d3886e15abf383b78edd2a5d679e0b6`.
   The paper's Rights and permissions grants CC BY 4.0, including material without
   a contrary credit line. No contrary license was found on this supplement.

**Scope of the license claim:** the general FlyWire guidelines at
<https://home.flywire.ai/guidelines> say **CC BY-NC 4.0** for the public release.
This project does not relabel that release CC BY. The imported files rely on the
**separate, explicit CC BY 4.0 grants on the authors' Zenodo skeleton deposit and
the published annotation supplement**. Direct meshes, Codex exports and template
meshes under other or uncertain terms were not imported. Checked 2026-10-15;
the selected Zenodo metadata is retained in
[`flybrain/skeleton-deposit-license.json`](flybrain/skeleton-deposit-license.json).
Credit the authors above and describe the simplification, sampling and envelope
when redistributing this adaptation. License text:
<https://creativecommons.org/licenses/by/4.0/> and `../licenses/CC-BY-4.0.txt`.

## Selection, geometry and calibration

- The selector excludes annotation rows with a nonempty `status`. Within each
  superclass it visits `(side, cell_type-or-cell_class)` groups in a deterministic
  hash order and takes neurons round robin until the quota is filled. The sample
  favours diversity, **not population-proportional sampling**; colour density
  cannot be interpreted as cell counts or connection strength.
- The complete source file has 139,273 skeleton groups. The paper reports 139,255
  connectome neurons. Those are distinct counts; this model claims only its 2,200
  selected, individually listed IDs, not equivalence between the two totals.
  See [`flybrain/sample.csv`](flybrain/sample.csv) and
  [`flybrain/processing.json`](flybrain/processing.json).
- Convert all coordinates and radii from nm to µm by dividing by 1,000. Translate
  by `(525,250,140)` µm, then rotate 180° about X (`x,-y,-z`). This is a rigid
  change of view, not an axis stretch or mirror. No biological left/right labels
  are added; the papers discuss the underlying FAFB acquisition's laterality issue.
- Preserve junctions and simplify only degree-two chains using 3D
  Ramer–Douglas–Peucker at 1 µm tolerance. Prune terminal subtrees starting at
  7 µm total cable and increase that threshold by 1.4× until the neuron has at
  most 55/70/100/100 segments for optic/central/projection/centrifugal respectively.
  Thus **fine branches and short twigs are intentionally omitted**. Chords
  approximate the source paths; the result is not suitable for morphometry.
  The source deposit's own healed edges are retained as published; no additional
  graph connections are made between neurons or disconnected components.
- Derive the envelope from the **unsimplified selected sample**, accumulating
  source edge length at edge midpoints in 2 µm voxels. Smooth with Gaussian sigma
  2.5 voxels; extract at 1.2% of the peak, marching-cubes step 4 voxels. This is
  visual context, not a biological density estimate or physical boundary.
- Signed normalized 16-bit positions restore uniform micrometre units through
  node transforms (`KHR_mesh_quantization`). The position quantization error is
  below 0.03 µm in Euclidean distance. No Draco/Meshopt or external decoder is
  needed. Vertex colour is linear RGB, stored as normalized RGBA8. Line thickness
  is for visibility, not neurite diameter.
- The retained neuronal paths span **802.55 × 349.57 × 269.03 µm**. Including the
  envelope and 100 µm ruler, the actual production loader finds a lateral extent
  of about **805.97 µm**. These are derived measurements of this source sample,
  not a claim about all fruit flies or an anatomical capsule.
- **Recommended item value: `0.0008 m`**, defined as the approximate lateral width
  of the reconstructed brain including both optic lobes and lamina. The entry's
  `reference_size: 800` then makes one model unit exactly one micrometre when the
  item is drawn. Its 10° pitch and −12° yaw give an extent of **0.979×** the listed
  value in the vendored Three.js loader. The included ruler is 100 µm long.
  Do not attach the unchanged entry to a 500/600 µm item: the production renderer
  scales geometry by `item.value / reference_size`, which would invalidate its
  micrometre calibration and the ruler.

## Rebuild

The large raw Parquet and the full published annotation table are build inputs,
not hosted runtime assets. Download them outside the repository:

```sh
mkdir -p /tmp/flybrain
curl -fL --retry 3 \
  https://zenodo.org/api/records/10877326/files/sk_lod1_783_healed_ds2.parquet/content \
  -o /tmp/flybrain/sk.parquet
curl -fL --retry 3 \
  'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-024-07686-5/MediaObjects/41586_2024_7686_MOESM5_ESM.tsv' \
  -o /tmp/flybrain/annotations.tsv
# pyarrow is needed only for preparation. Keep optional dependencies temporary:
./venv/bin/python -m pip install --target /tmp/flybrain-deps --no-deps pyarrow==26.0.0
PYTHONPATH=/tmp/flybrain-deps ./venv/bin/python scripts/build_flybrain_model.py prepare \
  --parquet /tmp/flybrain/sk.parquet --annotations /tmp/flybrain/annotations.tsv \
  --cache /tmp/flybrain/processed.npz
./venv/bin/python scripts/build_flybrain_model.py build \
  --cache /tmp/flybrain/processed.npz --output-dir /tmp/flybrain/final
# After the items job adds the exact item name and agreed value:
./venv/bin/python scripts/register_model.py \
  /tmp/flybrain/final/fruit-fly-brain-flywire.entry.json \
  /tmp/flybrain/final/fruit-fly-brain-flywire.glb
```

Preparation streams the complete Parquet in batches, carries split neurons across
batch boundaries, checks both input hashes, and rejects cyclic trees. It keeps
only the selected simplified graphs plus their unsimplified density grid. Build
uses no network or pyarrow. Tests cover physical transforms, real graph junctions,
disconnected components, missing parents, cycles, simplification and selection.

## Review limits

Khronos glTF Validator: zero errors, warnings, infos and hints. The production
GLTFLoader successfully parses the final asset under Node, including its actual
LineBasicMaterial conversion and per-vertex bounds. There are six draw calls,
137,209 neuronal path segments, three ruler segments and 30,768 shell triangles.

The sandbox prevents Chromium from starting (`bootstrap_check_in ... Permission
denied`), so **model_lab screenshots, full audit and actual-explorer/mobile
rendering are not verified here**. Rest, side, top and light-background software
geometry reviews are included under `handoff/flybrain/`; they were inspected but
are clearly labeled approximations, not production screenshots. See that folder's
`REPORT.md` for the remaining browser commands and the pending item dependency.
