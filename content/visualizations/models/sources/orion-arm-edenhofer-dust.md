# Orion Arm: local measured 3D dust

Source: [Edenhofer et al., Zenodo 8187943](https://zenodo.org/records/8187943),
CC BY 4.0. Scientific basis: [A parsec-scale Galactic 3D dust map out to 1.25 kpc
from the Sun](https://arxiv.org/abs/2308.01295).

The model is a physical local window of the published three-dimensional mean
extinction-density grid, inside the Local/Orion Arm. It does not establish the
arm's full width or length. Its 15,707 points are the densest 5% of finite
16-pc-spaced grid samples in a 1,072-pc-wide cube around the Sun. False colors
encode density; no depth, clouds or stars were synthesized.

See [complete conversion and scope](deepsky3d-models.md#orion-arm) and the
[pinned source manifest](deepsky3d/manifest.json). Source refresh uses
`scripts/prepare_deepsky3d_dust.py`; the offline build needs no FITS dependency.
