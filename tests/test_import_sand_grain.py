import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fetch_model_assets import inspect_glb  # noqa: E402
from import_sand_grain import make_glb, smooth_mesh  # noqa: E402


class SandGrainTest(unittest.TestCase):
    def test_subdivision_keeps_a_closed_surface_and_quadruples_faces(self):
        top = (0, 0, 1)
        bottom = (0, 0, -1)
        ring = [(1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0)]
        faces = [(top, ring[i], ring[(i + 1) % 4]) for i in range(4)]
        faces += [(bottom, ring[(i + 1) % 4], ring[i]) for i in range(4)]
        vertices, refined = smooth_mesh(faces)
        self.assertEqual(len(vertices), 18)
        self.assertEqual(len(refined), 32)
        self.assertEqual(inspect_glb(make_glb(faces))["triangle_count"], 32)

    def test_manifest_matches_the_generated_asset(self):
        models = json.loads((ROOT / "content/visualizations/models.json").read_text())["models"]
        entry = next(model for model in models if model["id"] == "sand-atlas-caicos-ooid-80")
        actual = inspect_glb((ROOT / entry["src"]).read_bytes())
        for key in ("bytes", "sha256", "triangle_count"):
            self.assertEqual(entry[key], actual[key])


if __name__ == "__main__":
    unittest.main()
