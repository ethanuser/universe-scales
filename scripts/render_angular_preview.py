#!/usr/bin/env python3
"""Flat geometry previews for audit_angular_models.mjs --previews (not WebGL screenshots)."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def render(parts, envelope, size=360):
    center = (np.array(envelope['min']) + envelope['max']) / 2
    extent = np.array(envelope['max']) - envelope['min']
    scale = size * 0.83 / max(extent[:2])
    polygons = []
    light = np.array([-0.3, 0.8, 0.55])
    light /= np.linalg.norm(light)
    for raw_faces, color, alpha in parts:
        faces = np.asarray(raw_faces)
        points = (faces - center)[:, :, :2] * [scale, -scale] + [size / 2, size / 2]
        normals = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
        normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-12)
        shade = np.clip(0.48 + 0.45 * np.abs(normals @ light), 0, 1)
        for triangle, tone, depth in zip(points, shade, np.mean(faces[:, :, 2], axis=1)):
            rgb = tuple(int(v) for v in np.clip(np.array(color) * tone * 255, 0, 255))
            polygons.append((depth, triangle, (*rgb, int(alpha * 255))))
    image = Image.new('RGB', (size, size), '#101d29')
    draw = ImageDraw.Draw(image, 'RGBA')
    for _, triangle, rgba in sorted(polygons, key=lambda part: part[0]):
        draw.polygon([tuple(p) for p in triangle], fill=rgba)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    report = json.loads((args.directory / 'audit.json').read_text())
    overview = []
    for result in report['results']:
        if 'envelope' not in result:
            continue
        phases = []
        for index, sample in enumerate(result['samples'][:-1]):
            source = args.directory / f"{result['index']:02d}-{index}.json"
            image = render(json.loads(source.read_text()), result['envelope'])
            tile = Image.new('RGB', (360, 404), '#101d29')
            tile.paste(image, (0, 0))
            draw = ImageDraw.Draw(tile)
            draw.text((10, 365), result['name'], fill='white')
            draw.text((10, 384), f"phase {sample['phase']:.3f} rad | t={sample['seconds']:.5g} s", fill='#9bb8c9')
            phases.append(tile)
        sheet = Image.new('RGB', (360 * len(phases), 430), '#101d29')
        for index, tile in enumerate(phases):
            sheet.paste(tile, (index * 360, 0))
        ImageDraw.Draw(sheet).text((10, 413), 'GEOMETRY ONLY - textures, reflections, perspective and production UI not rendered', fill='#dbb875')
        sheet.save(args.directory / f"{result['index']:02d}-phases.png")
        overview.append(phases[0])
    sheet = Image.new('RGB', (360 * 5, 404 * ((len(overview) + 4) // 5)), '#101d29')
    for index, image in enumerate(overview):
        sheet.paste(image, ((index % 5) * 360, (index // 5) * 404))
    sheet.save(args.directory / 'overview.png')
    print(f"Rendered {len(overview)} models at five phases in {args.directory}")


if __name__ == '__main__':
    main()
