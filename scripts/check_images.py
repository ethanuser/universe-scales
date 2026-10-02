#!/usr/bin/env python3
"""
Audit image and thumbnail coverage for exported frontend items.

Default input is `exports/frontend/*.yaml` and expected image locations are:
- originals: images/<dimension>_<item>.jpg|jpeg|png|webp
- thumbnails: images/thumbs/<dimension>_<item>.jpg
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from collections import Counter

try:
    import yaml
except ImportError:  # pragma: no cover - fallback parser path
    yaml = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover - optional dependency
    Image = None


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


def sanitize_for_filename(value: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", value)
    cleaned = re.sub(r"[-\s]+", "_", cleaned)
    return cleaned.lower()


def expected_basename(dimension: str, item_name: str) -> str:
    return f"{sanitize_for_filename(dimension)}_{sanitize_for_filename(item_name)}"


@dataclass
class MissingRecord:
    dimension: str
    item_name: str
    basename: str
    missing_original: bool
    missing_thumbnail: bool


def is_readable_image(path: Path) -> bool:
    try:
        if not path.exists() or path.stat().st_size == 0:
            return False
        # Avoid counting vector/video files with misleading extensions as valid.
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            return False
        if Image is None:
            return path.stat().st_size > 1024
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def find_existing_original(images_dir: Path, basename: str, *, validate: bool) -> Path | None:
    for ext in IMAGE_EXTENSIONS:
        candidate = images_dir / f"{basename}{ext}"
        if validate:
            if is_readable_image(candidate):
                return candidate
        elif candidate.exists() and candidate.stat().st_size > 0:
            return candidate
    return None


def iter_yaml_files(data_dir: Path) -> Iterable[Path]:
    return sorted(path for path in data_dir.glob("*.yaml") if path.is_file())


def parse_yaml_items(yaml_path: Path) -> list[dict]:
    if yaml is not None:
        loaded = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        items = loaded.get("items") or []
        return items if isinstance(items, list) else []

    # Narrow fallback parser: only extracts `items` + item `name` fields.
    items: list[dict] = []
    in_items = False
    current: dict | None = None
    for raw_line in yaml_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "items:":
            in_items = True
            continue
        if not in_items:
            continue
        if stripped.startswith("- "):
            if current:
                items.append(current)
            current = {}
            stripped = stripped[2:].strip()
        if current is None or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        if key == "name":
            current["name"] = value.strip().strip("\"'")
    if current:
        items.append(current)
    return items


def audit(
    data_dir: Path,
    images_dir: Path,
    thumbs_dir: Path,
    *,
    validate_images: bool,
) -> tuple[int, list[MissingRecord]]:
    total_items = 0
    missing: list[MissingRecord] = []

    for yaml_file in iter_yaml_files(data_dir):
        dimension = yaml_file.stem
        items = parse_yaml_items(yaml_file)

        for item in items:
            if not isinstance(item, dict):
                continue
            item_name = str(item.get("name", "")).strip()
            if not item_name:
                continue
            total_items += 1
            basename = expected_basename(dimension, item_name)

            original = find_existing_original(images_dir, basename, validate=validate_images)
            thumb = thumbs_dir / f"{basename}.jpg"
            missing_original = original is None
            missing_thumbnail = not is_readable_image(thumb) if validate_images else (not thumb.exists() or thumb.stat().st_size == 0)

            if missing_original or missing_thumbnail:
                missing.append(
                    MissingRecord(
                        dimension=dimension,
                        item_name=item_name,
                        basename=basename,
                        missing_original=missing_original,
                        missing_thumbnail=missing_thumbnail,
                    )
                )

    return total_items, missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Check image and thumbnail coverage for exported items.")
    parser.add_argument("--data-dir", default="exports/frontend", help="Directory containing exported YAML files.")
    parser.add_argument("--images-dir", default="images", help="Directory containing full-size images.")
    parser.add_argument("--thumbs-dir", default="images/thumbs", help="Directory containing thumbnails.")
    parser.add_argument("--show", type=int, default=50, help="How many missing records to print.")
    parser.add_argument("--no-validate", action="store_true", help="Only check file existence; skip image readability validation.")
    parser.add_argument("--by-dimension", action="store_true", help="Print missing counts grouped by dimension.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    data_dir = (root / args.data_dir).resolve()
    images_dir = (root / args.images_dir).resolve()
    thumbs_dir = (root / args.thumbs_dir).resolve()

    total_items, missing = audit(
        data_dir,
        images_dir,
        thumbs_dir,
        validate_images=not args.no_validate,
    )

    missing_original_count = sum(1 for rec in missing if rec.missing_original)
    missing_thumb_count = sum(1 for rec in missing if rec.missing_thumbnail)
    complete_count = total_items - len(missing)

    print(f"YAML source: {data_dir}")
    print(f"Images dir:  {images_dir}")
    print(f"Thumbs dir:  {thumbs_dir}")
    print("-" * 60)
    print(f"Total items checked:        {total_items}")
    print(f"Complete image+thumb pairs: {complete_count}")
    print(f"Missing original image:     {missing_original_count}")
    print(f"Missing thumbnail:          {missing_thumb_count}")
    print(f"Any missing:                {len(missing)}")

    if args.by_dimension and missing:
        print("\nMissing by dimension:")
        counter = Counter(rec.dimension for rec in missing)
        for dimension, count in sorted(counter.items(), key=lambda x: (-x[1], x[0])):
            print(f"- {dimension}: {count}")

    if missing:
        print("\nSample missing records:")
        for rec in missing[: max(0, args.show)]:
            issues = []
            if rec.missing_original:
                issues.append("original")
            if rec.missing_thumbnail:
                issues.append("thumbnail")
            print(f"- {rec.dimension}/{rec.item_name} [{', '.join(issues)}] -> {rec.basename}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
