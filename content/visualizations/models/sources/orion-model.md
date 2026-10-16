# Orion Nebula: observed light, published 3D structure

Images (both CC BY 4.0):
- Hubble Orion Treasury mosaic, https://esahubble.org/images/heic0601a/ (30.03 arcmin square,
  north up). Credit: NASA, ESA, M. Robberto (Space Telescope Science Institute/ESA) and the
  Hubble Space Telescope Orion Treasury Project Team.
- Wide view, https://noirlab.edu/public/images/noao-m42steinberg/ (130.89 x 73.22 arcmin,
  north 79 degrees left of vertical). Credit: KPNO/NOIRLab/NSF/AURA/Ryan Steinberg and
  Family/Adam Block. Its listed center (Dec -4:41:52) disagrees with the image, which has the
  Trapezium near its middle, so the image is pinned at the Trapezium pixel (833, 512) and the
  shift refined by cross-correlation with Hubble (about 6 canvas px).

Both are resampled onto one north-up canvas, 64 arcmin (25.0 ly at 1,344 ly) centered on
theta-1 Ori C. Ground-based colors are scaled to Hubble's where they overlap; Hubble fills its
square. The photo becomes calibrated glowing sprites (scripts/nebula_volume.py): front-on, the
summed sprites reproduce the photo.

Depth follows published structure, placed illustratively:
- O'Dell et al. 2009, AJ 137, 367 (https://doi.org/10.1088/0004-6256/137/1/367): the bright
  gas is the main ionization front on the face of the Orion Molecular Cloud, about 0.2 pc
  (0.65 ly) behind the Trapezium, tilting toward us farther out.
- Pabst et al. 2019, Nature 565, 618 (https://arxiv.org/abs/1901.04221): theta-1 Ori C's wind
  has blown a bubble about 4 pc across whose near half-shell, the Veil, expands toward us at
  13 km/s.
Gas sits on that curved wall, with a share on the near half-shell (radius 6.5 ly) that grows
away from the center; the Orion Nebula Cluster's stars sit in front of the wall. Neither paper
gives a per-pixel depth: placement is an illustration of the geometry, not tomography.

Rebuild: `./venv/bin/python scripts/build_nebula_volumes.py orion OUT.glb --hubble heic0601a.jpg
--wide noao-m42steinberg.jpg` (ESA "large" JPEG, NOIRLab "large" JPEG; hashes in models.json).
