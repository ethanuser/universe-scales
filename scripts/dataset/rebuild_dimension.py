#!/usr/bin/env python3
"""Safely rebuild and merge one generated dataset dimension."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from scripts.dataset import build_dataset


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_GLOBALS = (
    "DATASET_DIR", "RAW_DIR", "EXPORTS_DIR", "EXPORT_SQLITE_DIR", "EXPORT_JSON_DIR",
    "EXPORT_FRONTEND_DIR", "DIMENSIONS_EXPORT_DIR", "DIMENSION_CATALOG_EXPORT_PATH",
    "CANONICAL_DB_PATH", "SQLITE_EXPORT_PATH", "WRITER_PACKET_EXPORT_PATH", "CONTENT_EXPORT_PATH",
)


@contextmanager
def staged_builder_paths(root: Path, stage: Path) -> Iterator[None]:
    """Redirect builder outputs while retaining repository raw inputs and provenance root."""
    output_paths = {
        "DATASET_DIR": stage / "dataset",
        "RAW_DIR": stage / "dataset" / "raw",
        "EXPORTS_DIR": stage / "exports",
        "EXPORT_SQLITE_DIR": stage / "exports" / "sqlite",
        "EXPORT_JSON_DIR": stage / "exports" / "json",
        "EXPORT_FRONTEND_DIR": stage / "exports" / "frontend",
        "DIMENSIONS_EXPORT_DIR": stage / "exports" / "json" / "dimensions",
        "DIMENSION_CATALOG_EXPORT_PATH": stage / "exports" / "json" / "dimension_catalog.json",
        "CANONICAL_DB_PATH": stage / "dataset" / "universe_scales.sqlite",
        "SQLITE_EXPORT_PATH": stage / "exports" / "sqlite" / "universe_scales.sqlite",
        "WRITER_PACKET_EXPORT_PATH": stage / "exports" / "json" / "writer_packets.jsonl",
        "CONTENT_EXPORT_PATH": stage / "exports" / "json" / "observation_content.jsonl",
        "LEGACY_DATA_DIR": root / "dataset" / "raw" / "legacy_yaml",
        "LEGACY_FALLBACK_DIR": root / "data",
    }
    names = (*OUTPUT_GLOBALS, "LEGACY_DATA_DIR", "LEGACY_FALLBACK_DIR")
    previous = {name: getattr(build_dataset, name) for name in names}
    for name, value in output_paths.items():
        setattr(build_dataset, name, value)

    original_export = build_dataset.DatasetBuilder.export_frontend_yaml

    def export_frontend_yaml_in_stage(builder: build_dataset.DatasetBuilder) -> None:
        # The builder copies flagship YAML into ROOT/data after exporting it.
        previous_root = build_dataset.ROOT
        build_dataset.ROOT = stage
        try:
            original_export(builder)
        finally:
            build_dataset.ROOT = previous_root

    build_dataset.DatasetBuilder.export_frontend_yaml = export_frontend_yaml_in_stage
    try:
        yield
    finally:
        build_dataset.DatasetBuilder.export_frontend_yaml = original_export
        for name, value in previous.items():
            setattr(build_dataset, name, value)


def build_staged_dimension(root: Path, stage: Path) -> None:
    (stage / "data").mkdir(parents=True, exist_ok=True)
    with staged_builder_paths(root, stage):
        build_dataset.DatasetBuilder().run()


def table_columns(connection: sqlite3.Connection, table: str, schema: str = "main") -> list[str]:
    return [str(row[1]) for row in connection.execute(f"PRAGMA {schema}.table_info({table})")]


def insert_rows(
    connection: sqlite3.Connection,
    table: str,
    rows: list[sqlite3.Row],
    *,
    schema: str = "staged",
) -> None:
    if not rows:
        return
    columns = table_columns(connection, table, schema)
    names = ", ".join(f'"{column}"' for column in columns)
    placeholders = ", ".join("?" for _ in columns)
    connection.executemany(
        f'INSERT INTO main."{table}" ({names}) VALUES ({placeholders})',
        [tuple(row[column] for column in columns) for row in rows],
    )


def dimension_id(connection: sqlite3.Connection, slug: str, schema: str = "main") -> str | None:
    row = connection.execute(
        f'SELECT id FROM {schema}.dimensions WHERE slug = ?', (slug,)
    ).fetchone()
    return str(row[0]) if row else None


def rows_for(connection: sqlite3.Connection, table: str, column: str, value: str) -> list[sqlite3.Row]:
    return connection.execute(f'SELECT * FROM staged."{table}" WHERE "{column}" = ?', (value,)).fetchall()


def upsert_dimension(connection: sqlite3.Connection, staged_id: str, old_id: str | None) -> None:
    row = connection.execute("SELECT * FROM staged.dimensions WHERE id = ?", (staged_id,)).fetchone()
    if row is None:
        raise ValueError(f"Staged dimension row not found: {staged_id}")
    if old_id and old_id != staged_id:
        raise ValueError("Dimension ID changed for this slug; refusing to remap unrelated foreign keys")
    columns = table_columns(connection, "dimensions", "staged")
    if old_id:
        assignments = ", ".join(f'"{column}" = ?' for column in columns if column != "id")
        values = [row[column] for column in columns if column != "id"] + [old_id]
        connection.execute(f"UPDATE main.dimensions SET {assignments} WHERE id = ?", values)
    else:
        insert_rows(connection, "dimensions", [row])


def merge_database(root: Path, stage: Path, slug: str) -> Path:
    canonical = root / "dataset" / "universe_scales.sqlite"
    staged_db = stage / "dataset" / "universe_scales.sqlite"
    if not canonical.is_file() or not staged_db.is_file():
        raise FileNotFoundError("Canonical and staged SQLite databases are required")

    merged = stage / "merged.sqlite"
    shutil.copy2(canonical, merged)
    connection = sqlite3.connect(merged)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("ATTACH DATABASE ? AS staged", (str(staged_db),))
        old_id = dimension_id(connection, slug)
        new_id = dimension_id(connection, slug, "staged")
        if not new_id:
            raise ValueError(f"Dimension not produced by staged build: {slug}")

        connection.execute("BEGIN IMMEDIATE")
        old_subject_ids = set()
        if old_id:
            old_subject_ids = {
                str(row[0]) for row in connection.execute(
                    "SELECT subject_id FROM main.observations WHERE dimension_id = ?", (old_id,)
                )
            }
            old_observation_ids = [str(row[0]) for row in connection.execute(
                "SELECT id FROM main.observations WHERE dimension_id = ?", (old_id,)
            )]
            for table in ("observation_content", "observation_qualifiers", "observation_sources"):
                connection.execute(
                    f'DELETE FROM main."{table}" WHERE observation_id IN '
                    f'(SELECT id FROM main.observations WHERE dimension_id = ?)', (old_id,)
                )
            connection.execute("DELETE FROM main.observations WHERE dimension_id = ?", (old_id,))
            connection.execute("DELETE FROM main.coverage_bins WHERE dimension_id = ?", (old_id,))
            connection.execute("DELETE FROM main.units WHERE dimension_id = ?", (old_id,))

        upsert_dimension(connection, new_id, old_id)
        insert_rows(connection, "units", rows_for(connection, "units", "dimension_id", new_id))

        staged_subject_ids = {
            str(row[0]) for row in connection.execute(
                "SELECT subject_id FROM staged.observations WHERE dimension_id = ?", (new_id,)
            )
        }
        candidate_subject_ids = old_subject_ids | staged_subject_ids
        old_shared_ids = {
            str(row[0]) for row in connection.execute(
                "SELECT DISTINCT subject_id FROM main.observations WHERE dimension_id != ?", (old_id or "",)
            )
        }
        staged_shared_ids = {
            str(row[0]) for row in connection.execute(
                "SELECT DISTINCT o.subject_id FROM staged.observations o "
                "JOIN staged.dimensions d ON d.id = o.dimension_id WHERE d.slug != ?", (slug,)
            )
        }
        exclusive_subject_ids = candidate_subject_ids - old_shared_ids - staged_shared_ids

        staged_subjects = {
            str(row["id"]): row for row in connection.execute("SELECT * FROM staged.subjects")
            if str(row["id"]) in candidate_subject_ids
        }
        for subject_id in candidate_subject_ids:
            subject = staged_subjects.get(subject_id)
            exists = connection.execute("SELECT 1 FROM main.subjects WHERE id = ?", (subject_id,)).fetchone()
            if subject is None:
                continue
            if not exists:
                insert_rows(connection, "subjects", [subject])
            elif subject_id in exclusive_subject_ids:
                columns = table_columns(connection, "subjects", "staged")
                assignments = ", ".join(f'"{column}" = ?' for column in columns if column != "id")
                values = [subject[column] for column in columns if column != "id"] + [subject_id]
                connection.execute(f"UPDATE main.subjects SET {assignments} WHERE id = ?", values)

        insert_rows(connection, "observations", rows_for(connection, "observations", "dimension_id", new_id))
        for table in ("observation_content", "observation_qualifiers"):
            ids = [str(row[0]) for row in connection.execute(
                "SELECT id FROM staged.observations WHERE dimension_id = ?", (new_id,)
            )]
            if ids:
                rows = connection.execute(
                    f'SELECT * FROM staged."{table}" WHERE observation_id IN ({",".join("?" for _ in ids)})', ids
                ).fetchall()
                insert_rows(connection, table, rows)

        source_ids = [str(row[0]) for row in connection.execute(
            "SELECT DISTINCT os.source_id FROM staged.observation_sources os "
            "JOIN staged.observations o ON o.id = os.observation_id WHERE o.dimension_id = ?", (new_id,)
        )]
        for source_id in source_ids:
            row = connection.execute("SELECT * FROM staged.sources WHERE id = ?", (source_id,)).fetchone()
            present = connection.execute("SELECT 1 FROM main.sources WHERE id = ?", (source_id,)).fetchone()
            if row is not None and not present:
                insert_rows(connection, "sources", [row])
        observation_ids = [str(row[0]) for row in connection.execute(
            "SELECT id FROM staged.observations WHERE dimension_id = ?", (new_id,)
        )]
        if observation_ids:
            source_links = connection.execute(
                "SELECT * FROM staged.observation_sources WHERE observation_id IN "
                f'({",".join("?" for _ in observation_ids)})', observation_ids
            ).fetchall()
            insert_rows(connection, "observation_sources", source_links)
        insert_rows(connection, "coverage_bins", rows_for(connection, "coverage_bins", "dimension_id", new_id))

        for subject_id in old_subject_ids - staged_subject_ids:
            if subject_id in exclusive_subject_ids:
                connection.execute(
                    "DELETE FROM main.subjects WHERE id = ? AND NOT EXISTS "
                    "(SELECT 1 FROM main.observations WHERE subject_id = ?)", (subject_id, subject_id)
                )

        violations = connection.execute("PRAGMA main.foreign_key_check").fetchall()
        if violations:
            raise sqlite3.IntegrityError(f"Foreign-key violations after merge: {violations[:5]}")
        connection.commit()
        result = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise sqlite3.DatabaseError(f"Merged database integrity check failed: {result}")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return merged


def jsonl_records(path: Path) -> list[bytes]:
    return path.read_bytes().splitlines(keepends=True) if path.exists() else []


def record_payload(line: bytes) -> dict[str, Any] | None:
    try:
        return json.loads(line)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def merge_jsonl(
    current: Path,
    staged: Path,
    output: Path,
    predicate: Any,
) -> None:
    original_lines = jsonl_records(current)
    staged_lines = [line for line in jsonl_records(staged) if predicate(record_payload(line))]
    output_lines: list[bytes] = []
    inserted = False
    for line in original_lines:
        if predicate(record_payload(line)):
            if not inserted:
                output_lines.extend(staged_lines)
                inserted = True
            continue
        output_lines.append(line)
    if not inserted:
        output_lines.extend(staged_lines)
    output.write_bytes(b"".join(output_lines))


def merge_json_document(current: Path, staged: Path, output: Path, slug: str, *, keyed: bool) -> None:
    original = json.loads(current.read_text(encoding="utf-8"))
    replacement = json.loads(staged.read_text(encoding="utf-8"))
    if keyed:
        original[slug] = replacement[slug]
    else:
        staged_row = next((row for row in replacement if row.get("slug") == slug), None)
        if staged_row is None:
            raise ValueError(f"Dimension missing from staged catalog: {slug}")
        for index, row in enumerate(original):
            if row.get("slug") == slug:
                original[index] = staged_row
                break
        else:
            original.append(staged_row)
    output.write_text(json.dumps(original, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stage_outputs(root: Path, stage: Path, slug: str, subject_ids: set[str]) -> dict[Path, Path]:
    current_json = root / "exports" / "json"
    staged_json = stage / "exports" / "json"
    prepared = stage / "prepared"
    prepared.mkdir()
    outputs: dict[Path, Path] = {}
    jsonl_filters = {
        "observations.jsonl": lambda row: bool(row and row.get("dimension_slug") == slug),
        "observation_content.jsonl": lambda row: bool(row and row.get("dimension_slug") == slug),
        "writer_packets.jsonl": lambda row: bool(row and row.get("dimension", {}).get("slug") == slug),
        "subjects.jsonl": lambda row: bool(row and row.get("id") in subject_ids),
    }
    for filename, predicate in jsonl_filters.items():
        target, result = current_json / filename, prepared / filename
        merge_jsonl(target, staged_json / filename, result, predicate)
        outputs[target] = result

    for filename, keyed in (("coverage_report.json", True), ("dimension_catalog.json", False)):
        target, result = current_json / filename, prepared / filename
        merge_json_document(target, staged_json / filename, result, slug, keyed=keyed)
        outputs[target] = result

    dimension_json = root / "exports" / "json" / "dimensions" / f"{slug}.json"
    outputs[dimension_json] = stage / "exports" / "json" / "dimensions" / f"{slug}.json"
    frontend_yaml = root / "exports" / "frontend" / f"{slug}.yaml"
    outputs[frontend_yaml] = stage / "exports" / "frontend" / f"{slug}.yaml"
    site_yaml = root / "data" / f"{slug}.yaml"
    staged_site_yaml = stage / "data" / f"{slug}.yaml"
    if staged_site_yaml.exists():
        outputs[site_yaml] = staged_site_yaml

    return outputs


def replace_transactionally(stage: Path, replacements: dict[Path, Path]) -> None:
    backup_dir = stage / "backups"
    backup_dir.mkdir()
    backups: dict[Path, Path | None] = {}
    replaced: list[Path] = []
    for index, (target, source) in enumerate(replacements.items()):
        if not source.is_file():
            raise FileNotFoundError(f"Expected staged output missing: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"{index}.bak" if target.exists() else None
        if backup:
            shutil.copy2(target, backup)
        backups[target] = backup
    try:
        for target, source in replacements.items():
            os.replace(source, target)
            replaced.append(target)
    except Exception:
        for target in reversed(replaced):
            backup = backups[target]
            if backup:
                os.replace(backup, target)
            else:
                target.unlink(missing_ok=True)
        raise


def merge_dimension(root: Path, stage: Path, slug: str) -> None:
    root, stage = root.resolve(), stage.resolve()
    canonical = root / "dataset" / "universe_scales.sqlite"
    export_db = root / "exports" / "sqlite" / "universe_scales.sqlite"
    merged_db = merge_database(root, stage, slug)

    with sqlite3.connect(canonical) as old_db, sqlite3.connect(stage / "dataset" / "universe_scales.sqlite") as new_db:
        old_id = dimension_id(old_db, slug)
        new_id = dimension_id(new_db, slug)
        subject_ids = set()
        for connection, dimension in ((old_db, old_id), (new_db, new_id)):
            if dimension:
                subject_ids.update(str(row[0]) for row in connection.execute(
                    "SELECT DISTINCT subject_id FROM observations WHERE dimension_id = ?", (dimension,)
                ))
        old_non_target = {
            str(row[0]) for row in old_db.execute(
                "SELECT DISTINCT o.subject_id FROM observations o JOIN dimensions d ON d.id=o.dimension_id WHERE d.slug != ?", (slug,)
            )
        }
        new_non_target = {
            str(row[0]) for row in new_db.execute(
                "SELECT DISTINCT o.subject_id FROM observations o JOIN dimensions d ON d.id=o.dimension_id WHERE d.slug != ?", (slug,)
            )
        }
        subject_ids -= old_non_target | new_non_target

    replacements = stage_outputs(root, stage, slug, subject_ids)
    export_copy = stage / "merged-export.sqlite"
    shutil.copy2(merged_db, export_copy)
    replacements[canonical] = merged_db
    replacements[export_db] = export_copy
    replace_transactionally(stage, replacements)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild and merge one dataset dimension safely.")
    parser.add_argument("dimension", help="Dimension slug, for example length")
    parser.add_argument("--dry-run", action="store_true", help="Build and validate staged outputs without changing repository outputs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with tempfile.TemporaryDirectory(prefix="rebuild-dimension-", dir=ROOT) as temporary:
        stage = Path(temporary)
        build_staged_dimension(ROOT, stage)
        # A staged export is still a full build; only this slug is ever published.
        with sqlite3.connect(stage / "dataset" / "universe_scales.sqlite") as staged_db:
            staged_id = dimension_id(staged_db, args.dimension)
        if not staged_id:
            raise SystemExit(f"Unknown dimension slug: {args.dimension}")
        if args.dry_run:
            merge_database(ROOT, stage, args.dimension)
            print(f"Validated staged rebuild for {args.dimension}; repository outputs unchanged.")
            return 0
        merge_dimension(ROOT, stage, args.dimension)
    print(f"Rebuilt dimension: {args.dimension}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
