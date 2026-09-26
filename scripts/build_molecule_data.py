#!/usr/bin/env python3
"""Build small, traceable atom-and-bond data for the Length explorer."""

import argparse
import json
import math
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "content/visualizations/molecules.json"
GLUCOSE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/79025/record/JSON?record_type=3d"
WATER_URL = "https://cccbdb.nist.gov/expgeom2x.asp?casno=7732185"
ELEMENTS = {1: "H", 6: "C", 8: "O"}


def water():
    bond_length = 0.958
    bond_angle = 104.4776
    half_angle = math.radians(bond_angle / 2)
    dx = bond_length * math.sin(half_angle)
    dy = bond_length * math.cos(half_angle)
    return {
        "name": "Gas-phase H2O",
        "source": WATER_URL,
        "atoms": [
            {"element": "O", "position": [0, 0, 0]},
            {"element": "H", "position": [-dx, dy, 0]},
            {"element": "H", "position": [dx, dy, 0]},
        ],
        "bonds": [[0, 1], [0, 2]],
        "bond_length_angstrom": bond_length,
        "bond_angle_degrees": bond_angle,
    }


def glucose(record):
    compound = record["PC_Compounds"][0]
    if compound["id"]["id"]["cid"] != 79025:
        raise ValueError("Expected PubChem CID 79025 (alpha-D-glucose)")
    atom_ids = compound["atoms"]["aid"]
    elements = compound["atoms"]["element"]
    conformer = compound["coords"][0]["conformers"][0]
    coordinate_ids = compound["coords"][0]["aid"]
    coordinates = {
        aid: [conformer[axis][index] for axis in "xyz"]
        for index, aid in enumerate(coordinate_ids)
    }
    atoms = [
        {"element": ELEMENTS[element], "position": coordinates[aid]}
        for aid, element in zip(atom_ids, elements, strict=True)
    ]
    if sorted(atom["element"] for atom in atoms) != sorted("C" * 6 + "H" * 12 + "O" * 6):
        raise ValueError("PubChem record does not have the expected C6H12O6 composition")
    index_by_id = {aid: index for index, aid in enumerate(atom_ids)}
    bonds = [
        [index_by_id[a], index_by_id[b]]
        for a, b in zip(compound["bonds"]["aid1"], compound["bonds"]["aid2"], strict=True)
    ]
    if len(bonds) != 24 or any(
        not 0.7 < math.dist(atoms[a]["position"], atoms[b]["position"]) < 1.7
        for a, b in bonds
    ):
        raise ValueError("Glucose conformer has an unexpected bond graph or bond length")
    return {"name": "Alpha-D-glucopyranose (PubChem 3D conformer)",
            "source": "https://pubchem.ncbi.nlm.nih.gov/compound/79025",
            "atoms": atoms, "bonds": bonds}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pubchem-record", type=Path,
                        help="Use a previously downloaded official PubChem JSON record")
    args = parser.parse_args()
    if args.pubchem_record:
        record = json.loads(args.pubchem_record.read_text())
    else:
        with urlopen(GLUCOSE_URL, timeout=30) as response:
            record = json.load(response)
    result = {"schema_version": 1, "coordinate_unit": "angstrom",
              "models": {"water": water(), "glucose": glucose(record)}}
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
