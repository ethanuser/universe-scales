import hashlib
import json
import math
import unittest
from pathlib import Path

from shapely.geometry import shape
from shapely.ops import transform


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "content/visualizations/area-sources"
ENTRIES = ROOT / "handoff/area-gis/entries.json"
MANIFEST = ASSETS / "manifest.json"
REQUIRED_FIELDS = {
    "id", "name", "geojson", "central_longitude", "source", "author",
    "license", "license_url", "note",
}
EXPECTED_IDS = {
    "lake-tahoe-surface", "new-york-city", "caspian-sea-surface",
    "texas", "greenland", "australia",
}


def spherical_cylindrical_equal_area_estimate(geometry):
    # Spherical cylindrical equal-area transform with R=6378137 m.
    radius = 6_378_137
    standard_parallel_cos = math.cos(math.radians(30))

    def project(longitude, latitude, z=None):
        return (
            radius * standard_parallel_cos * math.radians(longitude),
            radius * math.sin(math.radians(latitude)) / standard_parallel_cos,
        )

    return transform(project, geometry).area


class PreparedAreaGisTests(unittest.TestCase):
    def test_entries_are_a_compact_licensed_array(self):
        entries = json.loads(ENTRIES.read_text(encoding="utf-8"))
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        by_id = {entry["id"]: entry for entry in entries}
        self.assertIsInstance(entries, list)
        self.assertEqual(set(by_id), EXPECTED_IDS)
        self.assertTrue(all(set(entry) == REQUIRED_FIELDS for entry in entries))
        self.assertEqual(
            {path.name for path in ASSETS.glob("*.geojson")},
            {Path(entry["geojson"]).name for entry in entries},
        )

        total_bytes = 0
        for item_id, entry in by_id.items():
            self.assertIn("Public domain", entry["license"])
            self.assertNotIn("ODbL", entry["license"])
            path = ROOT / entry["geojson"]
            payload_bytes = path.read_bytes()
            total_bytes += len(payload_bytes)
            collection = json.loads(payload_bytes)
            self.assertEqual(collection["type"], "FeatureCollection")
            self.assertEqual(len(collection["features"]), 1)
            geometry = shape(collection["features"][0]["geometry"])
            self.assertTrue(geometry.is_valid, item_id)
            item = manifest_item(manifest, item_id)
            self.assertLessEqual(item["output_vertices"], 100_000)
            self.assertEqual(item["output_bytes"], len(payload_bytes))
            self.assertEqual(item["output_sha256"], hashlib.sha256(payload_bytes).hexdigest())

        self.assertEqual(total_bytes, manifest["total_geometry_bytes"])
        self.assertLess(total_bytes, 2_000_000)

    def test_pinned_source_hashes_and_city_quantity_notes(self):
        from importlib.util import module_from_spec, spec_from_file_location

        script_path = ROOT / "scripts/prepare_area_gis.py"
        spec = spec_from_file_location("prepare_area_gis", script_path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for key, expected_hash in module.PINNED_SOURCE_SHA256.items():
            self.assertEqual(manifest["source_snapshots"][key]["sha256"], expected_hash)

        items = {item["id"]: item for item in manifest["items"]}
        self.assertNotIn("manhattan", items)
        self.assertNotIn("rhode-island", items)
        nyc = items["new-york-city"]
        self.assertEqual(nyc["quantity_definition"], "Land area")
        self.assertEqual(nyc["source_feature_count"], 5)
        self.assertIn("736.005 km2", nyc["note"])
        self.assertIn("778.181 km2", nyc["note"])
        self.assertAlmostEqual(
            spherical_cylindrical_equal_area_estimate(
                shape(json.loads((ROOT / nyc["geojson"]).read_text())["features"][0]["geometry"])
            ) / 1e6,
            736.005,
            places=2,
        )


def manifest_item(manifest, item_id):
    return next(item for item in manifest["items"] if item["id"] == item_id)


if __name__ == "__main__":
    unittest.main()
