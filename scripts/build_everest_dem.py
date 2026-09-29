#!/usr/bin/env python3
"""Build a compact Everest terrain block from Mapzen Terrarium elevation tiles.

Uses z12 tiles around 27.9881 N, 86.9250 E. Supply a directory containing
everest-X-Y.png files, or let the script download the public AWS tiles.
The 30 m-class DEM undershoots the surveyed summit, so a narrow correction
brings that one point to 8,848.86 m; the terrain is not a survey-grade model.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from PIL import Image

from fetch_model_assets import pack_glb


SUMMIT_LAT = 27.9881
SUMMIT_LON = 86.9250
SUMMIT_ELEVATION = 8848.86
ZOOM = 12
TILE_SIZE = 256
START_X, START_Y = 3036, 1715
TILES = 3
HALF_PIXELS = 94
STEP = 2


def tile_pixels(directory):
    tiles = np.empty((TILES * TILE_SIZE, TILES * TILE_SIZE, 3), dtype=np.uint8)
    provenance = []
    for row in range(TILES):
        for col in range(TILES):
            x, y = START_X + col, START_Y + row
            path = directory / f"everest-{x}-{y}.png"
            url = f"https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{ZOOM}/{x}/{y}.png"
            if not path.exists():
                path.write_bytes(urlopen(url, timeout=30).read())
            raw = path.read_bytes()
            provenance.append({"url": url, "sha256": hashlib.sha256(raw).hexdigest()})
            tile = np.asarray(Image.open(path).convert("RGB"))
            if tile.shape != (TILE_SIZE, TILE_SIZE, 3):
                raise ValueError(f"Unexpected tile size: {path}")
            tiles[row * TILE_SIZE:(row + 1) * TILE_SIZE,
                  col * TILE_SIZE:(col + 1) * TILE_SIZE] = tile
    return tiles, provenance


def glb_primitive(document, binary, positions, normals, colors, indices, material):
    attributes = {}
    for name, array in (("POSITION", positions), ("NORMAL", normals), ("COLOR_0", colors)):
        array = np.asarray(array, dtype=np.float32)
        binary.extend(b"\0" * (-len(binary) % 4))
        view = len(document["bufferViews"])
        document["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": array.nbytes})
        binary.extend(array.tobytes())
        accessor = {"bufferView": view, "componentType": 5126, "count": len(array), "type": "VEC3"}
        if name == "POSITION":
            accessor["min"] = array.min(axis=0).tolist()
            accessor["max"] = array.max(axis=0).tolist()
        attributes[name] = len(document["accessors"])
        document["accessors"].append(accessor)
    indices = np.asarray(indices, dtype=np.uint32)
    binary.extend(b"\0" * (-len(binary) % 4))
    view = len(document["bufferViews"])
    document["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": indices.nbytes})
    binary.extend(indices.tobytes())
    accessor = len(document["accessors"])
    document["accessors"].append({"bufferView": view, "componentType": 5125,
                                  "count": len(indices), "type": "SCALAR"})
    return {"attributes": attributes, "indices": accessor, "material": material, "mode": 4}


def build(tile_dir, output):
    pixels, provenance = tile_pixels(tile_dir)
    elevation = pixels[:, :, 0].astype(float) * 256 + pixels[:, :, 1] + pixels[:, :, 2] / 256 - 32768
    tile_x = (SUMMIT_LON + 180) / 360 * 2 ** ZOOM
    latitude = math.radians(SUMMIT_LAT)
    tile_y = (1 - math.asinh(math.tan(latitude)) / math.pi) / 2 * 2 ** ZOOM
    center_x = round((tile_x - START_X) * TILE_SIZE)
    center_y = round((tile_y - START_Y) * TILE_SIZE)
    samples = np.arange(-HALF_PIXELS, HALF_PIXELS + 1, STEP)
    px = center_x + samples
    py = center_y + samples
    heights = elevation[np.ix_(py, px)].copy()
    # Preserve the measured summit as one localized adjustment, not a rescale of all relief.
    highest = np.unravel_index(np.argmax(heights), heights.shape)
    correction = SUMMIT_ELEVATION - heights[highest]
    yy, xx = np.indices(heights.shape)
    heights += correction * np.exp(-((xx - highest[1]) ** 2 + (yy - highest[0]) ** 2) / (2 * 2.3 ** 2))
    heights[highest] = SUMMIT_ELEVATION
    meters_per_pixel = (math.cos(latitude) * 2 * math.pi * 6378137) / (TILE_SIZE * 2 ** ZOOM)
    step_m = STEP * meters_per_pixel
    n = len(samples)
    X, Z = np.meshgrid(samples * meters_per_pixel, samples * meters_per_pixel)
    positions = np.stack((X, heights, Z), axis=-1).reshape(-1, 3)
    dh_dz, dh_dx = np.gradient(heights, step_m, step_m)
    normals = np.stack((-dh_dx, np.ones_like(heights), -dh_dz), axis=-1)
    normals /= np.linalg.norm(normals, axis=-1, keepdims=True)
    # Altitude and aspect shading are vertex colors, not a satellite photograph.
    snow = np.clip((heights - 7350) / 700, 0, 1)[..., None]
    rock = np.array([0.35, 0.36, 0.38])
    snow_color = np.array([0.89, 0.92, 0.94])
    aspect = np.clip(0.78 + 0.22 * normals[:, :, 1], 0.65, 1)[..., None]
    colors = ((rock * (1 - snow) + snow_color * snow) * aspect).reshape(-1, 3)
    top_indices = []
    for row in range(n - 1):
        for col in range(n - 1):
            a = row * n + col
            top_indices.extend((a, a + n, a + 1, a + 1, a + n, a + n + 1))
    # Single opaque, closed block to sea level. There is no transparent plinth.
    boundary = ([(0, col) for col in range(n)]
                + [(row, n - 1) for row in range(1, n)]
                + [(n - 1, col) for col in range(n - 2, -1, -1)]
                + [(row, 0) for row in range(n - 2, 0, -1)])
    wall_positions, wall_normals, wall_colors, wall_indices = [], [], [], []
    for index, (row, col) in enumerate(boundary):
        next_row, next_col = boundary[(index + 1) % len(boundary)]
        a = positions[row * n + col]
        b = positions[next_row * n + next_col]
        outward = np.array([b[2] - a[2], 0, a[0] - b[0]])
        outward /= np.linalg.norm(outward)
        base = len(wall_positions)
        wall_positions.extend((a, b, [a[0], 0, a[2]], [b[0], 0, b[2]]))
        wall_normals.extend([outward] * 4)
        wall_colors.extend(([0.42, 0.41, 0.4], [0.42, 0.41, 0.4],
                            [0.23, 0.24, 0.26], [0.23, 0.24, 0.26]))
        wall_indices.extend((base, base + 2, base + 1, base + 1, base + 2, base + 3))
    low, high = samples[0] * meters_per_pixel, samples[-1] * meters_per_pixel
    floor_start = len(wall_positions)
    wall_positions.extend(([low, 0, low], [low, 0, high], [high, 0, low], [high, 0, high]))
    wall_normals.extend(([0, -1, 0],) * 4)
    wall_colors.extend(([0.23, 0.24, 0.26],) * 4)
    wall_indices.extend((floor_start, floor_start + 1, floor_start + 2,
                         floor_start + 2, floor_start + 1, floor_start + 3))
    doc = {"asset": {"version": "2.0", "generator": "Universe Scales DEM terrain builder"},
           "scene": 0, "scenes": [{"nodes": [0, 1, 2]}],
           "nodes": [{"mesh": 0, "name": "Everest terrain and sea-level block"},
                     {"name": "summit-label", "translation": positions[highest[0] * n + highest[1]].tolist(),
                      "extras": {"label": "Summit 8,849 m"}},
                     {"name": "sea-level-label", "translation": [0, 240, high],
                      "extras": {"label": "Sea level"}}],
           "meshes": [{"primitives": []}], "buffers": [], "bufferViews": [], "accessors": [],
           "materials": [{"name": "matte terrain", "doubleSided": True,
                          "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1],
                                                   "metallicFactor": 0, "roughnessFactor": 0.98}}]}
    binary = bytearray()
    doc["meshes"][0]["primitives"].append(glb_primitive(doc, binary, positions, normals.reshape(-1, 3),
                                                            colors, top_indices, 0))
    doc["meshes"][0]["primitives"].append(glb_primitive(doc, binary, wall_positions, wall_normals,
                                                            wall_colors, wall_indices, 0))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(pack_glb(doc, binary))
    return {"output": str(output), "bytes": output.stat().st_size,
            "triangles": (len(top_indices) + len(wall_indices)) // 3,
            "summit_raw_m": float(heights[highest] - correction), "summit_final_m": float(heights.max()),
            "tiles": provenance}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tiles", type=Path, default=Path("/private/tmp"))
    parser.add_argument("--output", type=Path, default=Path("content/visualizations/models/mapzen-everest-dem.glb"))
    args = parser.parse_args()
    print(json.dumps(build(args.tiles, args.output), indent=2))
