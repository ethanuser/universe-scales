"""Independent physical and archival invariants for the space3d3 batch."""
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_space3d3_models import SOURCES, C, LY_KM, PARAMS, rotating_webb_vectors
from fetch_model_assets import read_glb, sha
from preview_space3d3_cpu import read_scene


class Space3D3PhysicsTests(unittest.TestCase):
    def test_light_year_is_exact_julian_definition(self):
        self.assertEqual(int(LY_KM*1000),9460730472580800)
        self.assertEqual(C['day_s']*C['julian_year_days'],31557600)

    def test_archive_checksums(self):
        for record in json.loads((SOURCES/'manifest.json').read_text())['sources']:
            with self.subTest(file=record['file']):
                self.assertEqual(sha((SOURCES/record['file']).read_bytes()),record['sha256'])

    def test_webb_rotation_preserves_all_measured_ranges(self):
        original=np.array(json.loads((SOURCES/'webb-vectors.json').read_text())['xyz_km'])
        rotated=rotating_webb_vectors()
        np.testing.assert_allclose(np.linalg.norm(rotated,axis=1),np.linalg.norm(original,axis=1),rtol=1e-14)
        self.assertEqual(len(rotated),184)
        self.assertGreater(np.ptp(rotated[:,1]),600000)
        self.assertGreater(np.ptp(rotated[:,2]),1400000)
        # A real halo trajectory stays antisolar; it is never centered on Earth.
        self.assertTrue(np.all(rotated[:,0]>1000000))

    def test_webb_is_not_a_fabricated_closed_ellipse(self):
        p=rotating_webb_vectors()
        self.assertGreater(np.linalg.norm(p[-1]-p[0]),1000)
        d=json.loads((SOURCES/'webb-vectors.json').read_text())
        self.assertEqual(d['jd_tdb'][0],2460310.5)
        self.assertEqual(d['jd_tdb'][-1],2460676.5)

    def test_radcliffe_clouds_remain_isotropic_in_final_asset(self):
        source=json.loads((SOURCES/'radcliffe-clouds.json').read_text())['clouds']
        observed=np.array([c['xyz_pc'] for c in source])
        self.assertEqual(len(observed),141)
        e=json.loads((ROOT/'handoff/space3d3/space3d3-radcliffe-clouds.entry.json').read_text())
        matrix=np.array(e['processing']['view_matrix_rows'])
        np.testing.assert_allclose(matrix@matrix.T,np.eye(3),atol=1e-14)
        self.assertAlmostEqual(np.linalg.det(matrix),1)
        primitives,_=read_scene((ROOT/e['src']).read_bytes())
        p=next(q['p'] for q in primitives if q['mode']==0)
        np.testing.assert_allclose(p,observed@matrix.T,atol=1e-4)
        # No authored vertical exaggeration or invented dense cloud samples.
        self.assertEqual(len(p),141)
        self.assertEqual(np.ptp(p[:,1]),np.ptp(observed[:,2]))

    def test_altitude_is_not_center_distance(self):
        e=json.loads((ROOT/'handoff/space3d3/space3d3-geostationary-altitude.entry.json').read_text())
        p=e['processing']
        self.assertEqual(p['altitude_km'],35786)
        self.assertAlmostEqual(p['center_to_orbit_km']-p['earth_equatorial_radius_km'],35786)
        self.assertAlmostEqual(p['center_to_orbit_km'],42164.137)

    def test_alpha_ellipse_uses_angular_orbit_and_parallax(self):
        e=json.loads((ROOT/'handoff/space3d3/space3d3-alpha-cen-relative-orbit.entry.json').read_text())
        p=e['processing']
        self.assertAlmostEqual(p['physical_a_au'],17.66/.743)
        self.assertAlmostEqual(p['periastron_separation_au']+p['apastron_separation_au'],2*p['physical_a_au'])
        self.assertAlmostEqual(p['apastron_separation_au']/p['periastron_separation_au'],(1+.524)/(1-.524))

    def test_final_glbs_match_entries_and_neptune_dataset_gate_is_safe(self):
        registry={m['id']:m for m in json.loads((ROOT/'content/visualizations/models.json').read_text())['models']}
        entries=list((ROOT/'handoff/space3d3').glob('*.entry.json'))
        self.assertEqual(len(entries),15)
        for path in entries:
            e=json.loads(path.read_text());data=(ROOT/e['src']).read_bytes()
            with self.subTest(model=e['id']):
                self.assertEqual(sha(data),e['sha256'])
                self.assertLess(len(data),3000000)
                doc,_=read_glb(data)
                self.assertFalse(set(doc.get('extensionsRequired',[])) & {'KHR_draco_mesh_compression','EXT_meshopt_compression','KHR_texture_basisu'})
                self.assertNotIn('display_label',e)
                if e.get('requires_dataset'):
                    self.assertEqual(e['requires_dataset']['value_m'],4514953000000)
                    items=yaml.safe_load((ROOT/'dataset/raw/legacy_yaml/length.yaml').read_text())['items']
                    actual=float(next(i['value'] for i in items if i['name']=='Sun-Neptune Distance'))
                    if actual!=4514953000000:
                        self.assertNotIn(e['id'],registry)
                    elif e['id'] in registry:
                        self.assertEqual(registry[e['id']]['sha256'],e['sha256'])
                else:
                    self.assertEqual(registry[e['id']]['sha256'],e['sha256'])


if __name__=='__main__': unittest.main()
