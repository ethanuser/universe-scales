# Golden Gate Bridge main span — original exterior diagram

Original geometry by Universe Scales, CC0 1.0. No downloaded bridge mesh,
photograph, engineering drawing pixels or third-party artwork is embedded.
Built offline by `scripts/build_earth3d2_structures.py`.

## Dimensional basis (opened 2026-10-16)

- [Golden Gate Bridge District: design and construction statistics](https://www.goldengate.org/bridge/history-research/statistics-data/design-construction-stats/):
  4,200 ft between tower centers (1,280.16 m using the international foot),
  90 ft overall deck width, towers 746 ft above water and 500 ft above roadway,
  33 × 54 ft tower-leg base dimensions, 36⅜ inch main-cable diameter,
  2 11/16 inch suspender diameter and 50 ft suspender spacing.
- [District-hosted Sheppard/Tongue chapter, Table 3.1](https://www.goldengate.org/assets/1/6/ggb-exhibit-chapter-statistics.pdf):
  144 m main-cable sag. The builder uses a **parabolic approximation** through
  that sag and the tower tops. It does not claim a surveyed cable curve or
  copy the erroneous/mixed simplified curve descriptions on other education pages.
- [District: how the bridge spans the Golden Gate](https://www.goldengate.org/exhibits/how-the-bridge-spans-the-golden-gate/):
  the trusses hand their loads to suspenders at 50 ft intervals.

## What is shown

Only the central span and its two towers. Side spans, anchorages, approaches,
water, terrain, submerged foundations and internal construction are omitted.
The cut is visibly qualified in the display label and on-model annotation.
Reference size is **1,280 model metres**, matching the unchanged catalog's
rounded 1,280 m. Tower centers remain 1,280.16 m apart; tower bodies slightly
increase the exterior width, which remains within the size rule.

Tower taper, cross-bracing, truss depth and member sections, flat roadway,
markings, plinths and colors are authored exterior simplifications. They are
not measured details or a structural analysis. Deck center elevation follows
746−500 ft; the source's 220 ft navigational clearance is a different measure
and was not substituted for deck elevation. Cable thickness is not enlarged
to keep it visible: thin cables may naturally become subpixel at small sizes.

## Review

CPU textured geometry previews and dimensional checks are in
`handoff/earth3d2/previews/`. These do not verify WebGL lighting, overlay labels,
perspective or UI. Production model-lab and mobile review remain for the lead.
