"""Scoped source/value checks for the planet Area and Volume additions."""
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("Mercury", "Venus", "Mars", "Saturn", "Uranus", "Neptune", "Pluto")
RADII_KM = {
    "Mercury": 2439.4, "Venus": 6051.8, "Mars": 3389.50,
    "Saturn": 58232.0, "Uranus": 25362.0, "Neptune": 24622.0,
    "Pluto": 1188.3,
}


def records(dimension):
    return json.loads((ROOT / f"dataset/raw/curated/{dimension}.json").read_text())


class PlanetAreaVolumeTests(unittest.TestCase):
    def test_new_items_are_unique_and_derived_from_jpl_mean_radii(self):
        for dimension, formula in (
            ("area", lambda r: 4 * math.pi * r**2),
            ("volume", lambda r: 4 * math.pi * r**3 / 3),
        ):
            rows = records(dimension)
            names = [r["canonical_name"] for r in rows]
            for body, radius_km in RADII_KM.items():
                name = f"{body} {'surface area' if dimension == 'area' else 'volume'}"
                self.assertEqual(names.count(name), 1)
                row = next(r for r in rows if r["canonical_name"] == name)
                self.assertEqual(row["value_type"], "derived")
                self.assertEqual(row["source_url"], "https://ssd.jpl.nasa.gov/planets/phys_par.html")
                self.assertEqual(row["qualifiers"]["mean_radius_km"], radius_km)
                expected = formula(radius_km * 1000)
                self.assertAlmostEqual(row["value_base"] / expected, 1, delta=6e-6)

        saturn_area = next(
            r for r in records("area") if r["canonical_name"] == "Saturn surface area"
        )
        self.assertEqual(
            saturn_area["qualifiers"]["measurement"],
            "equivalent-volume sphere surface area",
        )

    def test_texture_map_and_volume_mappings_use_existing_body_assets(self):
        source_map = json.loads((ROOT / "handoff/planet-area-volume/area-texture-sources.json").read_text())
        entries = json.loads((ROOT / "handoff/planet-area-volume/entries.json").read_text())
        registry = json.loads((ROOT / "content/visualizations/models.json").read_text())["models"]
        ids = {entry["id"] for entry in registry}
        self.assertEqual(set(source_map["bodies"]), set(NAMES))
        self.assertTrue({v["asset_id"] for v in source_map["bodies"].values()} <= ids)
        self.assertEqual({v["item"] for v in entries["volume_mappings"]}, {f"{n} volume" for n in NAMES})
        saturn = next(v for v in entries["volume_mappings"] if v["item"] == "Saturn volume")
        self.assertEqual(saturn["geometry"], "mesh")
        self.assertIn("reference_size", saturn["calibration"]["method"])


if __name__ == "__main__":
    unittest.main()
