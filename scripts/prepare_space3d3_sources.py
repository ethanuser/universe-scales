#!/usr/bin/env python3
"""Refresh compact scientific inputs; the model builder itself stays offline.

Only coordinates, numerical facts and one licensed EHT image are retained.
JPL requests are sequential. No extra Python packages are required.
"""
import argparse
import csv
import io
import json
import re
from pathlib import Path

import requests

from fetch_model_assets import sha, write_json

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'content/visualizations/models/sources/space3d3'
WAVE_URL = 'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-019-1874-z/MediaObjects/41586_2019_1874_MOESM1_ESM.html'
EHT_URL = 'https://cdn.eso.org/images/publicationjpg/eso1907a.jpg'


def parse_vectors(document):
    text = document['result']
    rows = list(csv.reader(io.StringIO(text.split('$$SOE')[1].split('$$EOE')[0].strip())))
    return {'jd_tdb': [float(r[0]) for r in rows],
            'xyz_km': [[float(v) for v in r[2:5]] for r in rows],
            'frame': 'J2000 ecliptic; geometric vectors relative to Earth center',
            'target': re.search(r'Target body name: (.+)', text).group(1).strip(),
            'signature': document['signature']}


def parse_wave(text):
    match = re.search(r"Plotly.newPlot\(\s*'[^']+',\s*", text)
    traces, _ = json.JSONDecoder().raw_decode(text[match.end():])
    trace = next(t for t in traces if t.get('name') == 'Radcliffe Wave')
    # The original interactive figure labels Plotly x as Galactic Y and y as X.
    # Keep that explicit swap; do not infer the frame from the JS key names.
    clouds = [{'name': n, 'xyz_pc': [x, y, z]} for n, x, y, z in
              zip(trace['text'], trace['y'], trace['x'], trace['z'])]
    if len(clouds) != 141:
        raise ValueError('Review changed Radcliffe member selection')
    return {'source': WAVE_URL, 'paper': 'https://doi.org/10.1038/s41586-019-1874-z',
            'frame': 'Heliocentric Galactic Cartesian pc: X toward Galactic center, Y toward l=90, Z north',
            'selection': 'All 141 points in the authors\' Radcliffe Wave trace; no fit or posterior samples',
            'clouds': clouds}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, help='Read raw source files from this directory')
    args = parser.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    records = []

    def get(name, url, params=None):
        if args.cache:
            data = (args.cache/name).read_bytes()
        else:
            response = requests.get(url, params=params, timeout=90,
                                    headers={'User-Agent': 'UniverseScalesScientificSources/1.0'})
            response.raise_for_status()
            data = response.content
        return data

    def record(name, url, raw):
        records.append({'file': name, 'url': url, 'source_bytes': len(raw),
                        'source_sha256': sha(raw), 'sha256': sha((DEST/name).read_bytes())})

    for name, command in [('webb', '-170'), ('sun', '10')]:
        params = {'format': 'json', 'COMMAND': f"'{command}'", 'OBJ_DATA': "'NO'",
                  'MAKE_EPHEM': "'YES'", 'EPHEM_TYPE': "'VECTORS'", 'CENTER': "'500@399'",
                  'START_TIME': "'2024-01-01'", 'STOP_TIME': "'2025-01-01'", 'STEP_SIZE': "'2 d'",
                  'OUT_UNITS': "'KM-S'", 'REF_PLANE': "'ECLIPTIC'", 'REF_SYSTEM': "'ICRF'",
                  'VEC_TABLE': "'1'", 'CSV_FORMAT': "'YES'", 'VEC_CORR': "'NONE'"}
        request = requests.Request('GET', 'https://ssd.jpl.nasa.gov/api/horizons.api', params=params).prepare()
        raw = get('horizons-'+name+'.json', request.url)
        write_json(DEST/(name+'-vectors.json'), parse_vectors(json.loads(raw)))
        record(name+'-vectors.json', request.url, raw)

    raw = get('wave.html', WAVE_URL)
    write_json(DEST/'radcliffe-clouds.json', parse_wave(raw.decode()))
    record('radcliffe-clouds.json', WAVE_URL, raw)
    rights_url = 'https://api.datacite.org/dois/10.7910/DVN/07L7YZ'
    raw = get('wave-rights.json', rights_url)
    document = json.loads(raw)
    attributes = document.get('data', {}).get('attributes', document)
    rights = {k: attributes[k] for k in ['doi', 'titles', 'rightsList', 'url']}
    if not any(r.get('rightsIdentifier') == 'cc0-1.0' for r in rights['rightsList']):
        raise ValueError('Review changed cloud dataset rights')
    write_json(DEST/'radcliffe-data-rights.json', rights)
    record('radcliffe-data-rights.json', rights_url, raw)

    raw = get('m87-eht.jpg', EHT_URL)
    (DEST/'m87-eht.jpg').write_bytes(raw)
    record('m87-eht.jpg', EHT_URL, raw)
    # Transcribed parameters have their own citations and remain reviewable.
    records.append({'file': 'parameters.json', 'sha256': sha((DEST/'parameters.json').read_bytes()),
                    'note': 'Numerical facts transcribed from the primary sources listed in the file'})
    write_json(DEST/'manifest.json', {'retrieved': '2026-10-16', 'sources': records})


if __name__ == '__main__':
    main()
