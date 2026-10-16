#!/usr/bin/env python3
"""Render all terrain3d handoff models using the existing CPU depth rasterizer.

These orthographic rest/side images do not verify WebGL, production materials,
constant-pixel line widths, labels, perspective, explorer grounding, or mobile.
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from preview_space3d2_cpu import render


if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    entries=sorted((root/'handoff/terrain3d').glob('*.entry.json'))
    dest=root/'handoff/terrain3d/previews';dest.mkdir(parents=True,exist_ok=True)
    audit=[];tiles=[]
    for path in entries:
        e=json.loads(path.read_text());panel=Image.new('RGB',(1120,615),'#07121e')
        for side in [False,True]:
            im,extent=render((root/e['src']).read_bytes(),e['presentation'],quarter=side,size=560)
            panel.paste(im,(560*int(side),20))
            if not side:
                ratio=float(max(extent[:2])/e['presentation']['reference_size'])
                audit.append(dict(id=e['id'],rest_extent=ratio,passes_extent_rule=.6<=ratio<=1.3))
        draw=ImageDraw.Draw(panel)
        draw.text((10,4),e['id']+' | rest / quarter camera',fill='white')
        draw.text((10,590),'CPU ORTHOGRAPHIC APPROXIMATION - no WebGL, production lighting/labels, or mobile verification',fill='#ddbd80')
        panel.save(dest/(e['id']+'.png'));tiles.append(panel.resize((720,395)))
        print(e['id'],ratio,flush=True)
    sheet=Image.new('RGB',(1440,395*math.ceil(len(tiles)/2)),'#07121e')
    for i,tile in enumerate(tiles):sheet.paste(tile,(i%2*720,i//2*395))
    sheet.save(dest/'overview.png')
    (dest/'geometry-audit.json').write_text(json.dumps(dict(method=__doc__,models=audit),indent=2)+'\n')
