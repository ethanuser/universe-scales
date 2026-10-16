#!/usr/bin/env python3
"""Build rotatable, glowing 3D models of emission nebulae from their photographs.

    ./venv/bin/python scripts/build_nebula_volumes.py orion --hubble heic0601a.jpg --wide noao-m42steinberg.jpg OUT.glb
    ./venv/bin/python scripts/build_nebula_volumes.py carina --image noao0136a.jpg OUT.glb
    ./venv/bin/python scripts/build_nebula_volumes.py tarantula --image eso0650a.jpg OUT.glb

Each photo keeps its observed sky-plane positions and colors (see nebula_volume.py
for the calibration that makes the front view reproduce the photo). What a photo
cannot give is depth. Orion's depth follows its published structure: the bright
Huygens region is the ionization front on the face of the Orion Molecular Cloud,
about 0.2 pc behind the Trapezium and curving toward us farther out (O'Dell et al.
2009), inside a wind-blown bubble about 4 pc across whose near half-shell is the
Veil (Pabst et al. 2019). Carina and Tarantula have no comparable published 3D
maps, so their gas is wrapped onto irregular shells around their central clusters,
the generic geometry of wind- and radiation-blown HII regions. That depth is
illustrative and the registry says so. Units are light-years; observer at +z.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nebula_volume import (add_cloud, calibrated_samples, decompose, elliptical_feather,  # noqa: E402
                           grid_samples, load_rgb, sample_field, smooth_noise, split_stars)
from volume_glb import VolumeGLB  # noqa: E402

ARCSEC = math.pi / 180 / 3600


def ly_per_arcsec(distance_ly):
    return distance_ly * ARCSEC


# ---------------------------------------------------------------- Orion canvas

ORION_DISTANCE_LY = 1344          # about 412 pc
TRAPEZIUM = (83.81858, -5.38967)  # theta1 Ori C, degrees (J2000)
HUBBLE = {"center": (83.79054, -5.41398), "field_arcmin": 30.03, "north_left_deg": 0.0}
# NOIRLab lists Dec -4:41:52 for the wide image's center, but the image itself puts the
# Trapezium near its middle (M43 and NGC 1977 lie north, i.e. left, as "north 79 degrees
# left of vertical" requires). So the wide image is pinned at the Trapezium's pixel and the
# shift refined by cross-correlation with Hubble.
WIDE = {"anchor_px": (833.0, 512.0), "field_arcmin": (130.89, 73.22), "north_left_deg": 79.0}
M43 = (83.87917, -5.26750)        # NGC 1982 center, for its label


def sky_offset_arcsec(position, origin):
    """(east, north) offset in arcseconds of position from origin (small angles)."""
    d_ra = (position[0] - origin[0]) * math.cos(math.radians(origin[1]))
    return d_ra * 3600, (position[1] - origin[1]) * 3600


def warp_to_canvas(image, center, scale, north_left_deg, size, pixel, anchor_px=None, shift=(0.0, 0.0)):
    """Resample a north-rotated image onto a north-up, east-left canvas centered on
    the Trapezium. scale and pixel are arcsec per source / canvas pixel. With
    anchor_px, that source pixel lands on the canvas center (plus shift)."""
    if anchor_px is None:
        east, north = sky_offset_arcsec(center, TRAPEZIUM)
        cx, cy = size / 2 - east / pixel, size / 2 - north / pixel
        uc, vc = image.width / 2, image.height / 2
    else:
        cx, cy = size / 2 + shift[0], size / 2 + shift[1]
        uc, vc = anchor_px
    theta = math.radians(north_left_deg)
    k = pixel / scale
    cos, sin = math.cos(theta) * k, math.sin(theta) * k
    # source = R(theta) * (canvas - canvas_center_of_image) + source_center
    coefficients = (cos, sin, uc - cos * cx - sin * cy, -sin, cos, vc + sin * cx - cos * cy)
    warped = image.transform((size, size), Image.AFFINE, coefficients, Image.BICUBIC)
    mask = Image.new("L", image.size, 255).transform((size, size), Image.AFFINE, coefficients, Image.BILINEAR)
    return np.asarray(warped, np.float32) / 255, np.asarray(mask, np.float32) / 255


def orion_canvas(hubble_path, wide_path, size=2400, span_arcmin=64):
    from scipy import ndimage
    Image.MAX_IMAGE_PIXELS = None
    pixel = span_arcmin * 60 / size
    hubble = Image.open(hubble_path).convert("RGB")
    wide = Image.open(wide_path).convert("RGB")
    h, h_mask = warp_to_canvas(hubble, HUBBLE["center"], HUBBLE["field_arcmin"] * 60 / hubble.width,
                               HUBBLE["north_left_deg"], size, pixel)
    wide_scale = WIDE["field_arcmin"][0] * 60 / wide.width
    w, w_mask = warp_to_canvas(wide, None, wide_scale, WIDE["north_left_deg"], size, pixel, WIDE["anchor_px"])
    # Refine the wide image's shift: cross-correlate high-passed luminance where both exist.
    def highpass(image):
        lum = image.mean(axis=2)
        return ndimage.gaussian_filter(lum, 3) - ndimage.gaussian_filter(lum, 25)
    region = (h_mask > 0.99) & (w_mask > 0.99)
    target = highpass(h) * region
    best = (-np.inf, (0.0, 0.0))
    for dx in range(-24, 25, 3):
        for dy in range(-24, 25, 3):
            moved = np.roll(highpass(w), (dy, dx), axis=(0, 1))
            score = (moved * target).sum()
            if score > best[0]:
                best = (score, (float(dx), float(dy)))
    shift = best[1]
    w, w_mask = warp_to_canvas(wide, None, wide_scale, WIDE["north_left_deg"], size, pixel, WIDE["anchor_px"], shift)
    # Match the ground-based colors to Hubble's where both exist (blurred, unsaturated).
    hb, wb = ndimage.gaussian_filter(h, (6, 6, 0)), ndimage.gaussian_filter(w, (6, 6, 0))
    both = (h_mask > 0.99) & (w_mask > 0.99) & (hb.max(axis=2) < 0.9) & (wb.max(axis=2) > 0.02)
    gain = (hb[both] * wb[both]).sum(axis=0) / (wb[both] ** 2).sum(axis=0)
    # Hubble wins inside its square, blending over its outer 10%.
    inner = ndimage.distance_transform_edt(h_mask > 0.99)
    weight = np.clip(inner / (0.1 * HUBBLE["field_arcmin"] * 60 / pixel), 0, 1)[..., None]
    canvas = weight * h + (1 - weight) * np.clip(w * gain, 0, 1) * w_mask[..., None]
    return canvas, pixel, {"color_gain_wide_to_hubble": gain.round(4).tolist(), "wide_shift_px": shift}


# --------------------------------------------------------------- depth models

def orion_depth(x, y, kind, rng, fields):
    """Blister wall behind the Trapezium plus the near half of the Veil bubble."""
    rho = np.hypot(x, y)
    wall = -0.65 + 2.6 * (1 - np.exp(-rho ** 2 / (2 * 4.5 ** 2)))
    bubble_r = 6.5
    rho_b = np.hypot(x - 0.3, y + 1.2)
    dome = np.sqrt(np.clip(bubble_r ** 2 - rho_b ** 2, 0, None))
    on_shell = (rng.random(len(x)) < 0.12 + 0.3 * np.clip((rho - 1.5) / 4, 0, 1)) & (rho_b < bubble_r)
    jitter = {"glow": 0.8, "detail": 0.35, "stars": 0.0}[kind]
    z = np.where(on_shell, wall + (dome - wall) * rng.uniform(0.75, 1.0, len(x)), wall)
    z += 0.5 * fields["warp"] + rng.normal(0, jitter, len(x)) if jitter else 0
    if kind == "stars":  # the Orion Nebula Cluster sits in front of the wall
        z = wall + np.abs(rng.normal(0, 1.4, len(x)))
    return z


def shell_depth(radius, roughness=0.3, thickness=0.06):
    """Gas on irregular shells around the origin: front or back is chosen by a smooth
    random field, so whole filaments stay together."""
    def depth(x, y, kind, rng, fields):
        rho = np.hypot(x, y)
        r = radius * (1 + roughness * fields["radius"])
        r = np.maximum(r, rho * 1.08)
        cap = np.sqrt(np.clip(r ** 2 - rho ** 2, 0, None))
        if kind == "stars":
            return rng.uniform(-1, 1, len(x)) * radius * 1.1
        # A filled, lumpy volume: coherent front/back structure plus scatter.
        scatter = {"glow": 0.45, "detail": 0.3}[kind]
        side = np.clip(0.75 * fields["side"] + rng.normal(0, scatter, len(x)), -1, 1)
        return side * cap + rng.normal(0, thickness * radius, len(x))
    return depth


def image_ellipse(image, center_px, ly_per_px, percentile=60, filled=False):
    """Brightness-weighted second moments of the brighter pixels around center_px:
    (angle radians, semi-axis a, semi-axis b) in ly, a >= b. A thin ring has variance
    a^2/2 along an axis; a filled ellipse has a^2/4."""
    lum = image.max(axis=2)
    ys, xs = np.nonzero(lum > np.percentile(lum, percentile))
    w = lum[ys, xs]
    dx, dy = (xs - center_px[0]) * ly_per_px, (center_px[1] - ys) * ly_per_px
    cov = np.cov(np.stack([dx, dy]), aweights=w)
    values, vectors = np.linalg.eigh(cov)
    a, b = np.sqrt((4 if filled else 2) * values[::-1])
    return math.atan2(vectors[1, 1], vectors[0, 1]), a, b


def crab_depth(angle, a, b):
    """Prolate shell (long axis in the sky plane, line-of-sight semi-axis b) for the
    filaments; the smooth synchrotron glow fills the interior."""
    def depth(x, y, kind, rng, fields):
        c, s = math.cos(angle), math.sin(angle)
        u, v = (x * c + y * s) / a, (-x * s + y * c) / b
        # Filaments beyond the fitted ellipse sit on a slightly larger one, not at z = 0.
        q = np.hypot(u, v) / np.maximum(1, np.hypot(u, v) * 1.12)
        cap = b * np.sqrt(np.clip(1 - q * q, 0, None))
        if kind == "stars":
            return rng.uniform(-1, 1, len(x)) * a
        if kind == "glow":
            return cap * rng.uniform(-0.85, 0.85, len(x))
        side = np.sign(np.clip(0.8 * fields["side"] + rng.normal(0, 0.45, len(x)), -1, 1) + 1e-9)
        on_shell = side * cap * rng.uniform(0.75, 1.05, len(x))
        # Outskirts seen beyond the fitted ellipse spread through the depth, not one sheet.
        z = np.where(np.hypot(u, v) > 1, cap * rng.uniform(-1, 1, len(x)), on_shell)
        return z + rng.normal(0, 0.04 * b, len(x))
    return depth


def ring_depth(angle, a, b):
    """The Ring as a barrel seen nearly end-on (O'Dell et al. 2013): its waist makes the
    bright ring, its end caps the faint center, and a larger faint shell the halo."""
    length = 1.6 * a
    def depth(x, y, kind, rng, fields):
        c, s = math.cos(angle), math.sin(angle)
        r = np.hypot((x * c + y * s) / a, (-x * s + y * c) / b)
        if kind == "stars":
            return rng.uniform(-1, 1, len(x)) * 2 * a
        side = np.where(fields["side"] + rng.normal(0, 0.5, len(x)) > 0, 1, -1)
        caps = side * length * np.sqrt(np.clip(1 - r * r, 0, None)) * rng.uniform(0.85, 1.0, len(x))
        waist = rng.normal(0, 0.22 * length, len(x)) * np.exp(-((r - 1) / 0.25) ** 2)
        rho = np.hypot(x, y)
        halo = rng.uniform(-1, 1, len(x)) * np.sqrt(np.maximum(np.clip((1.45 * a) ** 2 - rho ** 2, 0, None), (0.5 * rho) ** 2))
        inner, outer = np.clip((0.85 - r) / 0.2, 0, 1), np.clip((r - 1.15) / 0.2, 0, 1)
        return inner * caps + outer * halo + (1 - inner) * (1 - outer) * waist
    return depth


# --------------------------------------------------------------------- build

def build_volume(canvas, ly_per_px, center_px, depth, output, labels, reference_ly, counts, seed, feather_start=0.6):
    rng = np.random.default_rng(seed)
    height, width = canvas.shape[:2]
    gas, stars = split_stars(canvas, radius=3, threshold=0.07, limit=counts["stars"])
    gas = gas * elliptical_feather((height, width), feather_start)[..., None]
    star_feather = sample_field(elliptical_feather((height, width), 0.75), stars[:, 0], stars[:, 1])
    stars = stars[star_feather > 0.05]
    fields = {name: smooth_noise((height, width), sigma, rng)
              for name, sigma in (("warp", width / 30), ("radius", width / 14), ("side", width / 22))}

    def model_xy(x_px, y_px):
        return (x_px - center_px[0]) * ly_per_px, (center_px[1] - y_px) * ly_per_px

    def field_values(x_px, y_px):
        return {name: sample_field(field, x_px, y_px) for name, field in fields.items()}

    glb = VolumeGLB("Universe Scales nebula volume builder")
    span = width * ly_per_px
    low, high = decompose(gas, radius=max(3, round(width / 160)), sigma=width / 70)
    layers = (("gas-glow", low, None, 1 / 22, 44), ("gas-filaments", high, counts["detail"], 1 / 180, 7))
    sprites = {}
    for name, target, count, per_pixel, max_px in layers:
        q = per_pixel * reference_ly / span
        if count:
            x_px, y_px, color, alpha = calibrated_samples(target, count, rng, q, gamma=0.9)
        else:
            x_px, y_px, color, alpha = grid_samples(target, max(4, round(width / 120)), rng, q)
        x, y = model_xy(x_px, y_px)
        kind = "glow" if count is None else "detail"
        z = depth(x, y, kind, rng, field_values(x_px, y_px))
        add_cloud(glb, name, np.column_stack([x, y, z]), color, alpha, per_pixel, max_px,
                  alpha_floor=0.012 if count is None else 0.03)
        sprites[name] = len(x)

    x, y = model_xy(stars[:, 0], stars[:, 1])
    z = depth(x, y, "stars", rng, field_values(stars[:, 0], stars[:, 1]))
    color = stars[:, 2:5] / np.maximum(stars[:, 2:5].max(axis=1, keepdims=True), 1e-3)
    peak = stars[:, 5] * star_feather[star_feather > 0.05]
    bright = np.arange(len(x)) < 30
    positions = np.column_stack([x, y, z])
    add_cloud(glb, "bright-stars", positions[bright], color[bright], np.clip(peak[bright] * 1.5, 0.35, 1), 1 / 140, 6)
    add_cloud(glb, "stars", positions[~bright], color[~bright], np.clip(peak[~bright] * 2, 0.12, 1), 1 / 420, 2.4)
    for text, position in labels:
        glb.node(f"label-{text}", translation=position, extras={"label": text})
    size = glb.write(output)
    return {"bytes": size, "sprites": sprites, "stars": int(len(x)), "span_ly": [width * ly_per_px, height * ly_per_px]}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("nebula", choices=["orion", "carina", "tarantula", "crab", "ring"])
    parser.add_argument("output")
    parser.add_argument("--image")
    parser.add_argument("--hubble")
    parser.add_argument("--wide")
    args = parser.parse_args()

    if args.nebula == "orion":
        canvas, pixel, extra = orion_canvas(args.hubble, args.wide)
        ly_px = ly_per_arcsec(ORION_DISTANCE_LY) * pixel
        center = (canvas.shape[1] / 2, canvas.shape[0] / 2)
        east, north = sky_offset_arcsec(M43, TRAPEZIUM)
        m43 = (-east * ly_per_arcsec(ORION_DISTANCE_LY), north * ly_per_arcsec(ORION_DISTANCE_LY), 0.0)
        result = build_volume(canvas, ly_px, center, orion_depth, args.output,
                              [("Trapezium", (0, 0, 0.3)), ("M43", m43)], 25.368,
                              {"detail": 70000, "stars": 2600}, 0x0410)
        result.update(extra)
    elif args.nebula == "carina":
        # NOIRLab noao0136a: 79.95 x 132.38 arcmin, north 1 degree left of vertical,
        # at about 7,500 ly (NASA). Center the shells on the brightest region (Trumpler 16).
        canvas = load_rgb(args.image, width=1300)
        ly_px = ly_per_arcsec(7500) * 79.95 * 60 / canvas.shape[1]
        from scipy import ndimage
        glow = ndimage.gaussian_filter(canvas.max(axis=2), 25)
        cy, cx = np.unravel_index(np.argmax(glow), glow.shape)
        result = build_volume(canvas, ly_px, (cx + 0.5, cy + 0.5), shell_depth(80), args.output,
                              [], 300.0, {"detail": 70000, "stars": 3000}, 0xCA21, feather_start=0.62)
        result["center_px"] = [int(cx), int(cy)]
    elif args.nebula == "crab":
        # ESA/Hubble heic0515a: 6.41 arcmin square, north up, at about 6,500 ly.
        canvas = load_rgb(args.image, width=1800)
        ly_px = ly_per_arcsec(6500) * 6.41 * 60 / canvas.shape[1]
        center = (canvas.shape[1] / 2, canvas.shape[0] / 2)
        angle, a, b = image_ellipse(canvas, center, ly_px, 55, filled=True)
        result = build_volume(canvas, ly_px, center, crab_depth(angle, a, b), args.output, [], 11.0,
                              {"detail": 70000, "stars": 400}, 0xC2AB, feather_start=0.8)
        result["shell_axes_ly"] = [round(a, 2), round(b, 2), round(math.degrees(angle), 1)]
    elif args.nebula == "ring":
        # ESA/Webb weic2320b (NIRCam): 2.14 x 2.17 arcmin at about 2,567 ly (Gaia, 787 pc).
        # Keep the central 78% (about 1.25 ly) so the faint halo does not swamp the 1 ly ring.
        Image.MAX_IMAGE_PIXELS = None
        width, height = Image.open(args.image).size
        keep = 0.78
        box = (width * (1 - keep) / 2, height * (1 - keep) / 2, width * (1 + keep) / 2, height * (1 + keep) / 2)
        canvas = load_rgb(args.image, width=1600, crop=box)
        ly_px = ly_per_arcsec(2567) * 2.14 * 60 * keep / canvas.shape[1]
        center = (canvas.shape[1] / 2, canvas.shape[0] / 2)
        angle, a, b = image_ellipse(canvas, center, ly_px, 75)
        result = build_volume(canvas, ly_px, center, ring_depth(angle, a, b), args.output, [], 1.0,
                              {"detail": 70000, "stars": 300}, 0x2157, feather_start=0.7)
        result["ring_axes_ly"] = [round(a, 3), round(b, 3), round(math.degrees(angle), 1)]
    else:
        # ESO eso0650a: 62.40 x 62.31 arcmin at 170,000 ly. Crop 1.15x the 951-ly
        # aperture around R136, as in the earlier model.
        Image.MAX_IMAGE_PIXELS = None
        width, height = Image.open(args.image).size
        px_per_arcmin = width / 62.40
        ly_per_arcmin = ly_per_arcsec(170_000) * 60
        half = 1.15 * 951.3 / ly_per_arcmin * px_per_arcmin / 2
        cx, cy = 0.435 * width, 0.245 * height
        canvas = load_rgb(args.image, width=1600, crop=(cx - half, cy - half, cx + half, cy + half))
        ly_px = 2 * half / px_per_arcmin * ly_per_arcmin / canvas.shape[1]
        center = (canvas.shape[1] / 2, canvas.shape[0] / 2)
        result = build_volume(canvas, ly_px, center, shell_depth(320), args.output,
                              [("R136", (0, 0, 0))], 951.3, {"detail": 70000, "stars": 2500}, 0x7A2A, feather_start=0.55)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
