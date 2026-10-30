#!/usr/bin/env python3
"""Build Length models that have no public 3D source, from published measurements.

    ./venv/bin/python scripts/build_measured_models.py OUT_DIR [name ...]

Each model's geometry is set by cited numbers (see SOURCES and the matching
content/visualizations/models/sources/*.md); nothing is scaled by eye.

- great-pyramid: original Khufu pyramid, base 230.33 m, height 146.6 m (Petrie 1883;
  Lehner & Hawass 2017). Smooth Tura-limestone casing as built.
- inner-core: Earth's inner core, radius 1221.5 km (PREM, Dziewonski & Anderson 1981),
  cut open to the innermost inner core, radius ~650 km (Stephenson, Tkalcic & Sambridge 2021).
- kola-borehole: SG-3 rock column, 12,262 m, with the Proterozoic Pechenga complex over the
  Archean basement at 6,842 m (Kozlovsky 1984) and the bottom-hole temperature of ~180 C.
- dvd-tracks / bluray-tracks: three tracks of pits at the format track pitch, channel bit
  length and run-length limits (ECMA-267 DVD; Blu-ray Disc Association white paper 2018).
- ton618-horizon: Schwarzschild horizon for 4.07e10 solar masses (Ge et al. 2019), with
  Neptune's orbit and the heliopause where Voyager 1 crossed it, to the same scale.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geo_glb_common import GLB  # noqa: E402


def flat(triangles):
    """Triangles (n, 3, 3) -> positions, indices, flat normals (one normal per face)."""
    tri = np.asarray(triangles, dtype=np.float64).reshape(-1, 3, 3)
    normal = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
    return tri.reshape(-1, 3), np.arange(len(tri) * 3), np.repeat(normal, 3, axis=0)


def box(x0, x1, y0, y1, z0, z1):
    """Twelve outward-facing triangles of an axis-aligned box."""
    p = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return [tri for a, b, c, d in quads for tri in ((p[a], p[b], p[c]), (p[a], p[c], p[d]))]


def sphere(radius, rings=48, segments=96, keep=lambda theta, phi: True):
    """Smooth UV sphere; `keep(theta, phi)` drops quads (theta polar, phi azimuth) for cutaways."""
    positions, normals, indices = [], [], []
    for i in range(rings + 1):
        theta = math.pi * i / rings
        for j in range(segments + 1):
            phi = 2 * math.pi * j / segments
            n = (math.sin(theta) * math.cos(phi), math.cos(theta), math.sin(theta) * math.sin(phi))
            normals.append(n)
            positions.append(tuple(radius * c for c in n))
    for i in range(rings):
        for j in range(segments):
            if not keep(math.pi * (i + 0.5) / rings, 2 * math.pi * (j + 0.5) / segments):
                continue
            a = i * (segments + 1) + j
            b, c, d = a + 1, a + segments + 1, a + segments + 2
            indices += [a, c, b, b, c, d]
    return np.array(positions), np.array(indices), np.array(normals)


def ring(radius, width, z, segments=256):
    """A flat annulus in the xy plane at depth z, facing +z."""
    positions, indices = [], []
    for j in range(segments + 1):
        a = 2 * math.pi * j / segments
        for r in (radius - width / 2, radius + width / 2):
            positions.append((r * math.cos(a), r * math.sin(a), z))
    for j in range(segments):
        a = 2 * j
        indices += [a, a + 1, a + 2, a + 1, a + 3, a + 2]
    return np.array(positions), np.array(indices), np.tile([0.0, 0.0, 1.0], (len(positions), 1))


def great_pyramid(path):
    import io
    from PIL import Image, ImageDraw
    half, height, courses = 230.33 / 2, 146.6, 210
    apex = (0, height, 0)
    corners = [(-half, 0, -half), (half, 0, -half), (half, 0, half), (-half, 0, half)]
    faces = [(corners[(k + 1) % 4], corners[k], apex) for k in range(4)]
    faces += [(corners[0], corners[1], corners[2]), (corners[0], corners[2], corners[3])]
    # About 210 stone courses (Lehner & Hawass); drawn evenly spaced as faint joints. The real
    # courses thin from ~1.5 m near the base to ~0.6 m higher up.
    image = Image.new("RGB", (8, 2048), (205, 186, 150))
    draw = ImageDraw.Draw(image)
    for k in range(1, courses):
        y = round(2048 * (1 - k / courses))
        draw.line([(0, y), (8, y)], fill=(178, 158, 124))
    buffer = io.BytesIO(); image.save(buffer, "PNG")
    glb = GLB("Universe Scales measured-model builder")
    casing = glb.material("Tura limestone casing", color=(0.92, 0.88, 0.80, 1), rough=0.9,
                          texture=glb.texture(buffer.getvalue(), "image/png"))
    pos, idx, nrm = flat(faces)
    uvs = np.stack([np.full(len(pos), 0.5), 1 - pos[:, 1] / height], axis=1)
    glb.mesh_node("pyramid", [glb.primitive(pos, idx, casing, normals=nrm, uvs=uvs)])
    glb.label_node("height", (0, height * 1.06, 0), "146.6 m as built", labelRole="dimension")
    return glb.write(path), {"reference_size": height, "measure_axis": "y"}


def inner_core(path):
    radius, innermost = 1221.5, 650.0
    glb = GLB("Universe Scales measured-model builder")
    shell = glb.material("inner core (solid iron-nickel)", color=(0.86, 0.55, 0.26, 1), rough=0.55, metal=0.35,
                         emissive=(0.35, 0.12, 0.02))
    inner = glb.material("innermost inner core", color=(1.0, 0.82, 0.45, 1), rough=0.5, metal=0.3,
                         emissive=(0.55, 0.32, 0.08))
    cut = glb.material("cut face", color=(0.93, 0.62, 0.30, 1), rough=0.7, emissive=(0.30, 0.10, 0.02))
    # Remove the quarter facing the default camera (x > 0, z > 0) to show the inside.
    open_quarter = lambda theta, phi: not (math.cos(phi) > 0 and math.sin(phi) > 0)
    pos, idx, nrm = sphere(radius, keep=open_quarter)
    glb.mesh_node("inner core", [glb.primitive(pos, idx, shell, normals=nrm)])
    pos, idx, nrm = sphere(innermost, rings=32, segments=64, keep=open_quarter)
    glb.mesh_node("innermost inner core", [glb.primitive(pos, idx, inner, normals=nrm)])
    # The two cut faces: half-disks in the x=0 plane (z > 0) and z=0 plane (x > 0), with the
    # innermost core drawn as a lighter disk on each.
    for name, axis in (("cut face x", 0), ("cut face z", 2)):
        for r0, r1, material in ((innermost, radius, cut), (0.0, innermost, inner)):
            positions, indices = [], []
            steps = 96
            for k in range(steps + 1):
                t = math.pi * k / steps - math.pi / 2
                for r in (r0, r1):
                    u, y = r * math.cos(t), r * math.sin(t)
                    positions.append((0.0, y, u) if axis == 0 else (u, y, 0.0))
            for k in range(steps):
                a = 2 * k
                indices += [a, a + 2, a + 1, a + 1, a + 2, a + 3]
            normal = (-1.0, 0.0, 0.0) if axis == 0 else (0.0, 0.0, -1.0)
            positions = np.array(positions)
            # Offset the innermost disk a hair forward of the outer face to avoid z-fighting.
            if r0 == 0.0:
                positions += np.array(normal) * -0.5
            glb.mesh_node(name, [glb.primitive(positions, np.array(indices), material,
                                               normals=np.tile(normal, (len(positions), 1)))])
    glb.label_node("innermost", (innermost * 0.5, innermost * 0.15, innermost * 0.5), "innermost inner core ~650 km")
    glb.label_node("radius", (0, radius * 1.08, 0), "1,221.5 km radius", labelRole="dimension")
    return glb.write(path), {"reference_size": 2 * radius, "measure_axis": "y"}


def kola_borehole(path):
    depth, boundary, width, thick = 12262.0, 6842.0, 1800.0, 700.0
    glb = GLB("Universe Scales measured-model builder")
    proterozoic = glb.material("Proterozoic Pechenga volcanic and sedimentary rocks", color=(0.33, 0.40, 0.33, 1), rough=0.95)
    archean = glb.material("Archean gneiss and granite", color=(0.66, 0.55, 0.52, 1), rough=0.95)
    hole = glb.material("borehole", color=(0.05, 0.05, 0.05, 1), rough=0.6, emissive=(0.02, 0.02, 0.02))
    surface = glb.material("surface", color=(0.80, 0.82, 0.78, 1), rough=0.9)
    for name, top, bottom, material in (("Proterozoic", 0.0, -boundary, proterozoic),
                                        ("Archean", -boundary, -depth, archean)):
        pos, idx, nrm = flat(box(-width / 2, width / 2, bottom, top, -thick / 2, thick / 2))
        glb.mesh_node(name, [glb.primitive(pos, idx, material, normals=nrm)])
    pos, idx, nrm = flat(box(-width / 2, width / 2, 0, 12, -thick / 2, thick / 2))
    glb.mesh_node("ground surface", [glb.primitive(pos, idx, surface, normals=nrm)])
    # The real hole is 0.2 m wide; drawn 40 m wide on the front face so it can be seen.
    pos, idx, nrm = flat(box(-20, 20, -depth, 14, thick / 2, thick / 2 + 6))
    glb.mesh_node("borehole", [glb.primitive(pos, idx, hole, normals=nrm)])
    glb.label_node("top", (0, 400, thick / 2), "Proterozoic volcanic and sedimentary rocks")
    glb.label_node("boundary", (0, -boundary - 350, thick / 2), "6,842 m · Archean gneiss and granite")
    glb.label_node("bottom", (0, -depth - 450, thick / 2), "12,262 m · about 180 °C", labelRole="dimension")
    return glb.write(path), {"reference_size": depth, "measure_axis": "y"}


def disc_tracks(path, pitch, bit, runs, width, depth, tracks=3, length=None, seed=7, label="", metal=(0.78, 0.80, 0.84)):
    """Pits (dark recesses) in a reflective layer: `tracks` tracks at `pitch`, pit and land lengths
    drawn from the format's run-length limits (multiples of the channel bit), deterministically."""
    rng = np.random.default_rng(seed)
    length = length or 4 * pitch
    across = tracks * pitch
    glb = GLB("Universe Scales measured-model builder")
    layer = glb.material("reflective layer", color=(*metal, 1), rough=0.35, metal=0.15)
    pit = glb.material("pit", color=(0.16, 0.20, 0.34, 1), rough=0.7)
    pos, idx, nrm = flat(box(-across / 2, across / 2, -depth * 1.5, 0, -length / 2, length / 2))
    glb.mesh_node("reflective layer", [glb.primitive(pos, idx, layer, normals=nrm)])
    weights = np.array([1 / n for n in runs], dtype=float)
    weights /= weights.sum()
    triangles = []
    for t in range(tracks):
        x = -across / 2 + pitch * (t + 0.5)
        z = -length / 2 - rng.uniform(0, 3) * bit
        on = bool(t % 2)
        while z < length / 2:
            run = rng.choice(runs, p=weights) * bit
            z0, z1 = max(z, -length / 2), min(z + run, length / 2)
            if on and z1 - z0 > bit * 0.5:
                # A pit: rounded ends approximated by a beveled box, recessed below the layer top.
                triangles += box(x - width / 2, x + width / 2, -depth, 0.001 * pitch, z0, z1)
            z += run
            on = not on
    pos, idx, nrm = flat(triangles)
    glb.mesh_node("pits", [glb.primitive(pos, idx, pit, normals=nrm)])
    glb.label_node("pitch", (-across / 2 + pitch, depth * 0.5, length / 2 + pitch * 0.15), label, labelRole="dimension")
    return glb.write(path), {"reference_size": pitch, "measure_axis": "x"}


def dvd_tracks(path):
    # ECMA-267: track pitch 0.74 um, channel bit 0.133 um, EFMPlus run lengths 3T-11T and 14T.
    return disc_tracks(path, 0.74, 0.1333, [3, 4, 5, 6, 7, 8, 9, 10, 11, 14], width=0.32, depth=0.105,
                       length=3.2, label="0.74 µm track pitch")


def bluray_tracks(path):
    # Blu-ray (25 GB layer): track pitch 0.32 um, channel bit 74.5 nm, 1-7PP run lengths 2T-8T.
    return disc_tracks(path, 0.32, 0.0745, [2, 3, 4, 5, 6, 7, 8], width=0.14, depth=0.065,
                       length=1.4, label="0.32 µm track pitch", metal=(0.82, 0.82, 0.86))


def ton618_horizon(path):
    # Schwarzschild radius r_s = 2GM/c^2 for M = 4.07e10 solar masses; units of r_s.
    G, c, msun = 6.67430e-11, 299792458.0, 1.98847e30
    rs = 2 * G * 4.07e10 * msun / c ** 2
    au = 1.495978707e11
    neptune = 30.07 * au / rs          # Neptune's mean orbital radius
    heliopause = 121.6 * au / rs       # where Voyager 1 crossed the heliopause (2012)
    glb = GLB("Universe Scales measured-model builder")
    horizon = glb.material("event horizon", color=(0.02, 0.02, 0.025, 1), rough=0.35, metal=0.0)
    orbit = glb.material("Neptune's orbit", color=(0.55, 0.75, 1.0, 1), rough=1.0, emissive=(0.45, 0.65, 1.0))
    edge = glb.material("heliopause", color=(1.0, 0.75, 0.45, 1), rough=1.0, emissive=(0.9, 0.6, 0.3))
    pos, idx, nrm = sphere(1.0, rings=64, segments=128)
    glb.mesh_node("event horizon", [glb.primitive(pos, idx, horizon, normals=nrm)])
    pos, idx, nrm = ring(neptune, 0.006, 1.02)
    glb.mesh_node("Neptune's orbit", [glb.primitive(pos, idx, orbit, normals=nrm)])
    pos, idx, nrm = ring(heliopause, 0.008, 1.02)
    glb.mesh_node("heliopause", [glb.primitive(pos, idx, edge, normals=nrm)])
    glb.label_node("neptune", (0, -neptune - 0.03, 1.03), "Neptune's orbit")
    glb.label_node("heliopause", (0, heliopause + 0.04, 1.03), "Voyager 1 at the heliopause")
    return glb.write(path), {"reference_size": 2.0, "measure_axis": "y", "rs_m": rs,
                             "neptune_rs": neptune, "heliopause_rs": heliopause}


BUILDERS = {"great-pyramid": great_pyramid, "inner-core": inner_core, "kola-borehole": kola_borehole,
            "dvd-tracks": dvd_tracks, "bluray-tracks": bluray_tracks, "ton618-horizon": ton618_horizon}


def main():
    out = Path(sys.argv[1])
    names = sys.argv[2:] or list(BUILDERS)
    for name in names:
        size, info = BUILDERS[name](out / f"measured-{name}.glb")
        print(json.dumps({"model": f"measured-{name}", "bytes": size, **info}))


if __name__ == "__main__":
    main()
