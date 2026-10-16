#!/usr/bin/env python3
"""Build a 3D model of the Laniakea region from real galaxies (2MASS Redshift Survey).

    ./venv/bin/python scripts/build_laniakea_galaxies.py 2mrs.tsv OUT.glb

2mrs.tsv is VizieR J/ApJS/199/26/table3 (Huchra et al. 2012) with columns GLON,
GLAT, Ktmag, cz, from
https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJS/199/26/table3&-out=GLON,GLAT,Ktmag,cz&-out.max=unlimited

Galaxies are placed at distance cz / H0 (H0 = 75 km/s/Mpc, as in Tully et al. 2014),
in supergalactic coordinates (SGX, SGY, SGZ) mapped to model (x, z, y) so the
supergalactic plane is horizontal. Units: Mpc. Positions are in redshift space:
peculiar velocities stretch clusters along our line of sight ("fingers of God"),
and the Milky Way's dusty disk hides a wedge of sky (the Zone of Avoidance).

Laniakea is defined by galaxy flows (Tully et al. 2014), which this model does not
compute; it shows the galaxies within about 80 Mpc of a point between the Milky Way
and the Great Attractor, roughly the published 160 Mpc extent. No membership boundary
is drawn.
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

H0 = 75.0
RADIUS_MPC = 80.0
# Galactic coordinates of the supergalactic north pole and of SGL = 0 (de Vaucouleurs).
SG_POLE = (47.37, 6.32)
SG_ZERO = (137.37, 0.0)
# Cluster centers (RA, Dec degrees J2000; cz km/s, NED/literature mean values).
CLUSTERS = {
    "Virgo Cluster": (187.70, 12.39, 1079),
    "Great Attractor (Norma Cluster)": (243.89, -60.91, 4871),
    "Centaurus Cluster": (192.20, -41.31, 3418),
    "Hydra Cluster": (159.18, -27.53, 3777),
    "Coma Cluster": (194.95, 27.98, 6925),
    "Perseus Cluster": (49.95, 41.51, 5366),
}


def galactic_unit(l_deg, b_deg):
    l, b = np.radians(l_deg), np.radians(b_deg)
    return np.stack([np.cos(b) * np.cos(l), np.cos(b) * np.sin(l), np.sin(b)], -1)


def supergalactic_matrix():
    z = galactic_unit(*SG_POLE)
    x = galactic_unit(*SG_ZERO)
    x = x - z * (x @ z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.stack([x, y, z])


def equatorial_to_galactic(ra_deg, dec_deg):
    # IAU 1958 / J2000 rotation (Hipparcos convention).
    matrix = np.array([[-0.0548755604, -0.8734370902, -0.4838350155],
                       [0.4941094279, -0.4448296300, 0.7469822445],
                       [-0.8676661490, -0.1980763734, 0.4559837762]])
    ra, dec = math.radians(ra_deg), math.radians(dec_deg)
    v = matrix @ np.array([math.cos(dec) * math.cos(ra), math.cos(dec) * math.sin(ra), math.sin(dec)])
    return math.degrees(math.atan2(v[1], v[0])) % 360, math.degrees(math.asin(v[2]))


def to_model(sg):
    """SGX, SGY, SGZ -> model x, y, z with SGZ up."""
    return np.stack([sg[..., 0], sg[..., 2], -sg[..., 1]], -1)


def load(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        parts = line.split("\t")
        if len(parts) != 4 or line.startswith("#"):
            continue
        try:
            rows.append([float(value) for value in parts])
        except ValueError:
            continue
    return np.array(rows)


def build(catalog, output, seed=0x1A71):
    rng = np.random.default_rng(seed)
    data = load(catalog)
    glon, glat, kmag, cz = data.T
    sg_rotation = supergalactic_matrix()
    distance = np.clip(cz, 1, None) / H0
    sg = (galactic_unit(glon, glat) * distance[:, None]) @ sg_rotation.T
    positions = to_model(sg)

    def cluster_position(name):
        ra, dec, velocity = CLUSTERS[name]
        l, b = equatorial_to_galactic(ra, dec)
        return to_model((galactic_unit(l, b) * velocity / H0) @ sg_rotation.T)

    center = 0.55 * cluster_position("Great Attractor (Norma Cluster)")
    offset = np.linalg.norm(positions - center, axis=1)
    fade = np.clip((RADIUS_MPC + 6 - offset) / 18, 0, 1)
    keep = (fade > 0) & (cz > 0)
    positions, kmag, distance, fade = positions[keep] - center, kmag[keep], distance[keep], fade[keep]
    # Absolute K magnitude -> relative luminosity, compressed for display.
    absolute = kmag - 5 * np.log10(np.maximum(distance, 0.5) * 1e6 / 10)
    luminosity = 10 ** (-0.4 * (absolute + 24))
    brightness = np.clip(0.25 + 0.35 * np.log10(luminosity + 1e-3) + 0.35, 0.18, 1) * fade
    warm = np.clip((absolute + 26) / 4, 0, 1)[:, None]  # brighter (more negative) galaxies are warmer
    colors = (1 - warm) * np.array([1.0, 0.86, 0.62]) + warm * np.array([0.72, 0.82, 1.0])

    glb = VolumeGLB("Universe Scales Laniakea galaxy builder")
    add_cloud(glb, "galaxies", positions, colors, brightness, 1 / 260, 3.2, alpha_floor=0.05)
    order = rng.permutation(len(positions))[: min(len(positions), 14000)]
    add_cloud(glb, "cosmic-web-glow", positions[order], np.tile([0.55, 0.62, 1.0], (len(order), 1)),
              np.full(len(order), 0.11) * fade[order], 1 / 55, 26, alpha_floor=0.012)
    glb.node("Milky Way", translation=-center, scale=0.6, extras={
        "label": "Milky Way (you are here)", "outline": True, "sphere": True, "markerRadius": 3, "markerPadding": 0.5})
    for name in CLUSTERS:
        position = cluster_position(name) - center
        glb.node(f"label-{name}", translation=position, extras={"label": name})
    size = glb.write(output)
    return {"bytes": size, "galaxies": int(len(positions)), "center_model_mpc": center.round(2).tolist(),
            "extent_mpc": (positions.max(0) - positions.min(0)).round(1).tolist()}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("catalog")
    parser.add_argument("output")
    args = parser.parse_args()
    print(json.dumps(build(args.catalog, args.output)))


if __name__ == "__main__":
    main()
