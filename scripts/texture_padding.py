#!/usr/bin/env python3
"""Pad texture-atlas gutters so mipmaps do not bleed background across UV seams.

NASA's planet spheres use a cube-cross atlas on a white background. When the
texture is minified, mip levels average that white into the face edges and
thin white lines appear along the cube seams. Filling every pixel outside the
UV islands with the nearest island color removes the seams without changing
the covered texels. Also usable as a script on delivered GLBs:

    python3 scripts/texture_padding.py content/visualizations/models/nasa-jupiter.glb ...

It rewrites the GLB in place and prints the new size and SHA-256; update the
registry entry (bytes, sha256, processing) afterwards.
"""

import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_model_assets import pack_glb, read_glb, sha  # noqa: E402

COMPONENTS = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
OPERATION = "Pad texture-atlas gutters with nearest UV-island colors to prevent mipmap seam bleeding"


def accessor_array(document, binary, index):
    accessor = document["accessors"][index]
    view = document["bufferViews"][accessor["bufferView"]]
    dtype = np.dtype(COMPONENTS[accessor["componentType"]]).newbyteorder("<")
    width = WIDTH[accessor["type"]]
    stride = view.get("byteStride", dtype.itemsize * width)
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    return np.ndarray((accessor["count"], width), dtype=dtype, buffer=binary,
                      offset=offset, strides=(stride, dtype.itemsize)).copy()


def uv_mask(uv_triangles, size, erode=1):
    """Rasterize UV triangles (N x 3 x 2, glTF UV space) into a coverage mask."""
    width, height = size
    image = Image.new("L", size, 0)
    draw = ImageDraw.Draw(image)
    for triangle in uv_triangles:
        draw.polygon([(u * width, v * height) for u, v in triangle], fill=255)
    mask = np.asarray(image) > 0
    # Edge texels are often already contaminated by JPEG ringing; refill them too.
    for _ in range(erode):
        inner = mask.copy()
        inner[1:, :] &= mask[:-1, :]
        inner[:-1, :] &= mask[1:, :]
        inner[:, 1:] &= mask[:, :-1]
        inner[:, :-1] &= mask[:, 1:]
        mask = inner
    return mask


def pad(pixels, mask, max_iterations=2048):
    """Fill pixels outside `mask` with the average of already-filled 4-neighbors, ring by ring."""
    color = pixels.astype(np.float64) * mask[..., None]
    filled = mask.copy()
    for _ in range(max_iterations):
        if filled.all():
            break
        total = np.zeros_like(color)
        count = np.zeros(mask.shape)
        for axis, step in ((0, 1), (0, -1), (1, 1), (1, -1)):
            shifted_color = np.roll(color, step, axis=axis)
            shifted_filled = np.roll(filled, step, axis=axis)
            edge = [slice(None)] * 2
            edge[axis] = 0 if step == 1 else -1
            shifted_filled[tuple(edge)] = False
            total += shifted_color * shifted_filled[..., None]
            count += shifted_filled
        grow = ~filled & (count > 0)
        color[grow] = total[grow] / count[grow][:, None]
        filled |= grow
    return np.clip(np.rint(color), 0, 255).astype(np.uint8)


def pad_glb(data):
    """Return (new GLB bytes, number of padded images)."""
    document, binary = read_glb(data)
    binary = bytearray(binary)
    triangles_by_image = {}
    for mesh in document["meshes"]:
        for primitive in mesh["primitives"]:
            if "TEXCOORD_0" not in primitive["attributes"] or "material" not in primitive:
                continue
            uv = accessor_array(document, binary, primitive["attributes"]["TEXCOORD_0"]).astype(np.float64)
            if "indices" in primitive:
                indices = accessor_array(document, binary, primitive["indices"]).reshape(-1)
            else:
                indices = np.arange(len(uv))
            triangles = uv[indices.reshape(-1, 3)]
            material = document["materials"][primitive["material"]]
            slots = [material.get(key) for key in ("normalTexture", "occlusionTexture", "emissiveTexture")]
            pbr = material.get("pbrMetallicRoughness", {})
            slots += [pbr.get(key) for key in ("baseColorTexture", "metallicRoughnessTexture")]
            for slot in filter(None, slots):
                image_index = document["textures"][slot["index"]]["source"]
                triangles_by_image.setdefault(image_index, []).append(triangles)
    payloads = {}
    for image_index, parts in triangles_by_image.items():
        item = document["images"][image_index]
        view = document["bufferViews"][item["bufferView"]]
        start = view.get("byteOffset", 0)
        with Image.open(io.BytesIO(bytes(binary[start:start + view["byteLength"]]))) as source:
            image = source.convert("RGB")
        mask = uv_mask(np.concatenate(parts), image.size)
        padded = Image.fromarray(pad(np.asarray(image), mask))
        output = io.BytesIO()
        if item.get("mimeType") == "image/png":
            padded.save(output, format="PNG", optimize=True)
        else:
            padded.save(output, format="JPEG", quality=88, subsampling=0, optimize=True)
        payloads[item["bufferView"]] = output.getvalue()
    if not payloads:
        return data, 0
    # Rebuild the binary chunk with replaced image views, keeping 4-byte alignment.
    rebuilt = bytearray()
    for index, view in enumerate(document["bufferViews"]):
        start = view.get("byteOffset", 0)
        chunk = payloads.get(index, bytes(binary[start:start + view["byteLength"]]))
        rebuilt.extend(b"\0" * (-len(rebuilt) % 4))
        view["byteOffset"] = len(rebuilt)
        view["byteLength"] = len(chunk)
        rebuilt.extend(chunk)
    rebuilt.extend(b"\0" * (-len(rebuilt) % 4))
    document["buffers"] = [{"byteLength": len(rebuilt)}]
    return pack_glb(document, bytes(rebuilt)), len(payloads)


def main(paths):
    for path in map(Path, paths):
        data, count = pad_glb(path.read_bytes())
        path.write_bytes(data)
        print(json.dumps({"file": str(path), "padded_images": count, "bytes": len(data), "sha256": sha(data)}))


if __name__ == "__main__":
    main(sys.argv[1:])
