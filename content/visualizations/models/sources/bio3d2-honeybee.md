# Honeybee — Western Honeybee - Adult Worker - CT Scan

## Source and permission

- Model: [Western Honeybee - Adult Worker - CT Scan](https://sketchfab.com/3d-models/western-honeybee-adult-worker-ct-scan-ee629bd30e4a47899de1b30b9b71c905) by **etainproject** (`etainproject`).
- [Official Sketchfab API](https://api.sketchfab.com/v3/models/ee629bd30e4a47899de1b30b9b71c905) opened 2026-10-16: downloadable, license slug **`by`**, [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/).
- Compact API/license and source-archive checksum record: [bio3d2/honeybee.json](bio3d2/honeybee.json). No download token or signed URL is retained.
- The local asset is a modified derivative; original attribution and license are retained in its registry entry.

## Definition and changes

The 11 mm X extent of the staged scan matches Worker 1 in [Thielens et al. (2020), Methods](https://www.nature.com/articles/s41598-019-56948-0), also linked by the source author. Native units are millimetres. The entry reference is 12.5 mm, matching the catalog’s representative value: the measured specimen therefore appears approximately 0.88 times that reference before resting rotation. Its compact preserved pose and missing/unresolved appendages are retained. No wings or hairs are fabricated. Amber material is false colour. The paper/API repeat a suspect mass; no mass is used here.

ETAIN / Arno Thielens worker honeybee micro-CT surface, in native millimetres. Its approximately 11 mm body is preserved within the catalog’s representative 12.5 mm scale, rather than enlarged to fill it. The preserved compact pose and unresolved/absent wing and leg detail remain as in the scan; no flying pose, hair or missing appendages are invented. Amber false colour is for inspection, not measured pigmentation.

## Rebuild

Stage UID `ee629bd30e4a47899de1b30b9b71c905` with `scripts/sketchfab_models.py stage` (owner's token file outside the repo), texture size 1024, archive allowance 100 MB and staged GLB allowance 150 MB. Large staging files remain outside the repository. Then run:

```sh
node scripts/prepare_bio3d2_imports.mjs /tmp/bio3d2/staged /tmp/bio3d2/processed MODULE_ROOT
```

`MODULE_ROOT` contains glTF Transform 4.5.0 and meshoptimizer. The script verifies source pins, converts legacy specular/glossiness to metallic/roughness, deduplicates/flattens/joins/welds the static scene, simplifies toward 50k triangles with error tolerance 0.005, prunes and quantizes. Only standard JPEG/PNG and decoder-free glTF are delivered; meshoptimizer is used offline, not as runtime mesh compression. The error bound may prevent reaching the exact target. No independent axis scaling is applied.

The final complete entry is [handoff JSON](../../../../handoff/bio3d2/bio3d2-honeybee.entry.json). Review limitations and skipped alternatives are in [REPORT.md](../../../../handoff/bio3d2/REPORT.md).
