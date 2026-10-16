"""Scientific assembly, physical-scale and export regressions for bio3d."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import build_bio3d_models as bio
from build_graphene_spacing import lattice
from render_glb_preview import accessor, read_glb
from preview_bio3d_cpu import rotation


class BioStructureTests(unittest.TestCase):
    def test_retained_coordinate_sources_are_pinned(self):
        for pdb in {s[0] for s in bio.SPECS.values()}:
            _, meta = bio.load(pdb)
            raw = (bio.SOURCE/f'{pdb}.npz').read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), meta['retained_npz_sha256'])

    def test_fullerene_is_experimental_trivalent_cage(self):
        data, _ = bio.load('5ET3')
        _, _, _, info = bio.fullerene(data)
        self.assertEqual(info['atoms'], 60)
        self.assertEqual(info['bonds'], 90)
        self.assertAlmostEqual(info['nuclear_cage_diameter_nm'], .71, delta=.02)
        with self.assertRaises(ValueError):
            bio.fullerene(bio.subset(data, np.arange(60) != 0))

    def test_ribosome_contains_one_biological_particle(self):
        data, meta = bio.load('4V88')
        data = bio.subset(data, data['sequence'] != '.')
        one = bio.assembly(data, meta)
        self.assertEqual(len(one['xyz']), 199833)
        self.assertLess(len(one['xyz']), len(data['xyz'])/1.9)
        # Asymmetric-unit copies would exceed the approximate 30 nm marker.
        self.assertLess(np.ptp(one['xyz'], axis=0).max()/10, 30)
        self.assertGreater(np.ptp(data['xyz'], axis=0).max()/10, 40)

    def test_npc_uses_all_eight_deposited_operations(self):
        data, meta = bio.load('7R5K')
        full = bio.assembly(data, meta)
        self.assertEqual(len(full['xyz']), 8*78030)
        self.assertTrue(np.all(data['atom'] == 'CA'))
        for op in meta['operations']:
            r = bio.operation(op)[:3, :3]
            np.testing.assert_allclose(r @ r.T, np.eye(3), atol=1e-7)
            self.assertAlmostEqual(np.linalg.det(r), 1, places=6)
        # A wall wedge alone would not cover both lateral dimensions.
        self.assertGreater(np.ptp(full['xyz'], axis=0)[:2].min()/10, 140)

    def test_microtubule_transforms_are_rigid_fits_to_deposited_coordinates(self):
        data, _ = bio.load('6DPU')
        _, _, info = bio.microtubule(bio.subset(data, data['sequence'] != '.'))
        self.assertEqual(info['protofilaments'], 14)
        self.assertLess(max(info['fit_rmsd_A']), .01)
        for key in ['lateral_transform', 'longitudinal_transform']:
            r = np.array(info[key])[:3, :3]
            np.testing.assert_allclose(r @ r.T, np.eye(3), atol=1e-6)

    def test_graphite_uses_crystallographic_interplane_distance(self):
        lower, upper, a, c = lattice()
        self.assertAlmostEqual(c/20, .33555)
        self.assertAlmostEqual(float(upper[:, 1].mean()-lower[:, 1].mean()), c/2)
        distances = np.linalg.norm(lower-np.roll(lower, 1, axis=0), axis=1)
        np.testing.assert_allclose(distances, a/np.sqrt(3), atol=1e-9)
        # AB stacking translates by one bond, without rescaling either layer.
        np.testing.assert_allclose(upper-lower, np.tile([a/np.sqrt(3), c/2, 0], (6, 1)))

    def test_surface_winding_and_physical_cut_plane(self):
        v, f, _ = bio.surface(np.array([[0., 0., 0.]]), np.ones((1, 3)), .2, 2., .1, clip=1.)
        self.assertGreater(float(np.mean(np.sum(v*bio.normals(v, f), axis=1))), 1)
        self.assertAlmostEqual(float(v[:, 2].max()), 1, places=5)
        self.assertAlmostEqual(float(v[:, 2].min()), -1, places=5)

    def test_collapsed_cavity_faces_do_not_cancel_exported_normals(self):
        v = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.],
                      [0., 0., 1.], [3., 0., 0.], [3., 1., 0.]])
        f = np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3],
                      [1, 4, 5], [4, 1, 5]])
        clean_v, clean_f = bio.clean_mesh(v, f)
        self.assertEqual(clean_v.shape, (4, 3))
        self.assertEqual(clean_f.shape, (4, 3))
        np.testing.assert_allclose(np.linalg.norm(bio.normals(clean_v, clean_f), axis=1), 1)

    def test_final_exports_keep_nm_calibration_and_reasonable_rest_extent(self):
        for path in bio.HANDOFF.glob('*.entry.json'):
            entry = json.loads(path.read_text())
            if entry['id'].startswith('sketchfab-'):
                continue
            doc, blob = read_glb(ROOT/entry['src'])
            parts = []
            for mesh in doc['meshes']:
                for p in mesh['primitives']:
                    points = accessor(doc, blob, p['attributes']['POSITION'])
                    self.assertTrue(np.isfinite(points).all())
                    parts.append(points)
                    normal = accessor(doc, blob, p['attributes']['NORMAL'])
                    np.testing.assert_allclose(np.linalg.norm(normal, axis=1), 1, atol=1e-4)
            points = np.concatenate(parts)
            pose = entry['presentation']
            points = points @ rotation(pose.get('pitch', 0), pose.get('yaw', 0), pose.get('roll', 0)).T
            ratio = np.ptp(points, axis=0)[:2].max()/pose['reference_size']
            self.assertGreaterEqual(ratio, .6, entry['id'])
            self.assertLessEqual(ratio, 1.3, entry['id'])
            self.assertLess(entry['bytes'], 3_000_000)
            self.assertLessEqual(entry['triangle_count'], 60000)
            self.assertEqual(entry['processing']['coordinate_unit'], 'nm')
            self.assertFalse(set(doc.get('extensionsUsed', [])) & {
                'KHR_draco_mesh_compression', 'EXT_meshopt_compression', 'KHR_texture_basisu', 'EXT_texture_webp'})


if __name__ == '__main__':
    unittest.main()
