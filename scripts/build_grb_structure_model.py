#!/usr/bin/env python3
"""Build a GRB catalog view of the disputed Hercules-Corona Borealis feature.

Only rows with explicitly spectroscopic redshifts from the NASA Swift table are
plotted. The angular map is dimensionless; only the separate claimed-extent
ruler is calibrated. No physical wall surface or 3D membership is inferred.
"""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from fetch_model_assets import pack_glb
from geo_glb_common import GLB

CATALOG_URL = "https://swift.gsfc.nasa.gov/archive/grb_table/fullview/"
C_M_S = 299_792_458.0
MPC_M = 3.085677581491367e22
GLY_M = 9.4607304725808e24
H0 = 67.4  # km s^-1 Mpc^-1, Planck 2018 flat-LCDM reference cosmology.
OMEGA_M = 0.315
Z_MIN, Z_MAX = 1.6, 2.1
CLAIMED_EXTENT_M = 10.0 * GLY_M
REGION = "published selection: Galactic 0 <= l <= 180 deg, b >= 0 deg"

# ICRS/J2000 equatorial unit vector to Galactic Cartesian (IAU 1958 system).
EQ_TO_GAL = np.array([
    [-0.0548755604162154, -0.8734370902348850, -0.4838350155487132],
    [0.4941094278755837, -0.4448296299600112, 0.7469822444972189],
    [-0.8676661490190047, -0.1980763734312015, 0.4559837761750669],
])


def _header_key(value):
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _column(headers, *names):
    normalized = {_header_key(name): index for index, name in enumerate(headers)}
    for name in names:
        if _header_key(name) in normalized:
            return normalized[_header_key(name)]
    raise ValueError(f"Swift TSV is missing required column: {names[0]}")


def _angle_degrees(value, ra=False):
    """Parse decimal-degree catalog values or explicit sexagesimal coordinates.

    Swift full-view RA columns are decimal degrees; only colon-delimited RA is
    interpreted as hours. Never infer a unit from the numeric magnitude.
    """
    value = value.strip().replace("−", "-")
    if not value or value.lower() in {"n/a", "na", "none", "-"}:
        return None
    if not re.match(r"^\s*[+-]?\d+:\d+:", value):
        match = re.match(r"^\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))(?:\s|$)", value)
        if not match:
            return None
        return float(match.group(1))
    parts = value.split(":")
    if len(parts) != 3:
        return None
    sign = -1 if parts[0].startswith("-") else 1
    first = abs(float(parts[0]))
    result = first + float(parts[1]) / 60 + float(parts[2]) / 3600
    result *= 15 if ra else 1
    return sign * result


def parse_spectroscopic_redshift(value):
    """Return z only when the Swift redshift field explicitly says spectral."""
    if (re.search(r"photometr|photo-?z", value, re.IGNORECASE)
            or re.search(r"[<>≤≥]|\blimit\b", value, re.IGNORECASE)):
        return None
    match = re.search(r"(?<![\w.])([0-9]+(?:\.[0-9]*)?|\.[0-9]+)", value)
    if not match or not re.search(r"absorption|emission|spectroscop|spectrum", value, re.IGNORECASE):
        return None
    z = float(match.group(1))
    return z if math.isfinite(z) and z >= 0 else None


def load_swift_rows(path):
    """Read the official full-view tab-separated export without inference."""
    raw = Path(path).read_bytes()
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = raw.decode("latin-1")
    reader = csv.reader(io.StringIO(decoded, newline=""), delimiter="\t")
    headers = next(reader, None)
    if not headers:
        raise ValueError("Swift TSV is empty")
    name_i = _column(headers, "GRB")
    z_i = _column(headers, "Redshift")
    coords = []
    for prefix in ("UVOT", "XRT", "BAT"):
        try:
            coords.append((_column(headers, f"{prefix} RA(J2000)"),
                           _column(headers, f"{prefix} Dec(J2000)"), prefix))
        except ValueError:
            continue
    if not coords:
        raise ValueError("Swift TSV needs UVOT, XRT, or BAT RA/Dec columns")

    events = []
    for row in reader:
        if len(row) < len(headers):
            continue
        z = parse_spectroscopic_redshift(row[z_i])
        if z is None or not Z_MIN <= z <= Z_MAX:
            continue
        position = None
        for ra_i, dec_i, source in coords:
            ra = _angle_degrees(row[ra_i], ra=True)
            dec = _angle_degrees(row[dec_i])
            if ra is not None and dec is not None and -90 <= dec <= 90:
                position = (ra % 360, dec, source)
                break
        if position is None:
            continue
        events.append({"name": row[name_i].strip(), "ra": position[0], "dec": position[1],
                       "position_source": position[2], "z": z})
    if not events:
        raise ValueError("No spectroscopic Swift events found in the requested redshift slice")
    return events


def comoving_distance_mpc(z, steps=2048):
    """Flat-LCDM radial comoving distance, numerical Simpson integration."""
    if z < 0 or not math.isfinite(z) or steps < 2 or steps % 2:
        raise ValueError("z must be finite and nonnegative; steps must be positive and even")
    h0_si = H0 * 1000 / 3.085677581491367e22
    dz = z / steps
    sample_z = np.linspace(0, z, steps + 1)
    expansion = np.sqrt(OMEGA_M * (1 + sample_z) ** 3 + (1 - OMEGA_M))
    integrand = 1 / expansion
    integral = dz / 3 * (integrand[0] + integrand[-1]
                         + 4 * integrand[1:-1:2].sum() + 2 * integrand[2:-1:2].sum())
    return C_M_S / h0_si * integral / MPC_M


def galactic_coordinates(ra_deg, dec_deg):
    ra, dec = math.radians(ra_deg), math.radians(dec_deg)
    equatorial = np.array([math.cos(dec) * math.cos(ra), math.cos(dec) * math.sin(ra), math.sin(dec)])
    x, y, z = EQ_TO_GAL @ equatorial
    return math.degrees(math.atan2(y, x)) % 360, math.degrees(math.asin(np.clip(z, -1, 1)))


def is_published_window(ra_deg, dec_deg):
    lon, lat = galactic_coordinates(ra_deg, dec_deg)
    return 0 <= lon <= 180 and lat >= 0


def cartesian_comoving_mpc(ra_deg, dec_deg, z):
    """Observer-centered comoving position; no wall or source depth is invented."""
    ra, dec = math.radians(ra_deg), math.radians(dec_deg)
    radius = comoving_distance_mpc(z)
    return radius * np.array([math.cos(dec) * math.cos(ra),
                              math.cos(dec) * math.sin(ra), math.sin(dec)])


def _add_lines(glb, name, lines, color):
    points = np.asarray(lines, dtype=np.float32).reshape(-1, 3)
    material = glb.material(name, color=(*color, 1), rough=1)
    if "KHR_materials_unlit" not in glb.doc.setdefault("extensionsUsed", []):
        glb.doc["extensionsUsed"].append("KHR_materials_unlit")
    glb.doc["materials"][material]["extensions"] = {"KHR_materials_unlit": {}}
    accessor = glb._accessor(points, 5126, "VEC3", 34962, True)
    mesh = {"name": name, "primitives": [{"attributes": {"POSITION": accessor},
                                            "material": material, "mode": 1}]}
    glb.doc["meshes"].append(mesh)
    node = {"name": name, "mesh": len(glb.doc["meshes"]) - 1}
    glb.doc["nodes"].append(node)
    glb.doc["scenes"][0]["nodes"].append(len(glb.doc["nodes"]) - 1)


def mollweide(longitude_deg, latitude_deg):
    """Equal-area sky projection in dimensionless chart coordinates."""
    # Preserve both chart edges, -180 and +180, so graticules do not jump
    # across the whole ellipse at their last segment.
    longitude = math.radians(math.remainder(longitude_deg, 360))
    latitude = math.radians(latitude_deg)
    if abs(abs(latitude) - math.pi / 2) < 1e-12:
        theta = math.copysign(math.pi / 2, latitude)
    else:
        theta = latitude
        for _ in range(12):
            residual = 2 * theta + math.sin(2 * theta) - math.pi * math.sin(latitude)
            derivative = 2 + 2 * math.cos(2 * theta)
            if abs(derivative) < 1e-12:
                break
            step = residual / derivative
            theta -= step
            if abs(step) < 1e-12:
                break
    return (2 * math.sqrt(2) / math.pi * longitude * math.cos(theta),
            math.sqrt(2) * math.sin(theta))


def _projected_line(points, scale, center=(0.0, 0.0)):
    return [(center[0] + x * scale, center[1] + y * scale, 0.0) for x, y in points]


def sky_chart_lines(scale, center=(0.0, 0.0), samples=72):
    """Mollweide outline and angular graticule; dimensions are chart-only."""
    lines = []
    outline = [(2 * math.sqrt(2) * math.cos(2 * math.pi * i / samples),
                math.sqrt(2) * math.sin(2 * math.pi * i / samples))
               for i in range(samples + 1)]
    lines.append(_projected_line(outline, scale, center))
    for latitude in (-60, 0, 60):
        points = [mollweide(longitude, latitude)
                  for longitude in np.linspace(-180, 180, samples + 1)]
        lines.append(_projected_line(points, scale, center))
    for longitude in range(-135, 180, 45):
        points = [mollweide(longitude, latitude)
                  for latitude in np.linspace(-89.9, 89.9, samples + 1)]
        lines.append(_projected_line(points, scale, center))
    return lines


def _segments_for_lines(lines):
    return [segment for line in lines for segment in zip(line[:-1], line[1:])]


def redshift_rug(events, x_min, x_max, y_center, y_jitter=0.045):
    """Dimensionless 1D distance strip; vertical offsets are display jitter."""
    low = comoving_distance_mpc(Z_MIN)
    high = comoving_distance_mpc(Z_MAX)
    points = []
    for index, event in enumerate(events):
        distance = comoving_distance_mpc(event["z"])
        x = x_min + (distance - low) / (high - low) * (x_max - x_min)
        # Stable, bounded offsets prevent coincident redshift samples hiding each other.
        offset = (((index * 37) % 17) / 16 - 0.5) * 2 * y_jitter
        points.append((x, y_center + offset, 0.0))
    return points


def build_glb(events):
    """Render angular observations and a detached, literature-inferred size key."""
    if not events:
        raise ValueError("At least one catalog event is required")
    glb = GLB("Universe Scales Swift GRB catalog view")
    selected = [event for event in events if is_published_window(event["ra"], event["dec"])]

    # The diagram's total x-span is one unit, the separate 10 Gly reference bar.
    # Mollweide x/y and the distance-strip y offsets are chart coordinates only.
    bar_span = 1.0
    map_scale = 0.68 / (4 * math.sqrt(2))
    map_center = (0.0, 0.25)
    positions, colors = [], []
    for event in events:
        longitude, latitude = galactic_coordinates(event["ra"], event["dec"])
        x, y = mollweide(longitude, latitude)
        positions.append((map_center[0] + x * map_scale, map_center[1] + y * map_scale, 0.0))
        in_2020_guide = is_published_window(event["ra"], event["dec"])
        colors.append((1.0, 0.58, 0.16) if in_2020_guide else (0.25, 0.62, 0.82))
    positions = np.asarray(positions, dtype=np.float32)
    colors = np.asarray(colors, dtype=np.float32)
    if "KHR_materials_unlit" not in glb.doc.setdefault("extensionsUsed", []):
        glb.doc["extensionsUsed"].append("KHR_materials_unlit")
    material = glb.material("Swift GRB angular positions; amber marks 2020 display guide",
                             color=(1, 1, 1, 1))
    glb.doc["materials"][material]["extensions"] = {"KHR_materials_unlit": {}}
    pos_accessor = glb._accessor(positions, 5126, "VEC3", 34962, True)
    color_accessor = glb._accessor(colors, 5126, "VEC3", 34962)
    glb.doc["meshes"].append({"name": "Swift spectroscopic GRBs; dimensionless sky projection",
        "primitives": [{"attributes": {"POSITION": pos_accessor, "COLOR_0": color_accessor},
                        "material": material, "mode": 0}]})
    glb.doc["nodes"].append({"name": "Observed GRB directions, Mollweide chart; not a 3D map", "mesh": 0,
        "extras": {"softPoints": True, "pointSize": {"max": 6, "perPixel": 1 / 75}}})
    glb.doc["scenes"][0]["nodes"].append(0)

    grid = sky_chart_lines(map_scale, map_center)
    _add_lines(glb, "Galactic longitude and latitude graticule", _segments_for_lines(grid),
               (0.32, 0.43, 0.5))

    # This is the broad quadrant highlighted as likely in Horvath et al. (2020),
    # not the original 2014 one-eighth-sky concentration cap.
    # Sample the meridians: Mollweide maps them to curves, not straight edges.
    guide = ([mollweide(0, latitude) for latitude in np.linspace(0, 90, 37)]
             + [mollweide(longitude, 90) for longitude in np.linspace(0, 180, 37)[1:]]
             + [mollweide(180, latitude) for latitude in np.linspace(90, 0, 37)[1:]]
             + [mollweide(longitude, 0) for longitude in np.linspace(180, 0, 37)[1:]])
    guide_line = _projected_line(guide, map_scale, map_center)
    _add_lines(glb, "2020 paper broad Galactic display guide; not 2014 cap",
               list(zip(guide_line[:-1], guide_line[1:])), (0.98, 0.65, 0.18))

    # Inset: the redshift-to-comoving-distance mapping, not 3D depth geometry.
    strip_x0, strip_x1 = -0.31, 0.31
    strip_y = -0.06
    _add_lines(glb, "Comoving distance strip axis", [
        ((strip_x0, strip_y, 0), (strip_x1, strip_y, 0)),
        ((strip_x0, strip_y - 0.018, 0), (strip_x0, strip_y + 0.018, 0)),
        ((strip_x1, strip_y - 0.018, 0), (strip_x1, strip_y + 0.018, 0)),
    ], (0.36, 0.48, 0.56))
    rug = redshift_rug(events, strip_x0, strip_x1, strip_y)
    rug_array = np.asarray(rug, dtype=np.float32)
    rug_accessor = glb._accessor(rug_array, 5126, "VEC3", 34962, True)
    rug_material = glb.material("Redshift-derived comoving distance samples", color=(0.96, 0.52, 0.19, 1))
    glb.doc["materials"][rug_material]["extensions"] = {"KHR_materials_unlit": {}}
    glb.doc["meshes"].append({"name": "1D comoving-distance rug; offsets are display jitter",
        "primitives": [{"attributes": {"POSITION": rug_accessor}, "material": rug_material, "mode": 0}]})
    glb.doc["nodes"].append({"name": "Redshift-to-distance inset; no 3D membership volume",
        "mesh": len(glb.doc["meshes"]) - 1,
        "extras": {"softPoints": True, "pointSize": {"max": 5, "perPixel": 1 / 85}}})
    glb.doc["scenes"][0]["nodes"].append(len(glb.doc["nodes"]) - 1)

    # The ruler alone carries the claimed physical length; panel and chart use diagram units.
    ruler_y = -0.29
    x0, x1 = -bar_span / 2, bar_span / 2
    _add_lines(glb, "Claimed extent scale bar", [
        ((x0, ruler_y, 0), (x0, ruler_y + 0.025, 0)),
        ((x0, ruler_y, 0), (x1, ruler_y, 0)),
        ((x1, ruler_y, 0), (x1, ruler_y + 0.025, 0)),
    ], (0.96, 0.76, 0.32))
    glb.label_node("Ruler label", [0, ruler_y + 0.055, 0],
                   "10 Gly")
    for node in glb.doc["nodes"]:
        if node.get("extras", {}).get("label"):
            node["extras"]["labelAxis"] = {"axis": "x", "length": 1, "minPixelLength": 35}
    return pack_glb(glb.doc, bytes(glb.bin)), len(events), len(selected)


def sample_comoving_span_gly(events):
    """Maximum pairwise span of observer-centered positions; not a wall size."""
    positions = np.asarray([cartesian_comoving_mpc(e["ra"], e["dec"], e["z"]) for e in events])
    if len(positions) < 2:
        return 0.0
    return float(np.linalg.norm(positions[:, None] - positions[None, :], axis=-1).max()
                 * MPC_M / GLY_M)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True,
                        help="NASA Swift GRB Table full-view tab-separated export")
    parser.add_argument("--output-dir", type=Path, default=Path("/private/tmp/length-grb"))
    args = parser.parse_args()
    events = load_swift_rows(args.catalog)
    model, count, selected = build_glb(events)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / "hercules-corona-borealis-grb-catalog.glb"
    path.write_bytes(model)
    if len(model) > 1_500_000:
        path.unlink()
        raise SystemExit(f"Model exceeds 1.5 MB budget: {len(model):,} bytes")
    metadata = {
        "catalog_url": CATALOG_URL,
        "catalog_sha256": hashlib.sha256(args.catalog.read_bytes()).hexdigest(),
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "redshift_range_inclusive": [Z_MIN, Z_MAX],
        "spectroscopic_events": count,
        "horvath_2020_broad_guide_events": selected,
        "cosmology": {"model": "flat LCDM", "H0_km_s_Mpc": H0, "Omega_m": OMEGA_M},
        "claimed_extent_m": CLAIMED_EXTENT_M,
        "representation": "dimensionless angular information diagram, not a scaled 3D map",
        "diagram_reference_bar_units": 1.0,
        "catalog_point_max_pairwise_comoving_span_gly": sample_comoving_span_gly(events),
        "model_bytes": len(model),
    }
    (args.output_dir / "build-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"{path}: {len(model):,} bytes; {count} spectroscopic GRBs in slice, "
          f"{selected} within published angular selection")


if __name__ == "__main__":
    main()
