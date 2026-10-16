from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_nebula_volumes import shell_depth, sky_offset_arcsec  # noqa: E402
from nebula_volume import KERNEL, calibrated_samples, decompose, elliptical_feather, grid_samples, split_stars  # noqa: E402


def test_image(seed=3, size=96):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size] / size
    glow = np.exp(-((xx - 0.5) ** 2 + (yy - 0.45) ** 2) / 0.05)
    image = np.stack([glow * 0.8, glow * 0.4, glow * 0.6], -1) + rng.random((size, size, 3)) * 0.02
    for x, y in rng.integers(5, size - 5, (6, 2)):
        image[y, x] = 1.0  # stars
    return image.astype(np.float32)


class NebulaVolumeTests(unittest.TestCase):
    def total_light(self, x, color, alpha, width, q):
        return (color.max(axis=1) * alpha).sum() * KERNEL * (width * q) ** 2

    def test_sprites_conserve_the_photo_light(self):
        gas = test_image()
        target = gas.max(axis=2).sum()
        q = 0.05
        for samples in (calibrated_samples(gas, 20000, np.random.default_rng(1), q, gamma=0.8),
                        grid_samples(gas, 3, np.random.default_rng(1), q, floor=0)):
            x, y, color, alpha = samples
            self.assertAlmostEqual(self.total_light(x, color, alpha, gas.shape[1], q) / target, 1, delta=0.06)
            self.assertTrue(np.all((x >= 0) & (x <= gas.shape[1]) & (y >= 0) & (y <= gas.shape[0])))

    def test_decomposition_is_nonnegative_and_exact(self):
        gas, _ = split_stars(test_image())
        low, high = decompose(gas, radius=3, sigma=4)
        self.assertTrue(np.all(low >= 0) and np.all(high >= 0))
        np.testing.assert_allclose(low + high, gas, atol=1e-6)

    def test_star_split_finds_point_sources(self):
        gas, stars = split_stars(test_image(), radius=3, threshold=0.2)
        self.assertGreaterEqual(len(stars), 5)
        self.assertLess(gas.max(), 0.95)

    def test_feather_and_shell_depth_bounds(self):
        feather = elliptical_feather((40, 60), 0.6)
        self.assertEqual(feather[20, 30], 1)
        self.assertEqual(feather[0, 0], 0)
        rng = np.random.default_rng(2)
        x, y = rng.uniform(-50, 50, (2, 500))
        fields = {name: rng.normal(size=500) for name in ("radius", "side", "warp")}
        z = shell_depth(80)(x, y, "detail", rng, fields)
        self.assertLess(np.abs(z).max(), 80 * 2.5)
        self.assertGreater(z.std(), 10)

    def test_sky_offsets_point_east_and_north(self):
        east, north = sky_offset_arcsec((10.01, 20.0), (10.0, 20.0))
        self.assertGreater(east, 0)
        self.assertAlmostEqual(north, 0)


if __name__ == "__main__":
    unittest.main()
