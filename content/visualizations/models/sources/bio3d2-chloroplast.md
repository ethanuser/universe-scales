# Chloroplast — Chloroplast

## Source and permission

- Model: [Chloroplast](https://sketchfab.com/3d-models/chloroplast-4c02b0c865d440f0a0b971d77d6e315e) by **montanhabio** (`montanhabio`).
- [Official Sketchfab API](https://api.sketchfab.com/v3/models/4c02b0c865d440f0a0b971d77d6e315e) opened 2026-10-16: downloadable, license slug **`by`**, [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/).
- Compact API/license and source-archive checksum record: [bio3d2/chloroplast.json](bio3d2/chloroplast.json). No download token or signed URL is retained.
- The local asset is a modified derivative; original attribution and license are retained in its registry entry.

## Definition and changes

The longest X extent is uniformly calibrated to 5 µm, a representative size within the 5–10 µm organelles described by Cooper. The source is artist-modeled. The title mesh is removed; native relative anatomy is retained, with authored green envelope/stroma and gold DNA colours. Two complementary material groups of the same STL share one colour to avoid introducing false stripes.

Authored chloroplast cutaway by montanhabio, uniformly calibrated to the representative 5 µm long axis. The model shows envelope, thylakoid stacks and stromal connections with DNA indicated. It is a teaching illustration, not segmented EM or measured internal architecture. Green/gold false colours were added and the floating title removed. Internal proportions and disc counts are illustrative.

## Rebuild

Stage UID `4c02b0c865d440f0a0b971d77d6e315e` with `scripts/sketchfab_models.py stage` (owner's token file outside the repo), texture size 1024, archive allowance 100 MB and staged GLB allowance 150 MB. Large staging files remain outside the repository. Then run:

```sh
node scripts/prepare_bio3d2_imports.mjs /tmp/bio3d2/staged /tmp/bio3d2/processed MODULE_ROOT
```

`MODULE_ROOT` contains glTF Transform 4.5.0 and meshoptimizer. The script verifies source pins, converts legacy specular/glossiness to metallic/roughness, deduplicates/flattens/joins/welds the static scene, simplifies toward 50k triangles with error tolerance 0.005, prunes and quantizes. Only standard JPEG/PNG and decoder-free glTF are delivered; meshoptimizer is used offline, not as runtime mesh compression. The error bound may prevent reaching the exact target. No independent axis scaling is applied.

The final complete entry is [handoff JSON](../../../../handoff/bio3d2/bio3d2-chloroplast.entry.json). Review limitations and skipped alternatives are in [REPORT.md](../../../../handoff/bio3d2/REPORT.md).
