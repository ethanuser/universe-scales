# Rotifer — Rotifera

## Source and permission

- Model: [Rotifera](https://sketchfab.com/3d-models/rotifera-f300e988fa5d4e749b04445efebfba8a) by **.hapto GmbH** (`.hapto`).
- [Official Sketchfab API](https://api.sketchfab.com/v3/models/f300e988fa5d4e749b04445efebfba8a) opened 2026-10-16: downloadable, license slug **`by`**, [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/).
- Compact API/license and source-archive checksum record: [bio3d2/rotifer.json](bio3d2/rotifer.json). No download token or signed URL is retained.
- The local asset is a modified derivative; original attribution and license are retained in its registry entry.

## Definition and changes

The source description links Senckenberg’s soil-life project. This is its authored bdelloid illustration, not a scan. The catalog’s representative 200 µm is assigned uniformly to the complete corona-to-toes Y span. [Rotifer size context](https://en.wikipedia.org/wiki/Rotifer) gives a broad usual range; this is not a species identification or a measured specimen. Original paint was stored in an emissive texture; it is used as base colour to respond to explorer lights. Cilia remain static.

A bdelloid rotifer illustration by .hapto GmbH for Senckenberg’s soil-life project, uniformly calibrated corona-to-toes to the catalog’s representative 200 µm length. The paired ciliated corona and telescoping body are authored anatomy, not a scan or an identified measured specimen. Original painted colours are retained in a light-responsive material; the cilia are static.

## Rebuild

Stage UID `f300e988fa5d4e749b04445efebfba8a` with `scripts/sketchfab_models.py stage` (owner's token file outside the repo), texture size 1024, archive allowance 100 MB and staged GLB allowance 150 MB. Large staging files remain outside the repository. Then run:

```sh
node scripts/prepare_bio3d2_imports.mjs /tmp/bio3d2/staged /tmp/bio3d2/processed MODULE_ROOT
```

`MODULE_ROOT` contains glTF Transform 4.5.0 and meshoptimizer. The script verifies source pins, converts legacy specular/glossiness to metallic/roughness, deduplicates/flattens/joins/welds the static scene, simplifies toward 50k triangles with error tolerance 0.005, prunes and quantizes. Only standard JPEG/PNG and decoder-free glTF are delivered; meshoptimizer is used offline, not as runtime mesh compression. The error bound may prevent reaching the exact target. No independent axis scaling is applied.

The final complete entry is [handoff JSON](../../../../handoff/bio3d2/bio3d2-rotifer.entry.json). Review limitations and skipped alternatives are in [REPORT.md](../../../../handoff/bio3d2/REPORT.md).
