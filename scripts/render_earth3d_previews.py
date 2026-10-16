#!/usr/bin/env python3
"""Orthographic CPU GLB review, including base-color textures (not WebGL verification).

Uses the registry's pre-rotation/calibration/rest pose and a real depth buffer.
No production lighting, environment reflections, normal maps, UI or perspective.
"""
import argparse
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from render_glb_preview import accessor as raw_accessor, node_matrix, read_glb

ROOT = Path(__file__).resolve().parents[1]


def accessor(doc, binary, index):
    value = raw_accessor(doc, binary, index)
    if doc['accessors'][index].get('normalized') and np.issubdtype(value.dtype, np.integer):
        return np.maximum(value.astype(float) / np.iinfo(value.dtype).max, -1)
    return value


def rotation(x=0, y=0, z=0):
    x, y, z = np.radians([x, y, z])
    cx, cy, cz, sx, sy, sz = math.cos(x), math.cos(y), math.cos(z), math.sin(x), math.sin(y), math.sin(z)
    return np.array([[cy*cz, -cy*sz, sy],
                     [cx*sz+sx*sy*cz, cx*cz-sx*sy*sz, -sx*cy],
                     [sx*sz-cx*sy*cz, sx*cz+cx*sy*sz, cx*cy]])


def parts(path, presentation):
    doc, binary = read_glb(path)
    result, textures = [], []
    for texture in doc.get('textures', []):
        source = doc['images'][texture['source']]
        view = doc['bufferViews'][source['bufferView']]
        start = view.get('byteOffset', 0)
        textures.append(np.asarray(Image.open(io.BytesIO(binary[start:start+view['byteLength']])).convert('RGBA')) / 255)
    pre = presentation.get('pre_rotation', {})
    base = np.eye(4)
    base[:3, :3] = rotation(**pre)

    def visit(index, parent):
        node = doc['nodes'][index]
        if node.get('name') in presentation.get('remove_nodes', []):
            return
        world = parent @ node_matrix(node)
        if 'mesh' in node:
            for primitive in doc['meshes'][node['mesh']]['primitives']:
                if primitive.get('mode', 4) != 4:
                    continue
                attrs = primitive['attributes']
                pos = accessor(doc, binary, attrs['POSITION']).astype(float)
                pos = (np.column_stack((pos, np.ones(len(pos)))) @ world.T)[:, :3]
                indices = accessor(doc, binary, primitive['indices']).reshape(-1) if 'indices' in primitive else np.arange(len(pos))
                material = doc.get('materials', [{}])[primitive.get('material', 0)]
                pbr = material.get('pbrMetallicRoughness', {})
                color = np.tile(pbr.get('baseColorFactor', [1, 1, 1, 1]), (len(pos), 1)).astype(float)
                if 'COLOR_0' in attrs:
                    vertex = accessor(doc, binary, attrs['COLOR_0'])
                    if np.issubdtype(vertex.dtype, np.integer):
                        vertex = vertex / np.iinfo(vertex.dtype).max
                    color[:, :vertex.shape[1]] *= vertex
                normals = accessor(doc, binary, attrs['NORMAL']) @ np.linalg.inv(world[:3, :3]) if 'NORMAL' in attrs else None
                if normals is not None:
                    normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-20)
                uv = accessor(doc, binary, attrs['TEXCOORD_0']) if 'TEXCOORD_0' in attrs else None
                tex = textures[pbr['baseColorTexture']['index']] if 'baseColorTexture' in pbr else None
                tex_def = doc['textures'][pbr['baseColorTexture']['index']] if tex is not None else {}
                sampler = doc.get('samplers', [{}])[tex_def.get('sampler', 0)] if doc.get('samplers') else {}
                result.append(dict(pos=pos, indices=indices.reshape(-1, 3), color=color, normals=normals, uv=uv, tex=tex,
                                   wrap=(sampler.get('wrapS', 10497), sampler.get('wrapT', 10497)),
                                   unlit='KHR_materials_unlit' in material.get('extensions', {}),
                                   mask=material.get('alphaCutoff', .5) if material.get('alphaMode') == 'MASK' else .01))
        for child in node.get('children', []):
            visit(child, world)
    for index in doc['scenes'][doc.get('scene', 0)]['nodes']:
        visit(index, base)
    all_pos = np.concatenate([part['pos'] for part in result])
    lo, hi = all_pos.min(axis=0), all_pos.max(axis=0)
    size = hi - lo
    reference = presentation.get('reference_size')
    if reference is None:
        reference = size['xyz'.index(presentation['measure_axis'])] if presentation.get('measure_axis') else max(size)
    scale = reference * presentation.get('measure_fraction', 1)
    pose = rotation(presentation.get('pitch', 0), presentation.get('yaw', 0), presentation.get('roll', 0))
    for part in result:
        part['pos'] = ((part['pos'] - (hi+lo)/2) / scale) @ pose.T
        if part['normals'] is not None:
            part['normals'] = part['normals'] @ pose.T
    return result, size.tolist()


def render(parts, side=False, size=600):
    view = rotation(0, 90 if side else 0, 0)
    points = np.concatenate([p['pos'] @ view.T for p in parts])
    lo, hi = points.min(axis=0), points.max(axis=0)
    extent = max((hi-lo)[:2])
    factor = size * .84 / max(extent, 1e-12)
    center = (hi+lo)/2
    image = np.empty((size, size, 3), float)
    image[:] = np.array([16, 25, 39]) / 255
    depth = np.full((size, size), -np.inf)
    light = np.array([-.35, .65, 1.0]); light /= np.linalg.norm(light)
    for part in parts:
        p = (part['pos'] @ view.T - center) * factor
        p[:, :2] = p[:, :2] * [1, -1] + size/2
        ns = part['normals'] @ view.T if part['normals'] is not None else None
        for ids in part['indices']:
            tri = p[ids]
            xmin, ymin = np.maximum(np.floor(tri[:, :2].min(axis=0)).astype(int), 0)
            xmax, ymax = np.minimum(np.ceil(tri[:, :2].max(axis=0)).astype(int), size-1)
            if xmax < xmin or ymax < ymin:
                continue
            a, b, c = tri[:, :2]
            denom = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
            if abs(denom) < 1e-10:
                continue
            yy, xx = np.mgrid[ymin:ymax+1, xmin:xmax+1]
            u = ((b[1]-c[1])*(xx+.5-c[0]) + (c[0]-b[0])*(yy+.5-c[1])) / denom
            v = ((c[1]-a[1])*(xx+.5-c[0]) + (a[0]-c[0])*(yy+.5-c[1])) / denom
            w = 1-u-v
            weights = np.stack((u, v, w), axis=-1)
            z = weights @ tri[:, 2]
            target_depth = depth[ymin:ymax+1, xmin:xmax+1]
            mask = (u >= -1e-8) & (v >= -1e-8) & (w >= -1e-8) & (z > target_depth)
            if not mask.any():
                continue
            weights = weights[mask]
            rgba = weights @ part['color'][ids]
            if part['tex'] is not None and part['uv'] is not None:
                uv = weights @ part['uv'][ids]
                # Wrapping happens after interpolation; wrapping each vertex first
                # would produce incorrect interpolation across tile boundaries.
                for axis, mode in enumerate(part.get('wrap', (33071, 33071))):
                    if mode == 10497:
                        uv[:, axis] %= 1
                    elif mode == 33648:
                        uv[:, axis] = 1-np.abs(uv[:, axis] % 2-1)
                texture = part['tex']
                tx = np.clip((uv[:, 0] * (texture.shape[1]-1)).astype(int), 0, texture.shape[1]-1)
                ty = np.clip((uv[:, 1] * (texture.shape[0]-1)).astype(int), 0, texture.shape[0]-1)
                rgba *= texture[ty, tx]
            if ns is not None:
                normals = weights @ ns[ids]
            else:
                normal = np.cross(part['pos'][ids[1]]-part['pos'][ids[0]], part['pos'][ids[2]]-part['pos'][ids[0]]) @ view.T
                normals = np.tile(normal, (len(weights), 1))
            normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-20)
            shade = .4 + .6 * np.abs(normals @ light)
            if part.get('unlit'):
                shade[:] = 1
            rgb = np.clip(rgba[:, :3] * shade[:, None], 0, 1)
            keep = rgba[:, 3] >= part['mask']
            iy, ix = np.where(mask)
            iy, ix = iy[keep]+ymin, ix[keep]+xmin
            image[iy, ix] = rgb[keep]
            depth[iy, ix] = z[mask][keep]
    return Image.fromarray(np.uint8(np.clip(image, 0, 1)*255)), float(extent)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--entry', type=Path, action='append', default=[])
    parser.add_argument('--model', type=Path)
    parser.add_argument('--size', type=int, default=600)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    entries = [json.loads(p.read_text()) for p in args.entry]
    if args.model:
        entries.append(dict(id=args.model.stem, src=str(args.model), presentation={}))
    report, tiles = [], []
    for entry in entries:
        scene, bounds = parts(ROOT / entry['src'], entry.get('presentation', {}))
        pair = Image.new('RGB', (args.size*2, args.size+65), '#101927')
        record = dict(id=entry['id'], source_bounds=bounds)
        for i, side in enumerate((False, True)):
            picture, extent = render(scene, side, args.size)
            pair.paste(picture, (i*args.size, 0))
            record['side_extent' if side else 'rest_extent'] = extent
        draw = ImageDraw.Draw(pair)
        draw.text((12, args.size+8), entry['id'] + ' | REST / SIDE', fill='white')
        draw.text((12, args.size+30), 'CPU ORTHOGRAPHIC PREVIEW - not production WebGL / reflections / UI verification', fill='#ddbd80')
        pair.save(args.output / f"{entry['id']}.png")
        tiles.append(pair.resize((720, int(pair.height*720/pair.width))))
        report.append(record)
        print(json.dumps(record), flush=True)
    if tiles:
        sheet = Image.new('RGB', (1440, tiles[0].height * math.ceil(len(tiles)/2)), '#101927')
        for i, tile in enumerate(tiles):
            sheet.paste(tile, ((i % 2)*720, (i//2)*tile.height))
        sheet.save(args.output / 'overview.png')
    (args.output / 'geometry-audit.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
