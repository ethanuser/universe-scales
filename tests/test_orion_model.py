import importlib.util
from pathlib import Path
import sys
import unittest

from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("build_orion_model", SCRIPTS / "build_orion_model.py")
orion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orion)
from fetch_model_assets import inspect_glb, read_glb  # noqa: E402


class OrionModelTests(unittest.TestCase):
    def test_observed_field_remains_smaller_than_whole_region(self):
        image = Image.new("RGB", (64, 64), (130, 65, 90))
        data, point_count = orion.build(image)
        stats = inspect_glb(data)
        self.assertLess(stats["bytes"], 1_500_000)
        self.assertEqual(stats["triangle_count"], 0)
        self.assertEqual(stats["external_resources"], [])
        document, _ = read_glb(data)
        self.assertGreater(point_count, 1000)
        cloud = document["meshes"][0]["primitives"][0]
        self.assertNotIn("indices", cloud, "valid nonindexed points should be packable")
        extent = document["accessors"][cloud["attributes"]["POSITION"]]
        self.assertLessEqual(extent["max"][0] - extent["min"][0], 13)
        self.assertGreater(orion.REGION_SPAN_LY, 25)
        self.assertLess(orion.REGION_SPAN_LY, 26)
        self.assertEqual(document["nodes"][0]["extras"]["pointSize"]["max"], 4.5)
        bracket = document["meshes"][1]["primitives"][0]
        self.assertEqual(bracket["mode"], 3)
        position = document["accessors"][bracket["attributes"]["POSITION"]]
        self.assertAlmostEqual(position["max"][0] - position["min"][0], orion.REGION_SPAN_LY)
        self.assertLess(position["max"][1], extent["min"][1], "span bracket must sit below the gas")
        cue = next(node for node in document["nodes"] if node["name"] == "Inferred depth annotation")
        self.assertEqual(cue["extras"]["labelAxis"]["axis"], "z")
        self.assertAlmostEqual(cue["extras"]["labelAxis"]["length"], 0.65)

    def test_reference_depth_places_central_front_behind_stars(self):
        self.assertAlmostEqual(orion.blister_depth(0.445, 0.456), -0.65)
        self.assertLess(orion.blister_depth(0.445, 0.456), orion.blister_depth(0, 0))
        self.assertEqual(orion.linear_color(0), 0)
        self.assertEqual(orion.linear_color(255), 1)


if __name__ == "__main__":
    unittest.main()
