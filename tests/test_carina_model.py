import importlib.util
from pathlib import Path
import sys
import unittest

from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("build_carina_model", SCRIPTS / "build_carina_model.py")
carina = importlib.util.module_from_spec(spec)
spec.loader.exec_module(carina)
from fetch_model_assets import inspect_glb, read_glb  # noqa: E402


class CarinaModelTests(unittest.TestCase):
    def test_photographed_field_is_not_stretched_to_whole_nebula(self):
        span_x, span_y = [carina.field_span_ly(angle) for angle in carina.FIELD_ARCMIN]
        self.assertAlmostEqual(span_x, 193.065, delta=0.02)
        self.assertAlmostEqual(span_y, 156.603, delta=0.02)
        self.assertLess(span_x, carina.REGION_SPAN_LY * 0.65)
        positions, _, _, _ = carina.surface_geometry()
        self.assertLessEqual(max(p[0] for p in positions) - min(p[0] for p in positions), span_x)
        self.assertLessEqual(max(p[1] for p in positions) - min(p[1] for p in positions), span_y)

    def test_compact_surface_and_correct_context_span(self):
        data, count = carina.build(Image.new("RGB", (1280, 1038), (160, 80, 110)))
        stats = inspect_glb(data)
        self.assertLess(stats["bytes"], 1_500_000)
        self.assertLess(stats["triangle_count"], 15_000)
        self.assertGreater(stats["triangle_count"], 8000)
        self.assertEqual(stats["external_resources"], [])
        self.assertEqual(count, stats["triangle_count"])
        document, _ = read_glb(data)
        self.assertEqual(document["meshes"][0]["primitives"][0]["mode"], 4)
        self.assertEqual(len(document["images"]), 1)
        self.assertEqual(document["images"][0]["mimeType"], "image/jpeg")
        bracket = document["accessors"][4]
        self.assertEqual(bracket["max"][0] - bracket["min"][0], 300)
        self.assertLess(document["accessors"][0]["max"][2] - document["accessors"][0]["min"][2], 20)

    def test_empty_image_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "no visible sky"):
            carina.build(Image.new("RGB", (1280, 1038)))


if __name__ == "__main__":
    unittest.main()
