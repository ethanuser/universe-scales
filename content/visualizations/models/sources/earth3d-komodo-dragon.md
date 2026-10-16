# Komodo Dragon: 3D model provenance

Authored Komodo dragon illustration by denys4624, uniformly calibrated nose to tail to the catalog’s representative 2.6 m adult-male length. The extended tail is included. This is an artist’s animal, not a scan, measured specimen or anatomical reconstruction; surface details and pose are illustrative.

- Source: https://sketchfab.com/3d-models/komodo-a3bb3a390dd1466e9bbab4a994329d45
- Credit: denys4624 on Sketchfab
- License of the delivered model: CC-BY-4.0 (http://creativecommons.org/licenses/by/4.0/)
- Dimensional/scientific basis: https://nationalzoo.si.edu/animals/komodo-dragon

## Calibration

Runtime presentation (angles in degrees): `{"pre_rotation": {"y": 90}, "measure_axis": "x", "yaw": -10, "pitch": 7}`.

Scaling is uniform on all three axes. The catalog value calibrates the stated axis or explicit reference size; it does not certify the source as a surveyed specimen. The per-item note above states the extent and representation.

## Rebuild and review

Builder: `scripts/prepare_earth3d_imports.mjs`. See `handoff/earth3d/REPORT.md` for commands, source preparation, checks and remaining production-browser work.

The rest/side images in `handoff/earth3d/previews/` are CPU orthographic previews. They include geometry, base-color textures and approximate lighting; they do not verify WebGL materials, reflections, perspective, picking, neighboring-item spacing, labels, the explorer or mobile behavior.

## License verification and source identity

Opened `https://api.sketchfab.com/v3/models/a3bb3a390dd1466e9bbab4a994329d45` on 2026-10-16. The API reports `license.slug: by` and `isDownloadable: true`. Public license/author evidence is retained in `earth3d-imports/komodo-dragon.license.json` (relative to this directory).

Original model title: Komodo. Source glTF archive: 2,303,250 bytes; SHA-256 `0da82072321346a8050c8619e4bbfad7c6edc1b3dd0a073cd2f37c4bf58d5694`.

Source archives and temporary download URLs are not committed. Staging reads the owner’s token from a file; neither tokens nor download URLs appear in the model, evidence files or report. The delivered self-contained GLB contains only PNG/JPEG textures and plain/quantized glTF geometry, with no Draco, Meshopt, KTX2 or WebP.

The 2.6 m representative length is the existing catalog value, retained without revision. Smithsonian’s National Zoo provides general species context; it is not a measurement of this authored model or an individual animal.
