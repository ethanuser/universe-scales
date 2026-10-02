import json
from pathlib import Path
import sys
import unittest
import zipfile
from io import BytesIO
from unittest.mock import patch

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_laniakea_watershed as watershed
from fetch_model_assets import inspect_glb


def fits_bytes(array):
    z, y, x = array.shape
    cards = [
        "SIMPLE  =                    T",
        "BITPIX  =                  -64",
        "NAXIS   =                    3",
        f"NAXIS1  = {x:20d}",
        f"NAXIS2  = {y:20d}",
        f"NAXIS3  = {z:20d}",
        "END",
    ]
    header = "".join(card.ljust(80) for card in cards).encode("ascii")
    header += b" " * ((2880 - len(header) % 2880) % 2880)
    payload = np.asarray(array, dtype=">f8").tobytes()
    return header + payload + b"\0" * ((-len(payload)) % 2880)


class LaniakeaWatershedTests(unittest.TestCase):
    def test_reads_fits_axes_and_padding_without_treating_padding_as_data(self):
        array = np.zeros((5, 4, 3))
        array[2, 1, 1] = 1
        result, header, header_size = watershed.read_primary_fits(fits_bytes(array))
        self.assertEqual(result.shape, array.shape)
        self.assertEqual(header_size, 2880)
        self.assertEqual(header["NAXIS1"], 3)
        np.testing.assert_array_equal(result, array)

    def test_rejects_nonzero_fits_padding(self):
        encoded = bytearray(fits_bytes(np.zeros((1, 1, 1))))
        encoded[-1] = 1
        with self.assertRaisesRegex(ValueError, "padding"):
            watershed.read_primary_fits(bytes(encoded))

    def test_diagonal_voxel_contacts_remain_separate_closed_outward_surfaces(self):
        mask = np.zeros((6, 6, 6), dtype=bool)
        mask[1:3, 1:3, 1:3] = True
        mask[3:5, 3:5, 3:5] = True
        vertices, faces, components = watershed.component_surface(mask, 1.0)
        self.assertEqual(components, 2)
        edges = np.sort(np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]])), axis=1)
        _, uses = np.unique(edges, axis=0, return_counts=True)
        np.testing.assert_array_equal(uses, 2)
        signed_volume = np.einsum(
            "ij,ij->i", vertices[faces[:, 0]],
            np.cross(vertices[faces[:, 1]], vertices[faces[:, 2]]),
        ).sum() / 6
        self.assertGreater(signed_volume, 0)
        normals = watershed.vertex_normals(vertices, faces)
        self.assertTrue(np.isfinite(normals).all())

    def test_stage_entry_preserves_native_mpc_scale_and_rights_caveat(self):
        grid = np.zeros((8, 8, 8), dtype=float)
        grid[2:5, 2:5, 2:5] = 1
        archive_buffer = BytesIO()
        with zipfile.ZipFile(archive_buffer, "w") as archive:
            archive.writestr(watershed.MEMBER, fits_bytes(grid))
        with patch.object(watershed, "GRID_SIZE", 8):
            glb, entry = watershed.create_model(archive_buffer.getvalue())
        stats = inspect_glb(glb)
        self.assertEqual(entry["processing"]["watershed_voxel_count"], 27)
        self.assertAlmostEqual(entry["processing"]["voxel_volume_mpc_h3"], 27 * (1000 / 8) ** 3)
        self.assertAlmostEqual(entry["presentation"]["reference_size"], 3 * 1000 / (8 * watershed.H))
        self.assertEqual(entry["presentation"]["reference_unit"], "Mpc")
        self.assertFalse(entry["production_registry_eligible"])
        self.assertIn("not stated", entry["redistribution_status"])
        self.assertEqual(stats["triangle_count"], entry["triangle_count"])
        self.assertLess(stats["triangle_count"], 60_000)
        self.assertLess(len(glb), 1_500_000)
        self.assertEqual(stats["external_resources"], [])
        self.assertEqual(entry["processing"]["watershed_label"], 1)
        self.assertNotIn("SGX", entry["processing"]["coordinate_policy"])


if __name__ == "__main__":
    unittest.main()
