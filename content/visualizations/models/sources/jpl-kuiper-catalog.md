# Kuiper Belt — model source and limitations

4,615 actual catalog-object locations from the pinned JPL SBDB orbital elements, propagated with a two-body approximation to 16 October 2026 TDB. Selection: asteroid records with semimajor axis 30–50 AU, perihelion at least 30 AU, and computed distance 30–50 AU. This is a selected, discovery-biased subset, not all Kuiper Belt objects or an unbiased density map. Point colors and sizes are display glyphs, not body sizes or measured colors. The faint Neptune ellipse is a JPL J2000 reference orbit; the Sun is physically scaled and subpixel. No synthetic filler points are added.

## Scientific and geometric basis

The exact query and response are pinned in space3d2/manifest.json and kuiper.json. It returns 4,747 asteroid records with 30 ≤ a ≤ 50 AU and q ≥30 AU. After two-body propagation to JD 2461329.5 TDB (16 October 2026) and a computed 30–50 AU distance cut, 4,615 source objects remain. Every dot retains an actual source identity; kuiper-displayed.json maps point order to JPL primary designation. The common-epoch step uses the [JPL DE440 solar GM](https://ssd.jpl.nasa.gov/astro_par.html); no N-body integration is implied. A deterministic shuffled prefix supports the runtime point LOD. The faint Neptune curve uses the JPL J2000 approximate reference ellipse. This discovery-biased sample excludes scattered/distant objects by definition; it is not the complete Kuiper Belt or a physical density reconstruction.

## Source, credit and rights

- Source: [https://ssd-api.jpl.nasa.gov/doc/sbdb_query.html](https://ssd-api.jpl.nasa.gov/doc/sbdb_query.html)
- Credit: NASA/JPL Solar System Dynamics; catalog visualization by Universe Scales
- Rights: U.S. public-domain NASA media/data; credit the named science teams; [source terms](https://www.nasa.gov/nasa-brand-center/images-and-media/).
- Download: [https://ssd-api.jpl.nasa.gov/sbdb_query.api?fields=pdes%2Cfull_name%2Cepoch%2Ca%2Ce%2Ci%2Com%2Cw%2Cma&sb-kind=a&sb-cdata=%7B%22AND%22%3A%5B%22a%7CRG%7C30%7C50%22%2C%22q%7CGE%7C30%22%5D%7D&full-prec=1&sort=pdes](https://ssd-api.jpl.nasa.gov/sbdb_query.api?fields=pdes%2Cfull_name%2Cepoch%2Ca%2Ce%2Ci%2Com%2Cw%2Cma&sb-kind=a&sb-cdata=%7B%22AND%22%3A%5B%22a%7CRG%7C30%7C50%22%2C%22q%7CGE%7C30%22%5D%7D&full-prec=1&sort=pdes)
- Original SHA-256: `acade45227a698b01cd01f05b712cbd9c3a17b99b228e77c0b31bac6e2360975` (1,105,414 bytes).
- Additional rights record: [space3d2-rights.md](../licenses/space3d2-rights.md).

## Reproduction and review

Run `./venv/bin/python scripts/build_space3d2_models.py` from the repository root. Inputs are pinned under `content/visualizations/models/sources/space3d2/`; they are not fetched at runtime. The preparation script refreshes inputs separately. No decoder extensions or external texture dependencies are used.

Units and calibration are recorded in the final entry JSON under `handoff/space3d2/`. Original sphere/Roche geometry uses km; small-body meshes retain source km; orbit coordinates preserve their AU relationships before a uniform catalog-reference conversion. Nominal solar radius and AU conversions follow [IAU 2015 B3](https://arxiv.org/html/1510.07674v1) and [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html).

CPU rest and quarter-camera previews are in `handoff/space3d2/previews/`. These are orthographic approximations, not WebGL/material, production explorer, mobile or model-lab approval. See `handoff/space3d2/REPORT.md` for the exact checks and outstanding integration work.
