# Outer solar system: reference-based illustrations

The two runtime scenes in `js/experiences/outer-solar-models.js` are authored
diagrams, not downloaded observational reconstructions. They use AU coordinates
and the exact IAU conversion `1 au = 149597870700 m`. No NASA image or mesh is
redistributed. Source facts are cited; authored geometry follows the project's
code license.

## Oort Cloud

[NASA's Oort Cloud facts](https://science.nasa.gov/solar-system/oort-cloud/facts/)
give an uncertain inner edge at 2,000-5,000 AU and outer edge at 10,000-100,000 AU.
The Length item now explicitly adopts the upper outer radius, 100,000 AU, and
shows its **200,000 AU diameter**, 2.991957414e16 m. This is a representative
choice from a broad range, not a measured edge.

The flattened Hills cloud (2,000-20,000 AU) and approximately isotropic outer
sample (20,000-100,000 AU) are explanatory components. The transition, disk
thickness, particle density and individual positions are **illustrative**, not
cataloged comets. Background:
[NASA technical review](https://ntrs.nasa.gov/api/citations/19910013647/downloads/19910013647.pdf).
Three very faint great circles indicate a contextual scale, not a gas shell.
The Sun is positioned at the origin, with an enlarged ring to keep it visible.
On-stage labels name the Sun, Hills cloud and outer cloud; component ranges and
schematic caveats remain in the explorer note rather than as stage captions.

## Heliosphere

[NASA's Voyager interstellar-mission overview](https://science.nasa.gov/mission/voyager/interstellar-mission/)
reports termination-shock crossings at 94 AU and 84 AU, and Voyager 1's
heliopause crossing at about 122 AU. We use rounded 90 AU and 120 AU radial
scales. The Length value is a **representative 240 AU nose-region diameter**
(twice 120 AU), 3.5903488968e13 m, not a measured upwind-to-tail extent.

The two compressed, nose-side boundary sectors are a schematic cutaway; the
downstream shape is left open rather than implying a closed measured surface.
An upwind arrow and rounded-radius ruler explain the orientation. Radial tracers show
solar-wind flow before the shock; outer particles only suggest the heliosheath.
Neither supplies a reconstructed gas density or magnetohydrodynamic solution.
The stage uses a sparse set of flow arrows and omits a separate cutaway caption;
the open boundary shape is apparent in the geometry and explained here.
The short tail tracers are not scaled to a measured tail length. Their four-lobe
appearance references
[NASA's IBEX tail interpretation](https://www.nasa.gov/news-release/nasa-satellite-provides-first-view-of-the-solar-systems-tail/),
not a unique accepted global shape. For alternative inferred shapes see
[NASA's discussion](https://www.nasa.gov/solar-system/uncovering-our-solar-systems-shape/).

## Verification

Run `node --test tests/outer-solar-models.test.mjs tests/model-points.test.mjs`
and `node scripts/model_lab.cjs shot /tmp/outer-solar "Oort Cloud" "Heliosphere"
--views rest,side --bg dark`. The lab should report resting extents near 1x of
the listed values. Soft particle sprites are opt-in and generated locally; no
texture downloads or compression decoders are needed.
