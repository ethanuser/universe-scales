"""Physical geometry, calibration and compatibility of delivered micro3d assets."""
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


class Micro3DModels(unittest.TestCase):
    def entry(self, slug):
        return json.loads((ROOT/f'handoff/micro3d/micro3d-{slug}.entry.json').read_text())

    def meshes(self, slug):
        entry = self.entry(slug)
        doc, binary = read_glb(ROOT/entry['src'])
        return [(m['name'], accessor(doc, binary, p['attributes']['POSITION']))
                for m in doc['meshes'] for p in m['primitives']]

    def test_assets_are_registered_decoder_free_with_valid_rest_extents(self):
        entries = sorted((ROOT/'handoff/micro3d').glob('*.entry.json'))
        self.assertEqual(len(entries), 4)
        registry = {e['id']: e for e in json.loads((ROOT/'content/visualizations/models.json').read_text())['models']}
        for path in entries:
            entry = json.loads(path.read_text())
            with self.subTest(id=entry['id']):
                stats = inspect_glb((ROOT/entry['src']).read_bytes())
                self.assertEqual(entry, registry[entry['id']])
                self.assertEqual(entry['sha256'], stats['sha256'])
                self.assertLess(stats['bytes'], 3_000_000)
                self.assertEqual(stats['external_resources'], [])
                self.assertEqual(stats['decompression_required'], [])
                self.assertNotIn('display_label', entry)
                self.assertTrue((ROOT/entry['processing']['source_note']).is_file())
                scene, _ = parts(ROOT/entry['src'], entry['presentation'])
                extent = np.ptp(np.concatenate([p['pos'] for p in scene]), axis=0)
                self.assertGreaterEqual(max(extent[:2]), .6)
                self.assertLessEqual(max(extent[:2]), 1.3)
                self.assertLessEqual(extent[0], entry['presentation'].get('layout_width_factor', 1)+1e-5)

    def test_explicit_normals_and_winding_agree(self):
        for path in (ROOT/'handoff/micro3d').glob('*.entry.json'):
            entry = json.loads(path.read_text())
            doc, binary = read_glb(ROOT/entry['src'])
            for m in doc['meshes']:
                for primitive in m['primitives']:
                    p = accessor(doc, binary, primitive['attributes']['POSITION']).astype(float)
                    n = accessor(doc, binary, primitive['attributes']['NORMAL']).astype(float)
                    f = accessor(doc, binary, primitive['indices']).reshape(-1, 3)
                    with self.subTest(id=entry['id'], mesh=m['name']):
                        np.testing.assert_allclose(np.linalg.norm(n, axis=1), 1, atol=1e-5)
                        face = np.cross(p[f[:, 1]]-p[f[:, 0]], p[f[:, 2]]-p[f[:, 0]])
                        lengths = np.linalg.norm(face, axis=1)
                        valid = lengths > lengths.max()*1e-9
                        self.assertGreater(((face[valid]/lengths[valid, None])*n[f[valid]].mean(1)).sum(1).min(), -.01)

    def test_helium_guide_is_rms_and_nucleons_are_only_composition_glyphs(self):
        meshes = self.meshes('helium-charge')
        self.assertEqual(sum('Proton glyph' == n for n, _ in meshes), 2)
        self.assertEqual(sum('Neutron glyph' == n for n, _ in meshes), 2)
        for name, p in meshes:
            if 'rms guide' in name:
                radius = np.linalg.norm(p, axis=1)
                self.assertAlmostEqual((radius.min()+radius.max())/2, 1.6785, places=5)
        self.assertIn('not a hard outer', self.entry('helium-charge')['note'])

    def test_fiber_coating_is_true_radius_and_not_mode_field(self):
        for name, p in self.meshes('optical-fiber'):
            radius = np.linalg.norm(p[:, :2], axis=1)
            if name == 'Core': np.testing.assert_allclose(radius, 4.1, atol=1e-5)
            if name == '125 micrometre cladding exterior': np.testing.assert_allclose(radius, 62.5, atol=1e-5)
            if name == 'Remaining polymer coating sector':
                self.assertTrue(np.allclose(radius, 62.5, atol=1e-4) or np.allclose(radius, 121, atol=1e-4))

    def test_karman_preserves_spherical_radii_and_altitude(self):
        for name, p in self.meshes('karman-line')[:2]:
            radius = np.linalg.norm(p + [0, 6371, 0], axis=1)
            np.testing.assert_allclose(radius, 6471 if '100 km' in name else 6371, atol=1e-4)

    def test_paramecium_body_length(self):
        body = self.meshes('paramecium')[0][1]
        self.assertAlmostEqual(float(np.ptp(body[:, 0])), 250)
        self.assertIn('not a scan', self.entry('paramecium')['note'])


if __name__ == '__main__': unittest.main()
