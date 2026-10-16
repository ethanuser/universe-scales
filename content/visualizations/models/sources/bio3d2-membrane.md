# Cell Membrane — original explanatory diagram

## Basis and calibration

- [Doktorova and Weinstein, Transbilayer lipid asymmetry (2018), PMID 29689220](https://pubmed.ncbi.nlm.nih.gov/29689220/): the plasma membrane's lipid bilayer is approximately 4 nm thick.
- [Nagle and Tristram-Nagle, Lipid Bilayer Structure (2000)](https://pmc.ncbi.nlm.nih.gov/articles/PMC2722933/): thickness depends on the lipid system and the structural definition; the generic catalog value is not an exact universal boundary.

The outer surfaces of the two head-group layers are exactly 4 nm apart. Hydrophilic heads face outward, paired hydrocarbon tails face inward, with authored bends. The lateral window, head sizes, spacing and visible lipid count are schematic. This is neither an MD snapshot nor atomically accurate lipid chemistry. No proteins, sugars, sterols or water molecules are invented. Native units are nm; do not confuse them with the other cell diagrams' µm.

## Reuse and build

Original geometric illustration by Universe Scales contributors, dedicated to CC0. Factual/anatomical references are linked above; none of their figures, text blocks or textures are redistributed. Internal colours, counts and all dimensions other than the calibrated outer dimension are authored teaching choices. This is registered as `authored_illustration`, with a visible '(diagram)' qualifier.

Offline rebuild: `./venv/bin/python scripts/build_bio3d2_cells.py --output /tmp/bio3d2/cells`. One unit is a nanometre; the entry's `reference_size` is 4. Keep native units and the explicit physical reference. Register the generated JSON and GLB with `scripts/register_model.py`.

Review limitations and integration: [bio3d2 report](../../../../handoff/bio3d2/REPORT.md). CPU previews verify geometry only; production WebGL, perspective and UI review remain pending.
