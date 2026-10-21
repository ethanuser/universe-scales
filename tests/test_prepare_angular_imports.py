import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_angular_imports as imports
from fetch_model_assets import pack_glb, read_glb


class AngularImportTests(unittest.TestCase):
    def convert(self, kind, names, pivot_name):
        nodes = [{"name": name, "translation": [i * .01, .15, .032],
                  "rotation": [0, 0, .5, .8660254037844386], "mesh": i}
                 for i, name in enumerate(names)]
        root = len(nodes)
        nodes.append({"name": "Source assembly", "children": list(range(root))})
        source = {"asset": {"version": "2.0"}, "nodes": nodes,
                  "meshes": [{"primitives": []} for _ in names],
                  "scenes": [{"nodes": [root]}]}
        source_data = pack_glb(source, b"original mesh and texture bytes")
        pivot = next(n["translation"] for n in nodes if n["name"] == pivot_name)
        with tempfile.TemporaryDirectory() as directory:
            path, output = Path(directory) / "source.glb", Path(directory) / "out.glb"
            path.write_bytes(source_data)
            with patch.dict(imports.SOURCES, {kind: hashlib.sha256(source_data).hexdigest()}):
                imports.prepare(path, output, kind)
            result, binary = read_glb(output.read_bytes())
            self.assertEqual(binary, read_glb(source_data)[1], "mesh/texture payload must not change")
            self.assertEqual(result["meshes"], source["meshes"])
            for group in result["nodes"][root]["children"]:
                parent = result["nodes"][group]
                for index in parent["children"]:
                    child = result["nodes"][index]
                    world = [a+b for a,b in zip(parent.get("translation", [0,0,0]), child["translation"])]
                    for actual, expected in zip(world, source["nodes"][index]["translation"]):
                        self.assertAlmostEqual(actual, expected)
                    self.assertEqual(child["rotation"], source["nodes"][index]["rotation"])
            with self.assertRaises(ValueError):
                imports.prepare(path, output, kind)
        return result, pivot

    def test_clock_hands_keep_authored_pose_and_share_the_hub_axis(self):
        result, pivot = self.convert("clock", ["Hour hand", "Minute hand", "Clock hand hub", "Dial"], "Clock hand hub")
        for name in ["HourHandRotor", "MinuteHandRotor"]:
            rotor = next(node for node in result["nodes"] if node["name"] == name)
            self.assertEqual(rotor["translation"], pivot)
            self.assertEqual(len(rotor["children"]), 1)

    def test_record_parts_share_the_spindle_while_the_arm_stays_fixed(self):
        names = ["Record centre label", "Vinyl record", "Rubber platter mat", "Spindle", "Tonearm"]
        names += ["Record groove" if not i else f"Record groove.{i:03}" for i in range(7)]
        result, pivot = self.convert("walnut-spin", names, "Spindle")
        rotor = next(node for node in result["nodes"] if node["name"] == "RecordRotor")
        self.assertEqual(rotor["translation"], pivot)
        self.assertEqual(len(rotor["children"]), 10)
        housing = next(node for node in result["nodes"] if node["name"] == "Housing")
        self.assertEqual({result["nodes"][i]["name"] for i in housing["children"]}, {"Spindle", "Tonearm"})


if __name__ == "__main__":
    unittest.main()
