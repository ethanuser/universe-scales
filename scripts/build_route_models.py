#!/usr/bin/env python3
"""Build geographic Length diagrams without confusing path length with span.

Coordinates remain at geographic scale. The separate straight ruler represents
the listed route/inventory length, not a geographic end-to-end measurement.
Inputs and generated outputs are cached outside the repo; no runtime API needed.
"""

import argparse
import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from build_dem_block import fetch_tile, latlon_to_global_pixel
from fetch_model_assets import write_json
from geo_glb_common import GLB, grid_indices, hillshade
from build_earth_moon_model import add_sphere

RADIUS_KM = 6371.0088
OSM_LICENSE = "https://opendatacommons.org/licenses/odbl/1-0/"
CONFIG = {
    "marathon": {"id": "boston-marathon-course", "item": "Marathon Distance", "total_km": 42.195,
                 "center": (-71.32, 42.31), "bounds": (-71.55, 42.20, -71.06, 42.38),
                 "zoom": 11, "vertical_gain": 12,
                 "source": "https://www.openstreetmap.org/relation/11680552",
                 "basis": "https://www.baa.org/races/boston-marathon/the-course/",
                 "ruler": "42.2 km",
                 "color": (0.05, 0.38, 0.86, 1)},
    "amazon": {"id": "amazon-river-geography", "item": "Amazon River", "total_km": 6400,
               "center": (-64, -5), "bounds": (-80, -18, -48, 7), "zoom": 5,
               "vertical_gain": 16,
               "source": "https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-rivers-lake-centerlines/",
               "basis": "https://www.esa.int/ESA_Multimedia/Images/2020/09/Amazon_River",
               "ruler": "~6,400 km",
               "color": (0.025, 0.34, 0.7, 1)},
    "wall": {"id": "great-wall-network-globe", "item": "Great Wall of China", "total_km": 21196.18,
             "center": (108, 37), "source": "https://www.openstreetmap.org/relation/318110",
             "basis": "https://whc.unesco.org/document/157507/",
             "ruler": "21,200 km total",
             "color": (0.96, 0.32, 0.1, 1)},
}


def geodesic_km(points):
    """Spherical geodesic sum, never the normalization used for the model."""
    points = np.radians(np.asarray(points, float))
    delta = np.diff(points, axis=0)
    a = np.sin(delta[:, 1] / 2) ** 2 + np.cos(points[:-1, 1]) * np.cos(points[1:, 1]) * np.sin(delta[:, 0] / 2) ** 2
    return float(np.sum(2 * RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))))


def geographic_frame(lonlat, center, height=0):
    """Earth-centered spherical coordinates in an east/up/south local frame.

    Chord distances and Earth curvature are preserved; this is not Web Mercator.
    Height and radius are km. The tangent datum at the center is y=0.
    """
    p = np.radians(np.asarray(lonlat, float))
    lon0, lat0 = np.radians(center)
    dlon = p[..., 0] - lon0
    lat = p[..., 1]
    radius = RADIUS_KM + np.asarray(height)
    x = radius * np.cos(lat) * np.sin(dlon)
    up = radius * (np.sin(lat) * math.sin(lat0) + np.cos(lat) * math.cos(lat0) * np.cos(dlon))
    north = radius * (np.sin(lat) * math.cos(lat0) - np.cos(lat) * math.sin(lat0) * np.cos(dlon))
    return np.stack((x, up - RADIUS_KM, -north), axis=-1)


def lines_from_geojson(document):
    result = []
    for feature in document["features"]:
        geometry = feature["geometry"]
        lines = [geometry["coordinates"]] if geometry["type"] == "LineString" else geometry["coordinates"]
        for points in lines:
            if len(points) >= 2:
                result.append(np.asarray(points, float))
    return result


def clip_lines(lines, bounds):
    """Clip each source segment to the map window, without joining fragments."""
    west, south, east, north = bounds
    result = []
    for line in lines:
        current = []
        for a, b in zip(line[:-1], line[1:]):
            delta = b - a
            lo, hi = 0., 1.
            for p, q in ((-delta[0], a[0] - west), (delta[0], east - a[0]),
                         (-delta[1], a[1] - south), (delta[1], north - a[1])):
                if p == 0:
                    if q < 0:
                        lo, hi = 1., 0.
                        break
                elif p < 0:
                    lo = max(lo, q / p)
                else:
                    hi = min(hi, q / p)
            if lo <= hi:
                start, end = a + lo * delta, a + hi * delta
                if current and not np.allclose(current[-1], start, rtol=0, atol=1e-8):
                    result.append(np.asarray(current))
                    current = []
                if not current:
                    current.append(start)
                current.append(end)
            elif current:
                result.append(np.asarray(current))
                current = []
        if len(current) > 1:
            result.append(np.asarray(current))
    return result


def osm_geojson(document):
    """Keep source ways separate: never bridge a gap or silently join branches."""
    relation = next(e for e in document["elements"] if e["type"] == "relation")
    features, seen = [], set()
    for member in relation["members"]:
        if member["type"] != "way" or member["ref"] in seen:
            continue
        geometry = member.get("geometry")
        if not geometry or any(p is None for p in geometry):
            raise ValueError("Incomplete OSM way geometry")
        seen.add(member["ref"])
        features.append({"type": "Feature", "properties": {"osm_way": member["ref"]},
                         "geometry": {"type": "LineString", "coordinates": [[p["lon"], p["lat"]] for p in geometry]}})
    if not features:
        raise ValueError("OSM relation contains no geometric ways")
    return {"type": "FeatureCollection", "source": f"https://www.openstreetmap.org/relation/{relation['id']}",
            "license": OSM_LICENSE, "attribution": "(c) OpenStreetMap contributors", "features": features}


def add_lines(glb, name, lines, color, width=0, radial=False):
    segments = [np.stack((p[:-1], p[1:]), axis=1).reshape(-1, 3) for p in lines if len(p) > 1]
    if not segments:
        raise ValueError("No line segments to render")
    positions = np.concatenate(segments).astype(np.float32)
    material = glb.material(name, color=color)
    glb.doc.setdefault("extensionsUsed", ["KHR_materials_unlit"])
    glb.doc["materials"][material]["extensions"] = {"KHR_materials_unlit": {}}
    position = glb._accessor(positions, 5126, "VEC3", 34962, True)
    glb.mesh_node(name, [{"attributes": {"POSITION": position}, "material": material, "mode": 1}])
    if width:
        pairs = positions.reshape(-1, 2, 3).astype(float)
        direction = pairs[:, 1] - pairs[:, 0]
        up = pairs.mean(axis=1) if radial else np.tile([0., 1., 0.], (len(pairs), 1))
        side = np.cross(up, direction)
        side *= width / 2 / np.maximum(np.linalg.norm(side, axis=1, keepdims=True), 1e-12)
        ribbon = np.stack((pairs[:, 0] - side, pairs[:, 0] + side,
                           pairs[:, 1] - side, pairs[:, 1] + side), axis=1).reshape(-1, 3)
        index = (np.arange(len(pairs))[:, None] * 4 + np.array([0, 2, 1, 1, 2, 3])).ravel()
        glb.mesh_node(name + " (display-width ribbon)", [glb.primitive(ribbon, index, material)])


def add_ruler(glb, total, y, z, caption):
    # This ruler is deliberately independent of the path's measured geometry.
    material = glb.material("Length guide", color=(0.72, 0.76, 0.8, 1))
    glb.doc.setdefault("extensionsUsed", ["KHR_materials_unlit"])
    glb.doc["materials"][material]["extensions"] = {"KHR_materials_unlit": {}}
    vertices = np.array([[-1,-1,-1], [1,-1,-1], [1,1,-1], [-1,1,-1],
                         [-1,-1,1], [1,-1,1], [1,1,1], [-1,1,1]], float) / 2
    indices = [0,2,1,0,3,2,4,5,6,4,6,7,0,1,5,0,5,4,3,7,6,3,6,2,0,4,7,0,7,3,1,2,6,1,6,5]
    for axis, length, position in [("x", total, [0, y, z]),
            ("y", total * 0.018, [-total / 2, y + total * 0.009, z]),
            ("y", total * 0.018, [total / 2, y + total * 0.009, z])]:
        glb.mesh_node("Straightened total-length reference", [glb.primitive(vertices, indices, material)], position)
        glb.doc["nodes"][-1].update(scale=[length if a == axis else total * 0.002 for a in "xyz"],
            extras={"screenLine": {"axis": axis, "length": length, "width": 2}})
    glb.label_node("Total length", [0, y, z], caption, labelRole="dimension", labelOffset={"x": 0, "y": -10})


def land_mask(land, bounds, size):
    west, south, east, north = bounds
    image = Image.new("L", size, 0)
    draw = ImageDraw.Draw(image)
    def pixels(ring):
        return [((p[0] - west) / (east - west) * size[0], (north - p[1]) / (north - south) * size[1]) for p in ring]
    for feature in land["features"]:
        geo = feature["geometry"]
        polygons = [geo["coordinates"]] if geo["type"] == "Polygon" else geo["coordinates"]
        for polygon in polygons:
            draw.polygon(pixels(polygon[0]), fill=255)
            for hole in polygon[1:]:
                draw.polygon(pixels(hole), fill=0)
    return image


def sample_elevation(lonlat, zoom, cache):
    """Bilinear Terrarium sampling with explicit zero ocean/negative elevations."""
    pixels = np.array([latlon_to_global_pixel(lat, lon, zoom) for lon, lat in np.asarray(lonlat).reshape(-1, 2)])
    result = np.zeros(len(pixels))
    tiles = {}
    provenance = []
    for i, (px, py) in enumerate(pixels):
        tx, ty = int(px // 256), int(py // 256)
        key = (tx, ty)
        if key not in tiles:
            tile, meta = fetch_tile(zoom, tx, ty, cache)
            tiles[key] = tile[:, :, 0].astype(float) * 256 + tile[:, :, 1] + tile[:, :, 2] / 256 - 32768
            provenance.append(meta)
        x, y = px % 256, py % 256
        # Clamp within the tile; one-pixel seam error is bounded by source resolution.
        x0, y0 = min(int(x), 254), min(int(y), 254)
        fx, fy = min(x - x0, 1), min(y - y0, 1)
        h = tiles[key]
        result[i] = max(0, h[y0, x0] * (1 - fx) * (1 - fy) + h[y0, x0 + 1] * fx * (1 - fy)
                        + h[y0 + 1, x0] * (1 - fx) * fy + h[y0 + 1, x0 + 1] * fx * fy) / 1000
    return result.reshape(np.asarray(lonlat).shape[:-1]), provenance


def terrain(glb, config, land, cache, rows=65, cols=145):
    west, south, east, north = config["bounds"]
    lon, lat = np.meshgrid(np.linspace(west, east, cols), np.linspace(north, south, rows))
    coordinates = np.stack((lon, lat), axis=-1)
    heights, tiles = sample_elevation(coordinates, config["zoom"], cache)
    positions = geographic_frame(coordinates, config["center"], heights * config["vertical_gain"])
    width, depth = np.ptp(positions[:, :, 0]), np.ptp(positions[:, :, 2])
    shade = hillshade(heights, width / (cols - 1), depth / (rows - 1))
    ramp = np.clip(heights / (4 if config["item"] == "Amazon River" else 0.25), 0, 1)[..., None]
    color = np.array([0.33, 0.48, 0.3]) * (1 - ramp) + np.array([0.71, 0.67, 0.53]) * ramp
    color *= (0.7 + 0.3 * shade)[..., None]
    mask = np.asarray(land_mask(land, config["bounds"], (cols, rows))) > 0
    color[~mask] = [0.1, 0.3, 0.43]
    texture = Image.fromarray(np.uint8(np.clip(color, 0, 1) * 255)).resize((1024, 512), Image.Resampling.BICUBIC)
    image = io.BytesIO()
    texture.save(image, format="JPEG", quality=88)
    material = glb.material("Elevation tint, not satellite imagery", texture=glb.texture(image.getvalue(), "image/jpeg"))
    u, v = np.meshgrid(np.linspace(0, 1, cols), np.linspace(0, 1, rows))
    # Normals follow the curved elevation surface, not a flattened height ramp.
    du, dv = np.gradient(positions, axis=1), np.gradient(positions, axis=0)
    normals = np.cross(dv, du)
    normals /= np.maximum(np.linalg.norm(normals, axis=-1, keepdims=True), 1e-12)
    glb.mesh_node("Geographic terrain", [glb.primitive(positions.reshape(-1, 3), grid_indices(rows, cols), material,
                                                     normals=normals.reshape(-1, 3), uvs=np.stack((u, v), axis=-1).reshape(-1, 2))])
    perimeter = np.concatenate((positions[0], positions[1:, -1], positions[-1, -2::-1], positions[-2:0:-1, 0]))
    bottom = float(positions[:, :, 1].min() - config["total_km"] * 0.014)
    bottom_ring = perimeter.copy()
    bottom_ring[:, 1] = bottom
    n = len(perimeter)
    walls = np.concatenate((perimeter, bottom_ring))
    sides = []
    for i in range(n):
        j = (i + 1) % n
        sides.extend((i, j, n + i, j, n + j, n + i))
    # A convex projected rectangular window has a simple opaque bottom fan.
    sides.extend(v for i in range(1, n - 1) for v in (n, n + i + 1, n + i))
    stone = glb.material("Closed terrain section", color=(0.3, 0.32, 0.27, 1))
    glb.mesh_node("Opaque terrain sides and base", [glb.primitive(walls, sides, stone)])
    return positions, bottom, tiles


def drape_on_terrain(points, positions, config, offset):
    """Drape on the rendered triangles, not finer DEM samples buried by them."""
    west, south, east, north = config["bounds"]
    rows, cols = positions.shape[:2]
    u = np.clip((points[:, 0] - west) / (east - west) * (cols - 1), 0, cols - 1)
    v = np.clip((north - points[:, 1]) / (north - south) * (rows - 1), 0, rows - 1)
    x, y = np.minimum(u.astype(int), cols - 2), np.minimum(v.astype(int), rows - 2)
    fx, fy = (u - x)[:, None], (v - y)[:, None]
    a, b, c, d = positions[y, x], positions[y + 1, x], positions[y, x + 1], positions[y + 1, x + 1]
    surface = np.where(fx + fy <= 1, a + fx * (c - a) + fy * (b - a),
                       d + (1 - fx) * (b - d) + (1 - fy) * (c - d))
    surface[:, 1] += offset
    return surface


def globe(glb, land, center):
    source = Path(__file__).resolve().parents[1] / "content/visualizations/models/nasa-earth.glb"
    add_sphere(glb.doc, glb.bin, source.read_bytes(), "Earth", 0, 1000)
    node = glb.doc["nodes"][-1]
    node["scale"] = [RADIUS_KM] * 3
    # NASA atlas: longitude = atan2(x,z) - pi; north is +y.
    # R_x(latitude) R_y(pi-longitude) puts the requested location front/center.
    lon, lat = map(math.radians, center)
    a, b = lat / 2, (math.pi - lon) / 2
    node["rotation"] = [math.sin(a)*math.cos(b), math.cos(a)*math.sin(b),
                        math.sin(a)*math.sin(b), math.cos(a)*math.cos(b)]
    glb.doc["scenes"][0]["nodes"].append(len(glb.doc["nodes"]) - 1)
    glb.triangles += 3072
    return -RADIUS_KM


def build(kind, geojson, land, cache, output):
    config = CONFIG[kind]
    geojson = dict(geojson)
    geojson["source"] = config["source"]
    geojson["attribution"] = "(c) OpenStreetMap contributors" if kind != "amazon" else "Natural Earth"
    geojson["license"] = "ODbL-1.0" if kind != "amazon" else "public domain"
    geojson["license_url"] = OSM_LICENSE if kind != "amazon" else "https://www.naturalearthdata.com/about/terms-of-use/"
    lines = lines_from_geojson(geojson)
    if not lines:
        raise ValueError("No source geography")
    glb = GLB("Universe Scales calibrated geographic route diagram")
    projected, tiles = [], []
    if kind == "wall":
        bottom = globe(glb, land, config["center"])
        projected = [geographic_frame(p, config["center"], 5) for p in lines]
        projected = [np.column_stack((p[:, 0], -p[:, 2], p[:, 1] + RADIUS_KM)) for p in projected]
        bottom = -RADIUS_KM
        z = 0
    else:
        positions, bottom, tiles = terrain(glb, config, land, cache)
        lines = clip_lines(lines, config["bounds"])
        projected = [drape_on_terrain(p, positions, config, config["total_km"] * 0.001) for p in lines]
        z = float(positions[:, :, 2].max() + config["total_km"] * 0.035)
    if kind == "amazon":
        mainstem = lines_from_geojson({"features": geojson["features"][:1]})
        mainstem = clip_lines(mainstem, config["bounds"])
        add_lines(glb, "Context tributaries (not summed as mainstem)", projected, (0.2, 0.45, 0.53, 1))
        highlighted = []
        for p in mainstem:
            highlighted.append(drape_on_terrain(p, positions, config, config["total_km"] * 0.0012))
        add_lines(glb, "Partial Amazonas mainstem (does not reach Atlantic)", highlighted, (0.04, 0.25, 0.9, 1), width=18)
        for coords, caption in [((-73.488623, -4.444854), "Ucayali-Maranon"),
                                ((-52.711768, -1.583820), "Inland mapped end")]:
            at = geographic_frame(np.asarray(coords), config["center"], config["total_km"] * 0.02)
            glb.label_node(caption, at, caption, labelLayout="orbit", labelPriority=0)
    else:
        add_lines(glb, "Mapped routes (gaps retained)", projected, config["color"],
                  width=100 if kind == "wall" else 0.14, radial=kind == "wall")
    if kind == "marathon":
        for coords, caption in [((-71.518205, 42.2297774), "Hopkinton"),
                                ((-71.0787, 42.3498), "Boston")]:
            h, _ = sample_elevation(np.asarray([coords]), config["zoom"], cache)
            at = geographic_frame(np.asarray(coords), config["center"], h[0] * config["vertical_gain"] + 0.7)
            glb.label_node(caption, at, caption, labelLayout="orbit", labelPriority=0)
    add_ruler(glb, config["total_km"], bottom - config["total_km"] * 0.035, z, config["ruler"])
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{config['id']}.glb"
    size = glb.write(path)
    osm = kind in {"wall", "marathon"}
    source_file = f"sources/routes/{config['id']}.geojson"
    author = ("(c) OpenStreetMap contributors; " if osm else "Natural Earth; ")
    author += ("NASA VTAD Earth; " if kind == "wall" else "Mapzen/USGS terrain; ")
    author += "diagram by Universe Scales"
    notes = {
        "marathon": "Boston's Hopkinton-to-Copley Square course is shown from 265 connected OpenStreetMap road ways over sampled Mapzen/USGS bare-earth elevation. The source graph has one start-to-finish path without invented connectors; its 42.417 km cartographic length is not the certified shortest running line. Horizontal coordinates are not stretched to 42.195 km: the lower straightened ruler marks the standard marathon distance. The displayed ribbon is draped on the terrain mesh, not a surveyed road-deck profile, and its width is exaggerated. Bare-earth relief is exaggerated 12 times and cannot establish runner-grade hill gradients. Tint is illustrative, not aerial photography. The B.A.A. defines the course; World Athletics defines the distance. Contains information from OpenStreetMap under ODbL; source geometry is supplied with the model.",
        "amazon": "A geographic Amazon-system diagram from Natural Earth centerlines and Mapzen elevation, not a full headwater-to-mouth survey. The highlighted 3,053 km cartographic reach runs from the Ucayali/Maranon confluence to an endpoint inland near the Xingu confluence region: it does not reach the Atlantic. Muted tributaries are geographic context, not part of that route. Unrepresented reaches are not joined. Heights are exaggerated 16 times; colors and river widths are illustrative. The separate approximate 6,400 km ruler follows NASA/ESA's common full-river estimate; FAO reports about 6,300-6,437 km under different source definitions. No river geometry is stretched to the total. Natural Earth cautions about imperfect basin alignments. This is a regional locator, not navigation or a measured river volume.",
        "wall": "Mapped Great Wall fragments and branches from OpenStreetMap appear on the same NASA Earth mesh and textures as the Earth Diameter item, with north up over China in the resting view. The orange line is widened to 100 km and raised 5 km for visibility, not wall thickness or height. This community mapping is incomplete and is not the official heritage inventory. The separate ruler shows the 2012 survey total of 21,196.18 km across walls and trenches from multiple eras, not a single continuous wall or the distance across China. Visible gaps are retained. Contains information from OpenStreetMap under ODbL; the derivative source geometry is supplied with the model. NASA media usage guidelines apply to the globe.",
    }
    note = notes[kind]
    entry = {"id": config["id"], "source": config["source"], "link_label": "Geographic model source",
             "basis_url": config["basis"], "basis_label": "Survey/course definition" if osm else "ESA: approximate full-river length",
             "author": author,
             "license": "OpenStreetMap geometry: ODbL 1.0; Natural Earth: public domain; authored diagram: CC-BY-4.0" if osm else "Natural Earth: public domain; Mapzen/USGS attribution; authored diagram: CC-BY-4.0",
             "license_url": OSM_LICENSE if osm else "https://www.naturalearthdata.com/about/terms-of-use/",
             "license_files": ["sources/route-models.md", "licenses/CC-BY-4.0.txt", source_file]
                              + (["licenses/ODbL-1.0.txt"] if osm else []),
             "matches": {"length": [config["item"]]}, "geometry": "geographic route diagram",
             "volume_semantics": "not a volume measurement", "closed_volume_checked": False,
             "presentation": {"reference_size": config["total_km"], "pitch": 0 if kind == "wall" else 55,
                              "layout_width_factor": 1.08, "focus_scale_factor": 1.1},
             "note": note,
             "processing": {"script": "scripts/build_route_models.py", "source_geometry": source_file,
                            "land_source": "content/visualizations/land.geojson",
                            "land_sha256": hashlib.sha256(json.dumps(land, sort_keys=True).encode()).hexdigest(),
                            "terrain_texture": "elevation tint; not aerial imagery",
                            "source_geometry_sha256": hashlib.sha256(json.dumps(geojson, sort_keys=True).encode()).hexdigest(),
                            "geographic_frame": "spherical ECEF/local tangent, mean Earth radius 6371.0088 km",
                            "model_unit": "km", "route_rescaled": False,
                            "mapped_segment_sum_km": sum(geodesic_km(p) for p in lines),
                            "mapped_path_count": len(lines), "total_reference_km": config["total_km"],
                            "vertical_exaggeration": config.get("vertical_gain", 1), "terrain_tiles": list({m["url"]: m for m in tiles}.values())}}
    if kind == "wall":
        earth = Path(__file__).resolve().parents[1] / "content/visualizations/models/nasa-earth.glb"
        entry["license"] = "OpenStreetMap geometry: ODbL 1.0; NASA Earth: U.S. public-domain media guidelines; authored diagram: CC-BY-4.0"
        entry["license_files"] += ["licenses/nasa-media-guidelines.html", "licenses/nasa-3d-resources.README.md"]
        entry["processing"]["earth_asset"] = {"source": "https://science.nasa.gov/resource/earth-3d-model/",
            "sha256": hashlib.sha256(earth.read_bytes()).hexdigest(), "operations": "Original NASA geometry, atlas and normal map; geographic rotation only"}
    write_json(output / f"{config['id']}.json", entry)
    (output / f"{config['id']}.geojson").write_text(json.dumps(geojson, separators=(",", ":"), ensure_ascii=True) + "\n")
    print(f"{path}: {size:,} bytes; {glb.triangles:,} triangles; {len(lines)} source paths; total ruler {config['total_km']} km")
    return entry, glb


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=CONFIG)
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--land", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path("/private/tmp/us-route-models/tiles"))
    parser.add_argument("--output", type=Path, default=Path("/private/tmp/us-route-models/built"))
    args = parser.parse_args()
    geojson = json.loads(args.geometry.read_text())
    if "elements" in geojson:
        geojson = osm_geojson(geojson)
    build(args.kind, geojson, json.loads(args.land.read_text()), args.cache, args.output)


if __name__ == "__main__":
    main()
