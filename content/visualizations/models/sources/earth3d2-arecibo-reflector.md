# Arecibo — idealized pre-collapse reflector only

Original dimensioned illustration by Universe Scales, CC0 1.0. Offline builder:
`scripts/build_earth3d2_structures.py`. No downloaded observatory mesh or photo.

## Scientific basis (opened 2026-10-16)

- [National Research Council, *Working Papers: Astronomy and Astrophysics Panel
  Reports* (1991), Planetary Astronomy, “Arecibo Radar Facility Upgrade”](https://www.nationalacademies.org/read/1635/chapter/11):
  **305 m diameter** fixed reflector, a section of a **265 m radius sphere**.
- [Cornell Chronicle, 1997 upgrade facts](https://news.cornell.edu/stories/1997/06/some-facts-and-little-history-about-arecibo):
  aluminum panels nominally **3 × 6 ft**; the original wire mesh was replaced
  by aluminum panels. The original rectangular panel texture is an
  approximation, not a measured layout or a claim that every panel is identical.

## Representation and calibration

Reference size is **305 m**. The analytic cap is
`y = 265 − sqrt(265² − x² − z²)`, with aperture radius 152.5 m.
Its resulting vertex-to-rim depth is approximately **48.277 m**. Cornell's
news page quotes 161 ft/51 m (itself an inconsistent conversion); this model
preserves the stated spherical radius and diameter instead of independently
stretching the cap to that rounded depth. Both metric axes have equal scale.

This is an idealized **intact pre-December-2020 reflector**, not the current
observatory. Feed platform, Gregorian system, suspension cables and towers,
ground screen, support structure and surrounding terrain are omitted.
All display qualifiers say reflector only; it must not be described as a
complete pre-collapse observatory reconstruction.

The zero-thickness, double-sided surface makes no solid-bowl, shell-thickness
or rear-structure claim. Normals face into the collecting surface. Color,
panel texture and studio reflection are illustrative. CPU previews do not
certify WebGL material, aliasing or overlay behavior; production review remains.
