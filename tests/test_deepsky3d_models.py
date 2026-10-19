"""Physical-coordinate and source-identity checks for public-catalog models."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_deepsky3d_models as sky
from render_glb_preview import read_glb, accessor


class DeepskyCatalogTests(unittest.TestCase):
    def test_sky_frame_preserves_distances_and_handedness(self):
        for ra,dec in [(0,0),(180,20),(81.28,-69.78),(201.69699,-47.47947)]:
            f=sky.sky_frame(ra,dec)
            np.testing.assert_allclose(f@f.T,np.eye(3),atol=1e-14)
            self.assertAlmostEqual(np.linalg.det(f),1)
            np.testing.assert_allclose(sky.unit_vectors([ra],[dec])@f.T,[[0,0,1]],atol=1e-14)

    def test_lmc_is_published_plane_with_near_side_and_absolute_distance(self):
        p=sky.lmc_disk(np.array([81.28,82.28,80.28]),np.array([-69.78,-68.78,-70.78]))
        np.testing.assert_allclose(p[0],[0,0,0],atol=1e-12)
        self.assertGreater(p[1,2],0) # northeast closer, +z toward observer
        self.assertLess(p[2,2],0)
        inc,theta=np.radians([34.7,122.5])
        n=[-np.sin(inc)*np.cos(theta),-np.sin(inc)*np.sin(theta),np.cos(inc)]
        np.testing.assert_allclose(p@np.array(n),0,atol=1e-12)
        # Independent central-angle ray/plane intersection: the line of nodes
        # remains at D0 along its sightline, rather than normalizing a bbox.
        small=sky.lmc_disk(np.array([81.28001]),np.array([-69.78]))[0]
        self.assertAlmostEqual(small[0],-49.59*np.cos(np.radians(-69.78))*np.radians(.00001),places=10)

    def test_omega_plane_has_no_invented_depth(self):
        p=sky.sky_plane(np.array([0.,1.]),np.array([0.,0.]),0,0,5430)
        self.assertEqual(p[1,2],0)
        self.assertAlmostEqual(p[1,0],-5430*np.tan(np.radians(1)))
        rows=sky.read_rows("gaia-edr3-omega-members.csv.gz")
        self.assertTrue(all(float(r["memberprob"])>.99 for r in rows))
        self.assertTrue(all(np.isfinite(float(r["bp_rp"])) for r in rows))

    def test_cosmological_distance_matches_independent_gauss_quadrature(self):
        x,w=np.polynomial.legendre.leggauss(64)
        for z in [.05,.475,.8]:
            integral=z/2*np.sum(w/np.sqrt(.27*(1+(x+1)*z/2)**3+.73))
            self.assertAlmostEqual(float(sky.comoving_mpc([z])[0]),299792.458/70*integral,places=5)

    def test_pinned_hashes_counts_and_integer_identities(self):
        m=json.loads((sky.SOURCES/"manifest.json").read_text())
        for name,info in m["files"].items():
            data=(sky.SOURCES/name).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),info["sha256"])
            if name.endswith(".npz"):
                continue
            rows=sky.read_rows(name)
            self.assertEqual(len(rows),info["rows"])
            key="source_id" if "source_id" in rows[0] else "specObjID" if "specObjID" in rows[0] else "row"
            self.assertEqual(len({r[key] for r in rows}),len(rows))
            self.assertTrue(all(r[key].isdigit() for r in rows))

    def test_final_glbs_contain_exactly_selected_catalog_positions(self):
        expected={"orionarm":15707,"lmc":23420,"omega":7313,"localvoid":471,"bootes":1343,"bao":141}
        for kind,cfg in sky.CONFIG.items():
            with self.subTest(kind=kind):
                p,color,alpha,ids=sky.catalog_geometry(kind)
                self.assertEqual(len(p),expected[kind])
                order=sorted(range(len(ids)),key=lambda i:hashlib.sha256(ids[i].encode()).digest())
                d,b=read_glb(sky.MODELS/(cfg["id"]+".glb"))
                self.assertEqual(len(d["nodes"]),1)
                self.assertEqual(len(d["meshes"]),1)
                prim=d["meshes"][0]["primitives"][0]
                self.assertEqual(prim["mode"],0)
                self.assertNotIn("indices",prim)
                actual=accessor(d,b,prim["attributes"]["POSITION"])
                np.testing.assert_array_equal(actual,p[order].astype(np.float32))
                self.assertNotIn("uri",d["buffers"][0])
                self.assertNotIn("images",d)
                self.assertLess((sky.MODELS/(cfg["id"]+".glb")).stat().st_size,3_000_000)
                ratio=max(np.ptp(actual,axis=0)[:2])/cfg["reference"]
                self.assertGreaterEqual(ratio,.6)
                self.assertLessEqual(ratio,1.3)

    def test_omega_bright_cut_and_no_quality_based_density_hole(self):
        _,_,_,ids=sky.catalog_geometry("omega")
        source={r["source_id"]:r for r in sky.read_rows("gaia-edr3-omega-members.csv.gz")}
        self.assertTrue(all(float(source[i]["g_mag"])<16 for i in ids))
        self.assertTrue(any(int(source[i]["qflag"])&2==0 for i in ids))

    def test_boss_and_void_windows_preserve_physical_scale(self):
        for kind,width,depth in [("bao",150,40),("bootes",150,40),("localvoid",60,20)]:
            p,_,_,_=sky.catalog_geometry(kind)
            self.assertLessEqual(np.max(np.abs(p[:,:2])),width/2)
            self.assertLessEqual(np.max(np.abs(p[:,2])),depth/2)
        self.assertEqual(sky.CONFIG["bootes"]["reference"],124)
        self.assertEqual(sky.CONFIG["bao"]["reference"],150)

    def test_dust_samples_keep_measured_cartesian_grid_and_missing_data(self):
        with np.load(sky.SOURCES/"edenhofer-local-dust.npz") as data:
            density=data["density"];coord=data["coordinates_pc"]
        self.assertEqual(density.shape,(68,68,68))
        np.testing.assert_array_equal(coord,np.arange(-536,537,16))
        self.assertEqual(np.count_nonzero(~np.isfinite(density)),304)
        p,_,_,ids=sky.catalog_geometry("orionarm")
        threshold=np.nanquantile(density,.95)
        for pos,identity in zip(p,ids):
            z,y,x=map(int,identity.split(":"))
            np.testing.assert_array_equal(pos,[coord[x],coord[y],coord[z]])
            self.assertGreaterEqual(density[z,y,x],threshold)
        meta=json.loads((sky.SOURCES/"manifest.json").read_text())["files"]["edenhofer-local-dust.npz"]
        self.assertEqual(len(meta["ranges"]),68)
        self.assertEqual(meta["fits_mean_header"]["CDELT1"],2)


if __name__=="__main__":unittest.main()
