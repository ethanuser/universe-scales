# Human Egg Cell — original explanatory diagram

## Basis and calibration

- [NICHD ovarian nomenclature workshop (2021)](https://www.nichd.nih.gov/research/atNICHD/Investigators/gomez-lobo/research/nomenclature-workshop-2021): human oocytes approximately 100–120 µm across.
- [Histology Guide, oocyte / fertilization TEM](https://www.histologyguide.org/EM-view/EM-326-oocyte/18-photo-1.html): oocyte, surrounding zona, polar bodies and completion of meiosis after fertilization. Its micrograph is explanatory reference only; no pixels or segmentation were copied.

The 120 µm calibration measures the oocyte proper, not zona or cumulus. This is a representative metaphase-II oocyte diagram: an indicated cortical spindle and a first polar body, without an interphase nucleus. The zona and oocyte front halves are cut for inspection. Zona thickness, perivitelline spacing, spindle, chromosomes and granules are authored proxies, not measurements. No naturally occurring colours are asserted.

## Reuse and build

Original geometric illustration by Universe Scales contributors, dedicated to CC0. Factual/anatomical references are linked above; none of their figures, text blocks or textures are redistributed. Internal colours, counts and all dimensions other than the calibrated outer dimension are authored teaching choices. This is registered as `authored_illustration`, with a visible '(diagram)' qualifier.

Offline rebuild: `./venv/bin/python scripts/build_bio3d2_cells.py --output /tmp/bio3d2/cells`. One unit is a micrometre; the entry's `reference_size` is 120. Keep native units and the explicit physical reference. Register the generated JSON and GLB with `scripts/register_model.py`.

Review limitations and integration: [bio3d2 report](../../../../handoff/bio3d2/REPORT.md). CPU previews verify geometry only; production WebGL, perspective and UI review remain pending.
