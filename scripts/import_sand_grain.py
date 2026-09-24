#!/usr/bin/env python3
"""Extract one scanned Sand Atlas STL particle as a self-contained web GLB.

Source: https://sand-atlas.scigem.com/sands/caicos-0000001/
The sample meshes are CC BY 4.0; the 10-facet archive contains individual
micro-CT-derived Caicos ooids, not synthetic spheres or beach photographs.
"""

import argparse
import math
import struct
import zipfile
from pathlib import Path

from fetch_model_assets import inspect_glb
from sketchfab_models import pack_glb


def facets(archive, member):
    data = archive.read(member)
    if len(data) < 84:
        raise ValueError("STL is truncated")
    count = struct.unpack_from("<I", data, 80)[0]
    if count > 200_000 or len(data) != 84 + count * 50:
        raise ValueError("Not a supported binary STL")
    for index in range(count):
        offset = 84 + index * 50 + 12
        yield tuple(struct.unpack_from("<fff", data, offset + vertex * 12)
                    for vertex in range(3))


def bounds(triangles):
    points = [point for triangle in triangles for point in triangle]
    low = [min(point[axis] for point in points) for axis in range(3)]
    high = [max(point[axis] for point in points) for axis in range(3)]
    return low, high


def make_glb(triangles):
    positions = bytearray()
    normals = bytearray()
    low, high = bounds(triangles)
    for a, b, c in triangles:
        ab = [b[axis] - a[axis] for axis in range(3)]
        ac = [c[axis] - a[axis] for axis in range(3)]
        normal = (ab[1] * ac[2] - ab[2] * ac[1],
                  ab[2] * ac[0] - ab[0] * ac[2],
                  ab[0] * ac[1] - ab[1] * ac[0])
        magnitude = math.sqrt(sum(value * value for value in normal)) or 1
        unit = tuple(value / magnitude for value in normal)
        for point in (a, b, c):
            positions.extend(struct.pack("<fff", *point))
            normals.extend(struct.pack("<fff", *unit))
    binary = positions + normals
    count = len(triangles) * 3
    document = {
        "asset": {"version": "2.0", "generator": "Universe Scales Sand Atlas STL importer"},
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(positions), "target": 34962},
            {"buffer": 0, "byteOffset": len(positions), "byteLength": len(normals), "target": 34962},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": count,
             "type": "VEC3", "min": low, "max": high},
            {"bufferView": 1, "componentType": 5126, "count": count,
             "type": "VEC3"},
        ],
        "materials": [{"name": "Caicos ooid", "pbrMetallicRoughness": {
            "baseColorFactor": [0.71, 0.62, 0.48, 1],
            "metallicFactor": 0, "roughnessFactor": 0.94}}],
        "meshes": [{"name": "Scanned sand grain", "primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1}, "material": 0}]}],
        "nodes": [{"mesh": 0}], "scenes": [{"nodes": [0]}], "scene": 0,
    }
    return pack_glb(document, binary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Downloaded meshes_10.zip")
    parser.add_argument("--list", action="store_true", help="Show particle dimensions")
    parser.add_argument("--particle", default="particle_00051.stl")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with zipfile.ZipFile(args.archive) as archive:
        if args.list:
            for member in archive.namelist():
                triangles = list(facets(archive, member))
                low, high = bounds(triangles)
                size = [high[axis] - low[axis] for axis in range(3)]
                print(f"{member}: {len(triangles)} faces; extent "
                      + " x ".join(f"{value * 1e6:.0f}" for value in size) + " um")
            return
        if args.particle not in archive.namelist():
            raise ValueError("Particle not in source archive")
        output = make_glb(list(facets(archive, args.particle)))
    if not args.output:
        raise ValueError("--output is required when extracting a particle")
    args.output.write_bytes(output)
    print(args.particle, inspect_glb(output))


if __name__ == "__main__":
    main()
