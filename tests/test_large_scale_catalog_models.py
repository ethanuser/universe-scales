import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_large_scale_catalog_models as models
from fetch_model_assets import inspect_glb, read_glb


class LargeScaleCatalogModelTests(unittest.TestCase):
    def test_comoving_distance_inverts_the_published_window(self):
        for distance in (215.0, 310.0, 370.0):
            z = models.redshift_for_distance_mpc(distance)
            self.assertAlmostEqual(models.hubble_distance_mpc(z), distance, places=6)

    def test_queries_encode_the_documented_regional_windows(self):
        sloan = models.query_for(models.CONFIG["sloan"])
        self.assertIn("sciencePrimary=1", sloan)
        self.assertIn("then z_noqso else z end as z", sloan)
        self.assertIn("then class_noqso else class end as class", sloan)
        self.assertIn("then zwarning_noqso else zwarning end as zwarning", sloan)
        self.assertIn("ra between 130.500000 and 210.000000", sloan)
        self.assertIn("dec between -2.000000 and 2.000000", sloan)
        self.assertIn("end) between 0.051461", sloan)
        virgo = models.query_for(models.CONFIG["virgo"])
        self.assertIn("end) between 0.000000000 and 0.008000000", virgo)
        self.assertIn("ra between 175.000000 and 200.000000", virgo)

    def test_equatorial_cartesian_conversion_preserves_radial_separations(self):
        a = models.sky_xyz(10, 0, 100)
        b = models.sky_xyz(10, 0, 110)
        self.assertAlmostEqual(float(np.linalg.norm(b - a)), 10.0, places=6)
        self.assertAlmostEqual(float(np.linalg.norm(models.sky_xyz(0, 0, 10))), 10.0)

    def test_catalog_reader_deduplicates_and_rejects_invalid_rows(self):
        payload = "#Table1\nra,dec,z,specObjID\n10,20,0.01,1\n10,20,0.01,1\n11,21,-0.1,2\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.csv"
            path.write_text(payload)
            rows = models.read_catalog(path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["specObjID"], "1")

    def test_model_is_embedded_and_does_not_rescale_catalog_positions_to_item_value(self):
        config = dict(models.CONFIG["virgo"])
        points = [
            {"specObjID": "1", "ra": 184.0, "dec": 8.0, "z": 0.003,
             "distance_mpc": models.hubble_distance_mpc(0.003)},
            {"specObjID": "2", "ra": 192.0, "dec": 15.0, "z": 0.007,
             "distance_mpc": models.hubble_distance_mpc(0.007)},
        ]
        content, stats, reference_size, extents, _ = models.build_model(points, config)
        self.assertLess(stats["bytes"], 1_500_000)
        self.assertEqual(stats["external_resources"], [])
        self.assertEqual(stats["triangle_count"], 0)
        self.assertAlmostEqual(reference_size, config["value_m"] / models.MPC_M)
        self.assertAlmostEqual(max(extents) / reference_size, 1.04, delta=0.08)
        self.assertEqual(stats["extensions_used"].count("KHR_materials_unlit"), 1)
        self.assertEqual(inspect_glb(content)["sha256"], stats["sha256"])
        document, _ = read_glb(content)
        self.assertFalse(any(node.get("extras", {}).get("label") for node in document["nodes"]))

    def test_rotation_matches_three_intrinsic_xyz(self):
        # Independent closed-form check with both pitch and yaw nonzero.
        x, y = math.radians(20), math.radians(10)
        expected = np.array([[math.cos(y), 0, math.sin(y)],
                             [math.sin(x) * math.sin(y), math.cos(x), -math.sin(x) * math.cos(y)],
                             [-math.cos(x) * math.sin(y), math.sin(x), math.cos(x) * math.cos(y)]])
        np.testing.assert_allclose(models.rotation_matrix_xyz({"x": 20, "y": 10}), expected)

    def test_catalog_entries_declare_diagram_semantics_and_native_unit_reference(self):
        self.assertEqual(models.CONFIG["virgo"]["value_m"], 9.46e23)
        self.assertAlmostEqual(models.CONFIG["virgo"]["value_m"] / models.MPC_M, 30.658, places=3)
        self.assertAlmostEqual(models.CONFIG["sloan"]["value_m"] / models.MPC_M, 450.0, places=3)
        self.assertEqual(models.CONFIG["virgo"]["pose"], {"pitch": 20, "yaw": 10})
        self.assertEqual(models.CONFIG["sloan"]["pose"], {"pitch": 65})
        self.assertEqual(models.CONFIG["sloan"]["pre_rotation"], {"y": 90})

    def test_sloan_length_uses_comoving_mpc_not_megalightyears(self):
        config = models.CONFIG["sloan"]
        self.assertEqual(config["value_m"], 1.3885549116711151e25)
        self.assertAlmostEqual(config["value_m"] / models.MPC_M, 450.0, places=12)
        self.assertAlmostEqual(config["value_m"] / models.LY_M / 1e9, 1.467, places=2)

    def test_catalog_dir_uses_snapshots_offline_and_records_repo_relative_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshots = root / "catalogs"
            output = root / "output"
            snapshots.mkdir()
            (snapshots / "sdss-dr17-virgo-window.csv").write_text(
                "#Table1\nra,dec,z,specObjID\n184,8,0.003,1\n192,15,0.007,2\n")
            (snapshots / "sdss-dr17-sloan-window.csv").write_text(
                "#Table1\nra,dec,z,specObjID\n140,0,0.06,3\n190,1,0.08,4\n")
            with mock.patch.object(models, "fetch_catalog", side_effect=AssertionError("network fallback")):
                entries = models.run(output, list(models.CONFIG), catalog_dir=snapshots)
            self.assertEqual([entry["processing"]["selection_rows"] for entry in entries], [2, 2])
            for entry in entries:
                self.assertEqual(entry["representation"], "catalog_diagram")
                self.assertEqual(entry["volume_semantics"], "not_a_volume_measurement")
                self.assertTrue(entry["processing"]["source_catalog"].startswith(
                    "content/visualizations/models/sources/catalogs/"))
                self.assertEqual(len(entry["processing"]["source_catalog_sha256"]), 64)
            self.assertEqual(entries[0]["presentation"]["pitch"], 20)
            self.assertEqual(entries[0]["presentation"]["yaw"], 10)
            self.assertEqual(entries[1]["presentation"]["pre_rotation"], {"y": 90})
            self.assertEqual(entries[1]["presentation"]["pitch"], 65)


if __name__ == "__main__":
    unittest.main()
