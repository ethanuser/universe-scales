# Charon — NASA Length model

Encounter coverage and map resolution are uneven; the unobserved or poorly observed regions are not measured high-resolution terrain.

## Sources and rights

- [Original NASA model page](https://science.nasa.gov/resource/charon-3d-model/) (opened 2026-10-16).
- [Exact original download](https://science.nasa.gov/wp-content/uploads/2023/09/Charon_1_2.glb); SHA-256 `3677525ff10e15f3d9cd0f0152801ed27ac3c277f8aad15056fe01cba20b2dbe`, 473,760 bytes.
- [NASA 3D Resources rights statement](https://github.com/nasa/NASA-3D-Resources/blob/master/README.md): NASA describes its collection as free and without copyright. [NASA media guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/) apply; no endorsement is implied.
- Credit: NASA Visualization Technology Applications and Development (VTAD). Source textures may be mosaics, processed imagery or agency illustrations; no claim of a complete, current true-color survey is made.

## Processing and calibration

- Calibration: `longest-extent`. The dataset's existing value supplies the physical length; no dataset files were edited.
- Retain original NASA geometry, node transforms, UVs and materials.
- Textures resized to at most 1024 px, JPEG color / PNG alpha and normal maps; no runtime decoder is needed.
- Rebuild: see `scripts/build_space3d_models.py` and `sources/space3d-manifest.json`. Prepared source cache hashes are pinned.

## Verification limits

CPU previews show approximate textured rest/side geometry only. Production WebGL screenshots, projected-size audit and explorer inspection are pending because this sandbox blocks Chromium. See `handoff/space3d/REPORT.md`.
