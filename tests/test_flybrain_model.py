import csv
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_flybrain_model as brain


class FlyBrainGeometryTests(unittest.TestCase):
    def test_coordinate_change_preserves_physical_distances_and_handedness(self):
        source = np.array([[500., 200., 100.], [600., 250., 140.]])
        transformed = brain.model_coordinates(source)
        self.assertAlmostEqual(np.linalg.norm(transformed[1] - transformed[0]),
                               np.linalg.norm(source[1] - source[0]))
        axes = brain.model_coordinates(np.eye(3)) - brain.model_coordinates(np.zeros((3, 3)))
        self.assertAlmostEqual(np.linalg.det(axes), 1)

    def test_chain_simplification_preserves_junctions_and_separate_components(self):
        # A fork and an independent component; simplification must never join them.
        xyz = np.array([[0., 0., 0.], [10, 0, 0], [20, 10, 0], [20, -10, 0],
                        [100, 0, 0], [110, 0, 0]])
        node = np.array([1, 3, 5, 8, 9, 10])
        parent = np.array([-1, 1, 3, 3, -1, 9])
        p, edges, _ = brain.simplify_tree(xyz, node, parent, np.ones(6), prune=0)
        self.assertTrue(any(np.all(p == xyz[1], axis=1)))
        self.assertEqual(len(edges), 4)
        for a, b in edges:
            self.assertEqual(p[a, 0] < 100, p[b, 0] < 100)

    def test_absent_parent_never_becomes_a_spurious_path(self):
        p, edges, _ = brain.simplify_tree(np.array([[0., 0, 0], [10., 0, 0]]),
                                         np.array([1, 4]), np.array([-1, 3]), np.ones(2))
        self.assertEqual(len(edges), 0)

    def test_cycles_fail_instead_of_hanging_or_fabricating_a_tree(self):
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            brain.simplify_tree(np.zeros((2, 3)), np.array([1, 2]), np.array([2, 1]), np.ones(2))

    def test_rdp_preserves_a_bend_larger_than_its_micrometre_tolerance(self):
        points = np.array([[0., 0, 0], [2, .2, 0], [4, 3, 0], [6, 0, 0]])
        kept = brain.rdp(points, tolerance=1.)
        self.assertIn(2, kept)
        np.testing.assert_array_equal(brain.rdp(points, tolerance=4.), [0, 3])

    def test_selection_is_independent_of_annotation_file_order_and_excludes_fragments(self):
        fields = ["root_id", "super_class", "side", "cell_type", "cell_class", "status"]
        rows = [[str(i), "central", "left" if i % 2 else "right", "type", "", ""] for i in range(20)]
        rows.append(["100", "central", "left", "other", "", "fragment"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "annotations.tsv"
            def write(values):
                with path.open("w") as stream:
                    writer = csv.writer(stream, delimiter="\t")
                    writer.writerow(fields)
                    writer.writerows(values)
            write(rows)
            first = brain.select_neurons(path)
            write(rows[::-1])
            self.assertEqual(list(first), list(brain.select_neurons(path)))
            self.assertNotIn(100, first)


if __name__ == "__main__":
    unittest.main()
