import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fetch_model_assets import read_glb, sha  # noqa: E402


class OrbitalDistanceModelTests(unittest.TestCase):
    def test_center_distance_and_body_radii(self):
        registry = json.loads((ROOT / "content/visualizations/models.json").read_text())
        models = {entry["id"]: entry for entry in registry["models"]}
        expected = {
            "nasa-earth-moon-distance": ("Earth-Moon Distance", 384_400_000,
                                          {"Earth": 6_371_000, "Moon": 1_737_500}),
            "nasa-sun-earth-au": ("Astronomical Unit", 149_597_870_700,
                                  {"Sun": 695_700_000, "Earth": 6_371_000}),
        }
        for model_id, (item, distance, radii) in expected.items():
            with self.subTest(model_id=model_id):
                entry = models[model_id]
                self.assertEqual(entry["matches"]["length"], [item])
                self.assertEqual(entry["presentation"]["reference_size"], 1)
                self.assertEqual(entry["processing"]["center_distance_m"], distance)
                data = (ROOT / entry["src"]).read_bytes()
                self.assertLess(len(data), 2_000_000)
                self.assertEqual(sha(data), entry["sha256"])
                document, _ = read_glb(data)
                nodes = {node["name"]: node for node in document["nodes"]}
                self.assertEqual(set(nodes), set(radii))
                self.assertEqual(sorted(node["translation"][0] for node in nodes.values()),
                                 [-0.5, 0.5])
                for name, radius in radii.items():
                    self.assertEqual(nodes[name]["scale"], [radius / distance] * 3)


if __name__ == "__main__":
    unittest.main()
