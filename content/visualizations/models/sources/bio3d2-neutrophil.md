# Neutrophil — original explanatory diagram

## Basis and calibration

- [Histology Guide, human blood smear](https://www.histologyguide.org/slideview/MH-033hr-blood-smear/07-slide-1.html): 12–15 µm diameter in smear, a segmented nucleus and cytoplasmic granules.

The catalog's 12 µm is the calibrated diameter. The diagram uses a rounded boundary and three visibly connected nuclear lobes. It does not reconstruct the shape of a smeared or migrating cell. Lobes, connectors, granules and their counts/positions/colours are authored. The viewing cut removes the front envelope; exposed structures retain their illustrative positions.

## Reuse and build

Original geometric illustration by Universe Scales contributors, dedicated to CC0. Factual/anatomical references are linked above; none of their figures, text blocks or textures are redistributed. Internal colours, counts and all dimensions other than the calibrated outer dimension are authored teaching choices. This is registered as `authored_illustration`, with a visible '(diagram)' qualifier.

Offline rebuild: `./venv/bin/python scripts/build_bio3d2_cells.py --output /tmp/bio3d2/cells`. One unit is a micrometre; the entry's `reference_size` is 12. Keep native units and the explicit physical reference. Register the generated JSON and GLB with `scripts/register_model.py`.

Review limitations and integration: [bio3d2 report](../../../../handoff/bio3d2/REPORT.md). CPU previews verify geometry only; production WebGL, perspective and UI review remain pending.
