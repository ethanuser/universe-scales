#!/usr/bin/env python3
"""Kilimanjaro summit window, in equal horizontal and vertical metres.

Offline normal build. --prepare obtains and records the source terrain tiles.
The bottom is a sea-level display datum, not the mountain's geological base.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import build_meteor_crater as terrain
from build_earth3d2_structures import HANDOFF, ROOT
from build_everyday_models import mesh
from fetch_model_assets import inspect_glb
from geo_glb_common import GLB, grid_indices, grid_normals

SOURCE = ROOT/'content/visualizations/models/sources/earth3d2-kilimanjaro'
LAT, LON, SPAN, COUNT, ZOOM = -3.0674, 37.3556, 6400, 129, 12


def prepare(tile_dir):
    terrain.LAT, terrain.LON, terrain.SPAN, terrain.COUNT, terrain.ZOOM = LAT, LON, SPAN, COUNT, ZOOM
    terrain.prepare(tile_dir, SOURCE)


def build():
    meta = json.loads((SOURCE/'provenance.json').read_text())
    if hashlib.sha256((SOURCE/'terrain.npz').read_bytes()).hexdigest() != meta['grid_sha256']:
        raise ValueError('Source terrain hash differs from provenance')
    data = np.load(SOURCE/'terrain.npz')
    h, xs, zs = data['heights'].astype(float), data['x'], data['z']
    x, z = np.meshgrid(xs, zs)
    p = np.stack((x, h, z), axis=-1)
    glb = GLB('Universe Scales: Kilimanjaro summit DEM window, sea-level datum, relief 1x')
    top = glb.material('Authored volcanic elevation palette', rough=.98, double_sided=False)
    wall = glb.material('Display cut, not geological strata', (.24, .18, .13, 1), rough=1, double_sided=False)
    # Elevation colors are not a map of rocks, snow or contemporary ice cover.
    t = np.clip((h-3900)/2000, 0, 1)[..., None]
    colors = np.array([.32, .24, .16])*(1-t)+np.array([.66, .58, .46])*t
    glb.mesh_node('Measured Kibo summit terrain, equal metric axes', [glb.primitive(
        p.reshape(-1, 3), grid_indices(*h.shape), top, normals=grid_normals(h, 50, 50),
        colors=colors.reshape(-1, 3), rgba8=True)])
    perimeter = np.concatenate((p[0, :], p[1:, -1], p[-1, -2::-1], p[-2:0:-1, 0]))
    points, faces = [], []
    for a, b in zip(perimeter, np.roll(perimeter, -1, axis=0)):
        k = len(points)
        points.extend([a, [a[0], 0, a[2]], [b[0], 0, b[2]], b])
        faces.extend([(k, k+2, k+1), (k, k+3, k+2)])
    mesh(glb, 'Summit window sides extended to sea-level display datum', points, faces, wall)
    mesh(glb, 'Sea-level display base', [[xs[0], 0, zs[0]], [xs[-1], 0, zs[0]],
         [xs[-1], 0, zs[-1]], [xs[0], 0, zs[-1]]], [(0, 1, 2), (0, 2, 3)], wall)
    glb.label_node('Scope qualifier', [0, float(h.max())+400, 0], 'KIBO SUMMIT WINDOW · massif continues beyond cut')
    glb.label_node('Datum qualifier', [0, -250, 0], 'SEA-LEVEL DATUM · not the mountain’s base')
    model_id = 'earth3d2-kilimanjaro'
    path = ROOT/f'content/visualizations/models/{model_id}.glb'; glb.write(path)
    entry = dict(id=model_id, source='https://registry.opendata.aws/terrain-tiles/',
                 basis_url='https://www.tanzaniaparks.go.tz/kilimanjaro/about', basis_label='TANAPA: Kibo summit altitude',
                 author='Mapzen / Tilezen; global SRTM and GMTED2010 terrain data courtesy of the U.S. Geological Survey; adaptation by Universe Scales',
                 license='Mapzen Terrain Tiles attribution; underlying USGS public-domain terrain data',
                 license_url='https://github.com/tilezen/joerd/blob/master/docs/attribution.md',
                 license_files=['sources/earth3d2-kilimanjaro.md'], matches={'length': ['Mount Kilimanjaro']},
                 geometry='mesh', representation='dem_terrain', volume_semantics='not_applicable', closed_volume_checked=False,
                 display_label='Kilimanjaro · summit window above sea level',
                 presentation=dict(reference_size=5895, yaw=-8, pitch=14, layout_width_factor=1.25),
                 note=('Actual Kibo summit terrain, sampled from Mapzen Terrarium tiles on a 50 m grid, with no vertical exaggeration or summit correction. '
                       'The authored 6.4 km square is a crop around the summit crater, not the full Kilimanjaro massif. '
                       'The sides extend straight down to a sea-level display datum; they are arbitrary cuts, not cliffs, measured rock walls or the mountain’s base. '
                       'Calibration uses TANAPA’s 5,895 m above-sea-level reference; the sampled grid maximum is about 5,886 m and is deliberately not forced to that reference. '
                       'Elevation colors are illustrative, not observed geology, current snow or glacier boundaries. '
                       'Mapzen / Tilezen; global SRTM and GMTED2010 terrain data courtesy of the U.S. Geological Survey.'),
                 processing=dict(script='scripts/build_earth3d2_terrain.py', units='metres', vertical_gain=1,
                                 source_note='content/visualizations/models/sources/earth3d2-kilimanjaro.md',
                                 source_grid_sha256=meta['grid_sha256'],
                                 provenance='content/visualizations/models/sources/earth3d2-kilimanjaro/provenance.json'),
                 src=str(path.relative_to(ROOT)), **inspect_glb(path.read_bytes()))
    HANDOFF.mkdir(parents=True, exist_ok=True)
    (HANDOFF/f'{model_id}.entry.json').write_text(json.dumps(entry, indent=2)+'\n')
    print(model_id, entry['bytes'], entry['triangle_count'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--tile-dir', type=Path, default=Path('/tmp/earth3d2/terrain-tiles'))
    args = parser.parse_args()
    if args.prepare:
        prepare(args.tile_dir)
    build()
