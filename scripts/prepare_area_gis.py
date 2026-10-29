#!/usr/bin/env python3
"""Acquire public boundary GeoJSON and prepare compact, sourced Area outlines."""

import argparse
import hashlib
import json
import urllib.request
from datetime import date
from pathlib import Path


MAX_VERTICES = 100_000
MAX_TOTAL_BYTES = 2_000_000
PINNED_SOURCE_SHA256 = {
    "natural_earth_countries": "239eec57ac17f100a11e2536cffc56752c318b50ae765b0918ff7aab4ce8f255",
    "natural_earth_admin1": "22d0e3ad85eb3e27f17cabf8ba2d50e554fbc27a87796ff891d958185da62fb5",
    "natural_earth_marine": "53f865e8ffa966cdd402145c82c5cd14ee7ce974cd0eb9a3f59f03a4cfd2d66c",
    "natural_earth_lakes": "2d036f53dedec578001c5c30c2959ee7d4eebc1306900fa4367c49929ec8f2d9",
    "natural_earth_land": "1ac90796408bc6ad6911d69448485d3c4dbf2190370080368a09976e1c9f7416",
    "census_nyc_counties": "da4051717caec55c75e3748c3608c2a3dbde8d1ff401bbaf4f952e3c3fb63ef1",
}
SOURCES = {
    "natural_earth_countries": {
        "title": "Natural Earth 1:10m Admin-0 Countries",
        "snapshot_date": "2026-10-28",
        "file": "ne_10m_admin_0_countries.geojson",
        "url": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_0_countries.geojson",
        "rights": "Natural Earth public domain",
        "author": "Natural Earth contributors",
        "license": "Public domain",
        "license_url": "https://www.naturalearthdata.com/about/terms-of-use/",
    },
    "natural_earth_admin1": {
        "title": "Natural Earth 1:10m Admin-1 States and Provinces",
        "snapshot_date": "2026-10-28",
        "file": "ne_10m_admin_1_states_provinces.geojson",
        "url": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson",
        "rights": "Natural Earth public domain",
        "author": "Natural Earth contributors",
        "license": "Public domain",
        "license_url": "https://www.naturalearthdata.com/about/terms-of-use/",
    },
    "natural_earth_lakes": {
        "title": "Natural Earth 1:10m Lakes",
        "snapshot_date": "2026-10-28",
        "file": "ne_10m_lakes.geojson",
        "url": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_lakes.geojson",
        "rights": "Natural Earth public domain",
        "author": "Natural Earth contributors",
        "license": "Public domain",
        "license_url": "https://www.naturalearthdata.com/about/terms-of-use/",
    },
    "natural_earth_marine": {
        "title": "Natural Earth 1:10m Geography Marine Polygons",
        "snapshot_date": "2026-10-28",
        "file": "ne_10m_geography_marine_polys.geojson",
        "url": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_geography_marine_polys.geojson",
        "rights": "Natural Earth public domain",
        "author": "Natural Earth contributors",
        "license": "Public domain",
        "license_url": "https://www.naturalearthdata.com/about/terms-of-use/",
    },
    "natural_earth_land": {
        "title": "Natural Earth 1:10m Land Polygons",
        "snapshot_date": "2026-10-29",
        "file": "ne_10m_land.geojson",
        "url": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson",
        "rights": "Natural Earth public domain",
        "author": "Natural Earth contributors",
        "license": "Public domain",
        "license_url": "https://www.naturalearthdata.com/about/terms-of-use/",
    },
    "census_nyc_counties": {
        "title": "U.S. Census Bureau 2024 Cartographic Boundary Counties, 1:500,000",
        "snapshot_date": "2026-10-29",
        "file": "cb_2024_us_county_500k.zip",
        "url": "https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_county_500k.zip",
        "rights": "U.S. Census Bureau TIGERweb; U.S. Government work, public domain",
        "author": "U.S. Census Bureau",
        "license": "Public domain (U.S. Government work)",
        "license_url": "https://www2.census.gov/geo/pdfs/maps-data/data/tiger/tgrshp2022/TGRSHP2022_TechDoc_Ch1.pdf",
    },
}

RECORDS = [
    ("Lake Tahoe surface", "natural_earth_lakes", {"name": "Lake Tahoe"}, "Water surface area", 496_000_000, 0, False, -120.0, "Natural Earth generalized lake outline; source-water extent and listed surface-area statistic may differ.", "Lake Tahoe"),
    ("New York City", "census_nyc_counties", {"COUNTYFP": ["005", "047", "061", "081", "085"]}, "Land area", 784_000_000, 0.0002, True, -73.94, "Union of five 1:500,000 Census county outlines clipped to Natural Earth 1:10m land and simplified at 0.0002 degrees. This mixed-scale coastline is generalized: its spherical cylindrical equal-area estimate (R=6378137 m) is 736.005 km2 versus 778.181 km2 in Census county land attributes. The listed 784 km2 is a rounded land-area statistic; neither outline nor calibration represents cadastral shorelines.", "Bronx, Kings, New York, Queens, Richmond Counties"),
    ("Caspian Sea surface", "natural_earth_marine", {"name": "Caspian Sea"}, "Water surface area", 371_000_000_000, 0, False, 51.0, "Natural Earth generalized marine polygon; shoreline and water-level epoch may differ from the listed statistic.", "Caspian Sea"),
    ("Texas", "natural_earth_admin1", {"iso_3166_2": "US-TX"}, "Total area", 696_200_000_000, 0, False, -99.0, "Natural Earth generalized state outline; the listed value approximates total area, not land-only area.", "Texas"),
    ("Greenland", "natural_earth_countries", {"ADMIN": "Greenland"}, "Land area", 2_166_000_000_000, 0, False, -42.0, "Natural Earth generalized dependency outline; coast/island detail follows its 1:10m cartographic convention.", "Greenland"),
    ("Australia", "natural_earth_countries", {"ADMIN": "Australia"}, "Land area", 7_690_000_000_000, 0, False, 134.0, "Natural Earth generalized country outline, including its mapped islands and external features.", "Australia"),
]


def vertex_count(coordinates):
    if coordinates and isinstance(coordinates[0], (int, float)):
        return 1
    return sum(vertex_count(value) for value in coordinates)


def acquire(work_dir):
    work_dir.mkdir(parents=True, exist_ok=True)
    source_metadata = {}
    for key, info in SOURCES.items():
        path = work_dir / info["file"]
        if not path.exists():
            request = urllib.request.Request(info["url"], headers={"User-Agent": "universe-scales-area-gis/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response, path.open("wb") as target:
                target.write(response.read())
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != PINNED_SOURCE_SHA256[key]:
            raise ValueError(f"{key}: source hash {digest} differs from pinned snapshot {PINNED_SOURCE_SHA256[key]}")
        source_metadata[key] = {
            "file": info["file"], "url": info["url"], "title": info["title"],
            "author": info["author"], "license": info["license"],
            "license_url": info["license_url"], "rights": info["rights"],
            "sha256": digest,
            "retrieved": info["snapshot_date"],
        }
    return source_metadata


def read_geojson(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("type") != "FeatureCollection":
        raise ValueError(f"{path}: expected GeoJSON FeatureCollection")
    return data["features"]


def read_source_features(path, source_key):
    if source_key != "census_nyc_counties":
        return read_geojson(path)
    try:
        import shapefile
    except ImportError as exc:
        raise RuntimeError("pyshp is required to read Census cartographic boundary ZIPs") from exc
    reader = shapefile.Reader(str(path))
    fields = [field[0] for field in reader.fields[1:]]
    features = []
    for row in reader.iterShapeRecords():
        properties = dict(zip(fields, row.record))
        if properties.get("STATEFP") == "36" and properties.get("COUNTYFP") in {"005", "047", "061", "081", "085"}:
            features.append({
                "type": "Feature",
                "properties": properties,
                "geometry": row.shape.__geo_interface__,
            })
    return features


def prepare(output_dir, work_dir):
    try:
        import shapely
        from shapely.geometry import mapping, shape
        from shapely.ops import unary_union
    except ImportError as exc:
        raise RuntimeError("Shapely is required (tested with Shapely 2.x)") from exc

    sources = acquire(work_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    previous_manifest_path = output_dir / "manifest.json"
    active_ids = {name.lower().replace(" ", "-") for name, *_ in RECORDS}
    if previous_manifest_path.exists():
        previous_manifest = json.loads(previous_manifest_path.read_text(encoding="utf-8"))
        for item in previous_manifest.get("items", []):
            if item.get("id") not in active_ids and item.get("geojson"):
                stale_path = output_dir / Path(item["geojson"]).name
                if stale_path.parent.resolve() == output_dir.resolve():
                    stale_path.unlink(missing_ok=True)
    for retired_name in ("manhattan.geojson", "rhode-island.geojson"):
        (output_dir / retired_name).unlink(missing_ok=True)
    entries = []
    manifest = {
        "retrieved": date.today().isoformat(), "geometry_engine": f"Shapely {shapely.__version__}",
        "source_snapshots": sources, "items": [],
    }
    total_bytes = 0
    for (name, source_key, required, area_definition, listed_area, tolerance,
         dissolve, central_longitude, note, source_feature_label) in RECORDS:
        source_path = work_dir / SOURCES[source_key]["file"]
        selected = []
        for feature in read_source_features(source_path, source_key):
            props = feature.get("properties", {})
            if all(
                (str(props.get(key, "")).casefold() in {str(item).casefold() for item in value}
                 if isinstance(value, list) else str(props.get(key, "")).casefold() == str(value).casefold())
                for key, value in required.items()
            ):
                selected.append(feature)
        if not selected:
            raise ValueError(f"{name}: no source feature matched {required}")
        geometries = [shape(feature["geometry"]) for feature in selected]
        if any(not geometry.is_valid for geometry in geometries):
            raise ValueError(f"{name}: invalid source geometry")
        geometry = unary_union(geometries) if dissolve else geometries[0]
        clipped_to_land = source_key == "census_nyc_counties"
        if clipped_to_land:
            from shapely.geometry import box

            xmin, ymin, xmax, ymax = geometry.bounds
            county_bounds = box(xmin - 0.02, ymin - 0.02, xmax + 0.02, ymax + 0.02)
            land_features = read_geojson(work_dir / SOURCES["natural_earth_land"]["file"])
            land_geometries = [
                shape(feature["geometry"])
                for feature in land_features
                if shape(feature["geometry"]).intersects(county_bounds)
            ]
            geometry = geometry.intersection(unary_union(land_geometries))
        if tolerance:
            geometry = geometry.simplify(tolerance, preserve_topology=True)
        if not geometry.is_valid:
            raise ValueError(f"{name}: output geometry is invalid")
        coordinates = mapping(geometry)["coordinates"]
        vertices = vertex_count(coordinates)
        if vertices > MAX_VERTICES:
            raise ValueError(f"{name}: {vertices} vertices exceeds {MAX_VERTICES}")
        filename = name.lower().replace(" ", "-") + ".geojson"
        payload = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": mapping(geometry)}]}
        target = output_dir / filename
        target.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
        size = target.stat().st_size
        total_bytes += size
        source_ids = [feature.get("properties", {}) for feature in selected]
        source = sources[source_key]
        map_entry = {
            "id": name.lower().replace(" ", "-"),
            "name": name,
            "geojson": f"content/visualizations/area-sources/{filename}",
            "central_longitude": central_longitude,
            "source": source["url"],
            "author": source["author"],
            "license": source["license"],
            "license_url": source["license_url"],
            "note": note,
        }
        record = {
            "listed_area_m2": listed_area,
            "quantity_definition": area_definition,
            "source_sha256": source["sha256"],
            "source_feature": source_feature_label,
            "source_feature_count": len(selected),
            "selected_source_properties": source_ids,
            "clip_source": "Natural Earth 1:10m Land Polygons" if clipped_to_land else None,
            "simplification_tolerance_degrees": tolerance or None,
            "output_vertices": vertices,
            "output_bytes": size,
            "output_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "calibration": "uniform scale to listed quantity; preserve source aspect ratio",
            **map_entry,
        }
        manifest["items"].append(record)
        entries.append(map_entry)
    if total_bytes > MAX_TOTAL_BYTES:
        raise ValueError(f"geometry bundle is {total_bytes} bytes; limit is {MAX_TOTAL_BYTES}")
    manifest["total_geometry_bytes"] = total_bytes
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("content/visualizations/area-sources"))
    parser.add_argument("--work-dir", type=Path, default=Path("/private/tmp/area-gis/raw"))
    args = parser.parse_args()
    entries = prepare(args.output, args.work_dir)
    entry_file = Path("handoff/area-gis/entries.json")
    entry_file.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(entries)} Area outlines in {args.output}")


if __name__ == "__main__":
    main()
