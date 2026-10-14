import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from extract_glb_node import extract
from fetch_model_assets import pack_glb, read_glb


class ExtractNodeTests(unittest.TestCase):
    def test_keeps_subtree_and_ancestor_transforms(self):
        document = {"asset": {"version": "2.0"}, "scenes": [{"nodes": [0, 4]}],
                    "nodes": [{"translation": [1, 2, 3], "children": [1, 3]},
                              {"name": "shaft", "children": [2]}, {"mesh": 0},
                              {"mesh": 1}, {"mesh": 2}], "meshes": []}
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "in.glb", Path(directory) / "out.glb"
            source.write_bytes(pack_glb(document, b""))
            extract(source, output, "shaft")
            result, _ = read_glb(output.read_bytes())
            self.assertEqual(result["scenes"], [{"nodes": [0]}])
            self.assertEqual(result["nodes"][0]["children"], [1])
            self.assertEqual(result["nodes"][0]["translation"], [1, 2, 3])
            self.assertEqual(result["nodes"][1]["children"], [2])
            with self.assertRaises(ValueError):
                extract(source, output, "missing")
            document["animations"] = [{"name": "rig"}]
            source.write_bytes(pack_glb(document, b""))
            with self.assertRaises(ValueError):
                extract(source, output, "shaft")


if __name__ == "__main__":
    unittest.main()
