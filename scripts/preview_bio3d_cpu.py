#!/usr/bin/env python3
"""Read final GLBs; render rest/side geometry with chain colors without WebGL.

These labeled, orthographic CPU previews are not production screenshots.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from build_bio3d_models import HANDOFF, ROOT
from render_glb_preview import accessor, read_glb


def rotation(pitch, yaw, roll):
    x, y, z = np.radians([pitch, yaw, roll])
    rx = np.array([[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]])
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rz = np.array([[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]])
    return rx @ ry @ rz


def render(entry, output, side=False, width=1000, height=800):
    doc, binary = read_glb(ROOT / entry['src'])
    pose = entry['presentation']
    matrix = rotation(pose.get('pitch', 0), pose.get('yaw', 0)+(90 if side else 0), pose.get('roll', 0))
    parts = []
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            a = p['attributes']
            points = accessor(doc, binary, a['POSITION']).astype(float) @ matrix.T
            indices = accessor(doc, binary, p['indices']).reshape(-1, 3)
            if 'COLOR_0' in a:
                colors = accessor(doc, binary, a['COLOR_0'])[:, :3].astype(float)/255
            else:
                material = doc['materials'][p['material']]['pbrMetallicRoughness']['baseColorFactor'][:3]
                colors = np.tile(material, (len(points), 1))
            n = accessor(doc, binary, a['NORMAL']).astype(float) @ matrix.T
            # Linear material colors -> approximate display gamma.
            light = np.array([-.35, .6, 1]); light /= np.linalg.norm(light)
            shade = .32+.75*np.maximum(0, n @ light)
            color = np.clip(colors*shade[:, None], 0, 1)**(1/2.2)
            face_color = np.round(color[indices].mean(1)*255).astype(np.uint8)
            parts.append((points[indices], face_color))
    triangles = np.concatenate([p[0] for p in parts]); colors = np.concatenate([p[1] for p in parts])
    low, high = triangles.min((0, 1)), triangles.max((0, 1))
    extent = high-low; center = (low+high)/2
    scale = min((width-140)/extent[0], (height-200)/extent[1])
    screen = np.stack(((triangles[..., 0]-center[0])*scale+width/2,
                       -(triangles[..., 1]-center[1])*scale+height/2-12), axis=-1)
    aa = 2
    image = Image.new('RGB', (width*aa, height*aa), '#101a22')
    draw = ImageDraw.Draw(image)
    for i in np.argsort(triangles[..., 2].mean(1)):
        draw.polygon([tuple(v*aa) for v in screen[i]], fill=tuple(colors[i]))
    image = image.resize((width, height), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16)
    except OSError:
        font = ImageFont.load_default()
    view = 'side' if side else 'rest'
    draw.text((25, 22), entry.get('display_label', entry['name']), fill='#e6f2f1', font=font)
    draw.text((25, 46), f"{entry['processing']['pdb']} · {view} · chain colors are illustrative", fill='#93adaf', font=font)
    draw.text((25, height-45), 'CPU geometry preview · orthographic · browser verification pending', fill='#93adaf', font=font)
    bar = entry['presentation']['reference_size']/2
    draw.line([(width-45-bar*scale, height-74), (width-45, height-74)], fill='#b6cfce', width=2)
    draw.text((width-45-bar*scale/2, height-65), f'{bar:g} nm', anchor='mt', fill='#b6cfce', font=font)
    output.parent.mkdir(parents=True, exist_ok=True); image.save(output)
    return {'id': entry['id'], 'view': view, 'extent_nm': extent.tolist(),
            'orthographic_extent_per_value': float(max(extent[:2])/pose['reference_size']), 'path': str(output)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, default=HANDOFF/'previews')
    args = p.parse_args()
    audit = []
    for path in sorted(HANDOFF.glob('*.entry.json')):
        entry = json.loads(path.read_text())
        for side in (False, True):
            result = render(entry, args.output_dir/f"{entry['id']}-{'side' if side else 'rest'}.png", side)
            audit.append(result); print(json.dumps(result), flush=True)
    (args.output_dir/'geometry-audit.json').write_text(json.dumps(audit, indent=2)+'\n')


if __name__ == '__main__':
    main()
