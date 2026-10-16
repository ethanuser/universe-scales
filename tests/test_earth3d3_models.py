"""Delivered geometry constraints and CPU texture-review regressions."""
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from fetch_model_assets import inspect_glb
from render_earth3d_previews import accessor, parts, render
from render_glb_preview import read_glb


class Earth3DThirdRound(unittest.TestCase):
    def entries(self):
        return [json.loads(p.read_text()) for p in sorted((ROOT/'handoff/earth3d3').glob('*.entry.json'))]

    def test_registered_deliveries_load_calibrate_and_match_handoff(self):
        entries = self.entries()
        self.assertEqual(len(entries), 7)
        registry = {e['id']: e for e in json.loads((ROOT/'content/visualizations/models.json').read_text())['models']}
        for entry in entries:
            with self.subTest(model=entry['id']):
                self.assertEqual(registry[entry['id']], entry)
                stats = inspect_glb((ROOT/entry['src']).read_bytes())
                self.assertEqual(stats['sha256'], entry['sha256'])
                self.assertLess(stats['bytes'], 3_000_000)
                self.assertFalse(stats['external_resources'])
                self.assertFalse(stats['decompression_required'])
                self.assertEqual((stats['skins'], stats['animations']), (0, 0))
                self.assertNotIn('display_label', entry)
                scene, _ = parts(ROOT/entry['src'], entry['presentation'])
                p = np.concatenate([q['pos'] for q in scene])
                self.assertTrue(np.isfinite(p).all())
                self.assertGreaterEqual(max(np.ptp(p, axis=0)[:2]), .6)
                self.assertLessEqual(max(np.ptp(p, axis=0)[:2]), 1.3)
                self.assertLessEqual(np.ptp(p[:, 0]), entry['presentation'].get('layout_width_factor', 1)+.01)
                doc, binary = read_glb(ROOT/entry['src'])
                for m in doc['meshes']:
                    for q in m['primitives']:
                        if 'NORMAL' in q['attributes']:
                            n = accessor(doc, binary, q['attributes']['NORMAL'])
                            np.testing.assert_allclose(np.linalg.norm(n, axis=1), 1, atol=.002)

    def test_authored_envelopes_preserve_physical_dimensions(self):
        for slug, reference in [('giant-squid', 13), ('lolong', 6.17), ('prelude-flng', 488), ('rafflesia', 1)]:
            entry = next(e for e in self.entries() if e['id'] == 'earth3d3-'+slug)
            scene, _ = parts(ROOT/entry['src'], {'reference_size': 1})
            p = np.concatenate([q['pos'] for q in scene])
            with self.subTest(slug=slug):
                self.assertAlmostEqual(np.ptp(p[:, 0]), reference, delta=.001)
                if slug == 'prelude-flng':
                    self.assertAlmostEqual(np.ptp(p[:, 2]), 74, delta=.001)
        entry = next(e for e in self.entries() if e['id'] == 'earth3d3-hoover-dam')
        doc, binary = read_glb(ROOT/entry['src'])
        face = doc['meshes'][0]['primitives'][0]
        p = accessor(doc, binary, face['attributes']['POSITION'])
        self.assertAlmostEqual(np.ptp(p[:, 1]), 726.4*.3048, delta=.001)
        self.assertAlmostEqual(entry['presentation']['reference_size'], 726.4*.3048)

    def test_import_licenses_are_direct_evidence_and_octopus_stays_pending(self):
        for entry in self.entries():
            if 'sketchfab_uid' not in entry:
                continue
            evidence = json.loads((ROOT/entry['processing']['source_evidence']).read_text())
            self.assertTrue(evidence['isDownloadable'])
            self.assertEqual(evidence['license']['slug'], 'by')
            self.assertEqual(evidence['author'], entry['sketchfab_author'])
            self.assertEqual(evidence['uid'], entry['sketchfab_uid'])
        registry = json.loads((ROOT/'content/visualizations/models.json').read_text())['models']
        self.assertFalse(any('Giant Pacific Octopus' in e.get('matches', {}).get('length', []) for e in registry))
        pending = json.loads((ROOT/'handoff/earth3d3/pending/earth3d3-giant-pacific-octopus.candidate.json').read_text())
        self.assertEqual(inspect_glb((ROOT/pending['asset']).read_bytes())['sha256'], pending['sha256'])

    def test_cpu_repeat_wrap_and_unlit_materials(self):
        # Translating a repeated UV atlas by an integer must preserve the image.
        texture = np.array([[[1., .2, .1, 1], [.2, 1, .1, 1]],
                            [[.1, .2, 1, 1], [1, 1, 1, 1]]])
        part = dict(pos=np.array([[-1., -1, 0], [1., -1, 0], [0., 1, 0]]),
                    indices=np.array([[0, 1, 2]]), color=np.ones((3, 4)), normals=np.tile([0., 0, -1], (3, 1)),
                    uv=np.array([[.1, .1], [1.9, .1], [.1, 1.9]]), tex=texture,
                    wrap=(10497, 10497), unlit=True, mask=.01)
        base, _ = render([part], size=70)
        shifted = {**part, 'uv': part['uv']+[3, -2]}
        repeated, _ = render([shifted], size=70)
        np.testing.assert_array_equal(np.array(base), np.array(repeated))
        # An unlit white surface must not get a Lambert-light multiplier.
        part = {**part, 'tex': None}
        white, _ = render([part], size=70)
        np.testing.assert_array_equal(np.asarray(white)[35, 35], [255, 255, 255])


if __name__ == '__main__':
    unittest.main()
