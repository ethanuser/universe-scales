#!/usr/bin/env python3
"""Stage official PDB mmCIF files and retain compact, unscaled structural data.

Network preparation is separate from the offline GLB builder. Large upstream
files remain in --cache; the retained NPZ arrays are CC0 coordinate derivatives.
"""
import argparse
import gzip
import hashlib
import json
import shlex
import ssl
from pathlib import Path
from urllib.request import urlopen

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'content/visualizations/models/sources/bio3d'
PDB_IDS = ('5ET3', '1KX5', '6VXX', '6BNO', '6DPU', '4V88', '7R5K', '2TMV')


def category(text, name):
    """Read a selected mmCIF category, including semicolon-delimited values.

    Deliberately handles the official, one-category-per-block mmCIF export;
    rejects ragged records rather than silently misreading coordinates.
    """
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(name + '.'))
    stop = next((i for i in range(start, len(lines)) if lines[i].startswith('#')), len(lines))
    block = lines[start:stop]
    if not lines[start-1].strip() == 'loop_':
        tokens = cif_tokens(block)
        return [{tokens[i].split('.', 1)[1]: tokens[i+1] for i in range(0, len(tokens), 2)}]
    count = next(i for i, line in enumerate(block) if not line.startswith(name + '.'))
    fields = [line.strip().split('.', 1)[1] for line in block[:count]]
    if name == '_atom_site':
        rows = [[v[1:-1] if v[:1] in ('"', "'") and v[-1:] == v[:1] else v
                 for v in line.split()] for line in block[count:] if line.strip()]
        if any(len(row) != len(fields) for row in rows):
            raise ValueError('Unexpected atom-site row layout')
        return [dict(zip(fields, row, strict=True)) for row in rows]
    tokens = cif_tokens(block[count:])
    if len(tokens) % len(fields):
        raise ValueError(f'Ragged {name} category')
    return [dict(zip(fields, tokens[i:i+len(fields)], strict=True))
            for i in range(0, len(tokens), len(fields))]


def cif_tokens(lines):
    result, multiline = [], None
    for line in lines:
        if line.startswith(';'):
            if multiline is None:
                multiline = [line[1:]]
            else:
                result.append('\n'.join(multiline).strip())
                multiline = None
        elif multiline is not None:
            multiline.append(line)
        else:
            result.extend(shlex.split(line, comments=False))
    if multiline is not None:
        raise ValueError('Unterminated mmCIF text')
    return result


def prepare(pdb, cache, destination=SOURCE):
    context = ssl.create_default_context(cafile='/etc/ssl/cert.pem')
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f'{pdb}.cif.gz'
    url = f'https://files.rcsb.org/download/{pdb}.cif.gz'
    if not path.exists():
        path.write_bytes(urlopen(url, context=context, timeout=120).read())
    raw = gzip.decompress(path.read_bytes())
    text = raw.decode()
    atoms = category(text, '_atom_site')
    # Remove waters, hydrogen, alternative conformers and zero occupancy.
    # NPC retains C-alpha only for an explicitly coarse scaffold envelope.
    keep = [a for a in atoms if a['label_comp_id'] not in ('HOH', 'DOD')
            and a['type_symbol'] not in ('H', 'D') and a['label_alt_id'] in ('.', 'A')
            and float(a['occupancy']) > 0 and a['pdbx_PDB_model_num'] == '1'
            and (pdb != '7R5K' or a['label_atom_id'] == 'CA')]
    if pdb == '5ET3':
        keep = [a for a in keep if a['label_comp_id'] == '60C']
        keep = [a for a in keep if a['label_asym_id'] == keep[0]['label_asym_id']]
    arrays = {key: np.array([a[field] for a in keep]) for key, field in
              [('chain', 'label_asym_id'), ('entity', 'label_entity_id'),
               ('residue', 'label_comp_id'), ('sequence', 'label_seq_id'),
               ('atom', 'label_atom_id'), ('element', 'type_symbol')]}
    xyz = np.array([[float(a['Cartn_' + axis]) for axis in 'xyz'] for a in keep], dtype=np.float32)
    arrays['xyz'] = xyz
    destination.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(destination / f'{pdb}.npz', **arrays)
    metadata_path = cache / f'{pdb}.json'
    if not metadata_path.exists():
        metadata_path.write_bytes(urlopen(f'https://data.rcsb.org/rest/v1/core/entry/{pdb}',
                                         context=context, timeout=60).read())
    api = json.loads(metadata_path.read_text())
    meta = {'pdb': pdb, 'url': url, 'source_sha256': hashlib.sha256(raw).hexdigest(),
            'compressed_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'retained_npz_sha256': hashlib.sha256((destination/f'{pdb}.npz').read_bytes()).hexdigest(),
            'retained_atoms': len(keep), 'unit': 'angstrom',
            'citation': api['rcsb_primary_citation'], 'title': api['struct']['title'],
            'assembly_gen': category(text, '_pdbx_struct_assembly_gen'),
            'operations': category(text, '_pdbx_struct_oper_list')}
    (destination / f'{pdb}.json').write_text(json.dumps(meta, indent=2) + '\n')
    print(pdb, len(keep), 'atoms;', len(set(arrays['chain'])), 'chains; extent A:', np.ptp(xyz, axis=0))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache', type=Path, default=Path('/tmp/bio3d-source'))
    p.add_argument('--pdb', nargs='+', choices=PDB_IDS, default=PDB_IDS)
    args = p.parse_args()
    for pdb in args.pdb:
        prepare(pdb, args.cache)


if __name__ == '__main__':
    main()
