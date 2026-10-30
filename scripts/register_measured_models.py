#!/usr/bin/env python3
"""Build and register the measurement-based Length models (scripts/build_measured_models.py).

    ./venv/bin/python scripts/register_measured_models.py [name ...]

Writes each GLB to content/visualizations/models/, its provenance note to
content/visualizations/models/sources/<id>.md and its registry entry (via register_model.py).
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_measured_models as builder  # noqa: E402

CC0 = {"author": "Universe Scales", "license": "CC0-1.0",
       "license_url": "https://creativecommons.org/publicdomain/zero/1.0/"}

MODELS = {
    "great-pyramid": dict(item="Great Pyramid of Giza", representation="measured_reconstruction",
        source="https://www.ronaldbirdsall.com/gizeh/petrie/c7.html",
        basis_label="Petrie (1883), The Pyramids and Temples of Gizeh, ch. 7",
        presentation={"layout_width_factor": 2.2, "yaw": 30, "color_gain": 0.85},
        note="The Great Pyramid as built, from survey measurements: a square base 230.33 m on a side "
             "(Petrie's mean of the four casing-base sides) and an original height of 146.6 m, giving the "
             "measured face slope of about 51.8 degrees. Faces show the smooth Tura-limestone casing that "
             "has since been stripped; the capstone, the slight concavity of the faces (under 1 m) and the "
             "present-day stepped core are not modeled.",
        sources=["W. M. Flinders Petrie (1883), The Pyramids and Temples of Gizeh, chapter 7: casing base sides 230.25-230.45 m (mean 230.33 m), slope 51 deg 52 min.",
                 "M. Lehner and Z. Hawass (2017), Giza and the Pyramids: original height 146.6 m (280 royal cubits)."]),
    "inner-core": dict(item="Earth's Inner Core", representation="measured_reconstruction",
        source="https://doi.org/10.1016/0031-9201(81)90046-7",
        basis_label="PREM: Dziewonski & Anderson (1981)",
        presentation={"yaw": -45, "pitch": 12},
        note="Earth's solid inner core at the radius of the Preliminary Reference Earth Model, 1,221.5 km "
             "(2,443 km across), cut open by a quarter to show the innermost inner core, a central region about "
             "650 km in radius where seismic waves travel with a different directional dependence. Colors are "
             "illustrative of an iron-nickel solid near 5,000-6,000 K; the innermost-core boundary is a "
             "seismological estimate, not a sharp surface.",
        sources=["A. M. Dziewonski and D. L. Anderson (1981), Preliminary Reference Earth Model, Phys. Earth Planet. Inter. 25, 297: inner-core radius 1221.5 km.",
                 "J. Stephenson, H. Tkalcic and M. Sambridge (2021), Evidence for the innermost inner core, JGR Solid Earth 126, e2020JB020545: radius about 650 km."]),
    "kola-borehole": dict(item="Kola Superdeep Borehole", representation="measured_reconstruction",
        source="https://en.wikipedia.org/wiki/Kola_Superdeep_Borehole",
        basis_label="Kozlovsky (ed., 1984), The Superdeep Well of the Kola Peninsula",
        presentation={"layout_width_factor": 0.4, "yaw": 25},
        note="A slice of the rock column drilled by borehole SG-3, to its final depth of 12,262 m (1989). "
             "The upper 6,842 m are Proterozoic volcanic and sedimentary rocks of the Pechenga complex; below "
             "lie Archean gneisses, granites and amphibolites. The bottom-hole temperature was about 180 C. "
             "The hole itself is about 0.2 m wide and is drawn 40 m wide to be visible; the slab's width is "
             "arbitrary context.",
        sources=["Ye. A. Kozlovsky (ed., 1984/1987), The Superdeep Well of the Kola Peninsula, Springer: Proterozoic/Archean contact at 6,842 m.",
                 "Final depth 12,262 m (1989) and ~180 C bottom-hole temperature: summarized by the Kola SG-3 project reports and Wikipedia's cited sources."]),
    "dvd-tracks": dict(item="DVD Track Pitch", representation="specification_diagram",
        source="https://ecma-international.org/publications-and-standards/standards/ecma-267/",
        basis_label="ECMA-267 (DVD read-only disk)",
        presentation={"display_extent_factor": 4.6, "layout_width_factor": 4.4, "pitch": 62, "yaw": -20},
        note="Three tracks of a DVD data layer seen from above, at the standard 0.74 um track pitch. Pit and "
             "land lengths are whole multiples of the 0.133 um channel bit within the EFMPlus run-length "
             "limits (3T-11T and 14T), so the shortest pit is 0.40 um; the sequence is a deterministic "
             "random example, not real data. Pit width (~0.32 um) and depth (~105 nm, a quarter wavelength of "
             "650 nm light in polycarbonate) are typical values; pits are drawn as boxes.",
        sources=["ECMA-267 (2001), 120 mm DVD Read-Only Disk: track pitch 0.74 um, channel bit length 0.133 um (4.7 GB), run lengths 3T-11T and 14T."]),
    "bluray-tracks": dict(item="Blu-ray Track Pitch", representation="specification_diagram",
        source="https://en.wikipedia.org/wiki/Blu-ray",
        basis_label="Blu-ray Disc Association BD-ROM white paper",
        presentation={"display_extent_factor": 4.7, "layout_width_factor": 4.4, "pitch": 62, "yaw": -20},
        note="Three tracks of a Blu-ray data layer seen from above, at the standard 0.32 um track pitch. Pit "
             "and land lengths are whole multiples of the 74.5 nm channel bit (25 GB layer) within the 1-7PP "
             "run-length limits (2T-8T), so the shortest pit is 0.149 um; the sequence is a deterministic "
             "random example, not real data. Pit width (~0.14 um) and depth (~65 nm) are typical values; pits "
             "are drawn as boxes.",
        sources=["Blu-ray Disc Association, BD-ROM format white paper: track pitch 0.32 um, channel bit length 74.5 nm (25 GB), 1-7PP modulation (run lengths 2T-8T)."]),
    "ton618-horizon": dict(item="TON 618 Event Horizon", representation="derived_quantity",
        source="https://en.wikipedia.org/wiki/TON_618",
        basis_label="Ge et al. (2019): TON 618 mass 4.07e10 solar masses",
        presentation={},
        note="The event horizon of the quasar TON 618's black hole for a mass of 4.07e10 suns: a Schwarzschild "
             "radius r = 2GM/c^2 of 1.2e14 m, so 2.4e14 m (1,600 au) across. Drawn to the same scale in front of "
             "it are Neptune's orbit (30 au) and the heliopause where Voyager 1 crossed it (121.6 au). The "
             "horizon is not a surface one could see; the mass estimate is uncertain by a factor of a few.",
        sources=["X. Ge et al. (2019), AJ 157, 148: virial mass of TON 618, 4.07e10 solar masses.",
                 "Neptune's mean orbital radius 30.07 au (NASA); Voyager 1 crossed the heliopause at 121.6 au (Stone et al. 2013, Science 341, 150)."]),
}


def main(names):
    for name in names or MODELS:
        meta = MODELS[name]
        model_id = f"measured-{name}"
        with tempfile.TemporaryDirectory() as tmp:
            glb = Path(tmp) / f"{model_id}.glb"
            _, info = builder.BUILDERS[name](glb)
            notes = ROOT / "content/visualizations/models/sources" / f"{model_id}.md"
            notes.write_text(f"# {meta['item']} ({model_id})\n\n{meta['note']}\n\n## Sources\n\n" +
                             "".join(f"- {line}\n" for line in meta["sources"]) +
                             f"\nBuilt by `scripts/build_measured_models.py {name}` (CC0). Geometry is set by the "
                             "numbers above; nothing is scaled by eye.\n")
            presentation = {"reference_size": info["reference_size"], "measure_axis": info["measure_axis"],
                            **meta["presentation"]}
            entry = {"id": model_id, **CC0, "source": meta["source"], "basis_url": meta["source"],
                     "basis_label": meta["basis_label"], "link_label": "Model basis",
                     "license_files": ["licenses/CC0-1.0.txt", f"sources/{model_id}.md"],
                     "matches": {"length": [meta["item"]]}, "geometry": "mesh",
                     "representation": meta["representation"], "presentation": presentation,
                     "note": meta["note"], "processing": {"script": "scripts/build_measured_models.py", "model": name}}
            entry_path = Path(tmp) / "entry.json"
            entry_path.write_text(json.dumps(entry))
            out = subprocess.run([sys.executable, str(ROOT / "scripts/register_model.py"), str(entry_path), str(glb)],
                                 cwd=ROOT, capture_output=True, text=True)
            print((out.stdout or out.stderr).strip().splitlines()[-1])


if __name__ == "__main__":
    main(sys.argv[1:])
