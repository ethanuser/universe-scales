#!/usr/bin/env python3
"""Build two unexaggerated ETOPO 2022 terrain candidates, offline by default.

These are deliberately UNREGISTERED: their horizontal footprints exceed the
catalog's vertical quantities. See handoff/retry3d/REPORT.md before integration.
No walls, undersides, water planes, measurement geometry or missing data added.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image

from fetch_model_assets import inspect_glb
from geo_glb_common import GLB, grid_indices

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / 'content/visualizations/models'
SOURCES = MODELS / 'sources/retry3d'
HANDOFF = ROOT / 'handoff/retry3d'
BASE = 'https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/15s/15s_surface_elev_gtif/'
PRODUCT = 'https://www.ncei.noaa.gov/products/etopo-global-relief-model'
RIGHTS = 'https://www.ngdc.noaa.gov/metadata/published/NOAA/NESDIS/NGDC/MGG/DEM/iso/xml/etopo_2022.xml'
CONFIG = {
    'mauna-kea': dict(item='Mauna Kea', value=10211., tile='N30W165',
        bounds=(-156.15, 19.55, -154.60, 20.95), stride=3, water_level=0.,
        center=(-155.375, 20.25), pitch=52., yaw=-12., focus=20.,
        quantity_source='https://www.usgs.gov/faqs/how-big-are-hawaiian-volcanoes',
        note='Direct NOAA ETOPO 2022 topography/bathymetry of a northeastern Hawaii aperture, including Mauna Kea, Kohala and the offshore flank. Original elevations and horizontal geographic scale are retained, with no vertical exaggeration, invented base, walls, underside or water surface. Colors encode elevation, not a satellite photograph. This is a regional terrain surface, not an isolated geological boundary for Mauna Kea; the southern crop excludes Mauna Loa\'s summit. The catalog measures approximate summit-to-ocean-floor height, not this much wider aperture. ETOPO cell averaging smooths the summit and does not reproduce the exact USGS summit height or establish a unique mountain base. Integration requires the documented vertical-axis presentation exception.'),
    'baikal-depth': dict(item='Lake Baikal Depth', value=1642., tile='N60E105',
        bounds=(107.10, 52.95, 107.65, 53.20), stride=1, water_level=456.,
        center=(107.375, 53.075), pitch=52., yaw=-18., focus=28.,
        quantity_source='https://www.gebco.net/data-products/gridded-bathymetry-data',
        note='Direct NOAA ETOPO 2022 lake-bed elevations near the deep central Baikal basin southeast of Olkhon. This public NOAA release incorporates GEBCO lake bathymetry, avoiding an unverified license assumption about the separate GFZ contour archive. Elevations are translated by a nominal 456 m lake-surface datum; native cell centers and heights are otherwise retained. Only original adjacent cells whose vertices lie at or below that datum are triangulated. Land, water planes, walls, undersides and an invented lake volume are absent. Colors encode depth, not natural underwater color. The regional grid is an approximate bathymetric product, not a fresh survey or a claim to reproduce exactly the catalog\'s 1,642 m maximum. The aperture is much wider than the measured depth; integration requires the documented vertical-axis presentation exception.'),
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def prepare(name, cache):
    c = CONFIG[name]
    filename = f'ETOPO_2022_v1_15s_{c["tile"]}_surface.tif'
    path = cache / filename
    if not path.exists():
        subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                        '--max-time', '180', BASE + filename, '--output', str(path)], check=True)
    with Image.open(path) as im:
        step_x, step_y, _ = im.tag_v2[33550]
        _, _, _, west, north, _ = im.tag_v2[33922]
        a = np.asarray(im).copy()
    if a.shape != (3600, 3600) or not np.isfinite(a).all():
        raise ValueError('Unexpected ETOPO source grid')
    w, s, e, n = c['bounds']
    xs = west + (np.arange(a.shape[1]) + .5) * step_x
    ys = north - (np.arange(a.shape[0]) + .5) * step_y
    ix = np.flatnonzero((xs >= w) & (xs <= e))[::c['stride']]
    iy = np.flatnonzero((ys >= s) & (ys <= n))[::c['stride']]
    heights = a[np.ix_(iy, ix)].astype('<f4')
    folder = SOURCES / name
    folder.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(folder / 'grid.npz', longitude=xs[ix].astype('<f8'),
                        latitude=ys[iy].astype('<f8'), elevation_m=heights,
                        source_row=iy.astype('<i4'), source_column=ix.astype('<i4'))
    write_json(folder / 'provenance.json', dict(
        source=BASE + filename, product=PRODUCT, acquired='2026-10-23',
        original_sha256=digest(path), original_bytes=path.stat().st_size,
        grid_sha256=digest(folder / 'grid.npz'),
        native_pixel_scale_degrees=[step_x, step_y], pixel_registration='cell centers',
        tile_northwest_corner=[west, north], bounds_requested=c['bounds'],
        stride=c['stride'], shape=list(heights.shape),
        elevation_range_m=[float(heights.min()), float(heights.max())],
        processing='Select original pixel centers at a fixed stride; no resampling, interpolation, smoothing or height corrections. The complete original tile is optional external preparation cache, not a runtime dependency.'))


def normals(points, triangles):
    n = np.zeros_like(points)
    cross = np.cross(points[triangles[:, 1]] - points[triangles[:, 0]],
                     points[triangles[:, 2]] - points[triangles[:, 0]])
    for i in range(3):
        np.add.at(n, triangles[:, i], cross)
    lengths = np.linalg.norm(n, axis=1)
    if (lengths == 0).any():
        raise ValueError('Degenerate or unused source vertex')
    return n / lengths[:, None]


def build(name):
    c = CONFIG[name]
    folder = SOURCES / name
    meta = json.loads((folder / 'provenance.json').read_text())
    if digest(folder / 'grid.npz') != meta['grid_sha256']:
        raise ValueError('Pinned source subset changed')
    with np.load(folder / 'grid.npz') as d:
        lon, lat = np.meshgrid(d['longitude'], d['latitude'])
        height = d['elevation_m'].astype(float) - c['water_level']
    # Local equidistant cylindrical map projection; axes are metres. The stated
    # central-parallel approximation is never adjusted to the catalog quantity.
    lon0, lat0 = c['center']
    points = np.stack((np.radians(lon - lon0) * 6378137 * math.cos(math.radians(lat0)),
                       height, -np.radians(lat - lat0) * 6378137), axis=-1).reshape(-1, 3)
    triangles = grid_indices(*height.shape).reshape(-1, 3)
    if name == 'baikal-depth':
        triangles = triangles[(height.ravel()[triangles] <= 0).all(axis=1)]
    # Compact the retained original sample indices; never add boundary vertices.
    used, inverse = np.unique(triangles.ravel(), return_inverse=True)
    points = points[used]
    triangles = inverse.reshape(-1, 3)
    # grid_indices connects south then east: with south-positive Z its winding
    # already gives the upper terrain surface positive-Y face normals.
    h = points[:, 1]
    if name == 'mauna-kea':
        stops = [-6500, -4500, -1000, 0, 1, 1000, 2500, 4300]
        colors = [[10,25,55], [20,65,100], [35,115,140], [85,180,195],
                  [95,150,100], [105,100,70], [170,150,120], [235,225,210]]
    else:
        stops = [-1700, -1200, -600, -100, 0]
        colors = [[14,38,78], [21,77,126], [35,126,163], [91,183,197], [166,219,217]]
    colors = np.stack([np.interp(h, stops, np.asarray(colors)[:, i]) for i in range(3)], axis=-1) / 255
    glb = GLB('Universe Scales direct ETOPO 2022 sample conversion')
    material = glb.material('Elevation colors; unexaggerated source surface', double_sided=True)
    glb.mesh_node(name, [glb.primitive(points, triangles.ravel(), material,
                                     normals=normals(points, triangles), colors=colors, rgba8=True)])
    model_id = 'retry3d-' + name
    path = MODELS / (model_id + '.glb')
    glb.write(path)
    stats = inspect_glb(path.read_bytes())
    if stats['bytes'] > 3_000_000 or stats['triangle_count'] > 60_000:
        raise ValueError('Asset budget exceeded')
    entry = dict(id=model_id, src=str(path.relative_to(ROOT)), matches={'length': [c['item']]},
        source=PRODUCT, download_url=meta['source'],
        source_sha256=meta['original_sha256'], source_bytes=meta['original_bytes'],
        author='NOAA National Centers for Environmental Information; ETOPO 2022 compilation contributors, including GEBCO.',
        license='CC0-1.0',
        license_url=RIGHTS, license_files=['licenses/CC0-1.0.txt', 'sources/retry3d/etopo-rights.md'],
        reference=f'content/visualizations/models/sources/{model_id}.md',
        geometry='mesh', representation='data-derived',
        volume_semantics='not_a_volume_measurement', closed_volume_checked=False,
        note=c['note'], presentation=dict(reference_size=c['value'], measure_axis='y',
            pitch=c['pitch'], yaw=c['yaw'], layout_width_factor=c['focus'],
            focus_scale_factor=c['focus'], display_extent_factor=c['focus'], roughness=1, metalness=0),
        processing=dict(builder='scripts/build_retry3d_models.py',
            pinned_input=str((folder / 'grid.npz').relative_to(ROOT)), pinned_input_sha256=meta['grid_sha256'],
            vertical_exaggeration=1, horizontal_projection='Local equidistant cylindrical, WGS84 semi-major radius 6378137 m, fixed central latitude',
            center_lonlat=c['center'], nominal_water_level_m=c['water_level'],
            pending='UNREGISTERED. Vertical quantity versus horizontal footprint requires lead review; do not normalize the bounding box to the item value.'), **stats)
    write_json(HANDOFF / (model_id + '.entry.json'), entry)
    print(f'Prepared UNREGISTERED {model_id}: {stats["bytes"]:,} bytes, {stats["triangle_count"]:,} triangles')
    return entry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--cache', type=Path, default=Path('/tmp/retry3d-source-cache'))
    args = parser.parse_args()
    for name in CONFIG:
        if args.prepare:
            args.cache.mkdir(parents=True, exist_ok=True)
            prepare(name, args.cache)
        build(name)


if __name__ == '__main__':
    main()
