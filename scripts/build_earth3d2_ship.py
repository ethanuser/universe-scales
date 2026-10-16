#!/usr/bin/env python3
"""Original Ever Given exterior illustration: sourced envelope, authored details.

No downloaded ship geometry or copied photographs/textures. Not a cargo manifest,
naval-architecture model, or reconstruction of the Suez grounding configuration.
"""
import json

import numpy as np
from PIL import Image

from build_earth3d2_structures import Batch, HANDOFF, ROOT
from build_everyday_models import image_texture, mesh
from fetch_model_assets import inspect_glb
from geo_glb_common import GLB

SOURCE = 'https://gcaptain.com/wp-content/uploads/2023/07/Final-Investigation-Report-Ever-Given-23-March-2021.pdf'


def box(points, normals, uv, indices, center, size):
    center, half = np.asarray(center), np.asarray(size)/2
    for normal, corners in [
        ([1, 0, 0], [(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)]),
        ([-1, 0, 0], [(-1, -1, 1), (-1, 1, 1), (-1, 1, -1), (-1, -1, -1)]),
        ([0, 1, 0], [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)]),
        ([0, -1, 0], [(-1, -1, 1), (-1, -1, -1), (1, -1, -1), (1, -1, 1)]),
        ([0, 0, 1], [(1, -1, 1), (1, 1, 1), (-1, 1, 1), (-1, -1, 1)]),
        ([0, 0, -1], [(-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)]),
    ]:
        k = len(points)
        points.extend(center+np.asarray(corners)*half)
        normals.extend([normal]*4)
        uv.extend([(0, 1), (0, 0), (1, 0), (1, 1)])
        indices.extend([(k, k+1, k+2), (k, k+2, k+3)])


def build():
    glb = GLB('Universe Scales: original dimensioned Ever Given exterior illustration')
    hull = glb.material('Evergreen green, illustrative paint', (.025, .24, .10, 1), rough=.65, double_sided=False)
    lower = glb.material('Authored anti-fouling red', (.34, .055, .032, 1), rough=.78, double_sided=False)
    deck = glb.material('Painted cargo deck', (.10, .22, .17, 1), rough=.83, double_sided=False)
    white = glb.material('Accommodation and bridge', (.8, .81, .76, 1), rough=.68)
    glass = glb.material('Bridge glazing, illustrative', (.025, .065, .085, 1), rough=.32, metal=.15)
    gray = glb.material('Deck machinery', (.28, .32, .30, 1), rough=.74)
    black = glb.material('Funnel cap', (.035, .04, .035, 1), rough=.9)
    # Only overall length, beam and moulded depth are measurements. Section widths,
    # keel rise, the bow/transom curves and the smaller details are authored.
    length, breadth, depth = 399.98, 58.8, 32.9
    sections = np.array([[-length/2, 17, 8], [-190, 25, 3], [-175, 28.7, 0],
                         [-145, breadth/2, 0], [0, breadth/2, 0], [115, breadth/2, 0],
                         [148, 28.8, 1], [171, 24, 3], [187, 16, 7], [197, 5, 11], [length/2, .15, 15]])
    rings = []
    for x, width, bottom in sections:
        shoulder = max(16.5, bottom+4)
        rings.append([[x, depth, -width], [x, depth, width], [x, shoulder, width],
                      [x, bottom+3, width*.75], [x, bottom, 0], [x, bottom+3, -width*.75], [x, shoulder, -width]])
    p = np.asarray(rings)
    for name, mat, edges in [('Upper green hull', hull, [1, 6]), ('Lower hull', lower, [2, 3, 4, 5])]:
        points, faces = [], []
        for i in range(len(rings)-1):
            for j in edges:
                k = len(points); b = (j+1) % 7
                points.extend([p[i, j], p[i, b], p[i+1, b], p[i+1, j]])
                faces.extend([(k, k+1, k+2), (k, k+2, k+3)])
        mesh(glb, name, points, faces, mat)
    # Flat main deck, with no invented under-deck holds or ballast structure.
    points, faces = [], []
    for i in range(len(rings)-1):
        k = len(points); points.extend([p[i, 0], p[i, 1], p[i+1, 1], p[i+1, 0]])
        faces.extend([(k, k+1, k+2), (k, k+2, k+3)])
    mesh(glb, 'Authored main deck outline', points, faces, deck)
    for end in [0, len(rings)-1]:
        ring = p[end]; points = [ring.mean(0), *ring]
        faces = [(0, 1+j, 1+(j+1) % 7) for j in range(7)]
        if end == 0:
            faces = [tuple(reversed(f)) for f in faces]
        mesh(glb, 'Closed display transom/end', points, faces, hull)
    structure = Batch(glb)
    # Approximate locations follow the report's general-arrangement view, Figure 2.
    # They are deliberately not represented as dimensions extracted from the plan.
    for y in np.arange(depth+1.5, 61, 3):
        structure.beam([54, y, -22], [54, y, 22], 12, 2.85, white)
    structure.beam([54, 62, -27], [54, 62, 27], 14, 3.4, white)
    structure.beam([61.05, 62.3, -26], [61.05, 62.3, 26], .12, 1.9, glass)
    for z in [-22.1, 22.1]:
        for y in np.arange(38, 58, 4):
            for x in np.arange(50, 59, 2.5):
                structure.beam([x, y, z], [x+.8, y, z], .7, .08, glass)
    structure.beam([-139, depth, 0], [-139, 58, 0], 15, 13, white)
    structure.beam([-139, 58, 0], [-139, 61, 0], 16, 14, hull)
    structure.beam([-139, 61, 0], [-139, 62, 0], 16.2, 14.2, black)
    for x, y in [(54, 65), (-139, 64), (186, 37)]:
        structure.beam([x, y, 0], [x, y+6, 0], .25, .25, gray)
        structure.beam([x-3, y+3, 0], [x+3, y+3, 0], .2, .2, gray)
    for x in [-188, 179]:
        for z in [-9, 9]:
            structure.beam([x, depth+.4, z], [x, depth+2, z], 3, 4, gray)
    structure.write()
    # Authored partial load of nominal 40-foot high-cube boxes. This is no cargo
    # inventory or claim to the appearance on any particular voyage/date.
    yy, xx = np.mgrid[:64, :256]
    shade = (220+18*np.cos(xx/256*2*np.pi*36))[:, :, None]*np.ones((1, 1, 3))
    shade[[0, 1, 62, 63], :, :] = 140
    shade[:, [0, 1, 254, 255], :] = 140
    texture = image_texture(glb, shade)
    palette = [(.16, .35, .22), (.18, .26, .36), (.51, .16, .10), (.56, .45, .22),
               (.58, .62, .59), (.33, .19, .15), (.14, .36, .37), (.36, .39, .34)]
    cargo = []
    for index, color in enumerate(palette):
        mat = glb.material(f'Original container color {index+1}', (*color, 1), rough=.83, texture=texture, double_sided=False)
        cargo.append([mat, [], [], [], []])
    rng = np.random.default_rng(9811000)
    count = 0
    for x in np.arange(-174, 163, 12.5):
        if abs(x-54) < 14 or abs(x+139) < 14:
            continue
        width = np.interp(x, sections[:, 0], sections[:, 1])
        for row, z in enumerate(np.arange(-26.4, 27, 2.55)):
            if abs(z)+1.219 > width-1:
                continue
            tiers = 5 if abs(z) < 22 and x < 140 else 4
            if x > 152:
                tiers = 3
            for tier in range(tiers):
                mat, points, normals, uv, indices = cargo[int(rng.integers(len(cargo))) ]
                box(points, normals, uv, indices, [x, depth+.13+2.896/2+tier*2.93, z], [12.192, 2.896, 2.438])
                count += 1
    for mat, points, normals, uv, indices in cargo:
        mesh(glb, glb.doc['materials'][mat]['name'], points, indices, mat, np.asarray(normals), np.asarray(uv))
    model_id = 'earth3d2-ever-given'
    path = ROOT/f'content/visualizations/models/{model_id}.glb'; glb.write(path)
    entry = dict(id=model_id, source=SOURCE, basis_url=SOURCE, basis_label='Panama Maritime Authority: vessel particulars and arrangement',
                 author='Universe Scales', license='CC0-1.0', license_url='https://creativecommons.org/publicdomain/zero/1.0/',
                 license_files=['licenses/CC0-1.0.txt'],
                 matches={'length': ['Ever Given']}, geometry='mesh', representation='dimensioned_illustration',
                 volume_semantics='not_applicable', closed_volume_checked=False,
                 presentation=dict(reference_size=length, yaw=-35, pitch=17, layout_width_factor=1.02),
                 note=('Original exterior illustration of Ever Given. Hull envelope uses the Panama Maritime Authority’s 399.98 m length, '
                       '58.80 m moulded beam and 32.90 m moulded depth; the explorer uniformly calibrates to the catalog’s 399.94 m length '
                       '(a 0.01% difference), without independently stretching any axis. Accommodation and funnel locations are approximate readings '
                       'of the report’s general-arrangement drawing. Hull sections, keel/bow curves, superstructure dimensions, colors and machinery '
                       'are authored simplifications, not shipyard measurements. The partial above-deck load uses nominal 40 ft high-cube boxes; '
                       'its arrangement and colors are illustrative, not a container manifest or reconstruction of the 2021 grounding. '
                       'Propeller, rudder, holds, interior, water and canal are omitted. This is not a naval-architecture or stability model.'),
                 processing=dict(script='scripts/build_earth3d2_ship.py', units='metres',
                                 source_note='content/visualizations/models/sources/earth3d2-ever-given.md',
                                 envelope_m=[length, depth, breadth], partial_load_boxes=count,
                                 container_envelope_m=[12.192, 2.896, 2.438],
                                 details='Authored geometry; no copied ship mesh, drawing pixels, photo or logos.'),
                 src=str(path.relative_to(ROOT)), **inspect_glb(path.read_bytes()))
    HANDOFF.mkdir(parents=True, exist_ok=True)
    (HANDOFF/f'{model_id}.entry.json').write_text(json.dumps(entry, indent=2)+'\n')
    print(model_id, entry['bytes'], entry['triangle_count'], count, 'illustrative boxes')


if __name__ == '__main__':
    build()
