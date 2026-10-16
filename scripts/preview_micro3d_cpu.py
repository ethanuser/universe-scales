#!/usr/bin/env python3
"""Labeled orthographic CPU review; does not certify WebGL, UI or lighting."""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from render_earth3d_previews import accessor, parts, render, rotation
from render_glb_preview import read_glb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'handoff/micro3d/previews'


def labels(picture, entry, scene, side):
    """Project current assets' root label nodes using the same geometry camera.

    Labels are a legibility approximation: production SVG priority/fades differ.
    Refuse transformed/hierarchical nodes instead of silently misplacing labels.
    """
    doc, binary = read_glb(ROOT/entry['src'])
    for node in doc['nodes']:
        if any(k in node for k in ['children', 'rotation', 'scale', 'matrix']):
            raise ValueError('This batch preview expects untransformed root meshes/labels')
    raw = np.concatenate([accessor(doc, binary, p['attributes']['POSITION'])
                          for m in doc['meshes'] for p in m['primitives']])
    center = (raw.min(0)+raw.max(0))/2
    pose = entry['presentation']
    transform = rotation(pose.get('pitch', 0), pose.get('yaw', 0), pose.get('roll', 0))
    view = rotation(0, 90 if side else 0, 0)
    points = np.concatenate([p['pos'] @ view.T for p in scene])
    lo, hi = points.min(0), points.max(0)
    factor = picture.width*.84/max((hi-lo)[:2])
    view_center = (hi+lo)/2
    draw = ImageDraw.Draw(picture)
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
    for node in doc['nodes']:
        label = node.get('extras', {}).get('label')
        if not label: continue
        p = (np.array(node.get('translation', [0, 0, 0]))-center)/pose['reference_size']
        p = p @ transform.T @ view.T
        xy = (p-view_center)[:2]*factor*[1, -1]+picture.width/2
        # Keep all text visible for review; SVG hides/clips/declutters differently.
        width = draw.textlength(label, font=font)
        xy[0] = np.clip(xy[0], width/2+5, picture.width-width/2-5)
        xy[1] = np.clip(xy[1], 12, picture.height-12)
        draw.text(tuple(xy), label, font=font, fill='#edf3f5', anchor='mm',
                  stroke_width=2, stroke_fill='#101927')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    entries = [json.loads(p.read_text()) for p in sorted((ROOT/'handoff/micro3d').glob('*.entry.json'))]
    entries.append(dict(id='earth-prem-context', src='handoff/micro3d/earth-prem-context.glb',
                        presentation=dict(reference_size=12742, yaw=-32, pitch=18)))
    entries.append(dict(id='transistor-stack-context', src='handoff/micro3d/transistor-stack-context.glb',
                        presentation=dict(reference_size=14, yaw=-15, pitch=10)))
    tiles, results = [], []
    for entry in entries:
        scene, bounds = parts(ROOT/entry['src'], entry['presentation'])
        pair = Image.new('RGB', (1000, 555), '#101927')
        record = dict(id=entry['id'], source_bounds=bounds)
        for i, side in enumerate([False, True]):
            picture, extent = render(scene, side, 500)
            labels(picture, entry, scene, side)
            pair.paste(picture, (i*500, 0))
            record['side_extent' if side else 'rest_extent'] = extent
        draw = ImageDraw.Draw(pair)
        draw.text((12, 508), entry['id']+' | REST / QUARTER CAMERA', fill='white')
        draw.text((12, 530), 'CPU geometry / approximate labels - not WebGL, production SVG, explorer or mobile verification', fill='#ddbd80')
        pair.save(OUT/(entry['id']+'.png'))
        tiles.append(pair.resize((720, 400)))
        results.append(record)
        print(json.dumps(record), flush=True)
    overview = Image.new('RGB', (1440, math.ceil(len(tiles)/2)*400), '#101927')
    for i, tile in enumerate(tiles): overview.paste(tile, ((i % 2)*720, (i//2)*400))
    overview.save(OUT/'overview.png')
    (OUT/'geometry-audit.json').write_text(json.dumps(results, indent=2)+'\n')


if __name__ == '__main__': main()
