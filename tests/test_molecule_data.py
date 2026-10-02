import json
import math
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_molecule_data import water


class MoleculeDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "content/visualizations/molecules.json").read_text())

    def test_water_is_upward_facing_with_nist_bond_geometry(self):
        stored = self.data["models"]["water"]
        self.assertEqual(stored, water())
        oxygen, left, right = stored["atoms"]
        self.assertEqual(oxygen["element"], "O")
        self.assertTrue(left["position"][1] > 0 and right["position"][1] > 0)
        self.assertAlmostEqual(math.dist(oxygen["position"], left["position"]), 0.958, places=6)
        self.assertAlmostEqual(math.dist(oxygen["position"], right["position"]), 0.958, places=6)
        a = left["position"]
        b = right["position"]
        angle = math.degrees(math.acos(sum(x * y for x, y in zip(a, b)) / (0.958 ** 2)))
        self.assertAlmostEqual(angle, 104.4776, places=4)

    def test_glucose_has_alpha_d_glucopyranose_composition_and_bonds(self):
        glucose = self.data["models"]["glucose"]
        atoms = glucose["atoms"]
        self.assertEqual(Counter(atom["element"] for atom in atoms), Counter(C=6, H=12, O=6))
        self.assertEqual(len(glucose["bonds"]), 24)
        for a, b in glucose["bonds"]:
            self.assertNotEqual(a, b)
            self.assertTrue(0.7 < math.dist(atoms[a]["position"], atoms[b]["position"]) < 1.7)


if __name__ == "__main__":
    unittest.main()
