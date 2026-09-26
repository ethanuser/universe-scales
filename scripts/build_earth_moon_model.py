#!/usr/bin/env python3
"""Build calibrated distance diagrams from the existing NASA sphere models."""

import copy
import json
from pathlib import Path

from fetch_model_assets import check_matches, inspect_glb, pack_glb, read_glb, sha, write_json


ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "content/visualizations/models"
REGISTRY = ROOT / "content/visualizations/models.json"
RADII_M = {"Earth": 6_371_000, "Moon": 1_737_500, "Sun": 695_700_000}
SOURCES = {"Earth": "nasa-earth", "Moon": "nasa-moon", "Sun": "nasa-sun"}
DIAGRAMS = (
    {
        "id": "nasa-earth-moon-distance",
        "match": "Earth-Moon Distance",
        "bodies": ("Earth", "Moon"),
        "distance_m": 384_400_000,
        "source": "https://science.nasa.gov/moon/by-the-numbers/",
        "note": "NASA Earth and Moon spheres at a mean center-to-center separation of 384,400 km, "
                "with their radii at the same scale. The white bracket's lines are tangent to the facing "
                "edges, so it spans the surface-to-surface gap (about 376,300 km), slightly less than the "
                "center distance. Lunar distance changes during its orbit; this idealized diagram is not "
                "a view from a particular date or phase.",
    },
    {
        "id": "nasa-sun-earth-au",
        "match": "Astronomical Unit",
        "bodies": ("Sun", "Earth"),
        "distance_m": 149_597_870_700,
        "source": "https://ssd.jpl.nasa.gov/faq.html",
        "note": "NASA Sun and Earth spheres separated by exactly one astronomical unit "
                "(149,597,870,700 m) center-to-center, using their approximate mean radii. At this scale "
                "Earth is far smaller than a pixel; its label and the bracket mark where it is. The "
                "bracket's lines are tangent to the facing edges, so it spans the surface-to-surface gap "
                "(about 0.995 au). The au is a defined unit close to, but not identical to, the varying "
                "Sun-Earth distance. This idealized diagram is not an orbital snapshot.",
    },
)


def add_sphere(target, binary, source_data, name, x, distance_m):
    source, payload = read_glb(source_data)
    if (source.get("extensionsUsed") or len(source["meshes"]) != 1
            or len(source["nodes"]) != 1 or source["nodes"][0].get("mesh") != 0):
        raise ValueError(f"Unexpected {name} source GLB layout")
    if any(key in source["nodes"][0] for key in ("matrix", "translation", "scale")):
        raise ValueError(f"{name} is not a centered unit sphere")

    binary_offset = len(binary)
    view_offset = len(target["bufferViews"])
    accessor_offset = len(target["accessors"])
    image_offset = len(target["images"])
    sampler_offset = len(target["samplers"])
    texture_offset = len(target["textures"])
    material_offset = len(target["materials"])
    mesh_offset = len(target["meshes"])
    binary.extend(payload)
    binary.extend(b"\0" * (-len(binary) % 4))

    for item in source["bufferViews"]:
        view = copy.deepcopy(item)
        view["buffer"] = 0
        view["byteOffset"] = view.get("byteOffset", 0) + binary_offset
        target["bufferViews"].append(view)
    for item in source["accessors"]:
        accessor = copy.deepcopy(item)
        accessor["bufferView"] += view_offset
        target["accessors"].append(accessor)
    for item in source.get("images", []):
        image = copy.deepcopy(item)
        image["bufferView"] += view_offset
        target["images"].append(image)
    target["samplers"].extend(copy.deepcopy(source.get("samplers", [])))
    for item in source.get("textures", []):
        texture = copy.deepcopy(item)
        texture["source"] += image_offset
        if "sampler" in texture:
            texture["sampler"] += sampler_offset
        target["textures"].append(texture)
    for item in source.get("materials", []):
        material = copy.deepcopy(item)
        slots = [material.get(key) for key in ("normalTexture", "occlusionTexture", "emissiveTexture")]
        pbr = material.get("pbrMetallicRoughness", {})
        slots.extend(pbr.get(key) for key in ("baseColorTexture", "metallicRoughnessTexture"))
        for slot in slots:
            if slot:
                slot["index"] += texture_offset
        target["materials"].append(material)
    for item in source["meshes"]:
        mesh = copy.deepcopy(item)
        for primitive in mesh["primitives"]:
            primitive["attributes"] = {key: value + accessor_offset
                                       for key, value in primitive["attributes"].items()}
            primitive["indices"] += accessor_offset
            if "material" in primitive:
                primitive["material"] += material_offset
        target["meshes"].append(mesh)
    node = {"name": name, "mesh": mesh_offset,
            "translation": [x, 0, 0], "scale": [RADII_M[name] / distance_m] * 3}
    if "rotation" in source["nodes"][0]:
        node["rotation"] = source["nodes"][0]["rotation"]
    target["nodes"].append(node)


def build_diagram(config, by_id):
    output_path = MODELS / f"{config['id']}.glb"
    document = {"asset": {"version": "2.0", "generator": "Universe Scales NASA Earth-Moon composite"},
                "scene": 0, "scenes": [{"nodes": [0, 1]}], "nodes": [], "meshes": [],
                "materials": [], "textures": [], "images": [], "samplers": [],
                "accessors": [], "bufferViews": []}
    binary = bytearray()
    source_info = []
    for name, x in zip(config["bodies"], (-0.5, 0.5)):
        source_model = by_id[SOURCES[name]]
        if source_model.get("normalized_radius") != 1:
            raise ValueError(f"{name} source radius changed")
        data = (ROOT / source_model["src"]).read_bytes()
        if sha(data) != source_model["sha256"]:
            raise ValueError(f"{name} source hash changed")
        add_sphere(document, binary, data, name, x, config["distance_m"])
        source_info.append({"id": source_model["id"], "sha256": sha(data),
                            "source": source_model["source"]})

    output = pack_glb(document, bytes(binary))
    if len(output) > 2_000_000:
        raise ValueError(f"{config['id']} exceeds the 2 MB budget")
    entry = {
        "id": config["id"],
        "source": config["source"],
        "author": "NASA; composite assembled by Universe Scales",
        "license": "U.S. public-domain NASA media; NASA usage guidelines apply (not CC0)",
        "license_url": "https://www.nasa.gov/nasa-brand-center/images-and-media/",
        "license_files": ["licenses/nasa-media-guidelines.html", "licenses/nasa-3d-resources.README.md"],
        "matches": {"length": [config["match"]]},
        "geometry": "mesh",
        "note": config["note"],
        "src": str(output_path.relative_to(ROOT)),
        # The renderer adds the tangent-line bracket and upright body labels.
        "presentation": {"reference_size": 1, "distance_bracket": {"bodies": list(config["bodies"])}},
        "processing": {"source_models": source_info, "center_distance_m": config["distance_m"],
                       "body_radii_m": {name: RADII_M[name] for name in config["bodies"]},
                       "operations": ["Retain NASA geometry and embedded textures",
                                      "Place sphere centers one reference distance apart"]},
        "volume_semantics": "not_applicable", "closed_volume_checked": False,
        **inspect_glb(output),
    }
    return output_path, output, entry


def build():
    registry = json.loads(REGISTRY.read_text())
    by_id = {model["id"]: model for model in registry["models"]}
    built = [build_diagram(config, by_id) for config in DIAGRAMS]
    ids = {entry["id"] for _, _, entry in built}
    updated = [model for model in registry["models"] if model["id"] not in ids]
    updated.extend(entry for _, _, entry in built)
    check_matches(updated)
    for output_path, output, _ in built:
        output_path.write_bytes(output)
        print(f"Built {output_path.name}: {len(output):,} bytes")
    registry["models"] = updated
    write_json(REGISTRY, registry)


if __name__ == "__main__":
    build()
