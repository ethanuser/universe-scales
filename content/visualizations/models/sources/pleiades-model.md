# Pleiades in 3D from Gaia (pleiades-gaia-3d)

Members: Gaia Collaboration, Babusiaux et al. 2018, A&A 616, A10 (https://doi.org/10.1051/0004-6361/201832843),
Table A1a, Cluster = Pleiades, via VizieR J/A+A/616/A10 (RAdeg, DEdeg, Gmag, plx, e_plx; 1,331 stars).
Stars with e_plx >= 0.1 mas are dropped; each remaining star sits at distance 1/plx (median 136 pc,
444 ly), in a frame with the line of sight toward the camera, north up and east left. Stars more than
60 ly from the median center are dropped. The seven brightest (Alcyone, Atlas, Electra, Maia, Merope,
Taygeta, Pleione) are not in that table and have poor Gaia DR3 parallaxes (0.3-0.5 mas, none for
Alcyone), so they are placed at the median distance at their Gaia DR3 sky positions.
Color: interpolated from absolute G magnitude along the main sequence (valid for a single-age cluster),
brightness compressed. The blue reflection glow around the brightest stars is illustrative.
Gaia data: ESA/Gaia/DPAC, credited and cited. Rebuild: scripts/build_pleiades_model.py (query URL in
its docstring; catalog hash in models.json).
