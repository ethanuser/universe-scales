#!/usr/bin/env python3
"""Build the Milky Way model: NASA/JPL-Caltech's face-on concept as a glowing
disk, plus 3D stars sampled from it with realistic disk and bulge thickness.

    ./venv/bin/python scripts/build_milky_way_model.py PIA10748.jpg OUT.glb

Source image: PIA10748, "Our Milky Way Gets a Makeover", NASA/JPL-Caltech
(R. Hurt, SSC), 5600 x 5600 px. Its annotated version places the Sun 1,067 px
(at this resolution) below the Galactic Center; the model scales the image so
the Sun is 8.18 kpc from the center (GRAVITY Collaboration 2019). Units: kpc.
The disk lies in the x-z plane with the Sun on +z, galactic north +y.
"""
import argparse
import json
import math

import numpy as np
from PIL import Image, ImageFilter

from volume_glb import VolumeGLB, sample_by_brightness

SUN_KPC = 8.18
SUN_RADIUS_KPC = 695_700_000 / 3.0856775814913673e19
CENTER_PX = (2800.0, 2780.0)       # bulge peak in the 5600 px image (blurred maximum)
SUN_PX = (2800.0, 3867.5)          # from the annotated figure, scaled
CROP_PX = 2450                     # disk radius kept (about 18.8 kpc)


def build(source, output, stars=26000, seed=0x3a11):
    image = Image.open(source).convert("RGB")
    if image.size != (5600, 5600):
        raise ValueError(f"Expected the 5600 px PIA10748 image, got {image.size}")
    kpc_per_px = SUN_KPC / math.dist(CENTER_PX, SUN_PX)
    cx, cy = CENTER_PX
    crop = image.crop((int(cx - CROP_PX), int(cy - CROP_PX), int(cx + CROP_PX), int(cy + CROP_PX)))
    radius_kpc = CROP_PX * kpc_per_px

    # Texture: fade the outer 12% of the crop so the disk has no hard edge.
    side = 2048
    texture = crop.resize((side, side), Image.LANCZOS)
    grid = (np.indices((side, side)).transpose(1, 2, 0) + 0.5) / side * 2 - 1
    r = np.hypot(grid[..., 0], grid[..., 1])
    fade = np.clip((1 - r) / 0.12, 0, 1) ** 1.5
    pixels = np.asarray(texture, np.float32) * fade[..., None]
    texture = Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))

    glb = VolumeGLB("Universe Scales Milky Way builder")
    disk_material = glb.unlit("milky-way-disk", texture=glb.jpeg_texture(texture, 84))
    rings, segments = 32, 128
    positions, uvs, indices = [[0, 0, 0]], [[0.5, 0.5]], []
    for ring in range(1, rings + 1):
        rr = radius_kpc * ring / rings
        for segment in range(segments):
            angle = 2 * math.pi * segment / segments
            x, z = rr * math.cos(angle), rr * math.sin(angle)
            positions.append([x, 0, z])
            uvs.append([0.5 + x / (2 * radius_kpc), 0.5 + z / (2 * radius_kpc)])
    for segment in range(segments):
        indices += [0, 1 + segment, 1 + (segment + 1) % segments]
    for ring in range(1, rings):
        a0, b0 = 1 + (ring - 1) * segments, 1 + ring * segments
        for segment in range(segments):
            n = (segment + 1) % segments
            indices += [a0 + segment, b0 + segment, b0 + n, a0 + segment, b0 + n, a0 + n]
    disk = glb.primitive(positions, indices, disk_material, normals=[[0, 1, 0]] * len(positions), uvs=uvs)
    glb.node("milky-way-disk", [disk], extras={"additive": True})

    # Stars and glowing gas knots, sampled from the image, given 3D heights:
    # a thin disk (exponential scale height ~0.3 kpc) thickening into the bulge/bar.
    rng = np.random.default_rng(seed)
    small = crop.resize((1024, 1024), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    u, v, colors, luminance = sample_by_brightness(small, stars, rng, gamma=1.7, floor=0.06)
    x = (u * 2 - 1) * radius_kpc
    z = (v * 2 - 1) * radius_kpc
    radius = np.hypot(x, z)
    keep = radius < radius_kpc * 0.97
    x, z, radius, colors, luminance = x[keep], z[keep], radius[keep], colors[keep], luminance[keep]
    scale_height = 0.28 + 0.9 * np.exp(-radius / 1.6)
    y = rng.laplace(0, scale_height / 1.4)
    brightest = colors / np.maximum(colors.max(axis=1, keepdims=True), 1e-3)
    alpha = np.clip(0.25 + 0.75 * luminance, 0.2, 1.0)[:, None]
    star_material = glb.unlit("milky-way-stars")
    stars_primitive = glb.points(np.stack([x, y, z], 1), np.concatenate([brightest, alpha], 1), star_material)
    glb.node("milky-way-stars", [stars_primitive], extras={
        "softPoints": True, "additive": True, "pointSize": {"max": 2.4, "perPixel": 1 / 330}})

    glb.node("Sun", translation=[0, 0, SUN_KPC], scale=SUN_RADIUS_KPC, extras={
        "label": "Sun (you are here)", "outline": True, "sphere": True, "markerRadius": 3, "markerPadding": 0.5})
    glb.node("galactic-center-label", translation=[0, 1.4, 0], extras={"label": "Galactic center: Sagittarius A*"})
    size = glb.write(output)
    return {"bytes": size, "stars": int(len(x)), "disk_radius_kpc": radius_kpc, "kpc_per_px": kpc_per_px}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source")
    parser.add_argument("output")
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output)))


if __name__ == "__main__":
    main()
