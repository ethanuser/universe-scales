#!/usr/bin/env python3
"""Before/after textured CPU review; not production WebGL verification.

./venv/bin/python scripts/preview_upgrade3d_cpu.py --old-model /tmp/upgrade3d-old-basketball.glb
The previous registry entry is pinned in handoff/upgrade3d/research/.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

from render_earth3d_previews import parts, render

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / 'handoff/upgrade3d'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old-model', type=Path, required=True)
    args = parser.parse_args()
    old = json.loads((HANDOFF / 'research/basketball-previous.json').read_text())
    new = json.loads((HANDOFF / 'upgrade3d-basketball-scan.entry.json').read_text())
    before, old_bounds = parts(args.old_model, old['presentation'])
    after, new_bounds = parts(ROOT / new['src'], new['presentation'])
    out = HANDOFF / 'previews'
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for side in (False, True):
        pair = Image.new('RGB', (1400, 770), '#101927')
        draw = ImageDraw.Draw(pair)
        row = {'view': 'quarter-turn' if side else 'rest'}
        for i, (scene, label) in enumerate(((before, 'BEFORE: dimensioned illustration'),
                                          (after, 'AFTER: robin.sculac photoscan'))):
            picture, extent = render(scene, side, 700)
            pair.paste(picture, (i * 700, 0))
            draw.text((i * 700 + 16, 710), label, fill='white')
            draw.text((i * 700 + 16, 730), f'Projected extent: {extent:.4f} x catalog diameter', fill='white')
            row['before' if i == 0 else 'after'] = extent
        draw.text((16, 750), 'CPU ORTHOGRAPHIC: no production lighting / reflections / normal maps / perspective / UI', fill='#ddbd80')
        pair.save(out / f'basketball-{row["view"]}.png')
        records.append(row)

    # Render directly at these pixel sizes; do not just shrink the large preview.
    small = Image.new('RGB', (900, 380), '#101927')
    draw = ImageDraw.Draw(small)
    for i, scene in enumerate((before, after)):
        draw.text((i * 450 + 16, 16), 'BEFORE' if i == 0 else 'AFTER', fill='white')
        for j, size in enumerate((48, 96, 160)):
            picture, _ = render(scene, False, size)
            small.paste(picture, (i * 450 + 16 + j * 104, 130 - size // 2))
            draw.text((i * 450 + 16 + j * 104, 245), f'{size} px canvas', fill='white')
    draw.text((16, 310), 'Direct CPU rasterization at each canvas size; model occupies about 84%.', fill='white')
    draw.text((16, 335), 'This is a readability check, not a browser/mobile performance result.', fill='#ddbd80')
    small.save(out / 'basketball-small.png')
    (out / 'geometry-audit.json').write_text(json.dumps({
        'method': 'Textured CPU orthographic previews with registry transforms; not production model_lab.',
        'source_bounds': {'before': old_bounds, 'after': new_bounds},
        'views': records,
    }, indent=2) + '\n')

    # Verify the special-case color request against the unchanged current model.
    registry = json.loads((ROOT / 'content/visualizations/models.json').read_text())
    titanic = next(e for e in registry['models'] if e['id'] == 'earth3d3-titanic')
    scene, _ = parts(ROOT / titanic['src'], titanic['presentation'])
    picture, _ = render(scene, False, 900)
    proof = Image.new('RGB', (900, 950), '#101927')
    proof.paste(picture, (0, 0))
    draw = ImageDraw.Draw(proof)
    draw.text((16, 910), 'UNCHANGED TITANIC: existing black upper hull / red lower hull', fill='white')
    draw.text((16, 930), 'CPU reference only; no replacement or recoloring in this job.', fill='#ddbd80')
    proof.save(out / 'titanic-existing-black-hull.png')


if __name__ == '__main__':
    main()
