#!/usr/bin/env python3
"""NASA-map Mars globe and surface-referenced Parker encounter distance.

Uses local cached inputs. The distance is above the photosphere, not from the
Sun's center. No orbit or spacecraft dimensions are inferred from that number.
"""
import argparse
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

from build_earth_moon_model import add_sphere
from fetch_model_assets import inspect_glb, pack_glb, sha, write_json
from geo_glb_common import GLB, grid_indices
from register_model import register

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / 'handoff/space3d'


def sphere(glb, name, radius, material, center=(0, 0, 0), segments=96, rings=48, extras=None):
    theta, phi = np.meshgrid(np.linspace(0, np.pi, rings+1),
                             np.linspace(0, 2*np.pi, segments+1), indexing='ij')
    normals = np.stack((np.sin(theta)*np.cos(phi), np.cos(theta), -np.sin(theta)*np.sin(phi)), axis=-1)
    points = (normals*radius + center).reshape(-1, 3)
    uvs = np.stack((phi/(2*np.pi), theta/np.pi), axis=-1).reshape(-1, 2)
    index = grid_indices(rings+1, segments+1).reshape(-1, 3)
    # Omit degenerate triangles at the poles.
    faces = points[index]
    index = index[np.linalg.norm(np.cross(faces[:, 1]-faces[:, 0], faces[:, 2]-faces[:, 0]), axis=1) > radius**2*1e-12]
    glb.mesh_node(name, [glb.primitive(points, index.ravel(), material, normals=normals.reshape(-1, 3), uvs=uvs)])
    if extras:
        glb.doc['nodes'][-1]['extras'] = extras


def line(glb, name, positions, color):
    material = glb.material(name, color=(*color, 1))
    vertices = np.asarray(positions, dtype='<f4')
    attribute = glb._accessor(vertices, 5126, 'VEC3', 34962, True)
    glb.mesh_node(name, [{'mode': 1, 'attributes': {'POSITION': attribute}, 'material': material}])


def save(glb, entry):
    path = ROOT / f"content/visualizations/models/{entry['id']}.glb"
    glb.write(path)
    entry.update({'src': str(path.relative_to(ROOT)), 'geometry': 'mesh',
                  'license': 'U.S. public-domain NASA media; NASA usage guidelines apply (not CC0)',
                  'license_url': 'https://www.nasa.gov/nasa-brand-center/images-and-media/',
                  'license_files': ['licenses/nasa-media-guidelines.html', 'licenses/nasa-3d-resources.README.md'],
                  'volume_semantics': 'not_applicable', 'closed_volume_checked': False,
                  **inspect_glb(path.read_bytes())})
    entry_path = HANDOFF / f"{entry['id']}.entry.json"
    write_json(entry_path, entry)
    register(entry_path, path, 'length')
    return entry


def build_mars(directory):
    data = (directory/'mars-map').read_bytes()
    image = Image.open(io.BytesIO(data)).convert('RGB')
    image.thumbnail((2048, 1024), Image.Resampling.LANCZOS)
    output = io.BytesIO(); image.save(output, format='JPEG', quality=90, subsampling=0)
    glb = GLB('Universe Scales NASA Mars map globe')
    texture = glb.texture(output.getvalue(), 'image/jpeg')
    material = glb.material('NASA Mars mosaic', texture=texture, double_sided=False)
    sphere(glb, 'Mars', 1, material)
    return save(glb, {
        'id': 'nasa-mars-length', 'author': 'NASA; sphere assembled by Universe Scales',
        'source': 'https://github.com/nasa/NASA-3D-Resources/tree/master/Images%20and%20Textures/Mars',
        'download_url': 'https://raw.githubusercontent.com/nasa/NASA-3D-Resources/master/Images%20and%20Textures/Mars/Mars.jpg',
        'source_sha256': sha(data), 'source_bytes': len(data),
        'matches': {'length': ['Mars']}, 'representation': 'textured-sphere',
        'presentation': {'reference_size': 2, 'yaw': 125, 'roughness': 1, 'metalness': 0},
        'note': 'An idealized spherical Mars with the global Mars map distributed by NASA 3D Resources. The catalog mean diameter sets the sphere diameter. Surface colors come from the NASA map; no terrain relief or independent global elevation reconstruction is implied.',
        'processing': {'operations': ['Create latitude-longitude sphere of radius 1', 'Apply NASA global Mars image without invented surface markings', 'Embed JPEG texture at 2048 x 1024 maximum'], 'source_texture_sha256': sha(data)},
    })


def build_parker():
    # Dataset definition/source: SVS 14741, 3.8 million miles above the surface.
    altitude = 6_115_507_200
    solar_radius = 695_700_000  # NASA Sun Fact Sheet, volumetric mean radius.
    radius = solar_radius / altitude
    registry = json.loads((ROOT/'content/visualizations/models.json').read_text())['models']
    sun = next(m for m in registry if m['id'] == 'nasa-sun')
    glb = GLB('Universe Scales surface-referenced Parker encounter diagram')
    glb.doc['samplers'] = []
    source = (ROOT/sun['src']).read_bytes()
    add_sphere(glb.doc, glb.bin, source, 'Sun', -.5-radius, altitude)
    glb.doc['scenes'][0]['nodes'] = [0]
    glb.doc['nodes'][0]['extras'] = {'label': 'Sun', 'outline': True, 'sphere': True}
    # add_sphere copies a node; its physical radius uses the same NASA value.
    lower = -radius-.08
    line(glb, 'Surface-to-encounter ruler', [(-.5, 0, 0), (-.5, lower, 0),
                                            (-.5, lower, 0), (.5, lower, 0),
                                            (.5, lower, 0), (.5, 0, 0)], (.85, .9, 1))
    dot = glb.material('Encounter marker (not probe dimensions)', color=(1, .65, .15, 1), emissive=(.5, .2, .01))
    sphere(glb, 'Encounter location marker', .003, dot, (.5, 0, 0), 16, 8)
    glb.label_node('Encounter', (.5, .035, 0), '24 Dec 2024 encounter')
    glb.label_node('Altitude definition', (0, lower-.04, 0), '~6.1 million km above surface')
    return save(glb, {
        'id': 'nasa-parker-perihelion-distance', 'author': 'NASA; diagram assembled by Universe Scales',
        'source': 'https://svs.gsfc.nasa.gov/14741/',
        'basis_url': 'https://nssdc.gsfc.nasa.gov/planetary/factsheet/sunfact.html',
        'basis_label': 'NASA solar radius',
        'matches': {'length': ['Parker Solar Probe Closest Approach']}, 'representation': 'measurement-diagram',
        'presentation': {'reference_size': 1, 'roughness': 1, 'metalness': 0},
        'note': 'A Sun-to-encounter distance diagram for 24 December 2024. The ruler starts at the visible solar surface and spans the catalog altitude of about 6.1 million km; it does not start at the Sun\'s center. The Sun has the same physical scale. The amber point only marks the encounter location and is not the probe\'s size. The direction is illustrative, with no claim of orbital orientation or a full trajectory.',
        'processing': {'altitude_m': altitude, 'solar_radius_m': solar_radius,
                       'source_models': [{'id': sun['id'], 'sha256': sha(source), 'source': sun['source']}],
                       'operations': ['Reuse the existing NASA Sun mesh and texture', 'Place a location marker one altitude beyond the photosphere', 'Author a surface-to-marker ruler; retain physical Sun/altitude proportions']},
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True)
    args = parser.parse_args()
    HANDOFF.mkdir(parents=True, exist_ok=True)
    build_mars(args.source_dir)
    build_parker()


if __name__ == '__main__':
    main()
