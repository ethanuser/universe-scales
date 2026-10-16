# Human Cone Cell — original explanatory diagram

## Basis and calibration

- [Cone cell, structure summary](https://en.wikipedia.org/wiki/Cone_cell): approximate 40–50 µm total length and narrow cell width; the current catalog's 45 µm is a representative convention, not a universal cone length.
- [OpenStax, The Retina](https://openstax.org/books/introduction-behavioral-neuroscience/pages/6-2-the-retina): outer segment, connecting cilium, mitochondria-rich inner segment, nucleus and synaptic terminal.
- [Mustafi et al., Structure of Cone Photoreceptors (2009)](https://doi.org/10.1016/j.preteyeres.2009.05.003): cone outer-segment folds remain connected to the membrane; this differs from isolated rod discs.

The complete diagram is 45 µm long, with no independent width enlargement. It uses a tapered outer segment, visible sampling of membrane folds and a joining rear membrane, plus a cilium and continuous inner cell body. Fold count/spacing, regional lengths and internal geometry are authored; they do not resolve individual native membrane layers or identify a retinal location/cone pigment. The slender result is intentional at true scale.

## Reuse and build

Original geometric illustration by Universe Scales contributors, dedicated to CC0. Factual/anatomical references are linked above; none of their figures, text blocks or textures are redistributed. Internal colours, counts and all dimensions other than the calibrated outer dimension are authored teaching choices. This is registered as `authored_illustration`, with a visible '(diagram)' qualifier.

Offline rebuild: `./venv/bin/python scripts/build_bio3d2_cells.py --output /tmp/bio3d2/cells`. One unit is a micrometre; the entry's `reference_size` is 45. Keep native units and the explicit physical reference. Register the generated JSON and GLB with `scripts/register_model.py`.

Review limitations and integration: [bio3d2 report](../../../../handoff/bio3d2/REPORT.md). CPU previews verify geometry only; production WebGL, perspective and UI review remain pending.
