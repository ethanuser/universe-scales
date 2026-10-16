# Elephant Bird Egg: 3D model provenance

Real surface scan of RISD Nature Lab accession 132.32, reassembled from eggshell fragments and presumed by the collection to be an elephant-bird egg. Uniformly calibrated to the catalog’s representative 33 cm long axis, not a measured dimension or confirmed species identification of this particular specimen. Scan cracks and repaired fragments are retained; no invented shell geometry.

- Source: https://sketchfab.com/3d-models/elephant-bird-egg-c46a999a49d547d8bab39706d7a6b6ee
- Credit: RISD Nature Lab (RISDNaturelab); scan by Vir Naidu
- License of the delivered model: CC-BY-4.0 (http://creativecommons.org/licenses/by/4.0/)

## Calibration

Runtime presentation (angles in degrees): `{"measure_axis": "y", "yaw": -15, "pitch": 5, "pre_rotation": {"x": -20.697266, "z": 2.150853}}`.

Scaling is uniform on all three axes. The catalog value calibrates the stated axis or explicit reference size; it does not certify the source as a surveyed specimen. The per-item note above states the extent and representation.

## Rebuild and review

Builder: `scripts/prepare_earth3d_imports.mjs`. See `handoff/earth3d/REPORT.md` for commands, source preparation, checks and remaining production-browser work.

The rest/side images in `handoff/earth3d/previews/` are CPU orthographic previews. They include geometry, base-color textures and approximate lighting; they do not verify WebGL materials, reflections, perspective, picking, neighboring-item spacing, labels, the explorer or mobile behavior.

## License verification and source identity

Opened `https://api.sketchfab.com/v3/models/c46a999a49d547d8bab39706d7a6b6ee` on 2026-10-16. The API reports `license.slug: by` and `isDownloadable: true`. Public license/author evidence is retained in `earth3d-imports/elephant-bird-egg.license.json` (relative to this directory).

Original model title: Elephant Bird Egg. Source glTF archive: 19,805,196 bytes; SHA-256 `a72f175fc58623041cfa045a8731dc9c1a6cb38548d5dc43129d13e317e6f10d`.

Source archives and temporary download URLs are not committed. Staging reads the owner’s token from a file; neither tokens nor download URLs appear in the model, evidence files or report. The delivered self-contained GLB contains only PNG/JPEG textures and plain/quantized glTF geometry, with no Draco, Meshopt, KTX2 or WebP.

The scan’s long axis leans in its original file. A surface-area-weighted principal-component fit gives long-axis unit vector (0.03510845, 0.93480184, 0.35343021). The recorded rigid pre-rotation aligns that direction to Y before the 33 cm calibration. This prevents the original leaning pose from inflating the egg’s actual long dimension. No vertex positions are deformed.
