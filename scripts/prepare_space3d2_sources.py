#!/usr/bin/env python3
"""Refresh second-round space sources, separate from the offline model builder.

Network inputs are pinned by SHA-256 in manifest.json. Original shape coordinates
are retained losslessly as compressed arrays; no geometry is invented here.
JPL requests are deliberately sequential, as required by its fair-use policy.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlencode

import numpy as np
import requests

from fetch_model_assets import sha, write_json

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'content/visualizations/models/sources/space3d2'
URLS = {
    'ryugu.obj': 'https://data.darts.isas.jaxa.jp/pub/hayabusa2/paper/Watanabe_2019/SHAPE_SFM_49k_v20180804.obj',
    'hyperion.obj': 'https://sbn.psi.edu/pds/shape-models/files/SATURN_SMALL_MOONS/hyperion_30k_plt.tab.obj',
    'dimorphos.bds': 'https://naif.jpl.nasa.gov/pub/naif/pds/pds4/dart/dart_spice/spice_kernels/dsk/dimorphos_g_01940mm_spc_0000n00000_v004.bds',
    'hexagon.jpg': 'https://assets.science.nasa.gov/content/dam/science/psd/solar/2023/09/p/i/a/PIA17652.jpg',
    'grs2019.jpg': 'https://assets.science.nasa.gov/content/dam/science/psd/photojournal/pia/pia23/pia23606/PIA23606.jpg',
    'halley.json': 'https://ssd-api.jpl.nasa.gov/sbdb.api?' + urlencode({'sstr': '1P', 'full-prec': '1'}),
    'sedna.json': 'https://ssd-api.jpl.nasa.gov/sbdb.api?' + urlencode({'sstr': '90377', 'full-prec': '1'}),
    'kuiper.json': 'https://ssd-api.jpl.nasa.gov/sbdb_query.api?' + urlencode({
        'fields': 'pdes,full_name,epoch,a,e,i,om,w,ma', 'sb-kind': 'a',
        'sb-cdata': json.dumps({'AND': ['a|RG|30|50', 'q|GE|30']}, separators=(',', ':')),
        'full-prec': '1', 'sort': 'pdes'}),
}


def parse_obj(data):
    vertices, faces = [], []
    for line in data.decode().splitlines():
        fields = line.split()
        if fields and fields[0] == 'v':
            vertices.append([float(x) for x in fields[1:4]])
        elif fields and fields[0] == 'f':
            indices = [int(x.split('/')[0])-1 for x in fields[1:]]
            if len(indices) != 3:
                raise ValueError('Expected source triangles')
            faces.append(indices)
    return np.array(vertices, dtype=np.float64), np.array(faces, dtype=np.int32)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, help='Use downloaded files here, without network requests')
    args = parser.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    records = []
    for name, url in URLS.items():
        if args.cache:
            data = (args.cache/name).read_bytes()
        else:
            response = requests.get(url, timeout=90, headers={'User-Agent': 'UniverseScalesSourcePreparation/1.0'})
            response.raise_for_status()
            data = response.content
        if name.endswith('.bds'):
            # Optional preparation-only dependency: spiceypy. Never needed at runtime.
            import spiceypy as spice
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.bds') as temporary:
                temporary.write(data)
                temporary.flush()
                handle = spice.dasopr(temporary.name)
                try:
                    descriptor = spice.dlabfs(handle)
                    nv, np_ = spice.dskz02(handle, descriptor)
                    vertices = spice.dskv02(handle, descriptor, 1, nv)
                    faces = spice.dskp02(handle, descriptor, 1, np_)-1
                finally:
                    spice.dascls(handle)
            local = name.replace('.bds', '.npz')
            np.savez_compressed(DEST/local, vertices=vertices, faces=faces)
        elif name.endswith('.obj'):
            vertices, faces = parse_obj(data)
            local = name.replace('.obj', '.npz')
            np.savez_compressed(DEST/local, vertices=vertices, faces=faces)
        else:
            local = name
            (DEST/local).write_bytes(data)
        record = {'file': local, 'url': url, 'source_sha256': sha(data), 'source_bytes': len(data),
                  'sha256': sha((DEST/local).read_bytes())}
        if name.endswith('.json'):
            document = json.loads(data)
            if document.get('signature', {}).get('version') not in ('1.0', '1.3'):
                raise ValueError('Review changed JPL API version')
            record['signature'] = document['signature']
        records.append(record)
        print(local, flush=True)
    # This small table is transcribed from the opened JPL Table 1, rather than
    # fetched from an API. Pin it too so later edits cannot silently change context.
    records.append({'file': 'planet-elements.json',
                    'url': 'https://ssd.jpl.nasa.gov/planets/approx_pos.html',
                    'sha256': sha((DEST/'planet-elements.json').read_bytes()),
                    'note': 'Manually transcribed J2000 Table 1 reference ellipses'})
    write_json(DEST/'manifest.json', {'retrieved': '2026-10-16', 'sources': records})


if __name__ == '__main__':
    main()
