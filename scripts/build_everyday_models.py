#!/usr/bin/env python3
"""Build dimensioned everyday objects and the VLT primary mirror, offline.

All geometry is in metres. Standards/datasheets and authored details are
documented in content/visualizations/models/sources/earth3d-*.md.
No external artwork, fonts, photos, runtime dependencies or mesh decoders.
"""
import argparse
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from fetch_model_assets import inspect_glb
from geo_glb_common import GLB, grid_indices

ROOT = Path(__file__).resolve().parents[1]
ISO_CARD = 'https://www.iso.org/obp/ui#iso:std:iso-iec:7810:ed-3:v1:en'
SOURCES = {
    'table-tennis': ('Table Tennis Ball', .04, 'https://db.ittf.com/sites/default/files/public/2023-09/2023_ITTF_Statutes_clean_version2_2023-09-01_2.pdf',
                     'ITTF Laws 2.3: 40 mm diameter. Original unbranded matte shell; printed markings and wall thickness are omitted.'),
    'tennis': ('Tennis Ball', .067, 'https://www.itftennis.com/media/11845/2024-rulebook-atp-update.pdf',
               'A representative 67 mm ball, within the ITF Type 1/2 diameter range 65.4–68.6 mm. Original felt texture and stitchless seam pattern are illustrative; no manufacturer is implied.'),
    'basketball': ('Basketball', .239, 'https://au.wilson.com/pages/how-to-choose-a-basketball/1000',
                   'Representative size-7 basketball. Wilson specifies 29.5 inches circumference (238.51 mm derived diameter), rounded to the catalog’s 239 mm. Original pebble texture and eight-panel channel pattern are illustrative.'),
    'credit-card': ('Credit Card', .0856, ISO_CARD,
                    'ISO/IEC 7810 ID-1 envelope: 85.60 × 53.98 × 0.76 mm. Original fictitious unpersonalized card artwork; chip and graphic layout are illustrative. No account data or payment-brand marks.'),
    'smartphone': ('Smartphone', .1476, 'https://support.apple.com/en-us/121029',
                   'iPhone 16 body envelope from Apple: 147.6 × 71.6 × 7.8 mm. Original simplified exterior illustration, with authored screen art, corner curves, buttons and camera details; these small details are not engineering measurements. No internal geometry.'),
    'a4-paper': ('A4 Paper', .297, 'https://preview.sist.si/sist-preview/4087/9050e9a6768b43e2bcdedca70c895c61/ISO-216-1975.pdf',
                 'ISO 216 A4: 210 × 297 mm. A flat, double-sided sheet surface; thickness is deliberately not modeled because ISO 216 defines the trimmed edges, not a paper stock. No exaggerated curl or thickness.'),
    'silicon-wafer': ('Silicon Wafer', .3, 'https://svmi.com/wp-content/uploads/2020/09/SV031.pdf',
                      'Bare polished 300 mm silicon wafer, using SVM SV031 nominal 775 µm thickness and a 1 mm-deep 90° notch. No invented chip layout or enlarged circuitry; violet-gray appearance is illustrative.'),
    'vlt-mirror': ('Very Large Telescope Mirror', 8.2, 'https://www.eso.org/sci/facilities/paranal/telescopes/ut/m1unit.html',
                   'VLT M1 dimensioned optical illustration: 8.2 m outer diameter, 1 m central hole, nominal 175 mm meniscus thickness. Concave surface follows the published 28.8 m radius and conic constant −1.004616. Back surface is a constant axial offset, not a measured rear surface. Cell and actuators omitted; reflections are a studio environment.'),
}


def image_texture(glb, array):
    stream = io.BytesIO()
    Image.fromarray(np.uint8(np.clip(array, 0, 255))).save(stream, format='PNG')
    return glb.texture(stream.getvalue(), 'image/png')


def mesh(glb, name, points, indices, material, normals=None, uv=None):
    points = np.asarray(points, float)
    indices = np.asarray(indices).reshape(-1, 3)
    face_normals = np.cross(points[indices[:, 1]]-points[indices[:, 0]], points[indices[:, 2]]-points[indices[:, 0]])
    indices = indices[np.linalg.norm(face_normals, axis=1) > 1e-18]
    if normals is None:
        normals = np.zeros_like(points)
        face_normals = np.cross(points[indices[:, 1]]-points[indices[:, 0]], points[indices[:, 2]]-points[indices[:, 0]])
        for k in range(3):
            np.add.at(normals, indices[:, k], face_normals)
        normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-30)
    glb.mesh_node(name, [glb.primitive(points, indices.ravel(), material, normals=normals, uvs=uv)])


def sphere(glb, radius, material):
    lon, lat = np.meshgrid(np.linspace(0, 2*np.pi, 129), np.linspace(-np.pi/2, np.pi/2, 65))
    normals = np.stack((np.cos(lat)*np.cos(lon), np.sin(lat), np.cos(lat)*np.sin(lon)), axis=-1).reshape(-1, 3)
    uv = np.stack((lon/(2*np.pi), .5-lat/np.pi), axis=-1).reshape(-1, 2)
    indices = grid_indices(65, 129).reshape(-1, 3)
    mesh(glb, 'Calibrated spherical exterior', normals*radius, indices, material, normals, uv)


def ball(kind):
    glb = GLB('Universe Scales: dimensioned sporting ball')
    if kind == 'table-tennis':
        mat = glb.material('Unprinted matte white plastic', (.94, .94, .91, 1), rough=.72, double_sided=False)
    else:
        n = 1024
        uu, vv = np.meshgrid((np.arange(n)+.5)/n, (np.arange(n)+.5)/n)
        lon, lat = uu*2*np.pi, (.5-vv)*np.pi
        rng = np.random.default_rng(20261016)
        noise = rng.normal(0, 1, (n, n))
        if kind == 'tennis':
            # One closed undulating seam divides the two felt panels.
            distance = np.abs(lat-.63*np.sin(2*lon))
            seam = np.clip((.027-distance)/.007, 0, 1)
            base = np.array([191, 212, 39])
            rgb = base + noise[..., None]*3.5
            rgb = rgb*(1-seam[..., None]) + (np.array([238, 237, 206])+noise[..., None])*seam[..., None]
            rough = .97
        else:
            # Equator, meridian and two closed bowed channels produce eight panels.
            x = np.cos(lat)*np.cos(lon)
            y = np.sin(lat)
            z = np.cos(lat)*np.sin(lon)
            distance = np.minimum(np.abs(y), np.abs(x))
            # Two small-circle channels, each contained in one x hemisphere.
            distance = np.minimum(distance, np.abs(x-.69))
            distance = np.minimum(distance, np.abs(x+.69))
            seam = np.clip((.018-distance)/.004, 0, 1)
            pebble = np.sin(uu*2*np.pi*150)*np.sin(vv*np.pi*150)
            rgb = np.array([183, 79, 24]) + (noise*2+pebble*5)[..., None]
            rgb = rgb*(1-seam[..., None]) + np.array([30, 24, 18])*seam[..., None]
            rough = .86
        tex = image_texture(glb, rgb)
        mat = glb.material('Felt' if kind == 'tennis' else 'Pebbled composite and dark channels', rough=rough, texture=tex, double_sided=False)
    sphere(glb, SOURCES[kind][1]/2, mat)
    return glb


def rounded_outline(width, height, radius, steps=12):
    result = []
    for cx, cy, angle in [(width/2-radius, height/2-radius, 0), (-width/2+radius, height/2-radius, 90),
                           (-width/2+radius, -height/2+radius, 180), (width/2-radius, -height/2+radius, 270)]:
        for a in np.radians(np.linspace(angle, angle+90, steps+1)):
            result.append((cx+radius*np.cos(a), cy+radius*np.sin(a)))
    return np.array(result)


def plate(glb, name, outline, depth, face_mat, side_mat=None, back_mat=None, z=0):
    """Convex/star-convex XY outline, actual Z thickness; UVs fill face bounds."""
    n = len(outline)
    width, height = np.ptp(outline, axis=0)
    center = (outline.min(axis=0)+outline.max(axis=0))/2
    for front, mat in [(True, face_mat), (False, back_mat if back_mat is not None else face_mat)]:
        if not front and depth == 0:
            continue
        points = np.column_stack((np.vstack((center, outline)), np.full(n+1, z+(depth/2 if front else -depth/2))))
        indices = np.array([(0, i+1, (i+1) % n+1) for i in range(n)])
        if not front:
            indices = indices[:, ::-1]
        uv = np.column_stack(((points[:, 0]-center[0])/width+.5, .5-(points[:, 1]-center[1])/height))
        mesh(glb, name+(' front' if front else ' back'), points, indices, mat,
             np.tile([0, 0, 1 if front else -1], (n+1, 1)), uv)
    if depth > 0:
        for_side, side_n, indices = [], [], []
        for i in range(n):
            a, b = outline[i], outline[(i+1) % n]
            normal = np.array([b[1]-a[1], a[0]-b[0], 0]); normal /= np.linalg.norm(normal)
            k = len(for_side)
            for_side.extend([(a[0], a[1], z-depth/2), (b[0], b[1], z-depth/2),
                             (b[0], b[1], z+depth/2), (a[0], a[1], z+depth/2)])
            side_n.extend([normal]*4)
            indices.extend([(k, k+1, k+2), (k, k+2, k+3)])
        mesh(glb, name+' edge', for_side, indices, side_mat if side_mat is not None else face_mat, side_n)


def card():
    glb = GLB('Universe Scales: ID-1 card')
    h, w = 640, 1024
    yy, xx = np.mgrid[:h, :w]
    t = (xx/w*.55 + yy/h*.45)[..., None]
    rgb = np.array([18, 53, 77])*(1-t)+np.array([36, 111, 131])*t
    art = Image.fromarray(rgb.astype('uint8')); draw = ImageDraw.Draw(art)
    for offset in range(0, 7):
        draw.arc((650-offset*28, -210-offset*28, 1190+offset*28, 320+offset*28), 30, 300, fill=(68, 140, 153), width=2)
    draw.rounded_rectangle((110, 214, 262, 334), radius=14, fill='#cdb680', outline='#eddbb5', width=2)
    for x in [156, 211]:
        draw.line((x, 216, x, 333), fill='#746443', width=3)
    draw.line((111, 254, 261, 254), fill='#746443', width=3)
    draw.line((111, 294, 261, 294), fill='#746443', width=3)
    # Unpersonalized graphic bars, no invented personal/account information.
    for x in [112, 300, 488, 676]:
        draw.rounded_rectangle((x, 432, x+126, 442), radius=4, fill='#91b1bd')
    tex = image_texture(glb, np.array(art))
    front = glb.material('Original fictitious card design', rough=.42, texture=tex)
    edge = glb.material('Card polymer', (.23, .31, .35, 1), rough=.55)
    back = glb.material('Plain reverse', (.06, .18, .23, 1), rough=.5)
    # Rounded corners and graphics are authored; the nominal envelope is calibrated.
    plate(glb, 'ID-1 card', rounded_outline(.0856, .05398, .00318), .00076, front, edge, back)
    return glb


def phone():
    glb = GLB('Universe Scales: dimensioned iPhone 16 exterior illustration')
    rim = glb.material('Satin teal aluminum', (.12, .38, .41, 1), rough=.32, metal=.7)
    back = glb.material('Teal back glass', (.18, .53, .53, 1), rough=.23, metal=.08)
    plate(glb, '147.6 by 71.6 mm body', rounded_outline(.0716, .1476, .011), .0078, rim, rim, back)
    h, w = 1024, 512
    yy, xx = np.mgrid[:h, :w]
    q = (np.sin(xx/w*3+yy/h*5)+1)/2
    rgb = np.array([13, 28, 65])+q[..., None]*np.array([21, 96, 99])
    art = Image.fromarray(rgb.astype('uint8')); d = ImageDraw.Draw(art)
    d.rounded_rectangle((187, 26, 325, 61), radius=18, fill='#080e15')
    d.rounded_rectangle((185, 985, 327, 990), radius=3, fill='#d0eded')
    tex = image_texture(glb, np.array(art))
    glass = glb.material('Original screen art', rough=.23, texture=tex)
    plate(glb, 'Screen within body envelope', rounded_outline(.0676, .1436, .009), 0, glass, z=.003905)
    # Simplified camera shapes, not an Apple engineering model or measured protrusions.
    camera = glb.material('Camera surround', (.09, .28, .30, 1), rough=.28, metal=.45)
    lens = glb.material('Lens glass', (.012, .025, .04, 1), rough=.1, metal=.3)
    camera_outline = rounded_outline(.017, .033, .008)
    camera_outline += [-.020, .048]
    plate(glb, 'Authored camera island', camera_outline, .001, camera, z=-.0041)
    for cy in [.055, .041]:
        outline = np.array([(np.cos(t)*.0058-.020, np.sin(t)*.0058+cy) for t in np.linspace(0, 2*np.pi, 65)[:-1]])
        plate(glb, 'Illustrative camera lens', outline, .0005, lens, z=-.0048)
    return glb


def paper():
    glb = GLB('Universe Scales: ISO 216 A4 dimensional sheet')
    mat = glb.material('Unprinted white paper', (.91, .92, .90, 1), rough=1)
    # No stock thickness is implied by ISO 216.
    plate(glb, '210 by 297 mm sheet', np.array([[-.105, -.1485], [.105, -.1485], [.105, .1485], [-.105, .1485]]), 0, mat)
    return glb


def wafer():
    glb = GLB('Universe Scales: 300 mm bare silicon wafer')
    front = glb.material('Polished bare silicon', (.29, .29, .36, 1), rough=.15, metal=.65)
    edge = glb.material('Silicon edge', (.17, .18, .22, 1), rough=.4, metal=.35)
    radius, notch = .15, .001
    # Bottom V notch: 1 mm nominal depth, 90 degree included angle.
    theta = math.asin(notch/radius)
    angle = np.linspace(-np.pi/2+theta, 3*np.pi/2-theta, 513)
    outline = np.column_stack((radius*np.cos(angle), radius*np.sin(angle)))
    outline = np.vstack((outline, [0, -radius+notch]))
    plate(glb, '300 mm wafer, 775 micrometre thick', outline, .000775, front, edge)
    return glb


def mirror():
    glb = GLB('Universe Scales: ESO VLT M1 dimensioned optical illustration')
    front = glb.material('Aluminized optical surface', (.85, .89, .94, 1), rough=.085, metal=1)
    body = glb.material('Zerodur substrate', (.36, .37, .32, 1), rough=.6, metal=.12)
    radii = np.linspace(.5, 4.1, 49)
    angles = np.linspace(0, 2*np.pi, 193)
    r, a = np.meshgrid(radii, angles, indexing='ij')
    curvature, conic = 28.8, -1.004616
    sag = r*r/(curvature*(1+np.sqrt(1-(1+conic)*(r/curvature)**2)))
    x, y = r*np.cos(a), r*np.sin(a)
    for is_front, material in [(True, front), (False, body)]:
        # Concavity opens towards +Z; the rear is an explicitly approximate offset.
        z = sag if is_front else sag-.175
        points = np.stack((x, y, z), axis=-1).reshape(-1, 3)
        indices = grid_indices(*r.shape).reshape(-1, 3)
        if not is_front:
            indices = indices[:, ::-1]
        mesh(glb, 'Concave optical face' if is_front else 'Approximate rear face', points, indices, material)
    for edge_index in [0, -1]:
        points = np.stack([np.column_stack((x[edge_index], y[edge_index], sag[edge_index]-.175)),
                           np.column_stack((x[edge_index], y[edge_index], sag[edge_index]))]).reshape(-1, 3)
        indices = grid_indices(2, len(angles)).reshape(-1, 3)
        if edge_index == 0:
            indices = indices[:, ::-1]
        mesh(glb, 'Central bore' if edge_index == 0 else 'Outer edge', points, indices, body)
    return glb


def build(output, handoff):
    output.mkdir(parents=True, exist_ok=True)
    handoff.mkdir(parents=True, exist_ok=True)
    for kind, (name, value, source, note) in SOURCES.items():
        model_id = 'earth3d-'+kind
        glb = ball(kind) if kind in ('table-tennis', 'tennis', 'basketball') else {'credit-card': card, 'smartphone': phone, 'a4-paper': paper, 'silicon-wafer': wafer, 'vlt-mirror': mirror}[kind]()
        path = output / (model_id+'.glb'); glb.write(path)
        presentation = dict(reference_size=value, yaw=-15, pitch=9, roll=0)
        if kind in ('table-tennis', 'tennis', 'basketball'):
            presentation.update(yaw=20, pitch=12)
        if kind == 'credit-card':
            presentation.update(yaw=-15, pitch=12, roll=-7)
        if kind == 'vlt-mirror':
            presentation.update(yaw=-20, pitch=16, environment=.9)
        if kind == 'silicon-wafer':
            presentation.update(environment=.8)
        entry = dict(id=model_id, source=source, author='Universe Scales', license='CC0-1.0',
                     license_url='https://creativecommons.org/publicdomain/zero/1.0/', license_files=['licenses/CC0-1.0.txt'],
                     matches={'length': [name]}, geometry='mesh', representation='dimensioned_illustration',
                     volume_semantics='not_applicable', closed_volume_checked=False, presentation=presentation, note=note,
                     basis_url=source, basis_label='Dimensional standard / technical source',
                     processing={'script': 'scripts/build_everyday_models.py', 'units': 'metres', 'reference_size_m': value,
                                 'provenance': f'content/visualizations/models/sources/{model_id}.md'},
                     src=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path), **inspect_glb(path.read_bytes()))
        (handoff / (model_id+'.entry.json')).write_text(json.dumps(entry, indent=2, ensure_ascii=False)+'\n')
        print(f"{name}: {entry['bytes']:,} bytes, {entry['triangle_count']:,} triangles")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT/'content/visualizations/models')
    parser.add_argument('--handoff', type=Path, default=ROOT/'handoff/earth3d')
    args = parser.parse_args()
    build(args.output_dir, args.handoff)
