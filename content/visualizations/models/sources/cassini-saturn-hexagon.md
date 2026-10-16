# Saturn's Hexagon — model source and limitations

Cassini PIA17652 false-color polar mosaic on a shallow idealized spherical cap. The jet’s visible across-corners width is registered approximately to the catalog 25,000 km; the surrounding circular aperture is context and extends to about 1.28×. This is approximate image registration, not a georeferenced latitude/longitude map. Colors combine ultraviolet, visible and infrared wavelengths and are not natural vision. Geometry shows planetary curvature only, not measured cloud heights. The source is a 2012 image, not current weather or a six-sided solid object.

## Scientific and geometric basis

Source PIA17652 is a 1,024 × 1,024 false-color north-polar mosaic; see the NASA source for the ultraviolet/visible/infrared wavelength combination and 2012 imaging date. The complete image occupies a circular aperture 1.28 catalog widths across. Its jet is registered approximately, by image extent, to the catalog 25,000 km. This is a diagrammatic image drape, not a calibrated cartographic projection. A spherical curvature radius of 60,268 / 25,000 display units comes from the [NASA Saturn fact sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/saturnfact.html). No cloud heights or hexagonal wall are modeled.

## Source, credit and rights

- Source: [https://science.nasa.gov/resource/saturns-streaming-hexagon-storm/](https://science.nasa.gov/resource/saturns-streaming-hexagon-storm/)
- Credit: NASA/JPL-Caltech/SSI/Hampton University; cap assembled by Universe Scales
- Rights: U.S. public-domain NASA media/data; credit the named science teams; [source terms](https://www.nasa.gov/nasa-brand-center/images-and-media/).
- Download: [https://assets.science.nasa.gov/content/dam/science/psd/solar/2023/09/p/i/a/PIA17652.jpg](https://assets.science.nasa.gov/content/dam/science/psd/solar/2023/09/p/i/a/PIA17652.jpg)
- Original SHA-256: `29b65d1370390fda5ff32ad0e73bfc774cd0c4755a237005031663a46facb452` (109,646 bytes).
- Additional rights record: [space3d2-rights.md](../licenses/space3d2-rights.md).

## Reproduction and review

Run `./venv/bin/python scripts/build_space3d2_models.py` from the repository root. Inputs are pinned under `content/visualizations/models/sources/space3d2/`; they are not fetched at runtime. The preparation script refreshes inputs separately. No decoder extensions or external texture dependencies are used.

Units and calibration are recorded in the final entry JSON under `handoff/space3d2/`. Original sphere/Roche geometry uses km; small-body meshes retain source km; orbit coordinates preserve their AU relationships before a uniform catalog-reference conversion. Nominal solar radius and AU conversions follow [IAU 2015 B3](https://arxiv.org/html/1510.07674v1) and [JPL constants](https://ssd.jpl.nasa.gov/astro_par.html).

CPU rest and quarter-camera previews are in `handoff/space3d2/previews/`. These are orthographic approximations, not WebGL/material, production explorer, mobile or model-lab approval. See `handoff/space3d2/REPORT.md` for the exact checks and outstanding integration work.
