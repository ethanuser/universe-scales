# source3d-space — bounded astronomical source audit

2026-10-28. **No model or scripts added.** The Dinkinesh leads reviewed in this
pass did not meet both the requested numerical-geometry and explicit reuse
requirements. A small scan of the current Length export found no alternate
astronomical item with an immediately suitable measured mesh/data product.
No registry, runtime, dataset, export, existing asset, or existing report was
changed. The pre-existing modified `.DS_Store` was left untouched.

## Dinkinesh

The 2025 open-access geology paper is a fresh, primary lead:
[Bierhaus et al. (2025), PSJ 6, 299](https://doi.org/10.3847/PSJ/ae1968).
It says its updated numerical shape is based on Lucy L'LORRI data, with
2.1 m/pixel ground sampling on resolved areas and median radial error 1.7 m.
However, only about 60% of the surface is image-derived. The unseen hemisphere
is refined from an earlier superellipsoid using low-order perturbations to
match inertia-axis alignment, center-of-mass offset, and departure light curves.
Thus a full-body mesh would contain explicitly model-derived unseen terrain,
not measured surface topography. That does not itself disqualify a scientific
shape solution, provided the inferred coverage is documented. The paper says a full shape-model description
was still in preparation; the paper's figure is not a numerical mesh release.
The same paper gives maximum dimensions 910 x 870 x 716 m and equivalent
sphere diameter 738 m.

Fresh download lead checked: [Duncan Lyster's public TEMPEST repository](https://github.com/duncanLyster/TEMPEST),
whose Dinkinesh numerical shape is described by its discoverer as a model input.
The repository README describes a modified-MIT license requiring attribution
for public derivatives, but that is the software license; no separate explicit
CC BY, CC0, or public-domain grant for the bundled asteroid shape data was
verified. The available description also does not establish that its mesh is
the 2025 revised model, nor provide the mesh's source/version, extent, coverage,
and frame provenance in a directly verifiable data record. It therefore was
not acquired or copied. Repository presence or public downloadability alone is
not a qualifying data license.

Other fresh/primary routes checked:

- [DLR 2024 shape-model abstract and paper](https://elib.dlr.de/211156/): documents
  the photogrammetric work and partial stereo coverage, but the record exposes
  a conference abstract/PDF, not the numerical mesh or an explicit mesh reuse
  grant.
- [Lucy mission page](https://lucy.swri.edu/Dinkinesh.html) and
  [NASA overview](https://science.nasa.gov/solar-system/asteroids/dinkinesh/):
  provide images and mission summaries, not a released shape mesh with terms.
- [NAIF Lucy DSK directory](https://naif.jpl.nasa.gov/pub/naif/LUCY/kernels/dsk/)
  and its PDS4 counterpart were already checked in `handoff/retry3d/REPORT.md`;
  that report found only the Donaldjohanson DSK. This was not repeated as a new
  acquisition attempt.
- [CelestiaContent model credits](https://github.com/CelestiaProject/CelestiaContent)
  identify Dinkinesh models by ItzImcool but do not provide a CC BY/CC0/public-
  domain grant for the mesh. No model was imported from it.

The paper's openly accessible text is useful scientific evidence, but the
figure raster cannot be converted into a mesh without inventing depth. No
geometry was reconstructed from it. A source-released scientific shape solution
could be used once its numerical data, provenance and reuse rights are verified.

## Alternative Length anchors

The production coverage report, rather than registry-only matching, is the
authority for missing models: `Oort Cloud` and `Solar System` already have runtime
representations and are not gaps. `Milky Way Central Bar` and `Distance to the
Virgo Cluster` remain photo-only. A public density solution or catalog with
documented coordinates and selection could support a data-derived representation;
neither was acquired and qualified in this bounded pass. These are unresolved
leads, not proof that suitable data does not exist.

## Decision

No proposed entry JSON, GLB, source cache, or builder is supplied. Resume only
when a source provides a downloadable numerical mesh with traceable version,
coordinate frame, physical scale, covered/measured versus inferred regions,
and an explicit compatible reuse license. For Dinkinesh, the strongest next
lead is an author/PDS release of the revised numerical shape model and its
source-level license/provenance, rather than another search for an image or
secondary viewer copy.
