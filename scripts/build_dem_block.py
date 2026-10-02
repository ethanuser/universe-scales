#!/usr/bin/env python3
"""Generalized DEM block-diagram builder for the Length explorer.

Fetches public Mapzen Terrarium elevation tiles
(https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{z}/{x}/{y}.png,
elevation = R*256 + G + B/256 - 32768 meters; SRTM/GMTED on land, ETOPO1/GEBCO
derived bathymetry at sea) around an arbitrary center point and zoom, crops a
square window of a given size, and builds a compact block-diagram GLB:

  land mode: a single opaque terrain block from sea level (y=0) up to the
    high point, colored by an elevation ramp (rock/snow), exactly the shape
    of scripts/build_everest_dem.py generalized to any peak.
  sea mode:  an opaque seafloor block colored by a bathymetric depth ramp,
    with rock walls cut down to a flat base slightly below the deepest
    point, PLUS a translucent blue water shell (a flat sea-level cap and
    walls that follow the seafloor) running from the terrain up to sea
    level, lighter/more transparent near the top.

Both modes apply one Everest-style localized correction: the 30 m-to-150 m
class DEM tiles undershoot/oversmooth a single extreme point (a summit or a
trench's deepest sounding), so a narrow Gaussian bump anchors that one pixel
to an authoritative surveyed elevation without rescaling the sampled relief.

Two glTF nodes carry `extras.label` for the explorer's upright text labels:
one at the extreme point, one at the sea-level datum.

Reuses glb_primitive() from build_everest_dem.py (opaque RGB-vertex-color
triangles) and pack_glb() from fetch_model_assets.py (GLB container writer).
Neither file is modified. Water needs a translucent RGBA vertex color the
shared glb_primitive() does not support, so this script adds its own
glb_primitive_rgba() for that one case.

Example (Mariana Trench / Challenger Deep, sea mode):
  python3 build_dem_block.py --lat 11.3299 --lon 142.1993 --zoom 10 \\
      --crop-km 13.5 --mode sea --target-extreme -10935 \\
      --base-margin 300 --extreme-label "Challenger Deep, about 10.9 km" \\
      --tiles-dir ./tiles --output ./mariana-trench-dem.glb
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from PIL import Image

# Reuse, unmodified: the opaque-triangle GLB primitive builder from the
# Everest script, and the GLB container writer from the shared asset-fetching
# helpers. Both live next to this file in scripts/, so a plain import (the
# same pattern build_everest_dem.py itself uses for fetch_model_assets)
# resolves without any sys.path surgery.
from build_everest_dem import glb_primitive
from fetch_model_assets import pack_glb


TILE_SIZE = 256
EARTH_RADIUS_M = 6378137.0
TILE_URL_TEMPLATE = "https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{z}/{x}/{y}.png"


def meters_per_pixel(lat, zoom):
    return math.cos(math.radians(lat)) * 2 * math.pi * EARTH_RADIUS_M / (TILE_SIZE * 2 ** zoom)


def latlon_to_global_pixel(lat, lon, zoom):
    tile_x = (lon + 180) / 360 * 2 ** zoom
    lat_rad = math.radians(lat)
    tile_y = (1 - math.asinh(math.tan(lat_rad)) / math.pi) / 2 * 2 ** zoom
    return tile_x * TILE_SIZE, tile_y * TILE_SIZE


def fetch_tile(zoom, x, y, cache_dir):
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"tile-{zoom}-{x}-{y}.png"
    url = TILE_URL_TEMPLATE.format(z=zoom, x=x, y=y)
    if not path.exists():
        path.write_bytes(urlopen(url, timeout=30).read())
    raw = path.read_bytes()
    tile = np.asarray(Image.open(path).convert("RGB"))
    if tile.shape != (TILE_SIZE, TILE_SIZE, 3):
        raise ValueError(f"Unexpected tile size: {path}")
    return tile, {"url": url, "sha256": hashlib.sha256(raw).hexdigest()}


def elevation_window(lat, lon, zoom, half_pixels, cache_dir):
    """Fetch and stitch as many tiles as needed to cover a half_pixels radius
    around (lat, lon) at the given zoom, returning the full elevation array
    plus the fractional pixel coordinate of the center within it."""
    px_center, py_center = latlon_to_global_pixel(lat, lon, zoom)
    tx0 = int((px_center - half_pixels) // TILE_SIZE)
    tx1 = int((px_center + half_pixels) // TILE_SIZE)
    ty0 = int((py_center - half_pixels) // TILE_SIZE)
    ty1 = int((py_center + half_pixels) // TILE_SIZE)
    cols, rows = tx1 - tx0 + 1, ty1 - ty0 + 1
    canvas = np.empty((rows * TILE_SIZE, cols * TILE_SIZE, 3), dtype=np.uint8)
    provenance = []
    for row, ty in enumerate(range(ty0, ty1 + 1)):
        for col, tx in enumerate(range(tx0, tx1 + 1)):
            tile, meta = fetch_tile(zoom, tx, ty, cache_dir)
            provenance.append(meta)
            canvas[row * TILE_SIZE:(row + 1) * TILE_SIZE, col * TILE_SIZE:(col + 1) * TILE_SIZE] = tile
    elevation = canvas[:, :, 0].astype(float) * 256 + canvas[:, :, 1] + canvas[:, :, 2] / 256 - 32768
    origin_x, origin_y = tx0 * TILE_SIZE, ty0 * TILE_SIZE
    return elevation, px_center - origin_x, py_center - origin_y, provenance


def choose_step(half_pixels, max_samples):
    """Auto-thin the native pixel grid so it never exceeds max_samples per
    side, keeping the triangle budget predictable regardless of zoom/crop."""
    native_samples = 2 * half_pixels + 1
    if native_samples <= max_samples:
        return 1
    return math.ceil((native_samples - 1) / (max_samples - 1))


def apply_local_correction(heights, target, sigma):
    """Anchor the single most-extreme sampled pixel (max for land, min for
    sea) to an authoritative surveyed elevation with a narrow Gaussian bump,
    the same technique build_everest_dem.py uses for the summit: the
    coarse DEM undershoots/oversmooths one point, so only that point is
    corrected, not the sampled relief as a whole."""
    is_sea = target < 0
    extreme_index = np.unravel_index(np.argmin(heights) if is_sea else np.argmax(heights), heights.shape)
    raw_value = float(heights[extreme_index])
    correction = target - raw_value
    yy, xx = np.indices(heights.shape)
    bump = correction * np.exp(-((xx - extreme_index[1]) ** 2 + (yy - extreme_index[0]) ** 2) / (2 * sigma ** 2))
    corrected = heights + bump
    corrected[extreme_index] = target
    return corrected, extreme_index, raw_value


def compute_normals(heights, step_m):
    dh_dz, dh_dx = np.gradient(heights, step_m, step_m)
    normals = np.stack((-dh_dx, np.ones_like(heights), -dh_dz), axis=-1)
    normals /= np.linalg.norm(normals, axis=-1, keepdims=True)
    return normals


def land_colors(heights, normals, snowline=7350, snow_span=700):
    snow = np.clip((heights - snowline) / snow_span, 0, 1)[..., None]
    rock = np.array([0.35, 0.36, 0.38])
    snow_color = np.array([0.89, 0.92, 0.94])
    aspect = np.clip(0.78 + 0.22 * normals[:, :, 1], 0.65, 1)[..., None]
    return ((rock * (1 - snow) + snow_color * snow) * aspect).reshape(-1, 3)


def bathymetric_colors(heights, normals):
    """Tasteful ocean-depth ramp stretched to the sampled crop's own
    min/max, so a hadal trench (which is dark from rim to floor on any
    absolute abyssal scale) still shows readable contrast at a glance."""
    lo, hi = float(heights.min()), float(heights.max())
    t = np.clip((heights - lo) / max(hi - lo, 1e-6), 0, 1)[..., None]  # 0 = deepest, 1 = shallowest in crop
    stops = [
        (0.00, np.array([0.016, 0.022, 0.060])),  # near-black navy: hadal floor
        (0.35, np.array([0.030, 0.070, 0.150])),  # deep blue
        (0.70, np.array([0.060, 0.150, 0.260])),  # medium blue
        (1.00, np.array([0.110, 0.260, 0.340])),  # dark teal: shallow rim of the crop
    ]
    color = np.zeros(heights.shape + (3,))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        span = np.clip((t[..., 0] - t0) / (t1 - t0), 0, 1)[..., None]
        segment = (t[..., 0] >= t0) & (t[..., 0] <= t1)
        color[segment] = (c0 * (1 - span) + c1 * span)[segment]
    aspect = np.clip(0.82 + 0.18 * normals[:, :, 1], 0.7, 1)[..., None]
    return (color * aspect).reshape(-1, 3)


def build_grid_indices(n):
    indices = []
    for row in range(n - 1):
        for col in range(n - 1):
            a = row * n + col
            indices.extend((a, a + n, a + 1, a + 1, a + n, a + n + 1))
    return indices


def trace_boundary(n):
    return ([(0, col) for col in range(n)]
            + [(row, n - 1) for row in range(1, n)]
            + [(n - 1, col) for col in range(n - 2, -1, -1)]
            + [(row, 0) for row in range(n - 2, 0, -1)])


def glb_primitive_rgba(document, binary, positions, normals, colors_rgba, indices, material):
    """Like build_everest_dem.glb_primitive(), but COLOR_0 is a VEC4 (RGBA)
    accessor so per-vertex alpha can vary (glTF multiplies vertex alpha into
    the material's alpha under alphaMode BLEND). glb_primitive() only writes
    VEC3 colors, so this small sibling exists instead of modifying it."""
    attributes = {}
    for name, array, item_type in (("POSITION", positions, "VEC3"),
                                    ("NORMAL", normals, "VEC3"),
                                    ("COLOR_0", colors_rgba, "VEC4")):
        array = np.asarray(array, dtype=np.float32)
        binary.extend(b"\0" * (-len(binary) % 4))
        view = len(document["bufferViews"])
        document["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": array.nbytes})
        binary.extend(array.tobytes())
        accessor = {"bufferView": view, "componentType": 5126, "count": len(array), "type": item_type}
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


def build(args):
    half_pixels = args.half_pixels
    if half_pixels is None:
        mpp_estimate = meters_per_pixel(args.lat, args.zoom)
        half_pixels = round(args.crop_km * 1000 / 2 / mpp_estimate)
    step = args.step or choose_step(half_pixels, args.max_samples)

    elevation, cx, cy, provenance = elevation_window(args.lat, args.lon, args.zoom, half_pixels, args.tiles_dir)
    samples = np.arange(-half_pixels, half_pixels + 1, step)
    px = np.clip(np.round(cx + samples).astype(int), 0, elevation.shape[1] - 1)
    py = np.clip(np.round(cy + samples).astype(int), 0, elevation.shape[0] - 1)
    heights = elevation[np.ix_(py, px)].copy()

    heights, extreme_index, raw_extreme = apply_local_correction(heights, args.target_extreme, args.correction_sigma)

    mpp = meters_per_pixel(args.lat, args.zoom)
    step_m = step * mpp
    n = len(samples)
    X, Z = np.meshgrid(samples * mpp, samples * mpp)
    positions = np.stack((X, heights, Z), axis=-1).reshape(-1, 3)
    normals = compute_normals(heights, step_m)
    colors = (land_colors(heights, normals) if args.mode == "land" else bathymetric_colors(heights, normals))

    top_indices = build_grid_indices(n)
    boundary = trace_boundary(n)

    extreme_y = float(heights[extreme_index])
    low, high = float(samples[0] * mpp), float(samples[-1] * mpp)

    if args.mode == "land":
        base_y = 0.0  # sea level; the whole cutaway is opaque rock down to here, as in build_everest_dem.py
    else:
        base_y = extreme_y - args.base_margin  # a flat slab of rock slightly below the trench floor

    # --- Rock skirt: from the terrain boundary down to the flat base ---
    rock_wall_positions, rock_wall_normals, rock_wall_colors, rock_wall_indices = [], [], [], []
    dark_band = np.array([0.42, 0.41, 0.40]) if args.mode == "land" else np.array([0.18, 0.17, 0.19])
    darker_band = np.array([0.23, 0.24, 0.26]) if args.mode == "land" else np.array([0.10, 0.10, 0.12])
    for index, (row, col) in enumerate(boundary):
        next_row, next_col = boundary[(index + 1) % len(boundary)]
        a = positions[row * n + col]
        b = positions[next_row * n + next_col]
        outward = np.array([b[2] - a[2], 0, a[0] - b[0]])
        norm = np.linalg.norm(outward)
        outward = outward / norm if norm else np.array([0, 0, 1])
        base = len(rock_wall_positions)
        rock_wall_positions.extend((a, b, [a[0], base_y, a[2]], [b[0], base_y, b[2]]))
        rock_wall_normals.extend([outward] * 4)
        rock_wall_colors.extend((dark_band, dark_band, darker_band, darker_band))
        rock_wall_indices.extend((base, base + 2, base + 1, base + 1, base + 2, base + 3))
    floor_start = len(rock_wall_positions)
    rock_wall_positions.extend(([low, base_y, low], [low, base_y, high], [high, base_y, low], [high, base_y, high]))
    rock_wall_normals.extend(([0, -1, 0],) * 4)
    rock_wall_colors.extend((darker_band,) * 4)
    rock_wall_indices.extend((floor_start, floor_start + 1, floor_start + 2,
                               floor_start + 2, floor_start + 1, floor_start + 3))

    doc = {"asset": {"version": "2.0", "generator": "Universe Scales generalized DEM block builder"},
           "scene": 0, "scenes": [{"nodes": []}],
           "nodes": [], "meshes": [{"primitives": []}], "buffers": [], "bufferViews": [], "accessors": [],
           "materials": [{"name": "matte terrain", "doubleSided": True,
                          "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1],
                                                    "metallicFactor": 0, "roughnessFactor": 0.98}}]}
    binary = bytearray()
    doc["meshes"][0]["primitives"].append(
        glb_primitive(doc, binary, positions, normals.reshape(-1, 3), colors, top_indices, 0))
    doc["meshes"][0]["primitives"].append(
        glb_primitive(doc, binary, rock_wall_positions, rock_wall_normals, rock_wall_colors, rock_wall_indices, 0))

    terrain_node = {"mesh": 0, "name": "terrain and rock block"}
    doc["nodes"].append(terrain_node)
    doc["scenes"][0]["nodes"].append(0)

    if args.mode == "sea":
        # --- Water shell: a flat sea-level cap plus walls that rise from the
        # terrain boundary up to y=0, lighter/more transparent near the top. ---
        doc["materials"].append({"name": "translucent water", "doubleSided": True, "alphaMode": "BLEND",
                                  "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1],
                                                            "metallicFactor": 0, "roughnessFactor": 0.9}})
        top_color = np.array([0.66, 0.85, 0.93])
        top_alpha = args.water_top_alpha
        bottom_color = np.array([0.035, 0.110, 0.280])
        bottom_alpha = args.water_bottom_alpha
        deepest_y = float(heights.min())

        def water_color(y):
            # A depth exponent > 1 keeps most of the column pale/clear and only
            # deepens to a rich blue close to the seafloor (lighter at the top).
            t = np.clip(y / deepest_y, 0, 1) ** 1.8 if deepest_y < 0 else 0.0
            rgb = top_color * (1 - t) + bottom_color * t
            a = top_alpha * (1 - t) + bottom_alpha * t
            return np.array([rgb[0], rgb[1], rgb[2], a])

        water_wall_positions, water_wall_normals, water_wall_colors, water_wall_indices = [], [], [], []
        for index, (row, col) in enumerate(boundary):
            next_row, next_col = boundary[(index + 1) % len(boundary)]
            a = positions[row * n + col]
            b = positions[next_row * n + next_col]
            outward = np.array([b[2] - a[2], 0, a[0] - b[0]])
            norm = np.linalg.norm(outward)
            outward = outward / norm if norm else np.array([0, 0, 1])
            base = len(water_wall_positions)
            top_a, top_b = [a[0], 0.0, a[2]], [b[0], 0.0, b[2]]
            water_wall_positions.extend((top_a, top_b, a.tolist(), b.tolist()))
            water_wall_normals.extend([outward] * 4)
            water_wall_colors.extend((water_color(0.0), water_color(0.0), water_color(a[1]), water_color(b[1])))
            water_wall_indices.extend((base, base + 2, base + 1, base + 1, base + 2, base + 3))
        # Flat sea-level cap, a single quad (cheap: the surface itself carries no relief)
        cap_start = len(water_wall_positions)
        cap_color = water_color(0.0)
        water_wall_positions.extend(([low, 0.0, low], [low, 0.0, high], [high, 0.0, low], [high, 0.0, high]))
        water_wall_normals.extend(([0, 1, 0],) * 4)
        water_wall_colors.extend((cap_color,) * 4)
        water_wall_indices.extend((cap_start, cap_start + 1, cap_start + 2,
                                    cap_start + 2, cap_start + 1, cap_start + 3))

        doc["meshes"].append({"primitives": [glb_primitive_rgba(
            doc, binary, water_wall_positions, water_wall_normals, water_wall_colors, water_wall_indices, 1)]})
        water_node_index = len(doc["nodes"])
        doc["nodes"].append({"mesh": 1, "name": "water shell"})
        doc["scenes"][0]["nodes"].append(water_node_index)

        sea_level_label_pos = [0.0, args.base_margin * 0.6, high]
    else:
        sea_level_label_pos = [0.0, (heights.max() - heights.min()) * 0.03, high]

    extreme_row, extreme_col = extreme_index
    extreme_point = positions[extreme_row * n + extreme_col].tolist()

    extreme_label_index = len(doc["nodes"])
    doc["nodes"].append({"name": "extreme-label", "translation": extreme_point,
                          "extras": {"label": args.extreme_label}})
    doc["scenes"][0]["nodes"].append(extreme_label_index)

    sea_level_label_index = len(doc["nodes"])
    doc["nodes"].append({"name": "sea-level-label", "translation": sea_level_label_pos,
                          "extras": {"label": "Sea level"}})
    doc["scenes"][0]["nodes"].append(sea_level_label_index)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(pack_glb(doc, binary))

    triangle_count = (len(top_indices) + len(rock_wall_indices)
                       + (len(water_wall_indices) if args.mode == "sea" else 0)) // 3

    return {
        "output": str(args.output), "bytes": args.output.stat().st_size, "triangles": triangle_count,
        "mode": args.mode, "zoom": args.zoom, "half_pixels": half_pixels, "step": step, "grid_samples": n,
        "meters_per_pixel": mpp, "crop_size_m": float(samples[-1] - samples[0]) * mpp,
        "raw_extreme_m": raw_extreme, "corrected_extreme_m": extreme_y, "target_extreme_m": args.target_extreme,
        "base_y_m": base_y, "sea_level_y_m": 0.0, "bbox_y_min": min(base_y, float(heights.min())),
        "bbox_y_max": 0.0 if args.mode == "sea" else extreme_y,
        "tiles": provenance,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--zoom", type=int, required=True)
    parser.add_argument("--crop-km", type=float, help="square crop width/height in kilometers")
    parser.add_argument("--half-pixels", type=int, default=None, help="override: half-width in native tile pixels")
    parser.add_argument("--step", type=int, default=None, help="override: native-pixel stride for the sample grid")
    parser.add_argument("--max-samples", type=int, default=121, help="cap on grid samples per side (triangle budget)")
    parser.add_argument("--mode", choices=["land", "sea"], required=True)
    parser.add_argument("--target-extreme", type=float, required=True,
                         help="authoritative elevation (m) to anchor the sampled summit/deepest-point to; "
                              "positive for land, negative for sea")
    parser.add_argument("--correction-sigma", type=float, default=1.6,
                         help="Gaussian bump radius in sample-grid units for the local correction")
    parser.add_argument("--base-margin", type=float, default=300.0,
                         help="sea mode only: extra rock thickness (m) below the deepest sampled point")
    parser.add_argument("--water-top-alpha", type=float, default=0.10)
    parser.add_argument("--water-bottom-alpha", type=float, default=0.40)
    parser.add_argument("--extreme-label", type=str, required=True)
    parser.add_argument("--tiles-dir", type=Path, default=Path("/private/tmp/dem-tiles"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.half_pixels is None and args.crop_km is None:
        parser.error("either --crop-km or --half-pixels is required")
    print(json.dumps(build(args), indent=2))


if __name__ == "__main__":
    main()
