"""Physical invariants for the second space batch, independent of the renderer."""
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from build_space3d2_models import SOURCES, kepler_position, orbital_matrix, roche_radius


class SpaceModelPhysicsTests(unittest.TestCase):
    def test_kepler_perihelion_aphelion_and_major_axis(self):
        for body in ['halley', 'sedna']:
            data = json.loads((SOURCES/(body+'.json')).read_text())
            e = {v['name']: float(v['value']) for v in data['orbit']['elements']}
            p = kepler_position(e, np.array([0, np.pi]))
            self.assertAlmostEqual(np.linalg.norm(p[0]), e['a']*(1-e['e']), places=10)
            self.assertAlmostEqual(np.linalg.norm(p[1]), e['a']*(1+e['e']), places=10)
            self.assertAlmostEqual(np.linalg.norm(p[1]-p[0]), 2*e['a'], places=10)

    def test_orbital_frame_preserves_handedness_and_lengths(self):
        m = orbital_matrix({'om': 125., 'i': 162., 'w': 112.})
        np.testing.assert_allclose(m.T@m, np.eye(3), atol=1e-15)
        self.assertAlmostEqual(np.linalg.det(m), 1)

    def test_inclination_is_geometric_not_flattened(self):
        e = {'a': 42., 'e': 0., 'i': 30., 'om': 0., 'w': 0.}
        p = kepler_position(e, math.pi/2)
        np.testing.assert_allclose(p, [0, 42*math.cos(math.pi/6), 21], atol=1e-12)

    def test_roche_surface_matches_observed_pole_and_equator(self):
        ratio = 2.418/2.726
        t = np.array([0., np.pi/2, np.pi])
        r = roche_radius(t, ratio)
        np.testing.assert_allclose(r, [ratio, 1, ratio], atol=1e-14)

    def test_roche_surface_is_equipotential_everywhere(self):
        ratio = 2.418/2.726
        t = np.linspace(0, np.pi, 251)
        r = roche_radius(t, ratio)
        potential = 1/r + (1/ratio-1)*r*r*np.sin(t)**2
        np.testing.assert_allclose(potential, 1/ratio, atol=1e-14)

    def test_kuiper_snapshot_contains_real_unique_records_in_selection(self):
        snapshot = json.loads((SOURCES/'kuiper.json').read_text())
        self.assertEqual(len(snapshot['data']), int(snapshot['count']))
        names = set()
        for row in snapshot['data']:
            record = dict(zip(snapshot['fields'], row))
            self.assertNotIn(record['pdes'], names)
            names.add(record['pdes'])
            a, e = float(record['a']), float(record['e'])
            self.assertGreaterEqual(a, 30)
            self.assertLessEqual(a, 50)
            self.assertGreaterEqual(a*(1-e), 30-1e-9)


if __name__ == '__main__':
    unittest.main()
