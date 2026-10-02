import importlib.util
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest

from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("build_observable_universe_model",
                                              SCRIPTS / "build_observable_universe_model.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
from fetch_model_assets import inspect_glb, read_glb  # noqa: E402


def fits_card(key, value):
    return f"{key:<8}= {value:>20}".ljust(80).encode("ascii")


def fits_header(cards):
    data = b"".join(cards + [b"END".ljust(80, b" ")])
    return data.ljust(((len(data) + 2879) // 2880) * 2880, b" ")


def tiny_fits(path, nside=1, ordering="NESTED"):
    npix = 12 * nside * nside
    primary = fits_header([fits_card("SIMPLE", "T"), fits_card("BITPIX", "8"),
                           fits_card("NAXIS", "0"), fits_card("EXTEND", "T"),
                           fits_card("TELESCOP", "'WMAP'"), fits_card("OBJECT", "'ALL-SKY'")])
    table = fits_header([fits_card("XTENSION", "'BINTABLE'"), fits_card("BITPIX", "8"),
                         fits_card("NAXIS", "2"), fits_card("NAXIS1", "8"),
                         fits_card("NAXIS2", str(npix)), fits_card("PCOUNT", "0"),
                         fits_card("GCOUNT", "1"), fits_card("TFIELDS", "2"),
                         fits_card("TTYPE1", "'TEMPERATURE'"), fits_card("TFORM1", "'E'"),
                         fits_card("TUNIT1", "'mK, thermodynamic'"),
                         fits_card("TTYPE2", "'N_OBS'"), fits_card("TFORM2", "'E'"),
                         fits_card("PIXTYPE", "'HEALPIX'"), fits_card("ORDERING", f"'{ordering}'"),
                         fits_card("COORDSYS", "'G'"),
                         fits_card("NSIDE", str(nside))])
    rows = b"".join(struct.pack(">ff", float(i - npix // 2), 1.0) for i in range(npix))
    path.write_bytes(primary + table + rows.ljust(((len(rows) + 2879) // 2880) * 2880, b"\0"))


class ObservableUniverseModelTests(unittest.TestCase):
    def test_ang2pix_cardinal_pixels_and_range(self):
        # Published HEALPix base-face centers: four polar, four equatorial,
        # and four southern faces in NESTED order (Nside=1).
        centers = []
        centers.extend((math.acos(2 / 3), (face + 0.5) * math.pi / 2) for face in range(4))
        centers.extend((math.pi / 2, face * math.pi / 2) for face in range(4))
        centers.extend((math.acos(-2 / 3), (face + 0.5) * math.pi / 2) for face in range(4))
        self.assertEqual([builder.ang2pix_nest(1, theta, phi) for theta, phi in centers],
                         list(range(12)))
        for nside in (1, 2, 4, 64):
            for theta in (0, 0.2, 1.0, 1.5707963267948966, 2.4, 3.141592653589793):
                for phi in (0, 0.5, 1.57, 3.14, 4.71, 6.28):
                    pixel = builder.ang2pix_nest(nside, theta, phi)
                    self.assertGreaterEqual(pixel, 0)
                    self.assertLess(pixel, 12 * nside * nside)

    def test_nested_downsample_averages_contiguous_children(self):
        constant = [3.25] * (12 * 4 * 4)
        self.assertEqual(builder.downsample_nested(4, constant, 2), [3.25] * 48)
        values = list(range(12 * 4 * 4))
        result = builder.downsample_nested(4, values, 2)
        self.assertEqual(result[:4], [1.5, 5.5, 9.5, 13.5])
        self.assertEqual(result[4], 17.5)
        with self.assertRaisesRegex(ValueError, "divide"):
            builder.downsample_nested(4, values, 8)

    def test_reads_only_validated_nested_thermodynamic_fits(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.fits"
            tiny_fits(path)
            nside, values, digest = builder.read_healpix_fits(path)
            self.assertEqual(nside, 1)
            self.assertEqual(values, [-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5])
            self.assertEqual(len(digest), 64)
            tiny_fits(path, ordering="RING")
            with self.assertRaisesRegex(ValueError, "NESTED"):
                builder.read_healpix_fits(path)
            tiny_fits(path)
            data = path.read_bytes().replace(b"COORDSYS=                  'G'", b"COORDSYS=                  'C'", 1)
            path.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "Galactic"):
                builder.read_healpix_fits(path)
            tiny_fits(path)
            data = bytearray(path.read_bytes())
            struct.pack_into(">f", data, 5760, -1.6375e30)
            path.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "UNSEEN"):
                builder.read_healpix_fits(path)
            path.write_bytes(b"short")
            with self.assertRaisesRegex(ValueError, "truncated"):
                builder.read_healpix_fits(path)

    def test_texture_has_equirectangular_dimensions_and_colors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.jpg"
            digest = builder.make_texture(1, [0.0] * 12, path, width=32, height=16)
            with Image.open(path) as image:
                self.assertEqual(image.size, (32, 16))
            self.assertEqual(len(digest), 64)
            self.assertEqual(builder.temperature_color(-1), (18, 63, 150))
            self.assertEqual(builder.temperature_color(1), (240, 55, 25))

    def test_glb_bounds_cutaway_proportions_and_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "texture.jpg"
            Image.new("RGB", (64, 32), (100, 120, 150)).save(path, "JPEG")
            data, vertices, triangles = builder.build(path.read_bytes(), segments=32, rings=16)
        stats = inspect_glb(data)
        self.assertLess(stats["bytes"], 1_000_000)
        self.assertLessEqual(stats["triangle_count"], 10_000)
        self.assertEqual(stats["triangle_count"], triangles)
        self.assertEqual(stats["external_resources"], [])
        self.assertEqual(stats["extensions_required"], [])
        self.assertEqual(vertices, 3 * (2 * 16 - 1) * 32)
        document, _ = read_glb(data)
        shell = document["meshes"][0]["primitives"][0]
        positions = document["accessors"][shell["attributes"]["POSITION"]]
        self.assertAlmostEqual(max(abs(x) for x in positions["max"] + positions["min"]) / builder.CMB_RADIUS_LY,
                               1, delta=0.005)
        raw = read_glb(data)[1]
        view = document["bufferViews"][positions["bufferView"]]
        start = view.get("byteOffset", 0) + positions.get("byteOffset", 0)
        shell_positions = [struct.unpack_from("<3f", raw, start + 12 * i)
                           for i in range(positions["count"])]
        directions = [(x / builder.CMB_RADIUS_LY, y / builder.CMB_RADIUS_LY,
                       z / builder.CMB_RADIUS_LY) for x, y, z in shell_positions]
        self.assertAlmostEqual(min(y for _, y, _ in directions), -1, delta=0.005)
        self.assertAlmostEqual(max(y for _, y, _ in directions), 1, delta=0.005)
        index_accessor = document["accessors"][shell["indices"]]
        index_view = document["bufferViews"][index_accessor["bufferView"]]
        index_start = index_view.get("byteOffset", 0) + index_accessor.get("byteOffset", 0)
        indices = struct.unpack_from("<" + "I" * index_accessor["count"], raw, index_start)
        centroids = []
        for offset in range(0, len(indices), 3):
            pts = [shell_positions[index] for index in indices[offset:offset + 3]]
            center = [sum(point[axis] for point in pts) / 3 for axis in range(3)]
            length = sum(value * value for value in center) ** 0.5
            centroids.append(center[2] / length)
        self.assertFalse(any(z > math.cos(math.radians(30)) + 1e-4 for z in centroids),
                         "the +Z observer-facing cutaway must omit triangles in its cone")
        self.assertLess(triangles, 2 * 32 * 16, "the opening must remove shell triangles")
        horizon = document["meshes"][1]["primitives"][0]
        self.assertEqual(horizon["mode"], 1)
        hpos = document["accessors"][horizon["attributes"]["POSITION"]]
        hview = document["bufferViews"][hpos["bufferView"]]
        hstart = hview.get("byteOffset", 0) + hpos.get("byteOffset", 0)
        horizon_points = [struct.unpack_from("<3f", raw, hstart + 12 * i)
                          for i in range(hpos["count"])]
        self.assertTrue(all(abs(sum(v * v for v in point) ** 0.5 - builder.HORIZON_RADIUS_LY) < 1e5
                            for point in horizon_points))
        self.assertAlmostEqual(builder.HORIZON_RADIUS_LY / builder.CMB_RADIUS_LY, 1.0199, delta=0.0001)
        self.assertAlmostEqual(builder.REFERENCE_SIZE_LY,
                               8.8e26 / builder.LY_M, places=3)
        label_nodes = {node["name"]: node for node in document["nodes"] if "translation" in node}
        cmb_label = label_nodes["CMB boundary label"]
        horizon_label = label_nodes["Particle horizon label"]
        self.assertNotIn("mesh", cmb_label)
        self.assertAlmostEqual(sum(x * x for x in cmb_label["translation"]) ** 0.5 / builder.CMB_RADIUS_LY, 1)
        self.assertAlmostEqual(sum(x * x for x in horizon_label["translation"]) ** 0.5 / builder.HORIZON_RADIUS_LY, 1)
        self.assertLess(horizon_label["translation"][0], 0)
        self.assertNotEqual(cmb_label["translation"], horizon_label["translation"])
        for accessor in document["accessors"]:
            view = document["bufferViews"][accessor["bufferView"]]
            self.assertEqual((view.get("byteOffset", 0) + accessor.get("byteOffset", 0)) % 4, 0)
        self.assertEqual(document["images"][0]["mimeType"], "image/jpeg")
        self.assertNotIn("uri", document["images"][0])
        self.assertFalse(document["materials"][0]["doubleSided"])

    def test_cutaway_rim_and_galactic_uv_reprojection(self):
        import math
        positions, uv, indices = builder.shell_geometry(32, 16, 30)
        for (x, y, z), (u, v) in zip(positions, uv):
            self.assertAlmostEqual((u % 1), (math.atan2(z, x) / (2 * math.pi)) % 1)
            self.assertAlmostEqual(v, 0.5 - math.asin(max(-1, min(1, y / builder.CMB_RADIUS_LY))) / math.pi)
            self.assertLessEqual(z / builder.CMB_RADIUS_LY, math.cos(math.radians(30)) + 1e-6)
        for offset in range(0, len(indices), 3):
            a, b, c = (positions[i] for i in indices[offset:offset + 3])
            ab, ac = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
            normal = [ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2],
                      ab[0] * ac[1] - ab[1] * ac[0]]
            self.assertGreater(sum(normal[i] * a[i] for i in range(3)), 0, "front faces point outward")

    def test_cli_build_with_staged_map(self):
        staged = builder.DEFAULT_FITS
        if not staged.is_file():
            self.skipTest("staged NASA WMAP FITS is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            nside, values, _ = builder.read_healpix_fits(staged)
            self.assertEqual(nside, 512)
            reduced = builder.downsample_nested(nside, values)
            self.assertEqual(len(reduced), 49152)


if __name__ == "__main__":
    unittest.main()
