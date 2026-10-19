#!/usr/bin/env python3
"""Orthographic review of existing earth3d4 scans; not WebGL verification.

Optional --staged DIR regenerates the original fly's calibration illustration.
The illustration is review evidence, not part of any model or runtime scene.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from render_earth3d_previews import parts, render

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / 'handoff/earth3d4'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', type=Path)
    args = parser.parse_args()
    destination = HANDOFF / 'previews'
    destination.mkdir(exist_ok=True)
    records, panels = [], []
    for file in sorted(HANDOFF.glob('*.entry.json')):
        entry = json.loads(file.read_text())
        scene, bounds = parts(ROOT / entry['src'], entry['presentation'])
        pair = Image.new('RGB', (1400, 765), '#101927')
        record = dict(id=entry['id'], source_bounds=bounds)
        for i, side in enumerate((False, True)):
            picture, extent = render(scene, side, 700)
            pair.paste(picture, (i * 700, 0))
            record['side_extent' if side else 'rest_extent'] = extent
        draw = ImageDraw.Draw(pair)
        draw.text((12, 708), entry['id'] + ' | REST / SIDE', fill='white')
        draw.text((12, 730), 'CPU ORTHOGRAPHIC PREVIEW - not WebGL / transparency / reflections / UI verification', fill='#ddbd80')
        pair.save(destination / (entry['id'] + '.png'))
        panels.append(pair.resize((1120, 612)))
        records.append(record)
        print(json.dumps(record), flush=True)
    sheet = Image.new('RGB', (1120, 612 * len(panels)), '#101927')
    for i, panel in enumerate(panels):
        sheet.paste(panel, (0, 612 * i))
    sheet.save(destination / 'overview.png')
    (destination / 'geometry-audit.json').write_text(json.dumps(records, indent=2) + '\n')

    if args.staged:
        source = args.staged / 'ad29b897bd2b4e27bb04ab9d31baa117.glb'
        calibration = json.loads((HANDOFF / 'fly-calibration.json').read_text())
        scene, bounds = parts(source, {})
        points = np.concatenate([part['pos'] for part in scene]) * max(bounds)
        picture = Image.new('RGB', (1100, 730), '#101927')
        draw = ImageDraw.Draw(picture)
        for z, y in points[::12, [2, 1]]:
            x, py = int(550 + z * 470), int(380 - y * 470)
            if 0 <= x < 1100 and 0 <= py < 680:
                picture.putpixel((x, py), (190, 100, 50))
        locations = [(550 + p[2] * 470, 380 - p[1] * 470)
                     for p in calibration['landmarks_centered_source_units']]
        draw.line(locations, fill='#75d6ff', width=2)
        for (x, y), name in zip(locations, ('Abdomen tip', 'Anterior head surface')):
            draw.ellipse((x-6, y-6, x+6, y+6), outline='#c5f2ff', width=2)
            draw.text((x-30, y+15), name, fill='white')
        draw.text((20, 15), 'Original CT mesh: side projection with selected body-length surface vertices', fill='white')
        draw.text((20, 685), 'CALIBRATION REVIEW ONLY | point subsample | coordinates in fly-calibration.json', fill='#ddbd80')
        picture.save(destination / 'fly-calibration.png')


if __name__ == '__main__':
    main()
