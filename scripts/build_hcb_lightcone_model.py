#!/usr/bin/env python3
"""Build a 3D view of the reported Hercules-Corona Borealis Great Wall region.

    ./venv/bin/python scripts/build_hcb_lightcone_model.py OUT.glb

The model is the region where Horvath, Hakkila & Bagoly (2014, A&A 561, L12) reported a
concentration of gamma-ray bursts: centered at RA 17h00m, Dec +27.75 deg, redshift 1.6-2.1,
with axes of about 3 x 2.2 Gpc (10 x 7 billion light-years). It is drawn as the matching
curved slab of our past light cone (comoving distances from a flat Planck-2018 cosmology,
as in build_grb_structure_model.py), lit by the Swift bursts with spectroscopic redshifts
that fall inside it (the bundled 2026-10-01 Swift table). The slab's glow marks the claimed
region; it is not a map of galaxies or of a confirmed wall.

Units: billions of light-years (comoving). The slab faces +z (the explorer camera); the
Milky Way lies 16.5 Gly behind it; the light-cone edges run the first 30% of the way there. A sphere the size of
Laniakea (0.52 Gly) sits beside the slab for scale.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_grb_structure_model as grb  # noqa: E402
from nebula_volume import add_cloud  # noqa: E402
from volume_glb import VolumeGLB  # noqa: E402

GLY_PER_MPC = 3.26156e-3
CENTER = (255.0, 27.75)               # RA, Dec degrees
Z_RANGE = (1.6, 2.1)
AXES_GLY = (10.0, 7.0)                # reported major, minor extent
CATALOG = Path(__file__).resolve().parents[1] / "content/visualizations/models/sources/catalogs/swift-grb-full-2026-10-01.tsv"


def unit(ra_deg, dec_deg):
    ra, dec = np.radians(ra_deg), np.radians(dec_deg)
    return np.stack([np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)], -1)


def local_frame():
    """Rows: east, north, outward (line of sight) at the center direction."""
    forward = unit(*CENTER)
    north_pole = np.array([0.0, 0.0, 1.0])
    east = np.cross(north_pole, forward)
    east /= np.linalg.norm(east)
    north = np.cross(forward, east)
    return np.stack([east, north, forward])


def build(output, seed=0x4CB):
    rng = np.random.default_rng(seed)
    near, far = (grb.comoving_distance_mpc(z) * GLY_PER_MPC for z in Z_RANGE)
    mid = (near + far) / 2
    half = [math.atan(a / 2 / mid) for a in AXES_GLY]  # angular half-widths (radians)
    frame = local_frame()

    def model(direction, radius):
        # Seen from outside the light cone looking back at Earth: east is model -x.
        local = (direction @ frame.T) * np.asarray(radius)[..., None]
        return np.stack([-local[..., 0], local[..., 1], local[..., 2] - mid], -1)

    # The slab: uniform in comoving volume, feathered at its edges.
    count = 26000
    u = rng.uniform(-1, 1, (count * 2, 2))
    inside = (u ** 2).sum(axis=1) <= 1
    u = u[inside][:count]
    radius = np.cbrt(rng.uniform(near ** 3, far ** 3, len(u)))
    tangent = np.tan(u * half)
    direction = np.column_stack([tangent, np.ones(len(u))]) @ frame
    direction /= np.linalg.norm(direction, axis=1, keepdims=True)
    points = model(direction, radius)
    edge = np.clip((1 - np.hypot(*u.T)) / 0.35, 0, 1) * np.clip(np.minimum(radius - near, far - radius) / 0.5, 0, 1)
    hue = rng.uniform(0, 1, len(u))[:, None]
    colors = (1 - hue) * np.array([0.55, 0.45, 1.0]) + hue * np.array([0.35, 0.7, 1.0])

    glb = VolumeGLB("Universe Scales Hercules-Corona Borealis builder")
    # A brighter rim and faint interior: the glow marks a claimed boundary, not matter.
    rim = np.exp(-((1 - np.hypot(*u.T)) / 0.1) ** 2)
    add_cloud(glb, "reported-region", points, colors, (0.025 + 0.16 * rim) * np.clip(edge + rim, 0, 1), 1 / 45, 22, alpha_floor=0.012)

    # Real bursts inside the footprint.
    events = []
    for row in grb.load_swift_rows(CATALOG):
        if not Z_RANGE[0] <= row["z"] <= Z_RANGE[1]:
            continue
        d = unit(row["ra"], row["dec"]) @ frame.T
        offsets = np.arctan2(d[:2], d[2]) / half
        if (offsets ** 2).sum() <= 1:
            r = grb.comoving_distance_mpc(row["z"]) * GLY_PER_MPC
            events.append((row["name"], row["z"], model(unit(row["ra"], row["dec"]), r)))
    for name, z, position in events:
        glb.node(f"GRB {name}", translation=position, scale=0.12, extras={
            "label": f"GRB {name} (z = {z:g})", "outline": True, "sphere": True, "markerRadius": 2.5})
    flashes = np.array([position for _, _, position in events])
    add_cloud(glb, "burst-flashes", flashes, np.tile([1.0, 0.92, 0.7], (len(flashes), 1)), np.ones(len(flashes)), 1 / 30, 26)

    # Light-cone edges to the Milky Way and the Milky Way itself.
    earth = np.array([0.0, 0.0, -mid])
    corners = []
    for sx, sy in ((1, 1), (1, -1), (-1, -1), (-1, 1)):
        d = np.array([math.tan(sx * half[0] * 0.98), math.tan(sy * half[1] * 0.98), 1.0]) @ frame
        corners.append(model(d / np.linalg.norm(d), near))
    # Only the first 30% of each edge: the full 16.5 Gly would dominate the model's bounds.
    reach = 0.3
    lines = np.array([[corner + reach * (earth - corner), corner] for corner in corners], np.float32).reshape(-1, 3)
    material = glb.unlit("light-cone", color=(0.6, 0.7, 1.0, 0.35))
    accessor = glb._accessor(lines, 5126, "VEC3", 34962, True)
    glb.node("light-cone-edges", [{"attributes": {"POSITION": accessor}, "material": material, "mode": 1}])
    tip = np.mean([corner + reach * (earth - corner) for corner in corners], axis=0)
    glb.node("toward-milky-way", translation=tip, extras={
        "label": f"Toward the Milky Way, {mid:.1f} billion light-years"})

    # Laniakea for scale: a 0.52 Gly glowing ball beside the slab.
    ball = rng.normal(size=(1500, 3))
    ball = ball / np.linalg.norm(ball, axis=1, keepdims=True) * np.cbrt(rng.random((1500, 1))) * 0.26
    spot = np.array([AXES_GLY[0] / 2 + 0.9, -AXES_GLY[1] / 2 + 0.6, 0.0])
    add_cloud(glb, "laniakea-for-scale", ball + spot, np.tile([1.0, 0.85, 0.6], (1500, 1)), np.full(1500, 0.5), 1 / 400, 2.5)
    glb.node("laniakea-label", translation=spot + [0, 0.45, 0], extras={"label": "Laniakea, for scale"})
    size = glb.write(output)
    return {"bytes": size, "near_far_gly": [round(near, 3), round(far, 3)], "bursts_inside": [e[0] for e in events],
            "half_angles_deg": [round(math.degrees(h), 2) for h in half]}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("output")
    args = parser.parse_args()
    print(json.dumps(build(args.output)))


if __name__ == "__main__":
    main()
