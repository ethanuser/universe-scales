#!/usr/bin/env python3
"""Build original CC0 measurement diagrams and append their image credits.

Requires Pillow and CairoSVG (installed only in /tmp/images3-tools). Set
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib on macOS. All artwork is original SVG;
the cited sources supply scientific facts, not copied illustrations or pixels.
"""
import html
import io
import json
import math
import random
from pathlib import Path

import cairosvg
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "diagrams"
BG, INK, MUTED = "#081321", "#edf4fc", "#a5b8cd"
BLUE, GOLD = "#83d8f2", "#ffd398"


def text(x, y, label, size=28, color=INK, anchor="start", weight="normal"):
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'text-anchor="{anchor}" font-weight="{weight}" '
            f'font-family="Arial,Helvetica,sans-serif">{html.escape(label)}</text>')


def line(x1, y1, x2, y2, color=BLUE, width=2, dash=""):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}"/>')


def circle(x, y, r, fill="none", stroke="none", width=2, opacity=1):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"/>')


def frame(title, subtitle):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" '
            'viewBox="0 0 1200 800">'
            f'<rect width="1200" height="800" fill="{BG}"/>'
            + line(56, 39, 100, 39, GOLD, 4)
            + text(56, 98, title, 43, weight="bold")
            + text(56, 143, subtitle, 24, MUTED))


def footer(s, basis):
    return (s + line(56, 741, 1144, 741, "#24364a", 1)
            + text(56, 779, "Original explanatory diagram · CC0", 19, MUTED)
            + text(1144, 779, basis, 19, MUTED, "end"))


def bracket(x1, x2, y, label, color=GOLD, size=38):
    return (line(x1, y, x2, y, color, 3)
            + line(x1, y - 12, x1, y + 12, color, 3)
            + line(x2, y - 12, x2, y + 12, color, 3)
            + text((x1 + x2) / 2, y + 58, label, size, color, "middle"))


def save(stem, s, record, evidence):
    OUT.mkdir(exist_ok=True)
    p = OUT / (stem + ".svg")
    p.write_text(s + "</svg>\n")
    png = cairosvg.svg2png(url=str(p), output_width=2400, output_height=1600)
    im = Image.open(io.BytesIO(png)).convert("RGB")
    im = im.resize((1200, 800), Image.Resampling.LANCZOS)
    filename = "length_" + stem + ".jpg"
    im.save(ROOT / "images" / filename, quality=93, optimize=True)
    im.resize((300, 200), Image.Resampling.LANCZOS).save(
        ROOT / "images/thumbs" / filename, quality=90, optimize=True)
    record = {"file": "images/" + filename, **record}
    record.update(author="Universe Scales (original explanatory diagram)",
                  license="CC0",
                  license_url="https://creativecommons.org/publicdomain/zero/1.0/")
    record["changes"] = ("New original SVG; rendered to 1200 × 800 JPEG and a "
                         "300 × 200 thumbnail. " + evidence)
    (HERE / "sources" / (stem + ".json")).write_text(json.dumps({
        "source": record["source"], "original_svg": str(p.relative_to(ROOT)),
        "license": "CC0", "evidence": evidence,
        "accessed": "2026-10-16",
    }, ensure_ascii=False, indent=2) + "\n")
    return record


def main():
    records = []
    s = frame("Helium nucleus charge diameter", "Helium-4 · twice the root-mean-square charge radius")
    s += ('<defs><radialGradient id="charge"><stop offset="0" stop-color="#fff0cc"/>'
          '<stop offset="0.25" stop-color="#ffc36c" stop-opacity="0.9"/>'
          '<stop offset="0.55" stop-color="#f49d4b" stop-opacity="0.35"/>'
          '<stop offset="1" stop-color="#f49d4b" stop-opacity="0"/>'
          '</radialGradient></defs>')
    s += circle(354, 397, 253, "url(#charge)")
    s += ('<circle cx="354" cy="397" r="160" fill="none" '
          f'stroke="{GOLD}" stroke-width="2" stroke-dasharray="8 9"/>')
    s += circle(354, 397, 4, INK) + line(354, 397, 514, 397, GOLD, 3)
    s += text(433, 375, "r rms", 27, GOLD, "middle")
    s += line(194, 397, 194, 608, "#557086", 1, "5 7")
    s += line(514, 397, 514, 608, "#557086", 1, "5 7")
    s += bracket(194, 514, 603, "2 × r rms", GOLD, 34)
    s += text(696, 307, "≈ 3.36 fm", 68, GOLD, weight="bold")
    s += text(700, 362, "Charge spread", 30)
    s += text(700, 403, "rather than a sharp surface", 26, MUTED)
    s += line(700, 446, 1105, 446, "#2d4358", 1)
    s += text(700, 492, "r rms = 1.6785 fm", 29)
    s += text(700, 533, "CODATA 2022 recommended value", 23, MUTED)
    s += text(600, 704, "Cloud and dashed radius marker are schematic, not a measured density map.", 23, MUTED, "middle")
    records.append(save("helium_nucleus_charge_diameter", footer(s, "NIST · CODATA 2022"), {
        "source": "https://physics.nist.gov/cuu/Constants/Table/allascii.txt",
        "title": "Helium-4 nucleus — original rms charge-diameter diagram",
    }, "NIST lists an alpha-particle rms charge radius of 1.6785(21) fm. "
       "The displayed diameter is twice this radius, rounded to 3.36 fm. "
       "The soft cloud is illustrative and the dashed circle marks an rms radius, "
       "not a nuclear surface or an enclosed-charge fraction."))

    s = frame("PSR J0437–4715", "Neutron-star size inferred from NICER X-ray pulse modeling · 2024 result")
    s += ('<defs><radialGradient id="star" cx="35%" cy="29%" r="76%">'
          '<stop offset="0" stop-color="#d7f5ff"/><stop offset="0.37" stop-color="#70c9ea"/>'
          '<stop offset="0.75" stop-color="#237aab"/><stop offset="1" stop-color="#113654"/>'
          '</radialGradient><clipPath id="disk"><circle cx="350" cy="393" r="178"/>'
          '</clipPath></defs>')
    s += circle(350, 393, 193, "#77c9eb", opacity=0.06)
    s += circle(350, 393, 184, "#77c9eb", opacity=0.09)
    s += circle(350, 393, 178, "url(#star)", "#b1e2f4", 1)
    s += '<g clip-path="url(#disk)" fill="none" stroke="#d5f1ff" opacity="0.22" stroke-width="1.3">'
    for ry in [37, 100, 155]:
        s += f'<ellipse cx="350" cy="393" rx="178" ry="{ry}"/>'
    for rx in [62, 125]:
        s += f'<ellipse cx="350" cy="393" rx="{rx}" ry="178"/>'
    s += '</g>' + line(172, 393, 528, 393, GOLD, 3, "7 6")
    s += line(172, 393, 172, 615, "#557086", 1, "5 7")
    s += line(528, 393, 528, 615, "#557086", 1, "5 7")
    s += bracket(172, 528, 610, "≈ 22.7 km", GOLD, 40)
    s += text(680, 306, "A star on a city’s scale", 35, weight="bold")
    s += text(680, 367, "Equatorial radius", 27, MUTED)
    s += text(680, 429, "11.36 km", 56, BLUE)
    s += line(680, 465, 1120, 465, "#2d4358", 1)
    s += text(680, 511, "Diameter = 2 × radius", 30)
    s += text(680, 551, "Inferred from a physical model", 25, MUTED)
    s += text(600, 705, "Original size diagram · surface color and grid are illustrative, not an image of the star.", 22, MUTED, "middle")
    records.append(save("psr_j0437_4715_neutron_star", footer(s, "NASA / NICER · Choudhury et al. (2024)"), {
        "source": "https://heasarc.gsfc.nasa.gov/docs/nicer/science_nuggets/20240822.html",
        "title": "PSR J0437-4715 — original NICER equatorial-diameter diagram",
    }, "NASA's 22 August 2024 NICER summary gives an inferred equatorial radius "
       "of 11.36 km with 5–8% uncertainties. The diameter is twice the reported "
       "central radius, 22.72 km, shown as approximately 22.7 km. This is explicitly "
       "the 2024 result used by the dataset, not a claim to be a new radius analysis. "
       "Sphere color and coordinate grid are illustrative; no hot-spot geometry is invented."))

    s = frame("Milky Way central bar", "A long concentration of stars through the Galactic center · face-on schematic")
    s += ('<defs><radialGradient id="diskglow"><stop offset="0" stop-color="#92b9d3" stop-opacity="0.2"/>'
          '<stop offset="1" stop-color="#92b9d3" stop-opacity="0"/></radialGradient>'
          '<radialGradient id="barglow"><stop offset="0" stop-color="#ffe8bc"/>'
          '<stop offset="0.4" stop-color="#ffc26f" stop-opacity="0.6"/>'
          '<stop offset="1" stop-color="#ffc26f" stop-opacity="0"/></radialGradient></defs>')
    s += circle(365, 399, 239, "url(#diskglow)")
    rng = random.Random(150401401)
    for i in range(720):
        a = rng.random() * math.tau
        r = 230 * math.sqrt(rng.random())
        x, y = 365 + r * math.cos(a), 399 + r * math.sin(a)
        s += circle(round(x, 2), round(y, 2), round(rng.uniform(0.5, 1.5), 2), "#a3bfd3", opacity=0.45)
    # The long axis is at 30 degrees to the downward center-to-Sun ray.
    # Its 400 px end-to-end ruler corresponds to the source's ~10 kpc long-bar fit.
    s += '<g transform="translate(365 399) rotate(-60)">'
    s += '<ellipse rx="232" ry="61" fill="url(#barglow)"/>'
    for i in range(700):
        x = rng.uniform(-200, 200)
        y = rng.gauss(0, 12) * math.sqrt(max(0, 1 - (x / 205) ** 2))
        s += circle(round(x, 2), round(y, 2), round(rng.uniform(0.7, 1.7), 2), GOLD, opacity=0.7)
    s += line(-200, 0, 200, 0, GOLD, 2, "5 6")
    s += line(-200, 0, -200, -78, "#9b917e", 1, "4 6")
    s += line(200, 0, 200, -78, "#9b917e", 1, "4 6")
    s += bracket(-200, 200, -74, "", GOLD)
    s += '</g>'
    s += line(365, 399, 365, 663, "#7e9bb3", 2, "5 8")
    s += circle(365, 399, 4, INK) + circle(365, 650, 6, BLUE)
    # 30 degree angular arc between the Sun ray and one end of the bar.
    s += '<path d="M 365 479 A 80 80 0 0 0 405 468.28" fill="none" stroke="#83d8f2" stroke-width="2"/>'
    s += text(398, 515, "~30°", 27, BLUE)
    s += text(365, 694, "Sun direction", 24, BLUE, "middle")
    s += text(725, 303, "≈ 10 kpc", 64, GOLD, weight="bold")
    s += text(730, 351, "Bar length, end to end", 28)
    s += line(730, 393, 1115, 393, "#2d4358", 1)
    s += text(730, 439, "~5 kpc half-length", 30)
    s += text(730, 480, "Red-clump star-count model", 24, MUTED)
    s += text(730, 541, "Length depends on the method", 24, MUTED)
    s += text(730, 578, "and on the bar definition.", 24, MUTED)
    s += text(600, 728, "Illustrative stars, bar width and Sun placement · not a catalog map or an external photograph.", 21, MUTED, "middle")
    records.append(save("milky_way_central_bar", footer(s, "Wegg, Gerhard & Portail (2015)"), {
        "source": "https://arxiv.org/abs/1504.01401",
        "title": "Milky Way central bar — original long-bar measurement schematic",
    }, "Wegg, Gerhard and Portail (2015) infer a 5.0 ± 0.2 kpc half-length for "
       "their two-component bar and an angle of 28–33 degrees to the Sun–center "
       "line. The diagram uses an approximately 10 kpc full length and 30-degree "
       "orientation. Random star glyphs, the bar width and the Sun's radial "
       "placement are illustrative, explicitly not measured catalog positions. "
       "No spiral-arm geometry is asserted."))

    s = frame("Baryon acoustic oscillation scale", "A preferred separation in cosmic clustering · a statistical standard ruler")
    # One separation, NOT the diameter of a single physical cosmic bubble.
    rng = random.Random(150)
    for i in range(230):
        x, y = rng.uniform(80, 1120), rng.uniform(205, 454)
        s += circle(round(x, 2), round(y, 2), round(rng.uniform(0.8, 2.5), 2), "#9cb6cf", opacity=0.6)
    for x, y in [(280, 345), (920, 345)]:
        for r, op in [(35, .025), (22, .055), (12, .12)]:
            s += circle(x, y, r, BLUE, opacity=op)
        s += f'<ellipse cx="{x}" cy="{y}" rx="10" ry="4" fill="{BLUE}" transform="rotate(-30 {x} {y})"/>'
        s += circle(x, y, 3, INK)
    s += line(280, 345, 280, 491, "#6e8aa3", 2, "5 8")
    s += line(920, 345, 920, 491, "#6e8aa3", 2, "5 8")
    s += bracket(280, 920, 486, "≈ 150 Mpc", GOLD, 62)
    s += text(600, 597, "Present-day comoving separation", 27, MUTED, "middle")
    s += text(600, 654, "Pairs are slightly more common around this distance.", 30, INK, "middle")
    s += text(600, 705, "Conceptual galaxy pair · not a measured pair, a structure boundary or a bubble diameter.", 22, MUTED, "middle")
    records.append(save("baryon_acoustic_oscillation_scale", footer(s, "DESI · the BAO standard ruler"), {
        "source": "https://www.desi.lbl.gov/2026/07/30/new-desi-dr2-lyman-alpha-results-shed-light-on-dark-energy/",
        "title": "Baryon acoustic oscillation scale — original galaxy-pair separation diagram",
    }, "DESI describes BAO as a slight excess of tracer pairs separated by about "
       "150 Mpc, inherited from early-plasma sound waves. The diagram labels "
       "one present-day comoving pair separation, not a bubble diameter. The "
       "galaxy glyphs are illustrative, not a catalog or a measured pair. "
       "No numerical correlation-function data are invented or plotted."))

    credits_path = ROOT / "images/credits/length.json"
    data = json.loads(credits_path.read_text())
    new_files = {r["file"] for r in records}
    data["images"] = [r for r in data["images"] if r["file"] not in new_files] + records
    credits_path.write_text(json.dumps(data, indent=1) + "\n")
    (HERE / "credits-added.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    (OUT / "LICENSE.txt").write_text(
        "To the extent possible under law, Universe Scales waives all copyright "
        "and related or neighboring rights in the original diagrams in this "
        "directory under CC0 1.0 Universal.\n"
        "https://creativecommons.org/publicdomain/zero/1.0/\n"
        "Scientific facts are cited in ../sources/. No source artwork was copied.\n")
    print(f"Built {len(records)} original diagrams, full JPEGs and thumbnails.")


if __name__ == "__main__":
    main()
