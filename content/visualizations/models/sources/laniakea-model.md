# Laniakea CF4 reference preview

## Representation and limits

This is a reference-only preview: a unitless flat poster carrying the full Figure 1
projection from Dupuy & Courtois (2023). It retains the published CF4 galaxy
markers, streamlines, watershed colors, neighboring basin labels, and SGX/SGY/SGZ
orientation arrows. It adds no points, contour, flow, or reconstructed spatial
geometry. The panel's width, height, and orientation in the explorer have no
physical spatial meaning. It is not a 3D model, calibrated plane, or eligible
Length-model coverage asset. The production item should remain on its photo
fallback unless a rights-cleared, scientifically defensible calibrated model is
available. The metadata JSON is intentionally not a registry entry and contains
no `matches` or runtime `src` fields.

Figure 1 represents their **ungrouped CF4** reconstruction, in which Laniakea is
identified as a distinct watershed. In the grouped CF4 reconstruction it becomes
part of the Shapley basin. This dependence on catalog grouping is a scientific
caveat, not an asset-processing choice. The figure caption says its galaxy points
are placed at redshift and colored by basin membership; streamlines are computed
from the reconstructed velocity field, with their color gradients indicating
streamline density. The 50 Mpc h^-1 axes are orientation arrows, not a scale bar.

The A&A article identifies itself as open access under the Creative Commons
Attribution 4.0 license. Figure 1 is the article authors' CF4 visualization and
has no separate third-party credit notice in its caption; the preview metadata
records the paper, figure URL, authors, and license. This is figure-reuse
permission, not a redistribution license for CF4 catalog/grid inputs. The builder
retains the complete square image frame and performs only a downsample to at most
1024x1024 plus JPEG quality-88 re-encoding. There is no crop, retouching, contour
tracing, or change to figure colors.

## Scientific basis

- Dupuy, A. & Courtois, H. M. (2023), “Dynamic cosmography of the local Universe:
  Laniakea and five more watershed superclusters,” *A&A* 678, A176. DOI:
  [10.1051/0004-6361/202346802](https://doi.org/10.1051/0004-6361/202346802).
  [Article](https://www.aanda.org/articles/aa/full_html/2023/10/aa46802-23/aa46802-23.html)
  and [Figure 1 source image](https://arxiv.org/html/2305.02339v2/figures/visu_laniakea_names.jpeg).
  The article is [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- Tully, R. B., Courtois, H., Hoffman, Y. & Pomarède, D. (2014), “The Laniakea
  supercluster of galaxies,” *Nature* 513, 71–73. DOI:
  [10.1038/nature13674](https://doi.org/10.1038/nature13674). The authors define
  Laniakea using a divergent-flow surface and report an approximate 160 Mpc
  diameter. The explorer's length value is now `4.937084130386187e24 m`,
  the direct conversion of the approximate 160 Mpc span, replacing `5e23 m`.

Laniakea is a velocity-defined basin based on galaxy peculiar motions after
subtracting mean cosmic expansion (and, in the 2014 definition, long-range flows).
It is not a gravitationally bound system. The 2014 diameter is a quoted approximate
scale and is not derived from the Figure 1 panel or its pixel dimensions.

The paper reports an ungrouped-CF4 segmented volume of
`1.9e6 (Mpc h^-1)^3`; this GLB does not encode or render that volume. The official
[Cosmicflows data page](https://projets.ip2i.in2p3.fr/cosmicflows/) lists a CF4
watershed grid but does not state redistribution terms for that product. No grid,
CF2 mesh, or galaxy catalog is included or used to construct this figure panel.

## Rebuild and validation

Stage the article figure outside the repository, then build a GLB reference
preview and non-importable provenance metadata:

```sh
mkdir -p /private/tmp/length-laniakea
curl -L 'https://arxiv.org/html/2305.02339v2/figures/visu_laniakea_names.jpeg' \
  -o /private/tmp/length-laniakea/aa2023-fig1.jpeg
python3 scripts/build_laniakea_model.py \
  --figure /private/tmp/length-laniakea/aa2023-fig1.jpeg
python3 -m unittest discover -s tests -p 'test_laniakea_model.py'
```

The staged output is self-contained GLB with one textured quad, two triangles,
and no external resources. The builder enforces the 1.5 MB / 60,000-triangle
budget and a 1024-pixel maximum texture side. The metadata tag is `reference_panel`,
not `catalog_diagram`; neither output may be copied into shared registry/assets.
It records the source-image SHA-256, exact source/credit links, dimensions, and
re-encoding steps. No change to the Length dataset or production registry is made
here.
