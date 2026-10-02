#!/usr/bin/env python3
"""Build a diagrammatic Observable Universe model from a WMAP HEALPix map.

The map supplies observed CMB temperature anisotropy only. The shell is the
approximate present-distance last-scattering sphere; the larger wire sphere is
the particle horizon. The missing observer-facing cone is a viewing cutaway,
not a hole in the universe. Neither boundary represents a material wall or
density map.
"""

import argparse
import hashlib
import math
from pathlib import Path
import struct

from PIL import Image

from fetch_model_assets import pack_glb, write_json

LY_M = 9.4607304725808e15
CMB_RADIUS_LY = 45.6e9
OBSERVABLE_UNIVERSE_DIAMETER_M = 8.8e26
HORIZON_RADIUS_LY = OBSERVABLE_UNIVERSE_DIAMETER_M / (2 * LY_M)
REFERENCE_SIZE_LY = OBSERVABLE_UNIVERSE_DIAMETER_M / LY_M
TARGET_NSIDE = 64
DEFAULT_FITS = Path("/private/tmp/us-next-models/wmap_ilc_9yr_v5.fits")
SOURCE = "https://lambda.gsfc.nasa.gov/product/wmap/dr5/ilc_map_info.html"
DOWNLOAD = "https://lambda.gsfc.nasa.gov/data/map/dr5/dfp/ilc/wmap_ilc_9yr_v5.fits"
NASA_LICENSE = "https://www.nasa.gov/nasa-brand-center/images-and-media/"
PRIMARY_SIZE = 2880
FITS_DATA_OFFSET = 5760


def _cards(block):
    return [block[i:i + 80].decode("ascii") for i in range(0, len(block), 80)]


def _value(cards, key):
    prefix = f"{key:<8}="
    matches = [card for card in cards if card.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"FITS header must contain exactly one {key}")
    raw = matches[0][10:]
    return raw.split("/")[0].strip().strip("'").strip()


def read_healpix_fits(path):
    """Read the deliberately narrow WMAP binary-table FITS contract."""
    data = Path(path).read_bytes()
    if len(data) < FITS_DATA_OFFSET:
        raise ValueError("FITS file is truncated before its binary table")
    primary, table = _cards(data[:PRIMARY_SIZE]), _cards(data[PRIMARY_SIZE:FITS_DATA_OFFSET])
    if _value(primary, "SIMPLE") != "T" or _value(table, "XTENSION") != "BINTABLE":
        raise ValueError("Expected a primary HDU and one binary-table extension")
    if _value(table, "PIXTYPE") != "HEALPIX" or _value(table, "ORDERING") != "NESTED":
        raise ValueError("Expected HEALPIX NESTED ordering")
    coordinate_cards = [card for card in table if card.startswith("COORDSYS=")]
    if coordinate_cards and _value(table, "COORDSYS") != "G":
        raise ValueError("Expected Galactic-coordinate HEALPix pixels (COORDSYS='G')")
    if not coordinate_cards and (_value(primary, "TELESCOP") != "WMAP" or
                                 _value(primary, "OBJECT") != "ALL-SKY"):
        raise ValueError("Missing COORDSYS is accepted only for WMAP all-sky products")
    nside = int(_value(table, "NSIDE"))
    npix = int(_value(table, "NAXIS2"))
    row_bytes = int(_value(table, "NAXIS1"))
    if (_value(table, "NAXIS") != "2" or nside < 1 or nside & (nside - 1) or
            npix != 12 * nside * nside or row_bytes != 8):
        raise ValueError("Unsupported HEALPix table dimensions")
    if _value(table, "TFORM1") != "E" or _value(table, "TTYPE1") != "TEMPERATURE":
        raise ValueError("Expected float32 TEMPERATURE as the first table field")
    if _value(table, "TUNIT1") != "mK, thermodynamic":
        raise ValueError("Expected thermodynamic millikelvin temperatures")
    if int(_value(table, "TFIELDS")) != 2 or _value(table, "TFORM2") != "E":
        raise ValueError("Expected two float32 fields per row")
    end = FITS_DATA_OFFSET + npix * row_bytes
    if len(data) < end:
        raise ValueError("FITS pixel table is truncated")
    values = [struct.unpack_from(">f", data, FITS_DATA_OFFSET + i * row_bytes)[0]
              for i in range(npix)]
    if not all(math.isfinite(value) and abs(value) < 1e20 for value in values):
        raise ValueError("FITS temperature map contains non-finite or UNSEEN sentinel samples")
    return nside, values, hashlib.sha256(data).hexdigest()


def downsample_nested(nside, values, target_nside=TARGET_NSIDE):
    """Average each contiguous NESTED child group into its parent pixel."""
    if nside < 1 or nside & (nside - 1) or target_nside < 1 or target_nside & (target_nside - 1):
        raise ValueError("Nside values must be positive powers of two")
    if target_nside > nside or nside % target_nside:
        raise ValueError("Target Nside must divide source Nside")
    if len(values) != 12 * nside * nside:
        raise ValueError("Temperature array length does not match source Nside")
    children = (nside // target_nside) ** 2
    return [sum(values[start:start + children]) / children
            for start in range(0, len(values), children)]


def _spread_bits(value):
    result = 0
    bit = 0
    while value:
        result |= (value & 1) << (2 * bit)
        value >>= 1
        bit += 1
    return result


def ang2pix_nest(nside, theta, phi):
    """HEALPix NESTED ang2pix for RING-free sampling (theta from north pole)."""
    if nside < 1 or nside & (nside - 1):
        raise ValueError("Nside must be a positive power of two")
    if not math.isfinite(theta) or not 0 <= theta <= math.pi:
        raise ValueError("Theta must be finite and in [0, pi]")
    if not math.isfinite(phi):
        raise ValueError("Phi must be finite")
    z = math.cos(theta)
    za = abs(z)
    tt = (phi % (2 * math.pi)) * (2 / math.pi)
    if za <= 2 / 3:
        temp1 = nside * (0.5 + tt)
        temp2 = nside * z * 0.75
        jp = int(math.floor(temp1 - temp2))
        jm = int(math.floor(temp1 + temp2))
        ifp, ifm = jp // nside, jm // nside
        if ifp == ifm:
            face = (ifp & 3) + 4
        elif ifp < ifm:
            face = ifp & 3
        else:
            face = (ifm & 3) + 8
        ix, iy = jm % nside, nside - (jp % nside) - 1
    else:
        quadrant = int(math.floor(tt))
        tp = tt - quadrant
        tmp = nside * math.sqrt(3 * (1 - za))
        jp = min(nside - 1, int(math.floor(tp * tmp)))
        jm = min(nside - 1, int(math.floor((1 - tp) * tmp)))
        if z >= 0:
            face, ix, iy = quadrant & 3, nside - jm - 1, nside - jp - 1
        else:
            face, ix, iy = (quadrant & 3) + 8, jp, jm
    return face * nside * nside + _spread_bits(ix) + 2 * _spread_bits(iy)


def temperature_color(value, limit=0.25):
    """Blue-neutral-red diverging map, returned as sRGB bytes."""
    t = max(-1.0, min(1.0, value / limit))
    if t < 0:
        f = t + 1
        rgb = (18 + 222 * f, 63 + 179 * f, 150 + 105 * f)
    else:
        f = t
        rgb = (240, 242 - 187 * f, 255 - 230 * f)
    return tuple(round(channel) for channel in rgb)


def make_texture(nside, values, path, width=512, height=256):
    if len(values) != 12 * nside * nside:
        raise ValueError("Temperature array length does not match Nside")
    image = Image.new("RGB", (width, height))
    pixels = image.load()
    for y in range(height):
        dec = math.pi / 2 - math.pi * (y + 0.5) / height
        theta = math.pi / 2 - dec
        for x in range(width):
            # Texture longitude runs west-to-east; use Galactic lon directly.
            lon = 2 * math.pi * (x + 0.5) / width
            pixels[x, y] = temperature_color(values[ang2pix_nest(nside, theta, lon)])
    image.save(path, format="JPEG", quality=86, optimize=True, subsampling=0)
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def shell_geometry(segments, rings, opening_degrees):
    """Open +Z-polar shell, with UVs reprojected into Galactic sky coordinates."""
    if segments < 8 or rings < 4 or not 0 < opening_degrees < 90:
        raise ValueError("Shell requires at least 8 segments, 4 rings and a 0-90 degree opening")
    opening = math.radians(opening_degrees)

    def vertex(j, i):
        theta = opening + (math.pi - opening) * j / rings
        phi = 2 * math.pi * i / segments
        return [CMB_RADIUS_LY * math.sin(theta) * math.cos(phi),
                CMB_RADIUS_LY * math.sin(theta) * math.sin(phi),
                CMB_RADIUS_LY * math.cos(theta)]

    vertices, uvs = [], []
    for j in range(rings):
        for i in range(segments):
            a, b, c, d = vertex(j, i), vertex(j + 1, i), vertex(j, i + 1), vertex(j + 1, i + 1)
            faces = ((a, b, c),) if j == rings - 1 else ((a, b, c), (c, b, d))
            for face in faces:
                uv = [[(math.atan2(z, x) / (2 * math.pi)) % 1,
                       0.5 - math.asin(max(-1, min(1, y / CMB_RADIUS_LY))) / math.pi]
                      for x, y, z in face]
                # Repeat U locally at the longitude seam, never interpolate
                # across the whole sky. Each face owns its UV vertices.
                if max(u for u, _ in uv) - min(u for u, _ in uv) > 0.5:
                    uv = [[u + 1 if u < 0.5 else u, v] for u, v in uv]
                vertices.extend(face)
                uvs.extend(uv)
    return vertices, uvs, list(range(len(vertices)))


def build(texture_bytes, segments=96, rings=48, opening_degrees=30):
    if not texture_bytes.startswith(b"\xff\xd8"):
        raise ValueError("Texture must be JPEG data")
    document = {"asset": {"version": "2.0", "generator": "Universe Scales WMAP diagram"},
                "scene": 0, "scenes": [{"nodes": []}], "nodes": [], "meshes": [],
                "materials": [], "accessors": [], "bufferViews": [], "images": [],
                "textures": [], "samplers": [], "extensionsUsed": ["KHR_materials_unlit"]}
    binary = bytearray()

    def accessor(rows, kind="VEC3", target=34962, bounds=False):
        binary.extend(b"\0" * (-len(binary) % 4))
        flat = [item for row in rows for item in row]
        offset = len(binary)
        binary.extend(struct.pack("<" + "f" * len(flat), *flat))
        view = len(document["bufferViews"])
        document["bufferViews"].append({"buffer": 0, "byteOffset": offset,
                                        "byteLength": len(binary) - offset, "target": target})
        entry = {"bufferView": view, "componentType": 5126,
                 "count": len(rows), "type": kind}
        if bounds:
            entry["min"] = [min(row[i] for row in rows) for i in range(3)]
            entry["max"] = [max(row[i] for row in rows) for i in range(3)]
        document["accessors"].append(entry)
        return len(document["accessors"]) - 1

    def mesh_node(name, primitive, material, extras=None):
        index = len(document["meshes"])
        document["meshes"].append({"name": name, "primitives": [{**primitive, "material": material}]})
        node = len(document["nodes"])
        document["nodes"].append({"name": name, "mesh": index, "extras": extras or {}})
        document["scenes"][0]["nodes"].append(node)

    # The opening follows a true circular latitude, not a staircase of cells.
    vertices, uvs, indices = shell_geometry(segments, rings, opening_degrees)
    pos = accessor(vertices, bounds=True)
    uv = accessor(uvs, "VEC2")
    index_offset = len(binary)
    binary.extend(struct.pack("<" + "I" * len(indices), *indices))
    view = len(document["bufferViews"])
    document["bufferViews"].append({"buffer": 0, "byteOffset": index_offset,
                                    "byteLength": len(binary) - index_offset, "target": 34963})
    document["accessors"].append({"bufferView": view, "componentType": 5125,
                                  "count": len(indices), "type": "SCALAR",
                                  "min": [min(indices)], "max": [max(indices)]})
    texture_view = len(document["bufferViews"])
    binary.extend(texture_bytes)
    document["bufferViews"].append({"buffer": 0, "byteOffset": len(binary) - len(texture_bytes),
                                    "byteLength": len(texture_bytes)})
    document["images"].append({"bufferView": texture_view, "mimeType": "image/jpeg"})
    document["samplers"].append({"magFilter": 9729, "minFilter": 9987,
                                 "wrapS": 10497, "wrapT": 33071})
    document["textures"].append({"sampler": 0, "source": 0})
    document["materials"].append({"name": "Observed WMAP CMB anisotropy",
                                  "pbrMetallicRoughness": {"baseColorTexture": {"index": 0},
                                                            "metallicFactor": 0,
                                                            "roughnessFactor": 1},
                                  "doubleSided": False,
                                  "extensions": {"KHR_materials_unlit": {}}})
    mesh_node("WMAP ILC temperature on approximate last-scattering sphere",
              {"attributes": {"POSITION": pos, "TEXCOORD_0": uv},
               "indices": len(document["accessors"]) - 1, "mode": 4}, 0)

    # Three orthogonal great circles make the particle-horizon radius legible.
    line_positions = []
    for plane in range(3):
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            next_angle = 2 * math.pi * (i + 1) / segments
            a, b = HORIZON_RADIUS_LY * math.cos(angle), HORIZON_RADIUS_LY * math.sin(angle)
            c, d = HORIZON_RADIUS_LY * math.cos(next_angle), HORIZON_RADIUS_LY * math.sin(next_angle)
            line_positions.extend(([a, b, 0], [c, d, 0]) if plane == 0 else
                                  ([a, 0, b], [c, 0, d]) if plane == 1 else
                                  ([0, a, b], [0, c, d]))
    line_pos = accessor(line_positions, target=34962, bounds=True)
    line_material = len(document["materials"])
    document["materials"].append({"name": "Particle horizon guide", "doubleSided": True,
                                  "extensions": {"KHR_materials_unlit": {}},
                                  "pbrMetallicRoughness": {"baseColorFactor": [0.55, 0.82, 1, 0.78],
                                                            "metallicFactor": 0, "roughnessFactor": 1},
                                  "alphaMode": "BLEND"})
    mesh_node("Particle horizon (three great-circle guides)",
              {"attributes": {"POSITION": line_pos}, "mode": 1}, line_material)

    opening = math.radians(opening_degrees)
    rim = [[CMB_RADIUS_LY * math.sin(opening) * math.cos(2 * math.pi * i / segments),
            CMB_RADIUS_LY * math.sin(opening) * math.sin(2 * math.pi * i / segments),
            CMB_RADIUS_LY * math.cos(opening)] for i in range(segments)]
    rim_material = len(document["materials"])
    document["materials"].append({"name": "Diagram cutaway rim (not a physical boundary)",
                                  "pbrMetallicRoughness": {"baseColorFactor": [0.95, 0.72, 0.30, 1],
                                                            "metallicFactor": 0},
                                  "extensions": {"KHR_materials_unlit": {}}})
    mesh_node("Smooth diagram cutaway rim", {"attributes": {"POSITION": accessor(rim, bounds=True)},
                                               "mode": 2}, rim_material)

    def annotation(name, label, location, priority, offset):
        document["nodes"].append({"name": name, "translation": location,
                                  "extras": {"label": label, "labelLayout": "orbit",
                                             "labelPriority": priority, "labelOffset": offset}})
        document["scenes"][0]["nodes"].append(len(document["nodes"]) - 1)

    annotation("CMB boundary label", "CMB last scattering",
               [CMB_RADIUS_LY * 0.8, CMB_RADIUS_LY * 0.6, 0], 0, {"x": 56, "y": -32})
    annotation("Particle horizon label", "Particle horizon",
               [-HORIZON_RADIUS_LY * 0.8, -HORIZON_RADIUS_LY * 0.6, 0], 1, {"x": -55, "y": 32})

    # An explicit origin marker lets a viewer inspect the opening in the shell.
    p = accessor([[0, 0, 0]])
    marker_material = len(document["materials"])
    document["materials"].append({"name": "Observer marker", "pbrMetallicRoughness":
                                  {"baseColorFactor": [1, 0.88, 0.55, 1], "metallicFactor": 0},
                                  "extensions": {"KHR_materials_unlit": {}}})
    mesh_node("Observer at diagram origin", {"attributes": {"POSITION": p}, "mode": 0},
              marker_material, {"label": "Observer", "labelLayout": "orbit",
                                "labelPriority": 0, "labelOffset": {"x": 22, "y": 15},
                                "pointSize": {"max": 7, "perPixel": 1 / 100}})
    document["buffers"] = [{"byteLength": len(binary)}]
    return pack_glb(document, bytes(binary)), len(vertices), len(indices) // 3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fits", type=Path, default=DEFAULT_FITS)
    parser.add_argument("--output-dir", type=Path, default=Path("/private/tmp/observable-universe-model"))
    args = parser.parse_args()
    source_nside, source_values, fits_hash = read_healpix_fits(args.fits)
    values = downsample_nested(source_nside, source_values, TARGET_NSIDE)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    texture_path = args.output_dir / "cmb-equirectangular.jpg"
    texture_hash = make_texture(TARGET_NSIDE, values, texture_path)
    model, vertex_count, triangle_count = build(texture_path.read_bytes())
    model_path = args.output_dir / "observable-universe-wmap.glb"
    model_path.write_bytes(model)
    entry = {
        "id": "observable-universe-wmap", "source": SOURCE, "download_url": DOWNLOAD,
        "link_label": "WMAP nine-year ILC map", "author": "NASA/WMAP Science Team; model geometry by Universe Scales",
        "license": "U.S. public-domain NASA scientific data; attribution requested; NASA usage guidelines apply (not CC0)",
        "license_url": NASA_LICENSE,
        "license_files": ["licenses/nasa-media-guidelines.html", "sources/observable-universe-model.md"],
        "matches": {"length": ["Observable Universe"]}, "geometry": "mesh",
        "volume_semantics": "causal-horizon diagram, not an enclosed matter volume",
        "basis_url": "https://www.nasa.gov/science-research/astrophysics/how-big-is-space-we-asked-a-nasa-expert-episode-61/",
        "basis_label": "NASA: present-distance observable-universe span",
        "presentation": {"reference_size": REFERENCE_SIZE_LY, "yaw": 0,
                         "layout_width_factor": 1.08, "focus_scale_factor": 1.1},
        "note": "NASA/WMAP Science Team, via NASA LAMBDA; adapted into a causal-horizon diagram. The nine-year sky map colors temperature fluctuations, not matter density: blue is cooler and red warmer, with a display stretch of +/-0.25 mK. The Nside=64 display averages 64 original HEALPix child pixels; foreground cleaning is most reliable above about 10 degrees. The textured last-scattering shell has an approximate present-distance radius of 45.6 billion light-years. Blue guides show the slightly larger particle horizon, about 46.5 billion light-years, with their true proportional radii. The smooth amber-rimmed opening only exposes the observer; it is an authored cutaway, not a gap in the universe. Neither boundary is a material wall or the edge of all space.",
        "processing": {"script": "scripts/build_observable_universe_model.py",
                       "source_fits_sha256": fits_hash, "source_nside": source_nside,
                       "target_nside": TARGET_NSIDE,
                       "nested_child_averaging_factor": (source_nside // TARGET_NSIDE) ** 2,
                       "source_ordering": "NESTED", "source_coordinate_system": "Galactic",
                       "source_temperature_units": "mK thermodynamic", "source_resolution_degrees": 1.0,
                       "source_small_scale_caveat": "LAMBDA considers full-sky ILC reliable on scales >~10 degrees",
                       "texture_sha256": texture_hash,
                       "texture": "512x256 equirectangular JPEG; Galactic longitude/latitude sampled by HEALPix ang2pix; linear temperature stretch saturated at +/-0.25 mK",
                       "cmb_last_scattering_radius_ly": CMB_RADIUS_LY,
                       "particle_horizon_radius_ly": HORIZON_RADIUS_LY,
                       "shell_cutaway": "+Z cone, 30 degrees", "vertices": vertex_count,
                       "triangles": triangle_count, "depth_semantics": "diagrammatic boundaries; no volumetric claim"}}
    write_json(args.output_dir / "entry.json", entry)
    print(f"{model_path}: {len(model):,} bytes; {triangle_count:,} triangles; texture {texture_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
