#!/usr/bin/env python3
"""Two small, AB-stacked lattice windows from the CC0 COD 9011577 graphite cell.

This spacing diagram deliberately shows only one ring per layer: lateral sheet
context must not become many times larger than the interlayer measurement.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np

from build_bio3d_models import ROOT, HANDOFF, SOURCE, cylinder, normals
from fetch_model_assets import inspect_glb
from geo_glb_common import GLB

MODEL_ID = 'cod-9011577-graphene-spacing'


def lattice():
    raw = (SOURCE/'9011577.cif').read_text()
    a = float(re.search(r'^_cell_length_a\s+(\S+)', raw, re.M)[1])
    c = float(re.search(r'^_cell_length_c\s+(\S+)', raw, re.M)[1])
    bond = a/math.sqrt(3)
    theta = np.arange(6)*np.pi/3
    ring = np.stack((bond*np.cos(theta), np.zeros(6), bond*np.sin(theta)), axis=1)
    lower = ring + [-bond/2, -c/4, 0]
    upper = ring + [bond/2, c/4, 0]
    return lower, upper, a, c


def build(output):
    lower, upper, a, c = lattice()
    vertices, faces, colors = [], [], []
    for ring, color in [(lower, [.2, .62, .70]), (upper, [.86, .58, .25])]:
        for i in range(6):
            v, f = cylinder(ring[i], ring[(i+1)%6], .055, sides=12)
            faces.append(f+sum(len(x) for x in vertices)); vertices.append(v)
            colors.append(np.tile(color, (len(v), 1)))
    verts, tris = np.concatenate(vertices)/10, np.concatenate(faces)
    color = np.concatenate(colors)
    g = GLB('Universe Scales graphite lattice-spacing diagram')
    material = g.material('Graphite layer markers', rough=.65, double_sided=False)
    g.mesh_node('AB-stacked hexagonal windows', [g.primitive(verts, tris.ravel(), material,
                  normals=normals(verts, tris), colors=color, rgba8=True)])
    # This neutral line joins the layer planes, not the edge of the bond glyph.
    marker = g.material('Interlayer distance', color=(.65, .76, .78, 1))
    v, f = cylinder(np.array([.15, -c/40, 0]), np.array([.15, c/40, 0]), .002, sides=8)
    g.mesh_node('Layer-plane separation', [g.primitive(v, f.ravel(), marker, normals=normals(v, f))])
    for y in [-c/40, c/40]:
        v, f = cylinder(np.array([.13, y, 0]), np.array([.17, y, 0]), .002, sides=8)
        g.mesh_node('Plane-spacing ruler tick', [g.primitive(v, f.ravel(), marker, normals=normals(v, f))])
    g.label_node('Spacing label', [.15, 0, 0], 'plane spacing',
                 labelOffset={'x': 60, 'y': 0}, labelLeader=True)
    path = output/f'{MODEL_ID}.glb'; g.write(path)
    entry = {'id': MODEL_ID, 'name': 'Graphene Layer Spacing',
             'display_label': 'Graphene Layer Spacing · AB-stacked lattice windows',
             'source': 'https://www.crystallography.net/cod/9011577.html',
             'author': 'Trucano, P.; Chen, R.; Crystallography Open Database',
             'license': 'CC0-1.0', 'license_url': 'https://www.crystallography.net/cod/',
             'license_files': ['licenses/CC0-1.0.txt'], 'matches': {'length': ['Graphene Layer Spacing']},
             'geometry': 'mesh', 'representation': 'measurement_diagram',
             'basis_url': 'https://doi.org/10.1038/258136a0',
             'basis_label': 'Neutron-diffraction graphite structure',
             'link_label': 'COD graphite coordinates',
             'src': f'content/visualizations/models/{MODEL_ID}.glb',
             'presentation': {'reference_size': .335, 'pitch': 8, 'yaw': -15, 'roll': 0,
                              'layout_width_factor': 1.3, 'focus_scale_factor': 1.3},
             'note': 'Two hexagonal windows of neighboring AB-stacked graphite sheets, derived from the neutron-diffraction cell of COD 9011577 (a = 2.464 Å, c = 6.711 Å). Their plane separation is c/2 = 0.33555 nm; the catalog value is the approximate 0.335 nm. The neutral connector measures plane to plane. Colored tubes trace nuclear positions and bonds; their thickness and colors are illustrative. These are tiny windows into extended sheets, not isolated benzene molecules, and the gap is not the thickness of a single graphene sheet.',
             'provenance': f'content/visualizations/models/sources/{MODEL_ID}.md',
             'processing': {'builder': 'scripts/build_graphene_spacing.py', 'coordinate_unit': 'nm',
                            'pdb': 'COD 9011577', 'cell_a_A': a, 'cell_c_A': c,
                            'layer_spacing_nm': c/20,
                            'retained_cif_sha256': hashlib.sha256((SOURCE/'9011577.cif').read_bytes()).hexdigest()},
             'volume_semantics': 'not_a_volume_measurement', 'closed_volume_checked': False,
             **inspect_glb(path.read_bytes())}
    (HANDOFF/f'{MODEL_ID}.entry.json').write_text(json.dumps(entry, indent=2)+'\n')
    print(f"{MODEL_ID}: {entry['bytes']} bytes; plane separation {c/20} nm")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, default=ROOT/'content/visualizations/models')
    args = p.parse_args(); args.output_dir.mkdir(parents=True, exist_ok=True)
    build(args.output_dir)


if __name__ == '__main__':
    main()
