#!/usr/bin/env python3
"""Gateway Arch exterior loft from the NPS centroid/cross-section equations.

The weighted catenary is NOT a parabola or a constant-thickness extrusion.
See sources/earth3d-gateway-arch.md. All source constants are in feet.
"""
import json
from pathlib import Path

import numpy as np

from build_everyday_models import mesh
from fetch_model_assets import inspect_glb
from geo_glb_common import GLB

ROOT = Path(__file__).resolve().parents[1]
A, C, L, H = 68.7672, 3.0022, 299.2239, 625.0925
FOOT = .3048


def section(x):
    drop = A*(np.cosh(C*x/L)-1)
    y = H-drop
    slope = -A*C/L*np.sinh(C*x/L)
    outward = np.array([-slope, 1, 0]); outward /= np.linalg.norm(outward)
    side = np.sqrt(17**2+(54**2-17**2)*drop/H)
    center = np.array([x, y, 0])
    outer = center+outward*side/(2*np.sqrt(3))
    return np.array([outer+[0, 0, side/2], outer-[0, 0, side/2], center-outward*side/np.sqrt(3)])


def clip_ground(polygon):
    result = []
    for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
        if a[1] >= 0:
            result.append(a)
        if (a[1] >= 0) != (b[1] >= 0):
            t = a[1]/(a[1]-b[1])
            p = a+t*(b-a); p[1] = 0
            result.append(p)
    return result


def build():
    glb = GLB('Universe Scales: NPS weighted-catenary Gateway Arch exterior')
    steel = glb.material('Brushed stainless steel', (.78, .81, .84, 1), rough=.28, metal=1, double_sided=False)
    xs = np.linspace(-L-1, L+1, 513)
    rings = np.array([section(x) for x in xs])
    points, indices, normals, ground = [], [], [], []
    for i in range(len(xs)-1):
        for face in range(3):
            next_face = (face+1) % 3
            # Reverse orientation, so all three skin faces point outwards.
            polygon = clip_ground(np.array([rings[i, face], rings[i+1, face], rings[i+1, next_face], rings[i, next_face]]))
            if len(polygon) < 3:
                continue
            normal = np.cross(polygon[1]-polygon[0], polygon[2]-polygon[0])
            normal /= np.maximum(np.linalg.norm(normal), 1e-20)
            k = len(points)
            points.extend(polygon); normals.extend([normal]*len(polygon))
            indices.extend([(k, k+j, k+j+1) for j in range(1, len(polygon)-1)])
            ground.extend([p for p in polygon if p[1] == 0])
    # Cap the actual sloping leg/ground intersections; no below-ground foundation.
    for right in [False, True]:
        polygon = np.unique(np.round([p for p in ground if (p[0] > 0) == right], 8), axis=0)
        center = polygon.mean(axis=0)
        angles = np.arctan2(polygon[:, 2]-center[2], polygon[:, 0]-center[0])
        polygon = polygon[np.argsort(angles)]
        k = len(points)
        points.append(center); points.extend(polygon)
        normals.extend([[0, -1, 0]]*(len(polygon)+1))
        indices.extend([(k, k+j+1, k+(j+1) % len(polygon)+1) for j in range(len(polygon))])
    mesh(glb, 'Tapered equilateral-triangle steel exterior', np.array(points)*FOOT, indices, steel, normals)
    model_id = 'earth3d-gateway-arch'
    path = ROOT/f'content/visualizations/models/{model_id}.glb'
    glb.write(path)
    entry = dict(id=model_id, source='https://www.nps.gov/jeff/planyourvisit/mathematical-equation.htm',
                 basis_url='https://www.nps.gov/jeff/planyourvisit/gateway-arch-fact-sheet.htm',
                 basis_label='National Park Service dimensions and exterior geometry',
                 author='Universe Scales, from National Park Service geometry', license='CC0-1.0',
                 license_url='https://creativecommons.org/publicdomain/zero/1.0/', license_files=['licenses/CC0-1.0.txt'],
                 matches={'length': ['Gateway Arch']}, geometry='mesh', representation='dimensioned_illustration',
                 volume_semantics='not_applicable', closed_volume_checked=False,
                 presentation={'reference_size': 630*FOOT, 'yaw': -17, 'pitch': 3, 'environment': .85},
                 note='Dimensioned exterior of the Gateway Arch, using the National Park Service weighted-catenary centroid equation and equilateral triangular sections tapering from 54 ft at the base to 17 ft at the crown. Cross-sectional area varies linearly with distance below the crown. Height and outer span are about 630 ft (192 m). Ground cuts follow the sloping legs. Interiors, foundations, panel joints and observation windows are omitted; steel finish and studio reflections are illustrative.',
                 processing={'script': 'scripts/build_gateway_arch.py', 'units': 'metres',
                             'constants_feet': {'A': A, 'C': C, 'L': L, 'H': H},
                             'provenance': 'content/visualizations/models/sources/earth3d-gateway-arch.md'},
                 src=str(path.relative_to(ROOT)), **inspect_glb(path.read_bytes()))
    handoff = ROOT/'handoff/earth3d'; handoff.mkdir(parents=True, exist_ok=True)
    (handoff/f'{model_id}.entry.json').write_text(json.dumps(entry, indent=2)+'\n')
    p = np.array(points)*FOOT
    print(json.dumps(dict(bytes=entry['bytes'], triangles=entry['triangle_count'], bounds=np.ptp(p, axis=0).tolist())))


if __name__ == '__main__':
    build()
