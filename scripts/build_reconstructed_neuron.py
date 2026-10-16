#!/usr/bin/env python3
"""Offline, uncropped NeuroMorpho NMO_109111 -> smooth, radius-faithful GLB.

The bundled SWC is a comment-stripped derivative of the downloaded standardized
file. All coordinates, radii, parents and types are unchanged. Soma outline and
rigid alignment are extracted once from the original Neurolucida ASC.
"""
import argparse
import gzip
import json
import math
from pathlib import Path

import numpy as np

from build_neuron_model import read_swc
from fetch_model_assets import inspect_glb, write_json
from geo_glb_common import GLB, pack_glb

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'content/visualizations/models/sources/neuron'
MODEL_ID = 'neuromorpho-feldmeyer-neuron-109111'
SPAN_UM = 800
POSITION_ERROR_UM = 0.35
RADIUS_ERROR_UM = 0.08
SIDES = 6


def read_source(source=SOURCE):
    # Reuse the validating SWC parser without requiring a temporary file.
    import tempfile
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / 'cell.swc'
        path.write_bytes(gzip.decompress((source / 'BC140212B_21.swc.gz').read_bytes()))
        nodes, soma = read_swc(path)
    # A cycle or detached component cannot be assigned a propagation distance.
    children = {key: [] for key in nodes}
    for node in nodes.values():
        if node['parent'] >= 0:
            children[node['parent']].append(node['id'])
    distance = {soma['id']: 0.0}
    stack = [soma['id']]
    while stack:
        parent = stack.pop()
        for child in children[parent]:
            if child in distance:
                raise ValueError('SWC contains a cycle')
            a, b = nodes[parent], nodes[child]
            # Axon starts at its traced root, rather than the artificial
            # soma-center connector added by SWC standardization.
            start = 0 if b['type'] == 2 and a['type'] != 2 else distance[parent]
            length = math.dist(a['xyz'], b['xyz']) if a['type'] != 1 else 0
            distance[child] = start + length
            stack.append(child)
    if len(distance) != len(nodes):
        raise ValueError('SWC has a disconnected cycle')
    return nodes, soma, children, distance


def simplify_indices(points, radii, distances, position_error=POSITION_ERROR_UM,
                     radius_error=RADIUS_ERROR_UM):
    """Bound both 3D centerline and radius error, preserving branch endpoints.

    Parameters use original path distances, so the resulting interpolation
    retains original conduction distances even across simplified bends.
    """
    keep = {0, len(points) - 1}
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        length = distances[b] - distances[a]
        t = ((distances[a+1:b] - distances[a]) / length if length > 1e-10
             else np.linspace(0, 1, b-a+1)[1:-1])
        expected = points[a] + t[:, None] * (points[b] - points[a])
        errors = np.linalg.norm(points[a+1:b] - expected, axis=1) / position_error
        radial = np.abs(radii[a+1:b] - (radii[a] + t * (radii[b] - radii[a]))) / radius_error
        errors = np.maximum(errors, radial)
        i = int(np.argmax(errors)) + a + 1
        if errors[i-a-1] > 1:
            keep.add(i)
            stack.extend(((a, i), (i, b)))
    return np.array(sorted(keep))


def branches(nodes, soma, children, distance):
    for node_id, node in nodes.items():
        if node['type'] not in (2, 3, 4):
            continue
        parent = nodes[node['parent']]
        if parent['type'] == node['type'] and len(children[parent['id']]) == 1:
            continue
        path = [parent['id'], node_id]
        tip = node_id
        while len(children[tip]) == 1:
            child = children[tip][0]
            if nodes[child]['type'] != node['type']:
                break
            path.append(child)
            tip = child
        points = np.array([nodes[key]['xyz'] for key in path])
        radii = np.array([nodes[key]['radius'] for key in path])
        if parent['type'] == 1:
            radii[0] = radii[1]
        # Geometry may include soma connector, but pulse excludes it.
        distances = np.array([distance[key] for key in path])
        if parent['type'] == 1:
            distances[0] = -math.dist(points[0], points[1])
        keep = simplify_indices(points, radii, distances)
        yield node['type'], points[keep], radii[keep], distances[keep], path


def tube(points, radii, distances, sides=SIDES):
    """Continuous smooth-normal tube, with transported frames (no cone seams)."""
    # Subdivide long edges for a continuously moving, smoothly interpolated pulse.
    p, r, d = [], [], []
    for i in range(len(points)-1):
        steps = max(1, math.ceil(math.dist(points[i], points[i+1]) / 10))
        for t in np.arange(steps) / steps:
            p.append(points[i] * (1-t) + points[i+1] * t)
            r.append(radii[i] * (1-t) + radii[i+1] * t)
            d.append(distances[i] * (1-t) + distances[i+1] * t)
    p.append(points[-1]); r.append(radii[-1]); d.append(distances[-1])
    p, r, d = np.array(p), np.array(r), np.array(d)
    # Omit only coincident cross sections, never entire branches.
    valid = np.r_[True, np.linalg.norm(np.diff(p, axis=0), axis=1) > 1e-9]
    p, r, d = p[valid], r[valid], d[valid]
    if len(p) < 2:
        raise ValueError('Degenerate neurite branch')
    tangents = np.vstack((p[1]-p[0], p[2:]-p[:-2], p[-1]-p[-2]))
    tangents /= np.linalg.norm(tangents, axis=1)[:, None]
    reference = np.eye(3)[np.argmin(np.abs(tangents[0]))]
    normal = np.cross(tangents[0], reference)
    normal /= np.linalg.norm(normal)
    positions, normals = [], []
    for point, radius, tangent in zip(p, r, tangents):
        normal -= tangent * np.dot(normal, tangent)
        normal /= np.linalg.norm(normal)
        binormal = np.cross(tangent, normal)
        ring = np.array([normal * math.cos(2*math.pi*j/sides)
                         + binormal * math.sin(2*math.pi*j/sides) for j in range(sides)])
        positions.extend(point + radius * ring)
        normals.extend(ring)
    indices = []
    for i in range(len(p)-1):
        for j in range(sides):
            a, b = i*sides+j, i*sides+(j+1)%sides
            indices.extend((a, b, a+sides, b, b+sides, a+sides))
    # Closed end disks. Branch junctions intersect at their measured shared ring.
    for base, reverse in ((0, True), ((len(p)-1)*sides, False)):
        for j in range(1, sides-1):
            tri = [base, base+j, base+j+1]
            indices.extend(tri[::-1] if reverse else tri)
    return np.array(positions), np.array(normals), np.array(indices), np.repeat(d, sides), p, d


def soma_mesh(outline, radius):
    """Loft the observed soma contour; unmeasured depth is explicitly a proxy."""
    outline = np.array(outline)
    center = outline.mean(axis=0)
    rings, n = 12, len(outline)
    positions = [center + [0, 0, -radius]]
    for i in range(1, rings):
        angle = -math.pi/2 + math.pi*i/rings
        ring = center + (outline-center) * math.cos(angle)
        ring[:, 2] += radius * math.sin(angle)
        positions.extend(ring)
    positions.append(center + [0, 0, radius])
    indices = []
    for j in range(n):
        indices.extend((0, 1+(j+1)%n, 1+j))
    for i in range(rings-2):
        for j in range(n):
            a, b = 1+i*n+j, 1+i*n+(j+1)%n
            indices.extend((a, b, a+n, b, b+n, a+n))
    pole = len(positions)-1
    for j in range(n):
        indices.extend((pole, 1+(rings-2)*n+j, 1+(rings-2)*n+(j+1)%n))
    positions, indices = np.array(positions), np.array(indices)
    # Correct contour winding and average area-weighted normals at shared vertices.
    faces = positions[indices.reshape(-1, 3)]
    face_normals = np.cross(faces[:, 1]-faces[:, 0], faces[:, 2]-faces[:, 0])
    if np.sum(face_normals * (faces.mean(axis=1)-center)) < 0:
        indices = indices.reshape(-1, 3)[:, ::-1].ravel()
        face_normals *= -1
    normals = np.zeros_like(positions)
    for axis in range(3):
        np.add.at(normals, indices.reshape(-1, 3)[:, axis], face_normals)
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    return positions, normals, indices


def build(source=SOURCE):
    nodes, soma, children, distance = read_source(source)
    contour = json.loads((source / 'soma-contour.json').read_text())
    glb = GLB('Universe Scales uncropped NeuroMorpho reconstruction')
    axon_mat = glb.material('Axon • copper', (0.48, 0.19, 0.055, 1), rough=.48,
                            double_sided=False, emissive=(.09, .025, .004))
    dendrite_mat = glb.material('Dendrites • jade', (.055, .44, .37, 1), rough=.42,
                               double_sided=False, emissive=(.008, .06, .045))
    soma_mat = glb.material('Soma • pearl', (.55, .76, .63, 1), rough=.36,
                           double_sided=False)
    by_type = {2: [], 3: []}
    full_paths, pulse_points, pulse_distances = [], [], []
    for kind, p, r, d, path in branches(nodes, soma, children, distance):
        geometry = tube(p, r, d)
        by_type[2 if kind == 2 else 3].append(geometry)
        full_paths.append(path)
        if kind == 2:
            valid = geometry[5] >= 0
            pulse_points.extend(geometry[4][valid])
            pulse_distances.extend(geometry[5][valid])
    for kind, name, material in ((2, 'Axon', axon_mat), (3, 'Dendrites', dendrite_mat)):
        geometries = by_type[kind]
        offsets = np.cumsum([0]+[len(g[0]) for g in geometries[:-1]])
        positions = np.concatenate([g[0] for g in geometries])
        normals = np.concatenate([g[1] for g in geometries])
        indices = np.concatenate([g[2]+offset for g, offset in zip(geometries, offsets)])
        primitive = glb.primitive(positions, indices, material, normals=normals)
        if kind == 2:
            path = np.concatenate([g[3] for g in geometries]).astype(np.float32)
            primitive['attributes']['_PATH_DISTANCE'] = glb._accessor(path, 5126, 'SCALAR', 34962)
        glb.mesh_node(name, [primitive])
        glb.doc['nodes'][-1]['extras'] = {'neurite': 'axon' if kind == 2 else 'dendrite'}
    p, n, i = soma_mesh(contour['outline_swc_um'], soma['radius'])
    glb.mesh_node('Soma', [glb.primitive(p, i, soma_mat, normals=n)])

    # A screen-sized halo is an electrical annotation, not extra axon thickness.
    # Initially transparent: reduced-motion users see the resting reconstruction.
    halo_mat = glb.material('Electrical pulse halo (annotation)', (1, .64, .12, 0), blend=True)
    attrs = {'POSITION': glb._accessor(np.array(pulse_points, np.float32), 5126, 'VEC3', 34962, True),
             '_PATH_DISTANCE': glb._accessor(np.array(pulse_distances, np.float32), 5126, 'SCALAR', 34962)}
    glb.mesh_node('Axon electrical glow', [{'attributes': attrs, 'material': halo_mat, 'mode': 0}])
    glb.doc['nodes'][-1]['extras'] = {'neurite': 'pulse-halo', 'softPoints': True, 'hoverOverlay': False,
        'pointSize': {'max': 5, 'perPixel': .013},
        'pointLOD': {'fullPixels': 1, 'minimum': len(pulse_points), 'mobileMaximum': len(pulse_points)}}

    # Sparse, upright callouts use the existing screen-space label layout.
    glb.label_node('Soma label', (0, 0, 0), 'Soma', labelLayout='orbit',
                   labelPriority=100, labelOffset={'x': 35, 'y': -20})
    dendrites = [n for n in nodes.values() if n['type'] == 3]
    dendrite = max(dendrites, key=lambda n: n['xyz'][0])
    axons = [n for n in nodes.values() if n['type'] == 2]
    # Put the axon callout on its isolated long collateral, away from the
    # dendritic label in the dense central arbor.
    axon = min(axons, key=lambda n: abs(n['xyz'][1]+300) + abs(n['xyz'][0]+70))
    glb.label_node('Dendrites label', dendrite['xyz'], 'Dendrites', labelLayout='orbit',
                   labelPriority=90, labelOffset={'x': 35, 'y': -14})
    glb.label_node('Axon label', axon['xyz'], 'Axon', labelLayout='orbit',
                   labelPriority=95, labelOffset={'x': -30, 'y': 22})
    maximum = max(distance[n['id']] for n in axons)
    root = len(glb.doc['nodes'])
    glb.doc['nodes'].append({'name': 'Reconstructed neuron NMO_109111',
        'children': glb.doc['scenes'][0]['nodes'],
        'extras': {'animation': {'kind': 'reconstructed-neuron', 'period': 6.5,
            'launch': .8, 'travelSeconds': 4.5, 'aisDistanceUm': 20,
            'maxDistanceUm': maximum, 'pulseWidthUm': 22}}})
    glb.doc['scenes'][0]['nodes'] = [root]
    stats = {'units': 'micrometers', 'sourceNodes': len(nodes),
             'sourceSegments': len(nodes)-3, 'retainedBranches': len(full_paths),
             'crop': None, 'radiusGain': 1, 'positionErrorUm': POSITION_ERROR_UM,
             'radiusErrorUm': RADIUS_ERROR_UM, 'maxAxonPathUm': maximum,
             'sourceBoundsUm': np.ptp(np.array([n['xyz'] for n in nodes.values()]), axis=0).tolist(),
             'soma': 'Observed Neurolucida XY contour; authored depth loft using SWC equivalent radius'}
    glb.doc['extras'] = stats
    for key in ('images', 'textures', 'samplers'):
        if not glb.doc[key]:
            del glb.doc[key]
    data = pack_glb(glb.doc, glb.bin)
    return data, stats


def entry(data, stats, source=SOURCE):
    return {'id': MODEL_ID, 'replaces': 'pyramidal-neuron-action-potential',
        'source': 'https://neuromorpho.org/neuron_info.jsp?neuron_name=BC140212B_21',
        'author': 'Vishalini Emmenegger, Guanxiao Qi, Haijun Wang and Dirk Feldmeyer; NeuroMorpho.Org (RRID:SCR_002145)',
        'license': 'CC-BY-4.0', 'license_url': 'https://neuromorpho.org/useterm.jsp',
        'license_files': ['licenses/CC-BY-4.0.txt', 'sources/neuron-model.md'],
        'matches': {'length': ['Neuron']}, 'geometry': 'mesh',
        'representation': 'reconstruction',
        'basis_url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC6093438/',
        'basis_label': 'Emmenegger et al. (2018): morphology and electrophysiology',
        'presentation': {'reference_size': SPAN_UM, 'layout_width_factor': 1.25,
            'focus_scale_factor': 1.25, 'display_extent_factor': 1, 'roll': -127, 'pitch': 8, 'yaw': -10},
        'note': 'A real rat barrel-cortex layer-4 interneuron: NeuroMorpho.Org NMO_109111 (BC140212B_21), reconstructed by Emmenegger, Qi, Wang and Feldmeyer. The entire archived axon (copper) and dendrites (jade) are retained, with measured radii and a soma based on its traced outline; only soma depth is an authored loft. The reconstruction spans about 0.8 mm, requiring the accompanying Neuron dataset update. NeuroMorpho catalogs dendrites and axon as complete; this was a brain-slice preparation, so biological truncations remain possible. The glowing annotation starts in an assumed proximal axon initial segment and follows actual axonal path distances into the branches. Pulse speed, width, light and initial-segment position are illustrative, not measured voltage or conduction in this cell. Reduced motion shows the resting neuron. NeuroMorpho.Org (RRID:SCR_002145); Emmenegger et al. (2018), doi:10.1093/cercor/bhx352; Tecuatl, Ljungquist & Ascoli (2024), doi:10.1096/fba.2024-00048.',
        'processing': {**stats, 'script': 'scripts/build_reconstructed_neuron.py',
            'sources': json.loads((source / 'provenance.json').read_text())},
        **inspect_glb(data)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=SOURCE)
    parser.add_argument('--output-dir', type=Path, default=Path('/tmp/neuron-final'))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data, stats = build(args.source_dir)
    (args.output_dir / f'{MODEL_ID}.glb').write_bytes(data)
    write_json(args.output_dir / f'{MODEL_ID}.entry.json', entry(data, stats, args.source_dir))
    print(json.dumps({'bytes': len(data), **stats}, indent=2))


if __name__ == '__main__':
    main()
