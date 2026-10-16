#!/usr/bin/env python3
"""Offline, physically calibrated second-round space models.

Run prepare_space3d2_sources.py only to refresh the pinned inputs. This builder
does not fetch data, change datasets, or depend on browser/GPU tools.
"""
import argparse
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

from build_space3d_diagrams import sphere
from build_space3d_models import mesh_diameter
from fetch_model_assets import inspect_glb, read_glb, sha, view_bytes, write_json
from geo_glb_common import GLB, grid_indices
from register_model import register
from render_glb_preview import accessor

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT/'content/visualizations/models'
SOURCES = MODELS/'sources/space3d2'
HANDOFF = ROOT/'handoff/space3d2'
AU_M = 149597870700  # Exact IAU astronomical unit; JPL astrodynamic parameters.
SOLAR_RADIUS_KM = 695700  # IAU 2015 Resolution B3 nominal conversion.
SNAPSHOT_JD = 2461329.5  # 2026-10-16 00:00 TDB label; two-body display epoch.


def source_record(file):
    records = json.loads((SOURCES/'manifest.json').read_text())['sources']
    record = next(r for r in records if r['file'] == file)
    if sha((SOURCES/file).read_bytes()) != record['sha256']:
        raise ValueError(f'Changed source: {file}')
    return record


def base_entry(model_id, item, representation, note, source, author='Universe Scales'):
    return {'id': model_id, 'matches': {'length': [item]}, 'geometry': 'mesh',
            'representation': representation, 'note': note, 'source': source, 'author': author,
            'reference': f'content/visualizations/models/sources/{model_id}.md',
            'license': 'CC0-1.0', 'license_url': 'https://creativecommons.org/publicdomain/zero/1.0/',
            'license_files': ['licenses/CC0-1.0.txt'],
            'volume_semantics': 'not_a_volume_measurement', 'closed_volume_checked': False,
            'presentation': {'roughness': 1, 'metalness': 0}, 'processing': {}}


def agency(entry):
    entry.update(license='U.S. public-domain NASA media/data; credit the named science teams',
                 license_url='https://www.nasa.gov/nasa-brand-center/images-and-media/',
                 license_files=['licenses/nasa-media-guidelines.html'])
    return entry


def attach_source(entry, file):
    record = source_record(file)
    entry.update(download_url=record['url'], source_sha256=record['source_sha256'], source_bytes=record['source_bytes'])
    entry['processing']['pinned_input'] = str((SOURCES/file).relative_to(ROOT))
    entry['processing']['pinned_input_sha256'] = record['sha256']


def save(glb, entry, register_entry=True):
    path = MODELS/(entry['id']+'.glb')
    glb.write(path)
    entry.update(src=str(path.relative_to(ROOT)), **inspect_glb(path.read_bytes()))
    if entry['bytes'] > 3_000_000:
        raise ValueError('Asset budget exceeded')
    HANDOFF.mkdir(parents=True, exist_ok=True)
    entry_path = HANDOFF/(entry['id']+'.entry.json')
    write_json(entry_path, entry)
    if register_entry:
        register(entry_path, path, 'length')
    else:
        print(f"Prepared {entry['id']} (pending a distinct moon dataset item)")
    return entry


def normals(points, faces):
    n = np.zeros_like(points)
    cross = np.cross(points[faces[:, 1]]-points[faces[:, 0]], points[faces[:, 2]]-points[faces[:, 0]])
    for i in range(3):
        np.add.at(n, faces[:, i], cross)
    length = np.linalg.norm(n, axis=1)
    if np.any(length < 1e-20):
        raise ValueError('Source has unreferenced/degenerate vertices')
    return n/length[:, None]


def build_shape(body, item, reference_km=None, pose=None, pending=False):
    data = np.load(SOURCES/(body+'.npz'))
    # Body-fixed Z north becomes display +Y, preserving handedness.
    points = data['vertices'][:, [0, 2, 1]] * [1, 1, -1]
    faces = data['faces'].astype(np.int32)
    # The Ryugu OBJ contains unreferenced patch-border vertices. Remove those
    # only; all referenced coordinates and original faces remain unchanged.
    used, inverse = np.unique(faces.ravel(), return_inverse=True)
    points = points[used]
    faces = inverse.reshape(-1, 3)
    volume = np.einsum('ij,ij->i', points[faces[:, 0]],
                       np.cross(points[faces[:, 1]], points[faces[:, 2]])).sum()/6
    if volume < 0:
        faces = faces[:, [0, 2, 1]]
    glb = GLB('Universe Scales measured spacecraft shape')
    material = glb.material('Neutral illustrative albedo; source topography', color=(.50, .49, .47, 1), double_sided=False)
    glb.mesh_node(body.capitalize(), [glb.primitive(points, faces.ravel(), material, normals=normals(points, faces))])
    # Require actual closed topology before using equivalent-volume calibration.
    from geo_glb_common import pack_glb
    diameter = mesh_diameter(pack_glb(glb.doc, glb.bin))
    model_id = {'ryugu': 'jaxa-ryugu-shape', 'hyperion': 'cassini-hyperion-shape',
                'dimorphos': 'dart-dimorphos-preimpact'}[body]
    source = {'ryugu': 'https://data.darts.isas.jaxa.jp/pub/hayabusa2/paper/Watanabe_2019/README.html',
              'hyperion': 'https://data.nasa.gov/dataset/saturn-small-moon-shape-models-v1-0',
              'dimorphos': 'https://pds.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=urn:nasa:pds:dart_shapemodel:data_derived_dimorphos_model_v004&version=1.0'}[body]
    author = {'ryugu': 'ISAS/JAXA; Watanabe et al. (2019), Hayabusa2 shape-model team',
              'hyperion': 'Peter C. Thomas; NASA/JPL/Cassini ISS; NASA PDS Small Bodies Node',
              'dimorphos': 'NASA/Johns Hopkins APL DART team; NASA PDS/NAIF'}[body]
    note = {'ryugu': 'Hayabusa2 measured SfM shape, 49,152 original triangles. The equatorial ridge and resolved relief are from spacecraft data; gray albedo is authored, not a surface photograph. Catalog mean diameter calibrates the closed mesh equivalent-volume diameter. Body-fixed north is up; the inspection pose is authored.',
            'hyperion': 'The Cassini/Thomas 30k-plate measured shape of Saturn’s moon Hyperion, not the redwood tree. Craters and major relief are from the archived shape, not procedural noise. Neutral gray is an authored albedo; unresolved small crater detail is absent. The catalog mean diameter calibrates the equivalent-volume diameter; an oblique pose foreshortens its long axis.',
            'dimorphos': 'The DART final pre-impact global SPC shape v004, sampled from NASA NAIF’s 1.940 m DSK. This is the shape before 26 September 2022, not a prediction of the reshaped asteroid. Catalog 151 m equivalent-volume diameter calibrates the closed mesh. Neutral gray is authored; no impact crater or ejecta is invented.'}[body]
    entry = base_entry(model_id, item, 'spacecraft-derived-shape', note, source, author)
    if body == 'ryugu':
        entry.update(license='ISAS/JAXA open-data terms, compatible with CC BY 4.0',
                     license_url='https://www.isas.jaxa.jp/en/researchers/data-policy/',
                     license_files=['licenses/CC-BY-4.0.txt', 'licenses/space3d2-rights.md'])
    else:
        agency(entry)
        entry['license_files'].append('licenses/space3d2-rights.md')
    attach_source(entry, body+'.npz')
    entry['presentation'].update(reference_size=diameter if reference_km is None else reference_km, **(pose or {}))
    entry.update(closed_volume_checked=True, volume_semantics='equivalent_volume_diameter_calibration')
    entry['processing'].update(source_vertex_count=len(points), original_triangles=len(faces),
                               computed_equivalent_diameter_km=diameter,
                               operations=['Read pinned original coordinates in km without simplification',
                                           'Rotate body-fixed Z north to display Y, preserving handedness',
                                           'Compute area-weighted normals and check closed oriented topology'])
    return save(glb, entry, not pending)


def build_saturn(ringed):
    original = MODELS/'nasa-saturn-angular.glb'
    source = original.read_bytes()
    doc, binary = read_glb(source)
    glb = GLB('Universe Scales reuse of NASA VTAD Saturn')
    material_map = {}
    for index, m in enumerate(doc['materials'][:2 if ringed else 1]):
        image = doc['images'][doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']]
        texture = glb.texture(view_bytes(doc, binary, image['bufferView']), image['mimeType'])
        material_map[index] = glb.material(m.get('name', 'NASA texture'), texture=texture,
                                          blend=m.get('alphaMode') == 'BLEND', double_sided=False)
    for node in doc['nodes'][:3 if ringed else 1]:
        primitives = []
        for q in doc['meshes'][node['mesh']]['primitives']:
            a = q['attributes']
            primitives.append(glb.primitive(accessor(doc, binary, a['POSITION']),
                accessor(doc, binary, q['indices']).ravel(), material_map[q['material']],
                normals=accessor(doc, binary, a['NORMAL']), uvs=accessor(doc, binary, a['TEXCOORD_0'])))
        glb.mesh_node(node['name'], primitives)
    model_id = 'nasa-saturn-main-rings' if ringed else 'nasa-saturn-globe-length'
    item = "Saturn's Rings" if ringed else 'Saturn'
    note = ('NASA VTAD’s original Saturn globe and ring meshes, retaining their textures and relative proportions. Calibration uses the catalog 280,360 km span to the F ring in the source’s 120,536 km equatorial-diameter units. The model’s outer edge is within 1% of that span. This is a main-ring view; the diffuse E ring and individual particles are not represented.' if ringed else
            'NASA VTAD’s original oblate textured Saturn globe. The catalog mean diameter is calibrated against the source’s equatorial-diameter scale, preserving polar flattening. Rings are shown at their true relative scale under the separate Saturn’s Rings item; including them here would exceed the explorer’s 1.3× body-diameter extent rule. The texture is an illustrative global mosaic, not current weather.')
    entry = agency(base_entry(model_id, item, 'scientific-agency-illustration', note,
                 'https://science.nasa.gov/resource/saturn-3d-model/', 'NASA Visualization Technology Applications and Development (VTAD)'))
    # NASA source filename establishes a 1000-unit equatorial diameter = 120536 km.
    entry['presentation'].update(reference_size=(280360 if ringed else 116464)/120536*1000,
                                  pitch=28 if ringed else 8, roll=-18 if ringed else -12,
                                  layout_width_factor=1.2)
    entry['processing'].update(source_models=[{'id': 'nasa-saturn-angular', 'sha256': sha(source)}],
        source_equatorial_diameter_units=1000, source_equatorial_diameter_km=120536,
        operations=['Reuse NASA source geometry, UVs and already resized embedded textures',
                    'Retain globe and both original ring faces' if ringed else 'Extract globe; omit ring meshes and unused ring image'])
    return save(glb, entry)


def textured_patch(glb, name, image, xy, z, material_color=(1, 1, 1, 1)):
    output = io.BytesIO()
    image.thumbnail((1536, 1536), Image.Resampling.LANCZOS)
    image.save(output, 'JPEG', quality=93, subsampling=0)
    texture = glb.texture(output.getvalue(), 'image/jpeg')
    material = glb.material(name, color=material_color, texture=texture, double_sided=True)
    # A small emissive contribution retains the actual image's shadow structure.
    glb.doc['materials'][material]['emissiveTexture'] = {'index': texture}
    glb.doc['materials'][material]['emissiveFactor'] = [.25, .25, .25]
    points = np.column_stack((xy, z))
    rows, cols = int(round(np.sqrt(len(xy)))), int(round(np.sqrt(len(xy))))
    faces = grid_indices(rows, cols).reshape(-1, 3)
    # grid_indices assumes a terrain XZ grid; our rows run down a facing XY sheet.
    if np.cross(points[faces[0, 1]]-points[faces[0, 0]], points[faces[0, 2]]-points[faces[0, 0]])[2] < 0:
        faces = faces[:, [0, 2, 1]]
    uv = np.column_stack(((xy[:, 0]-xy[:, 0].min())/np.ptp(xy[:, 0]),
                          (xy[:, 1].max()-xy[:, 1])/np.ptp(xy[:, 1])))
    glb.mesh_node(name, [glb.primitive(points, faces.ravel(), material, normals=normals(points, faces), uvs=uv)])


def build_hexagon():
    glb = GLB('Cassini polar image on an idealized Saturn cloud-top cap')
    image = Image.open(SOURCES/'hexagon.jpg').convert('RGB')
    # Circular polar aperture; the observed jet is retained from the image.
    # The source is a polar mosaic, not a georeferenced orthographic texture;
    # registration to the approximate catalog jet width is explicitly approximate.
    radial, phi = np.meshgrid(np.linspace(0, .64, 49), np.linspace(0, 2*np.pi, 129), indexing='ij')
    xy = np.column_stack(((radial*np.cos(phi)).ravel(), (radial*np.sin(phi)).ravel()))
    radius = 60268/25000
    z = np.sqrt(radius**2-np.sum(xy**2, axis=1))-radius
    points = np.column_stack((xy, z))
    faces = grid_indices(49, 129).reshape(-1, 3)
    area = np.cross(points[faces[:, 1]]-points[faces[:, 0]], points[faces[:, 2]]-points[faces[:, 0]])
    faces = faces[np.linalg.norm(area, axis=1) > 1e-12]
    area = np.cross(points[faces[:, 1]]-points[faces[:, 0]], points[faces[:, 2]]-points[faces[:, 0]])
    if area[:, 2].mean() < 0:
        faces = faces[:, [0, 2, 1]]
    uv = np.column_stack((xy[:, 0]/1.28+.5, .5-xy[:, 1]/1.28))
    n = np.column_stack((xy, z+radius))/radius
    buf = io.BytesIO(); image.save(buf, 'JPEG', quality=94, subsampling=0)
    texture = glb.texture(buf.getvalue(), 'image/jpeg')
    mat = glb.material('Cassini false-color polar cloud image', texture=texture, double_sided=True)
    glb.doc['materials'][mat].update(emissiveTexture={'index': texture}, emissiveFactor=[.25, .25, .25])
    glb.mesh_node('Cassini north polar cloud cap', [glb.primitive(points, faces.ravel(), mat, normals=n, uvs=uv)])
    entry = agency(base_entry('cassini-saturn-hexagon', "Saturn's Hexagon", 'image-textured-cloud-cap',
        'Cassini PIA17652 false-color polar mosaic on a shallow idealized spherical cap. The jet’s visible across-corners width is registered approximately to the catalog 25,000 km; the surrounding circular aperture is context and extends to about 1.28×. This is approximate image registration, not a georeferenced latitude/longitude map. Colors combine ultraviolet, visible and infrared wavelengths and are not natural vision. Geometry shows planetary curvature only, not measured cloud heights. The source is a 2012 image, not current weather or a six-sided solid object.',
        'https://science.nasa.gov/resource/saturns-streaming-hexagon-storm/',
        'NASA/JPL-Caltech/SSI/Hampton University; cap assembled by Universe Scales'))
    entry['presentation'].update(reference_size=1, layout_width_factor=1.3)
    attach_source(entry, 'hexagon.jpg')
    entry['processing'].update(source_image_size=list(image.size),
        operations=['Retain original 1024px NASA polar mosaic in a circular aperture',
                    'Register image jet width approximately; retain image cloud markings',
                    'Drape over a shallow cap with Saturn curvature; no relief noise'])
    return save(glb, entry)


def build_grs():
    glb = GLB('Juno enhanced-color image on idealized cloud-top patch')
    # Full storm in the right part of PIA23606. Keep the surrounding collar.
    image = Image.open(SOURCES/'grs2019.jpg').convert('RGB').crop((1740, 80, 2760, 1000))
    x, y = np.meshgrid(np.linspace(-.60, .60, 65), np.linspace(.5412, -.5412, 65))
    xy = np.column_stack((x.ravel(), y.ravel()))
    radius = 71492/16350
    z = np.sqrt(radius**2-np.sum(xy**2, axis=1))-radius
    textured_patch(glb, 'Juno Great Red Spot and cloud collar', image, xy, z)
    entry = base_entry('juno-great-red-spot', 'Great Red Spot', 'image-textured-cloud-patch',
        'An enhanced-color Juno cloud image (12 February 2019) draped over an idealized shallow cloud-top patch. The storm is shown at the catalog’s representative April 2017 width of 16,350 km. This is an illustrative size comparison using later imagery, not a measured 2019 map or a claim that the storm’s size stayed constant. The surrounding collar is context. Curvature is schematic; neither cloud heights nor storm depth are reconstructed. Credit NASA/JPL-Caltech/SwRI/MSSS; processing Kevin M. Gill, CC BY; cropped and draped by Universe Scales.',
        'https://science.nasa.gov/photojournal/the-great-red-spot/',
        'NASA/JPL-Caltech/SwRI/MSSS; image processing Kevin M. Gill; adapted by Universe Scales')
    entry.update(license='CC BY (image processing); NASA public-domain image data',
        license_url='https://science.nasa.gov/photojournal/the-great-red-spot/',
        license_files=['licenses/space3d2-rights.md', 'licenses/nasa-media-guidelines.html'])
    entry['presentation'].update(reference_size=1, pitch=-8, yaw=-10, layout_width_factor=1.25)
    attach_source(entry, 'grs2019.jpg')
    entry['processing'].update(image_crop_pixels=[1740, 80, 2760, 1000],
        operations=['Crop PIA23606 around the full Great Red Spot and collar',
                    'Use the catalog 2017 size as a representative display scale, explicitly not 2019 astrometry',
                    'Drape over an idealized shallow spherical patch; do not invent storm relief'])
    return save(glb, entry)


def roche_radius(theta, polar_ratio):
    """Roche equipotential with equatorial radius 1 and the specified polar radius."""
    omega2 = 2*(1/polar_ratio-1)
    lo, hi = np.full_like(theta, polar_ratio), np.ones_like(theta)
    for _ in range(60):
        r = (lo+hi)/2
        potential = 1/r + .5*omega2*r*r*np.sin(theta)**2
        lo = np.where(potential > 1/polar_ratio, r, lo)
        hi = np.where(potential > 1/polar_ratio, hi, r)
    return (lo+hi)/2


def build_star(kind):
    definitions = {
        'neutron': ('nicer-j0437-sphere', 'PSR J0437-4715 Neutron Star', 22.720, (.66, .83, 1),
            'https://arxiv.org/abs/2407.06789',
            'A true-size smooth sphere at the catalog’s 22.72 km equatorial-diameter estimate, twice the 11.36 km radius inferred by Choudhury et al. (2024) from NICER pulse-profile modeling and radio timing. It is not a resolved surface photograph. Sphericity and blue-white color are display conventions; hot spots, beams, atmosphere and gravitational lensing are not simulated. The 2024 radius has a 68% interval of -0.63/+0.95 km. A newer NICER analysis (arXiv:2512.08790) finds a broader, larger range, so this is explicitly the catalog’s 2024 estimate, not a unique established radius.'),
        'sirius': ('sirius-b-sphere', 'Sirius B', 11300, (.79, .87, 1),
            'https://arxiv.org/abs/1703.10625',
            'A smooth white-dwarf sphere calibrated to the catalog’s approximate 11,300 km diameter. Bond et al. (2017) infer a radius of 0.008098 solar radii. The blue-white tint is illustrative; no resolved surface texture, accretion disk or surrounding halo is claimed. Brightness is adjusted for inspection, not compared photometrically with other stars.'),
        'proxima': ('proxima-centauri-sphere', 'Proxima Centauri Diameter', 214553.880, (1, .43, .19),
            'https://www.aanda.org/articles/aa/pdf/2017/02/aa29930-16.pdf',
            'A smooth red-dwarf sphere calibrated to the catalog diameter, from the 0.1542 solar-radius estimate of Kervella et al. (2017). Warm color and inspection lighting are illustrative; no resolved photospheric map, invented spots, flares or corona is implied. Apparent brightness is adjusted for visibility and is not a luminosity comparison.'),
        'eris': ('eris-occultation-sphere', 'Eris', 2326, (.9, .91, .91),
            'https://www.eso.org/public/news/eso1142/',
            'An idealized untextured icy sphere at the 2,326 km diameter measured by Sicardy et al. (2011) from a stellar occultation (about ±12 km). It is not a spacecraft-derived terrain model: no resolved surface map of Eris is available here. Bright neutral material suggests its high reflectivity without inventing craters or albedo markings. Dysnomia is omitted.'),
    }
    if kind == 'vega':
        return build_vega()
    model_id, item, diameter, color, source, note = definitions[kind]
    glb = GLB('Universe Scales idealized measured-diameter sphere')
    material = glb.material('Illustrative color; no resolved surface map', color=(*color, 1),
                            emissive=tuple(c*.18 for c in color) if kind != 'eris' else None, double_sided=False)
    sphere(glb, item, diameter/2, material)
    entry = base_entry(model_id, item, 'idealized-size-sphere', note, source)
    entry['presentation']['reference_size'] = diameter
    if kind == 'neutron':
        entry['display_label'] = 'PSR J0437-4715 · 2024 NICER estimate'
    entry['processing'].update(native_units='km', diameter_km=diameter,
        operations=['Create a smooth sphere at the cited catalog diameter', 'Use an authored uniform material; no surface texture'])
    return save(glb, entry)


def build_vega():
    glb = GLB('Vega Roche surface from CHARA concordance parameters')
    ratio = 2.418/2.726
    theta, phi = np.meshgrid(np.linspace(0, np.pi, 65), np.linspace(0, 2*np.pi, 129), indexing='ij')
    radius = roche_radius(theta, ratio)
    p = np.stack((radius*np.sin(theta)*np.cos(phi), radius*np.cos(theta),
                  -radius*np.sin(theta)*np.sin(phi)), axis=-1).reshape(-1, 3)
    faces = grid_indices(65, 129).reshape(-1, 3)
    faces = faces[np.linalg.norm(np.cross(p[faces[:, 1]]-p[faces[:, 0]], p[faces[:, 2]]-p[faces[:, 0]]), axis=1) > 1e-10]
    # Analytic equipotential normals avoid averaging the degenerate pole seams.
    omega2 = 2*(1/ratio-1)
    n = p/np.linalg.norm(p, axis=1)[:, None]**3 - p*[omega2, 0, omega2]
    n /= np.linalg.norm(n, axis=1)[:, None]
    # A smooth latitude-only texture illustrates modeled gravity darkening.
    t = np.linspace(0, np.pi, 512)
    r = roche_radius(t, ratio)
    radial = 1/r**2 - omega2*r*np.sin(t)**2
    meridional = omega2*r*np.sin(t)*np.cos(t)
    gravity = np.hypot(radial, meridional)
    temperature = 10070*(gravity*ratio**2)**.231
    # Use T^4 only for a qualitative relative brightness; no claimed colorimetry.
    brightness = (temperature/10070)**4
    colors = np.array([.72, .84, 1])[None, :]*(.32+.68*brightness[:, None])
    pixels = np.uint8(np.clip(np.repeat(colors[:, None, :], 16, axis=1)*255, 0, 255))
    buf = io.BytesIO(); Image.fromarray(pixels).save(buf, 'PNG')
    texture = glb.texture(buf.getvalue(), 'image/png')
    material = glb.material('Qualitative gravity darkening', texture=texture, double_sided=False)
    glb.doc['materials'][material]['emissiveTexture'] = {'index': texture}
    glb.doc['materials'][material]['emissiveFactor'] = [.4, .4, .4]
    uv = np.stack((phi/(2*np.pi), theta/np.pi), axis=-1).reshape(-1, 2)
    # Physical source radius in km, without normalizing the polar axis separately.
    p *= 2.726*SOLAR_RADIUS_KM
    glb.mesh_node('Vega modeled Roche photosphere', [glb.primitive(p, faces.ravel(), material, normals=n, uvs=uv)])
    entry = base_entry('vega-roche-photosphere', 'Vega Diameter', 'interferometry-constrained-roche-model',
        'An oblate Roche equipotential using Monnier et al. (2012) CHARA/MIRC concordance-model equatorial and polar radii, 2.726 and 2.418 solar radii. Latitude shading qualitatively illustrates gravity darkening (polar temperature 10,070 K, exponent 0.231); it is not an observed surface map or calibrated color photometry. The oblique inspection view deliberately exposes flattening. From Earth Vega is seen nearly pole-on (~6.2°), so this is not its sky orientation. Earlier Aufdenberg et al. (2006) modeling supports rapid rotation but gives different parameters.',
        'https://arxiv.org/html/1211.6055v1')
    entry['presentation'].update(reference_size=3792956.400, pitch=23, roll=-16, layout_width_factor=1.1)
    entry['processing'].update(native_units='km', equatorial_radius_solar=2.726, polar_radius_solar=2.418,
        nominal_solar_radius_km=SOLAR_RADIUS_KM, gravity_darkening_beta=.231, polar_temperature_K=10070,
        operations=['Solve a Roche equipotential at each colatitude',
                    'Compute analytic gravity normals; shade smoothly by modeled relative temperature',
                    'Retain the true equator-to-pole radius ratio and authored inspection pose'])
    return save(glb, entry)


def orbital_matrix(elements):
    om, inc, w = [math.radians(elements[k]) for k in ['om', 'i', 'w']]
    def rz(t):
        return np.array([[math.cos(t), -math.sin(t), 0], [math.sin(t), math.cos(t), 0], [0, 0, 1]])
    rx = np.array([[1, 0, 0], [0, math.cos(inc), -math.sin(inc)], [0, math.sin(inc), math.cos(inc)]])
    return rz(om) @ rx @ rz(w)


def kepler_position(elements, mean_anomaly):
    """J2000 ecliptic XYZ in AU from heliocentric osculating elements."""
    m = np.asarray(mean_anomaly, dtype=float)
    e, a = elements['e'], elements['a']
    E = m.copy()
    for _ in range(50):
        step = (E-e*np.sin(E)-m)/(1-e*np.cos(E))
        E -= step
        if np.max(np.abs(step)) < 1e-13:
            break
    p = np.stack((a*(np.cos(E)-e), a*np.sqrt(1-e*e)*np.sin(E), np.zeros_like(E)), axis=-1)
    return p @ orbital_matrix(elements).T


def line(glb, name, points, color, pairs=False):
    p = np.asarray(points, dtype='<f4')
    if not pairs:
        p = np.stack((p[:-1], p[1:]), axis=1).reshape(-1, 3)
    m = glb.material(name, color=(*color, 1), emissive=tuple(c*.6 for c in color))
    glb.mesh_node(name, [{'mode': 1, 'attributes': {'POSITION': glb._accessor(p, 5126, 'VEC3', 34962, True)}, 'material': m}])


def marker(glb, name, p, color, label=None):
    m = glb.material(name+' location', color=(*color, 1), emissive=tuple(color))
    sphere(glb, name+' display marker', .003, m, p, 16, 8)
    if label:
        glb.label_node(name, p+np.array([.008, .018, 0]), label)


def build_orbit(body):
    doc = json.loads((SOURCES/(body+'.json')).read_text())
    elements = {e['name']: float(e['value']) for e in doc['orbit']['elements']}
    e, a = elements['e'], elements['a']
    span = (5306834865211.8 if body == 'halley' else 140000000000000)/AU_M
    # In-plane inspection frame, preserving relative ecliptic geometry. The
    # source long axis is horizontal; authored 18-degree tilt exposes depth.
    source_to_view = np.array([[-1, 0, 0], [0, 1, 0], [0, 0, -1]]) @ orbital_matrix(elements).T
    def view(p):
        return p @ source_to_view.T / span
    anomaly = np.linspace(0, 2*np.pi, 1801)
    orbit = view(kepler_position(elements, anomaly))
    glb = GLB('JPL osculating orbit measurement diagram')
    line(glb, body.capitalize()+' osculating orbit', orbit, (.42, .75, 1))
    # Center scene at the orbit midpoint to keep float coordinates small.
    center = np.array([a*e/span, 0, 0])
    # Translation is applied to all nodes together at the end.
    sun = np.zeros(3)
    marker(glb, 'Sun', sun, (1, .67, .22), 'Sun · marker')
    aphelion = view(kepler_position(elements, np.array([np.pi])))[0]
    perihelion = view(kepler_position(elements, np.array([0.])))[0]
    marker(glb, 'Aphelion', aphelion, (.66, .87, 1), f"Q = {a*(1+e):.1f} AU")
    if body == 'halley':
        source_record('planet-elements.json')
        marker(glb, 'Perihelion', perihelion, (.95, .7, .35))
        start, end = perihelion, aphelion
        caption = f"major axis · {2*a:.2f} AU"
    else:
        start, end = sun, aphelion
        caption = f"Sun to aphelion · {a*(1+e):.1f} AU"
    y = -.20 if body == 'halley' else -.27
    ruler = np.array([start, [start[0], y, 0], [start[0], y, 0], [end[0], y, 0], [end[0], y, 0], end])
    line(glb, 'Measured span ruler', ruler, (.85, .9, 1), pairs=True)
    glb.label_node('Distance definition', [(start[0]+end[0])/2, y-.04, 0], caption)
    # Ecliptic-plane orbit context: use the pinned JPL approximate planet table.
    if body == 'halley':
        for name, planet in json.loads((SOURCES/'planet-elements.json').read_text())['planets'].items():
            if name not in ('Earth', 'Jupiter', 'Neptune'):
                continue
            p = view(kepler_position(planet, np.linspace(0, 2*np.pi, 721)))
            # Neptune exceeds the Halley major-axis frame, so omit it here.
            if name == 'Neptune':
                continue
            line(glb, name+' orbit context', p, (.22, .30, .40))
    for node in glb.doc['nodes']:
        node['translation'] = (np.array(node.get('translation', [0, 0, 0]))-center).tolist()
    item = "Halley's Comet Orbit" if body == 'halley' else 'Sedna Aphelion'
    note = ('JPL SBDB heliocentric osculating ellipse for 1P/Halley, at the returned 1968 epoch; the ruler measures the entire major axis, not a Sun-to-comet radius or traveled path. Faint Earth/Jupiter ellipses are JPL J2000 reference orbits for context. This is a static two-body orbital diagram, not a current comet position or a full N-body trajectory. The Sun and endpoint dots are enlarged location markers, not true body diameters.' if body == 'halley' else
            'JPL SBDB heliocentric osculating ellipse for Sedna at the pinned 2026 epoch. The ruler runs from the Sun’s focus to aphelion, not across the whole ellipse. This source solution gives Q about 1,011 AU, differing from the catalog’s older approximate 937 AU; coordinates are preserved without stretching. The diagram is a two-body snapshot, not a measured future trajectory. Sun and endpoint dots are enlarged location markers, not physical bodies.')
    entry = agency(base_entry('jpl-'+body+'-orbit', item, 'catalog-orbit-diagram', note,
                              'https://ssd-api.jpl.nasa.gov/doc/sbdb.html', 'NASA/JPL Solar System Dynamics; diagram by Universe Scales'))
    attach_source(entry, body+'.json')
    entry['presentation'].update(reference_size=1, pitch=18, layout_width_factor=1.2)
    entry['processing'].update(elements=elements, source_epoch_jd_tdb=doc['orbit']['epoch'],
        source_orbit_id=doc['orbit']['orbit_id'], physical_reference_AU=span,
        source_to_inspection_rotation=source_to_view.tolist(),
        operations=['Solve Kepler equation for pinned JPL elements', 'Rotate rigidly to an orbital-plane inspection frame',
                    'Use catalog meters/AU as calibration; never normalize the coordinate bounds'])
    return save(glb, entry)


def build_kuiper():
    data = json.loads((SOURCES/'kuiper.json').read_text())
    positions, names, epochs = [], [], []
    for row in data['data']:
        record = dict(zip(data['fields'], row))
        if any(record.get(k) is None for k in ['a', 'e', 'i', 'om', 'w', 'ma', 'epoch']):
            continue
        elements = {k: float(record[k]) for k in ['a', 'e', 'i', 'om', 'w']}
        # Two-body mean motion from the DE440 solar GM, JPL astro_par.html.
        mean_motion = math.sqrt(1.32712440041279419e20/(elements['a']*AU_M)**3)*86400
        anomaly = math.radians(float(record['ma']))+mean_motion*(SNAPSHOT_JD-float(record['epoch']))
        p = kepler_position(elements, anomaly)
        if not 30 <= np.linalg.norm(p) <= 50:
            continue
        positions.append(p); names.append(record['pdes']); epochs.append(float(record['epoch']))
    p = np.asarray(positions)
    # Y-up ecliptic, one right-handed rigid rotation, no manufactured ring points.
    p = p[:, [0, 2, 1]] * [1, 1, -1]
    # Deterministic spatially unbiased prefix ordering for runtime point LOD.
    order = np.random.default_rng(4337).permutation(len(p))
    p = p[order]
    glb = GLB('Real JPL SBDB Kuiper-region orbit-element sample')
    material = glb.material('KBO location glyphs (not sizes)', color=(.66, .84, 1, 1), emissive=(.35, .5, .7))
    glb.mesh_node('Cataloged KBO locations', [{'mode': 0, 'attributes': {'POSITION': glb._accessor(p.astype('<f4'), 5126, 'VEC3', 34962, True)}, 'material': material}])
    glb.doc['nodes'][-1]['extras'] = {'pointSize': {'max': 3, 'perPixel': .005}, 'softPoints': True}
    # Actual Sun diameter in AU; a caption identifies the subpixel body.
    sun_mat = glb.material('Sun context', color=(1, .7, .3, 1), emissive=(1, .6, .2))
    sphere(glb, 'True-size Sun (subpixel)', SOLAR_RADIUS_KM*1000/AU_M, sun_mat, segments=24, rings=12)
    glb.label_node('Sun annotation', [0, 2, 0], 'Sun')
    source_record('planet-elements.json')
    planets = json.loads((SOURCES/'planet-elements.json').read_text())['planets']
    planet = planets['Neptune']
    neptune = kepler_position(planet, np.linspace(0, 2*np.pi, 721))[:, [0, 2, 1]] * [1, 1, -1]
    line(glb, 'Neptune J2000 reference orbit', neptune, (.22, .38, .56))
    glb.label_node('Catalog qualification', [0, 0, 53], f'{len(p):,} catalog locations · selected 30–50 AU')
    entry = agency(base_entry('jpl-kuiper-catalog', 'Kuiper Belt', 'catalog-point-cloud',
        f'{len(p):,} actual catalog-object locations from the pinned JPL SBDB orbital elements, propagated with a two-body approximation to 16 October 2026 TDB. Selection: asteroid records with semimajor axis 30–50 AU, perihelion at least 30 AU, and computed distance 30–50 AU. This is a selected, discovery-biased subset, not all Kuiper Belt objects or an unbiased density map. Point colors and sizes are display glyphs, not body sizes or measured colors. The faint Neptune ellipse is a JPL J2000 reference orbit; the Sun is physically scaled and subpixel. No synthetic filler points are added.',
        'https://ssd-api.jpl.nasa.gov/doc/sbdb_query.html', 'NASA/JPL Solar System Dynamics; catalog visualization by Universe Scales'))
    attach_source(entry, 'kuiper.json')
    entry['presentation'].update(reference_size=15000000000000/AU_M, pitch=24, yaw=-12, roll=-8, layout_width_factor=1.1)
    identity_path = SOURCES/'kuiper-displayed.json'
    write_json(identity_path, {'point_order_pdes': [names[i] for i in order]})
    entry['processing'].update(native_units='AU', selected_query_count=int(data['count']), displayed_count=len(p),
        display_epoch_jd_tdb=SNAPSHOT_JD, point_identities=str(identity_path.relative_to(ROOT)),
        point_identities_sha256=sha(identity_path.read_bytes()),
        operations=['Retain actual JPL osculating elements and solve Kepler equation',
                    'Propagate mean anomaly to a common display epoch with a fixed two-body approximation',
                    'Select computed heliocentric distance 30–50 AU; retain true coordinates',
                    'Shuffle deterministically for runtime LOD; add no synthetic objects'])
    return save(glb, entry)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', choices=['saturn', 'shapes', 'clouds', 'stars', 'orbits', 'kuiper'])
    args = parser.parse_args()
    if args.only in (None, 'saturn'):
        build_saturn(False); build_saturn(True)
    if args.only in (None, 'shapes'):
        build_shape('ryugu', 'Ryugu', pose={'yaw': -25, 'pitch': 12, 'layout_width_factor': 1.25})
        build_shape('dimorphos', 'Dimorphos', pose={'yaw': -18, 'pitch': 12, 'layout_width_factor': 1.3})
        build_shape('hyperion', 'Hyperion Moon', pose={'yaw': 60, 'pitch': 15, 'layout_width_factor': 1.3}, pending=True)
    if args.only in (None, 'clouds'):
        build_hexagon(); build_grs()
    if args.only in (None, 'stars'):
        for kind in ['eris', 'neutron', 'sirius', 'proxima', 'vega']:
            build_star(kind)
    if args.only in (None, 'orbits'):
        build_orbit('halley'); build_orbit('sedna')
    if args.only in (None, 'kuiper'):
        build_kuiper()


if __name__ == '__main__':
    main()
