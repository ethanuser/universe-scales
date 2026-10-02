# Particle-scale diagrams: sources and definitions

These scenes visualize reported length scales. Each has a one-unit calibrated
span and `presentation.reference_size: 1`; for the proton that span runs from
the center to the rms-radius circle. Its illustrative 3D cloud extends to both
sides of the center. Neither the quark limit nor the rms circle is a hard surface.

## Displayed scales

| Item | Displayed quantity | Value | Scene | Scientific interpretation |
| --- | --- | ---: | --- | --- |
| Planck Length | Planck length | `1.616255e-35 m` | `planck-length-ruler` | Derived from `sqrt(hbar G / c^3)` using 2022 CODATA. This does not establish a smallest possible or measured length. |
| Quark | Effective quark-radius upper limit | `< 4.3e-19 m` | `hera-quark-radius-limit` | HERA combined H1/ZEUS analysis; 95% CL, quark form-factor model. An exclusion bound, not a radius measurement. |
| Proton Radius | Proton rms electric charge radius | `0.84075(64) fm` (`8.4075e-16 m`) | `proton-rms-charge-radius` | 2022 CODATA recommendation as listed by PDG. An rms moment of the charge distribution, not its outer edge. |
| Electron | Classical electron radius `r_e` | `2.8179403205(13)e-15 m` | `classical-electron-radius` | CODATA constant/derived electromagnetic scale; not the measured physical extent of an electron. |
| 1 MeV Neutrino Wavelength | 1 MeV neutrino de Broglie wavelength | `1.239841984e-12 m` | `neutrino-wavelength-1mev` | Kinematic wavelength `h/p ~= hc/E`, using the ultrarelativistic approximation. It is energy-dependent, not intrinsic particle size. |

## Primary references

- NIST, *2022 CODATA recommended values*, including Planck length and classical
  electron radius: <https://physics.nist.gov/cuu/Constants/Table/allascii.txt>
  and <https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=958143>.
- Zarnecki, *Limits on the effective quark radius from inclusive ep scattering
  & contact interactions at HERA*, based on combined H1 and ZEUS data,
  arXiv:1611.03825: <https://arxiv.org/abs/1611.03825>. Its reported limit is
  `0.43 x 10^-16 cm`; converting centimeters to meters gives `4.3e-19 m`.
- Particle Data Group, proton charge-radius data block:
  <https://pdgprod.lbl.gov/pdgprod/pdgLive/DataBlock.action?node=S016CR>.
  PDG identifies the quantity as `sqrt(<r_E^2>)` and lists `0.84075 +/-
  0.00064 fm` from Mohr et al. (2025), the 2022 CODATA adjustment.
- Particle Data Group, *Neutrino Masses, Mixing, and Oscillations* (2024):
  <https://pdg.lbl.gov/2024/reviews/rpp2024-rev-neutrino-mixing.pdf>. Together
  with the NIST exact SI values of `h`, `c`, and the electron-volt, these support
  the relativistic 1 MeV wavelength calculation `lambda ~= hc/E`. PDG mass
  constraints support the ultrarelativistic approximation, not any neutrino
  spatial radius.
- Sick (2018), *Proton Charge Radius from Electron Scattering*, Atoms 6, 2,
  <https://doi.org/10.3390/atoms6010002>, discusses the nonrelativistic dipole
  approximation, `rho_D(r) proportional to exp(-sqrt(12) r/R_D)`.
- Miller (2010), *Transverse Charge Densities*,
  <https://arxiv.org/abs/1002.0355>, explains why the static three-dimensional
  Fourier-density interpretation is not rigorous for relativistic constituents.

## Drawing conventions

- Planck is one undivided, thin span with two end caps. The quark scale uses
  the same quiet style with an open endpoint for its upper bound. Definitions
  and caveats appear in the detail panel, leaving the object name unobstructed.
- The proton is a rotatable, isotropic 3D cloud sampled from the illustrative
  dipole density above. The radial sampling distribution is Gamma(shape=3,
  scale=R/sqrt(12)), including the spherical volume factor, so the infinite
  distribution has rms radius R. A center-to-circle line measures exactly R.
  The cloud is cropped at 1.25 R (about 80.7% of this model's integrated density),
  with a maximum displayed diameter of 2.5 R. Layout and focus explicitly
  accommodate that diameter; it must not be rescaled to make a radius equal
  a diameter. This is a nonrelativistic model illustration, not an experimentally
  reconstructed proton interior. No hard sphere or colored quark balls are added.
- The electron scene is a one-sided radial measurement spoke. There is no
  electron body/sphere.
- The neutrino scene contains one sinusoidal cycle with a bracket spanning one
  wavelength. The wave amplitude is graphic and carries no physical field or
  probability-density meaning. Its slow phase progression is illustrative,
  independent of the physical frequency. It does not rotate as a rigid object.
- Geometry is procedural and deterministic. Factories allocate independent
  Three.js objects per call; the scenes contain fewer than 80 children and far
  fewer than 60,000 triangles. Nonzero bar/curve geometry gives each scene a
  pickable hull. Rest, end-on and actual-explorer views were checked using the
  production model lab. End-on views of longitudinal measurements naturally
  foreshorten; their labels do not turn them into physical particle surfaces.

The procedural code and its authored runtime geometry use the project's MIT
code license; this source note uses the project's CC BY 4.0 documentation license.
