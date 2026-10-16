#!/usr/bin/env python3
"""Re-register this batch after the lead merges source files and dataset updates.

Run with ./venv/bin/python handoff/space3d3/integrate.py from this checkout.
It writes only this checkout's model registry, never the dataset or other branches.
"""
import json
import sys
from pathlib import Path

import yaml

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from register_model import register


def main():
    items={e['name']:e for e in yaml.safe_load((ROOT/'dataset/raw/legacy_yaml/length.yaml').read_text())['items']}
    pending=[]
    for path in sorted(Path(__file__).parent.glob('*.entry.json')):
        entry=json.loads(path.read_text())
        required=entry.get('requires_dataset')
        if required and float(items.get(required['name'],{}).get('value',0))!=required['value_m']:
            pending.append(f"{entry['id']}: set {required['name']} to {required['value_m']} m first")
            continue
        registry=json.loads((ROOT/'content/visualizations/models.json').read_text())['models']
        match=set(entry['matches']['length'])
        conflict=next((m for m in registry if m['id']!=entry['id'] and match.intersection(m.get('matches',{}).get('length',[]))),None)
        if conflict:
            pending.append(f"{entry['id']}: another model already owns this item ({conflict['id']}); review before replacing")
            continue
        register(path,ROOT/entry['src'],'length')
    if pending:
        print('\nPending integration:')
        for message in pending: print('- '+message)
        return 1
    return 0


if __name__=='__main__':sys.exit(main())
