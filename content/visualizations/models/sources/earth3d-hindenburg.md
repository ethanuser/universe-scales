# Hindenburg: 3D model provenance

Authored Hindenburg airship by hank2, uniformly calibrated to 245 m overall length. Envelope, gondolas, fins and historically contextual tail markings are retained. The neutral envelope material is lightened for legibility; no independent axis scaling. Internal framework and gas bags are the artist’s illustration, not a structural survey.

- Source: https://sketchfab.com/3d-models/hindenburg-airship-b347e808f561465dab568fa61734e262
- Credit: hank2 on Sketchfab
- License of the delivered model: CC-BY-4.0 (http://creativecommons.org/licenses/by/4.0/)
- Dimensional/scientific basis: https://www.airships.net/hindenburg/disaster/commerce-department-report/

## Calibration

Runtime presentation (angles in degrees): `{"pre_rotation": {"y": 90}, "measure_axis": "x", "yaw": -8, "pitch": 8}`.

Scaling is uniform on all three axes. The catalog value calibrates the stated axis or explicit reference size; it does not certify the source as a surveyed specimen. The per-item note above states the extent and representation.

## Rebuild and review

Builder: `scripts/prepare_earth3d_imports.mjs`. See `handoff/earth3d/REPORT.md` for commands, source preparation, checks and remaining production-browser work.

The rest/side images in `handoff/earth3d/previews/` are CPU orthographic previews. They include geometry, base-color textures and approximate lighting; they do not verify WebGL materials, reflections, perspective, picking, neighboring-item spacing, labels, the explorer or mobile behavior.

## License verification and source identity

Opened `https://api.sketchfab.com/v3/models/b347e808f561465dab568fa61734e262` on 2026-10-16. The API reports `license.slug: by` and `isDownloadable: true`. Public license/author evidence is retained in `earth3d-imports/hindenburg.license.json` (relative to this directory).

Original model title: Hindenburg airship. Source glTF archive: 1,188,561 bytes; SHA-256 `a41932b598ff81b644543c21f4046d5d74a80bf7ecfcab88096ad6012e03f842`.

Source archives and temporary download URLs are not committed. Staging reads the owner’s token from a file; neither tokens nor download URLs appear in the model, evidence files or report. The delivered self-contained GLB contains only PNG/JPEG textures and plain/quantized glTF geometry, with no Draco, Meshopt, KTX2 or WebP.
