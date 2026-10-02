from io import BytesIO
from pathlib import Path
import sys
import unittest

from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_laniakea_model as laniakea
from fetch_model_assets import inspect_glb, read_glb, view_bytes


def jpeg_bytes(size=(64, 64), color=(210, 40, 30)):
    image = Image.new("RGB", size, color)
    output = BytesIO()
    image.save(output, format="JPEG")
    return output.getvalue()


class LaniakeaModelTests(unittest.TestCase):
    def setUp(self):
        self.source = jpeg_bytes()
        self.model = laniakea.build_model(self.source)

    def test_panel_is_a_single_flat_quad_with_embedded_authored_figure(self):
        document, binary = read_glb(self.model)
        stats = inspect_glb(self.model)
        self.assertEqual(stats["triangle_count"], 2)
        self.assertEqual(stats["external_resources"], [])
        self.assertEqual(len(document["meshes"]), 1)
        self.assertEqual(document["meshes"][0]["primitives"][0]["mode"], 4)
        self.assertEqual(len(document["images"]), 1)
        self.assertEqual(document["images"][0]["mimeType"], "image/jpeg")
        image = Image.open(BytesIO(view_bytes(
            document, binary, document["images"][0]["bufferView"])))
        self.assertEqual(image.size, (64, 64))
        self.assertLess(len(self.model), 1_500_000)

    def test_source_must_be_square_jpeg(self):
        with self.assertRaisesRegex(ValueError, "square JPEG"):
            laniakea.build_model(jpeg_bytes(size=(64, 32)))
        png = BytesIO()
        Image.new("RGB", (64, 64)).save(png, format="PNG")
        with self.assertRaisesRegex(ValueError, "square JPEG"):
            laniakea.build_model(png.getvalue())

    def test_texture_downsampling_preserves_the_full_frame_and_caps_at_1024(self):
        source = jpeg_bytes(size=(3000, 3000))
        texture, original_size, target_size = laniakea.panel_texture(source)
        self.assertEqual(original_size, (3000, 3000))
        self.assertEqual(target_size, (1024, 1024))
        with Image.open(BytesIO(texture)) as image:
            self.assertEqual(image.size, target_size)
            self.assertEqual(image.format, "JPEG")

    def test_metadata_marks_panel_as_reference_only_not_registry_coverage(self):
        metadata = laniakea.build_metadata(
            self.model, "staged.jpg", (64, 64), (64, 64), "source-digest")
        self.assertEqual(metadata["representation"], "reference_panel")
        self.assertFalse(metadata["production_registry_eligible"])
        self.assertNotIn("matches", metadata)
        self.assertNotIn("src", metadata)
        self.assertEqual(metadata["license_url"], laniakea.FIGURE_LICENSE)
        self.assertIn("Dupuy", metadata["author"])
        self.assertIn("Courtois", metadata["author"])
        self.assertIn("not a calibrated Length model", metadata["intended_use"])
        self.assertIn("must not be used as Length-model coverage", metadata["note"])
        self.assertIn("grouped CF4", metadata["note"])
        self.assertEqual(metadata["processing"]["source_image_dimensions_px"], [64, 64])
        self.assertEqual(metadata["processing"]["texture_dimensions_px"], [64, 64])
        self.assertEqual(metadata["processing"]["source_figure_sha256"], "source-digest")
        self.assertIn("no crop", metadata["processing"]["image_operations"][1])
        self.assertIn("Unitless display card", metadata["processing"]["model_plane_dimensions"])
        self.assertAlmostEqual(metadata["processing"]["published_diameter_context_m"], 4.937084130386187e24)


if __name__ == "__main__":
    unittest.main()
