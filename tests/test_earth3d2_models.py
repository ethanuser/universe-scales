"""Read delivered geometry to check calibration, winding and source integrity."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from fetch_model_assets import inspect_glb
from render_earth3d_previews import accessor, parts
from render_glb_preview import read_glb


class Earth3DSecondRound(unittest.TestCase):
    def entry(self, slug):
        return json.loads((ROOT/f'handoff/earth3d2/earth3d2-{slug}.entry.json').read_text())

    def raw(self, slug):
        entry = self.entry(slug)
        return read_glb(ROOT/entry['src'])

    def test_deliveries_are_self_contained_calibrated_and_registered(self):
        entries = sorted((ROOT/'handoff/earth3d2').glob('*.entry.json'))
        self.assertEqual(len(entries), 7)
        registry = {x['id']: x for x in json.loads((ROOT/'content/visualizations/models.json').read_text())['models']}
        for path in entries:
            entry = json.loads(path.read_text())
            with self.subTest(id=entry['id']):
                stats = inspect_glb((ROOT/entry['src']).read_bytes())
                self.assertLess(stats['bytes'], 3_000_000)
                self.assertEqual(stats['sha256'], entry['sha256'])
                self.assertEqual(stats['external_resources'], [])
                self.assertEqual(stats['decompression_required'], [])
                self.assertEqual(stats['skins'], 0)
                self.assertEqual(stats['animations'], 0)
                self.assertEqual(registry[entry['id']]['sha256'], stats['sha256'])
                self.assertEqual(registry[entry['id']], entry)
                scene, _ = parts(ROOT/entry['src'], entry['presentation'])
                p = np.concatenate([part['pos'] for part in scene])
                extent = max(np.ptp(p, axis=0)[:2])
                self.assertGreaterEqual(extent, .6)
                self.assertLessEqual(extent, 1.3)
                self.assertLessEqual(np.ptp(p[:, 0]), entry['presentation'].get('layout_width_factor', 1)+.01)
                for part in scene:
                    self.assertTrue(np.isfinite(part['pos']).all())
                    self.assertTrue(np.isfinite(part['normals']).all())

    def test_reflectors_preserve_diameter_curvature_and_concave_winding(self):
        for slug, diameter, radius in [('fast-reflector', 500, 300), ('arecibo-reflector', 305, 265)]:
            with self.subTest(slug=slug):
                doc, binary = self.raw(slug)
                prim = doc['meshes'][0]['primitives'][0]
                p = accessor(doc, binary, prim['attributes']['POSITION'])
                n = accessor(doc, binary, prim['attributes']['NORMAL'])
                f = accessor(doc, binary, prim['indices']).reshape(-1, 3)
                self.assertAlmostEqual(np.ptp(p[:, 0]), diameter, places=4)
                self.assertAlmostEqual(np.ptp(p[:, 2]), diameter, places=4)
                self.assertAlmostEqual(np.ptp(p[:, 1]), radius-np.sqrt(radius**2-(diameter/2)**2), places=4)
                np.testing.assert_allclose(np.linalg.norm(p-[0, radius, 0], axis=1), radius, atol=4e-5)
                face_n = np.cross(p[f[:, 1]]-p[f[:, 0]], p[f[:, 2]]-p[f[:, 0]])
                self.assertGreater((face_n*n[f].mean(1)).sum(1).min(), 0)
                self.assertGreater(n[:, 1].min(), 0)
                # The caveat lives in the note; on-screen names stay plain.
                self.assertIn('reflector', self.entry(slug)['note'].lower())

    def test_ship_has_sourced_envelope_and_hull_faces_point_outward(self):
        doc, binary = self.raw('ever-given')
        positions = []
        for m in doc['meshes'][:2]:
            prim = m['primitives'][0]
            p = accessor(doc, binary, prim['attributes']['POSITION'])
            positions.append(p)
            f = accessor(doc, binary, prim['indices']).reshape(-1, 3)
            face_n = np.cross(p[f[:, 1]]-p[f[:, 0]], p[f[:, 2]]-p[f[:, 0]])
            center = p[f].mean(1)
            # Side faces must face away from the keel plane in Z.
            valid = abs(face_n[:, 2]) > 1e-3
            self.assertGreater((face_n[valid, 2]*center[valid, 2]).min(), 0)
        extent = np.ptp(np.concatenate(positions), axis=0)
        np.testing.assert_allclose(extent, [399.98, 32.9, 58.8], atol=3e-5)
        cargo = next(m for m in doc['meshes'] if m['name'] == 'Original container color 1')
        cp = accessor(doc, binary, cargo['primitives'][0]['attributes']['POSITION'])
        # Each box has six separately shaded four-vertex faces.
        for b in cp.reshape(-1, 24, 3)[:10]:
            np.testing.assert_allclose(np.ptp(b, axis=0), [12.192, 2.896, 2.438], atol=3e-5)

    def test_bridge_tower_centers_and_cable_apex_are_not_whole_bridge_length(self):
        entry = self.entry('golden-gate-main-span')
        self.assertIn('main span', entry['note'].lower())
        doc, binary = self.raw('golden-gate-main-span')
        m = next(m for m in doc['meshes'] if m['name'] == 'Painted main cables and suspenders')
        p = accessor(doc, binary, m['primitives'][0]['attributes']['POSITION'])
        # World X envelope includes the main cable radius at the tower saddles.
        self.assertLess(abs(np.ptp(p[:, 0])-1280.16), .93)
        self.assertGreater(p[:, 1].max(), 746*.3048)
        self.assertLess(p[:, 1].max(), 746*.3048+.47)
        self.assertEqual(entry['presentation']['reference_size'], 1280)

    def test_kilimanjaro_grid_matches_unstretched_glb_and_datum(self):
        source = ROOT/'content/visualizations/models/sources/earth3d2-kilimanjaro'
        meta = json.loads((source/'provenance.json').read_text())
        self.assertEqual(hashlib.sha256((source/'terrain.npz').read_bytes()).hexdigest(), meta['grid_sha256'])
        data = np.load(source/'terrain.npz')
        doc, binary = self.raw('kilimanjaro')
        prim = doc['meshes'][0]['primitives'][0]
        p = accessor(doc, binary, prim['attributes']['POSITION'])
        np.testing.assert_array_equal(p[:, 1], data['heights'].ravel())
        self.assertEqual(np.ptp(p[:, 0]), 6400)
        self.assertEqual(np.ptp(p[:, 2]), 6400)
        self.assertEqual(meta['vertical_gain'], 1)
        self.assertLess(p[:, 1].max(), 5895)
        self.assertGreater(p[:, 1].max(), 5880)
        self.assertEqual(self.entry('kilimanjaro')['presentation']['reference_size'], 5895)

    def test_whale_retains_direct_license_evidence_and_static_geometry(self):
        entry = self.entry('sperm-whale')
        evidence = json.loads((ROOT/entry['processing']['source_evidence']).read_text())
        self.assertEqual(evidence['uid'], entry['sketchfab_uid'])
        self.assertEqual(evidence['license']['slug'], 'by')
        self.assertEqual(evidence['author'], entry['sketchfab_author'])
        self.assertIn(evidence['author'], entry['author'])
        self.assertTrue(evidence['isDownloadable'])
        doc, _ = self.raw('sperm-whale')
        self.assertNotIn('skins', doc)
        for m in doc['meshes']:
            for prim in m['primitives']:
                self.assertNotIn('JOINTS_0', prim['attributes'])
                self.assertNotIn('WEIGHTS_0', prim['attributes'])
                self.assertIn('TANGENT', prim['attributes'])

    def test_elephant_uses_withers_height_and_retains_full_body_depth(self):
        entry = self.entry('african-elephant')
        self.assertEqual(entry['presentation']['measure_axis'], 'y')
        evidence = json.loads((ROOT/entry['processing']['source_evidence']).read_text())
        self.assertEqual(evidence['license']['slug'], 'by')
        self.assertEqual(evidence['author'], entry['sketchfab_author'])
        scene, _ = parts(ROOT/entry['src'], {'reference_size': 1})
        p = np.concatenate([part['pos'] for part in scene])
        withers = p[p[:, 1].argmax()]
        # Source-mesh landmark, not a measured living specimen.
        self.assertLess(abs(withers[0]), .002)
        self.assertGreater(withers[2], 0)
        self.assertLess(withers[2], .007)
        self.assertGreater(np.ptp(p[:, 2])/np.ptp(p[:, 1]), 1.3)


if __name__ == '__main__':
    unittest.main()
