# Enceladus — NASA Length model

NASA's textured globe retains its original topology, texture coordinates and appearance. It is an idealized scale model, not a resolved terrain reconstruction.

## Sources and rights

- [Original NASA model page](https://science.nasa.gov/resource/enceladus-3d-model/) (opened 2026-10-16).
- [Exact original download](https://assets.science.nasa.gov/content/dam/science/psd/solar/2023/09/e/Enceladus_1_504.glb); SHA-256 `7548234bae15047d6c1af6bec4f348748b1acae7d4e7bfbe50e5bb3dda75506f`, 17,925,448 bytes.
- [NASA 3D Resources rights statement](https://github.com/nasa/NASA-3D-Resources/blob/master/README.md): NASA describes its collection as free and without copyright. [NASA media guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/) apply; no endorsement is implied.
- Credit: NASA Visualization Technology Applications and Development (VTAD). Source textures may be mosaics, processed imagery or agency illustrations; no claim of a complete, current true-color survey is made.

## Processing and calibration

- Calibration: `longest-extent`. The dataset's existing value supplies the physical length; no dataset files were edited.
- Retain original NASA geometry, node transforms, UVs and materials.
- Textures resized to at most 1024 px, JPEG color / PNG alpha and normal maps; no runtime decoder is needed.
- Rebuild: see `scripts/build_space3d_models.py` and `sources/space3d-manifest.json`. Prepared source cache hashes are pinned.

## Verification limits

CPU previews show approximate textured rest/side geometry only. Production WebGL screenshots, projected-size audit and explorer inspection are pending because this sandbox blocks Chromium. See `handoff/space3d/REPORT.md`.
