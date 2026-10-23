"""Dimensional and source-integrity checks, independent of production WebGL."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from fetch_model_assets import inspect_glb
from render_earth3d_previews import parts


class EarthModels(unittest.TestCase):
    @staticmethod
    def vertices(slug):
        scene, _ = parts(ROOT/f'content/visualizations/models/earth3d-{slug}.glb', {})
        return np.concatenate([part['pos'] for part in scene]), scene

    def test_spherical_objects_are_isotropic(self):
        # Basketball now uses a real photoscan; its irregularities must not be
        # forced into the exact sphere used by these remaining illustrations.
        for slug in ['table-tennis', 'tennis']:
            with self.subTest(slug=slug):
                vertices, _ = self.vertices(slug)
                # parts() normalizes by longest dimension, so all axes must be 1.
                np.testing.assert_allclose(np.ptp(vertices, axis=0), [1, 1, 1], atol=1e-6)
                np.testing.assert_allclose(np.linalg.norm(vertices, axis=1), .5, atol=1e-6)

    def test_card_retains_standard_width_height_and_thickness_ratios(self):
        vertices, _ = self.vertices('credit-card')
        np.testing.assert_allclose(np.ptp(vertices, axis=0), [1, 53.98/85.6, .76/85.6], atol=1e-6)

    def test_mirror_has_central_bore_and_unexaggerated_curvature(self):
        vertices, scene = self.vertices('vlt-mirror')
        # First primitive is the optical face; reverse the normalized centering.
        face = scene[0]['pos'] * 8.2
        radii = np.hypot(face[:, 0], face[:, 1])
        self.assertAlmostEqual(radii.min(), .5, places=5)
        self.assertAlmostEqual(radii.max(), 4.1, places=5)
        sag = lambda r: r*r/(28.8*(1+np.sqrt(1-(-.004616)*(r/28.8)**2)))
        self.assertAlmostEqual(np.ptp(face[:, 2]), sag(4.1)-sag(.5), places=5)
        # Surface normals point towards the opening, not into the substrate.
        self.assertGreater(scene[0]['normals'][:, 2].min(), .98)

    def test_gateway_arch_height_equals_outer_span(self):
        vertices, _ = self.vertices('gateway-arch')
        extent = np.ptp(vertices, axis=0)
        self.assertAlmostEqual(extent[0]/extent[1], 1, places=5)
        # True tapered triangular exterior: depth is ~54/630 of height.
        self.assertLess(abs(extent[2] - 54/630), .001)

    def test_terrain_preserves_metres_and_offline_grid_integrity(self):
        source = ROOT/'content/visualizations/models/sources/earth3d-meteor-crater'
        meta = json.loads((source/'provenance.json').read_text())
        self.assertEqual(hashlib.sha256((source/'terrain.npz').read_bytes()).hexdigest(), meta['grid_sha256'])
        data = np.load(source/'terrain.npz')
        self.assertEqual(meta['vertical_gain'], 1)
        self.assertAlmostEqual(np.ptp(data['x']), 1440)
        self.assertAlmostEqual(np.ptp(data['z']), 1440)
        _, scene = self.vertices('meteor-crater')
        face = scene[0]['pos'] * 1440
        self.assertAlmostEqual(np.ptp(face[:, 1]), float(np.ptp(data['heights'])), places=3)
        self.assertGreater(scene[0]['normals'][:, 1].min(), 0)
        # All four cropped side walls face outside the block.
        wall = scene[1]
        self.assertGreater(np.min(np.sum(wall['pos'][:, [0, 2]]*wall['normals'][:, [0, 2]], axis=1)), .49)

    def test_every_delivery_is_self_contained_small_and_calibrated(self):
        entries = sorted((ROOT/'handoff/earth3d').glob('*.entry.json'))
        self.assertEqual(len(entries), 14)
        registry = json.loads((ROOT/'content/visualizations/models.json').read_text())
        current = {name: model for model in registry['models']
                   for name in model.get('matches', {}).get('length', [])}
        for path in entries:
            entry = json.loads(path.read_text())
            # A replacement intentionally removes the retired GLB. Continue
            # checking the active delivery for that item, including real scans.
            active = current[entry['matches']['length'][0]]
            if active['id'] != entry['id']:
                entry = active
            with self.subTest(model=entry['id']):
                stats = inspect_glb((ROOT/entry['src']).read_bytes())
                self.assertLess(stats['bytes'], 3_000_000)
                self.assertEqual(stats['sha256'], entry['sha256'])
                self.assertEqual(stats['external_resources'], [])
                self.assertEqual(stats['decompression_required'], [])
                scene, _ = parts(ROOT/entry['src'], entry['presentation'])
                vertices = np.concatenate([part['pos'] for part in scene])
                extent = max(np.ptp(vertices, axis=0)[:2])
                self.assertGreaterEqual(extent, .6)
                self.assertLessEqual(extent, 1.3)

    def test_downloads_retain_license_and_author_evidence(self):
        folder = ROOT/'content/visualizations/models/sources/earth3d-imports'
        for slug in ['boeing-747-8', 'elephant-bird-egg', 'komodo-dragon', 'hindenburg']:
            with self.subTest(slug=slug):
                license_info = json.loads((folder/f'{slug}.license.json').read_text())
                entry = json.loads((ROOT/f'handoff/earth3d/earth3d-{slug}.entry.json').read_text())
                self.assertEqual(license_info['license']['slug'], 'by')
                self.assertTrue(license_info['isDownloadable'])
                self.assertEqual(license_info['uid'], entry['sketchfab_uid'])
                self.assertIn(license_info['author']['username'], entry['author'])
                self.assertEqual(license_info['author']['username'], entry['sketchfab_author'])
                manifest = json.loads((ROOT/'content/visualizations/models/sketchfab-length.json').read_text())
                curated = next(item for item in manifest['models'] if item['id'] == entry['id'])
                self.assertEqual(curated['author'], license_info['author']['username'])


if __name__ == '__main__':
    unittest.main()
