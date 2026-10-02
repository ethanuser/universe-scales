# Length Review: Baseline Round 1

Review count: **1 of 3**. Date: 2026-09-16. Scope: **length only**.

**Execution: 3/10. Accuracy: 4/10. Overall: min(3, 4) = 3/10. Not ready.**

Inspected `http://127.0.0.1:8002/?dimension=length` in the dedicated `agent-browser --session critic-length` session. Captured and visually viewed desktop 1280x900 and mobile 390x844 screenshots. This assesses the baseline loaded at the start of this review, not the parent's concurrent edits. I did not reload to mix implementations. On-disk controller code changed during review; equation findings below were confirmed against the functions actually loaded in the browser. No application code was edited.

## Highest-Impact Blockers

1. **[P1] This is still a pair comparison, not a continuous journey.** The stage renders the current item and its immediate predecessor at fixed lane centers, x=730 and x=240. Moving the reference exponent from 0.46844 to 0.49844 changes Butterfly/Human to Human/Giraffe: the human jumps across the stage rather than remaining spatially continuous. Nearest-item selection updates the pair, but does not make the experience a continuous world. Replace the pair-driven scene with persistent object positions and continuous camera/scale movement; let appropriate neighbors enter and leave the view without swapping lanes. Dropdown and Previous/Next may remain shortcuts, not the organizing mechanism.

2. **[P1] The pictures are not physically calibrated objects.** Human Height scales a cropped group photo without feet; Earth Diameter scales the black square around the planet; Amazon River scales a local river image, not its full course. Electron scales a grid of atomic orbital illustrations. The loaded SVG uses `preserveAspectRatio="none"`, stretching every image into a square. The disclaimer admits that the entire frame represents the number, but that is not an approximate measurement of the depicted subject. Use a calibrated model/cutout for measurable objects; otherwise use a clearly labeled length bar and keep an explicitly unscaled identification thumbnail separate. Distinguish height, diameter, radius, path length, separation, and theoretical length scales in the scene, not only in prose.

3. **[P1] The renderer changes physical scale at the large-size cap.** The intended equation is `S = 10^z m`, `w_raw = 200 * L / S` in SVG units, with a 200-unit reference bar. However, rendered width is `min(2200, w_raw)`. At `z = -25.0015586`, Quark (`4.3e-19 m`) should span about `8.63e8` SVG units but is rendered at 2200. The warning says the object extends beyond the view, not that its geometry has been rescaled by roughly 392,000 times. Cull or geometrically clip at the true scale; do not shrink geometry and retain a physically meaningful ruler. Unsupported upper bounds should not become literal solid-object dimensions either.

4. **[P1] The electron entry contains a demonstrably wrong quantitative explanation.** The displayed `2.80e-15 m` is approximately the classical electron radius, yet the name is just Electron and the image is atomic orbitals. The visible text claims electrostatic self-energy would exceed rest energy by 200,000 at this radius. From `r_e = e^2/(4*pi*epsilon_0*m_e*c^2)` and the charged-shell energy `U = e^2/(8*pi*epsilon_0*r)`, setting `r=r_e` gives `U/(m_e*c^2)=1/2`, not 200,000. This is a model-dependent classical length scale, not the measured physical radius of an electron. Rename it, remove the erroneous claim, and render a theoretical-length marker rather than a scaled orbital image. References: [NIST CODATA constants](https://physics.nist.gov/cuu/Constants/Table/allascii.txt), [Feynman Lectures II, chapter 28, equations 28.1 and 28.6](https://www.feynmanlectures.caltech.edu/II_28.html).

5. **[P1] Real sourced 3D is absent even for an available example.** Earth remains an SVG photograph with no model, orbit control, model provenance, or calibration disclosure. NASA offers an [Earth 3D model in glTF and USDZ](https://science.nasa.gov/resource/earth-3d-model/). Integrate a sourced, normalized asset with an explicit diameter and shared scene scale. Asset availability does not establish metrological accuracy: verify bounds, units, attribution, and projection instead of assuming a downloaded model is inherently calibrated.

6. **[P2] The explorer does not fit the initial viewport, and explanatory notes are expanded.** At 390x844, the toolbar starts around y=566, the stage spans y=682-892, and zoom settings start around y=1104. Thus the initial view shows only part of the scene and no zoom control. The expanded caption consumes about 131 px between the scene/comparison buttons and zoom. The desktop top screenshot also cuts off the lower scene and zoom. Collapse the introduction/method notes behind an info control and size the explorer around available viewport height, keeping navigation, zoom, selected value, and scene together. The visible mobile toolbar buttons do wrap within 390 px; horizontal overflow was not found (`scrollWidth=390`). The failure is vertical composition, not an overflowing toolbar.

## Equation And Data Spot Checks

- **Correct core proportionality before capping:** initial Human/Butterfly lengths are 1.7 m and 0.1 m; loaded SVG widths were 200.9267 and 11.8192 units, giving the correct 17:1 frame-width ratio. This does not validate the photographed subjects' scale.
- **Zoom is real but selection is discontinuous:** a synthetic wheel event on the stage changed exponent 0.22844 to 0.47844. Input changes selected nearby entries. Native CLI wheel attempts scrolled the document instead; physical wheel/trackpad behavior therefore remains unverified, not certified as working or definitively broken.
- **Planck length number:** `1.616e-35 m` is consistent with rounded CODATA `1.616255e-35 m`. This numerical check does not validate the accompanying claims about spacetime foam or a proven minimum distance. [NIST CODATA](https://physics.nist.gov/cuu/Constants/Table/allascii.txt).
- **Proton charge radius:** loaded value `8.7e-16 m` is about 3.5% above CODATA `8.4075e-16 m`. Update it or explicitly identify a historical measurement and uncertainty; keep rms charge radius distinct from a hard spherical boundary. [NIST CODATA](https://physics.nist.gov/cuu/Constants/Table/allascii.txt).
- **Earth's magnitude:** `1.27e7 m` is plausible at the displayed precision; NASA gives 12,756 km equatorial diameter. This checks the order/rounding, not the dataset's specific mean-diameter provenance. [NASA Earth facts](https://science.nasa.gov/earth/facts/).
- **Needs substantiation, not certified:** the loaded Neutrino entry gives `1e-12 m` as quantum-mechanical size without a visible energy, wavelength definition, or bound. Do not turn that unexplained number into a physical body size. Full particle, astronomical, and biological datasets were not audited.

## Evidence And Limits

All screenshots below were opened and visually inspected. Desktop files are 1280x900; mobile files are 390x844. Top screenshots are viewport captures, not full-page reductions.

- [Desktop initial view](/tmp/critic-length-r1-desktop.png)
- [Desktop scrolled controls and open notes](/tmp/critic-length-r1-desktop-controls.png)
- [Mobile initial view](/tmp/critic-length-r1-mobile.png)
- [Mobile scrolled controls and open notes](/tmp/critic-length-r1-mobile-controls.png)
- [Desktop extreme-gap cap](/tmp/critic-length-r1-desktop-gap.png)
- [Desktop Earth and Amazon photo frames](/tmp/critic-length-r1-desktop-earth.png)
- [Desktop electron claim and orbital image](/tmp/critic-length-r1-desktop-electron.png)

Verified a working item dropdown, source-link presence, rendered length ratios, nearest-item transition, synthetic wheel handler, expanded notes, and layout at the two requested sizes. Not verified: real-device pinch/touch gestures, physical trackpad continuity, complete keyboard/screen-reader access, cross-browser behavior, every source link, licensing/calibration of all assets, or every data record. No claim of exhaustive scientific certification. Parent changes after the initial page load require a requested rereview; two review rounds remain.
