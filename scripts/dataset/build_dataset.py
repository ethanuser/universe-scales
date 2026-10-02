#!/usr/bin/env python3
"""Build the canonical Universe Scales dataset and derived exports."""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import yaml


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.dataset.raw_loader import load_raw_catalog  # noqa: E402


DATASET_DIR = ROOT / "dataset"
RAW_DIR = DATASET_DIR / "raw"
LEGACY_DATA_DIR = RAW_DIR / "legacy_yaml"
EXPORTS_DIR = ROOT / "exports"
EXPORT_SQLITE_DIR = EXPORTS_DIR / "sqlite"
EXPORT_JSON_DIR = EXPORTS_DIR / "json"
EXPORT_FRONTEND_DIR = EXPORTS_DIR / "frontend"
DIMENSIONS_EXPORT_DIR = EXPORT_JSON_DIR / "dimensions"
DIMENSION_CATALOG_EXPORT_PATH = EXPORT_JSON_DIR / "dimension_catalog.json"
CANONICAL_DB_PATH = DATASET_DIR / "universe_scales.sqlite"
SQLITE_EXPORT_PATH = EXPORT_SQLITE_DIR / "universe_scales.sqlite"
WRITER_PACKET_EXPORT_PATH = EXPORT_JSON_DIR / "writer_packets.jsonl"
CONTENT_EXPORT_PATH = EXPORT_JSON_DIR / "observation_content.jsonl"
LEGACY_FALLBACK_DIR = ROOT / "data"

DEFAULT_REQUIRED_MIN_ITEMS = 24
DEFAULT_PREFERRED_TARGET_ITEMS = 24
DEFAULT_PREFERRED_MAX_ITEMS = 24
DEFAULT_SELECTION_BIN_COUNT = 24

PRIMARY_SOURCE_CLASS_SCORE = {
    "official_dataset": 1.0,
    "secondary_reference": 0.75,
    "wikidata": 0.7,
    "legacy_manual": 0.55,
}

CATEGORY_RECOGNIZABILITY = {
    "human-scale": 0.95,
    "everyday": 0.9,
    "architecture": 0.88,
    "infrastructure": 0.85,
    "engineering": 0.82,
    "interface": 0.83,
    "telecommunications": 0.82,
    "media": 0.81,
    "computing": 0.8,
    "storage": 0.78,
    "geography": 0.8,
    "astronomy": 0.78,
    "cosmology": 0.72,
    "fields": 0.72,
    "materials": 0.7,
    "biology": 0.68,
    "molecule": 0.6,
    "particle": 0.55,
    "reference": 0.72,
}

VALID_REVIEW_STATUSES = {
    "candidate",
    "accepted",
    "needs_source",
    "needs_description",
    "deprecated",
    "excluded",
}

VALID_DISPLAY_STATUSES = {
    "display",
    "hidden",
}


DISPLAY_PROVENANCE_QUALIFIERS = {
    "derivation", "derivation_note", "conversion_note", "source_url", "source_basis",
    "source_value_text", "source_unit",
}
DISPLAY_MEASUREMENT_QUALIFIERS = {"measurement", "measure"}
# Only known quantity descriptions are redundant. Unknown measurement wording
# stays in the identity, so conditions such as static/kinetic are never erased.
DISPLAY_GENERIC_MEASUREMENTS = {
    "angular-velocity": {
        "angular speed", "rotational speed", "rotational velocity", "rotation rate",
        "blade speed", "blade rotation", "clock hand rotation",
    },
    "friction-coefficient": {"coefficient of friction"},
}


def normalize_display_text(value: Any) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value)).casefold().split())


def slugify(value: str) -> str:
    value = value.lower().strip()
    chars = []
    previous_dash = False
    for char in value:
        if char.isalnum():
            chars.append(char)
            previous_dash = False
        else:
            if not previous_dash:
                chars.append("-")
                previous_dash = True
    slug = "".join(chars).strip("-")
    return slug or "item"


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def derive_publisher(url: str) -> tuple[str | None, str | None]:
    if url.startswith("repo://"):
        return "universe-scales repo", "MIT"

    netloc = urlparse(url).netloc.lower()
    if "wikipedia.org" in netloc:
        return "Wikipedia", "CC BY-SA 4.0"
    if "wikidata.org" in netloc:
        return "Wikidata", "CC0 1.0"
    if "nasa.gov" in netloc:
        return "NASA", None
    if "esa.int" in netloc:
        return "ESA", None
    if "jaxa.jp" in netloc:
        return "JAXA", None
    if netloc:
        return netloc, None
    return None, None


def derive_title(url: str, fallback: str) -> str:
    if url.startswith("repo://"):
        return url.replace("repo://", "")
    parsed = urlparse(url)
    candidate = unquote(parsed.path.rstrip("/").split("/")[-1]).replace("_", " ")
    return candidate or fallback


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def first_sentence(text: str) -> str:
    normalized = " ".join(text.split())
    if not normalized:
        return ""
    for separator in (". ", "! ", "? "):
        if separator in normalized:
            head = normalized.split(separator, 1)[0].strip()
            if head:
                return head.rstrip(".!?") + "."
    return normalized


def clean_trace_text(value: Any) -> Any:
    if value is None or isinstance(value, bool) or is_number(value):
        return value
    text = str(value)
    text = text.replace("\u0007", r"\approx ")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def format_source_value(source_value_text: Any, source_unit: Any) -> str:
    value_text = str(source_value_text or "").strip()
    unit_text = str(source_unit or "").strip()
    if not unit_text or not value_text:
        return value_text

    numeric_candidate = value_text.replace("+", "").replace("-", "").replace(".", "").replace("e", "").replace("E", "")
    if numeric_candidate.isdigit():
        return f"{value_text} {unit_text}"
    return value_text


def latexify_inline_math(value: Any) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        return ""
    text = text.replace("×", r" \times ")
    text = text.replace("*", r" \times ")
    text = text.replace("pi", r"\pi")
    text = text.replace(" uA", r" \,\mu\mathrm{A}")
    text = text.replace(" uC", r" \,\mu\mathrm{C}")
    text = text.replace(" uF", r" \,\mu\mathrm{F}")
    text = text.replace(" uK", r" \,\mu\mathrm{K}")
    text = text.replace(" pA", r" \,\mathrm{pA}")
    text = text.replace(" nA", r" \,\mathrm{nA}")
    text = text.replace(" mA", r" \,\mathrm{mA}")
    text = text.replace(" kA", r" \,\mathrm{kA}")
    text = text.replace(" MA", r" \,\mathrm{MA}")
    text = text.replace(" C", r" \,\mathrm{C}")
    text = text.replace(" A", r" \,\mathrm{A}")
    text = text.replace(" V", r" \,\mathrm{V}")
    text = text.replace(" K", r" \,\mathrm{K}")
    text = text.replace(" W", r" \,\mathrm{W}")
    text = text.replace(" F", r" \,\mathrm{F}")
    text = text.replace(" deg", r"^\circ")
    return re.sub(r"(?<![A-Za-z])([+-]?\d+(?:\.\d+)?)e([+-]?\d+)", r"\1 \\times 10^{\2}", text)


def choose_subject_canonical_name(existing_name: str, candidate_name: str) -> str:
    existing = (existing_name or "").strip()
    candidate = (candidate_name or "").strip()
    if not existing:
        return candidate
    if not candidate:
        return existing

    existing_lower = existing.lower()
    candidate_lower = candidate.lower()

    if existing_lower == candidate_lower:
        return existing
    if candidate_lower in existing_lower:
        return candidate
    if existing_lower in candidate_lower:
        return existing
    return existing


def is_reference_category(category: Any) -> bool:
    return str(category or "").strip().lower() == "reference"


def normalize_review_status(value: Any, *, default: str = "accepted") -> str:
    status = str(value or default).strip().lower().replace(" ", "_")
    return status if status in VALID_REVIEW_STATUSES else default


def normalize_display_status(value: Any, *, display_eligible: bool) -> str:
    default = "display" if display_eligible else "hidden"
    status = str(value or default).strip().lower().replace(" ", "_")
    return status if status in VALID_DISPLAY_STATUSES else default


def normalize_quality_flags(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_flags = [value]
    elif isinstance(value, list):
        raw_flags = value
    else:
        raw_flags = []
    flags = []
    for flag in raw_flags:
        normalized = str(flag).strip().lower().replace(" ", "_")
        if normalized and normalized not in flags:
            flags.append(normalized)
    return flags


class DatasetBuilder:
    def __init__(self) -> None:
        self.raw_catalog = load_raw_catalog()
        self.flagship_dimension_configs = list(self.raw_catalog.flagship_dimensions)
        self.flagship_dimensions = [str(item["slug"]) for item in self.flagship_dimension_configs]
        self.flagship_config_by_slug = {str(item["slug"]): item for item in self.flagship_dimension_configs}
        self.content_overrides_by_subject: dict[tuple[str, str], dict[str, Any]] = {}
        self.content_overrides_by_label: dict[tuple[str, str], dict[str, Any]] = {}
        for record in self.raw_catalog.content_overrides:
            dimension = str(record.get("dimension") or "")
            subject_key = record.get("subject_key")
            if dimension and subject_key:
                self.content_overrides_by_subject[(dimension, str(subject_key))] = record
            item_name = record.get("item_name")
            if dimension and item_name:
                self.content_overrides_by_label[(dimension, str(item_name))] = record

        self.conn: sqlite3.Connection | None = None
        self.dimension_export_meta: dict[str, dict[str, Any]] = {}
        self.dimension_lookup: dict[str, dict[str, Any]] = {}
        self.subjects_by_key: dict[str, dict[str, Any]] = {}
        self.sources_by_url: dict[str, str] = {}
        self.observation_meta: dict[str, dict[str, Any]] = {}
        self.coverage_report: dict[str, Any] = {}

    def run(self) -> None:
        self.prepare_directories()
        self.build_schema()
        self.import_legacy_dimensions()
        self.import_new_dimensions()
        self.import_curated_observations()
        self.apply_wikidata_cache()
        self.compute_flagship_selection()
        self.write_exports()

    def prepare_directories(self) -> None:
        DATASET_DIR.mkdir(exist_ok=True)
        RAW_DIR.mkdir(exist_ok=True)
        EXPORTS_DIR.mkdir(exist_ok=True)
        EXPORT_SQLITE_DIR.mkdir(parents=True, exist_ok=True)
        EXPORT_JSON_DIR.mkdir(parents=True, exist_ok=True)
        DIMENSIONS_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        EXPORT_FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

    def legacy_source_dir(self) -> Path:
        return LEGACY_DATA_DIR if LEGACY_DATA_DIR.exists() else LEGACY_FALLBACK_DIR

    def build_schema(self) -> None:
        if CANONICAL_DB_PATH.exists():
            CANONICAL_DB_PATH.unlink()
        self.conn = sqlite3.connect(CANONICAL_DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE dimensions (
                id TEXT PRIMARY KEY,
                slug TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                base_unit TEXT NOT NULL,
                quantity_kind TEXT,
                stable_flag INTEGER NOT NULL,
                description TEXT,
                description_format TEXT NOT NULL DEFAULT 'markdown',
                scale_mode TEXT NOT NULL DEFAULT 'log',
                frontend_group TEXT,
                frontend_group_label TEXT,
                frontend_order INTEGER NOT NULL DEFAULT 1000,
                required_min_items INTEGER NOT NULL DEFAULT 24,
                preferred_target_items INTEGER NOT NULL DEFAULT 24,
                preferred_max_items INTEGER NOT NULL DEFAULT 24,
                selection_bin_count INTEGER NOT NULL DEFAULT 24
            );

            CREATE TABLE units (
                id TEXT PRIMARY KEY,
                dimension_id TEXT NOT NULL REFERENCES dimensions(id),
                name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                to_base_factor REAL NOT NULL,
                offset REAL NOT NULL DEFAULT 0,
                description TEXT
            );

            CREATE TABLE subjects (
                id TEXT PRIMARY KEY,
                subject_type TEXT NOT NULL,
                canonical_name TEXT NOT NULL,
                wikidata_qid TEXT,
                synthetic_slug TEXT,
                summary TEXT,
                aliases_json TEXT NOT NULL DEFAULT '[]'
            );

            CREATE TABLE observations (
                id TEXT PRIMARY KEY,
                subject_id TEXT NOT NULL REFERENCES subjects(id),
                dimension_id TEXT NOT NULL REFERENCES dimensions(id),
                label TEXT NOT NULL,
                value_base REAL NOT NULL,
                original_value_text TEXT,
                value_type TEXT NOT NULL,
                lower_bound REAL,
                upper_bound REAL,
                uncertainty_text TEXT,
                snapshot_date TEXT,
                display_eligible INTEGER NOT NULL,
                selection_score REAL,
                rationale TEXT,
                summary TEXT,
                category TEXT,
                review_status TEXT NOT NULL DEFAULT 'accepted',
                display_status TEXT NOT NULL DEFAULT 'display',
                quality_flags_json TEXT NOT NULL DEFAULT '[]'
            );

            CREATE TABLE observation_content (
                id TEXT PRIMARY KEY,
                observation_id TEXT NOT NULL UNIQUE REFERENCES observations(id),
                content_origin TEXT NOT NULL,
                content_status TEXT NOT NULL,
                content_format TEXT NOT NULL DEFAULT 'markdown',
                summary_short TEXT,
                description_medium TEXT,
                description_long TEXT,
                hook TEXT,
                caveats TEXT,
                facts_json TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE observation_qualifiers (
                id TEXT PRIMARY KEY,
                observation_id TEXT NOT NULL REFERENCES observations(id),
                key TEXT NOT NULL,
                value_text TEXT,
                value_numeric REAL,
                unit_text TEXT
            );

            CREATE TABLE sources (
                id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                publisher TEXT,
                license_text TEXT,
                accessed_at TEXT,
                source_class TEXT NOT NULL
            );

            CREATE TABLE observation_sources (
                id TEXT PRIMARY KEY,
                observation_id TEXT NOT NULL REFERENCES observations(id),
                source_id TEXT NOT NULL REFERENCES sources(id),
                role TEXT NOT NULL,
                note TEXT
            );

            CREATE TABLE coverage_bins (
                id TEXT PRIMARY KEY,
                dimension_id TEXT NOT NULL REFERENCES dimensions(id),
                bin_index INTEGER NOT NULL,
                log10_min REAL NOT NULL,
                log10_max REAL NOT NULL,
                selected_observation_id TEXT
            );

            CREATE INDEX idx_observations_dimension_value ON observations(dimension_id, value_base, id);
            CREATE INDEX idx_observations_subject ON observations(subject_id, id);
            CREATE INDEX idx_observation_content_observation ON observation_content(observation_id);
            CREATE INDEX idx_observation_sources_observation ON observation_sources(observation_id, source_id);
            CREATE INDEX idx_coverage_bins_dimension ON coverage_bins(dimension_id, bin_index);
            """
        )

    @property
    def db(self) -> sqlite3.Connection:
        if self.conn is None:
            raise RuntimeError("Database not initialized")
        return self.conn

    def dimension_preferences(self, slug: str) -> dict[str, int]:
        raw = self.flagship_config_by_slug.get(slug, {})
        profile = self.dimension_profile(slug)
        required_min = int(raw.get("required_min_items", profile.get("required_min_items", DEFAULT_REQUIRED_MIN_ITEMS)))
        preferred_target = int(
            raw.get("preferred_target_items", profile.get("preferred_target_items", required_min or DEFAULT_PREFERRED_TARGET_ITEMS))
        )
        preferred_max = int(
            raw.get("preferred_max_items", profile.get("preferred_max_items", max(preferred_target, required_min, DEFAULT_PREFERRED_MAX_ITEMS)))
        )
        selection_bin_count = int(raw.get("selection_bin_count", profile.get("selection_bin_count", DEFAULT_SELECTION_BIN_COUNT)))
        return {
            "required_min_items": required_min,
            "preferred_target_items": max(required_min, preferred_target),
            "preferred_max_items": max(preferred_max, preferred_target, required_min),
            "selection_bin_count": max(1, selection_bin_count),
        }

    def dimension_profile(self, slug: str) -> dict[str, Any]:
        return deepcopy(self.raw_catalog.dimension_profiles.get(slug, {}))

    def dimension_name(self, slug: str, fallback: str) -> str:
        profile = self.dimension_profile(slug)
        return str(profile.get("name") or fallback)

    def dimension_scale_mode(self, slug: str) -> str:
        profile = self.dimension_profile(slug)
        mode = str(profile.get("scale_mode", "log")).strip().lower()
        return mode if mode in {"log", "linear"} else "log"

    def merge_units(self, slug: str, units: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        seen_names: set[str] = set()
        for unit in units + list(self.dimension_profile(slug).get("extra_units", [])):
            unit_name = str(unit["name"]).strip().lower()
            if unit_name in seen_names:
                continue
            seen_names.add(unit_name)
            merged.append(deepcopy(unit))
        return merged

    def upsert_dimension(
        self,
        slug: str,
        *,
        name: str,
        base_unit: str,
        quantity_kind: str,
        stable_flag: bool,
        description: str,
        units: list[dict[str, Any]],
        export_meta: dict[str, Any],
        preferences: dict[str, int],
        profile: dict[str, Any],
    ) -> str:
        dimension_id = f"dim:{slug}"
        description_format = str(profile.get("description_format", "markdown"))
        scale_mode = self.dimension_scale_mode(slug)
        frontend_group = profile.get("frontend_group")
        frontend_group_label = profile.get("frontend_group_label")
        frontend_order = int(profile.get("frontend_order", 1000))
        self.db.execute(
            """
            INSERT OR REPLACE INTO dimensions (
                id, slug, name, base_unit, quantity_kind, stable_flag, description,
                description_format, scale_mode, frontend_group, frontend_group_label, frontend_order,
                required_min_items, preferred_target_items, preferred_max_items, selection_bin_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dimension_id,
                slug,
                name,
                base_unit,
                quantity_kind,
                1 if stable_flag else 0,
                description,
                description_format,
                scale_mode,
                frontend_group,
                frontend_group_label,
                frontend_order,
                preferences["required_min_items"],
                preferences["preferred_target_items"],
                preferences["preferred_max_items"],
                preferences["selection_bin_count"],
            ),
        )
        self.db.execute("DELETE FROM units WHERE dimension_id = ?", (dimension_id,))
        for unit in units:
            unit_id = f"unit:{slug}:{slugify(unit['name'])}"
            self.db.execute(
                """
                INSERT INTO units (id, dimension_id, name, symbol, to_base_factor, offset, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    unit_id,
                    dimension_id,
                    unit["name"],
                    unit["symbol"],
                    float(unit["conversion_factor"]),
                    float(unit.get("offset", 0.0)),
                    unit.get("description"),
                ),
            )

        export_payload = deepcopy(export_meta)
        export_payload.update(preferences)
        export_payload["description_format"] = description_format
        export_payload["scale_mode"] = scale_mode
        export_payload["frontend_group"] = frontend_group
        export_payload["frontend_group_label"] = frontend_group_label
        export_payload["frontend_order"] = frontend_order
        self.dimension_export_meta[slug] = export_payload
        self.dimension_lookup[slug] = {
            "id": dimension_id,
            "slug": slug,
            "name": name,
            "base_unit": base_unit,
            "description_format": description_format,
            "scale_mode": scale_mode,
            "frontend_group": frontend_group,
            "frontend_group_label": frontend_group_label,
            "frontend_order": frontend_order,
            **preferences,
        }
        return dimension_id

    def import_legacy_dimensions(self) -> None:
        for yaml_path in sorted(self.legacy_source_dir().glob("*.yaml")):
            payload = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            slug = payload["dimension"]
            profile = self.dimension_profile(slug)
            quantity_kind = slug.replace("-", "_")
            base_units = payload.get("units") or [
                {
                    "name": payload["base_unit"],
                    "symbol": payload["base_unit"],
                    "conversion_factor": 1.0,
                    "description": f"Canonical base unit for {slug}.",
                }
            ]
            units = self.merge_units(slug, base_units)
            preferences = self.dimension_preferences(slug)
            export_meta = {
                "dimension": slug,
                "base_unit": payload["base_unit"],
                "dimension_description": payload.get("dimension_description", ""),
                "related_resources": deepcopy(payload.get("related_resources", [])),
                "show_limitations": payload.get("show_limitations", True),
                "units": deepcopy(units),
            }
            dimension_id = self.upsert_dimension(
                slug,
                name=self.dimension_name(slug, slug.replace("-", " ").title()),
                base_unit=payload["base_unit"],
                quantity_kind=quantity_kind,
                stable_flag=True,
                description=payload.get("dimension_description", ""),
                units=units,
                export_meta=export_meta,
                preferences=preferences,
                profile=profile,
            )
            source_id = self.ensure_source(
                url=f"repo://{yaml_path.relative_to(ROOT)}",
                title=str(yaml_path.relative_to(ROOT)),
                source_type="local_file",
                source_class="legacy_manual",
                publisher="universe-scales repo",
                license_text="MIT",
                accessed_at=None,
            )
            for item in payload.get("items", []):
                self.import_legacy_item(
                    yaml_path=yaml_path,
                    dimension_id=dimension_id,
                    dimension_slug=slug,
                    item=item,
                    seed_source_id=source_id,
                )

    def import_legacy_item(
        self,
        *,
        yaml_path: Path,
        dimension_id: str,
        dimension_slug: str,
        item: dict[str, Any],
        seed_source_id: str,
    ) -> None:
        name = item["name"]
        override = self.raw_catalog.legacy_overrides.get(dimension_slug, {}).get(name, {})
        subject_key = str(override.get("subject_key", f"scenario:{dimension_slug}:{slugify(name)}"))
        subject_type = str(override.get("subject_type", "scenario"))
        summary = item.get("description", "").strip() or name
        subject_id = self.ensure_subject(
            subject_key=subject_key,
            subject_type=subject_type,
            canonical_name=name,
            summary=summary,
            aliases=[],
            wikidata_key=override.get("wikidata_key"),
        )

        value_base = float(item["value"])
        observation_id = self.make_observation_id(dimension_slug, subject_key)
        value_type = str(override.get("value_type", "derived" if subject_type == "scenario" else "measured"))
        qualifiers = deepcopy(override.get("qualifiers", {}))
        display_eligible = bool(override.get("display_eligible", True))
        review_status = normalize_review_status(override.get("review_status"))
        display_status = normalize_display_status(override.get("display_status"), display_eligible=display_eligible)
        quality_flags = normalize_quality_flags(override.get("quality_flags"))
        if review_status in {"deprecated", "excluded"} or display_status == "hidden":
            display_eligible = False
        category = override.get("category", self.infer_category(name, dimension_slug))
        external_url = item.get("source")
        content = self.resolve_content_seed(
            dimension_slug=dimension_slug,
            subject_key=subject_key,
            label=name,
            default_summary=summary,
            default_description=summary,
            value_type=value_type,
            qualifiers=qualifiers,
            default_origin=f"legacy_seed:{yaml_path.relative_to(ROOT)}",
            facts={
                "ingest_source": str(yaml_path.relative_to(ROOT)),
                "legacy_item_name": name,
            },
            source_trace=self.build_source_trace(
                source_url=external_url,
                value_type=value_type,
                original_value_text=str(item["value"]),
                qualifiers=qualifiers,
                raw_payload=override,
                legacy=True,
            ),
        )
        observation_id = self.insert_observation(
            observation_id=observation_id,
            subject_id=subject_id,
            dimension_id=dimension_id,
            label=name,
            value_base=value_base,
            original_value_text=str(item["value"]),
            value_type=value_type,
            lower_bound=None,
            upper_bound=None,
            uncertainty_text=None,
            snapshot_date=None,
            display_eligible=display_eligible,
            summary=summary,
            category=category,
            qualifiers=qualifiers,
            content=content,
            review_status=review_status,
            display_status=display_status,
            quality_flags=quality_flags,
        )

        if external_url:
            publisher, license_text = derive_publisher(external_url)
            external_source_id = self.ensure_source(
                url=external_url,
                title=derive_title(external_url, name),
                source_type="web_page",
                source_class="secondary_reference",
                publisher=publisher,
                license_text=license_text,
                accessed_at=None,
            )
            self.link_observation_source(observation_id, external_source_id, role="external_source", note=None)
        self.link_observation_source(
            observation_id,
            seed_source_id,
            role="legacy_seed",
            note=str(yaml_path.relative_to(ROOT)),
        )

    def import_new_dimensions(self) -> None:
        for slug, payload in self.raw_catalog.dimension_catalog.items():
            profile = self.dimension_profile(slug)
            preferences = self.dimension_preferences(slug)
            units = self.merge_units(slug, deepcopy(payload["units"]))
            self.upsert_dimension(
                slug,
                name=self.dimension_name(slug, payload["name"]),
                base_unit=payload["base_unit"],
                quantity_kind=payload["quantity_kind"],
                stable_flag=bool(payload["stable_flag"]),
                description=payload["dimension_description"],
                units=units,
                export_meta={
                    "dimension": slug,
                    "base_unit": payload["base_unit"],
                    "dimension_description": payload["dimension_description"],
                    "related_resources": deepcopy(payload["related_resources"]),
                    "show_limitations": payload["show_limitations"],
                    "units": units,
                },
                preferences=preferences,
                profile=profile,
            )

    def import_curated_observations(self) -> None:
        for payload in self.raw_catalog.curated_observations:
            if is_reference_category(payload.get("category")):
                continue
            dimension_slug = str(payload["dimension"])
            dimension_id = self.dimension_lookup[dimension_slug]["id"]
            summary = str(payload["summary"])
            subject_key = str(payload["subject_key"])
            subject_id = self.ensure_subject(
                subject_key=subject_key,
                subject_type=str(payload["subject_type"]),
                canonical_name=str(payload["canonical_name"]),
                summary=summary,
                aliases=list(payload.get("aliases", [])),
                wikidata_key=payload.get("wikidata_key"),
            )
            observation_id = self.make_observation_id(dimension_slug, subject_key)
            content = self.resolve_content_seed(
                dimension_slug=dimension_slug,
                subject_key=subject_key,
                label=str(payload["canonical_name"]),
                default_summary=summary,
                default_description=summary,
                value_type=str(payload["value_type"]),
                qualifiers=deepcopy(payload.get("qualifiers", {})),
                default_origin=f"curated_seed:{payload['_raw_path']}",
                facts={
                    "ingest_source": payload["_raw_path"],
                    "canonical_name": payload["canonical_name"],
                },
                source_trace=self.build_source_trace(
                    source_url=str(payload["source_url"]),
                    value_type=str(payload["value_type"]),
                    original_value_text=str(payload.get("original_value_text") or payload["value_base"]),
                    qualifiers=deepcopy(payload.get("qualifiers", {})),
                    raw_payload=payload,
                ),
            )
            display_eligible = bool(payload.get("display_eligible", True))
            review_status = normalize_review_status(payload.get("review_status"))
            display_status = normalize_display_status(payload.get("display_status"), display_eligible=display_eligible)
            quality_flags = normalize_quality_flags(payload.get("quality_flags"))
            if review_status in {"deprecated", "excluded"} or display_status == "hidden":
                display_eligible = False
            observation_id = self.insert_observation(
                observation_id=observation_id,
                subject_id=subject_id,
                dimension_id=dimension_id,
                label=str(payload["canonical_name"]),
                value_base=float(payload["value_base"]),
                original_value_text=str(payload.get("original_value_text") or payload["value_base"]),
                value_type=str(payload["value_type"]),
                lower_bound=payload.get("lower_bound"),
                upper_bound=payload.get("upper_bound"),
                uncertainty_text=payload.get("uncertainty_text"),
                snapshot_date=payload.get("snapshot_date"),
                display_eligible=display_eligible,
                summary=summary,
                category=payload.get("category"),
                qualifiers=deepcopy(payload.get("qualifiers", {})),
                recognizability=payload.get("recognizability"),
                definition_clarity=payload.get("definition_clarity"),
                source_class=payload.get("source_class", "secondary_reference"),
                content=content,
                review_status=review_status,
                display_status=display_status,
                quality_flags=quality_flags,
            )
            external_url = str(payload["source_url"])
            source_class = str(payload.get("source_class", "secondary_reference"))
            publisher, license_text = derive_publisher(external_url)
            source_id = self.ensure_source(
                url=external_url,
                title=derive_title(external_url, str(payload["canonical_name"])),
                source_type="web_page",
                source_class=source_class,
                publisher=publisher,
                license_text=license_text,
                accessed_at=None,
            )
            self.link_observation_source(observation_id, source_id, role="external_source", note=None)

            curation_source_id = self.ensure_source(
                url=f"repo://{payload['_raw_path']}",
                title=payload["_raw_path"],
                source_type="local_file",
                source_class="legacy_manual",
                publisher="universe-scales repo",
                license_text="MIT",
                accessed_at=None,
            )
            self.link_observation_source(observation_id, curation_source_id, role="curation_manifest", note=None)

    def ensure_source(
        self,
        *,
        url: str,
        title: str,
        source_type: str,
        source_class: str,
        publisher: str | None,
        license_text: str | None,
        accessed_at: str | None,
    ) -> str:
        if url in self.sources_by_url:
            return self.sources_by_url[url]
        source_id = f"src:{slugify(url)}"
        candidate_id = source_id
        suffix = 2
        while True:
            existing = self.db.execute("SELECT url FROM sources WHERE id = ?", (candidate_id,)).fetchone()
            if existing is None or existing[0] == url:
                source_id = candidate_id
                break
            candidate_id = f"{source_id}-{suffix}"
            suffix += 1
        self.db.execute(
            """
            INSERT INTO sources (id, source_type, title, url, publisher, license_text, accessed_at, source_class)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (source_id, source_type, title, url, publisher, license_text, accessed_at, source_class),
        )
        self.sources_by_url[url] = source_id
        return source_id

    def ensure_subject(
        self,
        *,
        subject_key: str,
        subject_type: str,
        canonical_name: str,
        summary: str,
        aliases: list[str],
        wikidata_key: str | None,
    ) -> str:
        if subject_key in self.subjects_by_key:
            existing = self.subjects_by_key[subject_key]
            merged_aliases = sorted(set(existing["aliases"]) | set(aliases))
            existing["aliases"] = merged_aliases
            if not existing.get("wikidata_key") and wikidata_key:
                existing["wikidata_key"] = wikidata_key
            current_summary = self.db.execute("SELECT summary FROM subjects WHERE id = ?", (existing["id"],)).fetchone()[0]
            replacement_summary = current_summary
            if (not current_summary or current_summary == existing["canonical_name"]) and summary:
                replacement_summary = summary
            if existing["canonical_name"] == current_summary and canonical_name:
                replacement_summary = summary or replacement_summary
            if canonical_name:
                existing["canonical_name"] = choose_subject_canonical_name(existing["canonical_name"], canonical_name)
            self.db.execute(
                """
                UPDATE subjects
                   SET canonical_name = ?, summary = ?, aliases_json = ?
                 WHERE id = ?
                """,
                (existing["canonical_name"], replacement_summary, json_dumps(merged_aliases), existing["id"]),
            )
            return existing["id"]

        subject_id = f"sub:{slugify(subject_key)}"
        synthetic_slug = None
        if subject_type == "scenario":
            synthetic_slug = subject_key.split(":", 1)[-1]
        self.db.execute(
            """
            INSERT INTO subjects (id, subject_type, canonical_name, wikidata_qid, synthetic_slug, summary, aliases_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (subject_id, subject_type, canonical_name, None, synthetic_slug, summary, json_dumps(sorted(set(aliases)))),
        )
        self.subjects_by_key[subject_key] = {
            "id": subject_id,
            "aliases": sorted(set(aliases)),
            "wikidata_key": wikidata_key,
            "canonical_name": canonical_name,
        }
        return subject_id

    def apply_wikidata_cache(self) -> None:
        for subject_key, subject in self.subjects_by_key.items():
            wikidata_key = subject.get("wikidata_key")
            if not wikidata_key:
                continue
            cached = self.raw_catalog.wikidata_subjects.get(str(wikidata_key))
            if not cached:
                continue
            aliases = sorted(set(subject["aliases"]) | set(cached.get("aliases", [])))
            canonical_name = cached.get("canonical_name") or subject.get("canonical_name")
            self.db.execute(
                """
                UPDATE subjects
                   SET wikidata_qid = ?, aliases_json = ?, canonical_name = ?
                 WHERE id = ?
                """,
                (
                    cached["wikidata_qid"],
                    json_dumps(aliases),
                    canonical_name,
                    subject["id"],
                ),
            )
            subject["aliases"] = aliases
            subject["canonical_name"] = canonical_name

    def make_observation_id(self, dimension_slug: str, subject_key: str) -> str:
        base = f"obs:{dimension_slug}:{slugify(subject_key)}"
        counter = 1
        candidate = base
        while candidate in self.observation_meta:
            counter += 1
            candidate = f"{base}:{counter}"
        return candidate

    def augment_default_description(
        self,
        base_text: str,
        value_type: str,
        qualifiers: dict[str, Any],
        source_trace: dict[str, Any] | None = None,
    ) -> str:
        return " ".join((base_text or "").split()).strip()

    def build_source_trace(
        self,
        *,
        source_url: str | None,
        value_type: str,
        original_value_text: str | None,
        qualifiers: dict[str, Any],
        raw_payload: dict[str, Any] | None = None,
        legacy: bool = False,
    ) -> dict[str, Any]:
        payload = raw_payload or {}
        derivation = payload.get("derivation_note") or qualifiers.get("derivation")
        source_basis = payload.get("source_basis")
        source_value_text = payload.get("source_value_text")
        source_unit = payload.get("source_unit")
        conversion_note = payload.get("conversion_note")
        source_locator = payload.get("source_locator")

        if derivation or value_type == "derived":
            method = "derived"
        elif conversion_note:
            method = "converted"
        elif legacy:
            method = "legacy_seed"
        else:
            method = "direct"

        trace = {
            "method": method,
            "source_url": source_url,
            "source_basis": clean_trace_text(source_basis),
            "source_value_text": clean_trace_text(source_value_text),
            "source_unit": clean_trace_text(source_unit),
            "conversion_note": clean_trace_text(conversion_note),
            "derivation_note": clean_trace_text(derivation),
            "source_locator": clean_trace_text(source_locator),
            "original_value_text": clean_trace_text(original_value_text),
        }
        return {key: value for key, value in trace.items() if value not in (None, "", [])}

    def resolve_content_seed(
        self,
        *,
        dimension_slug: str,
        subject_key: str,
        label: str,
        default_summary: str,
        default_description: str,
        value_type: str,
        qualifiers: dict[str, Any],
        default_origin: str,
        facts: dict[str, Any] | None = None,
        source_trace: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        override = self.content_overrides_by_subject.get((dimension_slug, subject_key))
        if override is None:
            override = self.content_overrides_by_label.get((dimension_slug, label))

        summary_short = str((override or {}).get("summary_short") or first_sentence(default_summary or label))
        description_medium = str(
            (override or {}).get("description_medium")
            or self.augment_default_description(
                default_description or default_summary or summary_short,
                value_type,
                qualifiers,
                source_trace=source_trace,
            )
            or summary_short
        )
        description_long = (override or {}).get("description_long")
        hook = (override or {}).get("hook")
        caveats = (override or {}).get("caveats")
        content_status = str((override or {}).get("content_status") or "seeded")
        content_origin = str((override or {}).get("content_origin") or (override or {}).get("_raw_path") or default_origin)

        merged_facts = deepcopy(facts or {})
        if source_trace:
            merged_facts["source_trace"] = source_trace
        override_facts = (override or {}).get("facts")
        if isinstance(override_facts, dict):
            merged_facts.update(deepcopy(override_facts))

        return {
            "content_origin": content_origin,
            "content_status": content_status,
            "content_format": str((override or {}).get("content_format") or "markdown"),
            "summary_short": summary_short,
            "description_medium": description_medium,
            "description_long": description_long,
            "hook": hook,
            "caveats": caveats,
            "facts": merged_facts,
        }

    def insert_observation(
        self,
        *,
        observation_id: str,
        subject_id: str,
        dimension_id: str,
        label: str,
        value_base: float,
        original_value_text: str,
        value_type: str,
        lower_bound: float | None,
        upper_bound: float | None,
        uncertainty_text: str | None,
        snapshot_date: str | None,
        display_eligible: bool,
        summary: str,
        category: str | None,
        qualifiers: dict[str, Any],
        content: dict[str, Any],
        review_status: str,
        display_status: str,
        quality_flags: list[str],
        recognizability: float | None = None,
        definition_clarity: float | None = None,
        source_class: str | None = None,
    ) -> str:
        # Keep source observations intact; deduplicate only the display selection.
        self.db.execute(
            """
            INSERT INTO observations (
                id, subject_id, dimension_id, label, value_base, original_value_text, value_type,
                lower_bound, upper_bound, uncertainty_text, snapshot_date, display_eligible,
                selection_score, rationale, summary, category, review_status, display_status,
                quality_flags_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?)
            """,
            (
                observation_id,
                subject_id,
                dimension_id,
                label,
                value_base,
                original_value_text,
                value_type,
                lower_bound,
                upper_bound,
                uncertainty_text,
                snapshot_date,
                1 if display_eligible else 0,
                summary,
                category,
                review_status,
                display_status,
                json_dumps(quality_flags),
            ),
        )

        content_id = f"oc:{observation_id}"
        self.db.execute(
            """
            INSERT INTO observation_content (
                id, observation_id, content_origin, content_status, content_format, summary_short,
                description_medium, description_long, hook, caveats, facts_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                content_id,
                observation_id,
                content["content_origin"],
                content["content_status"],
                content["content_format"],
                content["summary_short"],
                content["description_medium"],
                content.get("description_long"),
                content.get("hook"),
                content.get("caveats"),
                json_dumps(content.get("facts", {})),
            ),
        )

        for index, (key, raw_value) in enumerate(sorted(qualifiers.items())):
            qualifier_id = f"qual:{observation_id}:{index + 1}"
            if is_number(raw_value):
                value_numeric = float(raw_value)
                value_text = str(raw_value)
            else:
                value_numeric = None
                value_text = str(raw_value)
            self.db.execute(
                """
                INSERT INTO observation_qualifiers (id, observation_id, key, value_text, value_numeric, unit_text)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (qualifier_id, observation_id, key, value_text, value_numeric, None),
            )

        self.observation_meta[observation_id] = {
            "definition_clarity_override": definition_clarity,
            "recognizability_override": recognizability,
            "source_class_override": source_class,
        }
        return observation_id

    def link_observation_source(self, observation_id: str, source_id: str, *, role: str, note: str | None) -> None:
        link_id = f"osrc:{observation_id}:{source_id}:{slugify(role)}"
        self.db.execute(
            """
            INSERT OR IGNORE INTO observation_sources (id, observation_id, source_id, role, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (link_id, observation_id, source_id, role, note),
        )

    def infer_category(self, name: str, dimension_slug: str) -> str:
        lowered = name.lower()
        if any(token in lowered for token in ("earth", "sun", "jupiter", "galaxy", "universe", "black hole", "nebula")):
            return "astronomy"
        if any(token in lowered for token in ("human", "cat", "dog", "tree", "bacteria", "virus", "neuron")):
            return "biology"
        if any(token in lowered for token in ("year", "day", "week", "hour", "movie", "work")):
            return "human-scale"
        return "everyday"

    def fetch_observations_for_dimension(self, slug: str) -> list[sqlite3.Row]:
        return self.db.execute(
            """
            SELECT o.*, s.source_class, sub.canonical_name, sub.subject_type
              FROM observations o
              JOIN dimensions d ON d.id = o.dimension_id
              JOIN subjects sub ON sub.id = o.subject_id
         LEFT JOIN (
                    SELECT os.observation_id, MAX(
                        CASE src.source_class
                            WHEN 'official_dataset' THEN 4
                            WHEN 'secondary_reference' THEN 3
                            WHEN 'wikidata' THEN 2
                            WHEN 'legacy_manual' THEN 1
                            ELSE 0
                        END
                    ) AS source_rank,
                    CASE MAX(
                        CASE src.source_class
                            WHEN 'official_dataset' THEN 4
                            WHEN 'secondary_reference' THEN 3
                            WHEN 'wikidata' THEN 2
                            WHEN 'legacy_manual' THEN 1
                            ELSE 0
                        END
                    )
                        WHEN 4 THEN 'official_dataset'
                        WHEN 3 THEN 'secondary_reference'
                        WHEN 2 THEN 'wikidata'
                        WHEN 1 THEN 'legacy_manual'
                        ELSE 'legacy_manual'
                    END AS source_class
                FROM observation_sources os
                JOIN sources src ON src.id = os.source_id
                GROUP BY os.observation_id
              ) s ON s.observation_id = o.id
             WHERE d.slug = ?
            """,
            (slug,),
        ).fetchall()

    def target_selected_count(self, slug: str, eligible_count: int) -> int:
        preferences = self.dimension_preferences(slug)
        preferred_target = preferences["preferred_target_items"]
        preferred_max = preferences["preferred_max_items"]
        return min(eligible_count, preferred_target, preferred_max)

    def is_display_candidate(self, row: sqlite3.Row) -> bool:
        return bool(row["display_eligible"]) and float(row["value_base"]) > 0 and not is_reference_category(row["category"])

    def display_representative_rank(self, row: sqlite3.Row) -> tuple[float, int, float, str]:
        meta = self.observation_meta.get(row["id"], {})
        source_class = row["source_class"] or meta.get("source_class_override") or "legacy_manual"
        content = self.db.execute(
            "SELECT * FROM observation_content WHERE observation_id = ?", (row["id"],)
        ).fetchone()
        richness = sum(bool(value) for value in self.fetch_qualifiers(row["id"]).values())
        richness += sum(row[key] is not None for key in ("lower_bound", "upper_bound", "uncertainty_text", "snapshot_date"))
        if content:
            richness += sum(bool(content[key]) for key in (
                "summary_short", "description_medium", "description_long", "hook", "caveats",
            ))
            richness += int(content["content_status"] == "curated")
            facts = json.loads(content["facts_json"] or "{}")
            richness += sum(bool(value) for value in facts.get("source_trace", {}).values())
        return (
            PRIMARY_SOURCE_CLASS_SCORE.get(source_class, 0.55),
            richness,
            self.base_selection_score(row),
            row["id"],
        )

    def select_display_representatives(self, rows: list[sqlite3.Row]) -> list[sqlite3.Row]:
        by_label: dict[tuple[str, str], list[sqlite3.Row]] = defaultdict(list)
        for row in rows:
            by_label[(row["dimension_id"], normalize_display_text(row["label"]))].append(row)

        representatives: list[sqlite3.Row] = []
        for (dimension_id, _), label_rows in by_label.items():
            slug = dimension_id.removeprefix("dim:")
            generic_measurements = {normalize_display_text(slug.replace("-", " "))}
            generic_measurements.update(DISPLAY_GENERIC_MEASUREMENTS.get(slug, set()))
            qualifiers_by_id = {
                row["id"]: {
                    normalize_display_text(key): normalize_display_text(value)
                    for key, value in self.fetch_qualifiers(row["id"]).items()
                    if value is not None and str(value).strip()
                }
                for row in label_rows
            }
            groups: dict[tuple[Any, ...], list[sqlite3.Row]] = defaultdict(list)
            for row in label_rows:
                qualifiers = qualifiers_by_id[row["id"]]
                identity = tuple(sorted(
                    (key, value) for key, value in qualifiers.items()
                    if key not in DISPLAY_PROVENANCE_QUALIFIERS
                    and key not in DISPLAY_MEASUREMENT_QUALIFIERS
                ))
                measurement_identity = tuple(sorted({
                    value for key, value in qualifiers.items()
                    if key in DISPLAY_MEASUREMENT_QUALIFIERS and value not in generic_measurements
                }))
                groups[(identity, measurement_identity, row["snapshot_date"] or "")].append(row)
            for candidates in groups.values():
                representatives.append(
                    max(candidates, key=self.display_representative_rank) if len(candidates) > 1 else candidates[0]
                )
        return sorted(representatives, key=lambda row: (row["value_base"], row["id"]))

    def compute_flagship_selection(self) -> None:
        for slug in sorted(self.dimension_lookup):
            dimension = self.dimension_lookup.get(slug)
            if not dimension:
                continue
            self.db.execute(
                "UPDATE observations SET rationale = NULL, selection_score = NULL WHERE dimension_id = ?",
                (dimension["id"],),
            )
            self.db.execute("DELETE FROM coverage_bins WHERE dimension_id = ?", (dimension["id"],))
            rows = self.fetch_observations_for_dimension(slug)
            raw_candidates = [row for row in rows if self.is_display_candidate(row)]
            eligible_rows = self.select_display_representatives(raw_candidates)
            bin_count = int(dimension["selection_bin_count"])
            preferred_target = int(dimension["preferred_target_items"])
            required_min = int(dimension["required_min_items"])
            preferred_max = int(dimension["preferred_max_items"])
            target_selected = self.target_selected_count(slug, len(eligible_rows))
            report = {
                "bin_count": bin_count,
                "empty_bin_count": bin_count,
                "raw_candidate_count": len(raw_candidates),
                "duplicate_candidate_count": len(raw_candidates) - len(eligible_rows),
                "candidate_count": len(eligible_rows),
                "selected_count": 0,
                "selected_primary_count": 0,
                "selected_secondary_count": 0,
                "required_min_items": required_min,
                "preferred_target_items": preferred_target,
                "preferred_max_items": preferred_max,
                "target_selected_count": target_selected,
                "selected_shortfall_to_required_min": required_min,
                "candidate_shortfall_to_preferred_target": max(0, preferred_target - len(eligible_rows)),
                "source_class_distribution": {},
            }
            self.coverage_report[slug] = report
            if not eligible_rows:
                continue

            scale_mode = str(dimension.get("scale_mode") or "log")
            if scale_mode == "linear":
                min_order = min(float(row["value_base"]) for row in eligible_rows)
                max_order = max(float(row["value_base"]) for row in eligible_rows)
                span = max(max_order - min_order, 1e-12)
            else:
                min_order = math.floor(min(math.log10(row["value_base"]) for row in eligible_rows))
                max_order = math.ceil(max(math.log10(row["value_base"]) for row in eligible_rows))
                span = max(max_order - min_order, 1)
            width = span / float(bin_count)

            for bin_index in range(bin_count):
                bin_id = f"bin:{slug}:{bin_index}"
                log_min = min_order + (bin_index * width)
                log_max = log_min + width
                self.db.execute(
                    """
                    INSERT OR REPLACE INTO coverage_bins
                        (id, dimension_id, bin_index, log10_min, log10_max, selected_observation_id)
                    VALUES (?, ?, ?, ?, ?, NULL)
                    """,
                    (bin_id, dimension["id"], bin_index, log_min, log_max),
                )

            grouped: dict[int, list[sqlite3.Row]] = defaultdict(list)
            for row in eligible_rows:
                order = float(row["value_base"]) if scale_mode == "linear" else math.log10(row["value_base"])
                index = int((order - min_order) / width) if width else 0
                index = max(0, min(bin_count - 1, index))
                grouped[index].append(row)

            base_scores: dict[str, float] = {}
            provisional_primary: dict[int, str] = {}
            for bin_index, candidates in grouped.items():
                ranked = sorted(
                    candidates,
                    key=lambda row: (
                        self.base_selection_score(row),
                        row["label"],
                        row["id"],
                    ),
                    reverse=True,
                )
                provisional_primary[bin_index] = ranked[0]["id"]
                for row in candidates:
                    base_scores[row["id"]] = self.base_selection_score(row)

            primary_selection: dict[int, sqlite3.Row] = {}
            for bin_index, candidates in grouped.items():
                neighbor_categories = self.neighbor_categories(bin_index, provisional_primary, grouped)
                ranked = sorted(
                    candidates,
                    key=lambda row: (
                        base_scores[row["id"]] + 0.1 * self.novelty_score(row["category"], neighbor_categories),
                        row["label"],
                        row["id"],
                    ),
                    reverse=True,
                )
                chosen = ranked[0]
                primary_selection[bin_index] = chosen
                final_score = base_scores[chosen["id"]] + 0.1 * self.novelty_score(chosen["category"], neighbor_categories)
                self.mark_observation_selected(
                    chosen["id"],
                    score=final_score,
                    rationale={
                        "selection": "primary_bin",
                        "dimension": slug,
                        "bin_index": bin_index,
                        "neighbor_categories": sorted(neighbor_categories),
                    },
                )
                self.db.execute(
                    "UPDATE coverage_bins SET selected_observation_id = ? WHERE id = ?",
                    (chosen["id"], f"bin:{slug}:{bin_index}"),
                )

                for candidate in candidates:
                    final_candidate_score = base_scores[candidate["id"]] + 0.1 * self.novelty_score(
                        candidate["category"], neighbor_categories
                    )
                    self.db.execute(
                        "UPDATE observations SET selection_score = ? WHERE id = ?",
                        (final_candidate_score, candidate["id"]),
                    )

            selected_ids = {row["id"] for row in primary_selection.values()}
            secondary_candidates: list[tuple[float, sqlite3.Row, int]] = []
            for bin_index, candidates in grouped.items():
                primary_row = primary_selection[bin_index]
                for candidate in candidates:
                    if candidate["id"] == primary_row["id"]:
                        continue
                    novelty = 1.0 if candidate["category"] != primary_row["category"] else 0.4
                    secondary_score = base_scores[candidate["id"]] + 0.1 * novelty
                    secondary_candidates.append((secondary_score, candidate, bin_index))
                    self.db.execute(
                        "UPDATE observations SET selection_score = COALESCE(selection_score, ?) WHERE id = ?",
                        (secondary_score, candidate["id"]),
                    )

            for score, candidate, bin_index in sorted(
                secondary_candidates,
                key=lambda item: (item[0], item[1]["label"], item[1]["id"]),
                reverse=True,
            ):
                if len(selected_ids) >= target_selected:
                    break
                if candidate["id"] in selected_ids:
                    continue
                primary_category = primary_selection[bin_index]["category"]
                if candidate["category"] == primary_category and len(grouped[bin_index]) <= 2:
                    continue
                selected_ids.add(candidate["id"])
                self.mark_observation_selected(
                    candidate["id"],
                    score=score,
                    rationale={
                        "selection": "secondary_bin",
                        "dimension": slug,
                        "bin_index": bin_index,
                        "primary_observation_id": primary_selection[bin_index]["id"],
                    },
                )

            if len(selected_ids) < target_selected:
                for score, candidate, bin_index in sorted(
                    secondary_candidates,
                    key=lambda item: (item[0], item[1]["label"], item[1]["id"]),
                    reverse=True,
                ):
                    if len(selected_ids) >= target_selected:
                        break
                    if candidate["id"] in selected_ids:
                        continue
                    selected_ids.add(candidate["id"])
                    self.mark_observation_selected(
                        candidate["id"],
                        score=score,
                        rationale={
                            "selection": "secondary_fill",
                            "dimension": slug,
                            "bin_index": bin_index,
                            "primary_observation_id": primary_selection[bin_index]["id"],
                        },
                    )

            selected_rows = self.db.execute(
                """
                SELECT o.id, src.source_class
                  FROM observations o
             LEFT JOIN (
                    SELECT os.observation_id,
                           CASE MAX(
                                CASE s.source_class
                                    WHEN 'official_dataset' THEN 4
                                    WHEN 'secondary_reference' THEN 3
                                    WHEN 'wikidata' THEN 2
                                    WHEN 'legacy_manual' THEN 1
                                    ELSE 0
                                END
                           )
                                WHEN 4 THEN 'official_dataset'
                                WHEN 3 THEN 'secondary_reference'
                                WHEN 2 THEN 'wikidata'
                                WHEN 1 THEN 'legacy_manual'
                                ELSE 'legacy_manual'
                           END AS source_class
                      FROM observation_sources os
                      JOIN sources s ON s.id = os.source_id
                     GROUP BY os.observation_id
                ) src ON src.observation_id = o.id
                 WHERE o.dimension_id = ? AND o.rationale IS NOT NULL
                """,
                (dimension["id"],),
            ).fetchall()
            nonempty_bins = len(grouped)
            report.update({
                "empty_bin_count": bin_count - nonempty_bins,
                "selected_count": len(selected_rows),
                "selected_primary_count": len(primary_selection),
                "selected_secondary_count": max(0, len(selected_rows) - len(primary_selection)),
                "selected_shortfall_to_required_min": max(0, required_min - len(selected_rows)),
                "source_class_distribution": dict(Counter(row["source_class"] or "legacy_manual" for row in selected_rows)),
            })

        self.db.commit()

    def base_selection_score(self, row: sqlite3.Row) -> float:
        meta = self.observation_meta.get(row["id"], {})
        source_class = row["source_class"] or meta.get("source_class_override") or "legacy_manual"
        provenance = PRIMARY_SOURCE_CLASS_SCORE.get(source_class, 0.55)
        qualifier_count = self.db.execute(
            "SELECT COUNT(*) FROM observation_qualifiers WHERE observation_id = ?",
            (row["id"],),
        ).fetchone()[0]
        qualifier_completeness = min(1.0, qualifier_count / 3.0)

        clarity_override = meta.get("definition_clarity_override")
        if clarity_override is not None:
            definition_clarity = float(clarity_override)
        else:
            definition_clarity = 0.55
            if row["summary"] and len(row["summary"]) >= 40:
                definition_clarity += 0.15
            if qualifier_count:
                definition_clarity += 0.15
            if row["value_type"] == "derived":
                definition_clarity += 0.05
            definition_clarity = min(1.0, definition_clarity)

        recognizability_override = meta.get("recognizability_override")
        if recognizability_override is not None:
            recognizability = float(recognizability_override)
        else:
            recognizability = CATEGORY_RECOGNIZABILITY.get(row["category"] or "", 0.65)

        return (
            (0.40 * provenance)
            + (0.20 * qualifier_completeness)
            + (0.20 * definition_clarity)
            + (0.10 * recognizability)
        )

    def neighbor_categories(
        self,
        bin_index: int,
        provisional_primary: dict[int, str],
        grouped: dict[int, list[sqlite3.Row]],
    ) -> set[str]:
        categories: set[str] = set()
        for neighbor in (bin_index - 1, bin_index + 1):
            observation_id = provisional_primary.get(neighbor)
            if not observation_id:
                continue
            for row in grouped.get(neighbor, []):
                if row["id"] == observation_id and row["category"]:
                    categories.add(str(row["category"]))
        return categories

    def novelty_score(self, category: str | None, neighbor_categories: set[str]) -> float:
        if not neighbor_categories:
            return 1.0
        if category and category not in neighbor_categories:
            return 1.0
        if category and len(neighbor_categories) == 1:
            return 0.7
        return 0.4

    def mark_observation_selected(self, observation_id: str, *, score: float, rationale: dict[str, Any]) -> None:
        self.db.execute(
            "UPDATE observations SET selection_score = ?, rationale = ? WHERE id = ?",
            (score, json_dumps(rationale), observation_id),
        )

    def write_exports(self) -> None:
        self.db.commit()
        self.db.execute("VACUUM")
        shutil.copyfile(CANONICAL_DB_PATH, SQLITE_EXPORT_PATH)
        self.export_subjects_jsonl()
        self.export_dimension_catalog()
        self.export_observations_jsonl()
        self.export_observation_content_jsonl()
        self.export_writer_packets()
        self.export_dimension_json()
        self.export_frontend_yaml()
        coverage_path = EXPORT_JSON_DIR / "coverage_report.json"
        coverage_path.write_text(json.dumps(self.coverage_report, indent=2, sort_keys=True), encoding="utf-8")

    def export_subjects_jsonl(self) -> None:
        rows = self.db.execute("SELECT * FROM subjects ORDER BY id").fetchall()
        output = EXPORT_JSON_DIR / "subjects.jsonl"
        with output.open("w", encoding="utf-8") as handle:
            for row in rows:
                payload = dict(row)
                payload["aliases"] = json.loads(payload.pop("aliases_json"))
                handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def export_dimension_catalog(self) -> None:
        dimension_rows = self.db.execute(
            """
            SELECT
                d.slug,
                d.name,
                d.base_unit,
                d.quantity_kind,
                d.description,
                d.description_format,
                d.scale_mode,
                d.frontend_group,
                d.frontend_group_label,
                d.frontend_order,
                d.required_min_items,
                d.preferred_target_items,
                d.preferred_max_items,
                d.selection_bin_count,
                COUNT(o.id) AS observation_count,
                SUM(CASE WHEN o.display_eligible = 1 AND (o.category IS NULL OR LOWER(o.category) != 'reference') THEN 1 ELSE 0 END) AS candidate_count,
                SUM(CASE WHEN o.rationale IS NOT NULL THEN 1 ELSE 0 END) AS selected_count
              FROM dimensions d
              LEFT JOIN observations o ON o.dimension_id = d.id
             GROUP BY d.id
             ORDER BY d.frontend_group_label, d.frontend_order, d.slug
            """
        ).fetchall()
        available_by_slug = {row["slug"]: dict(row) for row in dimension_rows}
        for slug, row in available_by_slug.items():
            if slug in self.coverage_report:
                row["candidate_count"] = self.coverage_report[slug]["candidate_count"]
        catalog: list[dict[str, Any]] = []

        for slug, profile in self.raw_catalog.dimension_profiles.items():
            row = available_by_slug.get(slug)
            catalog.append(
                {
                    "slug": slug,
                    "name": profile.get("name") or (row["name"] if row else slug.replace("-", " ").title()),
                    "frontend_group": profile.get("frontend_group") or (row["frontend_group"] if row else None),
                    "frontend_group_label": profile.get("frontend_group_label") or (row["frontend_group_label"] if row else None),
                    "frontend_order": int(profile.get("frontend_order", row["frontend_order"] if row else 1000)),
                    "status": profile.get("status") or ("available" if row else "planned"),
                    "available": row is not None,
                    "base_unit": row["base_unit"] if row else None,
                    "quantity_kind": row["quantity_kind"] if row else None,
                    "description": row["description"] if row else None,
                    "description_format": row["description_format"] if row else "markdown",
                    "scale_mode": row["scale_mode"] if row else str(profile.get("scale_mode", "log")),
                    "observation_count": int(row["observation_count"] or 0) if row else 0,
                    "candidate_count": int(row["candidate_count"] or 0) if row else 0,
                    "selected_count": int(row["selected_count"] or 0) if row else 0,
                    "required_min_items": int(row["required_min_items"]) if row else None,
                    "preferred_target_items": int(row["preferred_target_items"]) if row else None,
                    "preferred_max_items": int(row["preferred_max_items"]) if row else None,
                    "selection_bin_count": int(row["selection_bin_count"]) if row else None,
                }
            )

        for slug, row in available_by_slug.items():
            if slug in self.raw_catalog.dimension_profiles:
                continue
            catalog.append(
                {
                    "slug": slug,
                    "name": row["name"],
                    "frontend_group": row["frontend_group"],
                    "frontend_group_label": row["frontend_group_label"],
                    "frontend_order": int(row["frontend_order"]),
                    "status": "available",
                    "available": True,
                    "base_unit": row["base_unit"],
                    "quantity_kind": row["quantity_kind"],
                    "description": row["description"],
                    "description_format": row["description_format"],
                    "scale_mode": row["scale_mode"],
                    "observation_count": int(row["observation_count"] or 0),
                    "candidate_count": int(row["candidate_count"] or 0),
                    "selected_count": int(row["selected_count"] or 0),
                    "required_min_items": int(row["required_min_items"]),
                    "preferred_target_items": int(row["preferred_target_items"]),
                    "preferred_max_items": int(row["preferred_max_items"]),
                    "selection_bin_count": int(row["selection_bin_count"]),
                }
            )

        catalog.sort(key=lambda entry: (entry["frontend_group_label"] or "", entry["frontend_order"], entry["name"]))
        DIMENSION_CATALOG_EXPORT_PATH.write_text(json.dumps(catalog, indent=2, sort_keys=True), encoding="utf-8")

    def export_observations_jsonl(self) -> None:
        rows = self.db.execute(
            """
            SELECT
                o.*,
                d.slug AS dimension_slug,
                d.base_unit,
                d.quantity_kind,
                d.scale_mode,
                sub.canonical_name,
                sub.wikidata_qid,
                oc.content_origin,
                oc.content_status,
                oc.content_format,
                oc.summary_short,
                oc.description_medium,
                oc.description_long,
                oc.hook,
                oc.caveats,
                oc.facts_json
              FROM observations o
              JOIN dimensions d ON d.id = o.dimension_id
              JOIN subjects sub ON sub.id = o.subject_id
              LEFT JOIN observation_content oc ON oc.observation_id = o.id
             ORDER BY d.slug, o.value_base, o.id
            """
        ).fetchall()
        output = EXPORT_JSON_DIR / "observations.jsonl"
        with output.open("w", encoding="utf-8") as handle:
            for row in rows:
                payload = dict(row)
                payload["qualifiers"] = self.fetch_qualifiers(row["id"])
                payload["sources"] = self.fetch_sources(row["id"])
                payload["source_count"] = len(payload["sources"])
                payload["quality_flags"] = json.loads(payload.pop("quality_flags_json") or "[]")
                payload["facts"] = json.loads(payload.pop("facts_json") or "{}")
                payload["selected_for_display"] = payload["rationale"] is not None
                handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def export_observation_content_jsonl(self) -> None:
        rows = self.db.execute(
            """
            SELECT
                oc.*,
                o.label,
                o.value_base,
                o.value_type,
                d.slug AS dimension_slug,
                d.base_unit,
                sub.canonical_name AS subject_name,
                sub.subject_type,
                sub.wikidata_qid
              FROM observation_content oc
              JOIN observations o ON o.id = oc.observation_id
              JOIN dimensions d ON d.id = o.dimension_id
              JOIN subjects sub ON sub.id = o.subject_id
             ORDER BY d.slug, o.value_base, o.id
            """
        ).fetchall()
        with CONTENT_EXPORT_PATH.open("w", encoding="utf-8") as handle:
            for row in rows:
                payload = dict(row)
                payload["facts"] = json.loads(payload.pop("facts_json") or "{}")
                handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def export_writer_packets(self) -> None:
        rows = self.db.execute(
            """
            SELECT
                o.id,
                o.subject_id,
                o.dimension_id,
                o.label,
                o.value_base,
                o.original_value_text,
                o.value_type,
                o.selection_score,
                o.rationale,
                o.summary,
                o.category,
                o.review_status,
                o.display_status,
                o.quality_flags_json,
                d.slug AS dimension_slug,
                d.name AS dimension_name,
                d.base_unit,
                d.quantity_kind,
                d.scale_mode,
                d.description_format,
                d.required_min_items,
                d.preferred_target_items,
                d.preferred_max_items,
                d.selection_bin_count,
                sub.canonical_name AS subject_name,
                sub.subject_type,
                sub.wikidata_qid,
                oc.content_origin,
                oc.content_status,
                oc.content_format,
                oc.summary_short,
                oc.description_medium,
                oc.description_long,
                oc.hook,
                oc.caveats,
                oc.facts_json
              FROM observations o
              JOIN dimensions d ON d.id = o.dimension_id
              JOIN subjects sub ON sub.id = o.subject_id
              LEFT JOIN observation_content oc ON oc.observation_id = o.id
             ORDER BY d.slug, o.value_base, o.id
            """
        ).fetchall()

        rows_by_dimension: dict[str, list[sqlite3.Row]] = defaultdict(list)
        for row in rows:
            rows_by_dimension[row["dimension_slug"]].append(row)

        with WRITER_PACKET_EXPORT_PATH.open("w", encoding="utf-8") as handle:
            for dimension_slug in sorted(rows_by_dimension):
                dimension_rows = rows_by_dimension[dimension_slug]
                selected_positions = [index for index, row in enumerate(dimension_rows) if row["rationale"]]
                for index, row in enumerate(dimension_rows):
                    smaller_selected = self.selected_neighbor(dimension_rows, selected_positions, index, direction=-1)
                    larger_selected = self.selected_neighbor(dimension_rows, selected_positions, index, direction=1)
                    payload = {
                        "observation_id": row["id"],
                        "selected_for_display": row["rationale"] is not None,
                        "dimension": {
                            "slug": row["dimension_slug"],
                            "name": row["dimension_name"],
                            "base_unit": row["base_unit"],
                            "quantity_kind": row["quantity_kind"],
                            "scale_mode": row["scale_mode"],
                            "description_format": row["description_format"],
                            "required_min_items": row["required_min_items"],
                            "preferred_target_items": row["preferred_target_items"],
                            "preferred_max_items": row["preferred_max_items"],
                            "selection_bin_count": row["selection_bin_count"],
                        },
                        "subject": {
                            "id": row["subject_id"],
                            "name": row["subject_name"],
                            "subject_type": row["subject_type"],
                            "wikidata_qid": row["wikidata_qid"],
                        },
                        "observation": {
                            "label": row["label"],
                            "value_base": row["value_base"],
                            "original_value_text": row["original_value_text"],
                            "value_type": row["value_type"],
                            "summary": row["summary"],
                            "category": row["category"],
                            "review_status": row["review_status"],
                            "display_status": row["display_status"],
                            "quality_flags": json.loads(row["quality_flags_json"] or "[]"),
                            "selection_score": row["selection_score"],
                            "selection_rationale": json.loads(row["rationale"]) if row["rationale"] else None,
                        },
                        "content": {
                            "content_origin": row["content_origin"],
                            "content_status": row["content_status"],
                            "content_format": row["content_format"],
                            "summary_short": row["summary_short"],
                            "description_medium": row["description_medium"],
                            "description_long": row["description_long"],
                            "hook": row["hook"],
                            "caveats": row["caveats"],
                            "facts": json.loads(row["facts_json"] or "{}"),
                        },
                        "qualifiers": self.fetch_qualifiers(row["id"]),
                        "sources": self.fetch_sources(row["id"]),
                        "unit_conversions": self.fetch_unit_conversions(row["dimension_id"], row["value_base"]),
                        "nearby_selected": {
                            "smaller": smaller_selected,
                            "larger": larger_selected,
                        },
                    }
                    handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def selected_neighbor(
        self,
        rows: list[sqlite3.Row],
        selected_positions: list[int],
        current_index: int,
        *,
        direction: int,
    ) -> dict[str, Any] | None:
        if direction < 0:
            candidates = [position for position in selected_positions if position < current_index]
            if not candidates:
                return None
            neighbor = rows[candidates[-1]]
        else:
            candidates = [position for position in selected_positions if position > current_index]
            if not candidates:
                return None
            neighbor = rows[candidates[0]]
        return {
            "observation_id": neighbor["id"],
            "label": neighbor["label"],
            "value_base": neighbor["value_base"],
        }

    def export_dimension_json(self) -> None:
        for slug in self.export_dimension_slugs():
            payload = deepcopy(self.dimension_export_meta[slug])
            payload["items"] = self.fetch_selected_dimension_items(slug)
            payload["coverage_report"] = self.coverage_report.get(slug, {})
            output = DIMENSIONS_EXPORT_DIR / f"{slug}.json"
            output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def export_frontend_yaml(self) -> None:
        for slug in self.export_dimension_slugs():
            payload = deepcopy(self.dimension_export_meta[slug])
            payload["items"] = self.fetch_selected_dimension_items(slug)
            export_path = EXPORT_FRONTEND_DIR / f"{slug}.yaml"
            export_path.write_text(
                yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=1000),
                encoding="utf-8",
            )
            if slug in self.flagship_dimensions:
                shutil.copyfile(export_path, ROOT / "data" / f"{slug}.yaml")

    def export_dimension_slugs(self) -> list[str]:
        rows = self.db.execute(
            """
            SELECT slug
              FROM dimensions
             ORDER BY frontend_group_label, frontend_order, slug
            """
        ).fetchall()
        return [str(row["slug"]) for row in rows]

    def fetch_selected_dimension_items(self, slug: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            """
            SELECT
                o.*,
                sub.canonical_name,
                sub.wikidata_qid,
                oc.content_status,
                oc.content_format,
                oc.summary_short,
                oc.description_medium,
                oc.description_long,
                oc.hook,
                oc.caveats,
                oc.facts_json
              FROM observations o
              JOIN dimensions d ON d.id = o.dimension_id
              JOIN subjects sub ON sub.id = o.subject_id
              LEFT JOIN observation_content oc ON oc.observation_id = o.id
             WHERE d.slug = ? AND o.rationale IS NOT NULL
               AND (o.category IS NULL OR LOWER(TRIM(o.category)) != 'reference')
             ORDER BY o.value_base, o.id
            """,
            (slug,),
        ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            source_url = self.primary_source_url(row["id"])
            qualifiers = self.fetch_qualifiers(row["id"])
            sources = self.fetch_sources(row["id"])
            description_text = row["description_long"] or row["description_medium"] or row["summary_short"] or row["summary"]
            items.append(
                {
                    "id": row["id"],
                    "name": row["label"],
                    "value": row["value_base"],
                    "description": description_text,
                    "description_format": row["content_format"] or "markdown",
                    "summary_short": row["summary_short"],
                    "description_medium": row["description_medium"] or row["summary_short"] or row["summary"],
                    "description_long": row["description_long"],
                    "hook": row["hook"],
                    "caveats": row["caveats"],
                    "content_status": row["content_status"],
                    "review_status": row["review_status"],
                    "display_status": row["display_status"],
                    "quality_flags": json.loads(row["quality_flags_json"] or "[]"),
                    "facts": json.loads(row["facts_json"] or "{}"),
                    "source": source_url,
                    "source_count": len(sources),
                    "sources": sources,
                    "wikidata_qid": row["wikidata_qid"],
                    "value_type": row["value_type"],
                    "qualifiers": qualifiers,
                }
            )
        return items

    def primary_source_url(self, observation_id: str) -> str | None:
        row = self.db.execute(
            """
            SELECT s.url
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
             LIMIT 1
            """,
            (observation_id,),
        ).fetchone()
        return row["url"] if row else None

    def fetch_sources(self, observation_id: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            """
            SELECT
                s.id,
                s.url,
                s.title,
                s.publisher,
                s.license_text,
                s.source_class,
                s.source_type,
                os.role,
                os.note
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
                s.url,
                os.role
            """,
            (observation_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def fetch_unit_conversions(self, dimension_id: str, value_base: float) -> list[dict[str, Any]]:
        rows = self.db.execute(
            """
            SELECT name, symbol, to_base_factor, offset
              FROM units
             WHERE dimension_id = ?
             ORDER BY name
            """,
            (dimension_id,),
        ).fetchall()
        conversions: list[dict[str, Any]] = []
        for row in rows:
            conversions.append(
                {
                    "name": row["name"],
                    "symbol": row["symbol"],
                    "value": (value_base + float(row["offset"])) * float(row["to_base_factor"]),
                }
            )
        return conversions

    def fetch_qualifiers(self, observation_id: str) -> dict[str, str]:
        rows = self.db.execute(
            "SELECT key, value_text FROM observation_qualifiers WHERE observation_id = ? ORDER BY key",
            (observation_id,),
        ).fetchall()
        return {row["key"]: row["value_text"] for row in rows}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the canonical Universe Scales dataset.")
    return parser.parse_args()


def main() -> int:
    parse_args()
    builder = DatasetBuilder()
    builder.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
