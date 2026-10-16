#!/usr/bin/env python3
"""Prepare an offline, credited derivative from NeuroMorpho's direct data API.

Usage: ./venv/bin/python scripts/prepare_neuron_source.py --download-dir /tmp/neuron-download
No JSP scraping; source comments containing workstation paths are omitted.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import urllib.request

import numpy as np

from build_reconstructed_neuron import SOURCE, simplify_indices

BASE = 'https://neuromorpho.org/'
NAME = 'BC140212B_21'
URLS = {'swc': BASE + f'dableFiles/feldmeyer/CNG%20version/{NAME}.CNG.swc',
        'asc': BASE + f'dableFiles/feldmeyer/Source-Version/{NAME}.asc',
        'metadata': BASE + f'api/neuron/name/{NAME}'}
POINT = re.compile(r'^\s*\(\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\)', re.M)


def prepare(files, output=SOURCE):
    swc = files['swc'].read_text()
    rows = np.array([list(map(float, l.split())) for l in swc.splitlines()
                     if l.strip() and not l.startswith('#')])
    asc = files['asc'].read_text()
    original, standardized = [], []
    for kind, token in ((2, '(Axon)'), (3, '(Dendrite)')):
        # Standardization can remove later coincident samples. The first six
        # coordinates of each primary stem have direct one-to-one counterparts.
        raw = np.array(POINT.findall(asc[asc.index(token):]), float)[:6, :3]
        target = rows[rows[:, 1] == kind][:6, 2:5]
        original.extend(raw); standardized.extend(target)
    a, b = np.array(original), np.array(standardized)
    # Kabsch rigid fit: no scaling, stretching or second shrinkage correction.
    # NeuroMorpho rotates this specimen only about Z. Fit XY independently so
    # rounding of nearly coplanar stem samples cannot tilt the soma contour.
    u, _, vt = np.linalg.svd((a[:, :2]-a[:, :2].mean(0)).T @ (b[:, :2]-b[:, :2].mean(0)))
    planar = u @ vt
    if np.linalg.det(planar) < 0:
        u[:, -1] *= -1
        planar = u @ vt
    rotation = np.eye(3)
    rotation[:2, :2] = planar
    translation = b.mean(0) - a.mean(0) @ rotation
    error = float(np.max(np.linalg.norm(a @ rotation + translation - b, axis=1)))
    if error > .03:
        raise ValueError(f'Original/standardized alignment mismatch: {error} um')
    block = asc[asc.index('(CellBody)'):]
    block = block[:block.index('End of contour')]
    outline = np.array(POINT.findall(block), float)[:, :3] @ rotation + translation
    if np.linalg.norm(outline[0]-outline[-1]) > 1e-5:
        outline = np.vstack((outline, outline[0]))
    distances = np.r_[0, np.cumsum(np.linalg.norm(np.diff(outline, axis=0), axis=1))]
    keep = simplify_indices(outline, np.zeros(len(outline)), distances, position_error=.08)
    outline = outline[keep][:-1]
    output.mkdir(parents=True, exist_ok=True)
    clean = '# NeuroMorpho.Org NMO_109111; Feldmeyer archive; CC BY 4.0. See ../neuron-model.md.\n'
    clean += '\n'.join(l.strip() for l in swc.splitlines() if l.strip() and not l.startswith('#')) + '\n'
    (output / f'{NAME}.swc.gz').write_bytes(gzip.compress(clean.encode(), mtime=0))
    (output / 'soma-contour.json').write_text(json.dumps({'outline_swc_um': outline.tolist(),
        'source': URLS['asc'], 'rigid_rotation_row_vectors': rotation.tolist(),
        'translation_um': translation.tolist(), 'max_alignment_error_um': error,
        'outline_simplification_error_um': .08}, indent=2)+'\n')
    metadata = json.loads(files['metadata'].read_text())
    (output / 'metadata.json').write_text(json.dumps(metadata, indent=2)+'\n')
    provenance = {key: {'url': URLS[key], 'download_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                  for key, path in files.items()}
    provenance['license'] = {'url': BASE+'useterm.jsp', 'license': 'CC-BY-4.0', 'checked': '2026-10-15'}
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    print(json.dumps({'source_nodes': len(rows), 'outline_vertices': len(outline),
                      'alignment_error_um': error}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, default=SOURCE)
    args = parser.parse_args()
    args.download_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    for key, url in URLS.items():
        path = args.download_dir / f'{NAME}.{key}'
        if not path.exists():
            request = urllib.request.Request(url, headers={'User-Agent': 'UniverseScales-Morphology-Research/1.0'})
            path.write_bytes(urllib.request.urlopen(request, timeout=60).read())
        files[key] = path
    prepare(files, args.output_dir)


if __name__ == '__main__':
    main()
