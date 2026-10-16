"""Scientific-coordinate, source-integrity and rendering-budget regressions."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_terrain3d_models import CONFIG, SOURCE, drape, frame, simplify_line
from fetch_model_assets import inspect_glb
from render_earth3d_previews import accessor, parts
from render_glb_preview import read_glb


class Terrain3DModels(unittest.TestCase):
    def entry(self,name):
        return json.loads((ROOT/f'handoff/terrain3d/terrain3d-{name}.entry.json').read_text())

    def test_assets_remain_small_self_contained_registered_and_at_catalog_scale(self):
        registry={e['id']:e for e in json.loads((ROOT/'content/visualizations/models.json').read_text())['models']}
        for name in CONFIG:
            with self.subTest(name=name):
                e=self.entry(name);s=inspect_glb((ROOT/e['src']).read_bytes())
                self.assertEqual(s['sha256'],e['sha256']);self.assertEqual(registry[e['id']],e)
                self.assertLess(s['bytes'],3_000_000)
                self.assertLess(s['triangle_count'],60_000)
                self.assertEqual(s['external_resources'],[]);self.assertEqual(s['decompression_required'],[])
                self.assertNotIn('display_label',e)
                scene,_=parts(ROOT/e['src'],e['presentation'])
                p=np.concatenate([q['pos'] for q in scene]);extent=np.ptp(p,axis=0)
                self.assertTrue(np.isfinite(p).all())
                self.assertGreaterEqual(max(extent[:2]),.6);self.assertLessEqual(max(extent[:2]),1.3)
                self.assertLessEqual(extent[0],e['presentation']['layout_width_factor'])

    def test_every_terrain_vertex_preserves_pinned_geographic_coordinates_and_relief(self):
        for name,c in CONFIG.items():
            with self.subTest(name=name):
                with np.load(SOURCE/name/'terrain.npz') as data:h=data['heights'];ll=data['lonlat']
                step=c['mesh_step']
                expected=frame(c,ll,h.astype(float)*c['gain'])[::step,::step].reshape(-1,3).astype(np.float32)
                doc,binary=read_glb(ROOT/self.entry(name)['src'])
                prim=doc['meshes'][0]['primitives'][0]
                p=accessor(doc,binary,prim['attributes']['POSITION'])
                np.testing.assert_array_equal(p,expected)
                n=accessor(doc,binary,prim['attributes']['NORMAL']);f=accessor(doc,binary,prim['indices']).reshape(-1,3)
                geometric=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
                # Curved-grid east/south triangles and smoothed vertex normals face up.
                # On very steep relief, a centered derivative need not face along every facet.
                self.assertGreater(geometric[:,1].min(),0)
                self.assertGreater(n[:,1].min(),0)
                np.testing.assert_allclose(np.linalg.norm(n,axis=1),1,atol=2e-7)

    def test_pinned_grids_vectors_and_license_snapshots_match_provenance(self):
        for name in CONFIG:
            meta=json.loads((SOURCE/name/'provenance.json').read_text())
            for filename,sha in meta['files'].items():
                with self.subTest(name=name,file=filename):
                    self.assertEqual(hashlib.sha256((SOURCE/name/filename).read_bytes()).hexdigest(),sha)
            if not CONFIG[name].get('direct_usgs'):self.assertTrue(meta['tiles'])
            else:self.assertTrue(any('3DEPElevation' in r['url'] for r in meta['vector_sources']))
            self.assertTrue(all(t['url'].startswith('https://elevation-tiles-prod.s3.amazonaws.com/terrarium/') for t in meta['tiles']))
        rights=json.loads((SOURCE/'great-barrier-reef/reef-license.json').read_text())
        self.assertIn('creativecommons.org/licenses/by/4.0/',rights['licenseInfo'])

    def test_ocean_is_signed_noaa_bathymetry_and_surface_is_sea_level(self):
        with np.load(SOURCE/'gibraltar/terrain.npz') as data:self.assertLess(data['heights'].min(),-500)
        meta=json.loads((SOURCE/'gibraltar/provenance.json').read_text())
        self.assertTrue(any('ETOPO1_ice_surface' in r['url'] for r in meta['vector_sources']))
        doc,binary=read_glb(ROOT/self.entry('gibraltar')['src'])
        water=next(m for m in doc['meshes'] if m['name']=='Sea level')
        prim=water['primitives'][0];p=accessor(doc,binary,prim['attributes']['POSITION'])
        np.testing.assert_array_equal(p[:,1],np.zeros(len(p)))
        mat=doc['materials'][prim['material']]
        self.assertEqual(mat['alphaMode'],'BLEND');self.assertLess(mat['pbrMetallicRoughness']['baseColorFactor'][3],1)

    def test_fault_and_reef_selections_are_identified_separate_source_features(self):
        for name,kind,min_count in [('san-andreas','faults',8000),('great-barrier-reef','reefs',3000)]:
            d=json.loads(gzip.decompress((SOURCE/name/'vectors.geojson.gz').read_bytes()))
            selected=[f for f in d['features'] if f['properties']['kind']==kind]
            self.assertGreater(len(selected),min_count)
            if kind=='faults':
                self.assertTrue(all('San Andreas' in f['properties']['fault_name'] for f in selected))
                self.assertTrue(all(f['properties']['fault_id'] and f['properties']['section_name'] for f in selected))
                self.assertTrue(all(len(f['geometry']['coordinates'])>=2 for f in selected))
            else:
                ids=[f['id'] for f in selected];self.assertEqual(len(ids),len(set(ids)))
                self.assertTrue(all(f['properties']['FEAT_NAME']=='Reef' for f in selected))

    def test_path_drape_uses_visible_triangles_and_simplification_retains_endpoints(self):
        ll=np.array([[[0,1],[1,1]],[[0,0],[1,0]]],float)
        surface=np.array([[[0,0,0],[1,0,0]],[[0,0,1],[1,10,1]]],float)
        # Bilinear interpolation would produce 2.5 at the center, above the real diagonal.
        q=drape(np.array([[.5,.5],[.75,.25]]),ll,surface)
        np.testing.assert_allclose(q[:,1],[0,5])
        p=np.array([[0,0],[1,.01],[2,0],[2,2],[3,2]],float)
        reduced=simplify_line(p,.05)
        np.testing.assert_array_equal(reduced,p[[0,2,3,4]])
        np.testing.assert_array_equal(reduced[[0,-1]],p[[0,-1]])


if __name__=='__main__':unittest.main()
