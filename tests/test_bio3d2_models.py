"""Scientific calibration/topology regressions for the cell/animal additions."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from render_glb_preview import read_glb, accessor
from build_bio3d2_cells import Diagram


def meshes(kind):
    doc, binary = read_glb(ROOT/f'content/visualizations/models/bio3d2-{kind}.glb')
    return {m['name']: [accessor(doc, binary, p['attributes']['POSITION']).astype(float)
                        for p in m['primitives']] for m in doc['meshes']}


class BiologicalModels(unittest.TestCase):
    def test_ellipsoid_front_faces_point_outward(self):
        # CPU previews use two-sided lighting; this catches reversed faces that
        # otherwise disappear in the actual single-sided production material.
        d = Diagram(); m = d.material('test', (.5, .5, .5))
        d.ellipsoid('ellipsoid', (3, -2, 1), (2, 3, 1), m)
        p, f = d.parts[('ellipsoid', m)][0]
        n = np.cross(p[f[:, 1]]-p[f[:, 0]], p[f[:, 2]]-p[f[:, 0]])
        self.assertTrue(np.all(np.sum(n*(p[f].mean(1)-[3, -2, 1]), axis=1) > 0))

    def test_bilayer_thickness_and_inward_tails(self):
        scene = meshes('membrane')
        heads = np.concatenate(scene['Hydrophilic head groups'])
        tails = np.concatenate(scene['Paired inward hydrophobic tails'])
        np.testing.assert_allclose([heads[:, 1].min(), heads[:, 1].max()], [-2, 2], atol=1e-6)
        self.assertLess(np.abs(tails[:, 1]).max(), 1.6)
        self.assertGreaterEqual(np.abs(heads[:, 1]).min(), 1.49)

    def test_platelet_anucleate_and_mii_egg_without_interphase_nucleus(self):
        self.assertFalse(any('nucleus' in name.lower() for name in meshes('platelet')))
        egg = meshes('egg')
        self.assertFalse(any('nucleus' in name.lower() for name in egg))
        self.assertTrue(any('meiotic spindle' in name for name in egg))
        self.assertTrue(any('polar body' in name for name in egg))

    def test_capillary_has_an_open_lumen_and_calibrated_outer_diameter(self):
        scene = meshes('capillary')
        wall = np.concatenate([p for name, parts in scene.items() if 'wall' in name or 'lamina' in name for p in parts])
        radius = np.linalg.norm(wall[:, 1:], axis=1)
        self.assertGreater(radius.min(), 3.04)
        self.assertAlmostEqual(radius.max(), 3.5, places=5)
        self.assertAlmostEqual(np.ptp(wall[:, 1]), 7, places=5)

    def test_polar_body_sits_between_oocyte_and_zona(self):
        egg = meshes('egg')
        polar = np.concatenate(egg['First polar body (illustrative)'])
        radius = np.linalg.norm(polar, axis=1)
        self.assertGreater(radius.min(), 60)
        self.assertLess(radius.max(), 65)

    def test_registry_handoff_and_source_license_pins(self):
        registry = json.loads((ROOT/'content/visualizations/models.json').read_text())['models']
        entries = [e for e in registry if e['id'].startswith('bio3d2-')]
        self.assertEqual(len(entries), 12)
        for e in entries:
            self.assertEqual(e, json.loads((ROOT/'handoff/bio3d2'/f"{e['id']}.entry.json").read_text()))
            self.assertEqual(hashlib.sha256((ROOT/e['src']).read_bytes()).hexdigest(), e['sha256'])
            self.assertLess(e['bytes'], 3_000_000)
            self.assertFalse(e['external_resources'])
            if 'sketchfab_uid' in e:
                pin = json.loads((ROOT/'content/visualizations/models/sources/bio3d2'/f"{e['id'][7:]}.json").read_text())
                self.assertEqual(pin['uid'], e['sketchfab_uid'])
                self.assertEqual(pin['license']['slug'], 'by')
                self.assertTrue(pin['isDownloadable'])
        # Native mm retained for the measured worker, and native um for the
        # small CT tardigrade. Never normalize either specimen's box to one.
        by_id = {e['id']: e for e in entries}
        self.assertEqual(by_id['bio3d2-honeybee']['presentation']['reference_size'], 12.5)
        self.assertEqual(by_id['bio3d2-tardigrade']['presentation']['reference_size'], 152)


if __name__ == '__main__': unittest.main()
