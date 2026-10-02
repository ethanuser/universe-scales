#!/usr/bin/env python3
"""Build a compact, rotatable Tarantula illustration from ESO's observed colors.

The angular field sets XY scale. Depth is an authored illustration, not tomography.
Run with the unmodified screen-size eso0650a.jpg (not a cropped wallpaper).
"""

import argparse
import hashlib
import math
from pathlib import Path
import random
import struct

from PIL import Image

from fetch_model_assets import pack_glb, write_json

LIGHT_YEAR_M = 9.4607304725808e15
REFERENCE_M = 9e18
REFERENCE_LY = REFERENCE_M / LIGHT_YEAR_M
DISTANCE_LY = 170_000  # Published distance for this ESO release, not a new fit.
FIELD_ARCMIN = (62.40, 62.31)
IMAGE_URL = "https://cdn.eso.org/images/screen/eso0650a.jpg"
SOURCE = "https://www.eso.org/public/images/eso0650a/"
BASIS = "https://www.eso.org/public/news/eso0650/"
CENTER = (0.435, 0.245)  # Image-space center of the bright R136 region.


def field_span_ly(arcmin):
    return 2 * DISTANCE_LY * math.tan(math.radians(arcmin / 60) / 2)


def crop_box(image_size):
    width, height = image_size
    crop_width = REFERENCE_LY / field_span_ly(FIELD_ARCMIN[0]) * width
    crop_height = REFERENCE_LY / field_span_ly(FIELD_ARCMIN[1]) * height
    x, y = CENTER[0] * width, CENTER[1] * height
    return (round(x - crop_width / 2), round(y - crop_height / 2),
            round(x + crop_width / 2), round(y + crop_height / 2))


def linear_color(channel):
    value = channel / 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def sample_cloud(image, resolution=170):
    # Equal angular sampling on both axes, independent of the input aspect ratio.
    field = image.convert("RGB").crop(crop_box(image.size)).resize(
        (resolution, resolution), Image.Resampling.LANCZOS)
    random_source = random.Random(3000650)
    positions, colors = [], []
    for y in range(resolution):
        for x in range(resolution):
            rgb = field.getpixel((x, y))
            brightness = max(rgb) / 255
            if brightness < 0.11 or random_source.random() > min(1, brightness * 3):
                continue
            for _ in range(2):
                u = (x + random_source.random()) / resolution - 0.5
                v = 0.5 - (y + random_source.random()) / resolution
                radius2 = u * u + v * v
                if radius2 > 0.25:
                    continue
                edge = max(0, min(1, (0.5 - math.sqrt(radius2)) / 0.12))
                if random_source.random() > edge * edge * (3 - 2 * edge):
                    continue
                # The aperture is a viewing window, not a spherical gas boundary.
                # A shallow bowed layer + thickness suggests depth without using
                # brightness as a surrogate for a measured physical coordinate.
                z = REFERENCE_LY * (0.20 * radius2 - 0.045
                                   + (random_source.random() - 0.5) * 0.08)
                positions.append((u * REFERENCE_LY, v * REFERENCE_LY, z))
                colors.append(tuple(linear_color(channel) for channel in rgb))
    if not positions:
        raise ValueError("Reference image has no visible emission samples")
    return positions, colors


def build(image):
    positions, colors = sample_cloud(image)
    binary = bytearray()
    document = {"asset": {"version": "2.0", "generator": "Universe Scales ESO Tarantula illustration"},
                "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [], "meshes": [],
                "bufferViews": [], "accessors": [], "extensionsUsed": ["KHR_materials_unlit"]}
    for values in (positions, colors):
        offset = len(binary)
        binary.extend(struct.pack("<" + "f" * len(values) * 3, *(v for row in values for v in row)))
        view = len(document["bufferViews"])
        document["bufferViews"].append({"buffer": 0, "byteOffset": offset,
                                        "byteLength": len(binary) - offset, "target": 34962})
        document["accessors"].append({"bufferView": view, "componentType": 5126,
                                      "count": len(values), "type": "VEC3",
                                      "min": [min(row[i] for row in values) for i in range(3)],
                                      "max": [max(row[i] for row in values) for i in range(3)]})
    document["materials"] = [{"pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 0.68],
                               "metallicFactor": 0}, "alphaMode": "BLEND", "doubleSided": True,
                               "extensions": {"KHR_materials_unlit": {}}}]
    document["meshes"] = [{"name": "ESO emission in a calibrated viewing aperture", "primitives": [
        {"attributes": {"POSITION": 0, "COLOR_0": 1}, "mode": 0, "material": 0}]}]
    document["nodes"] = [{"name": "Tarantula emission (illustrative depth)", "mesh": 0,
                           "extras": {"softPoints": True, "pointSize": {"max": 5, "perPixel": 1 / 85}}}]
    document["buffers"] = [{"byteLength": len(binary)}]
    return pack_glb(document, bytes(binary)), len(positions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-image", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("/private/tmp/tarantula-model"))
    args = parser.parse_args()
    with Image.open(args.reference_image) as image:
        model, count = build(image)
        crop = crop_box(image.size)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / "tarantula-eso-cloud.glb"
    path.write_bytes(model)
    entry = {
        "id": "tarantula-eso-cloud", "source": SOURCE, "download_url": IMAGE_URL,
        "link_label": "ESO reference image", "author": "ESO/R. Fosbury (ST-ECF); geometry: Universe Scales",
        "license": "CC-BY-4.0", "license_url": "https://www.eso.org/public/outreach/copyright/",
        "license_files": ["licenses/CC-BY-4.0.txt", "sources/tarantula-model.md"],
        "matches": {"length": ["Tarantula Nebula"]}, "geometry": "mesh",
        "presentation": {"reference_size": REFERENCE_LY, "yaw": 12,
                         "layout_width_factor": 1.05, "focus_scale_factor": 1.15},
        "basis_url": BASIS, "basis_label": "ESO field of view and approximate nebula span",
        "note": "ESO/R. Fosbury (ST-ECF), adapted into a rotatable illustration. Colors and projected filaments come from the MPG/ESO 2.2-metre telescope's optical B, V, H-alpha and [O III] mosaic. Its published 62.40 by 62.31 arcminute field and 170,000-light-year distance set the scale. A circular viewing aperture around the bright R136 region spans the listed approximately 951 light-years, close to ESO's approximate 1,000-light-year nebula size; the aperture is not a measured gas edge. The bowed emitting layer and its thickness are artistic depth cues, not a tomographic reconstruction. Sample points represent emission, not individual atoms or stars.",
        "processing": {"script": "scripts/build_tarantula_model.py",
                       "source_image_sha256": hashlib.sha256(args.reference_image.read_bytes()).hexdigest(),
                       "source_field_arcmin": list(FIELD_ARCMIN), "adopted_distance_ly": DISTANCE_LY,
                       "crop_box_pixels": crop, "viewing_aperture_ly": REFERENCE_LY,
                       "cloud_points": count, "depth_semantics": "authored illustration, not measured"}
    }
    write_json(args.output_dir / "entry.json", entry)
    print(f"{path}: {len(model):,} bytes; {count:,} emission samples")


if __name__ == "__main__":
    main()
