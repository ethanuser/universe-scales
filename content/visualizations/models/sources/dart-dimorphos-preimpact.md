# Dimorphos — model source and limitations

The DART final pre-impact global SPC shape v004, sampled from NASA NAIF’s 1.940 m DSK. This is the shape before 26 September 2022, not a prediction of the reshaped asteroid. Catalog 151 m equivalent-volume diameter calibrates the closed mesh. Neutral gray is authored; no impact crater or ejecta is invented.

## Scientific and geometric basis

The original NAIF kernel is dimorphos_g_01940mm_spc_0000n00000_v004.bds: final pre-impact v004, global, nominal 1.940 m resolution. Its 49,152 triangles and 24,578 referenced vertices are extracted with spiceypy/CSPICE, without simplification. Source units are km. Closed-mesh equivalent-volume diameter is 0.149780 km, calibrated to the catalog's rounded 151 m. This is not the post-impact shape. [PDS collection metadata](https://pds.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=urn:nasa:pds:dart_shapemodel:data_derived_dimorphos_model_v004&version=1.0) describes the final pre-impact model and its uncertainties. The scientific reconstruction includes less constrained regions; do not interpret its neutral material as observed reflectance.

## Source, credit and rights

- Source: [https://pds.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=urn:nasa:pds:dart_shapemodel:data_derived_dimorphos_model_v004&version=1.0](https://pds.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=urn:nasa:pds:dart_shapemodel:data_derived_dimorphos_model_v004&version=1.0)
- Credit: NASA/Johns Hopkins APL DART team; NASA PDS/NAIF
- Rights: U.S. public-domain NASA media/data; credit the named science teams; [source terms](https://www.nasa.gov/nasa-brand-center/images-and-media/).
- Download: [https://naif.jpl.nasa.gov/pub/naif/pds/pds4/dart/dart_spice/spice_kernels/dsk/dimorphos_g_01940mm_spc_0000n00000_v004.bds](https://naif.jpl.nasa.gov/pub/naif/pds/pds4/dart/dart_spice/spice_kernels/dsk/dimorphos_g_01940mm_spc_0000n00000_v004.bds)
- Original SHA-256: `dce2cb662822448f6e765e6cfa568e0024af627e13eb7c9c44c55008a8b4b1e9` (2,714,624 bytes).
- Additional rights record: [space3d2-rights.md](../licenses/space3d2-rights.md).

## Reproduction and review

Run `./venv/bin/python scripts/build_space3d2_models.py` from the repository root. Inputs are pinned under `content/visualizations/models/sources/space3d2/`; they are not fetched at runtime. The preparation script refreshes inputs separately. No decoder extensions or external texture dependencies are used.

Units and calibration are recorded in the final entry JSON under `handoff/space3d2/`. Original sphere/Roche geometry uses km; small-body meshes retain source km; orbit coordinates preserve their AU relationships before a uniform catalog-reference conversion. Nominal solar radius and AU conversions follow [IAU 2015 B3](https://arxiv.org/html/1510.07674v1) and [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html).

CPU rest and quarter-camera previews are in `handoff/space3d2/previews/`. These are orthographic approximations, not WebGL/material, production explorer, mobile or model-lab approval. See `handoff/space3d2/REPORT.md` for the exact checks and outstanding integration work.
