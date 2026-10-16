# Space Shuttle Orbiter — NASA Length model

NASA's orbiter alone, without the external tank or boosters. The source nose-to-tail axis sets the scale. Original shape, thermal-tile maps and markings are retained; this is a historic engineering visualization.

## Sources and rights

- [Original NASA model page](https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Models/Space%20Shuttle%20%28D%29) (opened 2026-10-16).
- [Exact original download](https://raw.githubusercontent.com/nasa/NASA-3D-Resources/master/3D%20Models/Space%20Shuttle%20%28D%29/Space%20Shuttle%20%28D%29.glb); SHA-256 `d0015681ff092d36062fdfed78e2bd1ca0f86e90862840d25bae11c686ce3549`, 2,471,932 bytes.
- [NASA 3D Resources rights statement](https://github.com/nasa/NASA-3D-Resources/blob/master/README.md): NASA describes its collection as free and without copyright. [NASA media guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/) apply; no endorsement is implied.
- Credit: NASA (individual model artist not identified in source metadata). Source textures may be mosaics, processed imagery or agency illustrations; no claim of a complete, current true-color survey is made.

## Processing and calibration

- Calibration: `axis` on world `x` axis. The dataset's existing value supplies the physical length; no dataset files were edited.
- Decode source Draco offline; convert WebP images to PNG/JPEG.
- Textures resized to at most 512 px, JPEG color / PNG alpha and normal maps; no runtime decoder is needed.
- Rebuild: see `scripts/build_space3d_models.py` and `sources/space3d-manifest.json`. Prepared source cache hashes are pinned.

## Verification limits

CPU previews show approximate textured rest/side geometry only. Production WebGL screenshots, projected-size audit and explorer inspection are pending because this sandbox blocks Chromium. See `handoff/space3d/REPORT.md`.
