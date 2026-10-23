#!/usr/bin/env python3
"""CPU-only rest/side/small review; explicitly not production WebGL approval."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from render_earth3d_previews import parts, render
from preview_deepsky3d_cpu import render as render_points

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / 'handoff/retry3d'


def main():
    destination = HANDOFF / 'previews'
    destination.mkdir(parents=True, exist_ok=True)
    records, panels = [], []
    for file in sorted(HANDOFF.glob('*.entry.json')):
        entry = json.loads(file.read_text())
        if entry['geometry'] == 'points':
            pair = Image.new('RGB', (1400, 790), '#070d18')
            for i, yaw in enumerate((0, 90)):
                picture, extent = render_points(entry, yaw, drawn_pixels=560, canvas_size=700)
                pair.paste(picture, (i * 700, 0))
            draw = ImageDraw.Draw(pair)
            draw.text((12, 708), entry['id'] + ' | REST / SIDE | measured sky plane, zero invented depth', fill='white')
            draw.text((12, 730), 'CPU soft-point approximation - not WebGL / explorer / mobile verification', fill='#ddbd80')
            pair.save(destination / (entry['id'] + '.png'))
            small, _ = render_points(entry, drawn_pixels=120, canvas_size=150)
            small.save(destination / (entry['id'] + '-small.png'))
            panels.append(pair.resize((1120, 632)))
            continue
        scene, bounds = parts(ROOT / entry['src'], entry['presentation'])
        pair = Image.new('RGB', (1400, 790), '#101927')
        record = dict(id=entry['id'], native_extent_m=bounds,
                      native_vertical_extent_per_value=bounds[1] / entry['presentation']['reference_size'])
        for i, side in enumerate((False, True)):
            picture, extent = render(scene, side, 700)
            pair.paste(picture, (i * 700, 0))
            record['side_extent' if side else 'rest_extent'] = extent
        draw = ImageDraw.Draw(pair)
        draw.text((12, 708), entry['id'] + ' | REST / SIDE | 1x vertical scale', fill='white')
        draw.text((12, 730), 'UNREGISTERED CANDIDATE: horizontal footprint exceeds the listed vertical quantity.', fill='#edc986')
        draw.text((12, 752), 'CPU ORTHOGRAPHIC PREVIEW - no WebGL / production lighting / explorer / mobile verification', fill='#ddbd80')
        pair.save(destination / (entry['id'] + '.png'))
        small, _ = render(scene, False, 140)
        small.save(destination / (entry['id'] + '-small.png'))
        panels.append(pair.resize((1120, 632)))
        records.append(record)
        print(json.dumps(record), flush=True)
    sheet = Image.new('RGB', (1120, 632 * len(panels)), '#101927')
    for i, panel in enumerate(panels):
        sheet.paste(panel, (0, 632 * i))
    sheet.save(destination / 'overview.png')
    (destination / 'geometry-audit.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
