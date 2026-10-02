# Allen Cell Types Neuron Crop

## Source and citation

The morphology is the actual Allen Cell Types Database specimen **480114344**,
named `Rorb-IRES2-Cre-D;Ai14-197332.06.02.01`, from mouse visual cortex. The
Allen SDK's Cell Types example uses this specimen to demonstrate downloading
and plotting its SWC reconstruction. Its reconstruction record is **491771446**;
the source SWC is Allen well-known file **491771448**. The associated marker
file is **496606365**. The builder records the downloaded files' SHA-256 hashes
in the staged `entry.json`.

- [Specimen page and downloadable reconstruction](https://celltypes.brain-map.org/mouse/experiment/electrophysiology/480114344)
- [Allen SWC download](https://api.brain-map.org/api/v2/well_known_file_download/491771448)
- [Allen marker download](https://api.brain-map.org/api/v2/well_known_file_download/496606365)
- [Allen SDK Cell Types morphology documentation](https://alleninstitute.github.io/AllenSDK/cell_types.html)
- Gouwens, N. W., Sorensen, S. A., Berg, J., et al. (2019). “Classification of electrophysiological and morphological neuron types in the mouse visual cortex.” *Nature Neuroscience* 22, 1182–1195. [doi:10.1038/s41593-019-0417-0](https://doi.org/10.1038/s41593-019-0417-0)

The SWC stores traced 3D compartment centerlines, radii, type codes, and parent
links. Allen classifies this specimen as **dendrite-only** (3,959 source nodes,
101 branches, 45 bifurcations, 56 tips; reported whole reconstruction height
615.6 µm and total traced length 4,664.7 µm). It has no reconstructed axon.
The model is not a generic or complete neuron and must not be described as one
cell type representative of all neurons.

## Crop and geometry

The Length item describes a neuron plus local branches at roughly 100 µm. The
whole Allen reconstruction is much larger, so the builder keeps original SWC
coordinates and radii and clips each segment to a soma-centered cube from −50
to +50 µm on X, Y, and Z. It does not scale, squeeze, or bend the source tree.
Segments crossing the crop are cut at its planes; these crop ends are not
biological tips. In-crop Allen marker points retain their source meanings:
type 10 is a dendrite cut/truncation and type 20 marks a location where no
reconstruction was made. The soma is displayed as a sphere using the root
compartment's SWC radius; this is a compact visual proxy for the soma, not a
segmented soma surface. The source apical/basal labels and measured radii are
retained. Micrometers are the model coordinate units; the staged presentation
reference size is 100 µm.

Rebuild from the downloaded source files:

```sh
python3 scripts/build_neuron_model.py \
  --swc /private/tmp/neuron-scientific/allen-specimen-480114344.swc \
  --markers /private/tmp/neuron-scientific/allen-specimen-480114344-marker.swc \
  --output-dir /private/tmp/neuron-scientific
```

## Reuse terms

Allen Institute terms permit use, copying, distribution, and derivative works
for research or other **noncommercial** purposes, with the citation obligations
in its [Citation Policy](https://alleninstitute.org/legal/citation-policy/).
Commercial redistribution requires written permission under the
[Terms of Use](https://alleninstitute.org/terms-of-use/). This source is not
asserted to be CC-BY or CC0 and must not inherit the repository's permissive
asset license. The staged model entry preserves this restriction; confirm the
hosting and repository-distribution context before registering it.
