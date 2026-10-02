#!/usr/bin/env python3
"""Manhattan Island block model for the Length explorer.

Data (all open):
  * Elevation: Mapzen Terrarium z13 tiles (USGS 3DEP/NED over land), public AWS Open Data.
  * Shoreline, parks, ponds and building footprints/heights: OpenStreetMap contributors (ODbL),
    fetched from the Overpass API (see fetch commands in the OVERPASS dict below).

Output: one GLB in true 1:1 metres (X = along the island, Battery at -X, Inwood at +X; Y up;
sea level y=0), made of
  * a textured terrain block (100 m height grid; texture = shoreline, parks and every OSM
    building footprint drawn top-down at ~8 m/pixel),
  * a rock/water skirt down to y=-80 m,
  * extruded OSM footprints of the tallest buildings (height >= --min-height).

Usage: SSL_CERT_FILE=/etc/ssl/cert.pem python3 scripts/build_manhattan_block.py \
         --work WORKDIR --output manhattan-block.glb
WORKDIR must hold bldg_0..5.json, coast.json, water.json (the raw Overpass responses).
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from build_dem_block import elevation_window, latlon_to_global_pixel, meters_per_pixel
from geo_glb_common import (EARTH_R, GLB, ear_clip, grid_indices, grid_normals, polygon_area,
                             simplify_ring)

LAT0, LON0 = 40.790, -73.965
THETA = math.radians(22.0)          # island long axis bearing (Battery -> Inwood), degrees east of north
ZOOM = 13
OVERPASS = {
    "buildings": 'way["building"](S,-74.05,N,-73.90); out tags geom  (5 latitude slices 40.695-40.895)',
    "coast": 'way["natural"="coastline"](40.66,-74.08,40.91,-73.88); out geom',
    "water_parks": 'way[natural=water | leisure=park|garden|pitch|playground | landuse=grass|recreation_ground|cemetery] out tags geom',
}


def to_enu(lon, lat):
    return (math.radians(lon - LON0) * EARTH_R * math.cos(math.radians(LAT0)),
            math.radians(lat - LAT0) * EARTH_R)


def to_model(lon, lat):
    x, y = to_enu(lon, lat)
    u = x * math.sin(THETA) + y * math.cos(THETA)
    v = -x * math.cos(THETA) + y * math.sin(THETA)   # v points left of the island axis (west, the Hudson)
    return u, -v                                        # (model X, model Z); Hudson is -Z (far side)


def from_model(X, Z):
    v = -Z
    x = X * math.sin(THETA) - v * math.cos(THETA)
    y = X * math.cos(THETA) + v * math.sin(THETA)
    return (LON0 + math.degrees(x / (EARTH_R * math.cos(math.radians(LAT0)))),
            LAT0 + math.degrees(y / EARTH_R))


def from_model_arrays(X, Z):
    v = -Z
    x = X * math.sin(THETA) - v * math.cos(THETA)
    y = X * math.cos(THETA) + v * math.sin(THETA)
    return (LON0 + np.degrees(x / (EARTH_R * math.cos(math.radians(LAT0)))),
            LAT0 + np.degrees(y / EARTH_R))


def height_of(tags):
    try:
        if "height" in tags:
            return float(tags["height"].split()[0].replace(",", "."))
        if "building:levels" in tags:
            return float(tags["building:levels"]) * 3.3
    except ValueError:
        pass
    return None


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def land_mask(coast, X0, Z0, W, D, wpx, hpx, line_px=2, lines_are_land=True):
    """Rasterize OSM coastline lines and flood-fill the sea. OSM coastline ways keep land on their
    LEFT, so a point just right of each way is sea: those points seed the flood fill (thick
    lines close small gaps in the data). Returns a land bool array (True = land)."""
    img = Image.new("L", (wpx, hpx), 0)
    draw = ImageDraw.Draw(img)
    def px(lon, lat):
        X, Z = to_model(lon, lat)
        return ((X - X0) / W * wpx, (Z - Z0) / D * hpx)
    seeds = []
    for way in coast:
        geom = way["geometry"]
        draw.line([px(p["lon"], p["lat"]) for p in geom], fill=128, width=line_px)
        if len(geom) < 100:
            continue  # small basins/piers: their 'sea' seed can fall on the wrong side of a thick line
        stride = max(1, len(geom) // 6)
        for k in range(0, len(geom) - 1, stride):
            a, b = geom[k], geom[k + 1]
            dx = (b["lon"] - a["lon"]) * math.cos(math.radians(LAT0)); dy = b["lat"] - a["lat"]
            norm = math.hypot(dx, dy)
            if norm == 0:
                continue
            off = 0.0004
            seeds.append((0.5 * (a["lon"] + b["lon"]) + off * dy / norm / math.cos(math.radians(LAT0)),
                          0.5 * (a["lat"] + b["lat"]) - off * dx / norm))
    for lon, lat in seeds:
        x, y = map(int, px(lon, lat))
        if 0 <= x < wpx and 0 <= y < hpx and img.getpixel((x, y)) == 0:
            ImageDraw.floodfill(img, (x, y), 255)
    arr = np.asarray(img)
    return (arr != 255) if lines_are_land else (arr == 0)


def build(args):
    work = Path(args.work)
    buildings = {}
    for i in range(6):
        for e in json.load(open(work / f"bldg_{i}.json"))["elements"]:
            if e["type"] == "way" and len(e.get("geometry", [])) >= 4:
                buildings[e["id"]] = e
    coast = json.load(open(work / "coast.json"))["elements"]
    overlays = json.load(open(work / "water.json"))["elements"]

    # ---- frame: bounds from the Battery and Inwood extremes plus margin
    margin_x, margin_z = args.margin, args.margin
    # Z extent from the island itself: flood-fill Manhattan's land component on a coarse pass
    cw, cX0, cZ0, cW, cD = 1600, -13000.0, -9000.0, 26000.0, 16000.0
    chp = int(cw * cD / cW)
    coarse = land_mask(coast, cX0, cZ0, cW, cD, cw, chp, line_px=3, lines_are_land=False)
    img = Image.fromarray((coarse * 255).astype(np.uint8)).copy()
    tx, tz = to_model(-73.9855, 40.7580)
    ImageDraw.floodfill(img, (int((tx - cX0) / cW * cw), int((tz - cZ0) / cD * chp)), 100)
    comp = np.asarray(img) == 100
    rr, cc = np.nonzero(comp)
    m_x = (cX0 + cc.min() / cw * cW, cX0 + (cc.max() + 1) / cw * cW)
    m_z = (cZ0 + rr.min() / chp * cD, cZ0 + (rr.max() + 1) / chp * cD)
    battery_x, inwood_x = m_x
    Z0, Z1 = m_z[0] - margin_z, m_z[1] + margin_z
    X0, X1 = m_x[0] - margin_x, m_x[1] + margin_x
    W, D = X1 - X0, Z1 - Z0

    # ---- elevation grid
    step = args.cell
    xs = np.arange(X0, X1 + step, step)
    zs_ = np.arange(Z0, Z1 + step, step)
    xs = xs[xs <= X1 + 1e-6] if xs[-1] > X1 + step else xs
    XX, ZZ = np.meshgrid(xs, zs_)
    lon, lat = from_model_arrays(XX, ZZ)
    half = int(max(W, D) / meters_per_pixel(LAT0, ZOOM) * 0.75) + 60
    elevation, cx, cy, tiles = elevation_window(LAT0, LON0, ZOOM, half, Path(args.tiles))
    pxc, pyc = latlon_to_global_pixel(LAT0, LON0, ZOOM)
    def sample(lo, la):
        gx = np.array([latlon_to_global_pixel(0, l, ZOOM)[0] for l in lo.ravel()]) if False else None
        tx = (lo + 180) / 360 * 2 ** ZOOM * 256
        ty = (1 - np.arcsinh(np.tan(np.radians(la))) / math.pi) / 2 * 2 ** ZOOM * 256
        fx, fy = tx - (pxc - cx), ty - (pyc - cy)
        x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
        ax, ay = fx - x0, fy - y0
        return (elevation[y0, x0] * (1 - ax) * (1 - ay) + elevation[y0, x0 + 1] * ax * (1 - ay)
                + elevation[y0 + 1, x0] * (1 - ax) * ay + elevation[y0 + 1, x0 + 1] * ax * ay)
    dem = sample(lon, lat)

    # ---- land mask at texture resolution
    wpx = args.tex_width
    hpx = int(round(wpx * D / W))
    land = land_mask(coast, X0, Z0, W, D, wpx, hpx)
    # Neighbouring mainland (New Jersey, the Bronx, Queens) has open coastline ways in the query window,
    # so the flood fill mislabels it as sea. Recover it: anything within ~25 m of an OSM building is land.
    foot = Image.new("L", (wpx, hpx), 0)
    fdraw = ImageDraw.Draw(foot)
    for e in buildings.values():
        pts = []
        for p in e["geometry"]:
            X, Z = to_model(p["lon"], p["lat"])
            pts.append(((X - X0) / W * wpx, (Z - Z0) / D * hpx))
        fdraw.polygon(pts, fill=255)
    near = np.asarray(foot.filter(ImageFilter.MaxFilter(7))) > 0
    land = land | near
    def land_at(X, Z):
        c = np.clip(((X - X0) / W * wpx).astype(int), 0, wpx - 1)
        r = np.clip(((Z - Z0) / D * hpx).astype(int), 0, hpx - 1)
        return land[r, c]
    is_land = land_at(XX, ZZ)
    # a vertex is land if any texel within +-half a cell is land (keeps thin land like piers attached)
    heights = np.where(is_land, np.maximum(dem, 0.5), 0.0)
    rows, cols = heights.shape

    # ---- texture
    tex = Image.new("RGB", (wpx, hpx), (140, 178, 204))
    draw = ImageDraw.Draw(tex)
    land_rgb = np.array([226, 222, 212], dtype=np.uint8)
    arr = np.asarray(tex).copy()
    arr[land] = land_rgb
    tex = Image.fromarray(arr)
    draw = ImageDraw.Draw(tex)
    def px_poly(geom):
        pts = []
        for p in geom:
            X, Z = to_model(p["lon"], p["lat"])
            pts.append(((X - X0) / W * wpx, (Z - Z0) / D * hpx))
        return pts
    for way in overlays:
        t = way["tags"]
        kind = t.get("natural") or t.get("leisure") or t.get("landuse")
        g = way.get("geometry", [])
        if len(g) < 4 or kind == "coastline":
            continue
        color = (140, 178, 204) if kind == "water" else (176, 204, 150) if kind != "pitch" else (190, 208, 160)
        draw.polygon(px_poly(g), fill=color)
    tall = []
    for bid, e in buildings.items():
        h = height_of(e["tags"])
        pts = px_poly(e["geometry"])
        xsn = [p[0] for p in pts]; ysn = [p[1] for p in pts]
        if max(xsn) < 0 or min(xsn) > wpx or max(ysn) < 0 or min(ysn) > hpx:
            continue
        shade = 168 if not h else int(np.clip(168 - h * 0.25, 120, 168))
        draw.polygon(pts, fill=(shade, shade - 4, shade - 8))
        if h and h >= args.min_height:
            tall.append((bid, e, h))
    # sea colour a touch darker near nothing; keep the sea flat
    buf = io.BytesIO()
    tex.convert("RGB").save(buf, "JPEG", quality=args.jpeg_quality, optimize=True, subsampling=0)
    tex_bytes = buf.getvalue()
    if args.save_texture:
        Path(args.save_texture).write_bytes(tex_bytes)

    # ---- glTF
    g = GLB("Universe Scales Manhattan block builder")
    tex_id = g.texture(tex_bytes, "image/jpeg")
    mat_terrain = g.material("terrain and shoreline texture", texture=tex_id, rough=0.95)
    mat_vc = g.material("vertex colored", rough=0.9)
    positions = np.stack((XX, heights, ZZ), axis=-1).reshape(-1, 3)
    normals = grid_normals(heights, step, step)
    uvs = np.stack(((XX - X0) / W, (ZZ - Z0) / D), axis=-1).reshape(-1, 2)
    top = g.primitive(positions, grid_indices(rows, cols), mat_terrain, normals=normals, uvs=uvs)
    prims = [top]

    # skirt: terrain edge down to a flat base, water-blue where the edge is sea, earth-toned on land
    base_y = -args.base
    sk_pos, sk_col, sk_nrm, sk_idx = [], [], [], []
    ring = ([(0, c) for c in range(cols)] + [(r, cols - 1) for r in range(1, rows)]
            + [(rows - 1, c) for c in range(cols - 2, -1, -1)] + [(r, 0) for r in range(rows - 2, 0, -1)])
    def skirt_color(r, c, top_edge):
        if heights[r, c] <= 0.0:
            return np.array([0.36, 0.56, 0.70]) if top_edge else np.array([0.09, 0.16, 0.24])
        return np.array([0.55, 0.50, 0.44]) if top_edge else np.array([0.25, 0.23, 0.22])
    for k, (r, c) in enumerate(ring):
        r2, c2 = ring[(k + 1) % len(ring)]
        a, b = positions[r * cols + c], positions[r2 * cols + c2]
        out = np.array([b[2] - a[2], 0, a[0] - b[0]]); out = out / (np.linalg.norm(out) or 1)
        i = len(sk_pos)
        # water sits at y=0; a water-edge column tops out at 0 already
        sk_pos.extend((a, b, [a[0], base_y, a[2]], [b[0], base_y, b[2]]))
        sk_nrm.extend([out] * 4)
        sk_col.extend((skirt_color(r, c, True), skirt_color(r2, c2, True), skirt_color(r, c, False), skirt_color(r2, c2, False)))
        sk_idx.extend((i, i + 2, i + 1, i + 1, i + 2, i + 3))
    fl = len(sk_pos)
    sk_pos.extend(([X0, base_y, Z0], [X0, base_y, Z1], [X1, base_y, Z0], [X1, base_y, Z1]))
    sk_nrm.extend(([0, -1, 0],) * 4); sk_col.extend(([0.25, 0.23, 0.22],) * 4)
    sk_idx.extend((fl, fl + 1, fl + 2, fl + 2, fl + 1, fl + 3))
    prims.append(g.primitive(sk_pos, sk_idx, mat_vc, normals=sk_nrm, colors=sk_col))

    # extruded tall buildings
    b_pos, b_nrm, b_col, b_idx = [], [], [], []
    count = 0
    for bid, e, h in tall:
        pts = [to_model(p["lon"], p["lat"]) for p in e["geometry"]]
        if pts[0] == pts[-1]:
            pts = pts[:-1]
        if not (X0 < np.mean([p[0] for p in pts]) < X1 and Z0 < np.mean([p[1] for p in pts]) < Z1):
            continue
        pts = simplify_ring(pts, args.simplify)
        if len(pts) < 3 or abs(polygon_area(pts)) < args.min_area:
            continue
        cxm, czm = np.mean([p[0] for p in pts]), np.mean([p[1] for p in pts])
        gx = np.clip(((cxm - X0) / step), 0, cols - 1.001); gz = np.clip(((czm - Z0) / step), 0, rows - 1.001)
        r0, c0 = int(gz), int(gx)
        ground = float(heights[r0:r0 + 2, c0:c0 + 2].min())
        if not land_at(np.array([cxm]), np.array([czm]))[0]:
            continue
        ground_dem = float(dem[r0:r0 + 2, c0:c0 + 2].mean()) if ground > 0 else 0.0
        top_y = max(ground_dem, 0.5) + h
        bot_y = ground - 4.0
        t = np.clip(h / 300.0, 0, 1)
        jitter = ((bid * 2654435761) % 1000) / 1000.0
        wall = np.array([0.66, 0.65, 0.64]) * (1 - t) + np.array([0.80, 0.82, 0.86]) * t
        wall = wall * (0.92 + 0.12 * jitter)
        roof = np.clip(wall * 1.08, 0, 1)
        area = polygon_area(pts)
        seq = pts if area > 0 else pts[::-1]
        n = len(seq)
        for k in range(n):
            (x1, z1), (x2, z2) = seq[k], seq[(k + 1) % n]
            nx, nz = (z2 - z1), -(x2 - x1)          # outward normal for CCW (in X,Z with Y up viewed from above => flipped below)
            ln = math.hypot(nx, nz) or 1
            nrm = [-nx / ln, 0, -nz / ln]
            i = len(b_pos)
            b_pos.extend(([x1, bot_y, z1], [x2, bot_y, z2], [x1, top_y, z1], [x2, top_y, z2]))
            b_nrm.extend([nrm] * 4)
            b_col.extend((wall * 0.85, wall * 0.85, wall, wall))
            b_idx.extend((i, i + 1, i + 2, i + 2, i + 1, i + 3))
        tris = ear_clip(seq)
        base = len(b_pos)
        b_pos.extend([[x, top_y, z] for x, z in seq]); b_nrm.extend([[0, 1, 0]] * n); b_col.extend([roof] * n)
        for a_, b_, c_ in tris:
            b_idx.extend((base + a_, base + c_, base + b_))
        count += 1
    if b_pos:
        prims.append(g.primitive(b_pos, b_idx, mat_vc, colors=b_col, rgba8=True))  # no normals: flat shading
    g.mesh_node("Manhattan block", prims)

    for name, (lon_, lat_), text in [("battery-label", (-74.0150, 40.7040), "The Battery"),
                                      ("inwood-label", (-73.9265, 40.8720), "Inwood")]:
        X, Z = to_model(lon_, lat_)
        g.label_node(name, (X, 200, Z), text)
    size = g.write(args.output)
    return {"output": str(args.output), "bytes": size, "triangles": g.triangles,
            "extruded_buildings": count, "candidates_ge_min_height": len(tall),
            "buildings_total": len(buildings), "grid": [rows, cols], "cell_m": step,
            "block_m": [W, D], "bounds_x": [X0, X1], "bounds_z": [Z0, Z1], "texture": [wpx, hpx],
            "texture_bytes": len(tex_bytes), "island_x_extent_m": [battery_x, inwood_x], "island_z_extent_m": list(m_z),
            "island_length_m": inwood_x - battery_x,
            "tiles": tiles,
            "inputs_sha256": {f: sha_file(work / f) for f in
                              [f"bldg_{i}.json" for i in range(6)] + ["coast.json", "water.json"]}}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", required=True)
    ap.add_argument("--tiles", default="/private/tmp/dem-tiles-manhattan")
    ap.add_argument("--output", required=True)
    ap.add_argument("--margin", type=float, default=500.0)
    ap.add_argument("--cell", type=float, default=100.0)
    ap.add_argument("--base", type=float, default=80.0)
    ap.add_argument("--tex-width", type=int, default=2560)
    ap.add_argument("--jpeg-quality", type=int, default=80)
    ap.add_argument("--min-height", type=float, default=65.0)
    ap.add_argument("--min-area", type=float, default=120.0)
    ap.add_argument("--simplify", type=float, default=3.0)
    ap.add_argument("--save-texture", default=None)
    args = ap.parse_args()
    out = build(args)
    out.pop("tiles"); print(json.dumps(out, indent=2))
