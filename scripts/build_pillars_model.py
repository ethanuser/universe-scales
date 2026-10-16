#!/usr/bin/env python3
"""Build the Pillars of Creation model: STScI's 3D reconstruction wearing Hubble's
image, inside glowing ionized gas.

    ./venv/bin/python scripts/build_pillars_model.py PILLARS.glb HUBBLE.jpg OUT.glb

PILLARS.glb is the registered STScI mesh (nasa-pillars-of-creation.glb, whose long
axis is +y and whose Hubble line of sight is +x). HUBBLE.jpg is NASA's 2015 visible
image (eagle_pillars_2015-hst-3107x3240_print.jpg from NASA SVS 30774, served at
1024 x 1067 px). The mesh's silhouette was fitted to the image (FIT below, IoU 0.52;
the misses are bright rims and foreground dust that the mesh leaves out).

Output units are light-years, the tallest pillar 5 ly (NASA). Observer is +z, so the
explorer's resting view is Hubble's; turning it shows that the three pillars are
four clouds spread about 6 ly along the line of sight.

Layers:
  pillars   the mesh with the photo projected on it (unlit). Faces that look away
            from Hubble, or are hidden behind another cloud, are darkened dust.
  rims      glowing sprites on the visible surface where the photo is brighter than
            its surroundings: the ionization fronts boiling off the pillars.
  gas       the photo outside the pillars (stars removed) as glowing sprites spread
            through an illustrative 7 ly deep slab.
  stars     point sources from the photo at illustrative depths.
"""
import argparse
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_model_assets import read_glb  # noqa: E402
from nebula_volume import add_cloud, calibrated_samples, elliptical_feather, grid_samples, load_rgb, sample_field, smooth_noise, split_stars  # noqa: E402
from texture_padding import accessor_array  # noqa: E402
from volume_glb import VolumeGLB  # noqa: E402

PILLAR_LY = 5.0
FIT = (14.3256, 480.865, 1138.424)   # px per mesh unit, image x of mesh z=0, image y of mesh base
PER_PIXEL = {"rims": 1 / 160, "gas": 1 / 22, "fine": 1 / 60, "stars": 1 / 380, "bright": 1 / 120}


def load_mesh(path):
    document, binary = read_glb(Path(path).read_bytes())
    node = document["nodes"][0]
    primitive = document["meshes"][node["mesh"]]["primitives"][0]
    accessor = document["accessors"][primitive["attributes"]["POSITION"]]
    positions = accessor_array(document, binary, primitive["attributes"]["POSITION"]).astype(np.float64)
    if accessor.get("normalized"):
        positions /= 32767
    positions = positions * node.get("scale", [1, 1, 1]) + node.get("translation", [0, 0, 0])
    indices = accessor_array(document, binary, primitive["indices"]).reshape(-1, 3).astype(np.int64)
    return positions, indices


def vertex_normals(positions, indices):
    a, b, c = (positions[indices[:, k]] for k in range(3))
    face = np.cross(b - a, c - a)
    normals = np.zeros_like(positions)
    for k in range(3):
        np.add.at(normals, indices[:, k], face)
    return normals / np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)


def visible_vertices(uv_px, depth, indices, size, scale=0.5, tolerance=0.08):
    """Painter's-algorithm index buffer: is each vertex on the surface nearest Hubble?"""
    width, height = (int(s * scale) for s in size)
    canvas = Image.new("I", (width, height), -1)
    draw = ImageDraw.Draw(canvas)
    order = np.argsort(depth[indices].mean(axis=1))
    for face in order:
        draw.polygon([tuple(uv_px[k] * scale) for k in indices[face]], fill=int(face))
    buffer = np.asarray(canvas)
    front_depth = np.where(buffer >= 0, depth[indices].max(axis=1)[np.maximum(buffer, 0)], -np.inf)
    px = np.clip((uv_px * scale).astype(int), 0, [width - 1, height - 1])
    nearest = ndimage.maximum_filter(front_depth, size=3)[px[:, 1], px[:, 0]]
    return (depth >= nearest - tolerance) | ~np.isfinite(nearest)


def build(mesh_path, image_path, output, seed=0x9111):
    rng = np.random.default_rng(seed)
    raw, indices = load_mesh(mesh_path)
    image = load_rgb(image_path)
    height, width = image.shape[:2]
    px_per_unit, x0, y0 = FIT
    ly_per_unit = PILLAR_LY / raw[:, 1].max()
    ly_per_px = ly_per_unit / px_per_unit
    # Hubble looks along +x of the source mesh; make it -z (observer at +z).
    positions = np.column_stack([raw[:, 2], raw[:, 1], -raw[:, 0]]) * ly_per_unit
    normals = vertex_normals(positions, indices)
    uv_px = np.column_stack([x0 + raw[:, 2] * px_per_unit, y0 - raw[:, 1] * px_per_unit])
    uvs = uv_px / [width, height]

    def to_model(x_px, y_px):
        return (x_px - x0) * ly_per_px, (y0 - y_px) * ly_per_px

    # Mesh shading: full photo where Hubble sees the surface; elsewhere dark dust,
    # lit from above where NGC 6611's stars are.
    visible = visible_vertices(uv_px, positions[:, 2], indices, (width, height))
    facing = np.clip((normals[:, 2] + 0.1) / 0.6, 0, 1) ** 1.5
    seen = facing * visible
    light = np.clip(normals @ np.array([0.0, 0.8, 0.6]), 0, 1)
    dust = 0.22 + 0.38 * light
    factor = seen + (1 - seen) * dust
    shade = np.column_stack([factor, factor * 0.93, factor * 0.86])

    glb = VolumeGLB("Universe Scales Pillars of Creation builder")
    texture_image = Image.fromarray((image * 255).astype(np.uint8))
    material = glb.unlit("pillars-hubble", texture=glb.jpeg_texture(texture_image, 86), blend=False)
    mesh = glb.primitive(positions, indices.ravel(), material, colors=shade, uvs=uvs, rgba8=True)
    glb.node("pillars", [mesh])

    gas, stars = split_stars(image, radius=4, threshold=0.08, limit=1500)
    silhouette = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(silhouette)
    for face in indices:
        draw.polygon([tuple(uv_px[k]) for k in face], fill=255)
    inside = ndimage.gaussian_filter(np.asarray(silhouette, np.float32) / 255, 3)

    # Rims: sample the visible surface, weighted by how much the photo there
    # outshines its surroundings.
    a, b, c = (positions[indices[:, k]] for k in range(3))
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
    face_seen = seen[indices].mean(axis=1)
    highlight = np.clip(gas - ndimage.gaussian_filter(gas, (12, 12, 0)), 0, None).max(axis=2)
    count = 16000
    face = rng.choice(len(indices), size=count * 4, p=area * face_seen / (area * face_seen).sum())
    r1, r2 = rng.random((2, count * 4))
    flip = r1 + r2 > 1
    r1[flip], r2[flip] = 1 - r1[flip], 1 - r2[flip]
    weights = np.stack([1 - r1 - r2, r1, r2], 1)
    point = np.einsum("nk,nkd->nd", weights, positions[indices[face]])
    point_uv = np.einsum("nk,nkd->nd", weights, uv_px[indices[face]])
    glow = sample_field(highlight, point_uv[:, 0], point_uv[:, 1])
    keep = rng.random(len(glow)) < glow / max(glow.max(), 1e-6)
    point, point_uv = point[keep][:count], point_uv[keep][:count]
    normal = np.einsum("nk,nkd->nd", weights[keep][:count], normals[indices[face[keep][:count]]])
    point += normal * 0.015
    rim_color = np.stack([sample_field(gas[..., k], point_uv[:, 0], point_uv[:, 1]) for k in range(3)], 1)
    rim_value = rim_color.max(axis=1)
    add_cloud(glb, "ionization-fronts", point, rim_color / np.maximum(rim_value, 1e-4)[:, None],
              0.9 * sample_field(highlight, point_uv[:, 0], point_uv[:, 1]) / np.maximum(rim_value, 1e-4) * 0.5 + 0.04,
              PER_PIXEL["rims"], 3.0)

    # Gas outside the pillars, feathered at the photo's edges and given depth
    # through a soft slab around them.
    feather = elliptical_feather((height, width), 0.55, bottom=0.8)
    target = gas * (feather * (1 - inside))[..., None]
    depth_field = smooth_noise(gas.shape[:2], 70, rng)
    for name, share, count, per_pixel, max_px, spread in (("ionized-gas-glow", 0.7, 0, PER_PIXEL["gas"], 40, 0.55),
                                                          ("ionized-gas", 0.3, 20000, PER_PIXEL["fine"], 14, 0.3)):
        q = per_pixel * PILLAR_LY / (width * ly_per_px)
        if count:
            x_px, y_px, color, alpha = calibrated_samples(target, count, rng, q, gamma=0.6)
        else:
            x_px, y_px, color, alpha = grid_samples(target, 13, rng, q)
        x, y = to_model(x_px, y_px)
        z = -0.3 + 0.9 * sample_field(depth_field, x_px, y_px) + rng.normal(0, spread, len(x))
        add_cloud(glb, name, np.column_stack([x, y, z]), color, alpha * share, per_pixel, max_px)

    # Stars: the few brightest get bigger sprites.
    x, y = to_model(stars[:, 0], stars[:, 1])
    z = rng.normal(-0.3, 1.1, len(x))
    color = stars[:, 2:5] / np.maximum(stars[:, 2:5].max(axis=1, keepdims=True), 1e-3)
    peak = stars[:, 5]
    bright = np.arange(len(x)) < 25
    add_cloud(glb, "bright-stars", np.column_stack([x, y, z])[bright], color[bright],
              np.clip(peak[bright] * 1.6, 0.4, 1), PER_PIXEL["bright"], 7)
    add_cloud(glb, "stars", np.column_stack([x, y, z])[~bright], color[~bright],
              np.clip(peak[~bright] * 2.2, 0.15, 1), PER_PIXEL["stars"], 2.6)
    size = glb.write(output)
    return {"bytes": size, "vertices": len(positions), "triangles": len(indices), "stars": len(stars),
            "visible_vertex_fraction": float(visible.mean()), "ly_per_px": ly_per_px,
            "image_span_ly": [width * ly_per_px, height * ly_per_px], "depth_span_ly": float(np.ptp(positions[:, 2]))}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mesh")
    parser.add_argument("image")
    parser.add_argument("output")
    args = parser.parse_args()
    print(json.dumps(build(args.mesh, args.image, args.output)))


if __name__ == "__main__":
    main()
