"""Scientific input/coordinate checks for the retry3d public-data conversions."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_retry3d_models import CONFIG, SOURCES
from build_retry3d_m87 import geometry, read_image, SOURCE, PC_PER_ARCSEC
from render_glb_preview import read_glb, accessor


class Retry3DTests(unittest.TestCase):
    def test_pinned_sources_and_original_pixel_registration(self):
        for name in CONFIG:
            with self.subTest(name=name):
                folder = SOURCES / name
                meta = json.loads((folder / 'provenance.json').read_text())
                self.assertEqual(hashlib.sha256((folder / 'grid.npz').read_bytes()).hexdigest(), meta['grid_sha256'])
                with np.load(folder / 'grid.npz') as d:
                    west, north = meta['tile_northwest_corner']
                    dx, dy = meta['native_pixel_scale_degrees']
                    np.testing.assert_allclose(d['longitude'], west + (d['source_column'] + .5) * dx)
                    np.testing.assert_allclose(d['latitude'], north - (d['source_row'] + .5) * dy)
                    self.assertTrue(np.isfinite(d['elevation_m']).all())

    def test_terrain_vertices_are_source_samples_at_physical_scale(self):
        for name, config in CONFIG.items():
            with self.subTest(name=name):
                doc, binary = read_glb(ROOT / f'content/visualizations/models/retry3d-{name}.glb')
                primitive = doc['meshes'][0]['primitives'][0]
                positions = accessor(doc, binary, primitive['attributes']['POSITION'])
                with np.load(SOURCES / name / 'grid.npz') as d:
                    lon, lat = np.meshgrid(d['longitude'], d['latitude'])
                    heights = d['elevation_m'] - config['water_level']
                    x = np.radians(lon - config['center'][0]) * 6378137 * np.cos(np.radians(config['center'][1]))
                    z = -np.radians(lat - config['center'][1]) * 6378137
                    # Recover the nearest original cell from the exported X/Z,
                    # then check its exact source elevation. Added walls or
                    # normalized/reconstructed terrain would fail these checks.
                    column = np.abs(positions[:, 0, None] - x[0]).argmin(axis=1)
                    row = np.abs(positions[:, 2, None] - z[:, 0]).argmin(axis=1)
                    np.testing.assert_allclose(positions[:, 0], x[row, column], atol=.01, rtol=0)
                    np.testing.assert_allclose(positions[:, 2], z[row, column], atol=.01, rtol=0)
                    np.testing.assert_allclose(positions[:, 1], heights[row, column], atol=.001, rtol=0)
                if name == 'baikal-depth':
                    self.assertLessEqual(float(positions[:, 1].max()), 0)
                    self.assertEqual(float(positions[:, 1].min()), -1654)

    def test_terrain_topology_has_no_added_volume_or_inverted_normals(self):
        for name in CONFIG:
            with self.subTest(name=name):
                doc, binary = read_glb(ROOT / f'content/visualizations/models/retry3d-{name}.glb')
                self.assertEqual(len(doc['nodes']), 1)
                prim = doc['meshes'][0]['primitives'][0]
                positions = accessor(doc, binary, prim['attributes']['POSITION'])
                indices = accessor(doc, binary, prim['indices']).reshape(-1, 3)
                self.assertLessEqual(len(indices), 60000)
                cross = np.cross(positions[indices[:, 1]] - positions[indices[:, 0]],
                                 positions[indices[:, 2]] - positions[indices[:, 0]])
                self.assertTrue((cross[:, 1] > 0).all())
                normals = accessor(doc, binary, prim['attributes']['NORMAL'])
                np.testing.assert_allclose(np.linalg.norm(normals, axis=1), 1, atol=1e-6)
                self.assertTrue((normals[:, 1] > 0).all())

    def test_m87_fits_wcs_and_preserved_date(self):
        raw = gzip.decompress((SOURCE / 'm87_hst_f555w.fits.gz').read_bytes())
        meta = json.loads((SOURCE / 'provenance.json').read_text())
        self.assertEqual(hashlib.sha256(raw).hexdigest(), meta['original_sha256'])
        image, header = read_image(raw)
        self.assertEqual(image.shape, (800, 800))
        self.assertEqual(header['DATE-OBS'], '3/02/95')
        # Header plate scale is used, rather than treating this rotated image
        # as north-up or silently substituting the nominal 0.0455 arcsec value.
        cd = np.array([[header['CD1_1'], header['CD1_2']], [header['CD2_1'], header['CD2_2']]])
        np.testing.assert_allclose(np.linalg.norm(cd, axis=0) * 3600, [.0452, .0452], atol=1e-7)

    def test_m87_one_original_observation_per_point_and_no_depth(self):
        p, value, pixel, header = geometry()
        self.assertEqual(len(p), 9689)
        self.assertEqual(len(np.unique(pixel, axis=0)), len(p))
        self.assertTrue((p[:, 2] == 0).all())
        self.assertTrue((value > 150).all())
        doc, binary = read_glb(ROOT / 'content/visualizations/models/retry3d-m87-hst-map.glb')
        self.assertEqual(len(doc['nodes']), 1)
        primitive = doc['meshes'][0]['primitives'][0]
        self.assertEqual(primitive['mode'], 0)
        exported = accessor(doc, binary, primitive['attributes']['POSITION'])
        np.testing.assert_allclose(exported, p, atol=.001, rtol=0)
        self.assertTrue((exported[:, 2] == 0).all())
        # Physical separation of adjacent native samples must remain the WCS
        # angular separation times the archive's measured-distance convention.
        locations = {tuple(x): i for i, x in enumerate(pixel)}
        for index, (x, y) in enumerate(pixel):
            neighbor = locations.get((x + 1, y))
            if neighbor is not None:
                expected = np.hypot(header['CD1_1'], header['CD2_1']) * 3600 * PC_PER_ARCSEC
                self.assertAlmostEqual(float(np.linalg.norm(exported[index] - exported[neighbor])), expected, places=3)
                break
        else:
            self.fail('No adjacent measured pixels')

    def test_registered_map_is_calibrated_without_box_normalization(self):
        registry = json.loads((ROOT / 'content/visualizations/models.json').read_text())['models']
        entry = next(m for m in registry if m['id'] == 'retry3d-m87-hst-map')
        self.assertNotIn('display_label', entry)
        self.assertEqual(entry['matches']['length'], ['M87 Jet'])
        doc, binary = read_glb(ROOT / entry['src'])
        primitive = doc['meshes'][0]['primitives'][0]
        p = accessor(doc, binary, primitive['attributes']['POSITION'])
        ratio = np.ptp(p, axis=0).max() / entry['presentation']['reference_size']
        self.assertGreaterEqual(ratio, .6)
        self.assertLessEqual(ratio, 1.3)


if __name__ == '__main__':
    unittest.main()
