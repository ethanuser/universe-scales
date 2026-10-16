# International Space Station — NASA Length model

NASA's compact historic ISS engineering model. Original solar arrays, truss, modules and radiator geometry are retained, with source material colors. This is a historic configuration, not the present station or its newer roll-out arrays. The maximum source span is uniformly calibrated to the catalog end-to-end length.

## Sources and rights

- [Original NASA model page](https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Models/International%20Space%20Station%20%28ISS%29%20%28B%29) (opened 2026-10-16).
- [Exact original download](https://raw.githubusercontent.com/nasa/NASA-3D-Resources/master/3D%20Models/International%20Space%20Station%20%28ISS%29%20%28B%29/International%20Space%20Station%20%28ISS%29%20%28B%29.glb); SHA-256 `2ba4427413b0dd89a33d2acaf962dea8a96a3b1d8dceda05cc7aad547ffd3d16`, 476,992 bytes.
- [NASA 3D Resources rights statement](https://github.com/nasa/NASA-3D-Resources/blob/master/README.md): NASA describes its collection as free and without copyright. [NASA media guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/) apply; no endorsement is implied.
- Credit: NASA (individual model artist not identified in source metadata). Source textures may be mosaics, processed imagery or agency illustrations; no claim of a complete, current true-color survey is made.

## Processing and calibration

- Calibration: `longest-extent`. The dataset's existing value supplies the physical length; no dataset files were edited.
- Decode source Draco offline.
- Remove unused UVs and split normals; weld positions within each material.
- glTF Transform 4.5.0 simplify --ratio 0.2 --error 0.001; prune.
- Recompute area-weighted normals.
- Textures resized to at most 1024 px, JPEG color / PNG alpha and normal maps; no runtime decoder is needed.
- Rebuild: see `scripts/build_space3d_models.py` and `sources/space3d-manifest.json`. Prepared source cache hashes are pinned.

## Verification limits

CPU previews show approximate textured rest/side geometry only. Production WebGL screenshots, projected-size audit and explorer inspection are pending because this sandbox blocks Chromium. See `handoff/space3d/REPORT.md`.
