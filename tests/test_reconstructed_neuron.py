from pathlib import Path
import sys
import unittest

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import build_reconstructed_neuron as neuron
from fetch_model_assets import read_glb, inspect_glb


class ReconstructedNeuronTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes, cls.soma, cls.children, cls.distance = neuron.read_source()
        cls.branches = list(neuron.branches(cls.nodes, cls.soma, cls.children, cls.distance))
        cls.data, cls.stats = neuron.build()
        cls.document, cls.binary = read_glb(cls.data)

    def test_every_source_edge_is_retained_once_without_cropping(self):
        edges = [(a, b) for _, _, _, _, path in self.branches for a, b in zip(path, path[1:])]
        expected = [(n['parent'], n['id']) for n in self.nodes.values() if n['type'] in (2, 3, 4)]
        self.assertCountEqual(edges, expected)
        self.assertEqual(len(edges), len(set(edges)))
        self.assertGreater(sum(n['type'] == 2 for n in self.nodes.values()), 1000)
        self.assertIsNone(self.stats['crop'])
        self.assertEqual(self.stats['radiusGain'], 1)

    def test_simplified_centerlines_and_radii_stay_within_error_budgets(self):
        for _, p, r, d, path in self.branches:
            original = np.array([self.nodes[key]['xyz'] for key in path])
            radius = np.array([self.nodes[key]['radius'] for key in path])
            dist = np.array([self.distance[key] for key in path])
            if self.nodes[path[0]]['type'] == 1:
                radius[0] = radius[1]
                dist[0] = -np.linalg.norm(original[1]-original[0])
            interpolated = np.stack([np.interp(dist, d, p[:, axis]) for axis in range(3)], axis=1)
            self.assertLessEqual(np.max(np.linalg.norm(original-interpolated, axis=1)),
                                 neuron.POSITION_ERROR_UM + 1e-8)
            self.assertLessEqual(np.max(np.abs(radius-np.interp(dist, d, r))),
                                 neuron.RADIUS_ERROR_UM + 1e-8)

    def test_conduction_distance_accumulates_source_tree_not_straight_line(self):
        for n in self.nodes.values():
            if n['type'] != 2:
                continue
            parent = self.nodes[n['parent']]
            expected = (self.distance[parent['id']] + np.linalg.norm(np.array(n['xyz'])-parent['xyz'])
                        if parent['type'] == 2 else 0)
            self.assertAlmostEqual(self.distance[n['id']], expected)
        self.assertGreater(self.stats['maxAxonPathUm'], 900)

    def test_tube_surface_keeps_radii_and_outward_smooth_normals(self):
        points = np.array([[0, 0, 0], [0, 0, 5], [0, 1, 10]], float)
        radii = np.array([2, 1, .5])
        p, n, indices, distance, centers, _ = neuron.tube(points, radii, np.array([0, 5, 10]))
        offsets = p.reshape(-1, neuron.SIDES, 3)-centers[:, None, :]
        np.testing.assert_allclose(np.linalg.norm(offsets, axis=2),
                                   np.broadcast_to(radii[:, None], (3, neuron.SIDES)), atol=1e-8)
        np.testing.assert_allclose(np.linalg.norm(n, axis=1), 1, atol=1e-8)
        face = indices.reshape(-1, 3)[0]
        cross = np.cross(p[face[1]]-p[face[0]], p[face[2]]-p[face[0]])
        self.assertGreater(np.dot(cross, n[face].mean(axis=0)), 0)

    def test_gltf_is_self_contained_bounded_and_carries_clone_safe_pulse_data(self):
        audit = inspect_glb(self.data)
        self.assertLess(audit['bytes'], 3_000_000)
        self.assertEqual(audit['external_resources'], [])
        root = self.document['nodes'][self.document['scenes'][0]['nodes'][0]]
        self.assertEqual(root['extras']['animation']['kind'], 'reconstructed-neuron')
        axon = next(m for m in self.document['meshes'] if m['name'] == 'Axon')
        self.assertIn('_PATH_DISTANCE', axon['primitives'][0]['attributes'])
        halo = next(m for m in self.document['meshes'] if m['name'] == 'Axon electrical glow')
        material = self.document['materials'][halo['primitives'][0]['material']]
        self.assertEqual(material['pbrMetallicRoughness']['baseColorFactor'][3], 0)
        self.assertEqual(neuron.entry(self.data, self.stats)['license'], 'CC-BY-4.0')


if __name__ == '__main__':
    unittest.main()
