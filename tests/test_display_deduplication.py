import unittest

from scripts.dataset.build_dataset import DatasetBuilder


class DisplayDeduplicationTests(unittest.TestCase):
    def select(self, rows, qualifiers=None, groups=None):
        builder = DatasetBuilder.__new__(DatasetBuilder)
        builder.dimension_profile = lambda slug: {"display_equivalents": groups or []}
        builder.fetch_qualifiers = lambda key: (qualifiers or {}).get(key, {})
        builder.display_representative_rank = lambda row: (row["value_base"], row["id"])
        return builder.select_display_representatives(rows)

    @staticmethod
    def row(key, label, value, dimension="angular-velocity", date=None):
        return {"id": key, "label": label, "value_base": value,
                "dimension_id": f"dim:{dimension}", "snapshot_date": date}

    def test_equivalent_labels_and_rounded_values_use_explicit_preference(self):
        rows = [self.row("rounded", "Moon orbit", 2.66e-6),
                self.row("preferred", "Moon orbit around Earth", 2.66e-6)]
        group = {"labels": ["Moon orbit around Earth", "Moon orbit"], "preferred_id": "preferred"}
        self.assertEqual(self.select(rows, {"rounded": {"measurement": "orbital angular velocity"}}, [group]), [rows[1]])

    def test_conditions_and_dates_keep_distinct_observations(self):
        rows = [self.row("a", "Fan", 10), self.row("b", "Fan", 20),
                self.row("c", "Fan", 30, date="2020-01-01")]
        qualifiers = {"a": {"rpm": 100}, "b": {"rpm": 200}, "c": {"rpm": 200}}
        self.assertEqual(len(self.select(rows, qualifiers)), 3)

    def test_unfamiliar_measurement_definitions_are_not_discarded(self):
        rows = [self.row("a", "Material", .5, "friction-coefficient"),
                self.row("b", "Material", .3, "friction-coefficient")]
        qualifiers = {"a": {"measurement": "static friction"}, "b": {"measurement": "kinetic friction"}}
        self.assertEqual(len(self.select(rows, qualifiers)), 2)

    def test_generic_quantity_wording_and_derivation_do_not_make_duplicates(self):
        rows = [self.row("a", "Aluminum", 897, "specific-heat"),
                self.row("b", "Aluminum", 900, "specific-heat")]
        qualifiers = {"b": {"measurement": "specific heat capacity", "derivation": "rounded source value"}}
        self.assertEqual(len(self.select(rows, qualifiers)), 1)

    def test_equal_numbers_are_not_a_duplicate_identity(self):
        rows = [self.row("a", "Moon orbit", 1), self.row("b", "Earth rotation", 1)]
        self.assertEqual(len(self.select(rows)), 2)


if __name__ == "__main__":
    unittest.main()
