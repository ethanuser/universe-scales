#!/usr/bin/env python3
"""GLB writer for glowing volumetric models (galaxies, nebulae, cosmic structure).

Extends geo_glb_common.GLB with point-cloud primitives and node extras that the
explorer reads (three.js copies glTF `extras` into `userData`):

  softPoints: true            round, soft-edged sprites instead of square pixels
  additive: true              additive blending: overlapping sprites glow, black is clear
  pointSize: {max, perPixel}  sprite size in px = drawn model size * perPixel, capped at max
  label / outline / sphere    upright SVG label and marker circle (see AGENTS.md)

Point colors are RGBA8 (normalized bytes), so alpha can vary per point.
"""
import io

import numpy as np
from PIL import Image

from geo_glb_common import GLB

UNLIT = "KHR_materials_unlit"


class VolumeGLB(GLB):
    def __init__(self, generator):
        super().__init__(generator)
        self.points_count = 0

    def unlit(self, name, texture=None, color=(1, 1, 1, 1), blend=True):
        index = self.material(name, color=color, texture=texture, blend=blend, double_sided=True)
        self.doc["materials"][index].setdefault("extensions", {})[UNLIT] = {}
        used = self.doc.setdefault("extensionsUsed", [])
        if UNLIT not in used:
            used.append(UNLIT)
        return index

    def jpeg_texture(self, image, quality=86):
        buffer = io.BytesIO()
        image.convert("RGB").save(buffer, "JPEG", quality=quality, optimize=True, progressive=False)
        return self.texture(buffer.getvalue(), "image/jpeg")

    def points(self, positions, colors, material):
        positions = np.asarray(positions, dtype=np.float32)
        colors = np.clip(np.asarray(colors, dtype=np.float32), 0, 1)
        if colors.shape[1] == 3:
            colors = np.concatenate((colors, np.ones((len(colors), 1), np.float32)), axis=1)
        attributes = {"POSITION": self._accessor(positions, 5126, "VEC3", 34962, True),
                      "COLOR_0": self._accessor(np.round(colors * 255).astype(np.uint8), 5121, "VEC4", 34962)}
        self.doc["accessors"][-1]["normalized"] = True
        self.points_count += len(positions)
        return {"attributes": attributes, "material": material, "mode": 0}

    def node(self, name, primitives=None, extras=None, translation=None, scale=None, parent=None):
        node = {"name": name}
        if primitives:
            self.doc["meshes"].append({"name": name, "primitives": primitives})
            node["mesh"] = len(self.doc["meshes"]) - 1
        if extras:
            node["extras"] = extras
        if translation is not None:
            node["translation"] = [float(v) for v in translation]
        if scale is not None:
            node["scale"] = [float(scale)] * 3 if np.isscalar(scale) else [float(v) for v in scale]
        self.doc["nodes"].append(node)
        index = len(self.doc["nodes"]) - 1
        if parent is None:
            self.doc["scenes"][0]["nodes"].append(index)
        else:
            self.doc["nodes"][parent].setdefault("children", []).append(index)
        return index


def sample_by_brightness(image, count, rng, gamma=1.4, floor=0.0):
    """Pixel coordinates (x, y in [0, 1)) drawn with probability ~ luminance^gamma,
    jittered within each pixel, and the RGB color at each sample (0..1)."""
    pixels = np.asarray(image.convert("RGB"), dtype=np.float32) / 255
    luminance = pixels @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    weights = np.clip(luminance - floor, 0, None) ** gamma
    flat = weights.ravel() / weights.sum()
    chosen = rng.choice(flat.size, size=count, p=flat)
    height, width = luminance.shape
    ys, xs = np.divmod(chosen, width)
    x = (xs + rng.random(count)) / width
    y = (ys + rng.random(count)) / height
    return x, y, pixels.reshape(-1, 3)[chosen], luminance.ravel()[chosen]
