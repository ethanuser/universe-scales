#!/usr/bin/env python3
"""Direct small-canvas CPU readability checks, not production screenshots."""
import json
from pathlib import Path

from PIL import Image, ImageDraw
from render_earth3d_previews import parts, render

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / 'handoff/volume3d'


def main():
    entries = [json.loads(p.read_text()) for p in sorted(HANDOFF.glob('*.entry.json'))]
    sheet = Image.new('RGB', (1000, 220 * len(entries) + 50), '#101927')
    draw = ImageDraw.Draw(sheet)
    for row, entry in enumerate(entries):
        scene, _ = parts(ROOT / entry['src'], entry['presentation'])
        draw.text((16, row * 220 + 15), entry['id'], fill='white')
        for column, size in enumerate((48, 96, 160)):
            picture, _ = render(scene, False, size)
            x, y = 380 + column * 200, row * 220 + 120 - size // 2
            sheet.paste(picture, (x, y))
            draw.text((x, row * 220 + 205), f'{size} px canvas', fill='white')
    draw.text((16, sheet.height - 30),
              'CPU orthographic, individually fitted canvases; readability only. No WebGL / UI / mobile certification.',
              fill='#ddbd80')
    output = HANDOFF / 'previews/small.png'
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


if __name__ == '__main__':
    main()
