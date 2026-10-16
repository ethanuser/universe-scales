#!/usr/bin/env python3
"""Tardigraph / Gross et al. nanoCT meshes -> native-micrometre cutaway GLB.

Download the pinned upstream GLB separately; this builder is offline. Only the
whole-body scan structures are used: the independently registered head scan is
omitted. The body surface is Tardigraph's tracing of the CT cuticle.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from build_bio3d_models import simplify, clean_mesh, normals
from geo_glb_common import GLB
from render_glb_preview import read_glb, accessor

URL = 'https://tardigraph.meow-meow.io/resources/files/tardigrade-organs-glb.glb'
COLORS = {
    'body': (.34, .54, .60), 'gut': (.73, .37, .12), 'pharynx': (.83, .59, .20),
    'buccal-tube': (.83, .59, .20), 'esophagus': (.73, .37, .12),
    'storage-cells': (.58, .65, .47), 'ovary': (.23, .66, .59),
    'malpighian-tubules': (.30, .56, .76), 'stylets': (.80, .79, .62),
    'claw-glands': (.59, .47, .70),
}


def build(source, destination):
    metadata = json.loads(Path(__file__).resolve().parents[1].joinpath(
        'content/visualizations/models/sources/bio3d2/tardigrade.json').read_text())
    if hashlib.sha256(source.read_bytes()).hexdigest() != metadata['upstream_sha256']:
        raise ValueError('Upstream file differs from the reviewed source pin')
    doc, binary = read_glb(source)
    glb = GLB('Universe Scales: native-scale Gross et al. nanoCT via Tardigraph')
    omitted, retained = [], []
    for node in doc['nodes']:
        name = node['name']
        if name.endswith('-head') or name in ('brain', 'salivary-glands'):
            omitted.append(name); continue
        if any(k in node for k in ('matrix', 'translation', 'scale', 'rotation', 'children')):
            raise ValueError('Expected upstream world-space meshes')
        color = COLORS.get(name, (.45, .26, .65))
        mat = glb.material(name+' (false colour)', (*color, 1), rough=.74, double_sided=name == 'body')
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            p = accessor(doc, binary, primitive['attributes']['POSITION']).astype(float)
            f = accessor(doc, binary, primitive['indices']).reshape(-1, 3).astype(int)
            if name == 'body':
                # Cut only the shell. No reconstructed organ is repositioned,
                # mirrored, stretched or independently enlarged.
                centers = p[f].mean(1)
                f = f[(centers[:, 2] <= 0) | (centers[:, 1] < 0)]
            target = 9000 if name in ('body', 'storage-cells', 'gut') else 2500
            p, f = simplify(p, f, target)
            p, f = clean_mesh(p, f)
            glb.mesh_node(name, [glb.primitive(p, f.ravel(), mat, normals=normals(p, f))])
        retained.append(name)
    glb.write(destination)
    print(json.dumps({'retained': retained, 'omitted_registered_head_scan': omitted,
                      'bytes': destination.stat().st_size}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('destination', type=Path)
    args = p.parse_args(); build(args.source, args.destination)
