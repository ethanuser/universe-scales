#!/usr/bin/env python3
"""Re-register this batch after merging its files; no dataset edits or git actions."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
from register_model import register

for path in sorted(Path(__file__).parent.glob('*.entry.json')):
    entry = json.loads(path.read_text())
    if entry['id'] == 'cassini-hyperion-shape':
        print('Skip Hyperion until the distinct Hyperion Moon item exists')
        continue
    register(path, ROOT/entry['src'], 'length')
