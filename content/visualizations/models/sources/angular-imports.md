# Imported clock and record deck (2026-10-20)

This batch reuses two original Innerscene models released under CC0 1.0. The
part pages and the library terms were checked on October 20, 2026. Source URLs,
download URLs, byte counts and SHA-256 hashes are pinned in `models.json`.

| Asset | Source | Hosted size | Triangles | Observations |
| --- | --- | --- | --- | --- |
| Round Time | [Source and CC0 dedication](https://www.innerscene.com/tools/library/3d-parts/round-time-wall-clock-e937bcca) | 893,944 bytes | 9,468 | Hour hand; Minute hand |
| Walnut Spin | [Source and CC0 dedication](https://www.innerscene.com/tools/library/3d-parts/walnut-spin-turntable-1a5efb0a) | 1,222,792 bytes | 13,688 | 33 1/3 rpm record; 45 rpm vinyl record; 78 rpm record |

Library terms: <https://www.innerscene.com/tools/library/terms>.

## Preparation

Download the original files to temporary staging as `angular-clock-source.glb`
and `angular-walnut-spin-source.glb`, then run:

```sh
python3 scripts/prepare_angular_imports.py SOURCE_DIR OUTPUT_DIR
npx --yes @gltf-transform/cli@4.5.0 tangents OUTPUT_DIR/innerscene-clock-angular.glb FINAL_CLOCK.glb
npx --yes @gltf-transform/cli@4.5.0 tangents OUTPUT_DIR/innerscene-walnut-spin-angular.glb FINAL_DECK.glb
```

The script checks the reviewed source hashes and creates empty rotation groups
around existing source hub/spindle coordinates. Child translations are adjusted
to preserve their complete rest transforms. This first step leaves source mesh
and texture buffers unchanged. The final glTF Transform pass adds MikkTSpace
tangent attributes computed from existing positions, normals and UVs; it fixes
the source normal-map portability warnings. Surfaces, triangle counts, materials
and embedded images are preserved. No geometry or texture is authored. No
external decoder is needed. Both final assets validate with zero errors/warnings;
non-power-of-two source images produce informational messages only.

## Motion and Presentation

Clock hands rotate about the original hub. The clock's other hand is hidden
in each observation; the source has no second hand, so that observation retains
its previous illustration. Hour/minute variants have separate load-cache IDs,
preventing a hidden-hand variant from being reused for the other observation.
The source ash rim, raised indices, ivory dial and hand proportions are retained.

The deck's ten record/mat/label/groove nodes rotate around its existing spindle.
The spindle, bearing housing, cabinet and tonearm stay fixed. The separate motor
pulley is omitted because the belt/transmission is not modeled. The same authored
deck identifies three dataset speeds; it does not establish supported speeds or
record formats for a manufactured device. Source grooves and label are almost
rotationally symmetric, and the phase dial makes their rotation readable.

The camera looks along the selected rotation axis and uses the established
clockwise convention. Dataset values and plaques are unchanged.

## Verification and Handoff

The production browser lab sampled rest, quarter/half/three-quarter turns, a
non-symmetric phase and explicit simulated seconds. It checked the actual loaded
asset ID, fixed housing matrices, unchanged pivots, clockwise primary motion and
high-rate alias protection. Fresh loads through both the Hour hand and 78 rpm
record deep links were checked, plus 393 px viewport screenshots.

An existing startup race could cache a procedural fallback before the registry
arrived. Angular model creation now waits for that registry; failed/empty registry
responses still unlock the normal fallback path. `model_lab.cjs angular` checks
the loaded asset ID and accepts `--start "Item name"` to exercise a fresh deep link.

An independent visual critic scored execution/accuracy 8/8 for the clock and 9/8
for the deck. These are presentation judgments, not scientific certification.
The plain clock dial, symmetric record texture and unresolved stylus at small
display sizes remain source-model limitations.

For Claude: keep the authored second-hand clock and other mechanisms available.
These five observations now prefer downloaded assets. Candidate Direct Spin was
reviewed but omitted because it has no vinyl record. A separate low-poly HDD
listing was not imported because its component separation was not verified.
