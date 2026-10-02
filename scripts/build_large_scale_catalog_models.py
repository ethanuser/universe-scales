#!/usr/bin/env python3
"""Build catalog-window diagrams for Virgo and the Sloan Great Wall.

The figures show public SDSS galaxies selected inside published/explicit
survey windows. They do not assign every selected galaxy to either structure.
All positions are kept in comoving space (with a local translation only).
"""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import urllib.parse
import urllib.request

import numpy as np

from fetch_model_assets import inspect_glb, pack_glb
from geo_glb_common import GLB

C_KM_S = 299792.458
H0 = 71.0
OMEGA_M = 0.27
OMEGA_L = 0.73
MPC_M = 3.0856775814913673e22
LY_M = 9.4607304725808e15
SDSS_SQL = "https://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch"
SDSS_POLICY = "https://www.sdss.org/collaboration/image-use-policy/"
SDSS_RELEASE = "https://www.sdss4.org/dr17/"
GOTT = "https://arxiv.org/html/astro-ph/0310571v2"
TULLY = "https://doi.org/10.1086/159999"
NASA_LOCAL_SUPERCLUSTER = "https://imagine.gsfc.nasa.gov/features/cosmic/local_supercluster_info.html"
CATALOG_REPO_DIR = "content/visualizations/models/sources/catalogs"

CONFIG = {
    "virgo": {
        "id": "virgo-supercluster-sdss-window",
        "item": "Virgo Supercluster",
        "value_m": 9.46e23,
        "ra": (175.0, 200.0),
        "dec": (-5.0, 25.0),
        "z": (0.0, 0.008),
        "center_ra": 187.5,
        "center_dec": 10.0,
        "radial_note": "SDSS redshift-space window z=0.000-0.008",
        "source": SDSS_RELEASE,
        "basis": TULLY,
        "basis_label": "Local Supercluster morphology",
        "selection_source": NASA_LOCAL_SUPERCLUSTER,
        "pose": {"pitch": 20, "yaw": 10},
        "color": (0.24, 0.78, 0.93),
        "license": "SDSS public-release catalog data: public domain; authored diagram code: CC-BY-4.0",
        "scale_note": "NASA describes the Local Supercluster as roughly 100 million light-years across; this is an approximate characteristic span, not a measured hard edge.",
    },
    "sloan": {
        "id": "sloan-great-wall-sdss-window",
        "item": "Sloan Great Wall",
        "value_m": 1.3885549116711151e25,
        "ra": (130.5, 210.0),  # 8.7 h to 14 h, as in Gott et al.
        "dec": (-2.0, 2.0),
        "distance_mpc": (215.0, 370.0),
        "center_ra": 170.25,
        "center_dec": 0.0,
        "radial_note": "Gott et al. slice window: comoving distance 215-370 Mpc",
        "source": SDSS_RELEASE,
        "basis": GOTT,
        "basis_label": "Published SDSS slice and 450 Mpc comoving wall-length estimate",
        "selection_source": GOTT,
        "pose": {"pitch": 65},
        "pre_rotation": {"y": 90},
        "color": (1.0, 0.62, 0.24),
        "license": "SDSS public-release catalog data: public domain; authored diagram code: CC-BY-4.0",
        "scale_note": "Gott et al. report 450 Mpc comoving (419 Mpc at the observed epoch), about 1.37 billion light-years; 450 Mpc is not 450 million light-years.",
    },
}


def hubble_distance_mpc(redshift):
    """Flat LCDM comoving radial distance using the Gott et al. parameters."""
    if redshift < 0:
        raise ValueError("negative redshifts cannot be assigned this cosmological distance")
    steps = max(64, math.ceil(redshift * 20000))
    dz = redshift / steps
    total = 0.0
    for index in range(steps):
        z = (index + 0.5) * dz
        e = math.sqrt(OMEGA_M * (1 + z) ** 3 + OMEGA_L)
        total += 1 / e
    return C_KM_S / H0 * dz * total


def redshift_for_distance_mpc(distance_mpc):
    low, high = 0.0, 2.0
    for _ in range(70):
        mid = (low + high) / 2
        if hubble_distance_mpc(mid) < distance_mpc:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def query_for(config):
    if "distance_mpc" in config:
        zlo, zhi = (redshift_for_distance_mpc(d) for d in config["distance_mpc"])
    else:
        zlo, zhi = config["z"]
    ralo, rahi = config["ra"]
    declo, dechi = config["dec"]
    return (
        "select ra,dec, "
        "case when survey in ('boss','eboss') then z_noqso else z end as z, "
        "case when survey in ('boss','eboss') then class_noqso else class end as class, "
        "case when survey in ('boss','eboss') then zwarning_noqso else zwarning end as zwarning, "
        "specObjID from SpecObj where sciencePrimary=1 "
        "and (case when survey in ('boss','eboss') then class_noqso else class end)='GALAXY' "
        "and (case when survey in ('boss','eboss') then zwarning_noqso else zwarning end)=0 "
        f"and (case when survey in ('boss','eboss') then z_noqso else z end) between {zlo:.9f} and {zhi:.9f} "
        f"and dec between {declo:.6f} and {dechi:.6f} "
        f"and ra between {ralo:.6f} and {rahi:.6f}"
    )


def fetch_catalog(config, path, timeout=120):
    query = query_for(config)
    url = SDSS_SQL + "?" + urllib.parse.urlencode({"cmd": query, "format": "csv"})
    request = urllib.request.Request(url, headers={"User-Agent": "UniverseScales catalog diagram builder/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read()
    if not payload.startswith(b"#Table1"):
        raise ValueError(f"SDSS returned an unexpected response for {config['item']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return payload


def read_catalog(path):
    with path.open(newline="", encoding="utf-8") as stream:
        lines = (line for line in stream if not line.startswith("#"))
        rows = list(csv.DictReader(lines))
    points = []
    seen = set()
    for row in rows:
        identifier = row.get("specObjID", "")
        if identifier in seen:
            continue
        seen.add(identifier)
        ra, dec, z = (float(row[key]) for key in ("ra", "dec", "z"))
        if not (math.isfinite(ra) and math.isfinite(dec) and math.isfinite(z)):
            continue
        if not 0 <= z <= 2:
            continue
        points.append({"specObjID": identifier, "ra": ra, "dec": dec, "z": z,
                       "distance_mpc": hubble_distance_mpc(z)})
    if not points:
        raise ValueError(f"No usable SDSS galaxies in {path}")
    return points


def sky_xyz(ra_deg, dec_deg, distance_mpc):
    ra, dec = math.radians(ra_deg), math.radians(dec_deg)
    return np.array([distance_mpc * math.cos(dec) * math.cos(ra),
                     distance_mpc * math.sin(dec),
                     distance_mpc * math.cos(dec) * math.sin(ra)], dtype=float)


def rotation_matrix_xyz(euler_degrees):
    x, y, z = (math.radians(euler_degrees.get(axis, 0.0)) for axis in "xyz")
    rx = np.array([[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]])
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rz = np.array([[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]])
    # THREE.Euler's intrinsic XYZ order, not extrinsic fixed-axis rotations.
    return rx @ ry @ rz


def frame_points(points, config):
    distances = [p["distance_mpc"] for p in points]
    if "distance_mpc" in config:
        center_distance = sum(config["distance_mpc"]) / 2
    else:
        center_distance = (min(distances) + max(distances)) / 2
    origin = sky_xyz(config["center_ra"], config["center_dec"], center_distance)
    positions = np.array([sky_xyz(p["ra"], p["dec"], p["distance_mpc"]) - origin for p in points])
    return positions, origin, center_distance


def boundary_lines(config, origin, center_distance):
    """Return the curved edges of a selection window, not a structure surface."""
    ralo, rahi = config["ra"]
    declo, dechi = config["dec"]
    if "distance_mpc" in config:
        rlo, rhi = config["distance_mpc"]
    else:
        rlo = 0.0
        rhi = hubble_distance_mpc(config["z"][1])
    segments = []

    def path(points):
        arr = np.array([sky_xyz(*p) - origin for p in points])
        segments.extend(np.stack((arr[:-1], arr[1:]), axis=1))

    steps = 24
    for radius in (rlo, rhi):
        for dec in (declo, dechi):
            path([(ra, dec, radius) for ra in np.linspace(ralo, rahi, steps + 1)])
        for ra in (ralo, rahi):
            path([(ra, dec, radius) for dec in np.linspace(declo, dechi, max(8, steps // 2) + 1)])
    for ra in (ralo, rahi):
        for dec in (declo, dechi):
            path([(ra, dec, radius) for radius in np.linspace(rlo, rhi, steps + 1)])
    return np.asarray(segments, dtype=np.float32).reshape(-1, 3)


def add_lines(glb, positions, color):
    accessor = glb._accessor(np.asarray(positions, np.float32), 5126, "VEC3", 34962, True)
    material = glb.material("Faint survey-window guide (not a structure boundary)",
                             color=(*color, 0.28), blend=True, rough=1)
    extensions = glb.doc.setdefault("extensionsUsed", [])
    if "KHR_materials_unlit" not in extensions:
        extensions.append("KHR_materials_unlit")
    glb.doc["materials"][material]["extensions"] = {"KHR_materials_unlit": {}}
    glb.doc["meshes"].append({"name": "Survey selection window edges", "primitives": [
        {"attributes": {"POSITION": accessor}, "material": material, "mode": 1}]})
    node = {"name": "Survey selection window; not a wall or supercluster edge",
            "mesh": len(glb.doc["meshes"]) - 1}
    glb.doc["nodes"].append(node)
    glb.doc["scenes"][0]["nodes"].append(len(glb.doc["nodes"]) - 1)


def add_galaxies(glb, positions, redshifts, config):
    positions = np.asarray(positions, dtype=np.float32)
    z = np.asarray(redshifts, float)
    zmin, zmax = float(z.min()), float(z.max())
    t = (z - zmin) / max(zmax - zmin, 1e-12)
    near = np.array(config["color"], dtype=float)
    far = np.array([0.96, 0.88, 0.72])
    colors = (near[None, :] * (1 - t[:, None]) + far[None, :] * t[:, None]).astype(np.float32)
    position_accessor = glb._accessor(positions, 5126, "VEC3", 34962, True)
    color_accessor = glb._accessor(colors, 5126, "VEC3", 34962)
    material = glb.material("SDSS galaxy positions; point symbols are enlarged",
                             color=(1, 1, 1, 1), rough=1)
    extensions = glb.doc.setdefault("extensionsUsed", [])
    if "KHR_materials_unlit" not in extensions:
        extensions.append("KHR_materials_unlit")
    glb.doc["materials"][material]["extensions"] = {"KHR_materials_unlit": {}}
    glb.doc["meshes"].append({"name": "Catalog galaxy positions", "primitives": [{
        "attributes": {"POSITION": position_accessor, "COLOR_0": color_accessor},
        "material": material, "mode": 0}]})
    glb.doc["nodes"].append({"name": "SDSS catalog galaxies (point symbols)", "mesh": len(glb.doc["meshes"]) - 1,
                            "extras": {"softPoints": True, "pointSize": {"max": 4.5, "perPixel": 1 / 90}}})
    glb.doc["scenes"][0]["nodes"].append(len(glb.doc["nodes"]) - 1)


def build_model(points, config):
    positions, origin, center_distance = frame_points(points, config)
    window = boundary_lines(config, origin, center_distance)
    glb = GLB("Universe Scales SDSS large-scale catalog-window diagram")
    add_lines(glb, window, config["color"])
    add_galaxies(glb, positions, [p["z"] for p in points], config)
    extents = np.ptp(np.concatenate((positions, window), axis=0), axis=0)
    reference_size_model_units = round(config["value_m"] / MPC_M, 12)
    content = pack_glb(glb.doc, bytes(glb.bin))
    stats = inspect_glb(content)
    return content, stats, reference_size_model_units, extents.tolist(), center_distance


def entry_for(key, config, catalog_path, glb_path, stats, reference_size_model_units, extents, center_distance, points):
    config_query = query_for(config)
    local_supercluster_note = (
        "A redshift-space window through the SDSS footprint around the Virgo direction, not a Virgo/Local Supercluster membership catalog. "
        "Tully describes the Local Supercluster as an irregular combination of the Virgo core, a flattened disk and discrete halo clouds; no hard enclosing surface is asserted. "
        if key == "virgo" else
        "A catalog selection window based on the equatorial Sloan slice and 215-370 Mpc comoving interval in Gott et al.; points are not individually certified Sloan Great Wall members and the wireframe is not the wall boundary. "
    )
    note = (local_supercluster_note + config["scale_note"] + " Coordinates are SDSS DR17 galaxy sky positions and spectroscopic redshifts. "
            "Distances are inferred from redshift in flat LCDM (H0=71 km/s/Mpc, Omega_m=0.27, Omega_Lambda=0.73); peculiar velocities, especially for Virgo, are not corrected. "
            "The cloud is only translated to its selection-window center; catalog positions retain their mutual comoving separations. Galaxy markers are enlarged point symbols, not galaxy diameters. "
            "The ruler is a separate approximate catalog quantity, not a fit to the sample's bounding box.")
    digest = hashlib.sha256(catalog_path.read_bytes()).hexdigest()
    return {
        "id": config["id"], "source": config["source"], "link_label": "SDSS catalog source",
        "representation": "catalog_diagram", "volume_semantics": "not_a_volume_measurement",
        "basis_url": config["basis"], "basis_label": config["basis_label"],
        "selection_url": config["selection_source"],
        "author": "Sloan Digital Sky Survey Collaboration; diagram by Universe Scales",
        "license": config["license"], "license_url": SDSS_POLICY,
        "matches": {"length": [config["item"]]}, "geometry": "catalog-position survey-window diagram",
        "presentation": {"reference_size": reference_size_model_units,
                          **({"pre_rotation": config["pre_rotation"]} if "pre_rotation" in config else {}),
                          **config["pose"], "layout_width_factor": 1.05, "focus_scale_factor": 1.05},
        "note": note,
        "processing": {"script": "scripts/build_large_scale_catalog_models.py",
                       "source_catalog": f"{CATALOG_REPO_DIR}/{catalog_path.name}",
                       "source_catalog_sha256": digest, "catalog_query_endpoint": SDSS_SQL,
                       "catalog_release": "SDSS DR17 SpecObj", "sql_selection": config_query,
                       "selection_rows": len(points), "displayed_rows": len(points),
                       "coordinate_frame": "equatorial J2000 to comoving Cartesian; local translation only",
                       "distance_model": {"H0_km_s_Mpc": H0, "Omega_m": OMEGA_M, "Omega_lambda": OMEGA_L,
                                          "distance": "integral of dz/E(z), flat LCDM"},
                       "window_extent_mpc_xyz": extents,
                       "reference_size_model_units": reference_size_model_units,
                       "window_center_comoving_distance_mpc": center_distance,
                       "catalog_value_m": config["value_m"],
                       "catalog_value_definition": "approximate literature characteristic span; catalog coordinates are authored in native Mpc and are not fitted to the selection-window bounds",
                       "source_license_note": "SDSS states public data-release data are public domain; cite the release and relevant science papers.",
                       "max_geometry_bytes": 1500000},
        "src": str(glb_path), "format": "glb", "gltf_version": "2.0",
        "bytes": stats["bytes"], "sha256": stats["sha256"],
        "extensions_used": stats["extensions_used"], "extensions_required": stats["extensions_required"],
        "decompression_required": stats["decompression_required"], "triangle_count": stats["triangle_count"],
        "animations": stats["animations"], "skins": stats["skins"],
        "mesh_count": stats["mesh_count"], "external_resources": stats["external_resources"],
    }


def run(output_dir, keys, refresh=False, catalog_dir=None):
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_mode = catalog_dir is not None
    catalog_dir = Path(catalog_dir) if snapshot_mode else output_dir
    catalog_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for key in keys:
        config = CONFIG[key]
        catalog_path = catalog_dir / f"sdss-dr17-{key}-window.csv"
        if refresh or not catalog_path.exists():
            if snapshot_mode and not refresh:
                raise FileNotFoundError(f"Required catalog snapshot is missing: {catalog_path}")
            fetch_catalog(config, catalog_path)
        points = read_catalog(catalog_path)
        glb_path = output_dir / f"{config['id']}.glb"
        content, stats, reference_size, extents, center_distance = build_model(points, config)
        if stats["bytes"] > 1_500_000:
            raise ValueError(f"{glb_path.name} exceeds 1.5 MB: {stats['bytes']}")
        glb_path.write_bytes(content)
        entry = entry_for(key, config, catalog_path, glb_path, stats, reference_size, extents, center_distance, points)
        entry_path = output_dir / f"{config['id']}-entry.json"
        entry_path.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
        entries.append(entry)
        print(f"{config['item']}: {len(points)} catalog rows; {stats['bytes']:,} byte GLB; "
              f"reference {reference_size:.2f} GLB Mpc; output {glb_path}")
    (output_dir / "entries.json").write_text(json.dumps({"models": entries}, indent=2) + "\n", encoding="utf-8")
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("/private/tmp/length-catalogs"))
    parser.add_argument("--catalog-dir", type=Path,
                        help="Use exact CSV snapshots from this directory; missing files fail instead of querying SDSS")
    parser.add_argument("--catalogs", nargs="+", choices=CONFIG, default=list(CONFIG))
    parser.add_argument("--refresh", action="store_true", help="redownload source catalogs")
    args = parser.parse_args()
    run(args.output_dir, args.catalogs, args.refresh, catalog_dir=args.catalog_dir)


if __name__ == "__main__":
    main()
