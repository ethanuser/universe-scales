# Hubble Space Telescope — NASA Length model

The open aperture door and solar arrays are retained. The source body has an approximately 13.2-unit axial barrel; the open door extends beyond it. Calibration uses that barrel length, with the extent overhead documented separately.

## Sources and rights

- [Original NASA model page](https://science.nasa.gov/resource/hubble-space-telescope-3d-model/) (opened 2026-10-16).
- [Exact original download](https://assets.science.nasa.gov/content/dam/science/psd/solar/2023/09/h/Hubble.glb); SHA-256 `e6a40640d6846e8f5d9438821ebe2d7de730c8dadba1cc9dfdbcc148ff1052cd`, 11,463,124 bytes.
- [NASA 3D Resources rights statement](https://github.com/nasa/NASA-3D-Resources/blob/master/README.md): NASA describes its collection as free and without copyright. [NASA media guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/) apply; no endorsement is implied.
- Credit: NASA (individual model artist not identified). Source textures may be mosaics, processed imagery or agency illustrations; no claim of a complete, current true-color survey is made.

## Processing and calibration

- Calibration: `explicit`. The dataset's existing value supplies the physical length; no dataset files were edited.
- Retain original NASA geometry, node transforms, UVs and materials.
- Textures resized to at most 1024 px, JPEG color / PNG alpha and normal maps; no runtime decoder is needed.
- Rebuild: see `scripts/build_space3d_models.py` and `sources/space3d-manifest.json`. Prepared source cache hashes are pinned.

## Verification limits

CPU previews show approximate textured rest/side geometry only. Production WebGL screenshots, projected-size audit and explorer inspection are pending because this sandbox blocks Chromium. See `handoff/space3d/REPORT.md`.
