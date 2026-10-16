# Ryugu — model source and limitations

Hayabusa2 measured SfM shape, 49,152 original triangles. The equatorial ridge and resolved relief are from spacecraft data; gray albedo is authored, not a surface photograph. Catalog mean diameter calibrates the closed mesh equivalent-volume diameter. Body-fixed north is up; the inspection pose is authored.

## Scientific and geometric basis

The original SHAPE_SFM_49k_v20180804.obj has 49,152 triangles and 25,350 vertices, of which 772 are unused. Only unused vertices are removed; every referenced coordinate and triangle is retained. Source units are km. The closed mesh gives equivalent-volume diameter 0.896499 km. We calibrate that diameter to the catalog 896 m; the tiny difference reflects source/catalog rounding. The structure-from-motion model's broad equatorial ridge and resolved topography are measured, while the gray material is authored. No software subject to SPC distribution restrictions is bundled.

## Source, credit and rights

- Source: [https://data.darts.isas.jaxa.jp/pub/hayabusa2/paper/Watanabe_2019/README.html](https://data.darts.isas.jaxa.jp/pub/hayabusa2/paper/Watanabe_2019/README.html)
- Credit: ISAS/JAXA; Watanabe et al. (2019), Hayabusa2 shape-model team
- Rights: ISAS/JAXA open-data terms, compatible with CC BY 4.0; [source terms](https://www.isas.jaxa.jp/en/researchers/data-policy/).
- Download: [https://data.darts.isas.jaxa.jp/pub/hayabusa2/paper/Watanabe_2019/SHAPE_SFM_49k_v20180804.obj](https://data.darts.isas.jaxa.jp/pub/hayabusa2/paper/Watanabe_2019/SHAPE_SFM_49k_v20180804.obj)
- Original SHA-256: `012421d8fc981cede420b71ca34805cf71e6abfef26cdb750534600cc3adbd16` (2,639,581 bytes).
- Additional rights record: [space3d2-rights.md](../licenses/space3d2-rights.md).

## Reproduction and review

Run `./venv/bin/python scripts/build_space3d2_models.py` from the repository root. Inputs are pinned under `content/visualizations/models/sources/space3d2/`; they are not fetched at runtime. The preparation script refreshes inputs separately. No decoder extensions or external texture dependencies are used.

Units and calibration are recorded in the final entry JSON under `handoff/space3d2/`. Original sphere/Roche geometry uses km; small-body meshes retain source km; orbit coordinates preserve their AU relationships before a uniform catalog-reference conversion. Nominal solar radius and AU conversions follow [IAU 2015 B3](https://arxiv.org/html/1510.07674v1) and [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html).

CPU rest and quarter-camera previews are in `handoff/space3d2/previews/`. These are orthographic approximations, not WebGL/material, production explorer, mobile or model-lab approval. See `handoff/space3d2/REPORT.md` for the exact checks and outstanding integration work.
