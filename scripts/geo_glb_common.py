#!/usr/bin/env python3
"""Shared helpers for the geographic 3D-model builders (Manhattan, Panama Canal,
Amazon, ...): a small glTF 2.0 writer with vertex colors, RGBA vertex colors,
embedded JPEG/PNG textures and node extras (labels), plus polygon utilities.

No Draco/meshopt/KTX2/WebP: only plain glTF the site's GLTFLoader can read.
"""
import io
import json
import math
import struct
from pathlib import Path

import numpy as np

USER_AGENT = "universe-scales-model-builder/1.0 (educational; ethanpythonemail@gmail.com)"
EARTH_R = 6378137.0


def pack_glb(document, binary):
    document["buffers"] = [{"byteLength": len(binary)}]
    text = json.dumps(document, separators=(",", ":"), ensure_ascii=True).encode()
    text += b" " * (-len(text) % 4)
    binary = bytes(binary) + b"\0" * (-len(binary) % 4)
    return (struct.pack("<4sII", b"glTF", 2, 28 + len(text) + len(binary))
            + struct.pack("<I4s", len(text), b"JSON") + text
            + struct.pack("<I4s", len(binary), b"BIN\0") + binary)


class GLB:
    def __init__(self, generator="Universe Scales geographic model builder"):
        self.doc = {"asset": {"version": "2.0", "generator": generator}, "scene": 0,
                    "scenes": [{"nodes": []}], "nodes": [], "meshes": [], "materials": [],
                    "bufferViews": [], "accessors": [], "images": [], "textures": [], "samplers": []}
        self.bin = bytearray()
        self.triangles = 0

    def _view(self, payload, target=None):
        self.bin.extend(b"\0" * (-len(self.bin) % 4))
        view = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": len(payload)}
        if target:
            view["target"] = target
        self.bin.extend(payload)
        self.doc["bufferViews"].append(view)
        return len(self.doc["bufferViews"]) - 1

    def _accessor(self, array, component, kind, target, minmax=False):
        view = self._view(array.tobytes(), target)
        acc = {"bufferView": view, "componentType": component, "count": int(len(array)), "type": kind}
        if minmax:
            acc["min"] = array.min(axis=0).astype(float).tolist()
            acc["max"] = array.max(axis=0).astype(float).tolist()
        self.doc["accessors"].append(acc)
        return len(self.doc["accessors"]) - 1

    def material(self, name, color=(1, 1, 1, 1), rough=0.95, metal=0.0, blend=False,
                 texture=None, double_sided=True, emissive=None):
        m = {"name": name, "doubleSided": double_sided,
             "pbrMetallicRoughness": {"baseColorFactor": list(color), "metallicFactor": metal,
                                      "roughnessFactor": rough}}
        if texture is not None:
            m["pbrMetallicRoughness"]["baseColorTexture"] = {"index": texture}
        if blend:
            m["alphaMode"] = "BLEND"
        if emissive:
            m["emissiveFactor"] = list(emissive)
        self.doc["materials"].append(m)
        return len(self.doc["materials"]) - 1

    def texture(self, image_bytes, mime):
        view = self._view(image_bytes)
        self.doc["images"].append({"bufferView": view, "mimeType": mime})
        if not self.doc["samplers"]:
            self.doc["samplers"].append({"magFilter": 9729, "minFilter": 9987, "wrapS": 33071, "wrapT": 33071})
        self.doc["textures"].append({"source": len(self.doc["images"]) - 1, "sampler": 0})
        return len(self.doc["textures"]) - 1

    def primitive(self, positions, indices, material, normals=None, colors=None, uvs=None):
        positions = np.asarray(positions, dtype=np.float32)
        attrs = {"POSITION": self._accessor(positions, 5126, "VEC3", 34962, True)}
        if normals is not None:
            attrs["NORMAL"] = self._accessor(np.asarray(normals, dtype=np.float32), 5126, "VEC3", 34962)
        if colors is not None:
            colors = np.asarray(colors, dtype=np.float32)
            attrs["COLOR_0"] = self._accessor(colors, 5126, "VEC4" if colors.shape[1] == 4 else "VEC3", 34962)
        if uvs is not None:
            attrs["TEXCOORD_0"] = self._accessor(np.asarray(uvs, dtype=np.float32), 5126, "VEC2", 34962)
        indices = np.asarray(indices)
        if indices.max() < 65535:
            idx = self._accessor(indices.astype(np.uint16), 5123, "SCALAR", 34963)
        else:
            idx = self._accessor(indices.astype(np.uint32), 5125, "SCALAR", 34963)
        self.triangles += len(indices) // 3
        return {"attributes": attrs, "indices": idx, "material": material, "mode": 4}

    def mesh_node(self, name, primitives, translation=None):
        self.doc["meshes"].append({"name": name, "primitives": primitives})
        node = {"name": name, "mesh": len(self.doc["meshes"]) - 1}
        if translation is not None:
            node["translation"] = [float(v) for v in translation]
        self.doc["nodes"].append(node)
        self.doc["scenes"][0]["nodes"].append(len(self.doc["nodes"]) - 1)

    def label_node(self, name, position, text, **extras):
        self.doc["nodes"].append({"name": name, "translation": [float(v) for v in position],
                                  "extras": {"label": text, **extras}})
        self.doc["scenes"][0]["nodes"].append(len(self.doc["nodes"]) - 1)

    def write(self, path):
        for key in ("images", "textures", "samplers"):
            if not self.doc[key]:
                del self.doc[key]
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(pack_glb(self.doc, self.bin))
        return Path(path).stat().st_size


def grid_indices(rows, cols):
    r, c = np.meshgrid(np.arange(rows - 1), np.arange(cols - 1), indexing="ij")
    a = (r * cols + c).ravel()
    return np.stack((a, a + cols, a + 1, a + 1, a + cols, a + cols + 1), axis=1).ravel()


def grid_normals(heights, sx, sz):
    dz, dx = np.gradient(heights, sz, sx)
    n = np.stack((-dx, np.ones_like(heights), -dz), axis=-1)
    return (n / np.linalg.norm(n, axis=-1, keepdims=True)).reshape(-1, 3)


def hillshade(heights, sx, sz, azimuth=315, altitude=45):
    dz, dx = np.gradient(heights, sz, sx)
    slope = np.arctan(np.hypot(dx, dz))
    aspect = np.arctan2(dz, -dx)
    az, alt = math.radians(360 - azimuth + 90), math.radians(altitude)
    return np.clip(np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect), 0, 1)


def ear_clip(poly):
    """Triangulate a simple polygon (list of (x, y)); returns index triples."""
    n = len(poly)
    if n < 3:
        return []
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    idx = list(range(n)) if area > 0 else list(range(n))[::-1]
    tris, guard = [], 0
    def cross(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    def inside(p, a, b, c):
        return cross(a, b, p) >= 0 and cross(b, c, p) >= 0 and cross(c, a, p) >= 0
    while len(idx) > 3 and guard < 4 * n * n:
        guard += 1
        clipped = False
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = poly[i0], poly[i1], poly[i2]
            if cross(a, b, c) <= 1e-12:
                continue
            if any(inside(poly[j], a, b, c) for j in idx if j not in (i0, i1, i2)
                   and poly[j] != a and poly[j] != b and poly[j] != c):
                continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            clipped = True
            break
        if not clipped:
            idx.pop(0)  # degenerate: drop a vertex rather than loop forever
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris


def simplify_ring(pts, tol):
    """Douglas-Peucker on a closed ring (last point != first)."""
    if len(pts) <= 4:
        return pts
    def dp(seq):
        a, b = np.array(seq[0]), np.array(seq[-1])
        ab = b - a
        L = np.linalg.norm(ab)
        arr = np.array(seq[1:-1])
        if len(arr) == 0:
            return [seq[0], seq[-1]]
        d = np.abs(np.cross(ab, arr - a)) / L if L > 1e-9 else np.linalg.norm(arr - a, axis=1)
        k = int(np.argmax(d))
        if d[k] > tol:
            left, right = dp(seq[:k + 2]), dp(seq[k + 1:])
            return left[:-1] + right
        return [seq[0], seq[-1]]
    half = len(pts) // 2
    left, right = dp(list(pts[:half + 1])), dp(list(pts[half:]) + [pts[0]])
    ring = left[:-1] + right[:-1]
    return ring if len(ring) >= 3 else pts


def polygon_area(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                     for i in range(len(poly)))


def mercator_scale_xy(lon, lat, lon0, lat0):
    """Local equirectangular meters (east, north) around (lon0, lat0) on the WGS84 sphere of radius EARTH_R."""
    x = math.radians(lon - lon0) * EARTH_R * math.cos(math.radians(lat0))
    y = math.radians(lat - lat0) * EARTH_R
    return x, y
