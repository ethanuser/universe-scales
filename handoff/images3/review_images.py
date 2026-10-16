#!/usr/bin/env python3
"""Audit the six requested image slots and create all-Length review sheets.

Read-only outside this handoff. Uses the site's ASCII filename sanitization and
JPEG-before-PNG choice. Contact sheets are a subject review, not license approval
of pre-existing images. Run with the project venv (Pillow and PyYAML).
"""
import hashlib
import json
import math
import re
import textwrap
from pathlib import Path

import yaml
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REQUESTED = [
    "Helium Nucleus Charge Diameter", "Prelude FLNG", "PSR J0437-4715 Neutron Star",
    "Danyang-Kunshan Grand Bridge", "Milky Way Central Bar", "Baryon Acoustic Oscillation Scale",
]
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
INK = "#eef4fa"


def slug(name):
    return re.sub(r"[-\s]+", "_", re.sub(r"[^\w\s-]", "", name, flags=re.ASCII)).lower()


def font(size):
    return ImageFont.truetype(FONT, size)


def resolve(name):
    stem = "length_" + slug(name)
    for ext in ["jpg", "png"]:
        p = ROOT / "images" / (stem + "." + ext)
        if p.exists():
            return p
    return None


def rgb(source):
    # Some legacy .jpg paths actually contain transparent PNG data.
    # White preserves black chemical bonds/text during this review.
    if "A" in source.getbands() or "transparency" in source.info:
        rgba = source.convert("RGBA")
        im = Image.new("RGB", source.size, "white")
        im.paste(rgba, mask=rgba.getchannel("A"))
        return im
    return source.convert("RGB")


def sheet(names, path, columns, tile_width, tile_height, heading):
    rows = math.ceil(len(names) / columns)
    canvas = Image.new("RGB", (columns * tile_width, rows * tile_height + 64), "#101b2b")
    draw = ImageDraw.Draw(canvas)
    draw.text((18, 15), heading, font=font(25), fill=INK)
    for i, name in enumerate(names):
        x, y = i % columns * tile_width, i // columns * tile_height + 64
        im_path = resolve(name)
        if im_path:
            with Image.open(im_path) as source:
                im = rgb(source)
                im.thumbnail((tile_width - 20, tile_height - 68), Image.Resampling.LANCZOS)
                canvas.paste(im, (x + (tile_width - im.width) // 2, y + (tile_height - 68 - im.height) // 2))
        else:
            draw.rectangle((x + 10, y + 5, x + tile_width - 10, y + tile_height - 68), outline="#d6776c", width=2)
            draw.text((x + tile_width / 2, y + tile_height / 2 - 32), "NO IMAGE", font=font(21), fill="#ed978a", anchor="mm")
        for j, label in enumerate(textwrap.wrap(name, width=(tile_width - 20) // 10)):
            draw.text((x + 10, y + tile_height - 60 + 21 * j), label, font=font(18), fill=INK)
    canvas.save(path, quality=92, optimize=True)


def main():
    items = yaml.safe_load((ROOT / "dataset/raw/legacy_yaml/length.yaml").read_text())["items"]
    names = [i["name"] for i in items]
    credits = json.loads((ROOT / "images/credits/length.json").read_text())["images"]
    byfile = {r["file"]: r for r in credits}
    manifest, audit = [], []
    for name in names:
        p = resolve(name)
        r = {"item": name, "file": str(p.relative_to(ROOT)) if p else None}
        if p:
            r["dimensions"] = list(Image.open(p).size)
            r["credit"] = byfile.get(r["file"])
        manifest.append(r)
    (HERE / "all-length-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    thumbnail_findings = []
    for row in manifest:
        if not row["file"]:
            continue
        p = ROOT / row["file"]
        t = ROOT / "images/thumbs" / p.name
        if not t.exists():
            thumbnail_findings.append({"item": row["item"], "status": "matching thumbnail filename missing"})
            continue
        with Image.open(p) as full, Image.open(t) as thumb:
            a, b = rgb(full).resize((96, 96)), rgb(thumb).resize((96, 96))
            diff = sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3
        if diff > 10:
            thumbnail_findings.append({
                "item": row["item"], "status": "thumbnail differs", "mean_pixel_difference": round(diff, 2),
                "file": row["file"], "thumbnail": str(t.relative_to(ROOT)),
            })
    (HERE / "thumbnail-review.json").write_text(json.dumps(thumbnail_findings, indent=2) + "\n")
    review = HERE / "review"
    review.mkdir(exist_ok=True)
    for i in range(0, len(names), 20):
        sheet(names[i:i + 20], review / f"length-{i // 20 + 1:02d}.jpg", 5, 320, 250,
              f"Length subject review · {i + 1}–{min(i + 20, len(names))} / {len(names)}")
    sheet(REQUESTED, HERE / "contact-sheet.jpg", 2, 600, 460, "images3 · six requested Length image slots")
    for name in REQUESTED:
        p = resolve(name)
        if p is None:
            audit.append({"item": name, "status": "missing approved image"})
            continue
        im = Image.open(p)
        t = ROOT / "images/thumbs" / p.name
        thumb = Image.open(t)
        credit = byfile[str(p.relative_to(ROOT))]
        assert im.format == "JPEG" and im.width == 1200
        assert thumb.format == "JPEG" and thumb.width == 300
        assert thumb.height == round(im.height / 4)
        assert credit["author"] and credit["source"] and credit["changes"]
        assert credit["license"] in {"CC0", "Public domain"} or re.fullmatch(r"CC BY [0-9.]+", credit["license"])
        audit.append({
            "item": name, "file": str(p.relative_to(ROOT)), "dimensions": list(im.size),
            "thumbnail": str(t.relative_to(ROOT)), "thumbnail_dimensions": list(thumb.size),
            "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "thumbnail_sha256": hashlib.sha256(t.read_bytes()).hexdigest(), "license": credit["license"],
        })
    (HERE / "asset-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(names)} Length items; {sum(r['file'] is not None for r in manifest)} images.")
    print("Requested images:", sum("status" not in a for a in audit), "/", len(REQUESTED))
    print("Missing slots:", ", ".join(r["item"] for r in manifest if r["file"] is None))


if __name__ == "__main__":
    main()
