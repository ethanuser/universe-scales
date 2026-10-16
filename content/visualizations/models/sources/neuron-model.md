# Rat cortical interneuron — NeuroMorpho.Org NMO_109111

This replaces the runtime procedural pyramidal neuron. The earlier Allen
480114344 dendrite-only crop was a staged experiment, not a registered asset;
its noncommercial source was unsuitable for this import policy.

## Source, rights and required credit

**BC140212B_21**, NeuroMorpho.Org **NMO_109111**, Feldmeyer archive. A biocytin
reconstruction of a non-fast-spiking, local-projecting, non-Martinotti-like
interneuron in layer 4 of rat somatosensory barrel cortex. The source records
measured diameters, three-dimensional coordinates, soma, dendrites and axon,
and classifies the physical integrity as **Dendrites & Axon Complete**.

- [Reconstruction record](https://neuromorpho.org/neuron_info.jsp?neuron_name=BC140212B_21)
- [Metadata API](https://neuromorpho.org/api/neuron/name/BC140212B_21)
- [Standardized SWC](https://neuromorpho.org/dableFiles/feldmeyer/CNG%20version/BC140212B_21.CNG.swc)
- [Original Neurolucida ASC, including soma contour](https://neuromorpho.org/dableFiles/feldmeyer/Source-Version/BC140212B_21.asc)
- [NeuroMorpho.Org terms](https://neuromorpho.org/useterm.jsp), opened 2026-10-15:
  the repository explicitly licenses its material under **CC BY 4.0** and
  requires the original paper, repository name/RRID and repository paper below.

Required attribution, applying to the SWC derivative, contour and generated GLB:

1. **Emmenegger V, Qi G, Wang H, Feldmeyer D (2018).** Morphological and
   Functional Characterization of Non-fast-Spiking GABAergic Interneurons in
   Layer 4 Microcircuitry of Rat Barrel Cortex. *Cerebral Cortex* 28:1439–1457.
   [doi:10.1093/cercor/bhx352](https://doi.org/10.1093/cercor/bhx352);
   [open paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC6093438/).
2. **NeuroMorpho.Org (RRID:SCR_002145)**, Feldmeyer archive, NMO_109111.
3. **Tecuatl C, Ljungquist B, Ascoli GA (2024).** Accelerating the continuous
   community sharing of digital neuromorphology data. *FASEB BioAdvances*
   6(7):207–221. [doi:10.1096/fba.2024-00048](https://doi.org/10.1096/fba.2024-00048).

Adapted by Universe Scales: tube meshing, bounded simplification, soma loft,
false colors, labels and an illustrative electrical animation. The source data
and these morphology derivatives retain CC BY 4.0 attribution.
MouseLight was considered but rejected because its own
[terms](https://www.janelia.org/project-team/mouselight/neuronbrowser/)
specify CC BY-NC. Allen's prior staged asset has the restriction documented
in the git history and is not used by this model.

## Completeness and scale

The model keeps **all 65,332 standardized SWC nodes' tree connectivity** through
785 maximal branches: 65,329 process edges, with the two auxiliary SWC soma
edges represented instead by the soma surface. No spatial crop, axial stretch,
fabricated branches, spines, nucleus, synapses or myelin are added. Original
coordinate extents are **571.67 × 791.52 × 437.20 µm**. These numbers are computed
directly from the archived SWC, not asserted to be population averages or an
end-to-end axon length. Longest traced axonal root-to-tip path: **965.470 µm**;
the sum of branches is a different measurement from spatial span.

The reference extent is **800 model units**, with one model unit representing
one micrometer. This is intended for the proposed **8e-4 m (0.8 mm)** Length
value. **The items job must apply the dataset change in `handoff/neuron/REPORT.md`
before this model is published.** With the unchanged 1e-4 m item, the normalizer
would shrink its physical calibration eightfold. Passing a normalized size
audit alone cannot establish agreement with the scientific source.

This is a **complete archived reconstruction**, not proof that every process
of the living neuron survived sectioning. The metadata says a **350 µm** slice.
The original paper describes selecting well-preserved, high-quality complete
reconstructions, but slice preparation can sever biological processes. Do not
advertise this as an uncut whole-brain neuron or as a generic human neuron.
The source metadata reports shrinkage already corrected (XY 1.1; Z 2.1), also
described in the paper's reconstruction methods. No correction is applied again.

## Geometry and soma

`scripts/prepare_neuron_source.py` downloads only the metadata API and direct
data files, using an identifying, nonpersonal User-Agent. It strips comments
containing original workstation paths/contact details, preserves every SWC
numeric row, and bundles a deterministic gzip derivative. Download hashes and
direct URLs are retained in `neuron/provenance.json` and the registry entry.

The original soma is a single traced contour. Its outline is transformed into
standardized SWC coordinates with a rigid XY rotation and translation, fitted
to matching initial axon/dendrite samples. Maximum fitting residual is
**0.0272 µm** (rounding/conversion precision); the stored transform has no scale
factor. The closed contour is simplified within **0.08 µm**. The soma mesh
retains that irregular XY outline. **Depth is not measured:** a rounded loft
uses the SWC equivalent soma radius, **8.22559 µm**, as its depth semi-axis.
This is a contour-based surface proxy, not a segmented 3D soma membrane.

Processes use continuous, smooth-normal, six-sided tubes with parallel-
transported frames, rather than disconnected cones. Sampled SWC radii are
not multiplied by a visibility gain. Branch endpoints and bifurcations remain
fixed. Simplification bounds centerline interpolation error to **0.35 µm** and
radius interpolation error to **0.08 µm**, measured at every original sample.
The full original SWC remains available for exact measurements. Branch tubes
intersect at shared junction positions; this is not a manifold biological
membrane reconstruction and must not be used to infer enclosed cell volume.

Copper identifies the axon, jade the dendrites, and pale green the soma. Colors
are authored identifiers, not recorded fluorescence. Three upright callouts
use the existing collision-aware label layout.

## Action-potential annotation

The glTF root has `extras.animation.kind = "reconstructed-neuron"`.
`neuron-animation.js` registers its updater with the existing animation
registry. The production stage discovers the descriptor through GLTF cloning
and calibration wrappers and handles visibility and `prefers-reduced-motion`.

Every axon vertex carries `_PATH_DISTANCE`, the cumulative **original** SWC
distance, preserving propagation timing across simplification and branches.
A shader brightens the axon membrane near a traveling wavefront. A soft,
screen-sized point halo makes that electrical annotation legible without
thickening the anatomical tubes. At rest its material has zero opacity; when
reduced motion prevents updates, the anatomical reconstruction stays still.

The wave begins at an **assumed 20 µm** path distance into the proximal axon.
This is an explanatory AIS location, **not immunohistochemical identification
of this cell's AIS**. The general initiation/propagation mechanism is supported
by [Leterrier (2018), The Axon Initial Segment: An Updated Viewpoint](https://pmc.ncbi.nlm.nih.gov/articles/PMC6596274/).
No cell-specific voltage, conduction velocity or myelination is inferred.
The **6.5 s** loop launches at **0.8 s** and reaches the most distal traced tip
in **4.5 s**, with a **22 µm** visual pulse width. These are display choices,
not physiological measurements. No numerical mV readout is fabricated.

## Rebuild and review

Offline rebuild, no browser or runtime network dependency:

```sh
./venv/bin/python scripts/build_reconstructed_neuron.py --output-dir /tmp/neuron-final
python3 scripts/register_model.py \
  /tmp/neuron-final/neuromorpho-feldmeyer-neuron-109111.entry.json \
  /tmp/neuron-final/neuromorpho-feldmeyer-neuron-109111.glb
python3 scripts/bump_versions.py
```

Optional fresh source download (the original files are only temporary inputs):

```sh
./venv/bin/python scripts/prepare_neuron_source.py --download-dir /tmp/neuron-download
```

Production review commands and currently blocked browser checks are in the
handoff report. `preview_neuron_cpu.py` provides explicit **CPU geometry
previews**, never a substitute for production/mobile screenshots.
