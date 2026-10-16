#!/usr/bin/env python3
"""Build the Pleiades in 3D from Gaia parallaxes.

    ./venv/bin/python scripts/build_pleiades_model.py pleiades.tsv OUT.glb

pleiades.tsv: Gaia Collaboration (Babusiaux et al.) 2018, A&A 616, A10, Table A1a, the Pleiades
members (columns RAdeg, DEdeg, Gmag, plx, e_plx), from
https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/A%2BA/616/A10/tablea1a&Cluster=Pleiades&-out=RAdeg,DEdeg,Gmag,plx,e_plx&-out.max=unlimited

Each star is placed at its Gaia position and distance 1/parallax; stars with parallax error
over 0.1 mas are dropped. Units: light-years; the line of sight is +z (toward the camera), north
up and east left, so the resting view matches our sky. Distance errors (about 1 pc for typical
members) stretch the cluster slightly along the line of sight. Color comes from absolute
magnitude, valid along the main sequence of this single-age (~100 Myr) cluster.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nebula_volume import add_cloud  # noqa: E402
from volume_glb import VolumeGLB  # noqa: E402

LY_PER_PC = 3.26156
# The brightest members are too bright for the Gaia DR2 member table, and their Gaia DR3
# parallaxes are poor (+-0.3-0.5 mas, ~20 ly in depth; none for Alcyone): they are placed at the
# cluster's median distance at their Gaia DR3 sky positions (RA, Dec, G).
BRIGHT = {"Alcyone": (56.87125, 24.10493, 2.90), "Atlas": (57.29069, 24.05321, 3.62),
          "Electra": (56.21900, 24.11313, 3.70), "Maia": (56.45680, 24.36754, 3.86),
          "Merope": (56.58167, 23.94814, 4.17), "Taygeta": (56.30216, 24.46706, 4.26),
          "Pleione": (57.29683, 24.13650, 5.20)}
# Absolute G magnitude -> main-sequence color (blue-white B stars to red M dwarfs).
COLOR_STOPS = [(-2, (0.62, 0.72, 1.0)), (0.5, (0.8, 0.86, 1.0)), (2.5, (1.0, 0.97, 0.92)),
               (4.5, (1.0, 0.88, 0.66)), (7, (1.0, 0.7, 0.45)), (11, (1.0, 0.5, 0.35))]


def load(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        try:
            rows.append([float(p) for p in parts])
        except ValueError:
            continue
    return np.array(rows)


def color_for(absolute):
    stops = np.array([s[0] for s in COLOR_STOPS])
    colors = np.array([s[1] for s in COLOR_STOPS])
    return np.stack([np.interp(absolute, stops, colors[:, k]) for k in range(3)], 1)


def build(catalog, output):
    ra, dec, gmag, plx, eplx = load(catalog).T
    keep = eplx < 0.1
    ra, dec, gmag, plx = ra[keep], dec[keep], gmag[keep], plx[keep]
    distance_ly = 1000 / plx * LY_PER_PC
    median_ly = float(np.median(distance_ly))
    named = list(BRIGHT)
    extra = np.array([BRIGHT[name] for name in named])
    ra, dec, gmag = np.concatenate([ra, extra[:, 0]]), np.concatenate([dec, extra[:, 1]]), np.concatenate([gmag, extra[:, 2]])
    distance_ly = np.concatenate([distance_ly, np.full(len(extra), median_ly)])
    first_named = len(ra) - len(extra)
    ra0, dec0 = math.radians(np.median(ra)), math.radians(np.median(dec))
    # Local frame at the cluster center: east, north, toward us (+z).
    a, d = np.radians(ra), np.radians(dec)
    xyz = np.stack([np.cos(d) * np.cos(a), np.cos(d) * np.sin(a), np.sin(d)], 1) * distance_ly[:, None]
    forward = np.array([math.cos(dec0) * math.cos(ra0), math.cos(dec0) * math.sin(ra0), math.sin(dec0)])
    north = np.array([0, 0, 1.0]) - forward * forward[2]
    north /= np.linalg.norm(north)
    east = np.cross(north, forward)
    center = np.median(xyz, axis=0)
    rel = xyz - center
    model = np.stack([-rel @ east, rel @ north, -rel @ forward], 1)  # east left; +z toward Earth
    radius = np.linalg.norm(model, axis=1)
    inside = radius < 60
    model, gmag, distance_ly, ra, dec = model[inside], gmag[inside], distance_ly[inside], ra[inside], dec[inside]
    absolute = gmag - 5 * np.log10(distance_ly / LY_PER_PC / 10)
    colors = color_for(absolute)
    brightness = np.clip(1.15 - 0.09 * (absolute + 1.5), 0.15, 1)

    glb = VolumeGLB("Universe Scales Pleiades builder")
    bright = absolute < 1.0
    add_cloud(glb, "bright-stars", model[bright], colors[bright], np.ones(bright.sum()), 1 / 110, 10)
    add_cloud(glb, "stars", model[~bright], colors[~bright], np.clip(brightness[~bright] * 1.3, 0.25, 1), 1 / 210, 4)
    # Faint blue glow where starlight scatters off the dust cloud the cluster is passing through
    # (illustrative extent around the brightest stars).
    rng = np.random.default_rng(0x9135)
    glow = np.concatenate([p + rng.normal(0, 1.2, (160, 3)) * [1, 1, 0.6] for p in model[absolute < -0.5]])
    add_cloud(glb, "reflection-glow", glow, np.tile([0.45, 0.6, 1.0], (len(glow), 1)), np.full(len(glow), 0.02),
              1 / 45, 18, alpha_floor=0.012)
    star_index = {}
    order = np.cumsum(inside) - 1  # index of each original row among kept rows
    for k, name in enumerate(named):
        row = first_named + k
        if inside[row]:
            star_index[name] = int(order[row])
            glb.node(f"label-{name}", translation=model[order[row]], extras={"label": name})
    size = glb.write(output)
    return {"bytes": size, "stars": int(len(model)), "named": sorted(star_index),
            "extent_ly": (model.max(0) - model.min(0)).round(1).tolist(), "median_distance_ly": median_ly}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("catalog")
    parser.add_argument("output")
    args = parser.parse_args()
    print(json.dumps(build(args.catalog, args.output)))


if __name__ == "__main__":
    main()
