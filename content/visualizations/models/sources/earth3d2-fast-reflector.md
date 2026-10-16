# FAST — nominal spherical reflector only

Original dimensioned illustration by Universe Scales, CC0 1.0. Offline builder:
`scripts/build_earth3d2_structures.py`. No third-party artwork or model is copied.

## Scientific basis (opened 2026-10-16)

- [Li et al., *Adapting Active Reflector Technology for greater sensitivity and
  sky-coverage in FAST-like Telescopes*, §1](https://arxiv.org/html/2012.11167v1):
  nominal spherical primary radius **300 m**, physical opening **500 m**;
  the illuminated area is reshaped into a paraboloid of approximately **300 m**
  aperture. These are three different dimensions, not interchangeable.
- [Nan et al. 2011, FAST project, §3.2](https://arxiv.org/pdf/1105.3794):
  active cable net and approximately triangular reflector elements;
  individual-panel curvature differs from the overall nominal sphere.

## Representation and calibration

The actual geometry is the analytic cap `y = R − sqrt(R² − x² − z²)` inside
the 250 m radius aperture, with equal horizontal and vertical metres.
Normals point into the concave collecting face. Reference size is **500 m**,
not the 300 m illuminated area. The cap's derived depth is approximately
134.169 m; no independent depth value or vertical exaggeration is applied.

This is the **nominal reference sphere**, not FAST's observing paraboloid or
a surveyed position of every panel. A deterministic original triangular
texture suggests panel organization; its pattern and count are illustrative.
It is not a reconstruction of the actual geodesic panel layout. No false
claim to a specific number of measured panels is made.

Feed cabin, suspension towers, cable net, actuators, terrain and supporting
structure are omitted. The isolated reflector is explicitly qualified in the
display name, on-model annotation and registry note. The surface is zero
thickness and double-sided; it does not claim a solid bowl, rear profile,
aluminum thickness or geological sinkhole geometry. Gray aluminum colors and
studio reflections are illustrative. Production WebGL review remains pending.
