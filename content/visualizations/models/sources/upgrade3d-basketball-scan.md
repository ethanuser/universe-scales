# Basketball — licensed photogrammetry replacement

The mesh is **Rugged Basketball**, a photoscan of a worn Spalding basketball by
**robin.sculac**, captured with **3DF Zephyr**. Its original seams, photographed
pebbling, faded markings and wear are retained. It replaces `earth3d-basketball`,
the project's dimensioned illustration. No geometry was modeled from scratch.

- [Original model and creator description](https://sketchfab.com/3d-models/rugged-basketball-008e9eacb9044b11b358a0c2bdae1934)
- [Source API record](https://api.sketchfab.com/v3/models/008e9eacb9044b11b358a0c2bdae1934)
- License checked at the source on 2026-10-23: **`by`**, downloadable,
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- Compact source/license snapshot: `upgrade3d-basketball-scan.source.json`.
- Delivered credit: **robin.sculac on Sketchfab**. The scan's photographed brand
  is not a project endorsement or a claim that the source was commissioned by
  the manufacturer.

## Calibration and limits

The catalog remains **0.239 m diameter**. The existing dimensional basis is the
[Wilson sizing guide](https://au.wilson.com/pages/how-to-choose-a-basketball/1000),
which lists **29.5 inches circumference** for size 7. Dividing that circumference
by pi and converting inches to meters gives about **0.23851 m**, rounded by the
catalog to 0.239 m.

**The scan does not supply a measured specimen diameter or identify its size.**
It is a real specimen of the same type, uniformly scaled to the representative
catalog diameter; it is not evidence that this particular ball is size 7. The
longest source bounding-box extent calibrates the diameter, with no independent
axis scaling. Resting yaw/pitch are zero. The slight surface irregularities and
worn color belong to the source and are not corrected into an ideal sphere.
No volume or watertightness claim is made.

## Processing and rebuild

Stage outside the repository using the existing importer (never save credentials
or signed download URLs in this repository):

```sh
SSL_CERT_FILE=/etc/ssl/cert.pem ./venv/bin/python scripts/sketchfab_models.py stage \
  --token-file ~/.config/universe-scales/sketchfab-token \
  --uid 008e9eacb9044b11b358a0c2bdae1934 \
  --output-dir /tmp/upgrade3d-staged --max-archive-mb 25 \
  --max-glb-mb 20 --texture-size 1024

node scripts/prepare_upgrade3d_imports.mjs /tmp/upgrade3d-staged \
  /tmp/upgrade3d-final /path/to/node_modules

python3 scripts/register_model.py \
  handoff/upgrade3d/upgrade3d-basketball-scan.entry.json \
  /tmp/upgrade3d-final/upgrade3d-basketball-scan.glb
```

Use **glTF Transform 4.5.0** (`core`, `extensions`, `functions`). The preparation
script verifies the source/archive and staged GLB hashes before processing.
It converts the legacy specular/glossiness material to standard PBR, then
deduplicates, flattens, joins, welds and prunes. Position/normal/UV quantization
uses 16/12/14 bits. There is **no decimation, remeshing, filling, recoloring,
invented texture or replacement geometry**. Mesh and texture compression codecs
are not used. Source textures are resized to at most 1024 pixels by the importer.

The archive SHA-256 is
`e9808befbc1d65281c7598e758edb1fc03d0f8435fad44c10aa69e161396ea0b`.
The staged GLB SHA-256 is
`83fbb446e3c60921548e74188597dfaffe2e6ae170d1d933c2e9f9aab3d4d626`.
Final bytes, hash and triangle count are recomputed in the registry and handoff
entry. Source material conversion preserves its visible photographed colors.

## Visual review

`handoff/upgrade3d/previews/` contains before/after rest, quarter-turn and small
CPU renders. The selected scan was also compared with akaro96's darker
[Basketball scan](https://sketchfab.com/3d-models/basketball-e4850557b63446acab091cd6bf31041c).
That alternative has an incomplete underside visible from some rotations; the
selected scan reads more consistently across the inspected views and is smaller.

CPU images use the registry's transforms, textured surfaces and a depth buffer.
They do not certify production WebGL materials, lighting, perspective, picking,
radial neighbors or mobile behavior. The lead must run the production model lab
outside the documented Chromium sandbox restriction before merging.
