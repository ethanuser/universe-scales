# Saturn's Rings — model source and limitations

NASA VTAD’s original Saturn globe and ring meshes, retaining their textures and relative proportions. Calibration uses the catalog 280,360 km span to the F ring in the source’s 120,536 km equatorial-diameter units. The model’s outer edge is within 1% of that span. This is a main-ring view; the diffuse E ring and individual particles are not represented.

## Scientific and geometric basis

The ringed source spans 2,330.901 source units. The catalog 280,360 km reference is retained as an approximate F-ring span; source physical span is about 280,958 km. [PDS ring statistics](https://pds-rings.seti.org/saturn/saturn_rings_table.html) show that the F ring has a finite, variable radial range; this is not a precision outer boundary. Main rings and globe preserve the source scale. Diffuse distant rings are absent.

## Source, credit and rights

- Source: [https://science.nasa.gov/resource/saturn-3d-model/](https://science.nasa.gov/resource/saturn-3d-model/)
- Credit: NASA Visualization Technology Applications and Development (VTAD)
- Rights: U.S. public-domain NASA media/data; credit the named science teams; [source terms](https://www.nasa.gov/nasa-brand-center/images-and-media/).
- Additional rights record: [space3d2-rights.md](../licenses/space3d2-rights.md).

## Reproduction and review

Run `./venv/bin/python scripts/build_space3d2_models.py` from the repository root. Inputs are pinned under `content/visualizations/models/sources/space3d2/`; they are not fetched at runtime. The preparation script refreshes inputs separately. No decoder extensions or external texture dependencies are used.

Units and calibration are recorded in the final entry JSON under `handoff/space3d2/`. Original sphere/Roche geometry uses km; small-body meshes retain source km; orbit coordinates preserve their AU relationships before a uniform catalog-reference conversion. Nominal solar radius and AU conversions follow [IAU 2015 B3](https://arxiv.org/html/1510.07674v1) and [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html).

CPU rest and quarter-camera previews are in `handoff/space3d2/previews/`. These are orthographic approximations, not WebGL/material, production explorer, mobile or model-lab approval. See `handoff/space3d2/REPORT.md` for the exact checks and outstanding integration work.
