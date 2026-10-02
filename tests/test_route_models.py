import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_route_models as routes
from fetch_model_assets import inspect_glb, pack_glb, read_glb, view_bytes
from geo_glb_common import GLB


class RouteModelTests(unittest.TestCase):
    def test_geographic_coordinates_keep_earth_scale(self):
        center = (108, 37)
        at = routes.geographic_frame(np.array([center, (109, 37)]), center)
        np.testing.assert_allclose(at[0], [0, 0, 0], atol=1e-8)
        chord = np.linalg.norm(at[1] - at[0])
        arc = routes.geodesic_km([center, (109, 37)])
        self.assertLess(chord, arc)
        self.assertAlmostEqual(chord, arc, delta=0.01)
        self.assertGreater(arc, 88)
        self.assertLess(arc, 90)
        self.assertGreater(at[1, 0], 0)
        self.assertLess(routes.geographic_frame(np.array([108, 38]), center)[2], 0)

    def test_total_ruler_is_independent_of_geographic_extent(self):
        glb = GLB()
        total = 21196.18
        routes.add_ruler(glb, total, -7000, 0, "Inventory, not end-to-end length")
        line = glb.doc["nodes"][0]
        self.assertEqual(line["extras"]["screenLine"], {"axis": "x", "length": total, "width": 2})
        self.assertEqual(line["scale"][0], total)
        label = glb.doc["nodes"][-1]
        self.assertEqual(label["extras"]["labelRole"], "dimension")
        self.assertLess(label["extras"]["labelOffset"]["y"], 0)
        self.assertEqual(inspect_glb(pack_glb(glb.doc, bytes(glb.bin)))["triangle_count"], 36)

    def test_osm_preserves_gaps_and_deduplicates_ways(self):
        member = lambda ref, a, b: {"type": "way", "ref": ref,
                                    "geometry": [{"lon": a[0], "lat": a[1]}, {"lon": b[0], "lat": b[1]}]}
        first = member(1, (0, 0), (1, 0))
        result = routes.osm_geojson({"elements": [{"type": "relation", "id": 99,
                  "members": [first, member(2, (5, 0), (6, 0)), first]}]})
        self.assertEqual(len(result["features"]), 2)
        self.assertEqual(result["license"], routes.OSM_LICENSE)
        lines = routes.lines_from_geojson(result)
        self.assertEqual(len(lines), 2)
        self.assertLess(sum(routes.geodesic_km(p) for p in lines), 225)
        self.assertGreater(routes.geodesic_km(np.concatenate(lines)), 650)

    def test_incomplete_osm_geometry_rejected(self):
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            routes.osm_geojson({"elements": [{"type": "relation", "id": 1,
                "members": [{"type": "way", "ref": 1, "geometry": [None]}]}]})

    def test_map_clipping_does_not_bridge_outside_fragments(self):
        line = np.array([[-2, 0], [0, 0], [2, 0], [2, 2], [0, 0]])
        clipped = routes.clip_lines([line], (-1, -1, 1, 1))
        self.assertEqual(len(clipped), 2)
        for path in clipped:
            self.assertTrue(np.all(path >= -1))
            self.assertTrue(np.all(path <= 1))
        np.testing.assert_allclose(clipped[0][0], [-1, 0])
        np.testing.assert_allclose(clipped[0][-1], [1, 0])

    def test_globe_diameter_and_texture_uv_orientation(self):
        glb = GLB()
        routes.globe(glb, {"features": []}, (108, 37))
        mesh = glb.doc["meshes"][0]["primitives"][0]
        position = glb.doc["accessors"][mesh["attributes"]["POSITION"]]
        self.assertAlmostEqual((position["max"][0] - position["min"][0]) * glb.doc["nodes"][0]["scale"][0], 2 * routes.RADIUS_KM, delta=10)
        source, binary = read_glb((SCRIPTS.parent / "content/visualizations/models/nasa-earth.glb").read_bytes())
        self.assertEqual(glb.doc["materials"], source["materials"])
        for target_image, source_image in zip(glb.doc["images"], source["images"]):
            self.assertEqual(view_bytes(glb.doc, glb.bin, target_image["bufferView"]),
                             view_bytes(source, binary, source_image["bufferView"]))
        lon, lat = np.radians([108, 37])
        q = np.array(glb.doc["nodes"][0]["rotation"])
        point = np.array([-np.cos(lat)*np.sin(lon), np.sin(lat), -np.cos(lat)*np.cos(lon)])
        rotated = point + 2 * np.cross(q[:3], np.cross(q[:3], point) + q[3] * point)
        np.testing.assert_allclose(rotated, [0, 0, 1], atol=1e-8)
        stats = inspect_glb(pack_glb(glb.doc, bytes(glb.bin)))
        self.assertLess(stats["triangle_count"], 20000)
        self.assertEqual(stats["external_resources"], [])

    def test_wall_has_no_floating_fragment_callout(self):
        geometry = {"type": "FeatureCollection", "features": [{"type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": [[108, 37], [109, 37]]}}]}
        with TemporaryDirectory() as directory:
            _, glb = routes.build("wall", geometry, {"features": []}, Path(directory), Path(directory))
        labels = [node["extras"]["label"] for node in glb.doc["nodes"] if "label" in node.get("extras", {})]
        self.assertEqual(labels, [routes.CONFIG["wall"]["ruler"]])

    def test_registered_routes_match_dataset_without_stretching(self):
        root = SCRIPTS.parent
        models = json.loads((root / "content/visualizations/models.json").read_text())["models"]
        for config in routes.CONFIG.values():
            entry = next(m for m in models if m["id"] == config["id"])
            self.assertEqual(entry["presentation"]["reference_size"], config["total_km"])
            self.assertFalse(entry["processing"]["route_rescaled"])
            self.assertLess(entry["bytes"], 1500000)
            self.assertLess(entry["triangle_count"], 60000)
            self.assertEqual(entry["external_resources"], [])
            self.assertTrue((root / "content/visualizations/models" / entry["processing"]["source_geometry"]).exists())

    def test_road_drapes_on_mesh_not_finer_buried_dem_samples(self):
        positions = np.array([[[0, 0, 0], [10, 0, 0]], [[0, 0, 10], [10, 10, 10]]], float)
        config = {"bounds": (0, 0, 1, 1)}
        at = routes.drape_on_terrain(np.array([[0.2, 0.8], [0.8, 0.2]]), positions, config, 0.1)
        np.testing.assert_allclose(at[0], [2, 0.1, 2])
        np.testing.assert_allclose(at[1], [8, 6.1, 8])


if __name__ == "__main__":
    unittest.main()
