#!/usr/bin/env python3
"""Unexaggerated Meteor Crater terrain, with a bundled offline height grid.

Optional --prepare downloads Mapzen Terrarium tiles into --tile-dir and writes
the small derived grid and provenance. Normal builds never access the network.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from PIL import Image

from build_everyday_models import mesh
from fetch_model_assets import inspect_glb
from geo_glb_common import GLB, grid_indices, grid_normals

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'content/visualizations/models/sources/earth3d-meteor-crater'
# Authored crop center and display aperture; not a newly measured crater boundary.
LAT, LON, SPAN, COUNT, ZOOM = 35.0273, -111.0225, 1440, 121, 14


def prepare(tile_dir, source):
    tile_dir.mkdir(parents=True, exist_ok=True)
    source.mkdir(parents=True, exist_ok=True)
    p = np.linspace(-SPAN/2, SPAN/2, COUNT)
    x, z = np.meshgrid(p, p)
    latitude = LAT-np.degrees(z/6378137)
    longitude = LON+np.degrees(x/(6378137*math.cos(math.radians(LAT))))
    px = (longitude+180)/360 * (2**ZOOM)*256-.5
    py = (1-np.arcsinh(np.tan(np.radians(latitude)))/np.pi)/2 * (2**ZOOM)*256-.5
    x0, y0 = math.floor(px.min()/256), math.floor(py.min()/256)
    x1, y1 = math.floor((px.max()+1)/256), math.floor((py.max()+1)/256)
    mosaic = np.empty(((y1-y0+1)*256, (x1-x0+1)*256))
    records = []
    for ty in range(y0, y1+1):
        for tx in range(x0, x1+1):
            url = f'https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{ZOOM}/{tx}/{ty}.png'
            path = tile_dir/f'{ZOOM}-{tx}-{ty}.png'
            headers = {}
            if not path.exists():
                with urlopen(url, timeout=60) as response:
                    data = response.read()
                    headers = {k: v for k, v in response.headers.items() if k.lower() == 'x-imagery-sources'}
                path.write_bytes(data)
            data = path.read_bytes()
            tile = np.asarray(Image.open(io.BytesIO(data)).convert('RGB')).astype(float)
            heights = tile[:, :, 0]*256+tile[:, :, 1]+tile[:, :, 2]/256-32768
            mosaic[(ty-y0)*256:(ty-y0+1)*256, (tx-x0)*256:(tx-x0+1)*256] = heights
            records.append(dict(url=url, sha256=hashlib.sha256(data).hexdigest(), headers=headers))
    px, py = px-x0*256, py-y0*256
    ix, iy = np.floor(px).astype(int), np.floor(py).astype(int)
    fx, fy = px-ix, py-iy
    heights = (mosaic[iy, ix]*(1-fx)*(1-fy)+mosaic[iy, ix+1]*fx*(1-fy)
               +mosaic[iy+1, ix]*(1-fx)*fy+mosaic[iy+1, ix+1]*fx*fy)
    np.savez_compressed(source/'terrain.npz', heights=heights.astype('<f4'), x=p.astype('<f4'), z=p.astype('<f4'))
    record = dict(center_lat=LAT, center_lon=LON, aperture_m=SPAN, grid=COUNT, sample_spacing_m=SPAN/(COUNT-1),
                  vertical_gain=1, source_zoom=ZOOM, tiles=records,
                  min_elevation_m=float(heights.min()), max_elevation_m=float(heights.max()),
                  processing='Bilinear resampling to a local east/south metric grid; no summit/depth correction, smoothing, or vertical exaggeration.',
                  grid_sha256=hashlib.sha256((source/'terrain.npz').read_bytes()).hexdigest(),
                  attribution='Mapzen Terrain Tiles / Tilezen; United States 3DEP (formerly NED) and global GMTED2010 and SRTM terrain data courtesy of the U.S. Geological Survey.')
    (source/'provenance.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2))


def build(source):
    meta = json.loads((source/'provenance.json').read_text())
    data = np.load(source/'terrain.npz')
    h, xs, zs = data['heights'].astype(float), data['x'], data['z']
    x, z = np.meshgrid(xs, zs)
    # The flat bottom is a display cut 30 m below the lowest terrain sample.
    datum = h.min()-30
    y = h-datum
    glb = GLB('Universe Scales: USGS/Mapzen Meteor Crater, relief 1x')
    top = glb.material('Authored sandstone elevation palette', rough=.97, double_sided=False)
    wall = glb.material('Display block cut, not stratigraphy', (.38, .26, .15, 1), rough=1, double_sided=False)
    t = np.clip((h-h.min())/max(np.ptp(h), 1e-6), 0, 1)
    colors = np.array([.50, .35, .22])*(1-t[..., None])+np.array([.82, .70, .49])*t[..., None]
    normals = grid_normals(h, float(xs[1]-xs[0]), float(zs[1]-zs[0]))
    positions = np.stack((x, y, z), axis=-1).reshape(-1, 3)
    glb.mesh_node('Measured terrain with true relief', [glb.primitive(positions, grid_indices(*h.shape), top,
                                                                   normals=normals, colors=colors.reshape(-1, 3), rgba8=True)])
    perimeter = np.concatenate((positions.reshape(*h.shape, 3)[0, :], positions.reshape(*h.shape, 3)[1:, -1],
                                positions.reshape(*h.shape, 3)[-1, -2::-1], positions.reshape(*h.shape, 3)[-2:0:-1, 0]))
    vertices, faces = [], []
    for a, b in zip(perimeter, np.roll(perimeter, -1, axis=0)):
        k = len(vertices)
        vertices.extend([a, [a[0], 0, a[2]], [b[0], 0, b[2]], b])
        faces.extend([(k, k+2, k+1), (k, k+3, k+2)])
    mesh(glb, 'Opaque cropped terrain walls', vertices, faces, wall)
    mesh(glb, 'Flat display base', [[xs[0], 0, zs[0]], [xs[-1], 0, zs[0]], [xs[-1], 0, zs[-1]], [xs[0], 0, zs[-1]]],
         [(0, 1, 2), (0, 2, 3)], wall)
    model_id = 'earth3d-meteor-crater'
    path = ROOT/f'content/visualizations/models/{model_id}.glb'; glb.write(path)
    entry = dict(id=model_id, source='https://registry.opendata.aws/terrain-tiles/',
                 basis_url='https://pubs.usgs.gov/publication/ofr20241062/full', basis_label='USGS: Meteor Crater dimensions and geology',
                 author='Mapzen Terrain Tiles / Tilezen; terrain data courtesy of the U.S. Geological Survey; adaptation by Universe Scales',
                 license='Mapzen Terrain Tiles attribution; underlying USGS public-domain terrain data',
                 license_url='https://github.com/tilezen/joerd/blob/master/docs/attribution.md',
                 license_files=['sources/earth3d-meteor-crater.md'],
                 matches={'length': ['Meteor Crater']}, geometry='mesh', representation='dem_terrain',
                 volume_semantics='not_applicable', closed_volume_checked=False,
                 presentation={'reference_size': 1186, 'yaw': 0, 'pitch': 48, 'layout_width_factor': 1.25, 'focus_scale_factor': 1.2},
                 note='Meteor Crater in real terrain, sampled from Mapzen Terrarium elevation tiles on a 12 m grid. Horizontal and vertical metres use the same scale: no exaggerated relief, synthetic bowl or depth correction. The 1.44 km square includes context around the catalog’s approximately 1.19 km crater diameter; the square is not the crater rim. Sandstone colors are an authored elevation palette, not satellite imagery or mapped geological strata. The flat underside is an arbitrary display cut, not a subsurface boundary. Mapzen / Tilezen; United States 3DEP (formerly NED) and global GMTED2010 and SRTM terrain data courtesy of the U.S. Geological Survey.',
                 processing={'script': 'scripts/build_meteor_crater.py', 'units': 'metres', 'vertical_gain': 1,
                             'source_grid_sha256': meta['grid_sha256'], 'provenance': 'content/visualizations/models/sources/earth3d-meteor-crater/provenance.json'},
                 src=str(path.relative_to(ROOT)), **inspect_glb(path.read_bytes()))
    handoff = ROOT/'handoff/earth3d'; handoff.mkdir(parents=True, exist_ok=True)
    (handoff/f'{model_id}.entry.json').write_text(json.dumps(entry, indent=2)+'\n')
    print(f"Built {entry['bytes']:,} bytes; source relief {np.ptp(h):.2f} m; displayed width {SPAN/1186:.3f}x")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--tile-dir', type=Path, default=Path('/tmp/earth3d-meteor-tiles'))
    args = parser.parse_args()
    if args.prepare:
        prepare(args.tile_dir, args.source)
    build(args.source)
