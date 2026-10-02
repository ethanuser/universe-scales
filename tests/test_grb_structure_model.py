import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_grb_structure_model as grb
from fetch_model_assets import inspect_glb


class GrbStructureModelTests(unittest.TestCase):
    def test_projection_keeps_both_longitude_seam_edges(self):
        west = grb.mollweide(-180, 0)
        east = grb.mollweide(180, 0)
        self.assertAlmostEqual(west[0], -2 * np.sqrt(2))
        self.assertAlmostEqual(east[0], 2 * np.sqrt(2))
        self.assertAlmostEqual(grb.mollweide(360, 0)[0], 0)

    def test_spectroscopic_parser_excludes_ambiguous_and_photometric_values(self):
        self.assertEqual(grb.parse_spectroscopic_redshift("2.04 (VLT: absorption)"), 2.04)
        self.assertEqual(grb.parse_spectroscopic_redshift("1.81 (host emission spectrum)"), 1.81)
        self.assertIsNone(grb.parse_spectroscopic_redshift("2.04"))
        self.assertIsNone(grb.parse_spectroscopic_redshift("2.04 photometric"))
        self.assertIsNone(grb.parse_spectroscopic_redshift("z > 2.0 (limit)"))
        self.assertIsNone(grb.parse_spectroscopic_redshift("z > 2.0 (absorption limit)"))

    def test_swift_coordinates_accept_decimal_and_sexagesimal(self):
        self.assertAlmostEqual(grb._angle_degrees("12:00:00", ra=True), 180)
        self.assertAlmostEqual(grb._angle_degrees("-30:30:00"), -30.5)
        self.assertAlmostEqual(grb._angle_degrees("5.0", ra=True), 5.0)
        self.assertAlmostEqual(grb._angle_degrees("132.475 08:49:54.0", ra=True), 132.475)
        self.assertAlmostEqual(grb._angle_degrees("180.0", ra=True), 180)
        self.assertIsNone(grb._angle_degrees("n/a"))

    def test_cosmological_distance_matches_planck_scale(self):
        distance = grb.comoving_distance_mpc(2.0)
        self.assertGreater(distance, 5200)
        self.assertLess(distance, 5400)
        self.assertAlmostEqual(grb.comoving_distance_mpc(0), 0)

    def test_published_region_mask_uses_galactic_window(self):
        # Galactic l=60, b=30 transformed back to equatorial coordinates.
        galactic = np.array([0.5, 0.8660254037844386, 0.5])
        equatorial = grb.EQ_TO_GAL.T @ galactic
        ra = np.degrees(np.arctan2(equatorial[1], equatorial[0])) % 360
        dec = np.degrees(np.arcsin(equatorial[2]))
        self.assertTrue(grb.is_published_window(ra, dec))

    def test_mollweide_projection_is_an_equal_area_sky_chart(self):
        left = grb.mollweide(-180, 0)
        right = grb.mollweide(179.999, 0)
        north = grb.mollweide(0, 90)
        self.assertAlmostEqual(left[0], -2 * np.sqrt(2), places=6)
        self.assertAlmostEqual(right[0], 2 * np.sqrt(2), places=4)
        self.assertAlmostEqual(north[1], np.sqrt(2), places=6)

    def test_reader_filters_to_explicit_spectroscopy_and_slice(self):
        headers = ["GRB", "UVOT RA(J2000)", "UVOT Dec(J2000)", "Redshift"]
        galactic = np.array([0.5, 0.8660254037844386, 0.5])
        equatorial = grb.EQ_TO_GAL.T @ galactic
        ra = np.degrees(np.arctan2(equatorial[1], equatorial[0])) % 360
        dec = np.degrees(np.arcsin(equatorial[2]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "swift.tsv"
            with path.open("w", newline="") as output:
                writer = csv.writer(output, delimiter="\t")
                writer.writerow(headers)
                writer.writerow(["GRB-A", ra, dec, "2.04 (VLT: absorption)"])
                writer.writerow(["GRB-B", ra, dec, "2.04 (photometric)"])
                writer.writerow(["GRB-C", ra, dec, "2.3 (Keck: emission)"])
                writer.writerow(["GRB-D", "n/a", "n/a", "1.9 (VLT: absorption)"])
            events = grb.load_swift_rows(path)
        self.assertEqual([event["name"] for event in events], ["GRB-A"])
        self.assertEqual(events[0]["position_source"], "UVOT")

    def test_reader_falls_back_to_latin1_for_legacy_swift_export(self):
        headers = ["GRB", "UVOT RA(J2000)", "UVOT Dec(J2000)", "Redshift", "Comments"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "swift-latin1.tsv"
            with path.open("w", encoding="latin-1", newline="") as output:
                writer = csv.writer(output, delimiter="\t")
                writer.writerow(headers)
                writer.writerow(["GRB-A", "5.0", "10.0", "1.9 (VLT: absorption)", "observación"])
            events = grb.load_swift_rows(path)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["ra"], 5.0)

    def test_glb_is_a_quiet_dimensionless_chart_with_detached_claim_ruler(self):
        galactic = np.array([0.5, 0.8660254037844386, 0.5])
        equatorial = grb.EQ_TO_GAL.T @ galactic
        ra = np.degrees(np.arctan2(equatorial[1], equatorial[0])) % 360
        dec = np.degrees(np.arcsin(equatorial[2]))
        event = {"name": "catalog event", "ra": ra, "dec": dec, "z": 1.9}
        data, total, in_window = grb.build_glb([event])
        stats = inspect_glb(data)
        self.assertEqual((total, in_window), (1, 1))
        self.assertLess(len(data), 1_500_000)
        self.assertEqual(stats["external_resources"], [])
        self.assertEqual(stats["triangle_count"], 0)
        document_length = int.from_bytes(data[12:16], "little")
        document = json.loads(data[20:20 + document_length])
        names = [node.get("name", "") for node in document["nodes"]]
        self.assertTrue(any("Observed GRB directions" in name for name in names))
        self.assertTrue(any("Claimed extent" in name for name in names))
        self.assertFalse(any("shell" in name.lower() for name in names))
        self.assertFalse(any("wall surface" in name.lower() for name in names))
        labels = [node["extras"]["label"] for node in document["nodes"]
                  if node.get("extras", {}).get("label")]
        self.assertEqual(labels, ["10 Gly"])
        spans = []
        ruler_span = None
        for mesh in document["meshes"]:
            primitive = mesh["primitives"][0]
            bounds = document["accessors"][primitive["attributes"]["POSITION"]]
            span = np.asarray(bounds["max"]) - np.asarray(bounds["min"])
            spans.append(span)
            if mesh["name"] == "Claimed extent scale bar":
                ruler_span = span[0]
        self.assertAlmostEqual(ruler_span, 1.0, places=5)
        self.assertLessEqual(max(float(np.max(span)) for span in spans), 1.3)
        for node in document["nodes"]:
            if "mesh" in node:
                self.assertLess(node["mesh"], len(document["meshes"]))


if __name__ == "__main__":
    unittest.main()
