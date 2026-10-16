#!/usr/bin/env python3
"""Rebuild the curated NASA Length models from a hash-pinned local source cache.

See content/visualizations/models/sources/space3d-manifest.json for downloads.
This script never changes the dataset. Offline glTF Transform steps, where used,
are recorded in that manifest; pass the prepared cache with --source-dir.
"""
import argparse
import copy
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image

from fetch_model_assets import (inspect_glb, pack_glb, pack_views, read_glb,
                                scene_bounds, sha, view_bytes, write_json)
from render_glb_preview import accessor, node_matrix

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / 'content/visualizations/models'
MANIFEST = MODELS / 'sources/space3d-manifest.json'


def restore_normals(data):
    """Area-weighted normals after offline simplification of hard-split vertices."""
    document, payload = read_glb(data)
    binary = bytearray(payload)
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            if 'NORMAL' in primitive['attributes'] or primitive.get('mode', 4) != 4:
                continue
            points = accessor(document, binary, primitive['attributes']['POSITION']).astype(float)
            indices = (accessor(document, binary, primitive['indices']).ravel()
                       if 'indices' in primitive else np.arange(len(points))).reshape(-1, 3)
            faces = points[indices]
            cross = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
            normals = np.zeros_like(points)
            for corner in range(3):
                np.add.at(normals, indices[:, corner], cross)
            lengths = np.linalg.norm(normals, axis=1)
            # Oppositely wound duplicate faces can cancel; isolated source vertices
            # can have no incident face. Give either case a valid fallback normal.
            missing = lengths < 1e-15
            for triangle, face_normal in zip(indices, cross):
                length = np.linalg.norm(face_normal)
                if length > 1e-15:
                    for vertex in triangle:
                        if missing[vertex]:
                            normals[vertex] = face_normal / length
                            missing[vertex] = False
            normals[missing] = [0, 1, 0]
            normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-20)
            binary.extend(b'\0' * (-len(binary) % 4))
            view = len(document['bufferViews'])
            raw = normals.astype('<f4').tobytes()
            document['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(raw)})
            binary.extend(raw)
            index = len(document['accessors'])
            document['accessors'].append({'bufferView': view, 'componentType': 5126,
                                          'count': len(points), 'type': 'VEC3'})
            primitive['attributes']['NORMAL'] = index
    return pack_glb(document, bytes(binary))


def repair_missing_uv_materials(data):
    """Retain source shape; remove invalid texture bindings on UV-less primitives."""
    document, binary = read_glb(data)
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            if 'TEXCOORD_0' in primitive['attributes'] or 'material' not in primitive:
                continue
            source = document['materials'][primitive['material']]
            material = copy.deepcopy(source)
            changed = False
            for owner in [material, material.get('pbrMetallicRoughness', {})]:
                for key in list(owner):
                    if key.endswith('Texture'):
                        del owner[key]
                        changed = True
            if changed:
                primitive['material'] = len(document['materials'])
                document['materials'].append(material)
    return pack_glb(document, binary)


def resize_images(data, maximum=1024):
    """Keep geometry and material slots; encode all embedded images as PNG/JPEG."""
    document, binary = read_glb(data)
    payloads = [view_bytes(document, binary, i) for i in range(len(document['bufferViews']))]
    textures = []
    for item in document.get('images', []):
        index = item['bufferView']
        image = Image.open(io.BytesIO(payloads[index]))
        original = list(image.size)
        alpha = 'A' in image.getbands() and image.getchannel('A').getextrema()[0] < 255
        image = image.convert('RGBA' if alpha else 'RGB')
        image.thumbnail((maximum, maximum), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        # Normal maps must remain lossless; colors may use JPEG.
        normal_slots = {m.get('normalTexture', {}).get('index') for m in document.get('materials', [])}
        normal_images = {document['textures'][i].get('source') for i in normal_slots if i is not None}
        lossless = alpha or document['images'].index(item) in normal_images
        if lossless:
            image.save(output, format='PNG', optimize=True)
            item['mimeType'] = 'image/png'
        else:
            image.save(output, format='JPEG', quality=88, subsampling=0, optimize=True)
            item['mimeType'] = 'image/jpeg'
        payloads[index] = output.getvalue()
        textures.append({'name': item.get('name'), 'original_size': original,
                         'size': list(image.size), 'mime_type': item['mimeType']})
    # Offline-decoded NASA downloads sometimes retain a WebP texture extension.
    for texture in document.get('textures', []):
        ext = texture.get('extensions', {}).pop('EXT_texture_webp', None)
        if ext:
            texture['source'] = ext['source']
        if not texture.get('extensions'):
            texture.pop('extensions', None)
    for key in ['extensionsUsed', 'extensionsRequired']:
        if key in document:
            document[key] = [x for x in document[key] if x != 'EXT_texture_webp']
            if not document[key]:
                document.pop(key)
    return pack_glb(document, pack_views(document, payloads)), textures


def mesh_diameter(data):
    """Equivalent-volume diameter of the retained triangle mesh, in world units.

    UV seams duplicate vertices, so count coordinate-welded edges for closure.
    Reject open or inconsistently wound surfaces instead of inventing a volume.
    """
    document, binary = read_glb(data)
    all_faces = []

    def visit(index, parent):
        node = document['nodes'][index]
        matrix = parent @ node_matrix(node)
        if 'mesh' in node:
            for primitive in document['meshes'][node['mesh']]['primitives']:
                if primitive.get('mode', 4) != 4:
                    raise ValueError('Volume calibration needs triangles')
                points = accessor(document, binary, primitive['attributes']['POSITION'])
                points = (np.column_stack((points, np.ones(len(points)))) @ matrix.T)[:, :3]
                indices = (accessor(document, binary, primitive['indices']).ravel()
                           if 'indices' in primitive else np.arange(len(points)))
                all_faces.append(points[indices.reshape(-1, 3)])
        for child in node.get('children', []):
            visit(child, matrix)
    for root in document['scenes'][document.get('scene', 0)]['nodes']:
        visit(root, np.eye(4))
    faces = np.concatenate(all_faces)
    tolerance = np.ptp(faces.reshape(-1, 3), axis=0).max() * 1e-6
    _, welded = np.unique(np.round(faces.reshape(-1, 3) / tolerance).astype(np.int64),
                          axis=0, return_inverse=True)
    triangles = welded.reshape(-1, 3)
    # Degenerate UV-pole triangles have no physical area.
    triangles = triangles[np.array([len(set(t)) == 3 for t in triangles])]
    edges = np.concatenate([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]])
    _, inverse, count = np.unique(np.sort(edges, axis=1), axis=0, return_inverse=True, return_counts=True)
    orientation = np.bincount(inverse, weights=np.where(edges[:, 0] < edges[:, 1], 1, -1))
    if np.any(count != 2) or np.any(orientation != 0):
        raise ValueError('Mesh is not a closed consistently wound surface')
    # Translate before summation to avoid origin-related cancellation.
    faces -= faces.reshape(-1, 3).mean(axis=0)
    volume = abs(np.einsum('ij,ij->i', faces[:, 0], np.cross(faces[:, 1], faces[:, 2])).sum() / 6)
    return (6 * volume / np.pi) ** (1 / 3)


def build(spec, directory):
    path = directory / spec['prepared_file']
    data = path.read_bytes()
    if sha(data) != spec['prepared_sha256']:
        raise ValueError(f"Prepared source hash changed: {path}")
    if spec.get('remove_meshes_on_nodes'):
        document, binary = read_glb(data)
        for node in document['nodes']:
            if node.get('name') in spec['remove_meshes_on_nodes']:
                node.pop('mesh', None)
        data = pack_glb(document, binary)
    output, textures = resize_images(restore_normals(repair_missing_uv_materials(data)), spec.get('texture_max', 1024))
    document, binary = read_glb(output)
    bounds = scene_bounds(document, binary)
    presentation = copy.deepcopy(spec.get('presentation', {}))
    if spec['calibration'] == 'volume-equivalent-diameter':
        presentation['reference_size'] = mesh_diameter(output)
    elif spec['calibration'] == 'longest-extent':
        presentation['reference_size'] = max(b - a for a, b in zip(bounds['min'], bounds['max']))
    elif spec['calibration'] == 'axis':
        axis = 'xyz'.index(spec['measure_axis'])
        presentation['reference_size'] = bounds['max'][axis] - bounds['min'][axis]
    elif spec['calibration'] == 'explicit':
        if not presentation.get('reference_size', 0) > 0:
            raise ValueError('Explicit calibration needs a positive reference_size')
    else:
        raise ValueError(f"Unsupported calibration: {spec['calibration']}")
    entry = {k: copy.deepcopy(spec[k]) for k in
             ['id', 'source', 'download_url', 'author', 'note', 'matches', 'representation']}
    entry.update({
        'license': 'U.S. public-domain NASA media; NASA usage guidelines apply (not CC0)',
        'license_url': 'https://www.nasa.gov/nasa-brand-center/images-and-media/',
        'license_files': ['licenses/nasa-media-guidelines.html', 'licenses/nasa-3d-resources.README.md'],
        'geometry': 'mesh', 'src': f"content/visualizations/models/{spec['id']}.glb",
        'presentation': presentation, 'reference': f"content/visualizations/models/sources/{spec['id']}.md",
        'source_sha256': spec['source_sha256'], 'source_bytes': spec['source_bytes'],
        'processing': {'operations': spec['operations'] + ['Resize embedded images; preserve alpha and lossless normal maps'],
                       'prepared_sha256': spec['prepared_sha256'], 'textures': textures,
                       'calibration': spec['calibration'], 'source_bounds': bounds},
        'volume_semantics': 'not_applicable', 'closed_volume_checked': spec['calibration'] == 'volume-equivalent-diameter',
        **inspect_glb(output),
    })
    if entry['bytes'] > 3_000_000:
        raise ValueError(f"Asset budget exceeded: {spec['id']}: {entry['bytes']}")
    return output, entry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True)
    parser.add_argument('--register', action='store_true')
    args = parser.parse_args()
    from register_model import register
    handoff = ROOT / 'handoff/space3d'
    handoff.mkdir(parents=True, exist_ok=True)
    for spec in json.loads(MANIFEST.read_text())['models']:
        output, entry = build(spec, args.source_dir)
        destination = ROOT / entry['src']
        destination.write_bytes(output)
        entry_path = handoff / f"{entry['id']}.entry.json"
        write_json(entry_path, entry)
        if args.register:
            register(entry_path, destination, 'length')
        print(entry['id'], entry['bytes'], entry['presentation']['reference_size'])


if __name__ == '__main__':
    main()
