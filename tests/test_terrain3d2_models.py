"""Scientific-data integrity: metric calibration, source selections, no invented volume."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_terrain3d2_models import CONFIG, REGISTERED, SOURCE
from build_terrain3d_models import frame
from fetch_model_assets import inspect_glb
from render_glb_preview import accessor, read_glb


class Terrain3D2Models(unittest.TestCase):
    def entry(self,name):
        return json.loads((ROOT/f'handoff/terrain3d2/terrain3d2-{name}.entry.json').read_text())

    def test_pinned_inputs_and_registered_assets_have_verified_hashes_and_no_decoders(self):
        registry={e['id']:e for e in json.loads((ROOT/'content/visualizations/models.json').read_text())['models']}
        for name in REGISTERED:
            with self.subTest(name=name):
                meta=json.loads((SOURCE/name/'provenance.json').read_text())
                self.assertTrue(meta['sources'])
                for filename,sha in meta['files'].items():
                    self.assertEqual(hashlib.sha256((SOURCE/name/filename).read_bytes()).hexdigest(),sha)
                e=self.entry(name);stats=inspect_glb((ROOT/e['src']).read_bytes())
                self.assertEqual(stats['sha256'],e['sha256'])
                self.assertEqual(e,registry[e['id']])
                self.assertLess(stats['bytes'],3_000_000)
                self.assertLess(stats['triangle_count'],60_000)
                self.assertEqual(stats['external_resources'],[])
                self.assertEqual(stats['decompression_required'],[])
                self.assertNotIn('display_label',e)

    def test_terrain_contains_only_source_vertices_without_blocks_walls_or_rulers(self):
        for name in REGISTERED:
            c=CONFIG[name]
            with self.subTest(name=name):
                with np.load(SOURCE/name/'data.npz') as a:
                    p=frame(c,a['lonlat'],a['heights'].astype(float)*c['gain'])
                    if name=='appalachian-trail':p=p[::2,::2]
                doc,binary=read_glb(ROOT/self.entry(name)['src'])
                q=doc['meshes'][0]['primitives'][0]
                actual=accessor(doc,binary,q['attributes']['POSITION'])
                np.testing.assert_array_equal(actual,p.reshape(-1,3).astype(np.float32))
                self.assertEqual(len(doc['meshes']),1)
                self.assertFalse(any('screenLine' in n.get('extras',{}) for n in doc['nodes']))
                normals=accessor(doc,binary,q['attributes']['NORMAL'])
                np.testing.assert_allclose(np.linalg.norm(normals,axis=1),1,atol=2e-7)

    def test_vector_data_are_identified_original_features(self):
        trail=json.loads(gzip.decompress((SOURCE/'appalachian-trail/vectors.geojson.gz').read_bytes()))
        self.assertEqual(len(trail['features']),30)
        self.assertEqual(len({f['properties']['OBJECTID'] for f in trail['features']}),30)
        self.assertTrue(all(f['properties']['Version']=='June 2023' for f in trail['features']))
        damage=json.loads(gzip.decompress((SOURCE/'el-reno/vectors.geojson.gz').read_bytes()))
        self.assertEqual(len(damage['features']),1)
        self.assertEqual(damage['features'][0]['properties']['event_id'],'ElReno_Poly')
        self.assertEqual(damage['features'][0]['geometry']['type'],'Polygon')
        # The complete source is retained even though the display crops its path.
        ring=np.array(damage['features'][0]['geometry']['coordinates'][0])
        self.assertLess(ring[:,0].min(),-98.09)
        self.assertGreater(ring[:,0].max(),-97.85)

    def test_gravity_vertical_axis_plots_anomaly_and_never_claims_crater_relief(self):
        with np.load(SOURCE/'chicxulub/data.npz') as a:
            np.testing.assert_allclose(a['heights'],a['anomaly_mgal']*500,rtol=1e-7)
            self.assertLess(a['anomaly_mgal'].min(),0)
            self.assertGreater(a['anomaly_mgal'].max(),0)
        self.assertIn('500 display metres per mGal',self.entry('chicxulub')['note'])
        self.assertIn('not elevation',self.entry('chicxulub')['note'])


if __name__=='__main__':unittest.main()
