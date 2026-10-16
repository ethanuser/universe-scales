# Boeing 747-8: 3D model provenance

Authored Boeing 747-8 Intercontinental model by AF267 (jsong.js.us), originally configured for GeoFS. Calibrated uniformly nose to tail to the catalog’s 76.3 m overall length. The model’s span-to-length ratio is about 0.898, close to Boeing’s 68.4/76.3; local details, livery and landing gear are illustrative rather than an engineering survey. No geometry is stretched independently.

- Source: https://sketchfab.com/3d-models/boeing-747-8i-cd1977bedc32412fa1ce2cda23520b84
- Credit: AF267 (jsong.js.us) on Sketchfab
- License of the delivered model: CC-BY-4.0 (http://creativecommons.org/licenses/by/4.0/)
- Dimensional/scientific basis: https://www.lufthansa.com/br/en/articles/explore-flying/essentials-surprising-lufthansa-numbers

## Calibration

Runtime presentation (angles in degrees): `{"measure_axis": "x", "yaw": -15, "pitch": 12}`.

Scaling is uniform on all three axes. The catalog value calibrates the stated axis or explicit reference size; it does not certify the source as a surveyed specimen. The per-item note above states the extent and representation.

## Rebuild and review

Builder: `scripts/prepare_earth3d_imports.mjs`. See `handoff/earth3d/REPORT.md` for commands, source preparation, checks and remaining production-browser work.

The rest/side images in `handoff/earth3d/previews/` are CPU orthographic previews. They include geometry, base-color textures and approximate lighting; they do not verify WebGL materials, reflections, perspective, picking, neighboring-item spacing, labels, the explorer or mobile behavior.

## License verification and source identity

Opened `https://api.sketchfab.com/v3/models/cd1977bedc32412fa1ce2cda23520b84` on 2026-10-16. The API reports `license.slug: by` and `isDownloadable: true`. Public license/author evidence is retained in `earth3d-imports/boeing-747-8.license.json` (relative to this directory).

Original model title: Boeing 747-8i. Source glTF archive: 2,801,303 bytes; SHA-256 `c3684c87c07e876dd26fba64d89bf4dc89085647af7c1c509771b521a3241316`.

Source archives and temporary download URLs are not committed. Staging reads the owner’s token from a file; neither tokens nor download URLs appear in the model, evidence files or report. The delivered self-contained GLB contains only PNG/JPEG textures and plain/quantized glTF geometry, with no Draco, Meshopt, KTX2 or WebP.

## Dimensions opened and checked

- [Lufthansa, Essentials: 5 Surprising Numbers from Lufthansa’s History](https://www.lufthansa.com/br/en/articles/explore-flying/essentials-surprising-lufthansa-numbers), opened 2026-10-16, gives the 747-8 Intercontinental's 76.3 m length. This matches the existing catalog value.
- [Boeing AERO, Operating the 747-8 at Existing Airports](https://www.boeing.com/content/dam/boeing/v2/airports/7478-airport-comp/AERO_2010_q3_article3.pdf), opened 2026-10-16, page 16 and figure 3 give 68.4 m wingspan. The imported geometry's precise span/length ratio is 64.53568 / 71.88434 = 0.89777; the published comparison is 68.4 / 76.3 = 0.89646. Units of the authored source do not need to be real metres because calibration is uniform and explicit.

The older Boeing Startup overview URL returned 404 during direct verification; the live manufacturer and operator sources above replace it. No copyrighted technical drawings or manufacturer photos are bundled.
