#!/usr/bin/env python3
"""Offline dimensioned micro3d illustrations. Native units are explicit per asset.

Cuts, colors and nucleon positions are authored, not scans. See sources/micro3d-*.md.
No source images, network requests, or external runtime dependencies are used.
"""
import json
import math
from pathlib import Path

import numpy as np

from build_everyday_models import mesh
from fetch_model_assets import inspect_glb
from geo_glb_common import GLB, grid_indices

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / 'handoff/micro3d'
MODEL_DIR = ROOT / 'content/visualizations/models'

NIST = 'https://physics.nist.gov/cgi-bin/cuu/Value?ral%7Csearch_for=charge'
CNT = 'https://foundry.lbl.gov/2016/10/16/mos2-transistors-with-1-nanometer-gate-lengths/'
GROOVES = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC8571286/'
DVD = 'https://dev.ecma-international.org/wp-content/uploads/ECMA-267_3rd_edition_april_2001.pdf'
BD = 'https://jsss.copernicus.org/articles/8/111/2019/'
SILK = 'https://www.jstage.jst.go.jp/article/jsms1963/44/497/44_497_153/_article/-char/en'
FIBER = 'https://www.corning.com/catalog/coc/documents/product-family-specifications/0396_EMEA_BEN.pdf'
KOLA = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC6981266/'
KARMAN = 'https://www.fai.org/news/statement-about-karman-line'
PREM = 'https://link.springer.com/article/10.1140/epjc/s10052-022-10399-6'


def save(g, slug, item, reference, units, source, note, measurements, pose=None,
         representation='dimensioned_illustration'):
    model_id = 'micro3d-' + slug
    path = MODEL_DIR / (model_id + '.glb')
    g.write(path)
    entry = dict(id=model_id, source=source, basis_url=source, basis_label='Measurement and representation basis',
                 author='Universe Scales', license='CC0-1.0',
                 license_url='https://creativecommons.org/publicdomain/zero/1.0/',
                 license_files=['licenses/CC0-1.0.txt'], matches={'length': [item]},
                 geometry='mesh', representation=representation, volume_semantics='not_applicable',
                 closed_volume_checked=False,
                 presentation=dict(reference_size=reference, **(pose or {})), note=note,
                 processing=dict(script='scripts/build_micro3d_models.py', units=units,
                                 source_note=f'content/visualizations/models/sources/{model_id}.md',
                                 measurements=measurements),
                 src=str(path.relative_to(ROOT)), **inspect_glb(path.read_bytes()))
    HANDOFF.mkdir(parents=True, exist_ok=True)
    (HANDOFF / (model_id + '.entry.json')).write_text(json.dumps(entry, indent=2) + '\n')
    print(model_id, entry['bytes'], entry['triangle_count'])


def surface(g, name, points, rows, columns, mat, normals=None):
    mesh(g, name, np.asarray(points).reshape(-1, 3), grid_indices(rows, columns), mat, normals)


def sphere(g, name, radius, center, mat, lon_range=(0, 2*np.pi)):
    lon, lat = np.meshgrid(np.linspace(*lon_range, 97), np.linspace(-np.pi/2, np.pi/2, 49))
    n = np.stack((np.cos(lat)*np.cos(lon), np.sin(lat), np.cos(lat)*np.sin(lon)), axis=-1)
    surface(g, name, n*radius + center, 49, 97, mat, n.reshape(-1, 3))


def cylinder(g, name, radius, z0, z1, mat, angle=(0, 2*np.pi), center=(0, 0)):
    theta = np.linspace(*angle, 129)
    zz, aa = np.meshgrid([z0, z1], theta, indexing='ij')
    n = np.stack((np.cos(aa), np.sin(aa), np.zeros_like(aa)), axis=-1)
    p = n*radius
    p[..., 0] += center[0]; p[..., 1] += center[1]; p[..., 2] = zz
    # grid_indices has the opposite winding to the cylindrical outward normals.
    f = grid_indices(2, len(theta)).reshape(-1, 3)[:, ::-1]
    mesh(g, name, p.reshape(-1, 3), f, mat, n.reshape(-1, 3))


def annulus(g, name, inner, outer, z, mat, angle=(0, 2*np.pi), normal=1):
    rr, aa = np.meshgrid([inner, outer], np.linspace(*angle, 129), indexing='ij')
    p = np.stack((rr*np.cos(aa), rr*np.sin(aa), np.full_like(rr, z)), axis=-1)
    f = grid_indices(*rr.shape).reshape(-1, 3)[:, ::1 if normal > 0 else -1]
    mesh(g, name, p.reshape(-1, 3), f, mat, np.tile([0, 0, normal], (p.size//3, 1)))


def quad(g, name, points, mat):
    p = np.array(points, float)
    candidates = np.array([np.cross(p[1]-p[0], p[2]-p[0]), np.cross(p[2]-p[0], p[3]-p[0])])
    normal = candidates[np.argmax(np.linalg.norm(candidates, axis=1))]
    normal /= max(np.linalg.norm(normal), 1e-30)
    mesh(g, name, points, [(0, 1, 2), (0, 2, 3)], mat, np.tile(normal, (4, 1)))


def box(g, name, lo, hi, mat):
    lo, hi = np.array(lo), np.array(hi)
    for axis in range(3):
        other = [x for x in range(3) if x != axis]
        for side in [0, 1]:
            p = np.tile(lo, (4, 1))
            p[:, axis] = hi[axis] if side else lo[axis]
            for k, (a, b) in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
                p[k, other[0]] = hi[other[0]] if a else lo[other[0]]
                p[k, other[1]] = hi[other[1]] if b else lo[other[1]]
            outward = np.zeros(3); outward[axis] = 1 if side else -1
            if np.dot(np.cross(p[1]-p[0], p[2]-p[0]), outward) < 0:
                p = p[::-1]
            quad(g, name, p, mat)


def rod(g, name, a, b, radius, mat, sides=8):
    a, b = np.asarray(a, float), np.asarray(b, float)
    axis = b-a; axis /= np.linalg.norm(axis)
    side = np.cross(axis, [0, 0, 1] if abs(axis[2]) < .9 else [0, 1, 0])
    side /= np.linalg.norm(side); up = np.cross(axis, side)
    angles = np.arange(sides+1)*2*np.pi/sides
    n = side[None, :]*np.cos(angles)[:, None] + up[None, :]*np.sin(angles)[:, None]
    p = np.stack([a+n*radius, b+n*radius])
    mesh(g, name, p.reshape(-1, 3), grid_indices(2, sides+1).reshape(-1, 3)[:, ::-1],
         mat, np.tile(n, (2, 1)))


def ring(g, name, radius, mat, axis=2, thickness=None):
    t = np.linspace(0, 2*np.pi, 193)
    a = np.linspace(0, 2*np.pi, 7)
    r = radius + (thickness or radius*.004)*np.cos(a)[None, :]
    p = np.stack((r*np.cos(t)[:, None], r*np.sin(t)[:, None],
                  np.broadcast_to((thickness or radius*.004)*np.sin(a), r.shape if r.shape[0] > 1 else (len(t), len(a)))), axis=-1)
    if axis == 0: p = p[..., [2, 0, 1]]
    if axis == 1: p = p[..., [0, 2, 1]]
    surface(g, name, p, len(t), len(a), mat)


def ruler(g, a, b, mat, width, label, offset):
    a, b = np.array(a, float), np.array(b, float)
    rod(g, 'Measurement guide', a, b, width, mat)
    tangent = b-a; tangent /= np.linalg.norm(tangent)
    tick = np.array([-tangent[1], tangent[0], 0])*width*5
    for endpoint in [a, b]:
        rod(g, 'Measurement endpoint', endpoint-tick, endpoint+tick, width, mat)
    g.label_node('Measurement', (a+b)/2 + offset, label)


def helium():
    g = GLB('Universe Scales: helium-4 rms charge-diameter guide and schematic nucleons')
    proton = g.material('Two protons; illustrative red', (.82, .14, .075, 1), rough=.42)
    neutron = g.material('Two neutrons; illustrative blue', (.12, .42, .68, 1), rough=.48)
    guide = g.material('rms charge-radius guides', (.89, .70, .30, 1), rough=.8, emissive=(.16, .10, .025))
    # There is no experimentally observed tetrahedral packing of hard nucleon balls.
    # These four overlapping glyphs convey composition only.
    positions = np.array([[1, 1, 1], [-1, -1, 1], [1, -1, -1], [-1, 1, -1]])*.43
    for i, p in enumerate(positions):
        sphere(g, 'Proton glyph' if i < 2 else 'Neutron glyph', .78, p, proton if i < 2 else neutron)
    radius = 1.6785  # CODATA 2022, matching the existing item definition.
    for axis in range(3): ring(g, 'rms guide, not a surface', radius, guide, axis)
    g.label_node('Charge diameter', [0, -radius*1.12, 0], '3.357 fm')
    save(g, 'helium-charge', 'Helium Nucleus Charge Diameter', 2*radius, 'femtometres', NIST,
         'Helium-4 measurement diagram. Three thin guides mark twice the CODATA 2022 rms charge radius '
         '1.6785(21) fm: 3.357 fm. An rms radius is a moment of the charge distribution, not a hard outer '
         'boundary. Four overlapping colored nucleon glyphs show two protons and two neutrons; their '
         'radii, positions, colors and static tetrahedral arrangement are authored symbols, not measured '
         'nucleon surfaces or a nuclear-structure reconstruction. No electron cloud is shown.',
         dict(rms_charge_radius_fm=radius, rms_uncertainty_fm=.0021, diameter_fm=2*radius,
              nucleon_glyphs='schematic only'), dict(yaw=-17, pitch=12, layout_width_factor=1.02),
         'measurement_diagram')


def nanotube():
    g = GLB('Universe Scales: local nanotube gate-electrode fragment')
    carbon = g.material('Illustrative graphite-gray nanotube', (.19, .23, .28, 1), rough=.38, metal=.24)
    rim = g.material('Cut-edge annotation', (.24, .72, .78, 1), rough=.6, emissive=(.015, .07, .08))
    cylinder(g, 'Single-wall nanotube envelope; open authored ends', .5, -.35, .35, carbon)
    # Thin cyan cut rings distinguish the open tube from a solid rod. Their width is annotation.
    for z in [-.35, .35]:
        annulus(g, 'Cut rim guide', .496, .5, z, rim, normal=1 if z > 0 else -1)
    g.label_node('Gate dimension', [0, -.62, .35], '1 nm gate')
    save(g, 'nanotube-gate', 'One-Nanometer Transistor Gate', 1, 'nanometres', CNT,
         'Local detail of the approximately 1 nm-diameter single-walled carbon nanotube used as the '
         'physical gate electrode in Desai et al. (Science, 2016). The tube diameter in the current-flow '
         'direction is the gate length; it is not the length along the nanotube. The open, zero-thickness '
         'cylindrical envelope is an authored illustration, not an atomistic chirality reconstruction. '
         'Its 0.7 nm axial crop and cyan cut-edge guides are display choices. The actual device has a '
         'MoS2 channel and ZrO2 dielectric; those larger layers and the source/drain contacts are omitted '
         'so a 1 nm gate is not presented as a many-nanometre whole transistor. This is a gate detail, '
         'not a complete device cross-section. The larger local stack section is supplied separately '
         'at handoff/micro3d/transistor-stack-context.glb, with the published 5.8 nm ZrO2 thickness '
         'and 1.3 nm bilayer MoS2 thickness. That companion crops into the 50 nm SiO2 substrate '
         'and omits distant source/drain contacts; it is not registered against a 1 nm quantity.',
         dict(physical_gate_length_nm=1, axis_crop_nm=.7, boundary='zero-thickness envelope',
              companion_zirconia_thickness_nm=5.8, companion_mos2_thickness_nm=1.3,
              companion_source='https://nano.eecs.berkeley.edu/publications/Science_2016_1nm%20MoS2%20FETs.pdf'),
         dict(yaw=-24, pitch=23, environment=.35, layout_width_factor=1.2))


def transistor_context():
    """Unregistered, true-unit local cross-section: too large for the 1 nm item."""
    g = GLB('Universe Scales: local 2016 SWCNT-gated MoS2 device stack section; native nm')
    oxide = g.material('Zirconium dioxide; illustrative cyan', (.32, .66, .70, 1), rough=.72)
    mos = g.material('Bilayer molybdenum disulfide; illustrative gold', (.88, .62, .18, 1), rough=.52)
    sio = g.material('Cropped silicon dioxide substrate', (.35, .39, .47, 1), rough=.85)
    cnt = g.material('Nanotube gate', (.10, .14, .20, 1), rough=.4)
    guide = g.material('Measurement guides', (.87, .91, .92, 1), rough=.8)
    # Cross-sectional dielectric faces contain a true 1 nm circular gate opening.
    # No copied microscopy image, inferred atomic bonds, or fabricated contact positions.
    xs = np.r_[-6, np.linspace(-.5, .5, 97), 6]
    for z in [-.6, .6]:
        for a, b in zip(xs, xs[1:]):
            if a >= -.5 and b <= .5:
                da, db = math.sqrt(max(0, .25-a*a)), math.sqrt(max(0, .25-b*b))
                for low, high_a, high_b in [(True, .5-da, .5-db), (False, .5+da, .5+db)]:
                    points = [[a, 0 if low else high_a, z], [b, 0 if low else high_b, z],
                              [b, high_b if low else 5.8, z], [a, high_a if low else 5.8, z]]
                    quad(g, 'ZrO2 cross-section', points if z > 0 else points[::-1], oxide)
            else:
                points = [[a, 0, z], [b, 0, z], [b, 5.8, z], [a, 5.8, z]]
                quad(g, 'ZrO2 cross-section', points if z > 0 else points[::-1], oxide)
    for y in [0, 5.8]:
        quad(g, 'Dielectric boundary', [[-6, y, -.6], [6, y, -.6], [6, y, .6], [-6, y, .6]], oxide)
    for x in [-6, 6]:
        quad(g, 'Dielectric display cut', [[x, 0, -.6], [x, 5.8, -.6], [x, 5.8, .6], [x, 0, .6]], oxide)
    cylinder(g, '1 nm SWCNT gate', .5, -.6, .6, cnt, center=(0, .5))
    # CNT is a zero-thickness envelope; this circular end is a section marker, not a solid carbon rod.
    theta = np.linspace(0, 2*np.pi, 97)
    for a, b in zip(theta, theta[1:]):
        rod(g, 'Gate section marker', [.5*math.cos(a), .5+.5*math.sin(a), .602],
            [.5*math.cos(b), .5+.5*math.sin(b), .602], .008, guide, 4)
    box(g, 'Bilayer MoS2, 1.3 nm nominal thickness', [-6, 5.8, -.6], [6, 7.1, .6], mos)
    box(g, 'Authored 2 nm crop into the actual 50 nm SiO2 substrate', [-6, -2, -.6], [6, 0, .6], sio)
    ruler(g, [7.2, 0, .6], [7.2, 5.8, .6], guide, .017, '5.8 nm', [1.1, 0, 0])
    g.label_node('Channel name', [0, 7.8, .6], 'MoS2')
    g.label_node('Oxide name', [1.5, 3.3, .6], 'ZrO2')
    g.label_node('Substrate name', [0, -1, .61], 'SiO2')
    g.label_node('Gate name', [0, 1.4, .61], 'Gate')
    g.write(HANDOFF/'transistor-stack-context.glb')


def track(kind):
    blu = kind == 'blu-ray'
    pitch, groove, depth = (320., 100., 20.) if blu else (740., 300., 120.)
    g = GLB('Universe Scales: local optical-disc recording-groove surface')
    land = g.material('Illustrative silver-blue recording surface', (.43, .59, .71, 1), rough=.38, metal=.42)
    floor = g.material('Groove floor; same physical surface', (.27, .42, .55, 1), rough=.45, metal=.35)
    guide = g.material('Track-center guides', (.93, .73, .32, 1), rough=.8, emissive=(.12, .07, .02))
    # A single-pitch crop shows two partial neighboring grooves. Finite edge slopes are authored.
    xmin, xmax = -.6*pitch, .6*pitch
    breaks = {xmin, xmax}
    for center in [-pitch/2, pitch/2]:
        for offset in [-groove/2, -groove*.38, groove*.38, groove/2]:
            if xmin < center+offset < xmax: breaks.add(center+offset)
    xs = sorted(breaks)
    def height(x):
        d = min(abs(x-pitch/2), abs(x+pitch/2))
        return -depth*np.clip((groove/2-d)/(.12*groove), 0, 1)
    for i, (a, b) in enumerate(zip(xs, xs[1:])):
        za, zb = height(a), height(b)
        quad(g, f'Groove surface strip {i}', [(a, -.47*pitch, za), (b, -.47*pitch, zb),
                                             (b, .47*pitch, zb), (a, .47*pitch, za)],
             floor if za == zb == -depth else land)
    # Centerline bracket is an annotation, separated below the physical surface crop.
    ruler(g, [-pitch/2, -.55*pitch, depth*.08], [pitch/2, -.55*pitch, depth*.08],
          guide, .002*pitch, f'{int(pitch)} nm', [0, -.085*pitch, 0])
    name = 'Blu-ray Track Pitch' if blu else 'DVD Track Pitch'
    save(g, kind+'-grooves', name, pitch, 'nanometres', BD if blu else DVD,
         f'One-pitch cropped surface of a {"BD-R" if blu else "DVD-R"} recording-groove pattern. '
         f'Adjacent groove centers are {pitch:g} nm apart. The {groove:g} nm representative groove '
         f'width and {depth:g} nm depth follow the optical-media substrate measurements in Wu et al. '
         '(Microsystems & Nanoengineering, 2021); the pitch follows '
         f'{"the BDA nominal value and Hagemeier et al. (2019)" if blu else "ECMA-267 nominal DVD track spacing"}. '
         'The measured widths/depths are representative of that study, not universal format requirements. '
         'Straight local grooves approximate the disc spiral at this tiny crop. Edge slopes, reflectance '
         'and colors are authored; no vertical exaggeration is applied. The crop cuts through the outer '
         'parts of both grooves. This is a recordable-disc groove surface, not a fabricated BD-ROM/DVD-ROM '
         'pit sequence. Disc bulk, coatings and the full spiral are omitted. The golden bracket joins '
         'track centers, not groove edges.',
         dict(track_pitch_nm=pitch, representative_groove_width_nm=groove, groove_depth_nm=depth,
              surface_crop_width_nm=1.2*pitch, source_dimensions_url=GROOVES,
              edge_profile='authored trapezoid, equal XYZ units'),
         dict(yaw=-12, pitch=-22, environment=.35, layout_width_factor=1.24))


def silk():
    g = GLB('Universe Scales: representative smooth spider dragline silk segment')
    silk_mat = g.material('Illustrative pale silk', (.88, .80, .56, 1), rough=.34, metal=.06)
    cut = g.material('Authored flat segment cuts', (.67, .63, .45, 1), rough=.74)
    cylinder(g, 'Smooth filament exterior', 1.5, -.9, .9, silk_mat)
    for z in [-.9, .9]: annulus(g, 'Display cut', 0, 1.5, z, cut, normal=1 if z > 0 else -1)
    g.label_node('Fiber diameter', [0, -1.8, .9], '3 µm')
    save(g, 'spider-silk', 'Spider Silk Fiber', 3, 'micrometres', SILK,
         'Original smooth, circular-cylinder illustration of a representative 3 µm spider dragline '
         'filament, within the 2–5 µm Nephila clavata dragline range reported by the 1995 mechanical '
         'study. Silk dimensions vary by species, gland and spinning conditions. The paper reports '
         'a featureless surface; no fabricated scales, braided strands, roughness or glue droplets '
         'are added. The 1.8 µm displayed segment is an arbitrary crop, not a claim about thread '
         'length or a severed natural specimen. Flat cut faces and pale-gold material are illustrative. '
         'No molecular or measured internal cross-sectional reconstruction is claimed.',
         dict(representative_diameter_um=3, published_diameter_range_um=[2, 5], authored_crop_length_um=1.8),
         dict(yaw=-28, pitch=20, environment=.25, layout_width_factor=1.25))


def fiber():
    g = GLB('Universe Scales: cutaway telecommunications fiber cross-section')
    glass = g.material('Glass cladding; illustrative cyan', (.24, .60, .70, 1), rough=.42)
    face = g.material('Cut glass face', (.53, .79, .83, 1), rough=.68)
    core = g.material('8.2 micrometre core; illustrative blue', (.12, .28, .73, 1), rough=.42, emissive=(.015, .025, .10))
    coating = g.material('Protective polymer coating; illustrative amber', (.90, .42, .10, 1), rough=.57)
    # Remove one quarter of the glass shell to expose the narrow core down the segment.
    sector = (np.pi/2, 2*np.pi)
    cylinder(g, '125 micrometre cladding exterior', 62.5, -22.5, 22.5, glass, sector)
    for z in [-22.5, 22.5]:
        annulus(g, 'Cladding cut face', 4.1, 62.5, z, face, sector, normal=1 if z > 0 else -1)
    for theta in sector:
        direction = np.array([math.cos(theta), math.sin(theta)])
        a, b = direction*4.1, direction*62.5
        quad(g, 'Longitudinal cladding cut', [[*a, -22.5], [*b, -22.5], [*b, 22.5], [*a, 22.5]], face)
    cylinder(g, 'Core', 4.1, -22.5, 22.5, core)
    for z in [-22.5, 22.5]: annulus(g, 'Core end', 0, 4.1, z, core, normal=1 if z > 0 else -1)
    # Only a small, true-radius sector remains; never shrink a full 242 µm coating to 125 µm.
    coat_sector = tuple(np.radians([130, 140]))
    for radius in [62.5, 121]:
        cylinder(g, 'Remaining polymer coating sector', radius, -22.5, 0, coating, coat_sector)
    for z in [-22.5, 0]:
        annulus(g, 'Polymer cross-section', 62.5, 121, z, coating, coat_sector, normal=1 if z == 0 else -1)
    for theta in coat_sector:
        a = [62.5*math.cos(theta), 62.5*math.sin(theta)]
        b = [121*math.cos(theta), 121*math.sin(theta)]
        quad(g, 'Coating sector cut', [[*a, -22.5], [*b, -22.5], [*b, 0], [*a, 0]], coating)
    g.label_node('Core label', [10, 6, 25], 'Core')
    g.label_node('Coating label', [-89, 103, 0], 'Coating')
    g.label_node('Glass dimension', [0, -76, 22.5], '125 µm glass')
    save(g, 'optical-fiber', 'Optical Fiber Cladding', 125, 'micrometres', FIBER,
         'Original cross-section of a Corning SMF-28 Ultra type fiber: 8.2 µm nominal core diameter, '
         '125 µm glass cladding diameter and 242 µm coating diameter. The core is not the 9.2 µm '
         'mode-field diameter. A quarter of the cladding and most of the coating are cut away. '
         'The surviving 10-degree coating sector preserves the full 121 µm outer radius; its thickness '
         'is not compressed to fit the glass diameter. Segment length (45 µm), cut orientations and '
         'opaque contrasting colors are authored presentation choices. No refractive-index profile, '
         'internal polymer-layer subdivision, propagating light ray or material transparency is simulated. '
         'The listed quantity measures glass diameter only.',
         dict(core_diameter_um=8.2, cladding_diameter_um=125, coating_diameter_um=242,
              displayed_coating_angles_deg=[130, 140], axial_crop_um=45),
         dict(yaw=-6, pitch=4, layout_width_factor=1.29))


def kola():
    g = GLB('Universe Scales: Kola SG-3 nominal vertical-depth section')
    rock = g.material('Schematic crust section; no surveyed strata', (.32, .35, .39, 1), rough=.94)
    surface_mat = g.material('Arbitrary ground-section cut', (.38, .43, .39, 1), rough=.92)
    bore = g.material('Bore depth marker', (.95, .54, .13, 1), rough=.7, emissive=(.18, .055, .005))
    guide = g.material('Depth ruler', (.72, .80, .85, 1), rough=.8)
    d = 12262.
    box(g, 'Crust display window', [-3400, -d, -1800], [3400, 0, 0], rock)
    quad(g, 'Local level datum', [(-3400, 0, -1800), (3400, 0, -1800), (3400, 0, 0), (-3400, 0, 0)], surface_mat)
    # The visible orange stroke is a depth annotation, NOT a many-metre drill hole.
    rod(g, 'Depth annotation; not shaft width', [0, -d, 1], [0, 0, 1], d*.0016, bore)
    ruler(g, [4200, -d, 0], [4200, 0, 0], guide, d*.0018, '12,262 m', [900, 0, 0])
    g.label_node('Ground label', [-2200, 300, 0], 'Surface')
    g.label_node('Bore label', [0, -d-430, 0], 'SG-3')
    save(g, 'kola-depth', 'Kola Superdeep Borehole', d, 'metres', KOLA,
         'Kola SG-3 depth diagram with equal horizontal and vertical metres. The vertical datum-to-bottom '
         'marker spans the published 12,262 m depth. The orange stroke is a visible measurement annotation, '
         'not the physical bore diameter; no enlarged tunnel is modeled. The gray crust block is an '
         'arbitrarily cropped, uniform context section, not measured topography, lithology, a crustal '
         'thickness estimate or an assertion that the Moho lies at its bottom. The straight marker '
         'represents vertical depth, not the measured, deviating trajectory or branched drilling history. '
         'No invented subsurface fault surfaces are shown.',
         dict(vertical_depth_m=d, trajectory='not reconstructed', section_window='authored context crop',
              orange_stroke='depth annotation, not bore diameter'),
         dict(yaw=-14, pitch=7, layout_width_factor=.9), 'measurement_diagram')


def karman():
    g = GLB('Universe Scales: local Earth-to-Karman altitude section')
    earth = g.material('Spherical sea-level datum; illustrative blue', (.085, .32, .48, 1), rough=.88)
    border = g.material('100 km altitude guide; not a physical shell', (.21, .70, .89, 1), rough=.7,
                        emissive=(.025, .12, .18))
    guide = g.material('Altitude ruler', (.94, .73, .32, 1), rough=.8, emissive=(.12, .07, .02))
    radius, height, half_width, half_depth = 6371., 100., 34., 9.
    x, z = np.meshgrid(np.linspace(-half_width, half_width, 65), np.linspace(-half_depth, half_depth, 9), indexing='ij')
    for altitude, material, name in [(0, earth, 'Local spherical sea-level surface'),
                                     (height, border, 'Conventional 100 km altitude guide')]:
        r = radius + altitude
        y = np.sqrt(r*r-x*x-z*z)-radius
        p = np.stack((x, y, z), axis=-1)
        surface(g, name, p, *x.shape, material)
    ruler(g, [0, 0, 11], [0, height, 11], guide, .16, '100 km', [13, 0, 0])
    g.label_node('Altitude label', [0, 106, 0], 'Kármán line')
    g.label_node('Datum label', [0, -6, 0], 'Sea level')
    save(g, 'karman-line', 'Karman Line', height, 'kilometres', KARMAN,
         'Local geometric altitude section: 100 km from sea level to the FAI Kármán-line convention, '
         'using equal horizontal and vertical kilometres. Two small spherical patches use the 6,371 km '
         'mean Earth radius used in PREM and radii 6,371 and 6,471 km. The upper cyan patch and gold '
         'ruler are measurement guides, not physical surfaces, a sharp atmosphere edge or a shell of '
         'air. The 68 by 18 km local window is an authored crop. No exponential-density scale, abrupt '
         'sky-color boundary, launch trajectory, topography or horizontally compressed globe is invented. '
         'The full Earth is omitted because its diameter is over 127 times the listed altitude.',
         dict(conventional_altitude_km=height, mean_earth_radius_km=radius, radius_source=PREM,
              local_crop_km=[68, 18], vertical_exaggeration=1),
         dict(yaw=-13, pitch=14, layout_width_factor=.9), 'measurement_diagram')


def earth_core():
    """A core detail on stage, plus a separately reviewable full-Earth companion."""
    def materials(g):
        return [g.material('Solid inner core; illustrative gold', (.93, .66, .23, 1), rough=.52, metal=.12),
                g.material('Liquid outer core; illustrative orange', (.82, .27, .065, 1), rough=.72),
                g.material('Mantle; illustrative brick red', (.48, .16, .10, 1), rough=.88),
                g.material('Earth surface; schematic blue', (.11, .38, .51, 1), rough=.88)]
    radius = 1221.5
    g = GLB('Universe Scales: PREM inner-core detail')
    gold = g.material('Solid inner core; illustrative gold', (.93, .66, .23, 1), rough=.52, metal=.12)
    sphere(g, 'PREM solid inner core', radius, [0, 0, 0], gold)
    g.label_node('Core diameter', [0, -1390, 0], '2,443 km')
    save(g, 'inner-core', "Earth's Inner Core", 2442, 'kilometres', PREM,
         'PREM-based spherical inner-core detail, radius 1,221.5 km and diameter 2,443 km. The catalog '
         'currently rounds the inner-core radius to 1,221 km and lists 2,442 km; the resulting difference '
         'is 0.041%. Gold color and surface appearance are illustrative, not an image of the core. '
         'The solid inner core is not surrounded by invented visible magma texture. A separate '
         'unregistered full-Earth cutaway (handoff/micro3d/earth-prem-context.glb) preserves the PREM '
         '1,221.5 km inner-core, 3,480 km outer-core and 6,371 km Earth radii. The full Earth is omitted '
         'from this on-stage detail because it would render at 5.22 times the listed core diameter.',
         dict(inner_core_radius_km=radius, inner_core_diameter_km=2443,
              catalog_reference_diameter_km=2442, outer_core_radius_km=3480, earth_radius_km=6371),
         dict(yaw=-20, pitch=10, layout_width_factor=1.01))
    # Spherical shell exteriors and radial faces; no fictitious crust thickness is introduced.
    full = GLB('Universe Scales: PREM major-boundary context cutaway; not explorer-calibrated')
    mats = materials(full)
    sphere(full, 'Solid inner core', radius, [0, 0, 0], mats[0])
    for inner, outer, mat in [(radius, 3480, mats[1]), (3480, 6371, mats[2])]:
        sphere(full, 'Outer core' if inner == radius else 'Mantle and surface', outer,
               [0, 0, 0], mat if inner == radius else mats[3], (np.pi/2, 2*np.pi))
        # Cut planes at longitudes 0 and 90 degrees, each a semicircular annulus.
        r, a = np.meshgrid([inner, outer], np.linspace(-np.pi/2, np.pi/2, 97), indexing='ij')
        for longitude in [0, np.pi/2]:
            p = np.stack((r*np.cos(a)*math.cos(longitude), r*np.sin(a),
                          r*np.cos(a)*math.sin(longitude)), axis=-1)
            surface(full, 'Radial layer section', p, *r.shape, mat)
    full.write(HANDOFF/'earth-prem-context.glb')


def paramecium():
    """Observed morphology interpreted as an original surface, explicitly not tomography."""
    source = 'https://realmicrolife.com/paramecium-caudatum/'
    g = GLB('Universe Scales: original Paramecium caudatum morphology illustration')
    cell = g.material('Illustrative teal pellicle', (.22, .62, .58, 1), rough=.68)
    hair = g.material('Illustrative cilia', (.56, .84, .77, 1), rough=.83)
    def point(phi, theta):
        # The overall 3D surface and oral depression are authored from observed morphology.
        x = -125*np.cos(phi)
        profile = np.sin(phi)**(.8+.4*(x/250+.5))*(1-.12*x/125)
        delta = np.arctan2(np.sin(theta-.7), np.cos(theta-.7))
        oral = .38*np.exp(-(delta/.19)**2-((x+18)/44)**4)
        return np.stack((x+np.zeros_like(theta), 34*profile*np.cos(theta)*(1-oral),
                         25*profile*np.sin(theta)*(1-oral)), axis=-1)
    phi, theta = np.meshgrid(np.linspace(0, np.pi, 49), np.linspace(0, 2*np.pi, 129), indexing='ij')
    p = point(phi, theta)
    n = np.cross(np.gradient(p, axis=1), np.gradient(p, axis=0))
    n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-30)
    n[0] = [-1, 0, 0]; n[-1] = [1, 0, 0]
    mesh(g, 'Slipper-shaped pellicle with oral groove', p.reshape(-1, 3),
         grid_indices(*phi.shape).reshape(-1, 3)[:, ::-1], cell, n.reshape(-1, 3))
    # Paired cilia in longitudinal rows: no stochastic terrain or organelle filler.
    # Small triangular tubes share one mesh/material, avoiding thousands of draw calls.
    vertices, indices, normals = [], [], []
    for row in range(80):
        angle = row*2*np.pi/80
        for phase in np.linspace(.1, np.pi-.16, 25) + (row % 2)*.045:
            x = -125*np.cos(phase)
            if abs(angle-.7) < .17 and -65 < x < 25: continue
            for pair in [-1, 1]:
                start = point(phase+pair*.0025, angle)
                n = np.array([-np.cos(phase)/125, np.sin(phase)*np.cos(angle)/34,
                              np.sin(phase)*np.sin(angle)/25])
                n /= np.linalg.norm(n)
                length = 8 if phase < np.pi-.3 else 14
                bend = np.array([1., 0, 0]); bend -= n*np.dot(n, bend)
                bend /= max(np.linalg.norm(bend), 1e-10)
                centers = np.array([start, start+n*length*.65+bend*length*.12,
                                    start+n*length*.87+bend*length*.4])
                side = np.cross(n, [0, 0, 1] if abs(n[2]) < .9 else [0, 1, 0]); side /= np.linalg.norm(side)
                up = np.cross(n, side)
                t = np.arange(4)*2*np.pi/3
                radial = side[None, :]*np.cos(t)[:, None]+up[None, :]*np.sin(t)[:, None]
                tube = centers[:, None, :]+np.array([.12, .10, .035])[:, None, None]*radial[None, :, :]
                offset = len(vertices)
                vertices.extend(tube.reshape(-1, 3)); normals.extend(np.tile(radial, (3, 1)))
                indices.extend(grid_indices(3, 4).reshape(-1, 3)[:, ::-1]+offset)
    mesh(g, 'Paired cilia; static authored beat pose', vertices, indices, hair, normals)
    g.label_node('Oral groove name', [-24, 34, 29], 'Oral groove')
    g.label_node('Cilia name', [73, -43, 18], 'Cilia')
    save(g, 'paramecium', 'Paramecium', 250, 'micrometres', source,
         'Original external morphology illustration of Paramecium caudatum, using a representative '
         '250 µm cell-body length. Martin Kreutz’s microscopy observations document 170–300 µm cells, '
         'a rounded anterior, narrower posterior, an anteriorly widening oral groove, 80–120 longitudinal '
         'rows of paired cilia, and a tuft of 10–20 µm caudal cilia. This diagram uses 80 rows; ordinary '
         '8 µm cilia and 14 µm caudal cilia, their static bend, spacing, diameter, the body width/depth '
         'and precise oral-groove profile are authored simplifications. Cilia extend beyond the calibrated '
         '250 µm body. The cell is opaque for small-scale legibility; internal organelles, trichocysts '
         'and refractive contents are omitted. No source photograph is copied, and this is not a scan, '
         'measured specimen surface or reconstructed 3D microscopy volume.',
         dict(representative_body_length_um=250, observed_length_range_um=[170, 300],
              observed_ciliary_row_range=[80, 120], illustrated_ciliary_rows=80,
              observed_caudal_cilia_um=[10, 20], geometry='original morphology illustration'),
         dict(yaw=-12, pitch=-15, roll=3, layout_width_factor=1.15))


if __name__ == '__main__':
    helium()
    nanotube()
    transistor_context()
    track('blu-ray')
    track('dvd')
    silk()
    fiber()
    kola()
    karman()
    earth_core()
    paramecium()
