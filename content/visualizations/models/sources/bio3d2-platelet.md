# Human Platelet — original explanatory diagram

## Basis and calibration

- [Histology Guide, human blood smear](https://www.histologyguide.org/slideview/MH-033hr-blood-smear/07-slide-1.html): resting anucleate discs, 2–4 µm across. The catalog's 2.5 µm is representative.
- [Cuenca-Zamora et al., Tubulin in Platelets (2019)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6678703/): peripheral microtubule marginal band supports discoid shape.

The model is a cutaway of the resting disc, rather than a spiky activated platelet. The band is one display tube representing a bundle. Granule shapes/counts, positions and cut depth are authored. There is no nucleus; no individual molecular anatomy is claimed.

## Reuse and build

Original geometric illustration by Universe Scales contributors, dedicated to CC0. Factual/anatomical references are linked above; none of their figures, text blocks or textures are redistributed. Internal colours, counts and all dimensions other than the calibrated outer dimension are authored teaching choices. This is registered as `authored_illustration`, with a visible '(diagram)' qualifier.

Offline rebuild: `./venv/bin/python scripts/build_bio3d2_cells.py --output /tmp/bio3d2/cells`. One unit is a micrometre; the entry's `reference_size` is 2.5. Keep native units and the explicit physical reference. Register the generated JSON and GLB with `scripts/register_model.py`.

Review limitations and integration: [bio3d2 report](../../../../handoff/bio3d2/REPORT.md). CPU previews verify geometry only; production WebGL, perspective and UI review remain pending.
