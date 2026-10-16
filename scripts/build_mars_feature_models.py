#!/usr/bin/env python3
"""True-relief MOLA terrain windows, with retained offline source samples.

The MOLA PDS label defines 16 samples/degree, signed big-endian int16 meters
above the areoid. Pixel centers, not pixel corners, define sample coordinates.
The spherical local frame uses the label's 3396 km map reference radius; this is
an approximate areoid surface, not a reconstruction of the Mars gravity field.
"""
import argparse
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

from build_space3d_models import restore_normals
from fetch_model_assets import sha, write_json
from geo_glb_common import GLB, grid_indices

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT/'content/visualizations/models/sources/mola'
RADIUS_M = 3_396_000
RESOLUTION = 16
CONFIGS = [
    {'id': 'mola-olympus-mons', 'item': 'Olympus Mons Width',
     'bounds': [219.8, 12.5, 232.6, 24.5], 'stride': 2, 'reference_m': 585_000,
     'basis': 'https://planetarynames.wr.usgs.gov/SearchResults?Feature+Type=27_Mons&Target=20_Mars'},
    {'id': 'mola-valles-marineris', 'item': 'Valles Marineris',
     'bounds': [252, -20, 322, 2], 'stride': 4, 'reference_m': 4_000_000,
     'basis': 'https://www.usgs.gov/centers/astrogeology-science-center/science/valles-marineris-grand-canyon-mars'},
]
SOURCE_URL = 'https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg016/megt90n000eb.img'


def prepare(directory):
    raw = (directory/'mola.img').read_bytes()
    heights = np.frombuffer(raw, dtype='>i2').reshape(2880, 5760)
    SOURCES.mkdir(parents=True, exist_ok=True)
    for config in CONFIGS:
        west, south, east, north = config['bounds']
        rows = np.arange(math.ceil((90-north)*RESOLUTION-.5), math.floor((90-south)*RESOLUTION-.5)+1, config['stride'])
        cols = np.arange(math.ceil(west*RESOLUTION-.5), math.floor(east*RESOLUTION-.5)+1, config['stride'])
        np.savez_compressed(SOURCES/(config['id']+'.npz'), rows=rows, cols=cols,
                            heights=heights[np.ix_(rows, cols)].astype('<i2'))
    (SOURCES/'megt90n000eb.lbl').write_bytes((directory/'mola-label').read_bytes())
    write_json(SOURCES/'provenance.json', {'source_url': SOURCE_URL, 'source_sha256': sha(raw),
              'source_bytes': len(raw), 'label_sha256': sha((directory/'mola-label').read_bytes()),
              'operations': 'Retain exact original int16 samples and their global row/column indices; no interpolation, smoothing, height correction or exaggeration',
              'windows': CONFIGS})


def geographic_frame(lon, lat, heights, center):
    lon, lat = np.radians(lon), np.radians(lat)
    lon0, lat0 = np.radians(center)
    dlon = lon-lon0
    radius = RADIUS_M + heights
    east = radius*np.cos(lat)*np.sin(dlon)
    up = radius*(np.sin(lat)*math.sin(lat0) + np.cos(lat)*math.cos(lat0)*np.cos(dlon)) - RADIUS_M
    south = -radius*(np.sin(lat)*math.cos(lat0) - np.cos(lat)*math.sin(lat0)*np.cos(dlon))
    return np.stack((east, up, south), axis=-1)


def build(config):
    path = SOURCES/(config['id']+'.npz')
    data = np.load(path)
    lon = (data['cols']+.5)/RESOLUTION
    lat = 90-(data['rows']+.5)/RESOLUTION
    lon_grid, lat_grid = np.meshgrid(lon, lat)
    heights = data['heights'].astype(float)
    center = [float(lon.mean()), float(lat.mean())]
    positions = geographic_frame(lon_grid, lat_grid, heights, center)
    # A documented hypsometric palette: color is elevation, not a photograph.
    stops = np.array([-8000, -4000, 0, 4000, 12000, 22000])
    palette = np.array([[.06,.11,.22], [.12,.27,.36], [.49,.32,.21], [.68,.47,.29], [.84,.66,.41], [.99,.91,.72]])
    rgb = np.stack([np.interp(heights, stops, palette[:, i]) for i in range(3)], axis=-1)
    image = Image.fromarray(np.uint8(np.clip(rgb, 0, 1)*255))
    image = image.resize((min(1024, image.width*3), min(1024, image.height*3)), Image.Resampling.BILINEAR)
    output = io.BytesIO(); image.save(output, format='PNG')
    glb = GLB('Universe Scales MOLA true-relief surface window')
    tex = glb.texture(output.getvalue(), 'image/png')
    mat = glb.material('Elevation colors (not imagery)', texture=tex, double_sided=True)
    rows, cols = heights.shape
    u, v = np.meshgrid(np.linspace(0, 1, cols), np.linspace(0, 1, rows))
    glb.mesh_node(config['item']+' MOLA terrain', [glb.primitive(positions.reshape(-1, 3), grid_indices(rows, cols), mat,
                                                             uvs=np.stack((u, v), axis=-1).reshape(-1, 2))])
    glb.label_node('Relief definition', positions[0, cols//2]+[0, 3000, 0], 'MOLA elevations · 1× vertical')
    destination = ROOT/f"content/visualizations/models/{config['id']}.glb"
    glb.write(destination)
    # Keep smooth geometric normals in the emitted mesh.
    destination.write_bytes(restore_normals(destination.read_bytes()))
    from fetch_model_assets import inspect_glb
    from register_model import register
    provenance = json.loads((SOURCES/'provenance.json').read_text())
    entry = {
        'id': config['id'], 'src': str(destination.relative_to(ROOT)), 'author': 'NASA/MGS MOLA Science Team; surface assembled by Universe Scales',
        'source': 'https://pds-geosciences.wustl.edu/missions/mgs/megdr.html', 'download_url': SOURCE_URL,
        'source_sha256': provenance['source_sha256'], 'source_bytes': provenance['source_bytes'],
        'basis_url': config['basis'], 'basis_label': 'Feature definition and location',
        'license': 'U.S. public-domain NASA scientific data; credit MGS MOLA Science Team',
        'license_url': 'https://pds.nasa.gov/datastandards/citing/',
        'license_files': ['licenses/nasa-media-guidelines.html'],
        'matches': {'length': [config['item']]}, 'geometry': 'mesh', 'representation': 'measured-terrain-window',
        'presentation': {'reference_size': config['reference_m'], 'pitch': 58, 'yaw': 0, 'roughness': 1, 'metalness': 0},
        'note': 'A window of actual Mars Global Surveyor MOLA elevations with spherical Mars curvature and 1× vertical relief. Colors encode elevation above the areoid and are not a surface photograph. The rectangular crop is context, not the feature boundary; coordinates are never stretched to the catalog length. The map uses a spherical reference areoid and does not reproduce the full Mars gravity field. '+
                ('The approximate catalog volcano width is smaller than this surrounding terrain window.' if 'Olympus' in config['item'] else 'The catalog value is the approximate canyon-system length, not a traced centerline or the crop width.'),
        'processing': {'source_crop': str(path.relative_to(ROOT)), 'source_crop_sha256': sha(path.read_bytes()),
                       'center_lonlat_degrees': center, 'source_resolution_samples_per_degree': RESOLUTION,
                       'sample_stride': config['stride'], 'reference_radius_m': RADIUS_M, 'vertical_gain': 1,
                       'operations': ['Read exact retained MOLA sample centers and int16 heights', 'Map into a spherical local east/up/south frame', 'Keep true relief; color by elevation', 'Triangulate retained samples; compute geometric normals']},
        'volume_semantics': 'not_applicable', 'closed_volume_checked': False, **inspect_glb(destination.read_bytes()),
    }
    if entry['bytes'] > 3_000_000:
        raise ValueError('Terrain exceeds asset budget')
    ep = ROOT/f"handoff/space3d/{config['id']}.entry.json"
    write_json(ep, entry); register(ep, destination, 'length')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', type=Path, help='Cache containing mola.img and mola-label; otherwise rebuild offline')
    args = parser.parse_args()
    if args.prepare:
        prepare(args.prepare)
    for config in CONFIGS:
        build(config)


if __name__ == '__main__':
    main()
