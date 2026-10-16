# Human Capillary — original explanatory diagram

## Basis and calibration

- [Histology Guide, continuous capillary TEM](https://www.histologyguide.org/EM-view/EM-213-capillary/09-photo-1.html): 5–10 µm vessels, continuous endothelial wall and basal lamina. Capillary cell nuclei are outside the shown micrograph section, so the diagram's nucleus is explicitly authored.

The 7 µm calibration is the outer vessel diameter. A short cylinder window exposes the hollow lumen. Both ends and the front opening are viewing cuts, not biological ends/holes. Wall/lamina thickness, segment length and endothelial nucleus are illustrative; no TEM was traced, and no borrowed image pixels are present. No smooth-muscle coat is added to a capillary.

## Reuse and build

Original geometric illustration by Universe Scales contributors, dedicated to CC0. Factual/anatomical references are linked above; none of their figures, text blocks or textures are redistributed. Internal colours, counts and all dimensions other than the calibrated outer dimension are authored teaching choices. This is registered as `authored_illustration`, with a visible '(diagram)' qualifier.

Offline rebuild: `./venv/bin/python scripts/build_bio3d2_cells.py --output /tmp/bio3d2/cells`. One unit is a micrometre; the entry's `reference_size` is 7. Keep native units and the explicit physical reference. Register the generated JSON and GLB with `scripts/register_model.py`.

Review limitations and integration: [bio3d2 report](../../../../handoff/bio3d2/REPORT.md). CPU previews verify geometry only; production WebGL, perspective and UI review remain pending.
