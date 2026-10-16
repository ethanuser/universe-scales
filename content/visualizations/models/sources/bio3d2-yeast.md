# Budding Yeast Cell — original explanatory diagram

## Basis and calibration

- [Open University, background information on yeast](https://www.open.edu/openlearncreate/mod/oucontent/view.php?id=160725&section=3.9): spherical-to-ellipsoidal yeast, approximately 5–10 by 4–8 µm. A mother cell's 5 µm X diameter is calibrated here.
- [Klis et al., cell size/morphology in S. cerevisiae (2018)](https://doi.org/10.1093/femsyr/foy052): dimensions depend on growth conditions.

A small early daughter bud is context; it extends the total span beyond the mother's calibrated diameter. This is an original teaching diagram, not a traced cell. Vacuole, nucleus and mitochondrial positions/proportions are illustrative. The opaque rear wall and open front are an explanatory viewing cut; wall thickness is a display proxy.

## Reuse and build

Original geometric illustration by Universe Scales contributors, dedicated to CC0. Factual/anatomical references are linked above; none of their figures, text blocks or textures are redistributed. Internal colours, counts and all dimensions other than the calibrated outer dimension are authored teaching choices. This is registered as `authored_illustration`, with a visible '(diagram)' qualifier.

Offline rebuild: `./venv/bin/python scripts/build_bio3d2_cells.py --output /tmp/bio3d2/cells`. One unit is a micrometre; the entry's `reference_size` is 5. Keep native units and the explicit physical reference. Register the generated JSON and GLB with `scripts/register_model.py`.

Review limitations and integration: [bio3d2 report](../../../../handoff/bio3d2/REPORT.md). CPU previews verify geometry only; production WebGL, perspective and UI review remain pending.
