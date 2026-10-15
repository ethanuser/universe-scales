#!/usr/bin/env python3
"""Turn a nebula photograph into glowing 3D point layers.

The photo is split into gas (stars removed) and point-like stars. Gas becomes
two additive sprite layers: a few thousand large, faint "glow" sprites and tens
of thousands of small "detail" sprites. Each sprite keeps its sky-plane position
and color, and its alpha is calibrated so that, seen from the front, the summed
sprites reproduce the photo's brightness. Depth comes from a caller-supplied
function, so the same photo can be wrapped onto a published geometry (a bubble,
a blister) or an illustrative one.

Calibration: a soft sprite of s px adds about KERNEL * s^2 * alpha of its color.
The explorer sizes sprites as drawnPixels * perPixel, where drawnPixels is the
on-screen size of the model's reference_size; relative to the image width that is
q = perPixel * reference / image_width_units. With N sprites drawn with per-pixel
probability p, the expected front-view value is KERNEL * N * p * (W q)^2 * alpha,
for an image W pixels wide. Solving for alpha gives the target pixel value. The
canvas blends 8-bit display values, so alpha also has a floor below which faint
sprites would round away.
"""
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

KERNEL = 0.24          # integral of model-points.js softPointSprite over a unit sprite
ALPHA_FLOOR = 0.035    # about 2/255 per channel at a sprite's center once colors are normalized


def load_rgb(path, width=None, crop=None):
    """Display-space RGB in 0..1 (float32), optionally cropped and resized to `width`."""
    Image.MAX_IMAGE_PIXELS = None
    image = Image.open(path).convert("RGB")
    if crop:
        image = image.crop(tuple(int(round(v)) for v in crop))
    if width and image.width != width:
        image = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
    return np.asarray(image, np.float32) / 255


def srgb_to_linear(values):
    values = np.clip(values, 0, 1)
    return np.where(values <= 0.04045, values / 12.92, ((values + 0.055) / 1.055) ** 2.4)


def split_stars(rgb, radius=3, threshold=0.06, limit=4000):
    """Return (gas, stars). Gas is the image with point sources removed (grey opening,
    then a light blur to hide the seams). Stars are local maxima of the residual:
    rows of (x_px, y_px, r, g, b, peak) with colors from the original image."""
    footprint = np.hypot(*np.mgrid[-radius:radius + 1, -radius:radius + 1]) <= radius
    gas = np.stack([ndimage.grey_opening(rgb[..., c], footprint=footprint) for c in range(3)], -1)
    gas = ndimage.gaussian_filter(gas, (0.8, 0.8, 0))
    residual = np.clip(rgb - gas, 0, None).max(axis=2)
    peaks = (residual == ndimage.maximum_filter(residual, size=2 * radius + 1)) & (residual > threshold)
    ys, xs = np.nonzero(peaks)
    order = np.argsort(residual[ys, xs])[::-1][:limit]
    ys, xs = ys[order], xs[order]
    colors = rgb[ys, xs]
    return gas, np.column_stack([xs + 0.5, ys + 0.5, colors, residual[ys, xs]])


def calibrated_samples(target, count, rng, q, gamma=0.7, mask=None):
    """Sample `count` sprites from a display-space RGB target. Returns pixel positions
    (x, y, jittered), display colors normalized to max channel 1, and alphas."""
    value = target.max(axis=2)
    weight = np.clip(value, 0, None) ** gamma
    if mask is not None:
        weight = weight * mask
    total = weight.sum()
    probability = weight.ravel() / total
    chosen = rng.choice(probability.size, size=count, p=probability)
    height, width = value.shape
    ys, xs = np.divmod(chosen, width)
    x = xs + rng.random(count)
    y = ys + rng.random(count)
    pixel_value = value.ravel()[chosen]
    color = target.reshape(-1, 3)[chosen] / np.maximum(pixel_value, 1e-4)[:, None]
    alpha = pixel_value / (KERNEL * count * probability[chosen] * (width * q) ** 2)
    return x, y, color, alpha


def smooth_noise(shape, sigma, rng):
    """Gaussian random field with unit standard deviation and correlation length ~sigma px."""
    field = ndimage.gaussian_filter(rng.standard_normal(shape), sigma, mode="wrap")
    return field / field.std()


def sample_field(field, x, y):
    """Bilinear lookup of a 2D field at pixel positions."""
    return ndimage.map_coordinates(field, [y - 0.5, x - 0.5], order=1, mode="nearest")


def add_cloud(glb, name, positions, colors, alpha, per_pixel, max_px, alpha_floor=ALPHA_FLOOR, parent=None):
    """Write an additive soft-sprite cloud. Alphas above 1 are folded into color;
    sprites below the floor are dropped at random so the expected value is kept."""
    positions = np.asarray(positions, np.float32)
    colors = np.asarray(colors, np.float32)
    alpha = np.asarray(alpha, np.float32)
    over = np.maximum(alpha, 1)
    colors = np.clip(colors * over[:, None], 0, 1)
    alpha = np.clip(alpha, 0, 1)
    keep = alpha >= alpha_floor
    lucky = (~keep) & (np.random.default_rng(len(alpha)).random(len(alpha)) < alpha / alpha_floor)
    alpha = np.where(lucky, alpha_floor, alpha)
    keep |= lucky
    rgba = np.concatenate([srgb_to_linear(colors[keep]), alpha[keep, None]], 1)
    material = glb.unlit(f"{name}-sprites")
    primitive = glb.points(positions[keep], rgba, material)
    return glb.node(name, [primitive], parent=parent, extras={
        "softPoints": True, "additive": True, "pointSize": {"max": max_px, "perPixel": per_pixel}})
