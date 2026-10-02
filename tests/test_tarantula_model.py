import importlib.util
from pathlib import Path
import sys
import unittest

from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("build_tarantula_model", SCRIPTS / "build_tarantula_model.py")
tarantula = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tarantula)
from fetch_model_assets import inspect_glb, read_glb  # noqa: E402


class TarantulaModelTests(unittest.TestCase):
    def test_crop_uses_angular_field_without_stretching_full_photo(self):
        width, height = 1280, 1278
        left, top, right, bottom = tarantula.crop_box((width, height))
        span = (right - left) / width * tarantula.field_span_ly(62.40)
        self.assertAlmostEqual(span, tarantula.REFERENCE_LY, delta=3)
        self.assertLess(right - left, width / 3)
        self.assertGreater(top, 0)
        self.assertLess(bottom, height)
        self.assertGreater(tarantula.REFERENCE_LY, 950)
        self.assertLess(tarantula.REFERENCE_LY, 952)

    def test_model_is_bounded_compact_nonindexed_emission(self):
        image = Image.new("RGB", (1280, 1278), (160, 80, 110))
        data, count = tarantula.build(image)
        stats = inspect_glb(data)
        self.assertLess(stats["bytes"], 1_500_000)
        self.assertEqual(stats["triangle_count"], 0)
        self.assertEqual(stats["external_resources"], [])
        self.assertGreater(count, 30_000)
        self.assertLess(count, 60_000)
        document, _ = read_glb(data)
        primitive = document["meshes"][0]["primitives"][0]
        self.assertEqual(primitive["mode"], 0)
        self.assertNotIn("indices", primitive)
        positions = document["accessors"][0]
        self.assertLessEqual(positions["max"][0] - positions["min"][0], tarantula.REFERENCE_LY)
        self.assertLess(positions["max"][2] - positions["min"][2], tarantula.REFERENCE_LY * 0.14)
        self.assertIn("illustrative", document["nodes"][0]["name"])

    def test_empty_image_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "no visible emission"):
            tarantula.build(Image.new("RGB", (1280, 1278)))


if __name__ == "__main__":
    unittest.main()
