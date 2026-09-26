#!/usr/bin/env python3
"""Fetch licensed models, make self-contained GLBs, and verify exact-name matches.

Build:  python3 scripts/fetch_model_assets.py       (requires Pillow)
Subset: python3 scripts/fetch_model_assets.py --models coffee-mug soda-can cat ceiling-fan
Audit:  python3 scripts/fetch_model_assets.py --verify (standard library only)

Only writes content/visualizations/models/** and content/visualizations/models.json.
Source geometry is downloaded, not procedurally substituted. NASA's slightly
oblate bodies are explicitly adapted to unit spheres for analytic scale display.
"""

import argparse
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys
import time
import zipfile
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "content/visualizations/models"
REGISTRY = DIRECTORY.parent / "models.json"
NASA = "https://assets.science.nasa.gov/content/dam/science/psd/solar/2023/09"
KHRONOS = "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main"
NASA_LICENSE = "https://www.nasa.gov/nasa-brand-center/images-and-media/"
POLY_API = "https://api.polyhaven.com"
USER_AGENT = "UniverseScales-AssetFetcher/1.0 (licensed educational 3D assets)"
DECODERS = {"KHR_draco_mesh_compression", "EXT_meshopt_compression", "KHR_texture_basisu"}
ARTIFACTS = {}
LOCK = {}
FETCHED = {}


def celestial(body, filename, length, area, volume):
    return {
        "id": f"nasa-{body}",
        "source": f"https://science.nasa.gov/resource/{body}-3d-model/",
        "download_url": f"{NASA}/{body[0]}/{filename}.glb",
        "author": "NASA Visualization Technology Applications and Development (VTAD)",
        "license": "U.S. public-domain NASA media; NASA usage guidelines apply (not CC0)",
        "license_url": NASA_LICENSE,
        "license_files": ["licenses/nasa-media-guidelines.html", "licenses/nasa-3d-resources.README.md"],
        "matches": {"length": length, "area": [area], "volume": volume},
        "geometry": "sphere",
        "note": "NASA-authored topology, UVs and materials; adapted to a centered unit sphere. "
                "An idealized spherical scale model, not a geodetic/oblateness or terrain model. "
                "Use r=(3V/(4*pi))^(1/3) for volume or r=sqrt(A/(4*pi)) for total surface area. "
                "Texture resolution reduced to at most 1024 pixels; see processing metadata.",
    }


MODELS = [
    celestial("earth", "Earth_1_12756", ["Earth Diameter"], "Earth surface area", ["Earth volume"]),
    celestial("moon", "Moon_1_3474", [], "Moon surface area", ["Moon volume"]),
    celestial("jupiter", "Jupiter_1_142984", ["Jupiter Diameter"], "Jupiter surface area", []),
    celestial("sun", "Sun_1_1391000", ["Sun Diameter"], "Sun surface area", ["Sun volume"]),
    {
        "id": "wine-bottle",
        "source": "https://polyhaven.com/a/wine_bottles_01",
        "download_url": "https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/wine_bottles_01/wine_bottles_01_1k.gltf",
        "author": "Rico Cilliers (modeling); Jurita Burger (graphic design); Poly Haven",
        "license": "CC0-1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "license_files": ["licenses/CC0-1.0.txt", "licenses/polyhaven-license.html"],
        "matches": {"length": [], "area": [], "volume": ["Wine bottle"]},
        "geometry": "mesh",
        "note": "One Bordeaux bottle extracted from Poly Haven Wine Bottles 01, with original "
                "1k textures and glass transmission. Capacity is not the enclosed glass/mesh volume. "
                "Closed volume has NOT been checked. Use the same cubic-linear equivalent approximation "
                "as other mesh proxies, not a claim of measured watertight volume.",
    },
    {
        "id": "rigged-human",
        "source": "https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/RiggedFigure",
        "download_url": f"{KHRONOS}/Models/RiggedFigure/glTF-Binary/RiggedFigure.glb",
        "author": "Cesium (2017), distributed by Khronos Group",
        "license": "CC-BY-4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "license_files": ["licenses/CC-BY-4.0.txt", "licenses/rigged-human.README.md", "licenses/rigged-human.metadata.json"],
        "matches": {"length": ["Human Height"], "area": [], "volume": ["Human body volume"]},
        "geometry": "mesh",
        "note": "Static bind-pose derivative of a low-poly human figure, not an anatomical scan or calibrated person. "
                "Credit Cesium (2017), CC BY 4.0; adapted by Universe Scales. Skinning and animation "
                "removed; original bind-pose positions retained and transformed to Y-up. Use world bounds for height. "
                "Closed volume has NOT been checked. Use the same cubic-linear equivalent approximation "
                "as other mesh proxies; do not infer anatomical volume or skin area from this mesh.",
    },
]
MODELS[1]["source"] = "https://solarsystem.nasa.gov/resources/2366/earths-moon-3d-model/"
MODELS[1]["author"] = "NASA (individual model artist not identified in current asset metadata)"
MODELS[1]["note"] += " Legacy landing page is unavailable; the official NASA asset-host GLB remains available."
MODELS[3]["source"] = "https://science.nasa.gov/learn/heat/resource/sun-3d-model/"
MODELS[3]["author"] = "NASA (individual model artist not identified in current asset metadata)"
MODELS[3]["note"] += " Current landing page links USDZ only; the corresponding official GLB remains available."

# Only actual body rotation, never orbital motion around another body.
BODY_ROTATION = {"nasa-earth": "Earth rotation", "nasa-jupiter": "Jupiter rotation"}
for model in MODELS:
    if model["id"] in BODY_ROTATION:
        model["matches"]["angular-velocity"] = [BODY_ROTATION[model["id"]]]

KENNEY_FOOD = "https://kenney.nl/media/pages/assets/food-kit/83086fa91c-1719418518/kenney_food-kit.zip"
KENNEY_CAR = "https://kenney.nl/media/pages/assets/car-kit/1a312ec241-1775131960/kenney_car-kit.zip"
KENNEY_TRAIN = "https://kenney.nl/media/pages/assets/train-kit/cf8521d625-1727040883/kenney_train-kit.zip"
KENNEY_INDUSTRIAL = "https://kenney.nl/media/pages/assets/city-kit-industrial/0ec35b139d-1788171848/kenney_city-kit-industrial_2.0.zip"
UNITS_NOTE = ("Model units are dimensionless display units: centered world AABB, Y-up, longest world AABB axis = 1. "
              "For Length the renderer assumes the dataset length corresponds to the longest axis, not a measured anatomical landmark. "
              "For Volume use cubic-linear equivalent scaling only; capacity/envelope is not measured mesh volume.")


def extra_model(identifier, source, author, matches, note, **options):
    return {
        "id": identifier, "source": source, "author": author, "license": "CC0-1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "license_files": ["licenses/CC0-1.0.txt", *options.pop("license_files", [])],
        "matches": matches, "geometry": "mesh", "note": note,
        "model_units_note": UNITS_NOTE, **options,
    }


ADDITIONS = [
    extra_model("coffee-mug", "https://kenney.nl/assets/food-kit", "Kenney",
                {"volume": ["Coffee mug"]},
                "Stylized empty ceramic handled cup (source cup.glb), not the pack's wooden tankard mug.glb. "
                "Representative coffee mug, not a calibrated 250 mL vessel; no liquid is modeled.",
                download_url=KENNEY_FOOD, archive_member="Models/GLB format/cup.glb",
                license_files=["licenses/kenney-food-kit.txt"]),
    extra_model("soda-can", "https://kenney.nl/assets/food-kit", "Kenney",
                {"volume": ["Soda can", "Soda can volume"]},
                "Stylized actual soda can with pull-tab top (source soda-can.glb), not a food can or water bottle. "
                "Nominal beverage capacity is not the enclosed mesh volume.",
                download_url=KENNEY_FOOD, archive_member="Models/GLB format/soda-can.glb",
                license_files=["licenses/kenney-food-kit.txt"]),
    extra_model("wine-glass", "https://kenney.nl/assets/food-kit", "Kenney",
                {"volume": ["Wine glass volume"]},
                "Stylized stemmed wine glass (source glass-wine.glb). The dataset value is representative "
                "liquid capacity, not the volume of the glass material or its exact polygon interior.",
                download_url=KENNEY_FOOD, archive_member="Models/GLB format/glass-wine.glb",
                license_files=["licenses/kenney-food-kit.txt"]),
    extra_model("family-car", "https://kenney.nl/assets/car-kit", "Kenney",
                {"volume": ["Family car envelope volume"]},
                "Stylized four-wheel sedan (source sedan.glb), not a particular manufacturer or calibrated vehicle. "
                "Envelope volume is not cabin capacity, material volume, or a measured watertight mesh volume.",
                download_url=KENNEY_CAR, archive_member="Models/GLB format/sedan.glb",
                license_files=["licenses/kenney-car-kit.txt"]),
    extra_model("bucket", "https://polyhaven.com/a/wooden_bucket_02", "James Ray Cock; Poly Haven",
                {"volume": ["Bucket"]},
                "Actual open wooden bucket with metal bands and handles. Representative bucket, not a calibrated "
                "10 L container; hollow capacity is not solid wood/mesh volume.",
                polyhaven_id="wooden_bucket_02", license_files=["licenses/polyhaven-license.html"]),
    extra_model("freight-train-car", "https://kenney.nl/assets/train-kit", "Kenney",
                {"volume": ["Freight train car volume"]},
                "Stylized open-topped cargo railcar (source train-carriage-box.glb). The listed volume is a "
                "representative cargo-space volume, not the volume of the mesh or external railcar envelope.",
                download_url=KENNEY_TRAIN, archive_member="Models/GLB format/train-carriage-box.glb",
                license_files=["licenses/kenney-train-kit.txt"]),
    extra_model("shipping-container", "https://kenney.nl/assets/city-kit-industrial", "Kenney",
                {"volume": ["Shipping container", "Shipping container volume"]},
                "Stylized intermodal shipping container (source shipping-container-a.glb). The listed "
                "capacity is representative interior cargo space; the visible exterior is not an exact "
                "dimensional survey or a watertight volume measurement.",
                download_url=KENNEY_INDUSTRIAL,
                archive_member="Models/GLB format/shipping-container-a.glb",
                license_files=["licenses/kenney-industrial-kit.txt"]),
    extra_model("cat", "https://poly.pizza/m/qKICY6xla2", "Quaternius (creator); Poly Pizza (distributor)",
                {"length": ["Cat Length"]},
                "Stylized standing domestic cat, static bind-pose derivative. Includes its tail; longest-axis "
                "normalization is a display approximation, not a measured nose-to-rump anatomical length. "
                "Do not claim this is a scan, a specific breed, or a calibrated animal.",
                download_url="https://static.poly.pizza/67f5e3fe-37ee-4c86-95c8-d269d8c9f8ba.glb",
                license_files=["sources/cat.html", "licenses/quaternius-animals.html"],
                creator_source="https://quaternius.com/packs/ultimateanimatedanimals.html"),
    extra_model("ceiling-fan", "https://polyhaven.com/a/ceiling_fan", "Ulan Cabanilla; Poly Haven",
                {"angular-velocity": ["Ceiling fan"]},
                "Actual ceiling fan with separate fixture and blades. Animate only ceiling_fan_blades about its "
                "local +Y axis; do not rotate the fixture, light, or normalization root. No animation clip is needed. "
                "The same exact name covers both dataset Ceiling fan observations; use each observation's speed.",
                polyhaven_id="ceiling_fan", license_files=["licenses/polyhaven-license.html"]),
]
for model in ADDITIONS:
    if "polyhaven_id" in model:
        slug = model["polyhaven_id"]
        model["download_url"] = f"https://dl.polyhaven.org/file/ph-assets/Models/gltf/1k/{slug}/{slug}_1k.gltf"
MODELS.extend(ADDITIONS)
# Keep interrupted car/bucket definitions available, but outside the bounded build.
DEFAULT_MODEL_IDS = {m["id"] for m in MODELS} - {"family-car", "bucket"}

SUPPORT = {
    "licenses/nasa-media-guidelines.html": NASA_LICENSE,
    "licenses/nasa-3d-resources.README.md": "https://raw.githubusercontent.com/nasa/NASA-3D-Resources/master/README.md",
    "licenses/CC-BY-4.0.txt": f"{KHRONOS}/LICENSES/CC-BY-4.0.txt",
    "licenses/CC0-1.0.txt": f"{KHRONOS}/LICENSES/CC0-1.0.txt",
    "licenses/rigged-human.README.md": f"{KHRONOS}/Models/RiggedFigure/README.md",
    "licenses/rigged-human.metadata.json": f"{KHRONOS}/Models/RiggedFigure/metadata.json",
    "licenses/polyhaven-license.html": "https://polyhaven.com/license",
    "sources/wine-bottles-info.json": f"{POLY_API}/info/wine_bottles_01",
    "sources/wine-bottles-files.json": f"{POLY_API}/files/wine_bottles_01",
    "sources/nasa-earth.html": MODELS[0]["source"],
    "sources/nasa-jupiter.html": MODELS[2]["source"],
    "sources/nasa-sun.html": MODELS[3]["source"],
}
for model in ADDITIONS:
    SUPPORT[f"sources/{model['id']}.html"] = model["source"]
    if "polyhaven_id" in model:
        for endpoint in ("info", "files"):
            SUPPORT[f"sources/{model['id']}-{endpoint}.json"] = f"{POLY_API}/{endpoint}/{model['polyhaven_id']}"
SUPPORT["licenses/quaternius-animals.html"] = "https://quaternius.com/packs/ultimateanimatedanimals.html"

GAPS = [
    {"status": "no_dataset_entry",
     "note": "No Jupiter volume or Moon diameter item exists in the current exports. "
             "Earth-Moon Distance is not a Moon diameter; Earth's oceans is not Earth volume. "
             "Human skin area is deliberately not matched to an uncalibrated figure."},
    {"status": "source_page_unavailable",
     "source": "https://science.nasa.gov/resource/earths-moon-3d-model/",
     "note": "HTTP 404, as is /resource/moon-3d-model/. Official Moon_1_3474.glb succeeded. "
             "Newer SVS alternatives at https://svs.gsfc.nasa.gov/14959/ were larger "
             "(13.2 MB plain Moon; 6.9 MB grid-overlay version; larger terrain versions)."},
    {"status": "source_format_link_missing",
     "source": MODELS[3]["source"],
     "note": "Sun landing page exposes USDZ, not GLB. Corresponding NASA-hosted GLB returned HTTP 200 "
             "and was downloaded and validated; no USDZ conversion is required."},
    {"status": "deferred_bounded_task",
     "matches": {"volume": ["Bucket", "Family car envelope volume"]},
     "note": "Prior source definitions preserved in the fetch script, but not downloaded or validated in this bounded task."},
    {"status": "not_reviewed_in_bounded_task",
     "matches": {"length": ["Blue Whale", "Ant", "Grain of Sand"],
                 "volume": ["Grain of sand volume", "Bathtub", "Bathtub volume"]},
     "note": "No models delivered or licensing/identity claims made for these candidates. No generic whale, rock, or other substitute was used."},
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def download(url, md5=None, pinned=False):
    for attempt in range(3):
        try:
            if url in FETCHED:
                data = FETCHED[url]
            else:
                request = Request(url, headers={"User-Agent": USER_AGENT})
                with urlopen(request, timeout=90) as response:
                    data = response.read(100_000_001)
            break
        except OSError:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
    if len(data) > 100_000_000:
        raise ValueError(f"Asset exceeds the 100 MB limit: {url}")
    if md5 and hashlib.md5(data).hexdigest() != md5:
        raise ValueError(f"Upstream MD5 mismatch: {url}")
    digest = sha(data)
    if pinned and url in LOCK and digest != LOCK[url]["sha256"]:
        raise ValueError(f"Upstream asset changed: {url}. Review it before --update-lock.")
    ARTIFACTS[url] = {"url": url, "sha256": digest, "bytes": len(data), "pinned": pinned}
    FETCHED[url] = data
    return data


def read_glb(data):
    if len(data) < 28 or struct.unpack_from("<4sII", data) != (b"glTF", 2, len(data)):
        raise ValueError("Not a complete GLB 2.0 file")
    offset = 12
    chunks = []
    while offset < len(data):
        size, kind = struct.unpack_from("<I4s", data, offset)
        if size % 4 or offset + 8 + size > len(data):
            raise ValueError("Invalid GLB chunk")
        chunks.append((kind, data[offset + 8:offset + 8 + size]))
        offset += 8 + size
    if len(chunks) != 2 or [part[0] for part in chunks] != [b"JSON", b"BIN\0"]:
        raise ValueError("Expected one JSON and one BIN chunk")
    return json.loads(chunks[0][1]), chunks[1][1]


def pack_glb(document, binary):
    for mesh in document.get("meshes", []):
        for primitive in mesh["primitives"]:
            for index in primitive["attributes"].values():
                document["bufferViews"][document["accessors"][index]["bufferView"]]["target"] = 34962
            document["bufferViews"][document["accessors"][primitive["indices"]]["bufferView"]]["target"] = 34963
    document["buffers"] = [{"byteLength": len(binary)}]
    text = json.dumps(document, separators=(",", ":"), ensure_ascii=True).encode()
    text += b" " * (-len(text) % 4)
    binary += b"\0" * (-len(binary) % 4)
    return (struct.pack("<4sII", b"glTF", 2, 28 + len(text) + len(binary))
            + struct.pack("<I4s", len(text), b"JSON") + text
            + struct.pack("<I4s", len(binary), b"BIN\0") + binary)


def view_bytes(document, binary, index):
    view = document["bufferViews"][index]
    start = view.get("byteOffset", 0)
    return binary[start:start + view["byteLength"]]


def pack_views(document, payloads):
    binary = bytearray()
    for view, payload in zip(document["bufferViews"], payloads):
        binary.extend(b"\0" * (-len(binary) % 4))
        view.update(buffer=0, byteOffset=len(binary), byteLength=len(payload))
        binary.extend(payload)
    return bytes(binary)


def sphere_derivative(data):
    from PIL import Image

    document, binary = read_glb(data)
    payloads = [bytearray(view_bytes(document, binary, i)) for i in range(len(document["bufferViews"]))]
    node = document["nodes"][0]
    primitive = document["meshes"][node["mesh"]]["primitives"][0]
    position = document["accessors"][primitive["attributes"]["POSITION"]]
    normal = document["accessors"][primitive["attributes"]["NORMAL"]]
    original_bounds = {"min": position["min"], "max": position["max"], "node": copy.deepcopy(node)}
    if len(document["nodes"]) != 1 or position["componentType"] != 5126:
        raise ValueError("Unexpected NASA geometry; adaptation needs review")
    vertices = []
    for i in range(position["count"]):
        p_view = document["bufferViews"][position["bufferView"]]
        p_offset = position.get("byteOffset", 0) + i * p_view.get("byteStride", 12)
        xyz = struct.unpack_from("<3f", payloads[position["bufferView"]], p_offset)
        radius = math.sqrt(sum(value * value for value in xyz))
        unit = tuple(value / radius for value in xyz)
        struct.pack_into("<3f", payloads[position["bufferView"]], p_offset, *unit)
        vertices.append(struct.unpack_from("<3f", payloads[position["bufferView"]], p_offset))
        n_view = document["bufferViews"][normal["bufferView"]]
        n_offset = normal.get("byteOffset", 0) + i * n_view.get("byteStride", 12)
        struct.pack_into("<3f", payloads[normal["bufferView"]], n_offset, *unit)
    position["min"] = [min(p[axis] for p in vertices) for axis in range(3)]
    position["max"] = [max(p[axis] for p in vertices) for axis in range(3)]
    node.pop("scale", None)
    node.pop("translation", None)
    # Preserve the Sun's original texture orientation, but not its 1000x scale.
    textures = []
    for item in document.get("images", []):
        index = item["bufferView"]
        with Image.open(io.BytesIO(payloads[index])) as source:
            source.load()
            original_size = list(source.size)
            image = source.convert("RGB")
            image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            is_normal = "norm" in item.get("name", "").lower()
            if is_normal:
                image.save(output, format="PNG", optimize=True)
                item["mimeType"] = "image/png"
            else:
                image.save(output, format="JPEG", quality=88, subsampling=0, optimize=True)
                item["mimeType"] = "image/jpeg"
            payloads[index] = output.getvalue()
            textures.append({"name": item.get("name"), "original_size": original_size,
                             "size": list(image.size), "mime_type": item["mimeType"]})
    from texture_padding import OPERATION as PAD_OPERATION, pad_glb  # local: texture_padding imports this module
    padded, _ = pad_glb(pack_glb(document, pack_views(document, payloads)))
    return padded, {
        "operations": ["Normalize source POSITION and NORMAL vectors to unit radius; retain topology/UVs/materials",
                       "Remove source node scale; preserve source node rotation",
                       "Resize textures to <=1024px; JPEG color/emission quality 88, PNG normals",
                       PAD_OPERATION],
        "source_bounds": original_bounds, "textures": textures,
    }


def compact(document, key, indices):
    indices = sorted(set(indices))
    mapping = {old: new for new, old in enumerate(indices)}
    document[key] = [document[key][i] for i in indices]
    return mapping


def texture_infos(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.endswith("Texture") and isinstance(child, dict) and "index" in child:
                yield child
            else:
                yield from texture_infos(child)
    elif isinstance(value, list):
        for child in value:
            yield from texture_infos(child)


def wine_derivative(data, files):
    document = json.loads(data)
    node = next(n for n in document["nodes"] if n["name"] == "wine_bottles_01_bordeaux")
    document["meshes"] = [document["meshes"][node["mesh"]]]
    document["nodes"] = [{"name": node["name"], "mesh": 0}]
    document["scenes"] = [{"name": "Single Bordeaux wine bottle", "nodes": [0]}]
    document["scene"] = 0
    primitives = document["meshes"][0]["primitives"]
    mapping = compact(document, "materials", [p["material"] for p in primitives])
    for primitive in primitives:
        primitive["material"] = mapping[primitive["material"]]
    infos = list(texture_infos(document["materials"]))
    mapping = compact(document, "textures", [info["index"] for info in infos])
    for info in infos:
        info["index"] = mapping[info["index"]]
    mapping = compact(document, "images", [t["source"] for t in document["textures"]])
    for texture in document["textures"]:
        texture["source"] = mapping[texture["source"]]
    accessor_indices = []
    for primitive in primitives:
        accessor_indices.extend(primitive["attributes"].values())
        accessor_indices.append(primitive["indices"])
    mapping = compact(document, "accessors", accessor_indices)
    for primitive in primitives:
        primitive["attributes"] = {key: mapping[value] for key, value in primitive["attributes"].items()}
        primitive["indices"] = mapping[primitive["indices"]]
    bundle = files["gltf"]["1k"]["gltf"]
    includes = bundle["include"]
    buffer = includes[document["buffers"][0]["uri"]]
    binary = download(buffer["url"], buffer["md5"], pinned=True)
    mapping = compact(document, "bufferViews", [a["bufferView"] for a in document["accessors"]])
    for accessor in document["accessors"]:
        accessor["bufferView"] = mapping[accessor["bufferView"]]
    payloads = [view_bytes(document, binary, i) for i in range(len(document["bufferViews"]))]
    image_cache = {}
    for image in document["images"]:
        uri = image.pop("uri")
        if uri not in image_cache:
            resource = includes[uri]
            image_cache[uri] = download(resource["url"], resource["md5"], pinned=True)
        image["bufferView"] = len(payloads)
        document["bufferViews"].append({"buffer": 0})
        payloads.append(image_cache[uri])
    return pack_glb(document, pack_views(document, payloads)), {
        "operations": ["Extract only wine_bottles_01_bordeaux; remove collection translation",
                       "Prune unused meshes/materials/textures/accessors; embed original 1k JPEGs and binary data"],
        "selected_source_node": "wine_bottles_01_bordeaux",
    }


def human_derivative(data):
    document, original = read_glb(data)
    binary = bytearray(original)
    primitives = document["meshes"][0]["primitives"]
    for primitive in primitives:
        for semantic in ("JOINTS_0", "WEIGHTS_0"):
            primitive["attributes"].pop(semantic)
        for semantic in ("POSITION", "NORMAL"):
            accessor = document["accessors"][primitive["attributes"][semantic]]
            view = document["bufferViews"][accessor["bufferView"]]
            values = []
            for i in range(accessor["count"]):
                offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0) + i * view.get("byteStride", 12)
                x, y, z = struct.unpack_from("<3f", binary, offset)
                # Bake the source Z_UP root's axis conversion, not its animated pose.
                struct.pack_into("<3f", binary, offset, x, z, -y)
                values.append((x, z, -y))
            if "min" in accessor:
                accessor["min"] = [min(v[axis] for v in values) for axis in range(3)]
                accessor["max"] = [max(v[axis] for v in values) for axis in range(3)]
    document["nodes"] = [{"mesh": 0, "name": "Human figure, static bind pose, Y-up"}]
    document["scenes"] = [{"nodes": [0]}]
    document["scene"] = 0
    document.pop("skins", None)
    document.pop("animations", None)
    mapping = compact(document, "accessors", [index for p in primitives
                                              for index in [p["indices"], *p["attributes"].values()]])
    for primitive in primitives:
        primitive["indices"] = mapping[primitive["indices"]]
        primitive["attributes"] = {key: mapping[value] for key, value in primitive["attributes"].items()}
    mapping = compact(document, "bufferViews", [a["bufferView"] for a in document["accessors"]])
    for accessor in document["accessors"]:
        accessor["bufferView"] = mapping[accessor["bufferView"]]
    payloads = [view_bytes(document, binary, i) for i in range(len(document["bufferViews"]))]
    document["asset"]["copyright"] = "Cesium (2017), CC BY 4.0. Static bind-pose adaptation by Universe Scales."
    return pack_glb(document, pack_views(document, payloads)), {
        "operations": ["Remove animation, skin and joint attributes; retain original bind-pose geometry",
                       "Bake source Z_UP axis conversion into POSITION/NORMAL vectors; prune unused resources"],
    }


IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def matrix_product(a, b):
    # glTF matrices are column-major, including matrix accessors.
    return [sum(a[k * 4 + row] * b[col * 4 + k] for k in range(4))
            for col in range(4) for row in range(4)]


def node_matrix(node):
    if "matrix" in node:
        return node["matrix"]
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    sx, sy, sz = node.get("scale", [1, 1, 1])
    tx, ty, tz = node.get("translation", [0, 0, 0])
    return [(1-2*(y*y+z*z))*sx, 2*(x*y+z*w)*sx, 2*(x*z-y*w)*sx, 0,
            2*(x*y-z*w)*sy, (1-2*(x*x+z*z))*sy, 2*(y*z+x*w)*sy, 0,
            2*(x*z+y*w)*sz, 2*(y*z-x*w)*sz, (1-2*(x*x+y*y))*sz, 0,
            tx, ty, tz, 1]


def world_matrices(document):
    result = {}

    def visit(index, parent):
        if index in result:
            raise ValueError("Scene contains a repeated node or cycle")
        node = document["nodes"][index]
        result[index] = matrix_product(parent, node_matrix(node))
        for child in node.get("children", []):
            visit(child, result[index])

    for index in document["scenes"][document.get("scene", 0)]["nodes"]:
        visit(index, IDENTITY)
    return result


def float_vectors(document, binary, index, width=3):
    accessor = document["accessors"][index]
    if accessor["componentType"] != 5126 or "sparse" in accessor:
        raise ValueError("Expected dense floating-point accessor")
    view = document["bufferViews"][accessor["bufferView"]]
    for i in range(accessor["count"]):
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0) + i * view.get("byteStride", width * 4)
        yield struct.unpack_from(f"<{width}f", binary, offset)


def scene_bounds(document, binary):
    low, high = [math.inf] * 3, [-math.inf] * 3
    for index, matrix in world_matrices(document).items():
        node = document["nodes"][index]
        if "mesh" not in node:
            continue
        for primitive in document["meshes"][node["mesh"]]["primitives"]:
            for point in float_vectors(document, binary, primitive["attributes"]["POSITION"]):
                for axis in range(3):
                    value = sum(matrix[k*4+axis] * point[k] for k in range(3)) + matrix[12+axis]
                    if not math.isfinite(value):
                        raise ValueError("Non-finite world position")
                    low[axis], high[axis] = min(low[axis], value), max(high[axis], value)
    if not all(math.isfinite(v) for v in low + high):
        raise ValueError("Empty scene bounds")
    return {"min": low, "max": high}


def embed_images(document, binary, resolve):
    payloads = [view_bytes(document, binary, i) for i in range(len(document["bufferViews"]))]
    for image in document.get("images", []):
        if "uri" not in image:
            continue
        uri = image.pop("uri")
        payload = resolve(uri)
        image["mimeType"] = "image/png" if payload.startswith(b"\x89PNG\r\n\x1a\n") else "image/jpeg"
        image["bufferView"] = len(payloads)
        document["bufferViews"].append({"buffer": 0})
        payloads.append(payload)
    return pack_views(document, payloads)


def static_cat(document, binary):
    matrices = world_matrices(document)
    mesh_nodes = []
    for index, node in enumerate(document["nodes"]):
        if "mesh" not in node:
            continue
        skin = document["skins"][node["skin"]]
        inverse_binds = list(float_vectors(document, binary, skin["inverseBindMatrices"], 16))
        for joint, inverse_bind in zip(skin["joints"], inverse_binds):
            pose = matrix_product(matrices[joint], inverse_bind)
            if max(abs(a-b) for a, b in zip(pose, matrices[index])) > 0.001:
                raise ValueError("Cat is not in its bind pose; static conversion needs review")
        mesh_nodes.append({"mesh": node["mesh"], "name": node["name"], "matrix": matrices[index]})
    document["nodes"] = mesh_nodes
    document["scenes"] = [{"nodes": list(range(len(mesh_nodes)))}]
    document["scene"] = 0
    document.pop("skins")
    document.pop("animations", None)
    primitives = [p for mesh in document["meshes"] for p in mesh["primitives"]]
    for primitive in primitives:
        primitive["attributes"] = {k: v for k, v in primitive["attributes"].items()
                                    if not k.startswith(("JOINTS_", "WEIGHTS_"))}
    mapping = compact(document, "accessors", [a for p in primitives for a in [p["indices"], *p["attributes"].values()]])
    for primitive in primitives:
        primitive["indices"] = mapping[primitive["indices"]]
        primitive["attributes"] = {k: mapping[v] for k, v in primitive["attributes"].items()}
    mapping = compact(document, "bufferViews", [a["bufferView"] for a in document["accessors"]]
                      + [i["bufferView"] for i in document.get("images", [])])
    payloads = [view_bytes(document, binary, i) for i in range(len(document["bufferViews"]))]
    for item in document["accessors"] + document.get("images", []):
        item["bufferView"] = mapping[item["bufferView"]]
    return pack_views(document, payloads)


def normalize_scene(document, binary):
    bounds = scene_bounds(document, binary)
    extent = max(hi-lo for lo, hi in zip(bounds["min"], bounds["max"]))
    if extent <= 0:
        raise ValueError("Degenerate model bounds")
    center = [(lo+hi)/2 for lo, hi in zip(bounds["min"], bounds["max"])]
    roots = document["scenes"][document.get("scene", 0)]["nodes"]
    root = {"name": "display_normalization", "children": roots,
            "scale": [1/extent]*3, "translation": [-v/extent for v in center]}
    document["scenes"] = [{"nodes": [len(document["nodes"])]}]
    document["scene"] = 0
    document["nodes"].append(root)
    return {"source_bounds": bounds, "source_longest_extent": extent,
            "center": center, "normalized_longest_extent": 1, "up_axis": "+Y",
            "world_bounds": scene_bounds(document, binary)}


def additional_derivative(spec, data, support, outputs):
    details = {}
    if "archive_member" in spec:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            member = spec["archive_member"]
            source = archive.read(member)
            document, binary = read_glb(source)
            binary = embed_images(document, binary, lambda uri: archive.read(f"Models/GLB format/{uri}"))
            license_path = spec["license_files"][1]
            outputs[str(DIRECTORY / license_path)] = archive.read("License.txt")
            preview = f"Previews/{Path(member).stem}.png"
            outputs[str(DIRECTORY / f"sources/{spec['id']}-preview.png")] = archive.read(preview)
            details.update(archive_member=member, member_sha256=sha(source), member_bytes=len(source),
                           archive_license_sha256=sha(archive.read("License.txt")))
    elif "polyhaven_id" in spec:
        bundle = json.loads(support[f"sources/{spec['id']}-files.json"])["gltf"]["1k"]["gltf"]
        if hashlib.md5(data).hexdigest() != bundle["md5"] or bundle["url"] != spec["download_url"]:
            raise ValueError("Poly Haven source manifest mismatch")
        document = json.loads(data)
        if len(document["buffers"]) != 1:
            raise ValueError("Expected one source buffer")

        def resolve(uri):
            resource = bundle["include"][uri]
            return download(resource["url"], resource["md5"], pinned=True)

        binary = resolve(document["buffers"][0]["uri"])
        binary = embed_images(document, binary, resolve)
        outputs[str(DIRECTORY / f"sources/{spec['id']}.gltf")] = data
    else:
        document, binary = read_glb(data)
        binary = static_cat(document, binary)
        details["static_pose"] = "Bind pose verified against joint world matrices and inverse bind matrices; animation/skin removed"
    normalization = normalize_scene(document, binary)
    if spec["id"] == "ceiling-fan":
        blades = next(i for i, n in enumerate(document["nodes"]) if n["name"] == "ceiling_fan_blades")
        fixture = next(i for i, n in enumerate(document["nodes"]) if n["name"] == "ceiling_fan")
        if node_matrix(document["nodes"][blades]) != IDENTITY:
            raise ValueError("Fan blade pivot changed; rotation contract needs review")
        details["motion"] = {
            "type": "node_rotation", "rotating_node": "ceiling_fan_blades", "rotating_node_index": blades,
            "stationary_nodes": ["ceiling_fan"], "stationary_node_indices": [fixture],
            "axis_local": [0, 1, 0], "pivot_local": [0, 0, 0],
            "pivot_normalized_world": document["nodes"][-1]["translation"],
            "orientation": "Y-up hanging fixture; blades sweep the XZ plane. +Y points toward the ceiling. "
                           "Pivot may lie above the blades anywhere on the vertical spindle axis.",
            "angle_units": "radians", "speed_units": "radians per second",
            "integration": "Set bladeNode.rotation.y = theta0 + omega * elapsedSeconds. "
                           "Rotate only the named child, never scene/root/fixture. Positive follows right-hand rule; "
                           "dataset gives speed magnitude, not a measured direction. View obliquely or from below.",
        }
    return pack_glb(document, binary), {
        "operations": ["Retain authored geometry, materials, UVs and Y-up orientation; embed all resources",
                       "Add uniform normalization parent; preserve local child transforms and fan spindle pivot"],
        "normalization": normalization, **details,
    }


def inspect_glb(data, sphere=False):
    document, binary = read_glb(data)
    if document["asset"]["version"] != "2.0":
        raise ValueError("Expected glTF 2.0")
    if any("uri" in item for key in ("images", "buffers") for item in document.get(key, [])):
        raise ValueError("External resources are not allowed")
    extensions = document.get("extensionsUsed", [])
    if DECODERS.intersection(extensions + document.get("extensionsRequired", [])):
        raise ValueError("Unexpected geometry/texture decoder requirement")
    declared = document["buffers"][0]["byteLength"]
    if not declared <= len(binary) <= declared + 3:
        raise ValueError("Invalid declared binary length")
    for view in document.get("bufferViews", []):
        if view["buffer"] != 0 or view.get("byteOffset", 0) + view["byteLength"] > declared:
            raise ValueError("Buffer view is out of bounds")
    primitives = [p for mesh in document["meshes"] for p in mesh["primitives"]]
    def triangle_count(primitive):
        accessor = primitive.get("indices", primitive["attributes"]["POSITION"])
        count = document["accessors"][accessor]["count"]
        mode = primitive.get("mode", 4)
        if mode == 4:
            return count // 3
        if mode in (5, 6):
            return max(0, count - 2)
        return 0
    if sphere:
        for primitive in primitives:
            accessor = document["accessors"][primitive["attributes"]["POSITION"]]
            view = document["bufferViews"][accessor["bufferView"]]
            for i in range(accessor["count"]):
                offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0) + i * view.get("byteStride", 12)
                xyz = struct.unpack_from("<3f", binary, offset)
                if abs(math.sqrt(sum(v * v for v in xyz)) - 1) > 1e-6:
                    raise ValueError("Sphere vertex is not at unit radius")
        for node in document["nodes"]:
            if "matrix" in node or node.get("scale", [1, 1, 1]) != [1, 1, 1]:
                raise ValueError("Sphere has a non-unit transform")
    return {
        "format": "glb", "gltf_version": "2.0", "bytes": len(data),
        "sha256": sha(data), "extensions_used": extensions,
        "extensions_required": document.get("extensionsRequired", []),
        "decompression_required": [], "external_resources": [],
        "mesh_count": len(document["meshes"]),
        "triangle_count": sum(triangle_count(p) for p in primitives),
        "animations": len(document.get("animations", [])), "skins": len(document.get("skins", [])),
    }


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n")


def check_matches(models):
    names = {dimension: {item["name"] for item in json.loads(
        (ROOT / f"exports/json/dimensions/{dimension}.json").read_text())["items"]}
        for dimension in {dimension for model in models for dimension in model["matches"]}}
    assigned = set()
    for model in models:
        for dimension, matches in model["matches"].items():
            for match in matches:
                if match not in names[dimension]:
                    raise ValueError(f"Not an exact dataset name: {dimension}/{match}")
                if (dimension, match) in assigned:
                    raise ValueError(f"Duplicate model match: {dimension}/{match}")
                assigned.add((dimension, match))
    return len(assigned)


def verify():
    registry = json.loads(REGISTRY.read_text())
    count = check_matches(registry["models"])
    for model in registry["models"]:
        data = (ROOT / model["src"]).read_bytes()
        actual = inspect_glb(data, model["geometry"] == "sphere")
        for key in actual:
            if model[key] != actual[key]:
                raise ValueError(f"{model['id']}: stale {key}")
        normalization = model.get("processing", {}).get("normalization")
        if normalization:
            bounds = scene_bounds(*read_glb(data))
            if abs(max(hi-lo for lo, hi in zip(bounds["min"], bounds["max"])) - 1) > 1e-6:
                raise ValueError(f"{model['id']}: non-unit display bounds")
            if any(abs(lo+hi) > 1e-6 for lo, hi in zip(bounds["min"], bounds["max"])):
                raise ValueError(f"{model['id']}: off-center display bounds")
        for relative in model["license_files"]:
            if not (DIRECTORY / relative).is_file():
                raise ValueError(f"Missing license: {relative}")
        print(f"OK {model['id']}: {len(data):,} bytes; {actual['triangle_count']:,} triangles; no decoder")
    lock = json.loads((DIRECTORY / "sources/downloads.json").read_text())
    for artifact in lock["artifacts"]:
        if "local_path" in artifact:
            if sha((DIRECTORY / artifact["local_path"]).read_bytes()) != artifact["sha256"]:
                raise ValueError(f"Modified source/license record: {artifact['local_path']}")
    for artifact in lock.get("local_files", []):
        data = (DIRECTORY / artifact["path"]).read_bytes()
        if sha(data) != artifact["sha256"] or len(data) != artifact["bytes"]:
            raise ValueError(f"Modified provenance record: {artifact['path']}")
    print(f"Verified {len(registry['models'])} self-contained GLBs and {count} exact-name matches.")


def build(update_lock=False, model_ids=None):
    import PIL

    selected_ids = set(model_ids) if model_ids else DEFAULT_MODEL_IDS
    specs = [model for model in MODELS if model["id"] in selected_ids]
    if selected_ids - {model["id"] for model in specs}:
        raise ValueError("Unknown model ID")
    existing = json.loads(REGISTRY.read_text()) if REGISTRY.exists() else {"models": []}
    preserved = [model for model in existing["models"] if model["id"] not in selected_ids]
    for model in preserved:
        if model["id"] in BODY_ROTATION:
            model["matches"]["angular-velocity"] = [BODY_ROTATION[model["id"]]]
    check_matches(preserved + specs)
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    lock_path = DIRECTORY / "sources/downloads.json"
    old_lock = json.loads(lock_path.read_text()) if lock_path.exists() else {"artifacts": []}
    ARTIFACTS.update({a["url"]: a for a in old_lock["artifacts"]})
    if not update_lock:
        LOCK.update({a["url"]: a for a in old_lock["artifacts"] if a["pinned"]})
    needed = {path for spec in specs for path in spec["license_files"]}
    needed.update(path for path in SUPPORT if any(
        path.startswith(f"sources/{spec['id']}") for spec in specs))
    if "wine-bottle" in selected_ids:
        needed.update({"sources/wine-bottles-info.json", "sources/wine-bottles-files.json"})
    support = {}
    outputs = {}
    for path, url in SUPPORT.items():
        if path not in needed:
            continue
        target = DIRECTORY / path
        record = ARTIFACTS.get(url, {})
        if target.exists() and not update_lock and sha(target.read_bytes()) == record.get("sha256"):
            data = target.read_bytes()
        else:
            print(f"Fetching provenance {path}...", flush=True)
            data = download(url)
        support[path] = data
        outputs[str(target)] = data
        ARTIFACTS[url]["local_path"] = path
    result = preserved
    # Build everything in memory before replacing the runtime assets/registry.
    for spec in specs:
        print(f"Fetching {spec['id']}...", flush=True)
        data = download(spec["download_url"], pinned=True)
        source_sha = sha(data)
        source_bytes = len(data)
        if spec["geometry"] == "sphere":
            output, processing = sphere_derivative(data)
        elif spec["id"] == "wine-bottle":
            files = json.loads(support["sources/wine-bottles-files.json"])
            if hashlib.md5(data).hexdigest() != files["gltf"]["1k"]["gltf"]["md5"]:
                raise ValueError("Wine bottle source manifest checksum mismatch")
            output, processing = wine_derivative(data, files)
            outputs[str(DIRECTORY / "sources/wine-bottles.gltf")] = data
            ARTIFACTS[spec["download_url"]]["local_path"] = "sources/wine-bottles.gltf"
        elif spec["id"] == "rigged-human":
            output, processing = human_derivative(data)
        else:
            output, processing = additional_derivative(spec, data, support, outputs)
            if "polyhaven_id" in spec:
                ARTIFACTS[spec["download_url"]]["local_path"] = f"sources/{spec['id']}.gltf"
        entry = {**spec, "src": f"content/visualizations/models/{spec['id']}.glb",
                 **inspect_glb(output, spec["geometry"] == "sphere"),
                 "source_sha256": source_sha, "source_bytes": source_bytes,
                 "processing": processing,
                 "volume_semantics": "analytic_sphere" if spec["geometry"] == "sphere" else "cubic_linear_equivalent_approximation",
                 "closed_volume_checked": False}
        if spec["geometry"] == "sphere":
            entry["normalized_radius"] = 1
        outputs[entry["src"]] = output
        result.append(entry)
    for path, data in outputs.items():
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    local_files = {a["path"]: a for a in old_lock.get("local_files", [])}
    for path, data in outputs.items():
        relative = str((ROOT / path).relative_to(DIRECTORY))
        if relative.startswith(("sources/", "licenses/")):
            local_files[relative] = {"path": relative, "sha256": sha(data), "bytes": len(data)}
    write_json(lock_path, {"schema_version": 1, "artifacts": list(ARTIFACTS.values()),
                           "local_files": list(local_files.values())})
    # Preserve unrelated prior gap records and remove exact names now covered by
    # either this builder or supplementary importers.
    gaps = copy.deepcopy(GAPS)
    covered = {(dimension, name) for model in result for dimension, names in model["matches"].items() for name in names}
    for gap in existing.get("coverage_gaps", []):
        matches = {(dimension, name) for dimension, names in gap.get("matches", {}).items() for name in names}
        if gap not in gaps and not (matches and matches <= covered):
            gaps.append(gap)
    for gap in gaps:
        if "matches" in gap:
            gap["matches"] = {dimension: [name for name in names if (dimension, name) not in covered]
                              for dimension, names in gap["matches"].items()}
    gaps = [gap for gap in gaps if "matches" not in gap or any(gap["matches"].values())]
    build_info = {**existing.get("build", {}), "script": "scripts/fetch_model_assets.py",
                  "pillow_version": PIL.__version__,
                  "asset_lock": "content/visualizations/models/sources/downloads.json"}
    write_json(REGISTRY, {"schema_version": 1, "models": result, "coverage_gaps": gaps,
                         "build": build_info})
    verify()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Verify local GLBs and matches without downloads or writes")
    parser.add_argument("--update-lock", action="store_true", help="Accept reviewed upstream binary/texture changes")
    parser.add_argument("--models", nargs="+", choices=[m["id"] for m in MODELS],
                        help="Build only these IDs, preserving all other registered assets")
    args = parser.parse_args()
    try:
        verify() if args.verify else build(args.update_lock, args.models)
    except (OSError, ValueError, KeyError, struct.error, ImportError) as error:
        print(f"Model asset build failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
