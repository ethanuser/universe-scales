#!/usr/bin/env python3
"""Orthographic CPU geometry inspection when Chromium cannot launch.

This is NOT a production-renderer screenshot or a mobile browser test. It reads
the final GLB and plots its actual triangles and path-distance pulse annotation.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from build_reconstructed_neuron import ROOT, MODEL_ID
from fetch_model_assets import read_glb


def rotation(pitch, yaw, roll):
    x, y, z = np.radians([pitch, yaw, roll])
    rx = np.array([[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]])
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rz = np.array([[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]])
    return rx @ ry @ rz


def render(path, output, time, view='rest', width=1100, height=700):
    doc, binary = read_glb(path.read_bytes())
    def accessor(index):
        a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
        dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2'}[a['componentType']]
        size = {'SCALAR': 1, 'VEC3': 3}[a['type']]
        return np.frombuffer(binary, dtype=dtype, count=a['count']*size,
            offset=v.get('byteOffset', 0)+a.get('byteOffset', 0)).reshape(a['count'], size)
    matrix = rotation(8, -10, -127) if view == 'rest' else rotation(0, 90, -127)
    meshes, all_points = [], []
    animation = next(n['extras']['animation'] for n in doc['nodes'] if 'animation' in n.get('extras', {}))
    phase = time % animation['period']
    head = animation['aisDistanceUm'] + (phase-animation['launch']) * (
        animation['maxDistanceUm']-animation['aisDistanceUm'])/animation['travelSeconds']
    active = animation['launch'] <= phase <= animation['launch']+animation['travelSeconds']+.35
    for node in doc['nodes']:
        if 'mesh' not in node:
            continue
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            if primitive.get('mode', 4) != 4:
                continue
            attrs = primitive['attributes']
            points = accessor(attrs['POSITION']) @ matrix.T
            all_points.append(points)
            indices = accessor(primitive['indices']).reshape(-1, 3)
            material = doc['materials'][primitive['material']]
            color = np.array(material['pbrMetallicRoughness']['baseColorFactor'][:3])
            normals = accessor(attrs['NORMAL']) @ matrix.T
            face_normal = normals[indices].mean(axis=1)
            light = np.array([-.3, .5, 1]); light /= np.linalg.norm(light)
            shade = .65 + .6*np.maximum(0, face_normal @ light)
            color = np.clip(color[None, :] * shade[:, None], 0, 1)
            if '_PATH_DISTANCE' in attrs and active:
                distance = accessor(attrs['_PATH_DISTANCE']).ravel()[indices].mean(axis=1)
                pulse = np.exp(-2*((distance-head)/animation['pulseWidthUm'])**2)
                pulse *= distance >= animation['aisDistanceUm']
                color = np.clip(color + pulse[:, None]*np.array([2.8, 1.5, .22]), 0, 1)
            color = np.round(255 * color**(1/2.2)).astype(np.uint8)
            meshes.append((points[indices], color))
    points = np.concatenate(all_points)
    low, high = points.min(0), points.max(0)
    scale = min((width-70)/(high[0]-low[0]), (height-120)/(high[1]-low[1]))
    center = (low+high)/2
    def project(points):
        return np.stack(((points[..., 0]-center[0])*scale+width/2,
                         -(points[..., 1]-center[1])*scale+height/2-15), axis=-1)
    aa = 4
    image = Image.new('RGB', (width*aa, height*aa), '#101a22')
    draw = ImageDraw.Draw(image)
    triangles = np.concatenate([m[0] for m in meshes])
    colors = np.concatenate([m[1] for m in meshes])
    polygons = project(triangles)*aa
    for i in np.argsort(triangles[:, :, 2].mean(axis=1)):
        draw.polygon([tuple(v) for v in polygons[i]], fill=tuple(colors[i]))
    image = image.resize((width, height), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 13)
    except OSError:
        font = ImageFont.load_default()
    for node in doc['nodes']:
        if 'label' not in node.get('extras', {}):
            continue
        at = project(np.array(node['translation']) @ matrix.T)
        offset = node['extras']['labelOffset']
        end = at + [offset['x'], offset['y']]
        draw.line([tuple(at), tuple(end)], fill='#889997', width=1)
        draw.text(tuple(end), node['extras']['label'], fill='#e4ece7', font=font, anchor='mm',
                  stroke_width=2, stroke_fill='#101a22')
    draw.text((15, height-48), f'NMO_109111 • full trace • t = {time:g} s • {view}', fill='#c9dad4', font=font)
    draw.text((15, height-27), 'CPU geometry preview; browser verification blocked', fill='#99ada5', font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    extent = high-low
    print(json.dumps({'file': str(output), 'extentUm': extent.tolist(),
        'relativeTo800um': float(max(extent[:2])/800), 'time': time, 'view': view}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, default=ROOT/f'content/visualizations/models/{MODEL_ID}.glb')
    parser.add_argument('--output-dir', type=Path, default=Path('/tmp/neuron-cpu'))
    args = parser.parse_args()
    for time in (0, 1.2, 2.8, 4.8):
        render(args.model, args.output_dir/f'neuron-rest-{time:g}.png', time)
    render(args.model, args.output_dir/'neuron-side.png', 2.8, 'side')
    render(args.model, args.output_dir/'neuron-small.png', 2.8, width=393, height=400)


if __name__ == '__main__':
    main()
