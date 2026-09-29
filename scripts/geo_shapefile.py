#!/usr/bin/env python3
"""Tiny pure-Python ESRI shapefile reader (polyline/polygon/point) with .dbf attributes.

Used by the geographic model builders (Amazon River etc.) so they do not need
GDAL/fiona. Only what Natural Earth's public-domain shapefiles need.
"""
import struct
from pathlib import Path


def read_dbf(path):
    data = Path(path).read_bytes()
    n, header_len, record_len = struct.unpack("<IHH", data[4:12])
    fields, pos = [], 32
    while data[pos] != 0x0D:
        name = data[pos:pos + 11].split(b"\0")[0].decode("latin-1")
        length = data[pos + 16]
        fields.append((name, length))
        pos += 32
    rows = []
    for i in range(n):
        rec = data[header_len + i * record_len: header_len + (i + 1) * record_len]
        off, row = 1, {}
        for name, length in fields:
            row[name] = rec[off:off + length].decode("utf-8", "replace").strip()
            off += length
        rows.append(row)
    return rows


def read_shp(path):
    """Yield (parts, bbox) where parts is a list of [(x, y), ...] rings/lines."""
    data = Path(path).read_bytes()
    pos, out = 100, []
    while pos < len(data):
        _, length = struct.unpack(">ii", data[pos:pos + 8])
        content = data[pos + 8: pos + 8 + length * 2]
        pos += 8 + length * 2
        shape_type = struct.unpack("<i", content[:4])[0]
        if shape_type == 0:
            out.append(([], None)); continue
        if shape_type in (3, 5, 13, 15, 23, 25):
            bbox = struct.unpack("<4d", content[4:36])
            n_parts, n_points = struct.unpack("<ii", content[36:44])
            parts = list(struct.unpack(f"<{n_parts}i", content[44:44 + 4 * n_parts]))
            off = 44 + 4 * n_parts
            pts = [struct.unpack("<2d", content[off + 16 * i: off + 16 * i + 16]) for i in range(n_points)]
            parts.append(n_points)
            out.append(([pts[parts[i]:parts[i + 1]] for i in range(n_parts)], bbox))
        elif shape_type in (1, 11, 21):
            x, y = struct.unpack("<2d", content[4:20]); out.append(([[(x, y)]], (x, y, x, y)))
        else:
            raise ValueError(f"unsupported shape type {shape_type}")
    return out


def read_layer(basepath):
    base = Path(basepath)
    shapes, rows = read_shp(base.with_suffix(".shp")), read_dbf(base.with_suffix(".dbf"))
    return [{"parts": s[0], "bbox": s[1], **r} for s, r in zip(shapes, rows)]
