#!/usr/bin/env python3
"""Offline PDB coordinates -> calibrated, chain-colored, decoder-free GLBs.

One model unit is one nanometre. Coordinates are never stretched to the item
value. Surface meshes are smooth unions of display spheres around heavy atoms
(or C-alpha for the coarse NPC scaffold), not experimental density isosurfaces,
solvent-accessible surfaces, or literal hard molecular boundaries.
"""
import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes

from fetch_model_assets import inspect_glb, read_glb
from geo_glb_common import GLB
from prepare_bio3d_sources import SOURCE, ROOT
from render_glb_preview import accessor

HANDOFF = ROOT / 'handoff/bio3d'
PALETTE = np.array([[.17, .63, .69], [.90, .49, .26], [.54, .49, .79],
                    [.34, .70, .48], [.85, .68, .27], [.43, .66, .86]])
SPECS = {
    'fullerene': ('5ET3', 'Buckminsterfullerene', .71),
    'nucleosome': ('1KX5', 'Nucleosome', 11),
    'spike': ('6VXX', 'SARS-CoV-2 Spike', 20),
    'actin': ('6BNO', 'Actin Filament', 7),
    'microtubule': ('6DPU', 'Microtubule', 25),
    'ribosome': ('4V88', 'Ribosome', 30),
    'nuclear-pore': ('7R5K', 'Nuclear Pore Complex', 120),
    'tmv': ('2TMV', 'Tobacco Mosaic Virus', 300),
}
NOTES = {
    'fullerene': 'Experimental C60 cage from the 60C ligand in PDB 5ET3. The thin atoms and bonds mark nuclear positions, not van der Waals radii; the listed 0.71 nm is a nucleus-to-nucleus cage diameter. The surrounding binding peptide is omitted.',
    'nucleosome': 'PDB 1KX5 nucleosome core particle: both 147-base DNA strands and all eight histones, including resolved histone tails. DNA is amber; histones are colored by chain. The approximate 11 nm value describes the DNA-wrapped disc; resolved tails extend beyond it. Unresolved residues, water and ions are omitted.',
    'spike': 'PDB 6VXX closed prefusion spike ectodomain trimer, colored by protein chain, with only deposited glycan residues shown in gold. This engineered soluble construct resolves about 16 nm of the roughly 20 nm membrane-projecting spike; missing flexible stalk, membrane anchor and unresolved glycans are not invented. It is not the whole virus.',
    'actin': 'A 7 nm-long, flat-cut window through the experimental rabbit actin lattice of PDB 6BNO. Alternating deposited subunits have contrasting colors. Both ends are visualization cuts, not filament ends. The listed 7 nm is an approximate filament diameter; the irregular structural envelope can be wider. This short window does not show a complete helical crossover.',
    'microtubule': 'A 20 nm-long, flat-cut window through a reconstructed 14-protofilament GMPCPP microtubule lattice from PDB 6DPU. Alpha tubulin is teal and beta tubulin violet. Neighboring-protofilament and longitudinal transforms are fitted to matching deposited C-alpha coordinates. The seam is inferred; seam-specific conformations and disordered tails are unresolved. The generic 25 nm diameter is approximate; this in-vitro 14-protofilament example is wider than a common 13-protofilament cellular microtubule.',
    'ribosome': 'Author-defined biological assembly 1 of PDB 4V88: one yeast 80S ribosome, not the two particles in the asymmetric unit. Ribosomal RNA is gold; protein chains use a contrasting palette. Includes the deposited Stm1 protein; unmodeled residues, water and ions are omitted. Native coordinates are preserved, independently of the approximate 30 nm catalog value.',
    'nuclear-pore': 'Full eightfold assembly of PDB 7R5K, a constricted human nuclear pore scaffold modeled integratively using cryo-electron tomography and predicted protein structures. A deliberately coarse C-alpha envelope, colored by nucleoporin entity, preserves the central channel and deposited eightfold transforms. Disordered transport barrier, nuclear membranes and unresolved basket/filaments are absent. It is not an atomically resolved complete pore.',
    'tmv': 'A 300 nm-long flat-cut lattice reconstruction from PDB 2TMV protein and RNA coordinates and its deposited helical symmetry. The coat is teal and the RNA amber. The central channel and repeating surface follow the structural coordinates. This representative rod length uses repeated structural subunits; the two end planes are authored cuts, not experimentally reconstructed virion ends. The smooth display surface does not resolve individual atoms.',
}


def load(pdb):
    with np.load(SOURCE / f'{pdb}.npz', allow_pickle=False) as archive:
        data = {k: archive[k] for k in archive.files}
    return data, json.loads((SOURCE / f'{pdb}.json').read_text())


def subset(data, mask):
    return {k: v[mask] for k, v in data.items()}


def operation(op):
    m = np.eye(4)
    m[:3, :3] = [[float(op[f'matrix[{i}][{j}]']) for j in range(1, 4)] for i in range(1, 4)]
    m[:3, 3] = [float(op[f'vector[{i}]']) for i in range(1, 4)]
    return m


def assembly(data, metadata, assembly_id='1'):
    """Apply deposited, simple assembly operation lists; reject unsupported syntax."""
    pieces = []
    operations = {o['id']: operation(o) for o in metadata['operations']}
    for gen in metadata['assembly_gen']:
        if gen['assembly_id'] != assembly_id:
            continue
        mask = np.isin(data['chain'], gen['asym_id_list'].replace('\n', '').split(','))
        expression = gen['oper_expression']
        if any(c in expression for c in '()-'):
            raise ValueError('Use explicit helical reconstruction for operation products/ranges')
        for identifier in expression.split(','):
            part = subset(data, mask)
            m = operations[identifier]
            part['xyz'] = part['xyz'] @ m[:3, :3].T + m[:3, 3]
            pieces.append(part)
    if not pieces:
        raise ValueError('No assembly coordinates')
    return {k: np.concatenate([p[k] for p in pieces]) for k in data}


def rigid_fit(a, b):
    """Least-squares proper rigid transform; no scale or shear."""
    ca, cb = a.mean(0), b.mean(0)
    u, _, vt = np.linalg.svd((a-ca).T @ (b-cb))
    d = np.eye(3); d[2, 2] = np.linalg.det(vt.T @ u.T)
    r = vt.T @ d @ u.T
    m = np.eye(4); m[:3, :3] = r; m[:3, 3] = cb - r @ ca
    rmsd = float(np.sqrt(np.mean(np.sum((a @ r.T + m[:3, 3] - b)**2, axis=1))))
    return m, rmsd


def microtubule(data):
    def fit_chains(a, b):
        mask_a = (data['chain'] == a) & (data['atom'] == 'CA')
        mask_b = (data['chain'] == b) & (data['atom'] == 'CA')
        if not np.array_equal(data['sequence'][mask_a], data['sequence'][mask_b]):
            raise ValueError('Tubulin correspondences differ')
        return rigid_fit(data['xyz'][mask_a], data['xyz'][mask_b])
    lateral, error = fit_chains('A', 'C')
    longitudinal, error2 = fit_chains('A', 'K')
    if max(error, error2) > 1:
        raise ValueError('Inconsistent tubulin rigid transforms')
    base = subset(data, np.isin(data['chain'], ['A', 'B']))
    points, colors = [], []
    for pf in range(14):
        for turn in range(-4, 5):
            m = np.linalg.matrix_power(lateral, pf) @ np.linalg.matrix_power(longitudinal, turn)
            xyz = base['xyz'] @ m[:3, :3].T + m[:3, 3]
            # Center on the deposited dimer; discard remote copies before meshing.
            xyz[:, 2] -= float(base['xyz'][:, 2].mean())
            keep = np.abs(xyz[:, 2]) < 108
            points.append(xyz[keep])
            colors.append(np.where((base['entity'][keep] == '1')[:, None], PALETTE[0], PALETTE[2]))
    xyz = np.concatenate(points)
    # Keep native z as the filament axis. Translation has no effect on dimensions.
    xyz[:, :2] -= (xyz[:, :2].min(0)+xyz[:, :2].max(0))/2
    return xyz, np.concatenate(colors), {'protofilaments': 14, 'fit_rmsd_A': [error, error2],
            'lateral_transform': lateral.tolist(), 'longitudinal_transform': longitudinal.tolist()}


def tmv(data, meta):
    # The two consecutive operations determine the generator, including handedness.
    ops = {o['id']: operation(o) for o in meta['operations']}
    step = ops['26'] @ np.linalg.inv(ops['25'])
    rise = float(step[2, 3])
    if not 1.3 < rise < 1.5:
        raise ValueError('Unexpected TMV helical rise')
    copies = math.ceil(3000 / rise) + 40
    points, colors = [], []
    base_color = np.tile(PALETTE[0], (len(data['xyz']), 1))
    base_color[np.isin(data['residue'], ['A', 'C', 'G', 'U'])] = PALETTE[4]
    for index in range(-copies//2, copies//2 + 1):
        m = np.linalg.matrix_power(step, index)
        xyz = data['xyz'] @ m[:3, :3].T + m[:3, 3]
        keep = np.abs(xyz[:, 2]) < 1508
        points.append(xyz[keep]); colors.append(base_color[keep])
    return np.concatenate(points), np.concatenate(colors), {'rise_A': rise,
            'twist_degrees': math.degrees(math.atan2(step[1, 0], step[0, 0])),
            'window_length_nm': 300}


def surface(xyz, colors, spacing, radius, smooth, clip=None):
    """Smooth display envelope, retaining native dimensions and closed cut planes."""
    low = xyz.min(0) - radius - 3*spacing
    high = xyz.max(0) + radius + 3*spacing
    if clip is not None:
        low[2], high[2] = -clip-3*spacing, clip+3*spacing
    shape = np.ceil((high-low) / spacing).astype(int)+1
    tree = cKDTree(xyz)
    field = np.empty(shape, dtype=np.float32)
    yz = np.stack(np.meshgrid(np.arange(shape[1]), np.arange(shape[2]), indexing='ij'), -1).reshape(-1, 2)
    for x in range(shape[0]):
        grid = np.column_stack((np.full(len(yz), x), yz)) * spacing + low
        distance = tree.query(grid, workers=1)[0]
        field[x] = (radius-distance).reshape(shape[1:])
    field = gaussian_filter(field, smooth / spacing)
    if clip is not None:
        z = np.arange(shape[2])*spacing+low[2]
        field = np.minimum(field, (clip-np.abs(z))[None, None, :])
    verts, faces, _, _ = marching_cubes(field, 0, spacing=(spacing,)*3, allow_degenerate=False,
                                       gradient_direction='descent')
    # skimage's descent convention uses left-handed winding; glTF needs
    # counterclockwise front faces. Our field is positive inside the solid.
    faces = faces[:, [0, 2, 1]]
    verts += low
    # marching_cubes normals are replaced after simplification.
    nearest = tree.query(verts, workers=1)[1]
    return verts, faces, colors[nearest]


def normals(verts, faces):
    n = np.zeros_like(verts)
    cross = np.cross(verts[faces[:, 1]]-verts[faces[:, 0]], verts[faces[:, 2]]-verts[faces[:, 0]])
    for i in range(3):
        np.add.at(n, faces[:, i], cross)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    return n


def clean_mesh(verts, faces):
    """Drop collapsed, opposing duplicate faces left by lossy simplification.

    Closed tiny cavities can collapse to two coincident, oppositely wound
    triangles. Those have no enclosed volume and their normals cancel exactly.
    """
    _, inverse, counts = np.unique(np.sort(faces, axis=1), axis=0,
                                    return_inverse=True, return_counts=True)
    faces = faces[counts[inverse] == 1]
    area = np.linalg.norm(np.cross(verts[faces[:, 1]]-verts[faces[:, 0]],
                                   verts[faces[:, 2]]-verts[faces[:, 0]]), axis=1)
    faces = faces[area > 1e-10]
    used, inverse = np.unique(faces, return_inverse=True)
    return verts[used], inverse.reshape(-1, 3)


def simplify(verts, faces, target):
    if len(faces) <= target:
        return verts, faces
    with tempfile.TemporaryDirectory(prefix='bio3d-mesh-') as temp:
        tmp = Path(temp)
        g = GLB(); m = g.material('surface')
        g.mesh_node('surface', [g.primitive(verts, faces.ravel(), m)])
        g.write(tmp/'input.glb')
        # Calling a cached CLI directly avoids npm writing into a read-only
        # home cache in the worktree sandbox. It still writes plain glTF.
        cached = sorted((Path.home()/'.npm/_npx').glob('*/node_modules/@gltf-transform/cli/bin/cli.js'))
        command = (['node', str(cached[0])] if cached else
                   ['npx', '--cache', '/tmp/bio3d-npm-cache', '@gltf-transform/cli@4.5.0'])
        subprocess.run(command + ['weld', str(tmp/'input.glb'), str(tmp/'weld.glb')],
                       check=True, capture_output=True)
        subprocess.run(command + ['simplify', str(tmp/'weld.glb'), str(tmp/'small.glb'),
                                 '--ratio', str(target/len(faces)), '--error', '0.01'],
                       check=True, capture_output=True)
        doc, blob = read_glb((tmp/'small.glb').read_bytes())
        primitive = doc['meshes'][0]['primitives'][0]
        return accessor(doc, blob, primitive['attributes']['POSITION']).astype(float), accessor(
            doc, blob, primitive['indices']).reshape(-1, 3).astype(int)


def chain_colors(data, key):
    chains = list(dict.fromkeys(data['chain']))
    # Gold uniquely identifies nucleic acid in the nucleosome and ribosome.
    palette = np.delete(PALETTE, 4, axis=0) if key in ('nucleosome', 'ribosome') else PALETTE
    table = {c: palette[i % len(palette)] for i, c in enumerate(chains)}
    color = np.array([table[c] for c in data['chain']])
    if key in ('nucleosome', 'ribosome'):
        color[np.isin(data['residue'], ['DA', 'DC', 'DG', 'DT', 'A', 'C', 'G', 'U'])] = PALETTE[4]
    if key == 'spike':
        color[~np.isin(data['chain'], ['A', 'B', 'C'])] = PALETTE[4]
    if key == 'nuclear-pore':
        color = PALETTE[(data['entity'].astype(int)-1) % len(PALETTE)]
    return color


def cylinder(a, b, radius, sides=10):
    axis = b-a; axis /= np.linalg.norm(axis)
    u = np.cross(axis, [1, 0, 0] if abs(axis[0]) < .8 else [0, 1, 0]); u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    theta = np.arange(sides)*2*np.pi/sides
    ring = radius*(np.cos(theta)[:, None]*u+np.sin(theta)[:, None]*v)
    verts = np.concatenate((a+ring, b+ring, a[None], b[None]))
    faces = []
    for i in range(sides):
        j = (i+1)%sides
        faces.extend([(i, j, sides+i), (j, sides+j, sides+i),
                      (2*sides, j, i), (2*sides+1, sides+i, sides+j)])
    return verts, np.array(faces)


def fullerene(data):
    xyz = data['xyz'].astype(float); xyz -= xyz.mean(0)
    pairs = sorted(cKDTree(xyz).query_pairs(1.6))
    degree = np.bincount(np.array(pairs).ravel(), minlength=len(xyz))
    if len(xyz) != 60 or len(pairs) != 90 or not np.all(degree == 3):
        raise ValueError('C60 topology is not a trivalent 60-vertex cage')
    # Small geometry markers, not atom radii. Cylinders meet at actual nuclei.
    vertices, triangles = [], []
    for a, b in pairs:
        v, f = cylinder(xyz[a], xyz[b], .11)
        triangles.append(f+sum(len(vv) for vv in vertices)); vertices.append(v)
    verts = np.concatenate(vertices); faces = np.concatenate(triangles)
    colors = np.tile([.31, .68, .75], (len(verts), 1))
    return verts, faces, colors, {'atoms': 60, 'bonds': 90,
            'nuclear_cage_diameter_nm': float(np.max(np.linalg.norm(xyz[:, None]-xyz[None, :], axis=2)))/10}


def build(key, output):
    pdb, item, reference_nm = SPECS[key]
    data, meta = load(pdb)
    provenance = {}
    if key == 'fullerene':
        verts, faces, colors, provenance = fullerene(data)
    else:
        # Polymer coordinates; spike additionally retains deposited glycan atoms.
        if key != 'spike':
            data = subset(data, data['sequence'] != '.')
        if key == 'ribosome' or key == 'nuclear-pore':
            data = assembly(data, meta)
        colors = chain_colors(data, key)
        xyz = data['xyz'].astype(float)
        clip = None
        if key == 'microtubule':
            xyz, colors, provenance = microtubule(data); clip = 100
        elif key == 'tmv':
            xyz, colors, provenance = tmv(data, meta); clip = 1500
        else:
            xyz -= (xyz.min(0)+xyz.max(0))/2
        if key == 'actin':
            clip = 35
            mask = np.abs(xyz[:, 2]) <= 43
            xyz, colors = xyz[mask], colors[mask]
        spacing, radius, smooth = {
            'nucleosome': (1.2, 2.0, .8), 'spike': (1.5, 2.0, .9),
            'actin': (1.1, 2.0, .8), 'microtubule': (2, 3.0, 1.2),
            'ribosome': (2.6, 2.8, 1.4), 'nuclear-pore': (6, 7.5, 3.5),
            'tmv': (3.5, 2.8, 1.4),
        }[key]
        verts, faces, _ = surface(xyz, colors, spacing, radius, smooth, clip)
        verts, faces = simplify(verts, faces, 55000)
        verts, faces = clean_mesh(verts, faces)
        colors = colors[cKDTree(xyz).query(verts)[1]]
        provenance.update({'surface_grid_A': spacing, 'display_sphere_radius_A': radius,
                           'surface_smoothing_A': smooth, 'assembled_atoms': len(xyz)})
    # Rigid axis permutation only: filament/spike axis becomes vertical.
    if key in ('actin', 'microtubule', 'spike', 'tmv'):
        verts = verts[:, [0, 2, 1]] * [1, 1, -1]
    verts /= 10  # Angstrom -> nanometre, never a fitted bounding-box scale.
    g = GLB('Universe Scales PDB structural surface builder')
    material = g.material('Chain colors (illustrative)', rough=.72, double_sided=False)
    g.mesh_node(item, [g.primitive(verts, faces.ravel(), material, normals=normals(verts, faces),
                                 colors=colors, rgba8=True)])
    model_id = f'pdb-{pdb.lower()}-{key}'
    path = output / f'{model_id}.glb'
    g.write(path)
    presentation = {'reference_size': reference_nm, 'yaw': -18, 'pitch': 12,
                    'roughness': .72}
    framing = {'nucleosome': 1.2, 'actin': 1.3, 'microtubule': 1.3,
               'nuclear-pore': 1.3, 'fullerene': 1.06, 'ribosome': 1.06}
    if key in framing:
        presentation.update(layout_width_factor=framing[key], focus_scale_factor=framing[key])
    labels = {'actin': 'Actin Filament · cut segment',
              'microtubule': 'Microtubule · 14-protofilament segment',
              'spike': 'SARS-CoV-2 Spike · resolved ectodomain',
              'ribosome': 'Ribosome · yeast 80S',
              'nuclear-pore': 'Nuclear Pore Complex · constricted scaffold',
              'tmv': 'Tobacco Mosaic Virus · lattice reconstruction'}
    if key == 'nucleosome':
        presentation.update(pitch=42, yaw=-15, roll=15)
    if key == 'nuclear-pore':
        presentation.update(pitch=-30, yaw=15)
    if key == 'microtubule':
        presentation.update(pitch=28, yaw=15)
    if key == 'tmv':
        presentation.update(pitch=10, yaw=0, roll=-20)
    if key == 'spike':
        presentation.update(pitch=8, yaw=-20)
    entry = {'id': model_id, 'name': item, 'source': f'https://www.rcsb.org/structure/{pdb}',
             'author': ', '.join(meta['citation']['rcsb_authors']),
             'license': 'CC0-1.0', 'license_url': 'https://www.wwpdb.org/about/usage-policies',
             'license_files': ['licenses/CC0-1.0.txt'], 'matches': {'length': [item]},
             'geometry': 'mesh', 'representation': 'structural_model',
             'basis_url': 'https://doi.org/' + (meta['citation'].get('pdbx_database_id_DOI')
                                                          or '10.1126/science.1212642'),
             'basis_label': f'PDB {pdb} structure paper', 'link_label': f'PDB {pdb} coordinates',
             'presentation': presentation, 'note': NOTES[key],
             'provenance': f'content/visualizations/models/sources/{model_id}.md',
             'processing': {'builder': 'scripts/build_bio3d_models.py', 'coordinate_unit': 'nm',
                            'source_coordinate_unit': 'angstrom', 'pdb': pdb,
                            'source_sha256': meta['source_sha256'], **provenance},
             'src': f'content/visualizations/models/{model_id}.glb',
             'volume_semantics': 'not_a_volume_measurement', 'closed_volume_checked': False,
             **inspect_glb(path.read_bytes())}
    if key in labels:
        entry['display_label'] = labels[key]
    HANDOFF.mkdir(parents=True, exist_ok=True)
    (HANDOFF / f'{model_id}.entry.json').write_text(json.dumps(entry, indent=2)+'\n')
    print(json.dumps({'id': model_id, 'bytes': path.stat().st_size, 'triangles': len(faces),
                      'extent_nm': np.ptp(verts, axis=0).tolist()}), flush=True)
    return entry


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--models', nargs='+', choices=SPECS, default=list(SPECS))
    p.add_argument('--output-dir', type=Path, default=ROOT/'content/visualizations/models')
    args = p.parse_args(); args.output_dir.mkdir(parents=True, exist_ok=True)
    for key in args.models:
        build(key, args.output_dir)


if __name__ == '__main__':
    main()
