# Area Review: Baseline Round 1

Review count: **1 of 3**. Area only. Reviewed 2026-09-16 at `http://127.0.0.1:8002/?dimension=area` using isolated `agent-browser --session critic-area`. No application code edited; no subagents. Parent implementation was ongoing: these scores describe the loaded baseline and captured screenshots, not subsequent disk changes or an untested reload.

## Ratings

| Criterion | Score | Reason |
| --- | --- | --- |
| Execution | **4/10** | Legible, functional selection and scale control, but fundamentally a two-item comparison rather than the requested continuous journey. Initial viewport fit and collapsed-note requirements fail. |
| Accuracy | **7/10** | Square-root scaling and sampled data are sound; equivalent-area/photo caveats are honest. Undisclosed clipping changes the visible area, and mobile loses the on-stage scale annotation. Not a dataset certification. |
| Overall | **4/10** | `min(execution, accuracy)`; not ready against the stated requirements. |

## Highest-Impact Blockers

1. **P1: Replace fixed pair lanes with a continuous scale scene.** The baseline uses `ctx.pair` (selected item plus predecessor) at fixed centers x=240 and x=730. Changing the slider from exponent 0.331211 to 0.351211 switches Human skin to Parking space: Human skin jumps from x=730 to x=240 while A4 disappears. This is a comparison carousel driven by zoom, not spatial continuity. Keep objects at persistent scene positions, introduce/remove them by visibility, and derive focus from the camera without teleporting surviving objects.

2. **P1: Keep the stage and essential controls visible; collapse explanatory notes by default.** At 1280x900, the baseline zoom input starts around y=1035, below the viewport. At 390x844, the toolbar starts around y=517, the stage spans y=634-844, and settings start around y=1009. The long introductory note, caption, and selected-item prose are expanded without a disclosure control. Compact the explorer shell and put methodology/prose behind accessible closed disclosures. Mobile has no horizontal overflow and its toolbar wraps correctly; the failure is vertical composition, not off-screen horizontal buttons.

3. **P1: Report clipping from actual geometry, not an unrelated size threshold.** Reproduction: select Human skin area and set the reference-span exponent to about -0.14 (input rounds to -0.13878866; displayed span 0.726 m). The skin square is 358.96 SVG units high with top y=-68.96, so about **19.2% of its area is outside the stage**, but `.experience-live` is empty. The baseline only warns when `raw > 380`; this square starts cropping when its side exceeds its baseline y=290. Compute bounds against the viewport and show an explicit partial-area indicator before any clipping. Do not let a partial rectangle appear to be the complete listed area. The renderer also caps geometry at 2200 units: avoid changing scientific scale through a geometry cap, even for mostly off-screen shapes.

4. **P1 requirement gap: Real sourced 3D is not demonstrated.** Inspected Human skin, A4, Moon, and Earth representations are SVG equivalent-area squares with photos, except Earth, which is a sourced 2D Equal Earth map. The map is useful and honest, but neither it nor a photo is a real 3D asset. Integrate appropriate sourced models where available, with source/license and physical calibration; retain explicitly labeled equivalent-area fallbacks elsewhere. A model's projected silhouette must not be passed off as its total surface area. Availability and suitability of models for every item were not audited.

5. **P2: Preserve readable mobile scene labels and the scale-bar value.** Both mobile captures show an unlabeled scale line and no in-stage object labels. Subject buttons below the stage help identification, and the slider eventually repeats the span, but the scene itself loses its direct quantitative reference. Keep readable labels or anchored callouts visible alongside the stage rather than removing its text at the mobile breakpoint.

## Accuracy Spot Checks

- The inspected equation is `side = 200 * 10^(log10(A)/2 - zoom)`, with a 200-unit bar representing `10^zoom` meters. Thus displayed square areas scale with A, not A squared. At the initial Human skin/A4 state, side lengths 201.8567 and 38.6733 give squared ratio **27.2436**, matching `1.7 / 0.0624`. This passes for uncapped, unclipped geometry.
- A4's stored 0.0624 m^2 agrees with rounding `0.210 * 0.297 = 0.06237 m^2`; dimensions checked against [HP's paper-size reference](https://support.hp.com/in-en/document/bpq04022).
- Using the mean radii in [NASA's Moon/Earth fact sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html), `4*pi*r^2` gives Earth approximately 5.10064e14 m^2 and Moon approximately 3.79323e13 m^2, consistent with the stored 5.10e14 and 3.79e13 values. These are spherical approximations, not detailed topographic surface measurements.
- The baseline caption correctly explains that squares represent equivalent areas and photos identify subjects rather than their shapes. Earth's caption explicitly includes oceans in the map footprint; code normalizes the complete projected sphere's area, not only land. The map attribution is visible. An equal-area map is not a uniform ground-distance map, so its linear reference must remain framed as diagram scale.
- Human skin's 1.7 m^2 was used to test rendering ratios, not independently certified as a universal human value. Other molecular, geographic, and cosmic data were not exhaustively checked.

## Evidence

All screenshots below were captured and visually opened, not merely saved.

- [Desktop initial, 1280x900](/tmp/critic-area-r1-desktop.png)
- [Desktop after wheel/page movement, 1280x900](/tmp/critic-area-r1-desktop-wheel.png)
- [Earth representation, 1280x900](/tmp/critic-area-r1-earth.png)
- [Undisclosed clipped square, 1280x900](/tmp/critic-area-r1-clipped-area.png)
- [Mobile initial, 390x844](/tmp/critic-area-r1-mobile.png)
- [Mobile scrolled to controls, 390x844](/tmp/critic-area-r1-mobile-controls.png)

## Verification Limits

- Item selection, slider input, numerical geometry, the Earth map, and both viewport layouts were inspected. A synthetic stage wheel event changed zoom by 0.25 and was canceled by the handler. The CLI's real-wheel attempt instead moved the document 500 px; native wheel hit-target behavior is therefore inconclusive, not certified working or declared broken.
- Mobile means a 390x844 browser viewport, not a physical touch device. Pinch gestures, touch dragging, screen-reader behavior, all unit conversions, every endpoint, animation smoothness, and 3D asset provenance/calibration were not verified.
- Do not count parent edits made after this loaded baseline as passing this review. A requested rereview should be round 2 and reload the implementation deliberately.
