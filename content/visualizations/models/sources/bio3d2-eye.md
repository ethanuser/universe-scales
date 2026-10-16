# Human Eye — Human Eye

## Source and permission

- Model: [Human Eye](https://sketchfab.com/3d-models/human-eye-7621abd3b4604d95bad90f9a1aaac51f) by **ScannerDev** (`maskutfab`).
- [Official Sketchfab API](https://api.sketchfab.com/v3/models/7621abd3b4604d95bad90f9a1aaac51f) opened 2026-10-16: downloadable, license slug **`by`**, [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/).
- Compact API/license and source-archive checksum record: [bio3d2/eye.json](bio3d2/eye.json). No download token or signed URL is retained.
- The local asset is a modified derivative; original attribution and license are retained in its registry entry.

## Definition and changes

The source is a textured exterior illustration, with sclera/iris/pupil/cornea surfaces. X diameter is uniformly calibrated to 24 mm. [Bekerman et al. (2014)](https://doi.org/10.1155/2014/503645) report healthy adult dimensions near this representative scale. Painted vessels are illustrative and do not constitute a vascular reconstruction. The original iris texture and pupil remain; the model is not an optical simulation or a patient scan.

Authored external human-eye illustration by ScannerDev (maskutfab), uniformly calibrated to a representative 24 mm transverse eyeball diameter. The source sclera, iris, pupil and corneal surface are retained with their textures. It is not a patient scan or an optical/vascular reconstruction; the painted vessels are illustrative and no internal anatomy is claimed.

## Rebuild

Stage UID `7621abd3b4604d95bad90f9a1aaac51f` with `scripts/sketchfab_models.py stage` (owner's token file outside the repo), texture size 1024, archive allowance 100 MB and staged GLB allowance 150 MB. Large staging files remain outside the repository. Then run:

```sh
node scripts/prepare_bio3d2_imports.mjs /tmp/bio3d2/staged /tmp/bio3d2/processed MODULE_ROOT
```

`MODULE_ROOT` contains glTF Transform 4.5.0 and meshoptimizer. The script verifies source pins, converts legacy specular/glossiness to metallic/roughness, deduplicates/flattens/joins/welds the static scene, simplifies toward 50k triangles with error tolerance 0.005, prunes and quantizes. Only standard JPEG/PNG and decoder-free glTF are delivered; meshoptimizer is used offline, not as runtime mesh compression. The error bound may prevent reaching the exact target. No independent axis scaling is applied.

The final complete entry is [handoff JSON](../../../../handoff/bio3d2/bio3d2-eye.entry.json). Review limitations and skipped alternatives are in [REPORT.md](../../../../handoff/bio3d2/REPORT.md).
