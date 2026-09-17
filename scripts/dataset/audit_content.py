#!/usr/bin/env python3
"""Audit generated item descriptions against the museum-plaque style standard."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OBSERVATIONS = ROOT / "exports" / "json" / "observations.jsonl"

LOW_WORD_TARGET = 55
HIGH_WORD_TARGET = 120
HARD_HIGH_WORD_LIMIT = 150

GENERIC_PATTERNS = [
    re.compile(r"\bimportant in many\b", re.IGNORECASE),
    re.compile(r"\bvery (large|small|hot|cold|fast|slow)\b", re.IGNORECASE),
    re.compile(r"\bthis is important\b", re.IGNORECASE),
    re.compile(r"\bplays an important role\b", re.IGNORECASE),
]

METADATA_PATTERNS = [
    re.compile(r"\bsource[- ]side figure\b", re.IGNORECASE),
    re.compile(r"\bsource figure\b", re.IGNORECASE),
    re.compile(r"\bhere the quantity refers to\b", re.IGNORECASE),
    re.compile(r"\bbasis:\b", re.IGNORECASE),
    re.compile(r"\bconverted\b.*\bto\b", re.IGNORECASE),
]


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", text))


def has_unbalanced_math_delimiter(text: str) -> bool:
    positions = [match.start() for match in re.finditer(r"(?<!\\)\$", text)]
    index = 0
    while index < len(positions):
        start = positions[index]
        next_pos = positions[index + 1] if index + 1 < len(positions) else None
        following = text[start + 1 :].lstrip()
        looks_like_currency = bool(re.match(r"\d[\d,]*(?:\.\d+)?(?:\s|[.,;:)]|$)", following))
        if next_pos is None:
            if not looks_like_currency:
                return True
            index += 1
            continue

        segment = text[start + 1 : next_pos]
        has_math_marker = any(marker in segment for marker in ("\\", "^", "_", "=", r"\times", r"\approx"))
        is_simple_numeric_math = bool(re.fullmatch(r"\s*[+-]?\d[\d,]*(?:\.\d+)?(?:e[+-]?\d+)?\s*", segment, re.IGNORECASE))
        if has_math_marker or is_simple_numeric_math:
            index += 2
            continue

        # Treat paired currency mentions such as "$5 ... $10" as non-math.
        if looks_like_currency:
            index += 1
            continue
        return True
    return False


def audit_record(record: dict[str, Any]) -> list[str]:
    text = str(
        record.get("description_long")
        or record.get("description_medium")
        or record.get("summary_short")
        or record.get("summary")
        or ""
    ).strip()
    issues: list[str] = []
    count = word_count(text)

    if not text:
        issues.append("missing_description")
    elif count < LOW_WORD_TARGET:
        issues.append("short_description")
    elif count > HARD_HIGH_WORD_LIMIT:
        issues.append("too_long")
    elif count > HIGH_WORD_TARGET:
        issues.append("long_description")

    if any(pattern.search(text) for pattern in GENERIC_PATTERNS):
        issues.append("generic_language")
    if any(pattern.search(text) for pattern in METADATA_PATTERNS):
        issues.append("metadata_in_description")
    if "$" in text and has_unbalanced_math_delimiter(text):
        issues.append("unbalanced_math_delimiter")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit generated item descriptions.")
    parser.add_argument("--observations", default=str(DEFAULT_OBSERVATIONS), help="Path to observations.jsonl.")
    parser.add_argument("--dimension", action="append", default=[], help="Dimension slug to audit. Repeatable.")
    parser.add_argument("--all", action="store_true", help="Audit all observations, not just selected display observations.")
    parser.add_argument("--show", type=int, default=40, help="Number of issue records to print.")
    args = parser.parse_args()

    observations_path = Path(args.observations)
    dimensions = {slug.strip() for slug in args.dimension if slug.strip()}
    records = iter_jsonl(observations_path)

    issue_counts: Counter[str] = Counter()
    dimension_counts: dict[str, Counter[str]] = defaultdict(Counter)
    issue_rows: list[tuple[str, str, list[str], int]] = []
    audited_count = 0

    for record in records:
        if not args.all and not record.get("selected_for_display"):
            continue
        dimension = str(record.get("dimension_slug") or "")
        if dimensions and dimension not in dimensions:
            continue
        audited_count += 1
        issues = audit_record(record)
        if not issues:
            continue
        for issue in issues:
            issue_counts[issue] += 1
            dimension_counts[dimension][issue] += 1
        text = str(record.get("description_medium") or record.get("summary") or "")
        issue_rows.append((dimension, str(record.get("label") or ""), issues, word_count(text)))

    print(f"Audited observations: {audited_count}")
    print(f"Observations with issues: {len(issue_rows)}")
    if issue_counts:
        print("\nIssues:")
        for issue, count in issue_counts.most_common():
            print(f"- {issue}: {count}")

    if dimension_counts:
        print("\nBy dimension:")
        for dimension in sorted(dimension_counts):
            total = sum(dimension_counts[dimension].values())
            details = ", ".join(f"{issue}={count}" for issue, count in dimension_counts[dimension].most_common())
            print(f"- {dimension}: {total} ({details})")

    if issue_rows:
        print("\nSample records:")
        for dimension, label, issues, count in issue_rows[: max(0, args.show)]:
            print(f"- {dimension}/{label}: {', '.join(issues)} ({count} words)")

    return 1 if issue_rows else 0


if __name__ == "__main__":
    raise SystemExit(main())
