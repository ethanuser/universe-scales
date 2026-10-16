#!/usr/bin/env python3
"""Textured orthographic CPU review, NOT WebGL or production UI verification.

Implements a z-buffer, UV sampling, diffuse lighting and material alpha. It omits
normal maps, reflections, tone mapping, perspective and glTF material extensions.
"""
import argparse
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from fetch_model_assets import read_glb, view_bytes
from render_glb_preview import accessor, node_matrix


def rotation(pose):
    x, y, z = [math.radians(pose.get(k, 0)) for k in ['pitch', 'yaw', 'roll']]
    rx = np.array([[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]])
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rz = np.array([[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]])
    return rx @ ry @ rz  # Three.js intrinsic XYZ


def parts(data, pose):
    doc, binary = read_glb(data)
    textures = [np.asarray(Image.open(io.BytesIO(view_bytes(doc, binary, i['bufferView']))).convert('RGBA')) / 255
                for i in doc.get('images', [])]
    output = []

    def visit(index, parent):
        node = doc['nodes'][index]
        world = parent @ node_matrix(node)
        if 'mesh' in node:
            for primitive in doc['meshes'][node['mesh']]['primitives']:
                if primitive.get('mode', 4) != 4:
                    continue
                a = primitive['attributes']
                p = accessor(doc, binary, a['POSITION'])
                p = (np.column_stack((p, np.ones(len(p)))) @ world.T)[:, :3]
                normal = accessor(doc, binary, a['NORMAL']) if 'NORMAL' in a else np.zeros_like(p)
                normal = normal @ np.linalg.inv(world[:3, :3])
                normal /= np.maximum(np.linalg.norm(normal, axis=1)[:, None], 1e-20)
                indices = (accessor(doc, binary, primitive['indices']).ravel()
                           if 'indices' in primitive else np.arange(len(p))).reshape(-1, 3)
                uv = accessor(doc, binary, a['TEXCOORD_0']) if 'TEXCOORD_0' in a else np.zeros((len(p), 2))
                material = doc.get('materials', [{}])[primitive.get('material', 0)]
                pbr = material.get('pbrMetallicRoughness', {})
                slot = pbr.get('baseColorTexture')
                color = np.array(pbr.get('baseColorFactor', [1, 1, 1, 1]), dtype=float)
                if material.get('emissiveTexture') and max(material.get('emissiveFactor', [0, 0, 0])) > 0:
                    slot = material['emissiveTexture']
                    color = np.array([*material['emissiveFactor'], 1.], dtype=float)
                    material = {**material, 'cpuSelfLuminous': True}
                texture = textures[doc['textures'][slot['index']]['source']] if slot else None
                output.append((p, normal, indices, uv, color, texture, material))
        for child in node.get('children', []):
            visit(child, world)
    initial = np.eye(4)
    pre = pose.get('pre_rotation', {})
    initial[:3, :3] = rotation(dict(zip(['pitch', 'yaw', 'roll'], [pre.get(a, 0) for a in 'xyz'])))
    for root in doc['scenes'][doc.get('scene', 0)]['nodes']:
        visit(root, initial)
    all_points = np.concatenate([p[0] for p in output])
    center = (all_points.min(axis=0) + all_points.max(axis=0)) / 2
    rot = rotation(pose)
    return [((p-center) @ rot.T, n @ rot.T, i, uv, c, t, m) for p, n, i, uv, c, t, m in output]


def render(data, pose, side=False, size=480):
    scene = parts(data, pose)
    side_rotation = rotation({'yaw': 90}) if side else np.eye(3)
    scene = [(p @ side_rotation.T, n @ side_rotation.T, i, uv, c, t, m) for p, n, i, uv, c, t, m in scene]
    all_points = np.concatenate([p[0] for p in scene])
    bounds = np.ptp(all_points, axis=0)
    scale = size * .84 / max(bounds[:2])
    center = (all_points.min(axis=0) + all_points.max(axis=0)) / 2
    image = np.full((size, size, 3), [0.026, 0.043, 0.071])
    depth = np.full((size, size), -np.inf)
    light = np.array([-.45, .65, .8]); light /= np.linalg.norm(light)
    for points, normals, indices, uv, color, texture, material in scene:
        screen = (points-center) * [scale, -scale, 1] + [size/2, size/2, 0]
        for ids in indices:
            tri = screen[ids]
            a, b, c = tri[:, :2]
            area = (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
            if abs(area) < 1e-10:
                continue
            if not material.get('doubleSided', False) and area > 0:
                continue
            lo = np.maximum(np.floor(tri[:, :2].min(axis=0)).astype(int), 0)
            hi = np.minimum(np.ceil(tri[:, :2].max(axis=0)).astype(int)+1, size)
            if np.any(lo >= hi):
                continue
            xx, yy = np.meshgrid(np.arange(lo[0], hi[0])+.5, np.arange(lo[1], hi[1])+.5)
            w1 = ((xx-a[0])*(c[1]-a[1])-(yy-a[1])*(c[0]-a[0])) / area
            w2 = ((b[0]-a[0])*(yy-a[1])-(b[1]-a[1])*(xx-a[0])) / area
            weights = np.stack((1-w1-w2, w1, w2), axis=-1)
            z = weights @ tri[:, 2]
            region = np.s_[lo[1]:hi[1], lo[0]:hi[0]]
            mask = (weights.min(axis=-1) >= -1e-7) & (z > depth[region])
            if not mask.any():
                continue
            rgba = np.broadcast_to(color, (*xx.shape, 4)).copy()
            if texture is not None:
                coords = weights @ uv[ids]
                # Repeat sampling matches these source textures' sampler defaults.
                tx = np.floor((coords[..., 0] % 1)*texture.shape[1]).astype(int)
                ty = np.floor((coords[..., 1] % 1)*texture.shape[0]).astype(int)
                rgba *= texture[ty, tx]
            alpha = rgba[..., 3] if material.get('alphaMode') == 'BLEND' else np.ones_like(xx)
            if material.get('alphaMode') == 'MASK':
                mask &= rgba[..., 3] >= material.get('alphaCutoff', .5)
            n = weights @ normals[ids]
            n /= np.maximum(np.linalg.norm(n, axis=-1)[..., None], 1e-20)
            lambert = np.abs(n @ light) if material.get('doubleSided') else np.maximum(n @ light, 0)
            shade = np.ones_like(lambert) if material.get('cpuSelfLuminous') else .32 + .68 * lambert
            rgb = rgba[..., :3] * shade[..., None]
            target = image[region]
            target[mask] = (rgb*alpha[..., None] + target*(1-alpha[..., None]))[mask]
            depth[region][mask & (alpha > .5)] = z[mask & (alpha > .5)]
    result = Image.fromarray(np.uint8(np.clip(image, 0, 1)*255))
    # Approximate diagram lines/labels after the CPU mesh pass. The production
    # SVG label visibility/collision rules still require browser verification.
    doc, binary = read_glb(data)
    draw = ImageDraw.Draw(result)
    # Transform absolute source coordinates through the same source-box pivot.
    absolute = []
    def collect(index, parent):
        node = doc['nodes'][index]; matrix = parent @ node_matrix(node)
        if 'mesh' in node:
            for primitive in doc['meshes'][node['mesh']]['primitives']:
                if primitive.get('mode', 4) != 4:
                    continue
                p = accessor(doc, binary, primitive['attributes']['POSITION'])
                absolute.append((np.column_stack((p, np.ones(len(p)))) @ matrix.T)[:, :3])
        for child in node.get('children', []):
            collect(child, matrix)
    for root in doc['scenes'][doc.get('scene', 0)]['nodes']:
        collect(root, np.eye(4))
    absolute = np.concatenate(absolute)
    pivot = (absolute.min(axis=0)+absolute.max(axis=0))/2
    transform = side_rotation @ rotation(pose)
    def project(p):
        p = (p-pivot) @ transform.T - center
        return np.array([size/2+p[0]*scale, size/2-p[1]*scale])
    def overlays(index, parent):
        node = doc['nodes'][index]; matrix = parent @ node_matrix(node)
        if 'mesh' in node:
            for primitive in doc['meshes'][node['mesh']]['primitives']:
                if primitive.get('mode', 4) != 1:
                    continue
                p = accessor(doc, binary, primitive['attributes']['POSITION'])
                p = (np.column_stack((p, np.ones(len(p)))) @ matrix.T)[:, :3]
                for a, b in p.reshape(-1, 2, 3):
                    draw.line([tuple(project(a)), tuple(project(b))], fill='#cbd7e8', width=1)
        text = node.get('extras', {}).get('label')
        if text:
            p = project(matrix[:3, 3]); draw.text(tuple(p+[4, -14]), text, fill='#cbd7e8')
        for child in node.get('children', []):
            overlays(child, matrix)
    # Diagram overlays here use no pre-rotation; other models' production labels
    # are intentionally omitted because those require the runtime projection.
    if not pose.get('pre_rotation'):
        for root in doc['scenes'][doc.get('scene', 0)]['nodes']:
            overlays(root, np.eye(4))
    return result, bounds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--entry-dir', type=Path, default=Path('handoff/space3d'))
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    overview = []
    measurements = []
    for file in sorted(args.entry_dir.glob('*.entry.json')):
        entry = json.loads(file.read_text())
        data = Path(entry['src']).read_bytes()
        sheet = Image.new('RGB', (960, 535), '#07121e')
        for index, side in enumerate([False, True]):
            image, bounds = render(data, entry.get('presentation', {}), side)
            sheet.paste(image, (index*480, 25))
            ImageDraw.Draw(sheet).text((12+index*480, 8), entry['id']+' | '+('side' if side else 'rest'), fill='white')
            if not side:
                pose = entry.get('presentation', {})
                ratio = max(bounds[:2]) / pose.get('reference_size', max(bounds))
                measurements.append({'id': entry['id'], 'orthographic_extent_ratio': float(ratio)})
                overview.append((entry['id'], image.resize((240, 240))))
        ImageDraw.Draw(sheet).text((12, 512), 'CPU APPROXIMATION - no WebGL, normal maps, reflections, perspective or production UI', fill='#d4ba81')
        sheet.save(args.directory / (entry['id']+'.png'))
        print(entry['id'], flush=True)
    columns = 5
    sheet = Image.new('RGB', (columns*240, math.ceil(len(overview)/columns)*265), '#07121e')
    for index, (name, image) in enumerate(overview):
        x, y = index % columns*240, index//columns*265
        sheet.paste(image, (x, y))
        ImageDraw.Draw(sheet).text((x+5, y+244), name, fill='white')
    sheet.save(args.directory/'overview.png')
    (args.directory/'geometry-audit.json').write_text(json.dumps(measurements, indent=2)+'\n')


if __name__ == '__main__':
    main()
