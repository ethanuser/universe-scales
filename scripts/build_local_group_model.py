#!/usr/bin/env python3
"""Build the Local Group in 3D from McConnachie's nearby-galaxy catalog.

    ./venv/bin/python scripts/build_local_group_model.py mcconnachie.tsv PIA10748.jpg OUT.glb

mcconnachie.tsv is VizieR J/AJ/144/4 (McConnachie 2012, AJ 144, 4, as updated online) with
columns Name, SubG, GLON, GLAT, D, D(LG), VMag, R2:
https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/AJ/144/4&-out=Name,SubG,GLON,GLAT,D,D(LG),VMag,R2&-out.max=unlimited

Galaxies within 1,620 kpc of the Local Group barycenter (the listed ~10.6 million light-year
span) are placed at their catalog positions (heliocentric galactic coordinates, kpc), with the
galactic plane horizontal. Dwarf galaxies are glowing blobs sized by their half-light radii and
brightened by luminosity. The Milky Way uses NASA/JPL's face-on concept (PIA10748, as in
build_milky_way_model.py); M31 and M33 are exponential star disks of their measured sizes at
their measured inclinations and position angles. A faint sphere marks M31's gas halo, which
Project AMIGA traced to about 1.3 million light-years (Lehner et al. 2020).
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_laniakea_galaxies import equatorial_to_galactic, galactic_unit  # noqa: E402
from nebula_volume import add_cloud  # noqa: E402
from volume_glb import VolumeGLB, sample_by_brightness  # noqa: E402

LG_RADIUS_KPC = 1620.0
SUN_TO_GC_KPC = 8.18
# Disk parameters: (RA, Dec of center, inclination deg, PA deg east of north, scale length kpc, disk radius kpc)
DISKS = {
    "Andromeda Galaxy (M31)": ("Andromeda", 10.6847, 41.2690, 77.0, 38.0, 5.3, 23.0),
    "Triangulum Galaxy (M33)": ("Triangulum", 23.4621, 30.6599, 54.0, 23.0, 1.8, 9.0),
}
LABELS = ["LMC", "SMC", "NGC 6822", "IC 1613", "WLM", "Leo I", "NGC 185", "NGC 147", "IC 10"]
M31_HALO_KPC = 1.3e6 / 3261.56  # 1.3 million light-years
# Milky Way R200 from Cautun et al. 2020's M200 = 1.08e12 Msun (200 x critical density, h = 0.68).
MW_HALO_KPC = 215.0


def to_model(galactic_xyz):
    """Heliocentric galactic (x to GC, y to l = 90, z to NGP) -> model (x, y up, z)."""
    g = np.asarray(galactic_xyz, dtype=float)
    return np.stack([g[..., 0], g[..., 2], -g[..., 1]], -1)


def load(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        parts = [p.strip() for p in line.split("\t")]
        if len(parts) != 8 or line.startswith("#") or parts[0] in ("Name", "") or parts[0].startswith("-"):
            continue
        name, group, l, b, d, dlg, vmag, r2 = parts
        def num(value):
            try:
                return float(value)
            except ValueError:
                return math.nan
        rows.append({"name": name, "group": group, "l": num(l), "b": num(b), "d": num(d), "dlg": num(dlg),
                     "vmag": num(vmag), "r2_pc": num(r2)})
    return rows


def disk_frame(ra, dec, inclination, pa):
    """Unit vectors (galactic frame) of a disk's major axis, second in-plane axis, and normal."""
    def equatorial(ra_deg, dec_deg):
        a, d = math.radians(ra_deg), math.radians(dec_deg)
        return np.array([math.cos(d) * math.cos(a), math.cos(d) * math.sin(a), math.sin(d)])
    n = equatorial(ra, dec)
    north = np.array([0.0, 0.0, 1.0]) - n * n[2]
    north /= np.linalg.norm(north)
    east = np.cross(north, n)
    p, i = math.radians(pa), math.radians(inclination)
    major = math.cos(p) * north + math.sin(p) * east
    minor_sky = -math.sin(p) * north + math.cos(p) * east
    # The north-west side is the near side (dust lanes), so the far side lies toward +minor.
    second = math.cos(i) * minor_sky + math.sin(i) * n
    rotation = np.array([[-0.0548755604, -0.8734370902, -0.4838350155],
                         [0.4941094279, -0.4448296300, 0.7469822445],
                         [-0.8676661490, -0.1980763734, 0.4559837762]])
    return rotation @ major, rotation @ second


def exponential_disk(rng, count, scale, radius, thickness):
    r = rng.gamma(2.0, scale, count * 2)
    r = r[r < radius][:count]
    angle = rng.uniform(0, 2 * math.pi, len(r))
    # Two loose spiral arms as a mild density modulation.
    arms = rng.random(len(r)) < 0.45
    angle[arms] = (np.log(r[arms] / scale + 0.3) / math.tan(math.radians(15)) + rng.choice([0, math.pi], arms.sum())
                   + rng.normal(0, 0.35, arms.sum()))
    height = rng.laplace(0, thickness, len(r))
    return r * np.cos(angle), r * np.sin(angle), height, r


def build(catalog, milky_way_image, output, seed=0x1C41):
    rng = np.random.default_rng(seed)
    rows = load(catalog)
    glb = VolumeGLB("Universe Scales Local Group builder")
    positions = {}
    dwarfs = []
    for row in rows:
        if row["name"].startswith("The Galaxy"):
            continue
        if not (row["dlg"] <= LG_RADIUS_KPC) or math.isnan(row["d"]):
            continue
        xyz = to_model(galactic_unit(row["l"], row["b"]) * row["d"])
        positions[row["name"]] = xyz
        if row["name"] in ("Andromeda", "Triangulum"):
            continue
        dwarfs.append((xyz, row))

    # Dwarfs: blobs of points with a Gaussian profile ~ 2x half-light radius, brightness by luminosity.
    points, colors, alphas = [], [], []
    for xyz, row in dwarfs:
        # The Magellanic Clouds have no catalog half-light radius; ~1.5 and ~1 kpc are illustrative.
        default_pc = {"LMC": 1500, "SMC": 1000}.get(row["name"], 300)
        r_kpc = (row["r2_pc"] if not math.isnan(row["r2_pc"]) else default_pc) / 1000
        luminosity = 10 ** (-0.4 * ((row["vmag"] if not math.isnan(row["vmag"]) else -8) + 8))
        count = int(np.clip(40 + 40 * math.log10(luminosity + 1), 30, 400))
        points.append(xyz + rng.normal(0, max(r_kpc, 0.15), (count, 3)))
        colors.append(np.tile([1.0, 0.9, 0.78], (count, 1)))
        alphas.append(np.full(count, np.clip(0.25 + 0.08 * math.log10(luminosity + 1), 0.2, 0.7)))
    # One soft glow per galaxy, brighter for more luminous ones, so the group reads at a glance.
    centers = np.array([xyz for xyz, _ in dwarfs])
    glow = np.array([np.clip(0.18 + 0.06 * (-(row["vmag"] if not math.isnan(row["vmag"]) else -8) - 8), 0.12, 0.6)
                     for _, row in dwarfs])
    add_cloud(glb, "galaxy-glows", centers, np.tile([1.0, 0.92, 0.8], (len(centers), 1)), glow * 1.4, 1 / 110, 12)
    add_cloud(glb, "dwarf-galaxies", np.concatenate(points), np.concatenate(colors), np.concatenate(alphas), 1 / 650, 2.6)

    # Milky Way from the NASA/JPL face-on concept (center px, Sun px as in build_milky_way_model.py).
    image = Image.open(milky_way_image).convert("RGB")
    cx, cy, sun_y = 2800.0, 2780.0, 3867.5
    kpc_per_px = SUN_TO_GC_KPC / (sun_y - cy)
    crop = image.crop((int(cx - 2450), int(cy - 2450), int(cx + 2450), int(cy + 2450))).resize((700, 700), Image.LANCZOS)
    crop = crop.filter(ImageFilter.GaussianBlur(0.6))
    u, v, rgb, lum = sample_by_brightness(crop, 9000, rng, gamma=1.6, floor=0.06)
    px_u, px_v = cx - 2450 + u * 4900, cy - 2450 + v * 4900
    # Image up is toward the Galactic Center, image left is l = 90 (seen from the north pole).
    x_gal = (sun_y - px_v) * kpc_per_px
    y_gal = (cx - px_u) * kpc_per_px
    z_gal = rng.laplace(0, 0.25, len(u))
    mw = to_model(np.stack([x_gal, y_gal, z_gal], 1))
    add_cloud(glb, "milky-way", mw, rgb / np.maximum(rgb.max(axis=1, keepdims=True), 1e-3),
              np.clip(0.3 + 0.7 * lum, 0.3, 1), 1 / 700, 2.6)
    positions["Milky Way"] = to_model(np.array([SUN_TO_GC_KPC, 0, 0]))
    big = [positions["Milky Way"]]

    for label, (key, ra, dec, inc, pa, scale, radius) in DISKS.items():
        major, second = disk_frame(ra, dec, inc, pa)
        a, b, h, r = exponential_disk(rng, 7000 if key == "Andromeda" else 3500, scale, radius, 0.3)
        normal = np.cross(major, second)
        offsets = np.outer(a, major) + np.outer(b, second) + np.outer(h, normal)
        center_gal = galactic_unit(*equatorial_to_galactic(ra, dec)) * next(row["d"] for row in rows if row["name"] == key)
        cloud = to_model(center_gal + offsets)
        warm = np.clip(1 - r / (2.5 * scale), 0, 1)[:, None]
        add_cloud(glb, label, cloud, warm * np.array([1.0, 0.86, 0.62]) + (1 - warm) * np.array([0.7, 0.8, 1.0]),
                  np.full(len(cloud), 0.6), 1 / 700, 2.6)
        positions[label] = to_model(center_gal)
        big.append(positions[label])
    add_cloud(glb, "large-galaxy-glows", np.array(big), np.tile([1.0, 0.9, 0.75], (len(big), 1)),
              np.array([1.0, 1.0, 0.75]), 1 / 55, 22)

    def glowing_sphere(name, center, radius, count, color, interior, rim_alpha, per_pixel, max_px):
        """A faint ball with a brighter limb: reads as a soft boundary, not a solid."""
        points = rng.normal(size=(count, 3))
        points /= np.linalg.norm(points, axis=1, keepdims=True)
        r = radius * np.cbrt(rng.random((count, 1)))
        rim = np.exp(-((1 - r[:, 0] / radius) / 0.08) ** 2)
        add_cloud(glb, name, points * r + center, np.tile(color, (count, 1)), interior + rim_alpha * rim,
                  per_pixel, max_px, alpha_floor=0.008)

    # M31's circumgalactic gas halo (Project AMIGA).
    glowing_sphere("m31-gas-halo", positions["Andromeda Galaxy (M31)"], M31_HALO_KPC, 3000,
                   [0.45, 0.6, 1.0], 0.008, 0.05, 1 / 40, 20)
    glowing_sphere("milky-way-halo", to_model(np.array([SUN_TO_GC_KPC, 0, 0])), MW_HALO_KPC, 1800,
                   [1.0, 0.8, 0.55], 0.01, 0.06, 1 / 45, 18)
    # The listed ~10.6 million light-year span, centered between the Milky Way and M31.
    barycenter = (positions["Milky Way"] + positions["Andromeda Galaxy (M31)"]) / 2
    glowing_sphere("local-group-span", barycenter, LG_RADIUS_KPC, 3500, [0.6, 0.55, 0.9], 0.0, 0.1, 1 / 50, 16)

    for short in LABELS:
        match = next((key for key in positions if key == short or key.startswith(short + " (")), None)
        if match and match != short:
            positions[short] = positions[match]
    for name in ["Milky Way", *DISKS, *LABELS]:
        if name in positions:
            text = {"Milky Way": "Milky Way (you are here)"}.get(name, name)
            glb.node(f"label-{name}", translation=positions[name], extras={"label": text})
    glb.node("label-halo", translation=positions["Andromeda Galaxy (M31)"] + np.array([0, M31_HALO_KPC * 0.75, 0]),
             extras={"label": "Andromeda's gas halo, 1.3 million light-years"})
    glb.node("label-mw-halo", translation=positions["Milky Way"] + np.array([0, -MW_HALO_KPC * 0.85, 0]),
             extras={"label": "Milky Way's dark-matter halo"})
    glb.node("label-span", translation=barycenter + np.array([0, LG_RADIUS_KPC * 0.92, 0]),
             extras={"label": "Approximate Local Group span, about 10 million light-years"})
    size = glb.write(output)
    return {"bytes": size, "galaxies": len(dwarfs) + 4}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("catalog")
    parser.add_argument("milky_way_image")
    parser.add_argument("output")
    args = parser.parse_args()
    print(json.dumps(build(args.catalog, args.milky_way_image, args.output)))


if __name__ == "__main__":
    main()
