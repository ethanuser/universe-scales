#!/usr/bin/env python3
"""Query the canonical Universe Scales SQLite dataset."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "dataset" / "universe_scales.sqlite"


def open_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def format_source_value(source_value_text: str | None, source_unit: str | None) -> str:
    value_text = str(source_value_text or "").strip()
    unit_text = str(source_unit or "").strip()
    if not unit_text or not value_text:
        return value_text

    numeric_candidate = value_text.replace("+", "").replace("-", "").replace(".", "").replace("e", "").replace("E", "")
    if numeric_candidate.isdigit():
        return f"{value_text} {unit_text}"
    return value_text


def selected_clause(selected_only: bool) -> str:
    return "AND o.rationale IS NOT NULL" if selected_only else ""


def cmd_between(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    rows = conn.execute(
        f"""
        SELECT o.label, o.value_base, o.value_type, sub.canonical_name AS subject_name, sub.wikidata_qid
          FROM observations o
          JOIN dimensions d ON d.id = o.dimension_id
          JOIN subjects sub ON sub.id = o.subject_id
         WHERE d.slug = ?
           AND o.value_base BETWEEN ? AND ?
           {selected_clause(args.selected_only)}
         ORDER BY o.value_base, o.id
        """,
        (args.dimension, args.minimum, args.maximum),
    ).fetchall()
    for row in rows:
        qid = f" [{row['wikidata_qid']}]" if row["wikidata_qid"] else ""
        print(f"{row['value_base']:.6g}\t{row['label']}\t{row['value_type']}\t{row['subject_name']}{qid}")
    return 0


def cmd_nearest(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    row = conn.execute(
        f"""
        SELECT o.label, o.value_base, o.value_type, sub.canonical_name AS subject_name, sub.wikidata_qid
          FROM observations o
          JOIN dimensions d ON d.id = o.dimension_id
          JOIN subjects sub ON sub.id = o.subject_id
         WHERE d.slug = ?
           {selected_clause(args.selected_only)}
         ORDER BY ABS(LOG10(o.value_base) - LOG10(?)), o.id
         LIMIT 1
        """,
        (args.dimension, args.target),
    ).fetchone()
    if row is None:
        return 1
    qid = f" [{row['wikidata_qid']}]" if row["wikidata_qid"] else ""
    print(f"{row['value_base']:.6g}\t{row['label']}\t{row['value_type']}\t{row['subject_name']}{qid}")
    return 0


def cmd_dimension_stats(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    stats = conn.execute(
        """
        SELECT
            d.required_min_items,
            d.preferred_target_items,
            d.preferred_max_items,
            d.selection_bin_count,
            COUNT(*) AS observation_count,
            SUM(CASE WHEN o.display_eligible = 1 THEN 1 ELSE 0 END) AS candidate_count,
            SUM(CASE WHEN o.rationale IS NOT NULL THEN 1 ELSE 0 END) AS selected_count,
            MIN(o.value_base) AS min_value,
            MAX(o.value_base) AS max_value
          FROM observations o
          JOIN dimensions d ON d.id = o.dimension_id
         WHERE d.slug = ?
        """,
        (args.dimension,),
    ).fetchone()
    bin_stats = conn.execute(
        """
        SELECT COUNT(*) AS bin_count,
               SUM(CASE WHEN selected_observation_id IS NULL THEN 1 ELSE 0 END) AS empty_bin_count
          FROM coverage_bins cb
          JOIN dimensions d ON d.id = cb.dimension_id
         WHERE d.slug = ?
        """,
        (args.dimension,),
    ).fetchone()
    print(f"dimension\t{args.dimension}")
    print(f"required_min_items\t{stats['required_min_items'] or 0}")
    print(f"preferred_target_items\t{stats['preferred_target_items'] or 0}")
    print(f"preferred_max_items\t{stats['preferred_max_items'] or 0}")
    print(f"selection_bin_count\t{stats['selection_bin_count'] or 0}")
    print(f"observation_count\t{stats['observation_count']}")
    print(f"candidate_count\t{stats['candidate_count'] or 0}")
    print(f"selected_count\t{stats['selected_count'] or 0}")
    print(f"min_value\t{stats['min_value']:.6g}" if stats["min_value"] is not None else "min_value\t")
    print(f"max_value\t{stats['max_value']:.6g}" if stats["max_value"] is not None else "max_value\t")
    print(f"bin_count\t{bin_stats['bin_count'] or 0}")
    print(f"empty_bin_count\t{bin_stats['empty_bin_count'] or 0}")
    return 0


def cmd_subject(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    rows = conn.execute(
        """
        SELECT id, canonical_name, wikidata_qid, subject_type, summary, aliases_json
          FROM subjects
         WHERE id = ?
            OR canonical_name = ?
            OR canonical_name LIKE ?
         ORDER BY CASE WHEN id = ? THEN 0 WHEN canonical_name = ? THEN 1 ELSE 2 END, canonical_name
        """,
        (args.subject, args.subject, f"%{args.subject}%", args.subject, args.subject),
    ).fetchall()
    if not rows:
        return 1

    for row in rows:
        qid = row["wikidata_qid"] or ""
        print(f"subject\t{row['id']}\t{row['canonical_name']}\t{row['subject_type']}\t{qid}")
        if row["summary"]:
            print(f"summary\t{row['summary']}")
        observations = conn.execute(
            f"""
            SELECT d.slug AS dimension_slug, o.label, o.value_base, o.value_type
              FROM observations o
              JOIN dimensions d ON d.id = o.dimension_id
             WHERE o.subject_id = ?
               {selected_clause(args.selected_only)}
             ORDER BY d.slug, o.value_base, o.id
            """,
            (row["id"],),
        ).fetchall()
        for observation in observations:
            print(
                f"observation\t{observation['dimension_slug']}\t"
                f"{observation['value_base']:.6g}\t{observation['label']}\t{observation['value_type']}"
            )
    return 0


def cmd_observation(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    rows = conn.execute(
        """
        SELECT
            o.id,
            o.label,
            o.value_base,
            o.original_value_text,
            o.value_type,
            o.summary,
            o.rationale,
            o.review_status,
            o.display_status,
            o.quality_flags_json,
            d.slug AS dimension_slug,
            d.base_unit,
            sub.canonical_name AS subject_name,
            sub.wikidata_qid,
            oc.summary_short,
            oc.description_medium,
            oc.description_long,
            oc.facts_json
          FROM observations o
          JOIN dimensions d ON d.id = o.dimension_id
          JOIN subjects sub ON sub.id = o.subject_id
          LEFT JOIN observation_content oc ON oc.observation_id = o.id
         WHERE o.id = ?
            OR o.label = ?
            OR o.label LIKE ?
         ORDER BY CASE WHEN o.id = ? THEN 0 WHEN o.label = ? THEN 1 ELSE 2 END, o.id
        """,
        (args.observation, args.observation, f"%{args.observation}%", args.observation, args.observation),
    ).fetchall()
    if not rows:
        return 1

    for row in rows:
        print(
            f"observation\t{row['id']}\t{row['dimension_slug']}\t{row['value_base']:.6g}\t"
            f"{row['base_unit']}\t{row['label']}\t{row['value_type']}"
        )
        print(f"status\t{row['review_status']}\t{row['display_status']}")
        quality_flags = json.loads(row["quality_flags_json"] or "[]")
        if quality_flags:
            print(f"quality_flags\t{', '.join(quality_flags)}")
        print(f"subject\t{row['subject_name']}\t{row['wikidata_qid'] or ''}")
        if row["summary_short"]:
            print(f"summary_short\t{row['summary_short']}")
        if row["summary"]:
            print(f"summary\t{row['summary']}")
        facts = json.loads(row["facts_json"] or "{}")
        source_trace = facts.get("source_trace")
        if source_trace:
            print(f"source_method\t{source_trace.get('method', '')}")
            source_value_text = source_trace.get("source_value_text")
            source_unit = source_trace.get("source_unit")
            if source_value_text:
                print(f"source_value\t{format_source_value(source_value_text, source_unit)}")
            if source_trace.get("source_basis"):
                print(f"source_basis\t{source_trace['source_basis']}")
            if source_trace.get("conversion_note"):
                print(f"conversion_note\t{source_trace['conversion_note']}")
            if source_trace.get("derivation_note"):
                print(f"derivation_note\t{source_trace['derivation_note']}")
            if source_trace.get("source_locator"):
                print(f"source_locator\t{source_trace['source_locator']}")
            print(f"source_trace\t{json.dumps(source_trace, sort_keys=True)}")
        sources = conn.execute(
            """
            SELECT s.url, s.title, s.source_class, os.role
              FROM observation_sources os
              JOIN sources s ON s.id = os.source_id
             WHERE os.observation_id = ?
             ORDER BY
                CASE s.source_class
                    WHEN 'official_dataset' THEN 4
                    WHEN 'secondary_reference' THEN 3
                    WHEN 'wikidata' THEN 2
                    WHEN 'legacy_manual' THEN 1
                    ELSE 0
                END DESC,
                s.url
            """,
            (row["id"],),
        ).fetchall()
        for source in sources:
            print(f"source\t{source['source_class']}\t{source['role']}\t{source['title']}\t{source['url']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query the canonical Universe Scales dataset.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to the SQLite dataset.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    between = subparsers.add_parser("between", help="List observations whose value lies in a range.")
    between.add_argument("dimension")
    between.add_argument("minimum", type=float)
    between.add_argument("maximum", type=float)
    between.add_argument("--selected-only", action="store_true")
    between.set_defaults(func=cmd_between)

    nearest = subparsers.add_parser("nearest", help="Find the observation nearest a target value.")
    nearest.add_argument("dimension")
    nearest.add_argument("target", type=float)
    nearest.add_argument("--selected-only", action="store_true")
    nearest.set_defaults(func=cmd_nearest)

    stats = subparsers.add_parser("dimension-stats", help="Show coverage statistics for one dimension.")
    stats.add_argument("dimension")
    stats.set_defaults(func=cmd_dimension_stats)

    subject = subparsers.add_parser("subject", help="Show observations attached to a subject.")
    subject.add_argument("subject")
    subject.add_argument("--selected-only", action="store_true")
    subject.set_defaults(func=cmd_subject)

    observation = subparsers.add_parser("observation", help="Show one observation and its source trace.")
    observation.add_argument("observation")
    observation.set_defaults(func=cmd_observation)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    conn = open_db(args.db)
    try:
        return int(args.func(conn, args))
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
