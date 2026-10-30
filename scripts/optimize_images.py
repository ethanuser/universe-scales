#!/usr/bin/env python3
"""Shrink oversized item photos in place: long edge <= 2400 px, progressive JPEG q85.

    ./venv/bin/python scripts/optimize_images.py [--dry-run] [images/*.jpg ...]

Thumbnails (images/thumbs) are what the explorer and side panel load; the originals
only open in the full-size image viewer, where 2400 px is ample. A file is rewritten
only when it is wider/taller than 2400 px or larger than 1 MB, and only if the result
is smaller. Color profiles are kept; other metadata is dropped.
"""
import argparse
import io
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAX_EDGE, MAX_BYTES, QUALITY = 2400, 1_000_000, 85


def optimize(path, dry_run=False):
    before = path.stat().st_size
    with Image.open(path) as image:
        if max(image.size) <= MAX_EDGE and before <= MAX_BYTES:
            return None
        icc = image.info.get("icc_profile")
        image = image.convert("RGB")
        if max(image.size) > MAX_EDGE:
            image.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, "JPEG", quality=QUALITY, progressive=True, optimize=True,
                   **({"icc_profile": icc} if icc else {}))
    after = buffer.tell()
    if after >= before:
        return None
    if not dry_run:
        path.write_bytes(buffer.getvalue())
    return before, after


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    paths = args.paths or sorted((ROOT / "images").glob("*.jpg"))
    saved = count = 0
    for path in paths:
        result = optimize(path, args.dry_run)
        if result:
            count += 1
            saved += result[0] - result[1]
    print(f"{'Would shrink' if args.dry_run else 'Shrank'} {count} images, saving {saved / 1e6:.1f} MB")


if __name__ == "__main__":
    sys.exit(main())
