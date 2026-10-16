#!/usr/bin/env python3
"""Build a schematic Mycoplasma cell, about 200 nm across (units: nm).

    ./venv/bin/python scripts/build_mycoplasma_model.py OUT.glb

A wall-less, slightly flask-shaped cell (Mycoplasma genitalium cells are roughly 200-300 nm across;
the tapered tip stands for the attachment organelle) shown as a translucent single membrane
(~8 nm, no cell wall) over a cytoplasm holding ribosome glyphs (each 20 nm, the size of a
bacterial 70S ribosome) and a coiled nucleoid. The arrangement and counts are illustrative,
not a reconstruction of one cell.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geo_glb_common import GLB  # noqa: E402

WIDTH_NM = 200.0
LENGTH_NM = 260.0
MEMBRANE_NM = 8.0
RIBOSOME_NM = 20.0


def surface(radius_fn, rings=48, segments=64):
    """A closed surface of revolution about +x: radius_fn(t) for t in [0, 1] along the length."""
    positions, indices = [], []
    for i in range(rings + 1):
        t = i / rings
        x = (t - 0.5) * LENGTH_NM
        r = radius_fn(t)
        for j in range(segments):
            a = 2 * math.pi * j / segments
            positions.append((x, r * math.cos(a), r * math.sin(a)))
    for i in range(rings):
        for j in range(segments):
            a, b = i * segments + j, i * segments + (j + 1) % segments
            c, d = a + segments, b + segments
            indices += [a, c, b, b, c, d]
    positions = np.array(positions)
    # Surface-of-revolution normal (-dr/dx, cos a, sin a); along the axis at the poles.
    normals = []
    for i in range(rings + 1):
        t = i / rings
        dt = 1e-4
        slope = (radius_fn(min(1.0, t + dt)) - radius_fn(max(0.0, t - dt))) / ((min(1.0, t + dt) - max(0.0, t - dt)) * LENGTH_NM)
        for j in range(segments):
            a = 2 * math.pi * j / segments
            if radius_fn(t) < 1e-6:
                normals.append((1.0 if t > 0.5 else -1.0, 0.0, 0.0))
            else:
                n = np.array([-slope, math.cos(a), math.sin(a)])
                normals.append(n / np.linalg.norm(n))
    return positions, indices, np.array(normals)


def profile(t, shrink=0.0):
    # Rounded ellipsoidal body (t in 0..0.8) narrowing into a short attachment tip.
    radius = WIDTH_NM / 2
    if t <= 0.8:
        u = (t - 0.4) / 0.4
        r = radius * math.sqrt(max(0.0, 1 - u * u)) if t < 0.4 else radius * (1 - 0.62 * ((t - 0.4) / 0.4) ** 2)
    else:
        u = (t - 0.8) / 0.2
        r = radius * 0.38 * math.sqrt(max(0.0, 1 - u ** 4))
    return max(0.0, r - shrink)


def sphere(center, radius, rings=8, segments=10):
    positions, indices = [], []
    for i in range(rings + 1):
        phi = math.pi * i / rings
        for j in range(segments):
            th = 2 * math.pi * j / segments
            positions.append((center[0] + radius * math.sin(phi) * math.cos(th), center[1] + radius * math.cos(phi),
                              center[2] + radius * math.sin(phi) * math.sin(th)))
    for i in range(rings):
        for j in range(segments):
            a, b = i * segments + j, i * segments + (j + 1) % segments
            indices += [a, a + segments, b, b, a + segments, b + segments]
    return np.array(positions), indices


def build(output, seed=0x3C0):
    rng = np.random.default_rng(seed)
    glb = GLB("Universe Scales Mycoplasma builder")
    membrane = glb.material("membrane", color=(0.55, 0.75, 0.86, 0.32), blend=True, double_sided=True)
    cytoplasm = glb.material("cytoplasm", color=(0.93, 0.86, 0.72, 0.18), blend=True)
    ribosome_mat = glb.material("ribosomes", color=(0.82, 0.42, 0.32, 1))
    dna_mat = glb.material("nucleoid", color=(0.36, 0.38, 0.72, 1))

    pos, idx, nrm = surface(lambda t: profile(t))
    glb.mesh_node("membrane", [glb.primitive(pos, idx, membrane, normals=nrm)])
    pos, idx, nrm = surface(lambda t: profile(t, MEMBRANE_NM))
    glb.mesh_node("cytoplasm", [glb.primitive(pos, idx, cytoplasm, normals=nrm)])

    # Ribosome glyphs scattered through the cytoplasm away from the nucleoid core.
    centers = []
    while len(centers) < 70:
        x = rng.uniform(-0.45, 0.4) * LENGTH_NM
        t = x / LENGTH_NM + 0.5
        limit = profile(t, MEMBRANE_NM + RIBOSOME_NM / 2 + 2)
        y, z = rng.uniform(-limit, limit, 2)
        if limit > 0 and math.hypot(y, z) < limit and math.hypot(y, z) > 25 and \
                all(np.linalg.norm(np.subtract((x, y, z), c)) > RIBOSOME_NM for c in centers):
            centers.append((x, y, z))
    all_pos, all_idx = [], []
    for c in centers:
        p, i = sphere(c, RIBOSOME_NM / 2)
        all_idx += [k + len(all_pos) for k in i]; all_pos += p.tolist()
    all_pos = np.array(all_pos)
    glb.mesh_node("ribosomes", [glb.primitive(all_pos, all_idx, ribosome_mat,
                                              normals=(all_pos - np.repeat(np.array(centers), 90, axis=0)) / (RIBOSOME_NM / 2))])

    # Coiled nucleoid: a 3 nm tube along a smooth random walk near the center.
    walk = np.cumsum(rng.normal(0, 6, (420, 3)), axis=0)
    walk = (walk - walk.mean(0)) / np.abs(walk - walk.mean(0)).max(0) * [70, 45, 45]
    tube_pos, tube_idx = [], []
    for k in range(len(walk) - 1):
        a, b = walk[k], walk[k + 1]
        axis = (b - a) / max(np.linalg.norm(b - a), 1e-9)
        u = np.cross(axis, [0, 0, 1]); u = u / max(np.linalg.norm(u), 1e-9) if np.linalg.norm(u) > 1e-6 else np.array([1, 0, 0])
        v = np.cross(axis, u)
        base = len(tube_pos)
        for end in (a, b):
            for j in range(6):
                th = 2 * math.pi * j / 6
                tube_pos.append(end + 1.5 * (math.cos(th) * u + math.sin(th) * v))
        for j in range(6):
            n = (j + 1) % 6
            tube_idx += [base + j, base + 6 + j, base + n, base + n, base + 6 + j, base + 6 + n]
    tube_pos = np.array(tube_pos)
    glb.mesh_node("nucleoid", [glb.primitive(tube_pos, tube_idx, dna_mat)])
    size = glb.write(output)
    return {"bytes": size, "ribosome_glyphs": len(centers), "width_nm": WIDTH_NM, "length_nm": LENGTH_NM}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("output")
    print(json.dumps(build(parser.parse_args().output)))


if __name__ == "__main__":
    main()
