# Pillars of Creation: STScI 3D shape wearing Hubble's image

- Shape: STScI's "All Four Pillars (Positioning Reference)" model (Leah Hustak, Ralf Crawford;
  NASA, ESA, CSA, STScI), https://science.nasa.gov/asset/webb/pillars-of-creation-model-for-3d-printing/
- Image: NASA, ESA and the Hubble Heritage Team (STScI/AURA), 2015 visible-light image,
  https://svs.gsfc.nasa.gov/30774 ("The towering pillars are about 5 light-years tall"; 6,500 ly away).
- Used with credit under NASA media guidelines; not relicensed as CC0.

The mesh's silhouette, viewed along its +x axis, was fitted to the photo (IoU 0.52) and the
photo projected onto it, so the resting view is Hubble's. Turning it shows four separate
clouds spread about 6 ly along the line of sight. Surfaces Hubble cannot see are shaded dust.
Rim glow, gas and stars are sampled from the same photo; their depths are illustrative.
Build: `./venv/bin/python scripts/build_pillars_model.py STSCI_MESH.glb HUBBLE.jpg OUT.glb`
(STSCI_MESH.glb is the former nasa-pillars-of-creation.glb, git history before this commit).
