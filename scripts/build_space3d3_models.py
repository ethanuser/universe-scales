#!/usr/bin/env python3
"""Offline physical distance/orbit models from pinned primary-source inputs.

No dataset, exported data, images directory, or runtime code is edited.
Native units are documented per asset; reference_size is a physical conversion,
never the measured bounding-box extent. See handoff/space3d3/REPORT.md.
"""
import argparse
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

from build_space3d_diagrams import sphere
from build_space3d2_models import line, kepler_position
from fetch_model_assets import inspect_glb, read_glb, sha, view_bytes, write_json
from geo_glb_common import GLB, grid_indices
from register_model import register

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT/'content/visualizations/models'
SOURCES = MODELS/'sources/space3d3'
HANDOFF = ROOT/'handoff/space3d3'
PARAMS = json.loads((SOURCES/'parameters.json').read_text())
C = PARAMS['constants']
AU_KM = C['au_m']/1000
LY_KM = C['c_m_s']*C['day_s']*C['julian_year_days']/1000
PC_KM = C['pc_m']/1000
WHITE = (.75, .86, 1.)
CYAN = (.22, .65, .95)
AMBER = (1., .58, .12)


def pinned(name):
    records = json.loads((SOURCES/'manifest.json').read_text())['sources']
    record = next(r for r in records if r['file'] == name)
    if sha((SOURCES/name).read_bytes()) != record['sha256']:
        raise ValueError(f'Pinned source changed: {name}')
    return record


def entry(model_id, item, source, note, native_units='reference distance', reference_size=1):
    return {'id': model_id, 'matches': {'length': [item]}, 'geometry': 'mesh',
            'author': 'Universe Scales; scientific teams credited in source notes',
            'source': source, 'reference': f'content/visualizations/models/sources/{model_id}.md',
            'representation': 'measurement-diagram', 'note': note,
            'license': 'CC0-1.0', 'license_url': 'https://creativecommons.org/publicdomain/zero/1.0/',
            'license_files': ['licenses/CC0-1.0.txt'],
            'volume_semantics': 'not_a_volume_measurement', 'closed_volume_checked': False,
            'presentation': {'reference_size': reference_size, 'layout_width_factor': 1.3,
                             'roughness': 1, 'metalness': 0},
            'processing': {'builder': 'scripts/build_space3d3_models.py', 'native_units': native_units,
                           'parameters_sha256': pinned('parameters.json')['sha256'],
                           'operations': []}}


def agency(e):
    e.update(license='U.S. public-domain NASA media/data; credit the named science teams',
             license_url='https://www.nasa.gov/nasa-brand-center/images-and-media/',
             license_files=['licenses/nasa-media-guidelines.html', 'licenses/nasa-3d-resources.README.md'])
    return e


def attach(e, name):
    e['processing'].setdefault('pinned_inputs', []).append(pinned(name))


def save(glb, e, pending=False):
    HANDOFF.mkdir(parents=True, exist_ok=True)
    path = MODELS/(e['id']+'.glb')
    glb.write(path)
    e.update(src=str(path.relative_to(ROOT)), **inspect_glb(path.read_bytes()))
    if e['bytes'] >= 3_000_000:
        raise ValueError('GLB exceeds asset budget')
    write_json(HANDOFF/(e['id']+'.entry.json'), e)
    notes = f"""# {e['matches']['length'][0]}

{e['note']}

## Scientific basis and calibration

- Primary source: {e['source']}
- Parameter citations: `space3d3/parameters.json` (each group has its primary URL).
- Native units: {e['processing']['native_units']}.
- One catalog length is {e['presentation']['reference_size']:.12g} native units.
- Inspection pose: {json.dumps({k:e['presentation'][k] for k in ['pitch','yaw','roll'] if k in e['presentation']})} degrees, Three.js XYZ.
- Parameters and downloaded inputs are pinned by SHA-256 in `space3d3/manifest.json`.
- Source-specific numerical facts and operations: see the entry's `processing` record
  and `handoff/space3d3/{e['id']}.entry.json`.

## Credit and rights

{e['author']}. {e['license']}. {e['license_url']}
Original authored diagram geometry is CC0. Scientific paper text/figures are not
redistributed. NASA textures retain NASA credit and usage terms. The EHT color
image, where present, retains EHT Collaboration credit under CC BY 4.0, verified
on ESO's source page and copyright policy. Radcliffe numerical cloud coordinates
are from the authors' supplement and its CC0 cloud database (DataCite rights
record retained at `space3d3/radcliffe-data-rights.json`); the Plotly code/graphic
and fitted/posterior cloud samples are not redistributed.

## Rebuild and limitations

Run `./venv/bin/python scripts/build_space3d3_models.py` offline. Refreshing inputs
is separate: `scripts/prepare_space3d3_sources.py`. No runtime data service is used.
The handoff contains rest and quarter-camera CPU previews and loader checks.
These do not certify WebGL appearance, perspective, production SVG label handling,
the actual explorer, mobile, or the production model-lab audit.
"""
    (MODELS/'sources'/(e['id']+'.md')).write_text(notes)
    if pending:
        print('Prepared pending dataset correction:', e['id'])
    else:
        register(HANDOFF/(e['id']+'.entry.json'), path, 'length')
    return e


def marker(glb, name, position, color=AMBER, radius=.004, label=None):
    """Explicitly nonphysical location glyph; does not stand in for a body radius."""
    m = glb.material(name+' location glyph', color=(*color, 1), emissive=color)
    sphere(glb, name+' marker', radius, m, position, 16, 8)
    if label:
        glb.label_node(name+' label', np.asarray(position)+[0, radius*4, 0], label)


def ruler(glb, start, end, offset, text, ticks=0):
    start, end, offset = map(lambda a: np.asarray(a, dtype=float), (start, end, offset))
    a, b = start+offset, end+offset
    line(glb, 'Measurement bracket', [start, a, a, b, b, end], WHITE, pairs=True)
    if ticks:
        # Short, equal subdivisions of the physical ruler, not time samples.
        tick = offset/np.linalg.norm(offset)*np.linalg.norm(end-start)*.009
        pairs = []
        for i in range(1, ticks):
            p = a+(b-a)*i/ticks
            pairs.extend([p-tick, p+tick])
        line(glb, 'Equal ruler subdivisions', pairs, (.38, .53, .68), pairs=True)
    glb.label_node('Measurement', (a+b)/2+offset*.18, text)


def body(glb, e, name, radius, position, texture_only=False):
    """Retain an existing NASA map on an idealized sphere at the physical radius."""
    ids = {'Sun': 'nasa-sun', 'Earth': 'nasa-earth', 'Moon': 'nasa-moon',
           'Mercury': 'nasa-mercury', 'Jupiter': 'nasa-jupiter', 'Neptune': 'nasa-neptune'}
    registry = json.loads((ROOT/'content/visualizations/models.json').read_text())['models']
    src = next(m for m in registry if m['id'] == ids[name])
    data = (ROOT/src['src']).read_bytes()
    if sha(data) != src['sha256']:
        raise ValueError('Changed NASA source '+name)
    doc, binary = read_glb(data)
    material = next(m for m in doc['materials'] if m.get('pbrMetallicRoughness', {}).get('baseColorTexture') or m.get('emissiveTexture'))
    slot = material.get('pbrMetallicRoughness', {}).get('baseColorTexture') or material['emissiveTexture']
    texture_index = slot['index']
    image = doc['images'][doc['textures'][texture_index]['source']]
    raw = view_bytes(doc, binary, image['bufferView'])
    # Smaller maps suffice: most physical globes here are subpixel.
    im = Image.open(io.BytesIO(raw)).convert('RGB')
    im.thumbnail((1024, 512), Image.Resampling.LANCZOS)
    output = io.BytesIO(); im.save(output, 'JPEG', quality=90)
    tex = glb.texture(output.getvalue(), 'image/jpeg')
    if not texture_only:
        mat = glb.material(name+' NASA map', texture=tex, double_sided=False)
        if name == 'Sun':
            glb.doc['materials'][mat].update(emissiveTexture={'index': tex}, emissiveFactor=[.8]*3)
        # A unit sphere with node scaling makes the existing SVG outline radius exact.
        sphere(glb, name, 1, mat, segments=48, rings=24)
        glb.doc['nodes'][-1].update(scale=[float(radius)]*3, translation=list(map(float, position)),
            extras={'outline': True, 'sphere': True})
    e['processing'].setdefault('source_models', []).append({'id': src['id'], 'sha256': sha(data), 'source': src['source']})
    return tex


def build_planet(name):
    p = PARAMS['bodies'][name]
    distance = p['semimajor_axis_km']
    catalog = {'Mercury': 57900000, 'Jupiter': 778500000, 'Neptune': 4514953000}[name]
    glb = GLB('NASA physical mean-separation diagram')
    e = agency(entry('space3d3-sun-'+name.lower(), 'Sun-'+name+' Distance', p['source'],
        f'NASA Sun and {name} image maps on idealized spheres, separated by the NASA fact-sheet semimajor axis of {distance:,.0f} km. Body radii and distance use the same physical scale. This is a representative center-to-center separation equal to a, not an orbital snapshot or the diameter of the orbit. Subpixel body outlines are location aids. Faint inner reference ellipses, where present, use JPL J2000 elements and are not simultaneous planet positions.'))
    e['processing'].update(distance_km=distance, catalog_reference_km=catalog)
    body(glb, e, 'Sun', C['solar_radius_km']/catalog, [-.5, 0, 0])
    body(glb, e, name, p['radius_km']/catalog, [distance/catalog-.5, 0, 0])
    glb.label_node('Sun name', [-.5, .06, 0], 'Sun')
    glb.label_node('Planet name', [distance/catalog-.5, .06, 0], name)
    ruler(glb, [-.5, 0, 0], [distance/catalog-.5, 0, 0], [0, -.16, 0],
          f'{distance/1e6:,.2f} million km', ticks=5)
    if name != 'Mercury':
        planets = json.loads((MODELS/'sources/space3d2/planet-elements.json').read_text())['planets']
        for inner in (['Earth'] if name == 'Jupiter' else ['Earth', 'Jupiter']):
            points = kepler_position(planets[inner], np.linspace(0, 2*np.pi, 481))
            # Proper ecliptic to display mapping: X, Z, -Y (Y display up).
            points = points[:, [0, 2, 1]]*[1, 1, -1]*AU_KM/catalog + [-.5, 0, 0]
            line(glb, inner+' reference ellipse', points, (.18, .36, .49))
    e['presentation'].update(pitch=32)
    e['processing']['operations'] = ['Reuse embedded NASA maps; spherical mean-radius approximation',
                                     'Place centers one published semimajor axis apart, preserve km ratios']
    if name == 'Neptune':
        e['requires_dataset'] = {'name': 'Sun-Neptune Distance', 'value_m': 4514953000000,
                                'reason': 'Existing value 4514953000 is kilometers mistakenly stored as meters'}
    return save(glb, e, pending=name == 'Neptune')


def build_iss():
    altitude = PARAMS['iss']['representative_altitude_m']/1000
    earth_r = PARAMS['bodies']['Earth']['radius_km']/altitude
    glb = GLB('Surface-to-ISS altitude, local true-curvature Earth cap')
    e = agency(entry('space3d3-iss-altitude', 'ISS Orbital Altitude', PARAMS['iss']['source'],
        'A local Earth cap with true spherical curvature and a surface-normal ruler to NASA’s representative 250-mile (402.336 km) ISS altitude. The local cap is an arbitrary display window, not the whole Earth or an island boundary. Its 40 km underside is an authored cut, not crust depth. The ISS is a location glyph; its 109 m span is subpixel here. The altitude varies and this is not current telemetry. The ground imagery is the existing NASA global map with no invented terrain.'))
    # Reuse the map extraction helper without keeping its full globe.
    tex = body(glb, e, 'Earth', 1, [0, 0, 0], texture_only=True)
    longitude, latitude = np.meshgrid(np.linspace(-.45/earth_r, .45/earth_r, 41),
                                     np.linspace(-.32/earth_r, .32/earth_r, 33))
    n = np.stack((np.cos(latitude)*np.sin(longitude), np.cos(latitude)*np.cos(longitude),
                  -np.sin(latitude)), axis=-1).reshape(-1, 3)
    positions = n*earth_r-[0, earth_r, 0]
    # Geographic patch centered on equatorial Atlantic, longitude 20 W.
    uv = np.column_stack(((longitude.ravel()-math.radians(20))/(2*np.pi)+.5,
                          .5-latitude.ravel()/np.pi))
    mat = glb.material('NASA Earth map local spherical window', texture=tex, double_sided=True)
    glb.doc['materials'][mat].update(emissiveTexture={'index':tex},emissiveFactor=[.25]*3)
    faces = grid_indices(33, 41).reshape(-1, 3)
    cross = np.cross(positions[faces[:, 1]]-positions[faces[:, 0]], positions[faces[:, 2]]-positions[faces[:, 0]])
    if np.mean(np.einsum('ij,ij->i', cross, n[faces[:, 0]])) < 0:
        faces = faces[:, [0, 2, 1]]
    glb.mesh_node('Local Earth surface', [glb.primitive(positions, faces.ravel(), mat, normals=n, uvs=uv)])
    # Four closed display-cut walls, with a modest authored depth.
    edge = np.r_[np.arange(41), np.arange(81, 33*41, 41),
                 np.arange(33*41-2, 32*41-1, -1), np.arange(31*41, 0, -41)]
    border = positions[edge]; bottom = border.copy(); bottom[:, 1] = -.10
    pairs = np.stack((border, bottom), axis=1).reshape(-1, 3)
    wall_faces = []
    for i in range(len(border)):
        j = (i+1)%len(border)
        wall_faces.extend([2*i, 2*i+1, 2*j, 2*j, 2*i+1, 2*j+1])
    wall = glb.material('Display cut', color=(.035, .085, .11, 1))
    glb.mesh_node('Arbitrary cut walls', [glb.primitive(pairs, wall_faces, wall)])
    floor_points=np.vstack((bottom.mean(axis=0),bottom))
    floor_faces=np.array([[0,(i+1)%len(bottom)+1,i+1] for i in range(len(bottom))]).ravel()
    glb.mesh_node('Arbitrary cut floor',[glb.primitive(floor_points,floor_faces,wall,
                  normals=np.tile([0,-1.,0],(len(floor_points),1)))])
    marker(glb, 'ISS', [0, 1, 0], WHITE, label='ISS')
    line(glb, 'Surface-normal altitude', [[0, 0, 0], [0, 1, 0]], CYAN)
    ruler(glb, [0, 0, 0], [0, 1, 0], [.30, 0, 0], '402 km', ticks=4)
    e['presentation'].update(pitch=20, yaw=-12, roll=-10)
    e['processing'].update(altitude_km=altitude, earth_radius_km=earth_r*altitude,
        cap_longitude_center_deg=-20, display_cut_depth_per_altitude=.10,
        operations=['Preserve spherical curvature at the NASA mean radius', 'Sample existing global texture in a small equatorial window',
                    'Author a surface-normal altitude ruler; no ISS geometry enlargement'])
    return save(glb, e)


def build_geo():
    altitude = PARAMS['geo']['altitude_km']
    r = PARAMS['bodies']['Earth']['equatorial_radius_km']/altitude
    glb = GLB('Surface-referenced geostationary altitude diagram')
    e = agency(entry('space3d3-geostationary-altitude', 'Geostationary Orbit', PARAMS['geo']['source'],
        'A 35,786 km surface-to-orbit radial altitude, with the Earth at the same physical scale. The nearby cyan arc is only a 24-degree segment of the circular equatorial geostationary orbit, not its full diameter. The center-to-orbit radius is Earth’s equatorial radius plus the listed altitude. The spacecraft point is a location glyph. The inspection pose foreshortens the radial ruler slightly; no coordinates are stretched.'))
    center = np.array([-.5-r, 0, 0])
    body(glb, e, 'Earth', r, center)
    # The orbit lies in the equatorial XZ plane of this upright Earth.
    t = np.linspace(-math.radians(12), math.radians(12), 161)
    orbit = np.column_stack(((1+r)*np.cos(t), np.zeros_like(t), (1+r)*np.sin(t)))+center
    line(glb, 'Geostationary equatorial orbit segment', orbit, CYAN)
    marker(glb, 'Geostationary location', [.5, 0, 0], AMBER)
    ruler(glb, [-.5, 0, 0], [.5, 0, 0], [0, -.29, 0], '35,786 km above equator')
    glb.label_node('Earth name', center+[0, .22, 0], 'Earth')
    e['presentation'].update(yaw=40, pitch=25)
    e['processing'].update(altitude_km=altitude, earth_equatorial_radius_km=r*altitude,
        center_to_orbit_km=altitude*(1+r), shown_orbit_arc_degrees=24)
    return save(glb, e)


def rotating_webb_vectors():
    webb = json.loads((SOURCES/'webb-vectors.json').read_text())
    sun = json.loads((SOURCES/'sun-vectors.json').read_text())
    if webb['jd_tdb'] != sun['jd_tdb']:
        raise ValueError('Mismatched ephemeris epochs')
    anti_sun = -np.asarray(sun['xyz_km'])
    x = anti_sun/np.linalg.norm(anti_sun, axis=1)[:, None]
    z = np.tile([0., 0., 1.], (len(x), 1))
    y = np.cross(z, x); y /= np.linalg.norm(y, axis=1)[:, None]
    z = np.cross(x, y)
    vectors = np.asarray(webb['xyz_km'])
    # Display Y is ecliptic north; display Z is negative orbital tangential axis.
    return np.stack((np.einsum('ij,ij->i', vectors, x), np.einsum('ij,ij->i', vectors, z),
                     -np.einsum('ij,ij->i', vectors, y)), axis=-1)


def build_webb():
    d = PARAMS['webb']['approximate_l2_distance_km']
    glb = GLB('JPL Horizons JWST trajectory in rotating Sun-Earth coordinates')
    e = agency(entry('space3d3-webb-l2-trajectory', 'James Webb Space Telescope Orbit', PARAMS['webb']['source'],
        'JPL Horizons JWST_merged geometric Earth-centered vectors for 1 January 2024–1 January 2025, sampled every two TDB days and rotated at each epoch into a Sun–Earth co-rotating frame. The real non-closing trajectory is preserved, with no fabricated halo ellipse or amplified depth. The ruler spans NASA’s approximate 1.5 million km Earth-to-L2 distance, not the halo diameter or a constant telescope range. A faint circular lunar mean-distance guide is context, not lunar ephemeris. Location glyphs are enlarged; the Earth and Moon have physical radii.'))
    points = rotating_webb_vectors()/d
    line(glb, 'JWST 2024 Horizons trajectory', points, (.96, .65, .19))
    body(glb, e, 'Earth', PARAMS['bodies']['Earth']['radius_km']/d, [0, 0, 0])
    moon_r = PARAMS['bodies']['Moon']['mean_orbit_radius_km']/d
    t = np.linspace(0, 2*np.pi, 481)
    line(glb, 'Lunar mean-distance guide', np.column_stack((moon_r*np.cos(t), np.zeros_like(t), moon_r*np.sin(t))), (.19, .38, .52))
    body(glb, e, 'Moon', PARAMS['bodies']['Moon']['radius_km']/d, [0, 0, -moon_r])
    marker(glb, 'L2', [1, 0, 0], CYAN, label='L2')
    marker(glb, 'Webb 1 Jan 2024', points[0], AMBER, label='Webb')
    glb.label_node('Earth name', [0, .045, 0], 'Earth')
    ruler(glb, [0, 0, 0], [1, 0, 0], [0, -.38, 0], '~1.5 million km')
    e['presentation'].update(pitch=22, yaw=-55)
    e['processing'].update(approximate_l2_distance_km=d, epochs=len(points), frame='Earth center; X anti-Sun, Y ecliptic north, Z negative tangential',
        trajectory_range_km=[float(v) for v in [np.linalg.norm(points,axis=1).min()*d,np.linalg.norm(points,axis=1).max()*d]],
        operations=['Read pinned JPL geometric position vectors; require identical dates',
                    'Construct an orthonormal co-rotating basis at every epoch', 'Connect adjacent samples without forcing closure'])
    attach(e, 'webb-vectors.json'); attach(e, 'sun-vectors.json')
    return save(glb, e)


def build_alpha():
    p = PARAMS['alpha_cen']
    a, eccentricity = p['angular_a_arcsec']/p['parallax_arcsec'], p['e']
    reference = 7001180348760/ C['au_m']
    t = np.linspace(0, 2*np.pi, 1001)
    points = np.column_stack((a*(np.cos(t)-eccentricity), a*np.sqrt(1-eccentricity**2)*np.sin(t), np.zeros_like(t)))
    glb = GLB('Published Alpha Centauri AB relative orbital ellipse')
    e = entry('space3d3-alpha-cen-relative-orbit', 'Alpha Centauri A-B Orbit', p['source'],
        'Pourbaix & Boffin (2016) HARPS+ESO relative orbital solution: angular semimajor axis 17.66 arcsec / parallax 0.743 arcsec gives a = 23.7685 AU, e = 0.524 and P = 79.91 years. The blue ellipse is B’s relative orbit in a frame centered on A; it is not a pair of barycentric trajectories. The authored orbital-plane inspection view exposes the intrinsic ellipse rather than its nearly edge-on sky projection. A and B are location glyphs, with B shown at periastron; stellar diameters are not implied.', 'AU', reference)
    line(glb, 'B relative orbit', points, CYAN)
    marker(glb, 'A', [0, 0, 0], AMBER, radius=reference*.004, label='A')
    marker(glb, 'B at periastron', [a*(1-eccentricity), 0, 0], WHITE, radius=reference*.004, label='B')
    ruler(glb, [-a*(1+eccentricity), 0, 0], [a*(1-eccentricity), 0, 0], [0, -a*1.02, 0],
          f'2a = {2*a:.2f} AU')
    e['presentation'].update(pitch=24, roll=-8)
    e['processing'].update(physical_a_au=a, eccentricity=eccentricity, period_years=p['period_julian_years'],
                           periastron_separation_au=a*(1-eccentricity), apastron_separation_au=a*(1+eccentricity))
    return save(glb, e)


def build_trappist():
    p = PARAMS['trappist']; reference = 18520216392.66/1000/AU_KM
    glb = GLB('Agol et al. seven TRAPPIST-1 circular reference orbits')
    e = entry('space3d3-trappist-orbits', 'TRAPPIST-1 System', p['source'],
        'Seven coplanar circular reference orbits use Agol et al. (2021) semimajor axes, planet radii and 0.1192-solar-radius star. The circular approximation omits their small measured eccentricities; planet phases and the inspection view are authored, not ephemeris. Planet/star radii share the AU orbit scale; thin outline markers keep tiny planets findable. Colors are illustrative and do not assert surface maps, oceans or habitability. The outer orbit’s 0.12378 AU diameter is close to the catalog’s rounded 0.1238 AU.', 'AU', reference)
    star_mat = glb.material('Illustrative red dwarf', color=(.65, .11, .025, 1), emissive=(.7, .10, .02))
    sphere(glb, 'TRAPPIST-1', p['star_radius_solar']*C['solar_radius_km']/AU_KM, star_mat, segments=48, rings=24)
    palette = [(.95,.40,.19),(.94,.62,.28),(.88,.76,.43),(.37,.73,.78),(.37,.66,.90),(.52,.55,.84),(.68,.65,.83)]
    angles = np.radians([145, 225, 15, 70, 260, 195, 335])
    for i, planet in enumerate(p['planets']):
        radius = planet['a_au']; color = palette[i]
        theta = np.linspace(0, 2*np.pi, 481)
        line(glb, planet['name']+' circular reference orbit', np.column_stack((radius*np.cos(theta), radius*np.sin(theta), np.zeros_like(theta))), tuple(c*.65 for c in color))
        point = [radius*math.cos(angles[i]), radius*math.sin(angles[i]), 0]
        m = glb.material(planet['name']+' illustrative planet', color=(*color, 1), emissive=tuple(c*.15 for c in color))
        sphere(glb, planet['name'], 1, m, segments=24, rings=12)
        r = planet['radius_km']/AU_KM
        glb.doc['nodes'][-1].update(scale=[r]*3, translation=point,
                                  extras={'label': planet['name'], 'outline': True, 'sphere': True})
    ruler(glb, [-.06189, 0, 0], [.06189, 0, 0], [0, -.071, 0], '0.12378 AU')
    e['presentation'].update(pitch=30, roll=-14)
    e['processing'].update(planet_count=7, star_radius_solar=p['star_radius_solar'], circular_approximation=True,
        planet_parameters=p['planets'], phase_semantics='Authored positions; no date or dynamical state implied')
    return save(glb, e)


def build_sgr():
    p = PARAMS['sgr_a']; reference = 25400000000/1000
    radius = 2*C['solar_gm_km3_s2']*p['mass_solar']/(C['c_m_s']/1000)**2
    glb = GLB('Schwarzschild reference-horizon scale diagram')
    e = entry('space3d3-sgr-a-horizon', 'Sagittarius A* Event Horizon', p['source'],
        'A Schwarzschild reference horizon calculated as r_s = 2GM/c² from the 2019 GRAVITY noise-model mass of 4.152 million solar masses. Its Euclidean drawing diameter is about 24.52 million km, close to the catalog’s approximate 25.4 million km. This is a mass-based nonrotating reference boundary, not an observed black surface, EHT shadow, accretion disk, or embedding of curved space. Violet great circles and the rim are authored guides to the causal boundary; their thickness is not physical. Spin and mass uncertainty are not modeled.', 'km', reference)
    black = glb.material('Unlit reference horizon interior', color=(.003, .005, .012, 1), double_sided=False)
    sphere(glb, 'Schwarzschild reference horizon', radius, black)
    # Sparse boundary guides stay on the physical sphere, without glowing matter.
    t = np.linspace(0, 2*np.pi, 721)
    for axes, color in [((0,1),(.59,.42,.86)),((0,2),(.22,.24,.42)),((1,2),(.22,.24,.42))]:
        v = np.zeros((len(t),3)); v[:,axes[0]]=radius*np.cos(t);v[:,axes[1]]=radius*np.sin(t)
        line(glb, 'Horizon coordinate great circle', v, color)
    ruler(glb, [-radius,0,0], [radius,0,0], [0,-radius*1.14,0], f'2 r_s = {2*radius/1e6:.2f} million km')
    e['presentation'].update(pitch=15, yaw=18)
    e['processing'].update(mass_solar=p['mass_solar'], schwarzschild_radius_km=radius,
        spin_assumption=0, solar_gm_km3_s2=C['solar_gm_km3_s2'])
    return save(glb, e)


def eht_registration(image):
    """Numerically register the color intensity ridge, without claiming WCS."""
    rgb = np.asarray(image.convert('RGB'), dtype=float)/255
    h, w = rgb.shape[:2]
    # The published horizontal image centers the ring at its image center.
    # Use the central depression to refine the center from the hot-annulus bbox.
    yy, xx = np.mgrid[:h, :w]
    intensity = rgb.mean(axis=2)
    # Fit a circle to angular radial maxima around the approximate dark center.
    cx, cy = w/2, h*.475
    for _ in range(4):
        theta = np.linspace(0, 2*np.pi, 180, endpoint=False)
        radii = np.linspace(h*.10, h*.24, 400)
        x = np.clip((cx+np.cos(theta[:,None])*radii).astype(int),0,w-1)
        y = np.clip((cy+np.sin(theta[:,None])*radii).astype(int),0,h-1)
        peak = intensity[y,x].argmax(1)
        ridge = np.column_stack((x[np.arange(len(theta)),peak],y[np.arange(len(theta)),peak]))
        fit=np.linalg.lstsq(np.column_stack((2*ridge,np.ones(len(ridge)))),np.sum(ridge**2,axis=1),rcond=None)[0]
        cx,cy=fit[:2]
        center=np.array([cx,cy])
    radius = float(np.median(np.linalg.norm(ridge-center,axis=1)))
    return float(cx), float(cy), radius*2


def build_m87():
    image = Image.open(SOURCES/'m87-eht.jpg').convert('RGB')
    cx, cy, pixel_diameter = eht_registration(image)
    p = PARAMS['m87']
    # Small-angle physical diameter at the paper's adopted distance.
    diameter = math.radians(p['ring_diameter_microarcsec']/1e6/3600)*p['distance_mpc']*1e6*PC_KM
    reference = 103000000000000/1000
    glb = GLB('EHT 2017 M87 reconstructed sky image, circular aperture')
    e = entry('space3d3-m87-eht-ring', 'M87* Shadow', p['image'],
        'The real 2017 EHT reconstructed radio sky image (EHT Collaboration; ESO eso1907a), on a flat circular sky-plane aperture. The intensity ridge is registered approximately to the reported 42 ± 3 microarcsec emission-ring diameter at 16.8 Mpc (~105.6 billion km). The catalog’s ~103 billion km refers to this ring/shadow scale, not the event horizon. A feathered aperture cuts the outskirts at 1.24 ring diameters, preserving the intensity ridge. No 3D plasma, accretion geometry, or solid hole is inferred; rotation exposes a flat image. Orange is the published radio-intensity color mapping, not visible-light fire.', 'km', reference)
    e.update(author='EHT Collaboration; registered image aperture assembled by Universe Scales',
        representation='observed-radio-image', license='CC-BY-4.0',
        license_url='https://creativecommons.org/licenses/by/4.0/', license_files=['licenses/CC-BY-4.0.txt', 'licenses/space3d3-rights.md'],
        basis_url=p['source'], basis_label='2019 EHT measured ring scale')
    im = image.copy(); im.thumbnail((2048,2048),Image.Resampling.LANCZOS)
    buf=io.BytesIO();im.save(buf,'JPEG',quality=94)
    tex=glb.texture(buf.getvalue(),'image/jpeg')
    mat=glb.material('EHT observed radio-intensity image',texture=tex,double_sided=True,blend=True)
    glb.doc.setdefault('extensionsUsed',[]).append('KHR_materials_unlit')
    glb.doc['materials'][mat]['extensions']={'KHR_materials_unlit':{}}
    # Concentric rings feather only the crop's opacity outside the intensity ridge.
    theta=np.linspace(0,2*np.pi,257)
    radii=[.45,.50,.53,.56,.59,.62]
    alpha=[1,1,1,.75,.3,0]
    normalized=np.vstack(([0.,0.],*[np.column_stack((np.cos(theta),np.sin(theta)))*r for r in radii]))
    points=np.column_stack((normalized*diameter,np.zeros(len(normalized))))
    uv=np.column_stack(((cx+normalized[:,0]*pixel_diameter)/image.width,
                        (cy-normalized[:,1]*pixel_diameter)/image.height))
    faces=[np.column_stack((np.zeros(256,dtype=int),np.arange(1,257),np.arange(2,258))).ravel()]
    faces.append(grid_indices(len(radii),257)+1)
    colors=np.ones((len(points),4));colors[1:,3]=np.repeat(alpha,257)
    glb.mesh_node('M87 EHT sky plane',[glb.primitive(points,np.concatenate(faces),mat,normals=np.tile([0,0,1.],(len(points),1)),uvs=uv,colors=colors)])
    ruler(glb,[-diameter/2,-diameter*.59,1],[diameter/2,-diameter*.59,1],[0,-diameter*.035,0],'42 microarcsec')
    e['processing'].update(angular_ring_diameter_microarcsec=42, adopted_distance_mpc=16.8,
        physical_ring_diameter_km=diameter, image_registration_center_px=[cx,cy],
        image_registration_ridge_diameter_px=pixel_diameter, aperture_ring_diameters=1.24,
        operations=['Retain actual EHT color image; no generated replacement pixels',
                    'Fit approximate intensity ridge in the published JPEG, not a calibrated FITS/WCS image',
                    'Feather the circular aperture with vertex alpha beyond the intensity ridge; preserve square pixel aspect ratio'])
    attach(e,'m87-eht.jpg')
    return save(glb,e)


def wave_clouds():
    data=json.loads((SOURCES/'radcliffe-clouds.json').read_text())
    return data['clouds'],np.array([c['xyz_pc'] for c in data['clouds']],dtype=float)


def cloud_points(glb, points, name='Radcliffe cloud locations'):
    # Observed point positions only: no synthetic gas-density field or stars.
    colors=np.column_stack((np.linspace(.2,.95,len(points)),np.full(len(points),.58),np.linspace(.95,.25,len(points))))
    mat=glb.material(name,color=(1,1,1,1))
    glb.doc.setdefault('extensionsUsed',[])
    if 'KHR_materials_unlit' not in glb.doc['extensionsUsed']: glb.doc['extensionsUsed'].append('KHR_materials_unlit')
    glb.doc['materials'][mat]['extensions']={'KHR_materials_unlit':{}}
    a={'POSITION':glb._accessor(points.astype('<f4'),5126,'VEC3',34962,True),
       'COLOR_0':glb._accessor(colors.astype('<f4'),5126,'VEC3',34962)}
    glb.mesh_node(name,[{'mode':0,'attributes':a,'material':mat}])
    glb.doc['nodes'][-1]['extras']={'softPoints':True,'pointSize':{'max':7,'perPixel':.014}}


def build_wave():
    clouds,p=wave_clouds()
    # Rotate around north only, align the observed principal in-plane direction.
    _,_,vh=np.linalg.svd(p[:,:2]-p[:,:2].mean(0),full_matrices=False)
    long=vh[0]
    if long[1]<0:long=-long
    cross=np.array([long[1],-long[0]])
    view=np.column_stack((p[:,:2]@long,p[:,2],p[:,:2]@cross))
    reference=83254428158711040000/1000/PC_KM
    glb=GLB('Alves et al. 2020 selected 3D Radcliffe cloud positions')
    e=entry('space3d3-radcliffe-clouds','Radcliffe Wave','https://doi.org/10.1038/s41586-019-1874-z',
        'All 141 measured cloud locations selected as Radcliffe Wave members in Alves et al. (2020), extracted from the authors’ interactive supplement. Heliocentric Galactic Cartesian parsecs remain isotropic: no vertical exaggeration, fitted sine wave, synthetic cloud fill, or invented connecting tube. Colors and finite point sprites are authored identification aids, not gas extent, density, or individual stars. The inspection frame aligns the observed long axis horizontally with Galactic north up. The Sun is a location glyph. The 500 pc bar is a physical ruler; the catalog’s ~8,800 ly is an approximate chain length.','pc',reference)
    e.update(representation='catalog-position-diagram',author='João Alves, Catherine Zucker, Alyssa Goodman and collaborators; CC0 cloud data; assembly by Universe Scales')
    cloud_points(glb,view)
    marker(glb,'Sun',[0,0,0],AMBER,radius=reference*.004)
    glb.label_node('Sun name',[0,-reference*.06,0],'Sun')
    # Only named parts, no caveat plaques in the model.
    for name in ['Orion','Perseus','CygnusX']:
        indices=[i for i,c in enumerate(clouds) if c['name']==name]
        if indices:
            center=np.median(view[indices],axis=0)
            label_pos=center+[0,reference*.065,0]
            line(glb,name+' callout',[center,label_pos],(.24,.39,.50))
            glb.label_node(name,label_pos,'Cygnus X' if name=='CygnusX' else name)
    low=view.min(0)
    ruler(glb,[low[0],low[1]-80,0],[low[0]+500,low[1]-80,0],[0,-35,0],'500 pc')
    e['presentation'].update(pitch=18,roll=-6)
    e['processing'].update(cloud_count=len(clouds),galactic_in_plane_long_axis=long.tolist(),vertical_exaggeration=1,
        view_matrix_rows=[[*long,0],[0,0,1],[*cross,0]],
        operations=['Extract only the 141 selected observed cloud points', 'Swap Plotly x/y into the figure’s explicitly named Galactic X/Y',
                    'Rigidly rotate only the Galactic plane; retain actual Z heights'])
    attach(e,'radcliffe-clouds.json');attach(e,'radcliffe-data-rights.json')
    return save(glb,e)


def build_gc():
    glb=GLB('GRAVITY Sun to Galactic Center ruler with measured local cloud context')
    reference=PARAMS['sgr_a']['galactic_center_distance_pc']
    e=entry('space3d3-galactic-center-distance','Sun-Galactic Center Distance',PARAMS['sgr_a']['source'],
        'A Sun-to-Galactic-center measurement diagram spanning the 2019 GRAVITY geometric distance of 8,178 pc. The only local cloud context is the same 141 measured Alves et al. (2020) Radcliffe cloud locations, drawn in true heliocentric Galactic Cartesian parsecs at the same scale. X points toward the Galactic Center; Galactic north is up. Endpoint glyphs are location aids, not the dimensions of the Sun or black hole. No Milky Way outline, star density or galactic bar is invented.','pc',reference)
    _,p=wave_clouds()
    cloud_points(glb,p[:,[0,2,1]]*[1,1,-1])
    marker(glb,'Sun',[0,0,0],AMBER,radius=reference*.004,label='Sun')
    marker(glb,'Galactic Center',[reference,0,0],WHITE,radius=reference*.004,label='Galactic Center')
    line(glb,'Sun-center baseline',[[0,0,0],[reference,0,0]],(.28,.52,.69))
    ruler(glb,[0,0,0],[reference,0,0],[0,-reference*.13,0],'8,178 pc',ticks=8)
    e['presentation'].update(pitch=20,yaw=-10)
    e['processing'].update(center_distance_pc=reference,cloud_count=141,vertical_exaggeration=1)
    attach(e,'radcliffe-clouds.json');attach(e,'radcliffe-data-rights.json')
    return save(glb,e)


def build_light_distance(which):
    config={
        'light-year':('Light-Year',1.,'1 light-year','c × 1 Julian yr',12,'https://iauarchive.eso.org/public/themes/measuring/'),
        'barnard':("Barnard's Star Distance",5.97,'5.97 light-years',"Barnard's Star",6,PARAMS['nearby']['source']),
        'sirius':('Distance to Sirius',8.6,'8.6 light-years','Sirius',8,PARAMS['nearby']['source'])}[which]
    item,distance,text,target,ticks,source=config
    catalog={'light-year':1.,'barnard':5.9639572,'sirius':8.6018}[which]
    if which=='barnard': catalog=5.6413389734952056e16/(LY_KM*1000)
    if which=='sirius': catalog=8.136228206419488e16/(LY_KM*1000)
    glb=GLB('Physical light-distance measurement ruler')
    e=entry('space3d3-'+which+'-distance',item,source,
        ('A straight one-light-year ruler, derived exactly from c = 299,792,458 m/s and one Julian year = 365.25 days of 86,400 s. Twelve equal marks divide the distance into twelfths of a Julian year, not calendar months. Endpoints and the line are authored measurement aids, not a wave, photon size, or an observed trajectory.' if which=='light-year' else
         f'A heliocentric distance ruler using NASA’s approximate {distance:g}-light-year distance to {target}. The endpoints mark locations and do not represent stellar radii or luminosity; the orientation is authored and is not a sky direction or 3D astrometric coordinate reconstruction. The point of the true-scale ruler is the separation between the systems. Subdivisions are equal fractions of that distance.'),'ly',catalog)
    line(glb,'Distance baseline',[[0,0,0],[distance,0,0]],CYAN)
    marker(glb,'Start',[0,0,0],AMBER,radius=catalog*.004,label='Sun' if which!='light-year' else None)
    marker(glb,'End',[distance,0,0],WHITE,radius=catalog*.004,label=None if which=='light-year' else target)
    ruler(glb,[0,0,0],[distance,0,0],[0,-catalog*.15,0],text,ticks=ticks)
    if which=='light-year': glb.label_node('Light-time',[distance/2,catalog*.06,0],target)
    e['presentation'].update(yaw=12)
    e['processing'].update(distance_ly=distance,exact_light_year_m=int(LY_KM*1000),subdivision_count=ticks,
                           orientation_semantics='Authored measurement axis, no celestial direction')
    return save(glb,e)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only',help='One target: iss, geo, webb, Mercury, Jupiter, Neptune, alpha, trappist, sgr, m87, wave, gc, light-year, barnard, sirius')
    args=parser.parse_args()
    pinned('parameters.json')
    jobs={'iss':build_iss,'geo':build_geo,'webb':build_webb,
          **{name:(lambda n=name:build_planet(n)) for name in ['Mercury','Jupiter','Neptune']},
          'alpha':build_alpha,'trappist':build_trappist,'sgr':build_sgr,'m87':build_m87,
          'wave':build_wave,'gc':build_gc,
          **{name:(lambda n=name:build_light_distance(n)) for name in ['light-year','barnard','sirius']}}
    if args.only and args.only not in jobs: parser.error('Unknown target')
    for name,build in jobs.items():
        if args.only is None or name==args.only: build()


if __name__=='__main__':
    main()
