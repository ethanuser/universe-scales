#!/usr/bin/env python3
"""Build a scale-calibrated Carina illustration from ESO's VISTA sky mosaic.

The image covers only part of the nebula. A context bracket spans 300 light-years;
the gently bowed image surface is a depth cue, not a recovered 3D gas volume.
"""

import argparse
import hashlib
import io
import math
from pathlib import Path
import struct

from PIL import Image

from fetch_model_assets import pack_glb, write_json

LIGHT_YEAR_M = 9.4607304725808e15
REGION_SPAN_LY = 300
DISTANCE_LY = 7500
FIELD_ARCMIN = (88.49, 71.78)
IMAGE_URL = "https://cdn.eso.org/images/screen/eso1828b.jpg"
SOURCE = "https://www.eso.org/public/images/eso1828b/"
BASIS = "https://science.nasa.gov/missions/hubble/hubbles-sparkling-new-view-of-the-carina-nebula/"


def field_span_ly(arcmin):
    return 2 * DISTANCE_LY * math.tan(math.radians(arcmin / 60) / 2)


def surface_geometry(width=80):
    span_x, span_y = (field_span_ly(angle) for angle in FIELD_ARCMIN)
    height = round(width * span_y / span_x)
    positions, uv, colors, indices = [], [], [], []
    for y in range(height + 1):
        for x in range(width + 1):
            u, v = x / width - 0.5, 0.5 - y / height
            # A small bend is a presentation cue, never a density-to-depth fit.
            z = span_x * (0.08 * (u * u + v * v) - 0.015)
            edge = max(0, min(1, (0.5 - max(abs(u), abs(v))) / 0.04))
            positions.append((u * span_x, v * span_y, z))
            uv.append((x / width, y / height))
            colors.append((1, 1, 1, edge * edge * (3 - 2 * edge)))
            if x < width and y < height:
                start = y * (width + 1) + x
                indices.extend([start, start + width + 1, start + 1,
                                start + 1, start + width + 1, start + width + 2])
    return positions, uv, colors, indices


def build(image):
    document = {"asset": {"version": "2.0", "generator": "Universe Scales ESO Carina illustration"},
                "scene": 0, "scenes": [{"nodes": []}], "nodes": [], "meshes": [],
                "bufferViews": [], "accessors": [], "materials": [],
                "extensionsUsed": ["KHR_materials_unlit"]}
    binary = bytearray()

    def accessor(values, kind="VEC3", code="f", component=5126):
        binary.extend(b"\0" * (-len(binary) % 4))
        offset = len(binary)
        flat = values if kind == "SCALAR" else [v for row in values for v in row]
        binary.extend(struct.pack("<" + code * len(flat), *flat))
        view = len(document["bufferViews"])
        document["bufferViews"].append({"buffer": 0, "byteOffset": offset,
                                        "byteLength": len(binary) - offset, "target": 34962})
        index = len(document["accessors"])
        record = {"bufferView": view, "componentType": component, "count": len(values), "type": kind}
        if kind != "SCALAR":
            record.update({"min": [min(row[i] for row in values) for i in range(len(values[0]))],
                           "max": [max(row[i] for row in values) for i in range(len(values[0]))]})
        document["accessors"].append(record)
        return index

    def primitive(name, positions, colors=None, mode=0, tint=(1, 1, 1, 0.8), extras=None):
        attributes = {"POSITION": accessor(positions)}
        if colors:
            attributes["COLOR_0"] = accessor(colors)
        material = len(document["materials"])
        document["materials"].append({"pbrMetallicRoughness": {"baseColorFactor": list(tint),
                                        "metallicFactor": 0}, "alphaMode": "BLEND", "doubleSided": True,
                                        "extensions": {"KHR_materials_unlit": {}}})
        mesh = len(document["meshes"])
        document["meshes"].append({"name": name, "primitives": [{"attributes": attributes,
                                                                  "mode": mode, "material": material}]})
        node = len(document["nodes"])
        document["nodes"].append({"name": name, "mesh": mesh, "extras": extras or {}})
        document["scenes"][0]["nodes"].append(node)

    image = image.convert("RGB")
    if image.getbbox() is None:
        raise ValueError("Reference image has no visible sky samples")
    positions, uv, colors, indices = surface_geometry()
    attributes = {"POSITION": accessor(positions), "TEXCOORD_0": accessor(uv, "VEC2"),
                  "COLOR_0": accessor(colors, "VEC4")}
    triangles = accessor(indices, "SCALAR", "H", 5123)
    image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    jpeg = io.BytesIO()
    image.save(jpeg, format="JPEG", quality=90)
    binary.extend(b"\0" * (-len(binary) % 4))
    texture_view = len(document["bufferViews"])
    document["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(jpeg.getvalue())})
    binary.extend(jpeg.getvalue())
    document["images"] = [{"bufferView": texture_view, "mimeType": "image/jpeg"}]
    document["textures"] = [{"source": 0, "sampler": 0}]
    document["samplers"] = [{"magFilter": 9729, "minFilter": 9987, "wrapS": 33071, "wrapT": 33071}]
    document["materials"].append({"pbrMetallicRoughness": {"baseColorTexture": {"index": 0},
                                    "metallicFactor": 0}, "alphaMode": "BLEND", "doubleSided": True,
                                    "extensions": {"KHR_materials_unlit": {}}})
    document["meshes"].append({"name": "VISTA observed field on illustrative bowed surface", "primitives": [
        {"attributes": attributes, "indices": triangles, "mode": 4, "material": 0}]})
    document["nodes"].append({"name": "VISTA field (not a reconstructed gas volume)", "mesh": 0})
    document["scenes"][0]["nodes"].append(0)
    bottom = -field_span_ly(FIELD_ARCMIN[1]) / 2 - 10
    radius = REGION_SPAN_LY / 2
    primitive("Approximate whole-nebula span (not a gas edge)",
              [(-radius, bottom + 5, 0), (-radius, bottom, 0),
               (radius, bottom, 0), (radius, bottom + 5, 0)],
              mode=3, tint=(0.6, 0.68, 0.78, 0.65))
    document["buffers"] = [{"byteLength": len(binary)}]
    return pack_glb(document, bytes(binary)), len(indices) // 3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-image", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("/private/tmp/carina-model"))
    args = parser.parse_args()
    with Image.open(args.reference_image) as image:
        model, count = build(image)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / "carina-vista-field.glb"
    path.write_bytes(model)
    entry = {
        "id": "carina-vista-field", "replaces": "carina-vista-cloud",
        "source": SOURCE, "download_url": IMAGE_URL,
        "link_label": "ESO VISTA reference image",
        "author": "ESO/J. Emerson/M. Irwin/J. Lewis; geometry: Universe Scales",
        "license": "CC-BY-4.0", "license_url": "https://www.eso.org/public/outreach/copyright/",
        "license_files": ["licenses/CC-BY-4.0.txt", "sources/carina-model.md"],
        "matches": {"length": ["Carina Nebula"]}, "geometry": "mesh",
        "volume_semantics": "not a volume measurement", "closed_volume_checked": False,
        "presentation": {"reference_size": REGION_SPAN_LY, "yaw": 15,
                         "layout_width_factor": 1.05, "focus_scale_factor": 1.15},
        "basis_url": BASIS, "basis_label": "NASA: whole-nebula size and distance",
        "note": "ESO/J. Emerson/M. Irwin/J. Lewis, adapted into a rotatable image-derived surface. VISTA's Z, J and Ks bands show infrared structures and many foreground/background stars, not naked-eye colors. The published 88.49 by 71.78 arcminute field at about 7,500 light-years covers roughly 193 by 157 light-years. It is not stretched to the listed approximately 300-light-year nebula span: the lower bracket marks that broader context, not an observed gas edge. The observed image is mapped onto a gently bowed sheet; that bend is an artistic depth cue. This is a 2.5D illustration, not tomography or a measured gas-density volume.",
        "processing": {"script": "scripts/build_carina_model.py",
                       "source_image_sha256": hashlib.sha256(args.reference_image.read_bytes()).hexdigest(),
                       "source_field_arcmin": list(FIELD_ARCMIN), "adopted_distance_ly": DISTANCE_LY,
                       "image_span_ly": [field_span_ly(angle) for angle in FIELD_ARCMIN],
                       "whole_nebula_span_ly": REGION_SPAN_LY, "surface_triangles": count,
                       "texture_max_px": 1024, "texture_encoding": "JPEG quality 90",
                       "depth_semantics": "authored illustration, not measured"}
    }
    write_json(args.output_dir / "entry.json", entry)
    print(f"{path}: {len(model):,} bytes; {count:,} surface triangles")


if __name__ == "__main__":
    main()
