#!/usr/bin/env python3
"""Verify the canonical Universe Scales dataset artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.dataset.build_dataset import DatasetBuilder  # noqa: E402
from scripts.dataset.raw_loader import load_raw_catalog  # noqa: E402


DB_PATH = ROOT / "dataset" / "universe_scales.sqlite"
RAW_CATALOG = load_raw_catalog()
FLAGSHIP_DIMENSIONS = [str(item["slug"]) for item in RAW_CATALOG.flagship_dimensions]
GENERATED_FILES = [
    ROOT / "dataset" / "universe_scales.sqlite",
    ROOT / "exports" / "sqlite" / "universe_scales.sqlite",
    ROOT / "exports" / "json" / "subjects.jsonl",
    ROOT / "exports" / "json" / "dimension_catalog.json",
    ROOT / "exports" / "json" / "observations.jsonl",
    ROOT / "exports" / "json" / "observation_content.jsonl",
    ROOT / "exports" / "json" / "writer_packets.jsonl",
    ROOT / "exports" / "json" / "coverage_report.json",
]
GENERATED_FILES.extend(ROOT / "data" / f"{slug}.yaml" for slug in FLAGSHIP_DIMENSIONS)
GENERATED_FILES.extend(ROOT / "exports" / "frontend" / f"{slug}.yaml" for slug in FLAGSHIP_DIMENSIONS)
GENERATED_FILES.extend(ROOT / "exports" / "json" / "dimensions" / f"{slug}.json" for slug in FLAGSHIP_DIMENSIONS)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_hashes() -> dict[Path, str]:
    return {path: sha256(path) for path in GENERATED_FILES if path.exists()}


def verify_sqlite(conn: sqlite3.Connection) -> None:
    conn.row_factory = sqlite3.Row
    coverage = json.loads((ROOT / "exports" / "json" / "coverage_report.json").read_text(encoding="utf-8"))
    canonical_reference_count = conn.execute(
        """
        SELECT COUNT(*) AS count
          FROM observations
         WHERE LOWER(COALESCE(category, '')) = 'reference'
        """
    ).fetchone()["count"]
    assert canonical_reference_count == 0, "canonical corpus still contains reference observations"
    duplicate_selected_count = conn.execute(
        """
        SELECT COUNT(*) AS count
          FROM (
                SELECT dimension_id, LOWER(TRIM(label)) AS norm_label, value_base, COUNT(*) AS c
                  FROM observations
                 WHERE rationale IS NOT NULL
                 GROUP BY dimension_id, LOWER(TRIM(label)), value_base
                HAVING COUNT(*) > 1
          )
        """
    ).fetchone()["count"]
    assert duplicate_selected_count == 0, "selected export still contains duplicate label/value observations"

    for slug in FLAGSHIP_DIMENSIONS:
        dimension = conn.execute(
            """
            SELECT id, required_min_items, preferred_target_items, preferred_max_items, selection_bin_count
              FROM dimensions
             WHERE slug = ?
            """,
            (slug,),
        ).fetchone()
        assert dimension is not None, f"missing dimension row for {slug}"

        selected = conn.execute(
            """
            SELECT COUNT(*) AS count
              FROM observations
             WHERE dimension_id = ? AND rationale IS NOT NULL
            """,
            (dimension["id"],),
        ).fetchone()["count"]
        candidate = coverage[slug]["candidate_count"]
        required_min = int(dimension["required_min_items"])
        assert selected <= candidate, f"{slug} selected_count={selected} exceeds candidate_count={candidate}"
        if candidate > 0:
            assert selected > 0, f"{slug} has displayable candidates but nothing selected"

        selected_reference_count = conn.execute(
            """
            SELECT COUNT(*) AS count
              FROM observations
             WHERE dimension_id = ?
               AND rationale IS NOT NULL
               AND LOWER(COALESCE(category, '')) = 'reference'
            """,
            (dimension["id"],),
        ).fetchone()["count"]
        assert selected_reference_count == 0, f"{slug} still has selected reference placeholders"

        broken_rows = conn.execute(
            """
            SELECT COUNT(*) AS count
              FROM observations o
              LEFT JOIN observation_content oc ON oc.observation_id = o.id
             WHERE o.dimension_id = ?
               AND o.rationale IS NOT NULL
               AND (
                    o.subject_id IS NULL
                    OR o.value_base <= 0
                    OR o.value_type NOT IN ('measured', 'derived')
                    OR oc.observation_id IS NULL
                    OR COALESCE(oc.content_format, '') = ''
                    OR COALESCE(oc.summary_short, '') = ''
                    OR COALESCE(oc.description_medium, '') = ''
                    OR COALESCE(o.review_status, '') = ''
                    OR o.review_status NOT IN ('candidate', 'accepted', 'needs_source', 'needs_description', 'deprecated', 'excluded')
                    OR COALESCE(o.display_status, '') = ''
                    OR o.display_status NOT IN ('display', 'hidden')
                    OR COALESCE(o.quality_flags_json, '') = ''
                    OR NOT EXISTS (
                        SELECT 1 FROM observation_sources os WHERE os.observation_id = o.id
                    )
               )
            """,
            (dimension["id"],),
        ).fetchone()["count"]
        assert broken_rows == 0, f"{slug} has malformed selected observations"

        units = conn.execute("SELECT to_base_factor, offset FROM units WHERE dimension_id = ?", (dimension["id"],)).fetchall()
        sample = conn.execute(
            "SELECT value_base FROM observations WHERE dimension_id = ? AND rationale IS NOT NULL LIMIT 1",
            (dimension["id"],),
        ).fetchone()
        assert sample is not None or selected == 0, f"{slug} has no selected sample value"
        if sample is None:
            continue
        base_value = float(sample["value_base"])
        for unit in units:
            factor = float(unit["to_base_factor"])
            offset = float(unit["offset"])
            converted = (base_value + offset) * factor
            roundtrip = (converted / factor) - offset
            assert abs(roundtrip - base_value) < max(1e-12, abs(base_value) * 1e-12), f"{slug} unit roundtrip failed"

        assert coverage[slug]["bin_count"] == int(dimension["selection_bin_count"]), f"{slug} coverage bin count mismatch"
        assert coverage[slug]["required_min_items"] == required_min, f"{slug} required min mismatch"
        assert coverage[slug]["preferred_target_items"] == int(dimension["preferred_target_items"]), f"{slug} target mismatch"
        assert coverage[slug]["preferred_max_items"] == int(dimension["preferred_max_items"]), f"{slug} max mismatch"

    banned_labels = {
        "Micro Black Hole Lifetime",
        "Primordial Black Hole Lifetime",
        "Black Hole Lifetime",
        "Neutron Star Lifetime",
        "String Length",
    }
    banned_count = conn.execute(
        """
        SELECT COUNT(*) AS count
          FROM observations
         WHERE rationale IS NOT NULL AND label IN ({})
        """.format(",".join("?" for _ in banned_labels)),
        tuple(sorted(banned_labels)),
    ).fetchone()["count"]
    assert banned_count == 0, "theoretical or excluded observations are still selected"


def verify_yaml_files() -> None:
    coverage = json.loads((ROOT / "exports" / "json" / "coverage_report.json").read_text(encoding="utf-8"))
    for slug in FLAGSHIP_DIMENSIONS:
        site_yaml_path = ROOT / "data" / f"{slug}.yaml"
        export_yaml_path = ROOT / "exports" / "frontend" / f"{slug}.yaml"
        payload = yaml.safe_load(site_yaml_path.read_text(encoding="utf-8"))
        export_payload = yaml.safe_load(export_yaml_path.read_text(encoding="utf-8"))
        assert payload == export_payload, f"{slug}.yaml differs from frontend export copy"
        assert isinstance(payload.get("items"), list), f"{slug}.yaml missing items list"
        assert len(payload["items"]) == int(coverage[slug]["selected_count"]), f"{slug}.yaml selected count mismatch"
        for item in payload["items"]:
            assert item.get("description"), f"{slug}.yaml item missing description"
            assert item.get("description_medium"), f"{slug}.yaml item missing description_medium"
            assert not str(item.get("name", "")).startswith("Reference "), f"{slug}.yaml still exposes reference placeholder items"


def verify_json_exports() -> None:
    catalog_path = ROOT / "exports" / "json" / "dimension_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert isinstance(catalog, list) and catalog, "dimension catalog export is empty"
    assert any(entry.get("available") for entry in catalog), "dimension catalog has no available dimensions"

    writer_path = ROOT / "exports" / "json" / "writer_packets.jsonl"
    writer_lines = [json.loads(line) for line in writer_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert writer_lines, "writer packet export is empty"
    selected_packets = [line for line in writer_lines if line["selected_for_display"]]
    assert selected_packets, "writer packet export has no selected items"
    for packet in selected_packets[:10]:
        assert packet["content"]["summary_short"], "writer packet missing summary_short"
        assert packet["observation"]["review_status"], "writer packet missing review_status"
        assert packet["observation"]["display_status"], "writer packet missing display_status"
        assert isinstance(packet["observation"]["quality_flags"], list), "writer packet missing quality_flags"
        assert packet["sources"], "writer packet missing sources"
        assert packet["unit_conversions"], "writer packet missing unit conversions"
        assert packet["content"]["content_format"] == "markdown", "writer packet missing content format"


def verify_cli() -> None:
    commands = [
        [sys.executable, str(ROOT / "scripts" / "query_dataset.py"), "between", "mass", "1e-9", "1e9", "--selected-only"],
        [sys.executable, str(ROOT / "scripts" / "query_dataset.py"), "nearest", "density", "1000", "--selected-only"],
        [sys.executable, str(ROOT / "scripts" / "query_dataset.py"), "dimension-stats", "area"],
        [sys.executable, str(ROOT / "scripts" / "query_dataset.py"), "subject", "sub:entity-earth", "--selected-only"],
        [sys.executable, str(ROOT / "scripts" / "query_dataset.py"), "observation", "obs:frequency:entity-cesium-clock-transition"],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        assert result.returncode == 0, f"CLI command failed: {' '.join(command)}"
        assert result.stdout.strip(), f"CLI command returned no output: {' '.join(command)}"


def verify_determinism() -> None:
    before = snapshot_hashes()
    builder = DatasetBuilder()
    builder.run()
    after = snapshot_hashes()
    assert before == after, "Generated artifact hashes changed after a rebuild"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the canonical Universe Scales dataset.")
    parser.add_argument("--skip-determinism", action="store_true", help="Skip the rebuild-and-hash determinism check.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    conn = sqlite3.connect(DB_PATH)
    try:
        verify_sqlite(conn)
    finally:
        conn.close()
    verify_yaml_files()
    verify_json_exports()
    verify_cli()
    if not args.skip_determinism:
        verify_determinism()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
