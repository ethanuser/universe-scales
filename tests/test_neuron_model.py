import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("build_neuron_model", SCRIPTS / "build_neuron_model.py")
neuron = importlib.util.module_from_spec(spec)
spec.loader.exec_module(neuron)
from fetch_model_assets import inspect_glb, read_glb  # noqa: E402


class NeuronModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.swc = Path(self.temp.name) / "sample.swc"
        self.swc.write_text(
            "# id,type,x,y,z,radius,parent\n"
            "1 1 10 20 30 2 -1\n"
            "2 4 10 24 30 0.8 1\n"
            "3 4 10 80 30 0.2 2\n"
            "4 3 -5 20 30 0.7 1\n"
            "5 3 -70 20 30 0.1 4\n"
        )
        self.markers = Path(self.temp.name) / "sample-markers.csv"
        self.markers.write_text(
            "##x,y,z,radius,shape,name,comment,color_r,color_g,color_b\n"
            "15,20,30,0,1,10,,58,225,103\n"
            "80,20,30,0,1,20,,58,225,103\n"
        )

    def test_swc_parser_checks_tree_and_clip_intersections(self):
        nodes, soma = neuron.read_swc(self.swc)
        self.assertEqual(len(nodes), 5)
        self.assertEqual(soma["id"], 1)
        self.assertEqual(neuron.clip_segment((0, 0, 0), (80, 0, 0)), (0.0, 0.625))
        self.assertIsNone(neuron.clip_segment((55, 0, 0), (60, 0, 0)))

    def test_glb_keeps_real_radii_types_and_explicit_crop(self):
        data, stats = neuron.build(self.swc, self.markers)
        audit = inspect_glb(data)
        document, _ = read_glb(data)
        self.assertLess(audit["bytes"], 1_500_000)
        self.assertEqual(audit["external_resources"], [])
        self.assertGreater(audit["triangle_count"], 0)
        self.assertEqual(document["extras"]["crop"], {"center": "soma", "halfExtentUm": 50.0})
        self.assertEqual(document["extras"]["retainedSwcSegments"], 4)
        self.assertEqual(document["extras"]["cropIntersectedSegments"], 2)
        self.assertEqual(stats["included_markers"], 1)
        names = {mesh["name"] for mesh in document["meshes"]}
        self.assertIn("Soma (Allen SWC radius)", names)
        self.assertIn("Apical dendrites (Allen SWC)", names)
        self.assertIn("Basal dendrites (Allen SWC)", names)
        self.assertIn("Allen reconstruction markers", names)
        entry = neuron.build_entry(data, stats, self.swc, self.markers)
        self.assertEqual(entry["presentation"]["reference_size"], 100)
        self.assertIn("not CC-BY/CC0", entry["license"])
        self.assertIn("not a complete neuron", entry["note"])

    def test_rejects_missing_parent_and_non_soma_root(self):
        self.swc.write_text("1 3 0 0 0 1 -1\n")
        with self.assertRaisesRegex(ValueError, "soma root"):
            neuron.read_swc(self.swc)
        self.swc.write_text("1 1 0 0 0 1 -1\n2 3 1 0 0 1 9\n")
        with self.assertRaisesRegex(ValueError, "missing parent"):
            neuron.read_swc(self.swc)


if __name__ == "__main__":
    unittest.main()
