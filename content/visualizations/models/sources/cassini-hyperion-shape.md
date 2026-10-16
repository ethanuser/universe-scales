# Hyperion Moon — model source and limitations

The Cassini/Thomas 30k-plate measured shape of Saturn’s moon Hyperion, not the redwood tree. Craters and major relief are from the archived shape, not procedural noise. Neutral gray is an authored albedo; unresolved small crater detail is absent. The catalog mean diameter calibrates the equivalent-volume diameter; an oblique pose foreshortens its long axis.

## Scientific and geometric basis

The archived Thomas/Cassini 30k-plate model has 29,268 triangles, 14,636 vertices and source extents about 252.48 × 267.11 × 341.26 km before Y-up conversion. Its equivalent-volume diameter is 272.51 km. The [NASA Hyperion overview](https://science.nasa.gov/saturn/moons/hyperion/) quotes mean radius about 135 km, permitting an approximate 270 km mean-diameter item. Older three-axis estimates on that page differ from this later digital shape: the mesh is retained rather than distorted to those older axis values. The 60° yaw / 15° pitch is an authored inspection pose. This asset is unregistered because the existing exact name Hyperion identifies a redwood tree; proposed new name is Hyperion Moon.

## Source, credit and rights

- Source: [https://data.nasa.gov/dataset/saturn-small-moon-shape-models-v1-0](https://data.nasa.gov/dataset/saturn-small-moon-shape-models-v1-0)
- Credit: Peter C. Thomas; NASA/JPL/Cassini ISS; NASA PDS Small Bodies Node
- Rights: U.S. public-domain NASA media/data; credit the named science teams; [source terms](https://www.nasa.gov/nasa-brand-center/images-and-media/).
- Download: [https://sbn.psi.edu/pds/shape-models/files/SATURN_SMALL_MOONS/hyperion_30k_plt.tab.obj](https://sbn.psi.edu/pds/shape-models/files/SATURN_SMALL_MOONS/hyperion_30k_plt.tab.obj)
- Original SHA-256: `7b1bb010f9f7952e2647923a30bfed813850bf8e72e235a80ac4008a23e0c8fc` (1,228,388 bytes).
- Additional rights record: [space3d2-rights.md](../licenses/space3d2-rights.md).

## Reproduction and review

Run `./venv/bin/python scripts/build_space3d2_models.py` from the repository root. Inputs are pinned under `content/visualizations/models/sources/space3d2/`; they are not fetched at runtime. The preparation script refreshes inputs separately. No decoder extensions or external texture dependencies are used.

Units and calibration are recorded in the final entry JSON under `handoff/space3d2/`. Original sphere/Roche geometry uses km; small-body meshes retain source km; orbit coordinates preserve their AU relationships before a uniform catalog-reference conversion. Nominal solar radius and AU conversions follow [IAU 2015 B3](https://arxiv.org/html/1510.07674v1) and [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html).

CPU rest and quarter-camera previews are in `handoff/space3d2/previews/`. These are orthographic approximations, not WebGL/material, production explorer, mobile or model-lab approval. See `handoff/space3d2/REPORT.md` for the exact checks and outstanding integration work.
