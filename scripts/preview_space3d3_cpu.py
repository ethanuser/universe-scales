#!/usr/bin/env python3
"""CPU orthographic review of space3d3 meshes, lines and catalog points.

No browser, WebGL, production SVG label collision, perspective, shadow maps,
normal maps, or hardware performance is verified by these images.
"""
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from fetch_model_assets import read_glb, view_bytes, write_json
from preview_space3d_cpu import rotation
from render_glb_preview import accessor, node_matrix

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT/'handoff/space3d3'


def read_scene(data):
    doc, binary = read_glb(data)
    textures = [np.asarray(Image.open(io.BytesIO(view_bytes(doc, binary, i['bufferView']))).convert('RGBA'))/255
                for i in doc.get('images', [])]
    primitives, labels = [], []
    def visit(index, parent):
        node = doc['nodes'][index]
        matrix = parent @ node_matrix(node)
        if node.get('extras', {}).get('label'):
            labels.append((matrix[:3, 3], node['extras']['label']))
        if 'mesh' in node:
            for q in doc['meshes'][node['mesh']]['primitives']:
                a = q['attributes']
                points = accessor(doc, binary, a['POSITION'])
                points = (np.column_stack((points, np.ones(len(points)))) @ matrix.T)[:, :3]
                normal = accessor(doc, binary, a['NORMAL']) if 'NORMAL' in a else np.zeros_like(points)
                normal = normal @ np.linalg.inv(matrix[:3, :3])
                normal /= np.maximum(np.linalg.norm(normal, axis=1)[:, None], 1e-20)
                index = accessor(doc, binary, q['indices']).ravel() if 'indices' in q else np.arange(len(points))
                uv = accessor(doc, binary, a['TEXCOORD_0']) if 'TEXCOORD_0' in a else np.zeros((len(points), 2))
                material = doc['materials'][q.get('material', 0)]
                pbr = material.get('pbrMetallicRoughness', {})
                slot = pbr.get('baseColorTexture')
                texture = textures[doc['textures'][slot['index']]['source']] if slot else None
                color = np.asarray(pbr.get('baseColorFactor', [1, 1, 1, 1]), dtype=float)
                primitives.append(dict(p=points, n=normal, i=index, uv=uv, texture=texture,
                                       color=color, vertex_colors=(accessor(doc, binary, a['COLOR_0']) if 'COLOR_0' in a else None), material=material, mode=q.get('mode', 4)))
        for child in node.get('children', []):
            visit(child, matrix)
    for root in doc['scenes'][doc.get('scene', 0)]['nodes']:
        visit(root, np.eye(4))
    return primitives, labels


def render(data, pose, quarter=False, size=560):
    primitives, labels = read_scene(data)
    points = np.concatenate([q['p'] for q in primitives])
    pivot = (points.min(axis=0)+points.max(axis=0))/2
    rot = rotation(pose)
    if quarter:
        # Camera yaw relative to the rest scene, so a thin patch becomes edge-on.
        rot = rotation({'yaw': 90}) @ rot
    for q in primitives:
        q['p'] = (q['p']-pivot) @ rot.T
        q['n'] = q['n'] @ rot.T
    points = np.concatenate([q['p'] for q in primitives])
    center = (points.min(axis=0)+points.max(axis=0))/2
    extent = np.ptp(points, axis=0)
    scale = size*.80/max(extent[:2])
    def project(p):
        return (p-center)*[scale, -scale, 1]+[size/2, size/2, 0]
    canvas = np.full((size, size, 3), [.026, .043, .071])
    depth = np.full((size, size), -np.inf)
    light = np.array([-.45, .65, .8]); light /= np.linalg.norm(light)
    # Source ordering retains NASA ring faces after the opaque globe.
    for q in primitives:
        if q['mode'] != 4:
            continue
        material = q['material']
        screen = project(q['p'])
        for ids in q['i'].reshape(-1, 3):
            tri = screen[ids]
            a, b, c = tri[:, :2]
            area = (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
            if abs(area) < 1e-10 or (not material.get('doubleSided') and area > 0):
                continue
            lo = np.maximum(np.floor(tri[:, :2].min(axis=0)).astype(int), 0)
            hi = np.minimum(np.ceil(tri[:, :2].max(axis=0)).astype(int)+1, size)
            if np.any(lo >= hi):
                continue
            xx, yy = np.meshgrid(np.arange(lo[0], hi[0])+.5, np.arange(lo[1], hi[1])+.5)
            w1 = ((xx-a[0])*(c[1]-a[1])-(yy-a[1])*(c[0]-a[0]))/area
            w2 = ((b[0]-a[0])*(yy-a[1])-(b[1]-a[1])*(xx-a[0]))/area
            weights = np.stack((1-w1-w2, w1, w2), axis=-1)
            z = weights @ tri[:, 2]
            region = np.s_[lo[1]:hi[1], lo[0]:hi[0]]
            mask = (weights.min(axis=-1) >= -1e-7) & (z > depth[region])
            if not mask.any():
                continue
            rgba = np.broadcast_to(q['color'], (*xx.shape, 4)).copy()
            if q['vertex_colors'] is not None:
                vertex = q['vertex_colors'][ids]
                rgba[..., :vertex.shape[1]] *= weights @ vertex
            if q['texture'] is not None:
                uv = np.clip(weights @ q['uv'][ids], 0, .999999)
                tx = (uv[..., 0]*q['texture'].shape[1]).astype(int)
                ty = (uv[..., 1]*q['texture'].shape[0]).astype(int)
                rgba *= q['texture'][ty, tx]
            n = weights @ q['n'][ids]
            n /= np.maximum(np.linalg.norm(n, axis=-1)[..., None], 1e-20)
            lambert = np.abs(n @ light) if material.get('doubleSided') else np.maximum(n @ light, 0)
            emission = np.array(material.get('emissiveFactor', [0, 0, 0]))
            rgb = rgba[..., :3]*(.25+.65*lambert[..., None])
            if 'KHR_materials_unlit' in material.get('extensions', {}):
                rgb = rgba[..., :3]
            if material.get('emissiveTexture'):
                rgb += rgba[..., :3]*emission
            else:
                rgb += emission
            alpha = rgba[..., 3] if material.get('alphaMode') == 'BLEND' else np.ones_like(xx)
            if material.get('alphaMode') == 'MASK':
                mask &= rgba[..., 3] >= material.get('alphaCutoff', .5)
            canvas[region][mask] = (rgb*alpha[..., None]+canvas[region]*(1-alpha[..., None]))[mask]
            depth[region][mask & (alpha > .5)] = z[mask & (alpha > .5)]
    image = Image.fromarray(np.uint8(np.clip(canvas, 0, 1)*255))
    draw = ImageDraw.Draw(image)
    # CPU overlays are approximations, not the site's SVG collision/opacity rules.
    for q in primitives:
        screen = project(q['p'])
        color = tuple(np.uint8(np.clip(q['color'][:3]*255, 0, 255)))
        if q['mode'] == 1:
            for pair in screen[q['i']].reshape(-1, 2, 3):
                draw.line([tuple(a[:2]) for a in pair], fill=color, width=1)
        if q['mode'] == 0:
            for index, p in enumerate(screen):
                point_color = color
                if q['vertex_colors'] is not None:
                    point_color = tuple(np.uint8(np.clip(q['vertex_colors'][index, :3]*255, 0, 255)))
                draw.ellipse((p[0]-2, p[1]-2, p[0]+2, p[1]+2), fill=point_color)
    for p, label in labels:
        p = project((p-pivot) @ rot.T)
        width = draw.textlength(label)
        draw.text((max(4, min(size-width-4, p[0]-width/2)), max(4, min(size-16, p[1]-17))), label, fill='#dae8f8')
    return image, extent


def main():
    dest = HANDOFF/'previews'; dest.mkdir(parents=True, exist_ok=True)
    entries = [json.loads(p.read_text()) for p in sorted(HANDOFF.glob('*.entry.json'))]
    overview, audit = [], []
    for entry in entries:
        panel = Image.new('RGB', (1120, 620), '#07121e')
        for i in range(2):
            im, extent = render((ROOT/entry['src']).read_bytes(), entry['presentation'], bool(i))
            panel.paste(im, (i*560, 28))
            ImageDraw.Draw(panel).text((12+i*560, 8), entry['id']+' | '+('quarter camera' if i else 'rest'), fill='white')
            if not i:
                ratio = max(extent[:2])/entry['presentation']['reference_size']
                audit.append({'id': entry['id'], 'extent_per_catalog_value': float(ratio),
                              'width_per_value': float(extent[0]/entry['presentation']['reference_size']),
                              'passes_extent_rule': bool(.6 <= ratio <= 1.3)})
                overview.append((entry['id'], im.resize((300, 300))))
        ImageDraw.Draw(panel).text((12, 599), 'CPU ORTHOGRAPHIC APPROXIMATION · no WebGL, perspective, production labels, or mobile verification', fill='#d4ba81')
        panel.save(dest/(entry['id']+'.png'))
        print(entry['id'], audit[-1]['extent_per_catalog_value'], flush=True)
    sheet = Image.new('RGB', (1200, math.ceil(len(overview)/4)*326), '#07121e')
    for i, (name, im) in enumerate(overview):
        x, y = i%4*300, i//4*326
        sheet.paste(im, (x, y+20)); ImageDraw.Draw(sheet).text((x+7, y+5), name, fill='white')
    sheet.save(dest/'overview.jpg', quality=94)
    write_json(dest/'geometry-audit.json', {'method': 'CPU orthographic geometry, all primitive types; not production/WebGL verification', 'models': audit})


if __name__ == '__main__':
    main()
