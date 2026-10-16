# Tarantula Nebula: observed emission on illustrative shells

Image: https://www.eso.org/public/images/eso0650a/ (CC BY 4.0). Credit: ESO/R. Fosbury (ST-ECF).
MPG/ESO 2.2-metre WFI mosaic in B, V, H-alpha and [O III]; 62.40 x 62.31 arcmin. No ESO
endorsement is implied.

At the release's 170,000 ly (https://www.eso.org/public/news/eso0650/, "nearly 1,000 light-years
across") the crop is 1.15 x the listed 951 ly around R136 at image fraction (0.435, 0.245),
about 1,094 ly square, feathered to an ellipse. The photo becomes calibrated glowing sprites
(scripts/nebula_volume.py), so the front view reproduces it.

Depth is illustrative, not measured: gas is wrapped onto irregular, filled shells (radius ~320 ly,
+-30%) around R136, the generic geometry of HII regions blown by massive stars. Stars are given
random depths.

Rebuild: `./venv/bin/python scripts/build_nebula_volumes.py tarantula OUT.glb --image eso0650a.jpg`
(ESO "large" JPEG, 7872 x 7861 px; hash in models.json).
