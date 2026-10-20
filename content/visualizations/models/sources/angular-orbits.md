# Sourced bodies in Angular Velocity (2026-10-20)

This pass reuses existing credited GLBs; it adds no mesh, surface, orbit geometry,
texture, scientific dataset, or binary asset. Claude's inspection mechanisms are
left unchanged. The existing SVG circle and phase guide remain timing aids.

`js/experiences/angular-orbits.js` maps the eight orbital observations to:

| Observations | Orbiting asset | Central asset |
| --- | --- | --- |
| Pluto orbit around the Sun | `nasa-pluto` | `nasa-sun` |
| Mars orbit around the Sun | `nasa-mars-length` | `nasa-sun` |
| Earth orbit around the Sun | `nasa-earth` | `nasa-sun` |
| Venus orbit around the Sun | `nasa-venus` | `nasa-sun` |
| Mercury orbit around the Sun | `nasa-mercury` | `nasa-sun` |
| Moon orbit; Moon orbit around Earth | `nasa-moon` | `nasa-earth` |
| ISS orbit | `nasa-iss-length` | `nasa-earth` |

Source URLs, original authors, usage terms, processing and hashes remain in
`models.json`. The detail panel links both the orbiting and central model sources.
NASA usage guidelines are not relabeled CC0. Pluto's coverage limitations and the
ISS model's historic configuration remain in their notes.

The existing observation supplies angular speed in radians per second. The body
moves clockwise around the existing circular guide by omega times simulated
seconds. No observation is reinterpreted as a surface spin rate. Globe/satellite
attitude is held fixed; lunar synchronous orientation, axial spin, station attitude
control, ellipticity and current ephemerides are not simulated. Diameters and
orbit radii are independent display sizes, not physical proportions. This is
explicitly explained in the model note rather than claiming orbital reconstruction.

Each comparison lane has separate model instances even when they share one
source GLB. Center/body loading failures independently retain the existing SVG
center/photo fallback. The model lab now waits for both assets, samples four
orbital phases, checks translation with fixed center/attitude, and captures each
phase. Earth/Jupiter/Saturn axial-spin models are unchanged.

For Claude: continue authored mechanisms separately. These orbital slots already
use the downloaded bodies; avoid replacing them with new sphere stand-ins or
assigning orbital angular speed to their axial rotation. No dataset/plaque edits
are required for this integration.
