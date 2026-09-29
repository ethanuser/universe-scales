#!/usr/bin/env python3
"""Panama Canal terrain strip for the Length explorer.

Data (all open): Mapzen Terrarium z12 tiles (SRTM/USGS) for terrain; OpenStreetMap contributors
(ODbL) for the sea coastline, Lago Gatun / Lago Miraflores / other lake polygons and the canal
centerline (fetched from the Overpass API: pan_water.json, pan_coast.json, pan_canal.json).

Horizontal scale is exactly 1:1 (metres), rotated so the straight line from the Atlantic to the
Pacific approaches lies along +X. Heights are exaggerated by --exaggeration (default 8) so the
lake steps and hills are visible; the Atlantic is at -X, the Pacific at +X, sea level is y=0.
Texture: hillshaded elevation tint, sea, lake and canal centerline at ~30 m/pixel.
"""
import argparse, hashlib, io, json, math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from build_dem_block import elevation_window, meters_per_pixel
from geo_glb_common import EARTH_R, GLB, grid_indices, grid_normals, hillshade

A = (-79.915, 9.385)   # lon, lat: Limon Bay approach (Atlantic end)
B = (-79.525, 8.895)   # Pacific end beyond the Bridge of the Americas
LAT0, LON0 = (A[1] + B[1]) / 2, (A[0] + B[0]) / 2
ZOOM = 12
LAKE_LEVELS = {"Lago Gatún": 26.0, "Lago Miraflores": 16.5}   # nominal operating levels (m)


def enu(lon, lat):
    return (math.radians(lon - LON0) * EARTH_R * math.cos(math.radians(LAT0)),
            math.radians(lat - LAT0) * EARTH_R)


_ax, _ay = enu(*A); _bx, _by = enu(*B)
CHORD = math.hypot(_bx - _ax, _by - _ay)
DX, DY = (_bx - _ax) / CHORD, (_by - _ay) / CHORD


def to_model(lon, lat):
    x, y = enu(lon, lat)
    u = x * DX + y * DY
    v = -x * DY + y * DX
    return u, -v


def from_model_arrays(X, Z):
    v = -Z
    x = X * DX - v * DY
    y = X * DY + v * DX
    return (LON0 + np.degrees(x / (EARTH_R * math.cos(math.radians(LAT0)))), LAT0 + np.degrees(y / EARTH_R))


def join_rings(segments):
    segs = [list(s) for s in segments if len(s) >= 2]
    key = lambda p: (round(p[0], 7), round(p[1], 7))
    rings = []
    while segs:
        ring = segs.pop()
        changed = True
        while changed and key(ring[0]) != key(ring[-1]):
            changed = False
            for i, s in enumerate(segs):
                if key(s[0]) == key(ring[-1]): ring += s[1:]
                elif key(s[-1]) == key(ring[-1]): ring += s[::-1][1:]
                elif key(s[-1]) == key(ring[0]): ring = s + ring[1:]
                elif key(s[0]) == key(ring[0]): ring = s[::-1] + ring[1:]
                else: continue
                segs.pop(i); changed = True; break
        if len(ring) >= 4:
            rings.append(ring)
    return rings


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build(a):
    work = Path(a.work)
    water = json.load(open(work / "pan_water.json"))["elements"]
    coast = json.load(open(work / "pan_coast.json"))["elements"]
    canal = json.load(open(work / "pan_canal.json"))["elements"]
    X0, X1 = -CHORD / 2 - a.end_margin, CHORD / 2 + a.end_margin
    Z0, Z1 = a.z_min, a.z_max
    W, D = X1 - X0, Z1 - Z0
    wpx = a.tex_width; hpx = int(round(wpx * D / W))
    def px(lon, lat):
        X, Z = to_model(lon, lat); return ((X - X0) / W * wpx, (Z - Z0) / D * hpx)

    # elevation raster at texture resolution
    XX, ZZ = np.meshgrid(X0 + (np.arange(wpx) + .5) / wpx * W, Z0 + (np.arange(hpx) + .5) / hpx * D)
    lon, lat = from_model_arrays(XX, ZZ)
    half = int(max(W, D) / meters_per_pixel(LAT0, ZOOM) * 0.75) + 40
    elev, cx, cy, tiles = elevation_window(LAT0, LON0, ZOOM, half, Path(a.tiles))
    pxc = (LON0 + 180) / 360 * 2 ** ZOOM * 256
    pyc = (1 - math.asinh(math.tan(math.radians(LAT0))) / math.pi) / 2 * 2 ** ZOOM * 256
    tx = (lon + 180) / 360 * 2 ** ZOOM * 256 - (pxc - cx)
    ty = (1 - np.arcsinh(np.tan(np.radians(lat))) / math.pi) / 2 * 2 ** ZOOM * 256 - (pyc - cy)
    x0, y0 = np.floor(tx).astype(int), np.floor(ty).astype(int); fx, fy = tx - x0, ty - y0
    dem = (elev[y0, x0] * (1 - fx) * (1 - fy) + elev[y0, x0 + 1] * fx * (1 - fy)
           + elev[y0 + 1, x0] * (1 - fx) * fy + elev[y0 + 1, x0 + 1] * fx * fy)

    # sea: DEM cells at/below sea level that are connected to the two open-sea seeds (Limon Bay, Panama Bay)
    low = Image.fromarray(((dem <= 0.6) * 255).astype(np.uint8)).copy()
    for lo, la in [(-79.93, 9.40), (-79.53, 8.88), (-79.60, 8.85), (-79.90, 9.42)]:
        sx, sy = map(int, px(lo, la))
        if 0 <= sx < wpx and 0 <= sy < hpx and low.getpixel((sx, sy)) == 255:
            ImageDraw.floodfill(low, (sx, sy), 128)
    sea = np.asarray(low) == 128
    # lakes
    lake_level = np.full((hpx, wpx), np.nan)
    lakes = []
    for e in water:
        t = e.get("tags", {}); name = t.get("name", "")
        polys = []
        if e["type"] == "relation":
            outers = join_rings([[(p["lon"], p["lat"]) for p in m["geometry"]] for m in e["members"] if m["role"] == "outer" and m.get("geometry")])
            inners = join_rings([[(p["lon"], p["lat"]) for p in m["geometry"]] for m in e["members"] if m["role"] == "inner" and m.get("geometry")])
            polys = [(r, True) for r in outers] + [(r, False) for r in inners]
        elif e.get("geometry") and len(e["geometry"]) >= 4:
            polys = [([(p["lon"], p["lat"]) for p in e["geometry"]], True)]
        if not polys:
            continue
        mask = Image.new("L", (wpx, hpx), 0); md = ImageDraw.Draw(mask)
        for ring, outer in polys:
            md.polygon([px(*p) for p in ring], fill=255 if outer else 0)
        m = np.asarray(mask) > 0
        if not m.any():
            continue
        level = LAKE_LEVELS.get(name)
        if level is None:
            level = max(float(np.median(dem[m])), 0.0)
        lake_level[m & ~sea] = level
        lakes.append((name or str(e["id"]), level, int(m.sum())))
    is_lake = ~np.isnan(lake_level)

    level = np.where(sea, 0.0, np.where(is_lake, lake_level, np.maximum(dem, 0.5)))

    # texture
    hs = hillshade(dem * a.exaggeration, W / wpx, D / hpx, azimuth=315, altitude=40)
    e = np.clip(dem, 0, 500)[..., None]
    low, mid, high = np.array([.36, .52, .28]), np.array([.30, .44, .24]), np.array([.55, .52, .40])
    t1 = np.clip(e / 120, 0, 1); t2 = np.clip((e - 120) / 380, 0, 1)
    rgb = (low * (1 - t1) + mid * t1) * (1 - t2) + high * t2
    rgb = rgb * (0.55 + 0.65 * hs[..., None])
    rgb[is_lake] = np.array([.28, .55, .64])
    rgb[sea] = np.array([.13, .35, .56])
    tex = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).copy()
    td = ImageDraw.Draw(tex)
    route_len = 0.0
    for e_ in canal:
        t = e_.get("tags", {})
        if t.get("name") not in ("Canal de Panamá",) and t.get("lock") != "yes":
            continue
        g = e_.get("geometry") or []
        if len(g) >= 2:
            td.line([px(p["lon"], p["lat"]) for p in g], fill=(245, 240, 200), width=2)
    buf = io.BytesIO(); tex.save(buf, "JPEG", quality=a.jpeg_quality, optimize=True)
    if a.save_texture: Path(a.save_texture).write_bytes(buf.getvalue())

    # mesh
    cols = int(round(W / a.cell)) + 1; rows = int(round(D / a.cell)) + 1
    grid = np.asarray(Image.fromarray(level.astype(np.float32), mode="F").resize((cols, rows), Image.BOX))
    xs = np.linspace(X0, X1, cols); zs = np.linspace(Z0, Z1, rows)
    GX, GZ = np.meshgrid(xs, zs)
    H = grid * a.exaggeration
    g = GLB("Universe Scales Panama Canal strip builder")
    tid = g.texture(buf.getvalue(), "image/jpeg")
    mt = g.material("terrain texture", texture=tid); mv = g.material("skirt")
    pos = np.stack((GX, H, GZ), axis=-1).reshape(-1, 3)
    uv = np.stack(((GX - X0) / W, (GZ - Z0) / D), axis=-1).reshape(-1, 2)
    prims = [g.primitive(pos, grid_indices(rows, cols), mt, normals=grid_normals(H, W / (cols - 1), D / (rows - 1)), uvs=uv)]
    base = -a.base
    ring = ([(0, c) for c in range(cols)] + [(r, cols - 1) for r in range(1, rows)]
            + [(rows - 1, c) for c in range(cols - 2, -1, -1)] + [(r, 0) for r in range(rows - 2, 0, -1)])
    sp, sn, sc, si = [], [], [], []
    def col(r, c, top):
        wet = grid[r, c] <= 0.01
        return (np.array([.30, .50, .66]) if top else np.array([.08, .16, .26])) if wet else (np.array([.42, .38, .30]) if top else np.array([.20, .18, .16]))
    for k, (r, c) in enumerate(ring):
        r2, c2 = ring[(k + 1) % len(ring)]
        p, q = pos[r * cols + c], pos[r2 * cols + c2]
        o = np.array([q[2] - p[2], 0, p[0] - q[0]]); o = o / (np.linalg.norm(o) or 1)
        i = len(sp)
        sp.extend((p, q, [p[0], base, p[2]], [q[0], base, q[2]])); sn.extend([o] * 4)
        sc.extend((col(r, c, True), col(r2, c2, True), col(r, c, False), col(r2, c2, False)))
        si.extend((i, i + 2, i + 1, i + 1, i + 2, i + 3))
    f = len(sp)
    sp.extend(([X0, base, Z0], [X0, base, Z1], [X1, base, Z0], [X1, base, Z1])); sn.extend(([0, -1, 0],) * 4); sc.extend(([.2, .18, .16],) * 4)
    si.extend((f, f + 1, f + 2, f + 2, f + 1, f + 3))
    prims.append(g.primitive(sp, si, mv, normals=sn, colors=sc, rgba8=True))
    g.mesh_node("Panama Canal strip", prims)
    for name, (lo, la), text, lift in [("atl", (-79.925, 9.36), "Atlantic (Colon)", 60), ("gatun-locks", (-79.92, 9.27), "Gatun Locks", 60),
                                       ("gatun-lake", (-79.83, 9.19), "Gatun Lake, 26 m", 80),
                                       ("miraflores", (-79.595, 8.997), "Miraflores Locks", 60), ("pac", (-79.545, 8.91), "Pacific (Panama City)", 60)]:
        X, Z = to_model(lo, la)
        yy = float(grid[min(rows - 1, max(0, int((Z - Z0) / D * (rows - 1)))), min(cols - 1, max(0, int((X - X0) / W * (cols - 1))))]) * a.exaggeration
        g.label_node(name, (X, yy + lift * 4, Z), text)
    size = g.write(a.output)
    return {"output": str(a.output), "bytes": size, "triangles": g.triangles, "grid": [rows, cols], "block_m": [W, D],
            "chord_m": CHORD, "exaggeration": a.exaggeration, "lakes": lakes, "max_dem_m": float(dem.max()),
            "tiles": tiles, "texture": [wpx, hpx], "texture_bytes": len(buf.getvalue()),
            "inputs_sha256": {f: sha_file(work / f) for f in ("pan_water.json", "pan_coast.json", "pan_canal.json")}}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True); ap.add_argument("--tiles", required=True); ap.add_argument("--output", required=True)
    ap.add_argument("--z-min", type=float, default=-4000.0); ap.add_argument("--z-max", type=float, default=13500.0); ap.add_argument("--end-margin", type=float, default=2000.0)
    ap.add_argument("--cell", type=float, default=250.0); ap.add_argument("--exaggeration", type=float, default=8.0)
    ap.add_argument("--base", type=float, default=300.0); ap.add_argument("--tex-width", type=int, default=2560)
    ap.add_argument("--jpeg-quality", type=int, default=82); ap.add_argument("--save-texture")
    o = build(ap.parse_args()); o.pop("tiles"); print(json.dumps(o, indent=1))
