#!/usr/bin/env python3
"""Bake the curated whale/elephant bind pose before glTF Transform optimization.

This freezes the provided neutral pose; it does not pose or animate the animal.
Keep downloads outside the repository. See earth3d2-sperm-whale.md.
"""
import argparse
from pathlib import Path

import numpy as np

from geo_glb_common import pack_glb
from render_earth3d_previews import accessor
from render_glb_preview import node_matrix, read_glb


def bake(source, output):
    doc, data = read_glb(source)
    binary = bytearray(data)
    world = {}

    def visit(index, parent):
        world[index] = parent @ node_matrix(doc['nodes'][index])
        for child in doc['nodes'][index].get('children', []):
            visit(child, world[index])

    for index in doc['scenes'][doc.get('scene', 0)]['nodes']:
        visit(index, np.eye(4))

    def add(values):
        values = np.asarray(values, dtype='<f4')
        binary.extend(b'\0'*(-len(binary) % 4))
        view = len(doc['bufferViews'])
        doc['bufferViews'].append(dict(buffer=0, byteOffset=len(binary), byteLength=values.nbytes, target=34962))
        binary.extend(values.tobytes())
        doc['accessors'].append(dict(bufferView=view, componentType=5126, count=len(values), type='VEC3',
                                     min=values.min(0).tolist(), max=values.max(0).tolist()))
        return len(doc['accessors'])-1

    for index, node in enumerate(doc['nodes']):
        if 'skin' not in node:
            continue
        skin = doc['skins'][node['skin']]
        acc = doc['accessors'][skin['inverseBindMatrices']]
        view = doc['bufferViews'][acc['bufferView']]
        matrices = np.ndarray((acc['count'], 16), dtype='<f4', buffer=binary,
                              offset=view.get('byteOffset', 0)+acc.get('byteOffset', 0),
                              strides=(view.get('byteStride', 64), 4)).copy().reshape(-1, 4, 4).transpose(0, 2, 1)
        joint = np.array([np.linalg.inv(world[index]) @ world[j] @ matrices[k]
                          for k, j in enumerate(skin['joints'])])
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            attrs = primitive['attributes']
            if primitive.get('targets') or 'JOINTS_1' in attrs:
                raise ValueError('Curated bake only supports four-weight skinning without morph targets')
            p = accessor(doc, binary, attrs['POSITION'])
            j = accessor(doc, binary, attrs['JOINTS_0']).astype(int)
            w = accessor(doc, binary, attrs['WEIGHTS_0']).astype(float)
            if (w.sum(1) <= 0).any():
                raise ValueError('Unweighted skin vertex')
            w /= w.sum(1)[:, None]
            transform = (joint[j]*w[:, :, None, None]).sum(1)
            p = np.einsum('nij,nj->ni', transform, np.column_stack((p, np.ones(len(p)))))[:, :3]
            attrs['POSITION'] = add(p)
            if 'NORMAL' in attrs:
                n = accessor(doc, binary, attrs['NORMAL'])
                n = np.einsum('nji,nj->ni', np.linalg.inv(transform[:, :3, :3]), n)
                n /= np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-30)
                attrs['NORMAL'] = add(n)
            for key in ['JOINTS_0', 'WEIGHTS_0', 'TANGENT']:
                attrs.pop(key, None)
        node.pop('skin')
    doc.pop('skins', None)
    doc.pop('animations', None)
    output.write_bytes(pack_glb(doc, binary))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    bake(args.source, args.output)
