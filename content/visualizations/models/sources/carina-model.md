# Carina Nebula: whole-nebula optical image in 3D

Image: https://noirlab.edu/public/images/noao0136a/ (CC BY 4.0). Credit: CTIO/NOIRLab/NSF/AURA/
N. Smith (University of Minnesota). Curtis Schmidt telescope, Cerro Tololo; [O III] blue,
H-alpha green, [S II] red; 79.95 x 132.38 arcmin, north 1 degree left of vertical.

At NASA's ~7,500 ly (https://science.nasa.gov/missions/hubble/hubbles-sparkling-new-view-of-the-carina-nebula/)
the field is about 174 x 289 ly, essentially the whole ~300 ly nebula (the listed value).
The photo becomes calibrated glowing sprites (scripts/nebula_volume.py), so the front view
reproduces it.

Depth is illustrative: no 3D map of Carina exists. Gas is wrapped onto irregular, filled shells
(radius ~80 ly, +-30%) around the brightest region (Trumpler 16 / Eta Carinae), the generic shape
of nebulae blown by massive stars; a smooth random field keeps whole filaments together on the
near or far side. Stars are given random depths.

Rebuild: `./venv/bin/python scripts/build_nebula_volumes.py carina OUT.glb --image noao0136a.jpg`
(NOIRLab "large" JPEG, 2069 x 3426 px; hash in models.json). This replaces an earlier flat VISTA
infrared sheet (ESO eso1828b).
