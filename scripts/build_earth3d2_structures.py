#!/usr/bin/env python3
"""Offline, dimensioned exterior diagrams; sources/earth3d2-*.md explains limits."""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from build_everyday_models import image_texture, mesh
from fetch_model_assets import inspect_glb
from geo_glb_common import GLB, grid_indices

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT/'handoff/earth3d2'
BRIDGE_SOURCE = 'https://www.goldengate.org/bridge/history-research/statistics-data/design-construction-stats/'
FAST_SOURCE = 'https://arxiv.org/html/2012.11167v1'
ARECIBO_SOURCE = 'https://www.nationalacademies.org/read/1635/chapter/11'


class Batch:
    """Merge the many small structural members into one primitive per material."""
    def __init__(self, glb):
        self.glb, self.groups = glb, {}

    def add(self, mat, points, indices):
        p, f, count = self.groups.setdefault(mat, [[], [], 0])
        p.append(np.asarray(points, float))
        f.append(np.asarray(indices, int).reshape(-1, 3)+count)
        self.groups[mat][2] += len(points)

    def beam(self, a, b, width, depth, mat):
        a, b = np.asarray(a, float), np.asarray(b, float)
        axis = b-a; axis /= np.linalg.norm(axis)
        side = np.cross(axis, [0, 0, 1] if abs(axis[2]) < .9 else [0, 1, 0])
        side /= np.linalg.norm(side); up = np.cross(axis, side)
        points = [p+side*u*width/2+up*v*depth/2 for p in [a, b] for u, v in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
        self.add(mat, points, [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
                               (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
                               (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)])

    def tube(self, points, radius, mat, sides=8):
        points = np.asarray(points, float)
        tangent = np.gradient(points, axis=0); tangent /= np.linalg.norm(tangent, axis=1)[:, None]
        side = np.cross(tangent, np.tile([0, 0, 1], (len(points), 1)))
        if (np.linalg.norm(side, axis=1) < .01).any():
            raise ValueError('Tube requires a non-Z tangent')
        side /= np.linalg.norm(side, axis=1)[:, None]; up = np.cross(tangent, side)
        angle = np.arange(sides+1)*2*np.pi/sides
        p = points[:, None, :]+radius*(side[:, None, :]*np.cos(angle)[None, :, None]+up[:, None, :]*np.sin(angle)[None, :, None])
        # grid_indices winding is reversed for this frame.
        self.add(mat, p.reshape(-1, 3), grid_indices(len(points), sides+1).reshape(-1, 3)[:, ::-1])

    def write(self):
        for mat, (points, indices, _) in self.groups.items():
            # Flat beam edges are intentional; split by face to avoid rounded towers.
            p = np.concatenate(points); f = np.concatenate(indices)
            triangle_points = p[f].reshape(-1, 3)
            normals = np.cross(p[f[:, 1]]-p[f[:, 0]], p[f[:, 2]]-p[f[:, 0]])
            normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-30)
            mesh(self.glb, self.glb.doc['materials'][mat]['name'], triangle_points,
                 np.arange(len(triangle_points)).reshape(-1, 3), mat, np.repeat(normals, 3, axis=0))


def save(glb, slug, item, reference, basis, note, presentation, processing, display=None):
    model_id = 'earth3d2-'+slug
    path = ROOT/f'content/visualizations/models/{model_id}.glb'; glb.write(path)
    entry = dict(id=model_id, source=basis, basis_url=basis, basis_label='Dimensional and geometric basis',
                 author='Universe Scales', license='CC0-1.0', license_url='https://creativecommons.org/publicdomain/zero/1.0/',
                 license_files=['licenses/CC0-1.0.txt'],
                 matches={'length': [item]}, geometry='mesh', representation='dimensioned_illustration',
                 volume_semantics='not_applicable', closed_volume_checked=False,
                 presentation=dict(reference_size=reference, **presentation), note=note,
                 processing=dict(script='scripts/build_earth3d2_structures.py', units='metres',
                                 source_note=f'content/visualizations/models/sources/{model_id}.md', **processing),
                 src=str(path.relative_to(ROOT)), **inspect_glb(path.read_bytes()))
    if display:
        entry['display_label'] = display
    HANDOFF.mkdir(parents=True, exist_ok=True)
    (HANDOFF/f'{model_id}.entry.json').write_text(json.dumps(entry, indent=2)+'\n')
    print(model_id, entry['bytes'], entry['triangle_count'])


def bridge():
    glb = GLB('Universe Scales: Golden Gate main-span exterior diagram')
    steel = glb.material('International Orange, illustrative paint', (.63, .105, .035, 1), rough=.56, metal=.22)
    cable = glb.material('Painted main cables and suspenders', (.72, .16, .065, 1), rough=.52, metal=.2)
    asphalt = glb.material('Road surface', (.075, .085, .09, 1), rough=.96)
    concrete = glb.material('Tower bases, illustrative', (.46, .43, .37, 1), rough=.98)
    markings = glb.material('Road markings, illustrative', (.71, .66, .44, 1), rough=.9)
    batch = Batch(glb)
    # Major geometry follows District dimensions; minor members are authored.
    span = 1280.16  # 4,200 international feet; dataset rounds this to 1,280 m.
    half = span/2
    tower_top, deck_y = 746*.3048, (746-500)*.3048
    for x in [-half, half]:
        for z in [-13.7, 13.7]:
            batch.beam([x, 0, z], [x, 5, z], 18, 14, concrete)
            # Four tapered lifts evoke the exterior tower; not a structural survey.
            levels = [5, deck_y-9, deck_y+42, deck_y+89, tower_top]
            widths = [10, 9, 7, 6, 4.5]
            for y0, y1, w0, w1 in zip(levels, levels[1:], widths, widths[1:]):
                p = [[x+sx*w/2, y, z+sz*(16 if y < deck_y else 11)/2]
                     for y, w in [(y0, w0), (y1, w1)] for sx, sz in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
                batch.add(steel, p, np.array([(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
                                     (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
                                     (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)])[:, ::-1])
        for y in [deck_y-9, deck_y+42, deck_y+89, tower_top-6]:
            batch.beam([x, y, -13.7], [x, y, 13.7], 4, 6, steel)
        for y0, y1 in [(deck_y+4, deck_y+39), (deck_y+47, deck_y+86), (deck_y+94, tower_top-10)]:
            for sign in [-1, 1]:
                batch.beam([x, y0, sign*11.5], [x, y1, -sign*11.5], 1.15, 1.15, steel)
    batch.beam([-half, deck_y-1, 0], [half, deck_y-1, 0], 2, 27.432, asphalt)
    # Truss depth, diagonals and tower cross-bracing are schematic exterior details.
    stations = np.linspace(-half, half, 85)  # 84 bays, each 50 ft (15.24 m).
    for z in [-12.8, 12.8]:
        for y in [deck_y-2, deck_y-9]:
            batch.beam([-half, y, z], [half, y, z], .75, .75, steel)
        for a, b in zip(stations, stations[1:]):
            batch.beam([a, deck_y-2, z], [b, deck_y-9, z], .42, .42, steel)
            batch.beam([a, deck_y-9, z], [b, deck_y-2, z], .42, .42, steel)
        batch.beam([-half, deck_y+1.2, z], [half, deck_y+1.2, z], .16, .16, steel)
    # A parabola is a dimensioned approximation to the loaded cable, not a surveyed curve.
    sag = 144  # District-hosted Sheppard/Tongue chapter table 3.1.
    def cable_height(x):
        return tower_top-sag+sag*(np.asarray(x)/half)**2
    xs = np.linspace(-half, half, 257)
    for z in [-13.7, 13.7]:
        batch.tube(np.column_stack((xs, cable_height(xs), np.full(len(xs), z))), .923925/2, cable, 10)
        for x in stations[1:-1]:
            batch.tube([[x, deck_y, z], [x, float(cable_height(x)), z]], (2+11/16)*.0254/2, cable, 6)
    # Unbranded lane markings do not assert current lane control or traffic conditions.
    for z in [-8, -4, 0, 4, 8]:
        for x in np.arange(-half+6, half-6, 14):
            batch.beam([x, deck_y+.015, z], [min(x+5, half), deck_y+.015, z], .025, .12, markings)
    batch.write()
    glb.label_node('Model scope', [0, tower_top+24, 0], 'MAIN SPAN ONLY · side spans omitted')
    glb.label_node('Span definition', [0, -22, 0], '1,280 m · tower center to tower center')
    note = ('Original dimensioned exterior diagram of the Golden Gate Bridge main span only. '
            'Tower centers are 4,200 ft (1,280.16 m) apart; the catalog rounds this to 1,280 m. '
            'The 90 ft deck width, 746 ft tower height, 500 ft tower height above the deck, '
            'main cable diameter and 50 ft suspender spacing follow the Bridge District. '
            'The main cable is a parabolic approximation with 144 m sag from the District-hosted statics chapter. '
            'Tower taper, bracing, trusses, deck profile, road markings and colors are authored exterior simplifications. '
            'The cut stops at the main towers; side spans, anchorages, terrain, submerged foundations and internal construction are omitted. '
            'This is not a structural engineering model.')
    save(glb, 'golden-gate-main-span', 'Golden Gate Bridge Main Span', 1280, BRIDGE_SOURCE, note,
         dict(yaw=-38, pitch=12, layout_width_factor=1.04),
         dict(tower_center_span_m=span, cable_sag_m=sag, minor_geometry='authored exterior simplification'),
         'Golden Gate Bridge · main span only')


def reflector(kind):
    fast = kind == 'fast'
    diameter, radius = (500, 300) if fast else (305, 265)
    glb = GLB(f'Universe Scales: {kind.upper()} nominal spherical primary reflector')
    # The texture shows authored panel organization, not a surveyed panel inventory.
    size = 1024
    rng = np.random.default_rng(491 if fast else 305)
    art = Image.new('RGB', (size, size), '#bac4c7'); draw = ImageDraw.Draw(art)
    if fast:
        step = 24; rowheight = step*math.sqrt(3)/2
        for j in range(-1, int(size/rowheight)+2):
            y = j*rowheight
            shift = (j % 2)*step/2
            for i in range(-1, size//step+2):
                x = i*step+shift
                for direction in [-1, 1]:
                    vertices = [(x, y), (x+step, y), (x+step/2, y+direction*rowheight)]
                    shade = int(rng.integers(168, 201))
                    draw.polygon(vertices, fill=(shade, min(255, shade+8), min(255, shade+11)))
                    draw.line(vertices+[vertices[0]], fill='#7f9099', width=1)
    else:
        # Rectangular texture frequency approximates 3 x 6 ft panels.
        sx, sy = .9144/diameter*size, 1.8288/diameter*size
        for j in range(int(size/sy)+1):
            for i in range(int(size/sx)+1):
                v = int(rng.integers(174, 202))
                draw.rectangle((i*sx, j*sy, (i+1)*sx, (j+1)*sy), fill=(v, v+5, v+7))
        for x in np.arange(0, size, sx):
            draw.line([(x, 0), (x, size)], fill='#8a989d', width=1)
        for y in np.arange(0, size, sy):
            draw.line([(0, y), (size, y)], fill='#8a989d', width=1)
    texture = image_texture(glb, np.asarray(art))
    material = glb.material('Illustrative aluminum panel pattern', rough=.62, metal=.35, texture=texture)
    r, angle = np.meshgrid(np.linspace(0, diameter/2, 65), np.linspace(0, 2*np.pi, 257), indexing='ij')
    x, z = r*np.cos(angle), r*np.sin(angle)
    y = radius-np.sqrt(radius**2-r*r)
    p = np.stack((x, y, z), axis=-1).reshape(-1, 3)
    ns = np.stack((-x, radius-y, -z), axis=-1).reshape(-1, 3)/radius
    uv = np.stack((x/diameter+.5, z/diameter+.5), axis=-1).reshape(-1, 2)
    mesh(glb, 'Nominal spherical reflector surface; zero thickness', p,
         grid_indices(*r.shape).reshape(-1, 3)[:, ::-1], material, ns, uv)
    name = 'FAST Radio Telescope' if fast else 'Arecibo Telescope'
    glb.label_node('Scope qualifier', [0, y.max()+diameter*.13, 0], 'NOMINAL SPHERICAL REFLECTOR ONLY' if fast else 'PRE-COLLAPSE REFLECTOR ONLY')
    glb.label_node('Diameter', [0, -diameter*.07, diameter*.10], f'{diameter} m diameter')
    note = (f'Original dimensioned diagram of the {diameter} m primary reflector only, as a spherical cap '
            f'with {radius} m curvature radius. Geometry uses equal horizontal and vertical metres. ')
    if fast:
        note += ('FAST’s 500 m physical reflector is larger than its approximately 300 m illuminated aperture. '
                 'This is its nominal spherical reference shape, not the actively deformed paraboloid during an observation. '
                 'The triangular panel texture is an authored visual cue, not the measured panel layout or a panel-count claim. ')
    else:
        note += ('This is an idealized intact, pre-December-2020 surface, not the observatory’s present condition. '
                 'The rectangular texture approximates the published 3 × 6 ft aluminum panels, but is not a survey of their layout. ')
    note += ('Feed cabin/platform, suspension towers, cable network, surrounding ground and support structure are omitted. '
             'The zero-thickness, double-sided surface does not assert a solid metal bowl or a shell thickness; colors and reflections are illustrative.')
    save(glb, f'{kind}-reflector', name, diameter, FAST_SOURCE if fast else ARECIBO_SOURCE, note,
         dict(yaw=-12, pitch=50, layout_width_factor=1.02, environment=.3),
         dict(diameter_m=diameter, nominal_curvature_radius_m=radius, active_deformation=False,
              panel_pattern='authored, not a measured panel layout'),
         f'{"FAST" if fast else "Arecibo"} · {"nominal " if fast else "pre-collapse "}reflector only')


if __name__ == '__main__':
    bridge()
    reflector('fast')
    reflector('arecibo')
