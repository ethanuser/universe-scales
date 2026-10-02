#!/usr/bin/env python3
"""Build a compact, explicitly inferred-depth Orion nebula from a Hubble image.

python3 scripts/build_orion_model.py --reference-image /tmp/orion-hubble-1024.jpg

The 13-light-year Hubble field is NOT stretched to the whole dataset span.
Only its colors and sky-plane positions are observed. Depth is an authored
blister illustration, not a recovered volumetric density or NASA's 3D mesh.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import struct

from PIL import Image

from fetch_model_assets import pack_glb, write_json

ROOT = Path(__file__).resolve().parents[1]
LIGHT_YEAR_M = 9.4607304725808e15
IMAGE_SPAN_LY = 13.0
REGION_SPAN_LY = 2.4e17 / LIGHT_YEAR_M
IMAGE_URL = ("https://assets.science.nasa.gov/dynamicimage/assets/science/missions/"
             "hubble/releases/2006/01/STScI-01EVT7X0BR54ZWDP1AG2DA54RA.tif?w=1024")
SOURCE = "https://science.nasa.gov/asset/hubble/hubbles-sharpest-view-of-the-orion-nebula/"
STRUCTURE_SOURCE = "https://doi.org/10.1088/0004-6256/137/1/367"


def linear_color(channel):
    value = channel / 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def blister_depth(u, v):
    # Observer is +Z. The central ionization front lies behind the Trapezium;
    # only that relative arrangement and ~0.2 pc offset are reference-based.
    radius2 = ((u - 0.445) * IMAGE_SPAN_LY / 0.85) ** 2 + ((v - 0.456) * IMAGE_SPAN_LY / 0.85) ** 2
    return -0.15 - 0.5 * math.exp(-radius2 / 2)


def sample_cloud(image, size=150):
    image = image.convert("RGB").resize((size, size), Image.Resampling.LANCZOS)
    random_source = random.Random(42006)
    positions, colors = [], []
    for y in range(size):
        for x in range(size):
            rgb = image.getpixel((x, y))
            brightness = max(rgb) / 255
            if brightness < 0.08 or random_source.random() > min(1, brightness * 2.4):
                continue
            for _ in range(2):
                u = (x + random_source.random()) / size
                v = (y + random_source.random()) / size
                # A thin emitting layer; outer-field depths remain illustrative.
                z = blister_depth(u, v) + (random_source.random() - 0.5) * 0.326
                positions.append(((u - 0.5) * IMAGE_SPAN_LY, (0.5 - v) * IMAGE_SPAN_LY, z))
                colors.append(tuple(linear_color(channel) for channel in rgb))
    return positions, colors


def build(image):
    document = {"asset": {"version": "2.0", "generator": "Universe Scales referenced Orion illustration"},
                "scene": 0, "scenes": [{"nodes": []}], "nodes": [], "meshes": [],
                "materials": [], "accessors": [], "bufferViews": [],
                "extensionsUsed": ["KHR_materials_unlit"]}
    binary = bytearray()

    def accessor(values, target=34962):
        offset = len(binary)
        binary.extend(struct.pack("<" + "f" * len(values) * 3, *(v for row in values for v in row)))
        view = len(document["bufferViews"])
        document["bufferViews"].append({"buffer": 0, "byteOffset": offset,
                                        "byteLength": len(binary) - offset, "target": target})
        index = len(document["accessors"])
        document["accessors"].append({"bufferView": view, "componentType": 5126,
                                      "count": len(values), "type": "VEC3",
                                      "min": [min(row[i] for row in values) for i in range(3)],
                                      "max": [max(row[i] for row in values) for i in range(3)]})
        return index

    def primitive(name, positions, colors=None, mode=0, tint=(1, 1, 1, 0.8), extras=None):
        attributes = {"POSITION": accessor(positions)}
        if colors:
            attributes["COLOR_0"] = accessor(colors)
        material = len(document["materials"])
        document["materials"].append({"pbrMetallicRoughness": {"baseColorFactor": list(tint), "metallicFactor": 0},
                                       "alphaMode": "BLEND", "doubleSided": True,
                                       "extensions": {"KHR_materials_unlit": {}}})
        mesh = len(document["meshes"])
        document["meshes"].append({"name": name, "primitives": [{"attributes": attributes, "mode": mode,
                                                                  "material": material}]})
        node = len(document["nodes"])
        document["nodes"].append({"name": name, "mesh": mesh, "extras": extras or {}})
        document["scenes"][0]["nodes"].append(node)

    positions, colors = sample_cloud(image)
    primitive("Hubble colors on inferred ionization layer", positions, colors,
              extras={"pointSize": {"max": 4.5, "perPixel": 1 / 110}})
    # Context is a span bracket, not fabricated gas outside the photographed field.
    radius, bottom = REGION_SPAN_LY / 2, -IMAGE_SPAN_LY / 2 - 1.5
    primitive("Approximate whole-nebula span", [(-radius, bottom + 0.5, 0), (-radius, bottom, 0),
              (radius, bottom, 0), (radius, bottom + 0.5, 0)], mode=3, tint=(0.42, 0.52, 0.65, 0.55))
    # The bright stellar group is schematic, not a new astrometric fit.
    trap_x = (0.445 - 0.5) * IMAGE_SPAN_LY
    trap_y = (0.5 - 0.456) * IMAGE_SPAN_LY
    stars = [(trap_x + x, trap_y + y, 0) for x, y in ((-0.045, 0.018), (0, 0), (0.032, 0.045), (0.07, -0.035))]
    primitive("Trapezium", stars, tint=(0.85, 0.92, 1, 1), extras={"label": "Trapezium",
              "labelLayout": "orbit", "labelPriority": 0, "pointSize": {"max": 3, "perPixel": 1 / 200}})
    depth, x, y = 0.65, trap_x + 1, trap_y + 1
    primitive("Inferred central depth cue", [(x, y, 0), (x, y, -depth),
              (x - 0.14, y, 0), (x + 0.14, y, 0),
              (x - 0.14, y, -depth), (x + 0.14, y, -depth)],
              mode=1, tint=(0.55, 0.68, 0.85, 0.7))
    node = len(document["nodes"])
    document["nodes"].append({"name": "Inferred depth annotation", "translation": [x, y, -depth / 2],
                               "extras": {"label": "0.2 pc depth (inferred)", "labelLayout": "orbit",
                                          "labelPriority": 1, "labelOffset": {"x": 70, "y": -30},
                                          "labelAxis": {"axis": "z", "length": depth, "minPixelLength": 8}}})
    document["scenes"][0]["nodes"].append(node)
    document["buffers"] = [{"byteLength": len(binary)}]
    return pack_glb(document, bytes(binary)), len(positions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-image", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("/private/tmp/orion-model"))
    args = parser.parse_args()
    with Image.open(args.reference_image) as image:
        model, point_count = build(image)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / "orion-hubble-blister.glb"
    path.write_bytes(model)
    entry = {
        "id": "orion-hubble-blister", "source": SOURCE, "download_url": IMAGE_URL,
        "link_label": "Reference image",
        "author": "Image: NASA, ESA, Hubble Space Telescope Orion Treasury Project Team, Massimo Robberto (STScI, ESA); inferred geometry: Universe Scales",
        "license": "NASA/ESA credited scientific image under NASA media guidelines; authored geometry under the project code license",
        "license_url": "https://www.nasa.gov/nasa-brand-center/images-and-media/",
        "license_files": ["licenses/nasa-media-guidelines.html", "sources/orion-model.md"],
        "matches": {"length": ["Orion Nebula"]}, "geometry": "mesh",
        "presentation": {"reference_size": REGION_SPAN_LY, "yaw": 22, "layout_width_factor": 1.05,
                         "focus_scale_factor": 1.15},
        "basis_url": STRUCTURE_SOURCE, "basis_label": "Blister structure: O'Dell et al. (2009)",
        "note": "Hubble's observed colors and sky-plane positions are sampled into a rotatable gas layer. The photographed field is 13 light-years wide; it is not stretched to the listed roughly 25-light-year whole nebula. The lower bracket indicates that larger contextual span, not an observed gas boundary. Inferred depth illustrates a thin ionization front behind the Trapezium, following Orion's blister interpretation; outside that inner region the depth is an artistic assumption. The four stellar markers are enlarged and schematic. This is not NASA's fly-through mesh, a tomographic reconstruction, or a measured 3D density map.",
        "processing": {"script": "scripts/build_orion_model.py", "source_image_sha256": hashlib.sha256(args.reference_image.read_bytes()).hexdigest(),
                       "image_field_span_ly": IMAGE_SPAN_LY, "reference_span_ly": REGION_SPAN_LY,
                       "cloud_points": point_count, "depth_semantics": "inferred illustration"}
    }
    write_json(args.output_dir / "entry.json", entry)
    print(f"{path}: {len(model):,} bytes; {point_count:,} gas samples")


if __name__ == "__main__":
    main()
