#!/usr/bin/env python3
"""CPU geometry review of the actual GLB when Chromium cannot start.

This is NOT a production-renderer screenshot or a substitute for model_lab.
Requires numpy and Pillow. No generated or reconstructed illustration is used.
Usage: ./venv/bin/python handoff/flybrain/render_review.py MODEL.glb OUT_DIR
"""
import json
import math
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def read(path):
    payload = Path(path).read_bytes()
    size = struct.unpack_from("<I", payload, 12)[0]
    doc = json.loads(payload[20:20 + size])
    binary = payload[28 + size:]
    types = {5121: "u1", 5122: "<i2", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
    def accessor(index):
        a = doc["accessors"][index]
        v = doc["bufferViews"][a["bufferView"]]
        dt = np.dtype(types[a["componentType"]])
        width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[a["type"]]
        data = np.ndarray((a["count"], width), dtype=dt, buffer=binary,
                          offset=v.get("byteOffset", 0) + a.get("byteOffset", 0),
                          strides=(v.get("byteStride", dt.itemsize * width), dt.itemsize)).copy()
        if a.get("normalized"):
            data = data.astype(float) / np.iinfo(dt).max
        return data
    primitives = []
    for node in doc["nodes"]:
        if "mesh" not in node:
            continue
        for p in doc["meshes"][node["mesh"]]["primitives"]:
            xyz = accessor(p["attributes"]["POSITION"])
            xyz = xyz * node.get("scale", [1, 1, 1]) + node.get("translation", [0, 0, 0])
            indices = accessor(p["indices"]).ravel().astype(int)
            colours = accessor(p["attributes"]["COLOR_0"]) if "COLOR_0" in p["attributes"] else None
            material = doc["materials"][p["material"]]
            primitives.append((xyz, indices.reshape(-1, 3 if p["mode"] == 4 else 2), colours, material))
    return primitives


def render(path, out, background="dark"):
    primitives = read(path)
    width, height, aa = 1200, 750, 2
    output = Path(out)
    output.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24 * aa)
    except OSError:
        font = ImageFont.load_default(size=24 * aa)
    for name, (pitch, yaw) in {"rest": (10, -12), "front": (0, 0), "side": (0, 90), "top": (90, 0)}.items():
        x, y = np.deg2rad([pitch, yaw])
        rx = np.array([[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]])
        ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
        transformed = [p[0] @ (rx @ ry).T for p in primitives]
        points = [p[:, :2] * 1500 / (1500 - p[:, 2:3]) for p in transformed]
        all_points = np.concatenate(points)
        lo, hi = all_points.min(0), all_points.max(0)
        zoom = min((width - 160) / (hi[0] - lo[0]), (height - 190) / (hi[1] - lo[1]))
        center = (lo + hi) / 2
        pixels = [(p - center) * [zoom * aa, -zoom * aa] + [width * aa / 2, height * aa / 2] for p in points]
        im = Image.new("RGB", (width * aa, height * aa),
                       (7, 12, 21) if background == "dark" else (240, 244, 248))
        draw = ImageDraw.Draw(im, "RGBA")
        for (xyz, edges, colours, material), projected, rotated in zip(primitives, pixels, transformed):
            base = np.array(material["pbrMetallicRoughness"]["baseColorFactor"])
            if edges.shape[1] == 3:
                for face in edges[np.argsort(rotated[edges, 2].mean(1))]:
                    draw.polygon([tuple(point) for point in projected[face]], fill=(41, 69, 107, 10))
            else:
                if colours is None:
                    colours = np.tile(base, (len(xyz), 1))
                for edge in edges[np.argsort(rotated[edges, 2].mean(1))]:
                    colour = colours[edge].mean(0)
                    rgb = np.where(colour[:3] <= .0031308, colour[:3] * 12.92,
                                   1.055 * colour[:3]**(1 / 2.4) - .055)
                    fill = tuple(np.round(np.r_[rgb, colour[3]] * 255).clip(0, 255).astype(int))
                    draw.line([tuple(point) for point in projected[edge]], fill=fill, width=aa)
        draw.text((40 * aa, 25 * aa), f"FlyWire v783 · 2,200 sampled neurons · {name}", font=font,
                  fill=(220, 230, 244, 255) if background == "dark" else (25, 39, 64, 255))
        draw.text((40 * aa, (height - 50) * aa), "Software geometry review · production browser blocked by sandbox", font=font, fill=(142, 160, 186, 255))
        im.resize((width, height), Image.Resampling.LANCZOS).save(output / f"flybrain-{name}.png")
        print(output / f"flybrain-{name}.png")


if __name__ == "__main__":
    render(*sys.argv[1:])
