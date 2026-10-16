# Phobos — NASA Length model

NASA/JPL-Caltech's irregular Phobos mesh is retained. The mean-diameter item is calibrated by the mesh's equivalent-volume diameter, not its longest dimension. Uniform scale uses the equivalent-volume diameter of the closed source mesh; no axes are stretched independently.

## Sources and rights

- [Original NASA model page](https://science.nasa.gov/resource/phobos-mars-moon-3d-model/) (opened 2026-10-16).
- [Exact original download](https://assets.science.nasa.gov/content/dam/science/psd/mars/resources/gltf_files/24878_Phobos_1_1000.glb); SHA-256 `757712101e4fbcf9527942ee664a3bc6dfe3ab460466b760f4bf51ee85dbd8d3`, 3,855,016 bytes.
- [NASA 3D Resources rights statement](https://github.com/nasa/NASA-3D-Resources/blob/master/README.md): NASA describes its collection as free and without copyright. [NASA media guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/) apply; no endorsement is implied.
- Credit: NASA/JPL-Caltech. Source textures may be mosaics, processed imagery or agency illustrations; no claim of a complete, current true-color survey is made.

## Processing and calibration

- Calibration: `volume-equivalent-diameter`. The dataset's existing value supplies the physical length; no dataset files were edited.
- Retain original NASA geometry, node transforms, UVs and materials.
- Textures resized to at most 1024 px, JPEG color / PNG alpha and normal maps; no runtime decoder is needed.
- Rebuild: see `scripts/build_space3d_models.py` and `sources/space3d-manifest.json`. Prepared source cache hashes are pinned.

## Verification limits

CPU previews show approximate textured rest/side geometry only. Production WebGL screenshots, projected-size audit and explorer inspection are pending because this sandbox blocks Chromium. See `handoff/space3d/REPORT.md`.
