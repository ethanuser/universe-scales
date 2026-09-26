#!/usr/bin/env python3
"""Render a quick untextured GLB geometry preview for candidate curation."""

import argparse
import json
import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


COMPONENTS = {5120: np.int8, 5121: np.uint8, 5122: np.int16,
              5123: np.uint16, 5125: np.uint32, 5126: np.float32}
TYPE_SIZE = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def read_glb(path):
    data = path.read_bytes()
    if data[:4] != b"glTF" or struct.unpack_from("<I", data, 4)[0] != 2:
        raise ValueError("Expected binary glTF 2.0")
    json_size = struct.unpack_from("<I", data, 12)[0]
    document = json.loads(data[20:20 + json_size])
    binary_start = 20 + json_size + 8
    return document, memoryview(data)[binary_start:]


def accessor(document, binary, index):
    item = document["accessors"][index]
    view = document["bufferViews"][item["bufferView"]]
    dtype = np.dtype(COMPONENTS[item["componentType"]]).newbyteorder("<")
    count = TYPE_SIZE[item["type"]]
    stride = view.get("byteStride", dtype.itemsize * count)
    offset = view.get("byteOffset", 0) + item.get("byteOffset", 0)
    return np.ndarray((item["count"], count), dtype=dtype, buffer=binary,
                      offset=offset, strides=(stride, dtype.itemsize)).copy()


def node_matrix(node):
    if "matrix" in node:
        return np.asarray(node["matrix"], dtype=float).reshape((4, 4)).T
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    rotation = np.array([
        [1 - 2 * (y*y + z*z), 2 * (x*y - z*w), 2 * (x*z + y*w)],
        [2 * (x*y + z*w), 1 - 2 * (x*x + z*z), 2 * (y*z - x*w)],
        [2 * (x*z - y*w), 2 * (y*z + x*w), 1 - 2 * (x*x + y*y)],
    ])
    result = np.eye(4)
    result[:3, :3] = rotation @ np.diag(node.get("scale", [1, 1, 1]))
    result[:3, 3] = node.get("translation", [0, 0, 0])
    return result


def triangles(document, binary, max_faces, excluded):
    parts = []

    def visit(node_index, parent):
        node = document["nodes"][node_index]
        if node.get("name") in excluded:
            return
        world = parent @ node_matrix(node)
        if "mesh" in node:
            for primitive in document["meshes"][node["mesh"]]["primitives"]:
                if primitive.get("mode", 4) != 4:
                    continue
                points = accessor(document, binary, primitive["attributes"]["POSITION"]).astype(float)
                points = (np.column_stack((points, np.ones(len(points)))) @ world.T)[:, :3]
                if "indices" in primitive:
                    index = accessor(document, binary, primitive["indices"]).reshape(-1)
                else:
                    index = np.arange(len(points))
                face_index = index[:len(index) // 3 * 3].reshape(-1, 3)
                material = document.get("materials", [{}])[primitive.get("material", 0)]
                color = material.get("pbrMetallicRoughness", {}).get("baseColorFactor", [0.67, 0.73, 0.77, 1])[:3]
                if "COLOR_0" in primitive["attributes"]:
                    vertex_color = accessor(document, binary, primitive["attributes"]["COLOR_0"])
                    color = np.mean(vertex_color[:, :3], axis=0)
                    if np.issubdtype(vertex_color.dtype, np.integer):
                        color = color / np.iinfo(vertex_color.dtype).max
                parts.append((points, face_index, np.asarray(color)))
        for child in node.get("children", []):
            visit(child, world)

    for root in document["scenes"][document.get("scene", 0)]["nodes"]:
        visit(root, np.eye(4))
    total = sum(len(index) for _, index, _ in parts)
    stride = max(1, math.ceil(total / max_faces))
    return [(points[index[::stride]], color) for points, index, color in parts if len(index)]


def render(parts, output, yaw, elevation, width=900, height=700):
    angle = math.radians(yaw)
    pitch = math.radians(elevation)
    eye = np.array([math.sin(angle) * math.cos(pitch), math.sin(pitch),
                    math.cos(angle) * math.cos(pitch)])
    right = np.cross([0, 1, 0], eye)
    right /= np.linalg.norm(right)
    up = np.cross(eye, right)
    all_points = np.concatenate([faces.reshape(-1, 3) for faces, _ in parts])
    center = (np.min(all_points, axis=0) + np.max(all_points, axis=0)) / 2
    projected = np.column_stack(((all_points - center) @ right, (all_points - center) @ up))
    extent = np.max(np.ptp(projected, axis=0))
    scale = min(width, height) * 0.84 / max(extent, 1e-9)
    polygons = []
    light = np.array([-0.3, 0.8, 0.55])
    light /= np.linalg.norm(light)
    for faces, color in parts:
        centered = faces - center
        planar = np.stack((centered @ right, centered @ up), axis=-1)
        screen = np.empty_like(planar[..., :2])
        screen[..., 0] = width / 2 + planar[..., 0] * scale
        screen[..., 1] = height / 2 - planar[..., 1] * scale
        normals = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
        lengths = np.linalg.norm(normals, axis=1)
        normals /= np.maximum(lengths[:, None], 1e-12)
        shade = np.clip(0.48 + 0.45 * np.abs(normals @ light), 0, 1)
        depth = np.mean(centered @ eye, axis=1)
        for points, tone, distance in zip(screen, shade, depth):
            rgb = tuple(int(value) for value in np.clip(color * tone * 255, 0, 255))
            polygons.append((distance, points, rgb))
    image = Image.new("RGB", (width, height), "#e8eef2")
    draw = ImageDraw.Draw(image)
    for _, points, rgb in sorted(polygons, key=lambda part: part[0]):
        draw.polygon([tuple(point) for point in points], fill=rgb)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    print(f"Rendered {len(polygons):,} triangles: {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--yaw", type=float, default=30)
    parser.add_argument("--elevation", type=float, default=22)
    parser.add_argument("--max-faces", type=int, default=8000)
    parser.add_argument("--exclude-node", action="append", default=[])
    args = parser.parse_args()
    document, binary = read_glb(args.model)
    parts = triangles(document, binary, args.max_faces, set(args.exclude_node))
    if not parts:
        raise ValueError("No triangle primitives found")
    render(parts, args.output, args.yaw, args.elevation)


if __name__ == "__main__":
    main()
