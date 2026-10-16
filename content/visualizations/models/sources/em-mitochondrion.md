# Mitochondrion from FIB-SEM (OpenOrganelle jrc_jurkat-1)

Data: Janelia OpenOrganelle / CellMap (COSEM), dataset jrc_jurkat-1 (a human Jurkat T cell,
FIB-SEM at 4 x 4 x 3.44 nm voxels), public bucket s3://janelia-cosem-datasets, CC BY 4.0.
Cite: Heinrich, L. et al. Nature 599, 141-146 (2021), https://doi.org/10.1038/s41586-021-03977-3;
Xu, C. S. et al. Nature 599, 147-151 (2021), https://doi.org/10.1038/s41586-021-03992-4.

Object 265 of `labels/mito_seg/s0` (instance segmentation) gives the outline: marching cubes on
an 8 nm grid, smoothed, decimated to 14k triangles, drawn translucent. Cristae are ridges of the
COSEM network's membrane prediction (`labels/mito-mem_pred/s0`) deeper than 45 nm inside the
outline (so the outer/inner boundary membranes are left to the shell), marching cubes at 4 nm,
Taubin-smoothed, decimated to 90k triangles. They are a machine-learning prediction from EM:
cristae the network did not detect are absent, so the folding is a lower bound.

Measured: 4.28 x 1.40 x 1.13 um; volume 1.96 um^3; outer surface 12.8 um^2. The Length item uses
this organelle's 4.3 um length. Rebuild: `./venv/bin/python scripts/build_em_mitochondrion.py
--output-dir OUT` (downloads ~5 GB of chunks; crop hashes in models.json).
