#!/usr/bin/env python3
"""Inspect two rejected numeric source candidates; never create/register a model.

Default is offline. --prepare downloads only the seven public files pinned in
research/source-pins.json. Requires the existing venv's NumPy and Pillow.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent


def get_file(cache, pin, prepare):
    path = cache / pin['name']
    if not path.exists() and prepare:
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_suffix(path.suffix + '.part')
        with urllib.request.urlopen(pin['url'], timeout=90) as response:
            partial.write_bytes(response.read())
        if hashlib.sha256(partial.read_bytes()).hexdigest() != pin['sha256']:
            partial.unlink()
            raise ValueError(f"Upstream hash changed: {pin['name']}; review before accepting")
        partial.replace(path)
    data = path.read_bytes()
    if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
        raise ValueError(f"Pinned source mismatch: {pin['name']}")
    return data


def afm(data):
    lines = data.decode('ascii').splitlines()
    offset = lines.index('top to bottom') + 1
    nx, ny = map(int, lines[offset:offset + 2])
    if lines[offset + 2:offset + 4] != ['m', 'm']:
        raise ValueError('Unexpected lateral units')
    width, height = map(float, lines[offset + 4:offset + 6])
    start = lines.index('end of header') + 1
    values = np.array([float(value) for value in lines[start:start + nx * ny]])
    if values.size != nx * ny or not np.isfinite(values).all():
        raise ValueError('Incomplete AFM height array')
    return values.reshape(ny, nx), width, height


def miras(data):
    rows = [line for line in data.decode('ascii').splitlines() if line.startswith('OGLE-')]
    if len(rows) != 65981 or len({line[:19] for line in rows}) != len(rows):
        raise ValueError('Unexpected Mira identity count')
    lon, lat, distance, error = [np.array([float(row[a:b]) for row in rows])
                               for a, b in [(52, 62), (63, 73), (286, 296), (297, 306)]]
    lon, lat = np.radians(lon), np.radians(lat)
    # Authors' Sun-to-GC distance, not the more recent value or a fitted bar.
    xyz = np.column_stack((distance * np.cos(lat) * np.cos(lon) / 1000 - 7.66,
                           distance * np.cos(lat) * np.sin(lon) / 1000,
                           distance * np.sin(lat) / 1000))
    keep = (distance > 0) & (error > 0) & (error < .2 * distance)
    # Diagnostic window only: it does not define bar membership or an edge.
    keep &= (np.abs(xyz[:, 0]) < 6) & (np.abs(xyz[:, 1]) < 6) & (np.abs(xyz[:, 2]) < 4)
    return len(rows), xyz[keep]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=Path('/tmp/length3d3-sources'))
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    pins = json.loads((HERE / 'research/source-pins.json').read_text())
    output = HERE / 'previews'
    output.mkdir(exist_ok=True)
    sheet = Image.new('RGB', (1536, 1100), '#18212b')
    draw = ImageDraw.Draw(sheet)
    arrays = []
    for index, pin in enumerate(pins['silk']['files']):
        values, width, height = afm(get_file(args.cache, pin, args.prepare))
        low, high = np.percentile(values, [1, 99])
        gray = np.uint8(np.clip((values - low) / (high - low), 0, 1) * 255)
        image = Image.fromarray(gray).convert('RGB').resize((512, 512))
        x, y = index % 3 * 512, index // 3 * 550
        sheet.paste(image, (x, y + 30))
        draw.text((x + 10, y + 8), f"{pin['name']} | {width * 1e6:g} x {height * 1e6:g} um", fill='white')
        arrays.append({'name': pin['name'], 'shape': list(values.shape),
                       'scan_m': [width, height], 'height_range_m': [float(values.min()), float(values.max())]})
    sheet.save(output / 'silk-afm-scope.png', optimize=True)
    count, xyz = miras(get_file(args.cache, pins['miras']['files'][0], args.prepare))
    image = Image.new('RGB', (1600, 820), '#070d18')
    draw = ImageDraw.Draw(image)
    for index, (axes, name) in enumerate([((0, 1), 'XY top'), ((0, 2), 'XZ edge')]):
        pixels = np.zeros((760, 760, 3), float)
        position = xyz[:, axes]
        col = np.floor(380 + position[:, 0] / 14 * 760).astype(int)
        row = np.floor(380 - position[:, 1] / 14 * 760).astype(int)
        for channel, gain in enumerate([.13, .08, .03]):
            np.add.at(pixels[:, :, channel], (row, col), gain)
        pixels += np.array([7, 13, 24]) / 255
        image.paste(Image.fromarray(np.uint8(np.clip(pixels, 0, 1) * 255)), (index * 800, 40))
        draw.text((index * 800 + 10, 10), name + ' | catalog positions | diagnostic window only', fill='white')
    image.save(output / 'mira-catalog-scope.png', optimize=True)
    result = {'method': 'Numerical-source inspection, not a model or WebGL preview.',
              'afm': arrays, 'miras': {'rows': count, 'diagnostic_window_rows': len(xyz),
                                      'extent_kpc': np.ptp(xyz, axis=0).tolist(),
                                      'gc_distance_kpc': 7.66,
                                      'selection': 'd>0, e_d>0, e_d/d<0.2; |x|<6, |y|<6, |z|<4 kpc. Display window, not bar membership.'}}
    (HERE / 'research/numeric-scope.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
