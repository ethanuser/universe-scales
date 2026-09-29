import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.dataset import build_dataset
from scripts.dataset import rebuild_dimension


class RebuildDimensionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.stage = self.root / "stage"
        self.stage.mkdir()
        self._make_repo_layout()
        self._make_database(self.root / "dataset" / "universe_scales.sqlite", staged=False)
        shutil.copy2(
            self.root / "dataset" / "universe_scales.sqlite",
            self.root / "exports" / "sqlite" / "universe_scales.sqlite",
        )
        self._make_database(self.stage / "dataset" / "universe_scales.sqlite", staged=True)
        shutil.copy2(
            self.stage / "dataset" / "universe_scales.sqlite",
            self.stage / "exports" / "sqlite" / "universe_scales.sqlite",
        )
        self._make_json_exports()

    def tearDown(self):
        self.temporary.cleanup()

    def _make_repo_layout(self):
        for path in (
            self.root / "dataset", self.root / "exports" / "sqlite",
            self.root / "exports" / "json" / "dimensions", self.root / "exports" / "frontend",
            self.root / "data", self.stage / "dataset", self.stage / "exports" / "sqlite",
            self.stage / "exports" / "json" / "dimensions", self.stage / "exports" / "frontend",
            self.stage / "data",
        ):
            path.mkdir(parents=True, exist_ok=True)

    def _make_database(self, path, *, staged):
        instance = build_dataset.DatasetBuilder.__new__(build_dataset.DatasetBuilder)
        instance.conn = None
        with patch.object(build_dataset, "CANONICAL_DB_PATH", path):
            instance.build_schema()
        with sqlite3.connect(path) as db:
            db.execute("PRAGMA foreign_keys = ON")
            db.executemany(
                "INSERT INTO dimensions (id, slug, name, base_unit, stable_flag) VALUES (?, ?, ?, ?, ?)",
                [("dim:length", "length", "Length new" if staged else "Length old", "meters", 1),
                 ("dim:duration", "duration", "Duration", "seconds", 1)],
            )
            subjects = [
                ("sub:shared", "entity", "Shared staged" if staged else "Shared", None, None, None, "[]"),
                ("sub:old", "entity", "Old target", None, None, None, "[]"),
            ]
            if staged:
                subjects.append(("sub:new", "entity", "New target", None, None, None, "[]"))
            db.executemany("INSERT INTO subjects VALUES (?, ?, ?, ?, ?, ?, ?)", subjects)
            db.execute("INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ("src:shared", "web", "Shared source", "https://example.test/shared", None, None, None, "secondary"))
            if staged:
                db.execute("INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           ("src:new", "web", "New source", "https://example.test/new", None, None, None, "primary"))
            db.executemany(
                "INSERT INTO units (id, dimension_id, name, symbol, to_base_factor) VALUES (?, ?, ?, ?, ?)",
                [("unit:length", "dim:length", "meters", "m", 1),
                 ("unit:duration", "dim:duration", "seconds", "s", 1)],
            )
            observations = [
                (("obs:length-new", "sub:new", "dim:length", "New value", 2.0) if staged
                 else ("obs:length-old", "sub:old", "dim:length", "Old value", 1.0)),
                ("obs:duration", "sub:shared", "dim:duration", "One second", 1.0),
            ]
            db.executemany(
                "INSERT INTO observations (id, subject_id, dimension_id, label, value_base, value_type, display_eligible) "
                "VALUES (?, ?, ?, ?, ?, 'measured', 1)", observations,
            )
            for obs_id, origin in (("obs:length-new", "new"),) if staged else (("obs:length-old", "old"),):
                db.execute(
                    "INSERT INTO observation_content (id, observation_id, content_origin, content_status) VALUES (?, ?, ?, 'ready')",
                    (f"content:{origin}", obs_id, origin),
                )
                db.execute(
                    "INSERT INTO observation_qualifiers (id, observation_id, key, value_text) VALUES (?, ?, 'condition', ?)",
                    (f"qualifier:{origin}", obs_id, origin),
                )
                source_id = "src:new" if staged else "src:shared"
                db.execute(
                    "INSERT INTO observation_sources (id, observation_id, source_id, role) VALUES (?, ?, ?, 'evidence')",
                    (f"link:{origin}", obs_id, source_id),
                )
            db.execute(
                "INSERT INTO coverage_bins (id, dimension_id, bin_index, log10_min, log10_max) VALUES "
                "('bin:length', 'dim:length', 0, -1, 1), ('bin:duration', 'dim:duration', 0, -1, 1)"
            )

    @staticmethod
    def _line(value):
        return json.dumps(value, sort_keys=True).encode() + b"\n"

    def _make_json_exports(self):
        current = self.root / "exports" / "json"
        staged = self.stage / "exports" / "json"
        current.mkdir(parents=True, exist_ok=True)
        staged.mkdir(parents=True, exist_ok=True)
        unrelated_observation = b'{ "dimension_slug" : "duration", "id" : "obs:duration" }\n'
        unrelated_content = b'{"dimension_slug":"duration","observation_id":"obs:duration"}\n'
        unrelated_packet = b'{ "dimension" : {"slug":"duration"}, "observation_id":"obs:duration" }\n'
        unrelated_subject = b'{ "id" : "sub:shared", "canonical_name" : "Shared" }\n'
        for name, unrelated in (("observations.jsonl", unrelated_observation),
                                ("observation_content.jsonl", unrelated_content),
                                ("writer_packets.jsonl", unrelated_packet),
                                ("subjects.jsonl", unrelated_subject)):
            (current / name).write_bytes(unrelated)

        target_observation = {"dimension_slug": "length", "id": "obs:length-new"}
        target_content = {"dimension_slug": "length", "observation_id": "obs:length-new"}
        target_packet = {"dimension": {"slug": "length"}, "observation_id": "obs:length-new"}
        target_subject = {"id": "sub:new", "canonical_name": "New target"}
        staged_lines = {
            "observations.jsonl": [target_observation],
            "observation_content.jsonl": [target_content],
            "writer_packets.jsonl": [target_packet],
            "subjects.jsonl": [target_subject],
        }
        for name, records in staged_lines.items():
            (staged / name).write_bytes(b"".join(self._line(record) for record in records))

        for folder in (current / "dimensions", staged / "dimensions"):
            folder.mkdir(exist_ok=True)
        (current / "coverage_report.json").write_text(json.dumps({"length": {"count": 1}, "duration": {"count": 7}}))
        (staged / "coverage_report.json").write_text(json.dumps({"length": {"count": 2}, "duration": {"count": 999}}))
        (current / "dimension_catalog.json").write_text(json.dumps([
            {"slug": "length", "name": "Length old"}, {"slug": "duration", "name": "Duration"}
        ]))
        (staged / "dimension_catalog.json").write_text(json.dumps([
            {"slug": "length", "name": "Length new"}, {"slug": "duration", "name": "Wrong staged duration"}
        ]))
        (current / "dimensions" / "length.json").write_text('{"version":"old"}')
        (staged / "dimensions" / "length.json").write_text('{"version":"new"}')
        (self.root / "exports" / "frontend" / "length.yaml").write_text("version: old\n")
        (self.stage / "exports" / "frontend" / "length.yaml").write_text("version: new\n")
        (self.root / "data" / "length.yaml").write_text("version: old\n")
        (self.stage / "data" / "length.yaml").write_text("version: new\n")

    def test_merges_only_requested_dimension_and_preserves_unrelated_jsonl_bytes(self):
        json_dir = self.root / "exports" / "json"
        unrelated = {
            name: (json_dir / name).read_bytes()
            for name in ("observations.jsonl", "observation_content.jsonl", "writer_packets.jsonl", "subjects.jsonl")
        }
        rebuild_dimension.merge_dimension(self.root, self.stage, "length")

        with sqlite3.connect(self.root / "dataset" / "universe_scales.sqlite") as db:
            self.assertEqual(db.execute("SELECT label FROM observations WHERE dimension_id='dim:length'").fetchall(), [("New value",)])
            self.assertEqual(db.execute("SELECT label FROM observations WHERE dimension_id='dim:duration'").fetchall(), [("One second",)])
            self.assertEqual(db.execute("SELECT canonical_name FROM subjects WHERE id='sub:shared'").fetchone(), ("Shared",))
            self.assertEqual(db.execute("SELECT canonical_name FROM subjects WHERE id='sub:new'").fetchone(), ("New target",))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM observation_content WHERE observation_id='obs:length-new'").fetchone(), (1,))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM observation_qualifiers WHERE observation_id='obs:length-new'").fetchone(), (1,))
            self.assertEqual(db.execute("SELECT source_id FROM observation_sources WHERE observation_id='obs:length-new'").fetchone(), ("src:new",))
            self.assertEqual(db.execute("SELECT name FROM dimensions WHERE slug='duration'").fetchone(), ("Duration",))
            self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])

        self.assertEqual(
            (self.root / "dataset" / "universe_scales.sqlite").read_bytes(),
            (self.root / "exports" / "sqlite" / "universe_scales.sqlite").read_bytes(),
        )
        for name, original_unrelated_line in unrelated.items():
            merged_lines = (json_dir / name).read_bytes().splitlines(keepends=True)
            self.assertIn(original_unrelated_line.rstrip(b"\n"), [line.rstrip(b"\n") for line in merged_lines])
        self.assertEqual(json.loads((json_dir / "coverage_report.json").read_text()),
                         {"length": {"count": 2}, "duration": {"count": 7}})
        catalog = json.loads((json_dir / "dimension_catalog.json").read_text())
        self.assertEqual(catalog, [{"name": "Length new", "slug": "length"}, {"name": "Duration", "slug": "duration"}])
        self.assertEqual((json_dir / "dimensions" / "length.json").read_text(), '{"version":"new"}')
        self.assertEqual((self.root / "exports" / "frontend" / "length.yaml").read_text(), "version: new\n")
        self.assertEqual((self.root / "data" / "length.yaml").read_text(), "version: new\n")

    def test_staging_redirects_outputs_but_keeps_raw_inputs_and_root(self):
        original_class = build_dataset.DatasetBuilder

        # Verify the context's path contract without invoking a repository-wide build.
        previous_root = build_dataset.ROOT
        with rebuild_dimension.staged_builder_paths(self.root, self.stage):
            self.assertEqual(build_dataset.ROOT, previous_root)
            self.assertEqual(build_dataset.LEGACY_DATA_DIR, self.root / "dataset" / "raw" / "legacy_yaml")
            self.assertEqual(build_dataset.LEGACY_FALLBACK_DIR, self.root / "data")
            self.assertEqual(build_dataset.CANONICAL_DB_PATH, self.stage / "dataset" / "universe_scales.sqlite")
            self.assertEqual(build_dataset.EXPORT_JSON_DIR, self.stage / "exports" / "json")
        self.assertIs(build_dataset.DatasetBuilder, original_class)


if __name__ == "__main__":
    unittest.main()
