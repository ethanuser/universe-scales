#!/usr/bin/env python3
"""Original CPU illustration of the existing CC0 4V88 biological-assembly mesh.

No production screenshot is claimed. Geometry is the existing authored smooth
envelope around experimental coordinates; vertex/chain colors are illustrative.
This deliberately does not change a model or reuse a PDB-101 copyrighted figure.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from render_glb_preview import accessor, read_glb
from import_images import export


def main():
    source=ROOT/'content/visualizations/models/pdb-4v88-ribosome.glb'
    doc,binary=read_glb(source)
    # The source mesh is already one biological assembly; no invented subunits.
    a=.28;b=-.40
    rx=np.array([[1,0,0],[0,np.cos(a),-np.sin(a)],[0,np.sin(a),np.cos(a)]])
    ry=np.array([[np.cos(b),0,np.sin(b)],[0,1,0],[-np.sin(b),0,np.cos(b)]])
    matrix=rx@ry
    parts=[]
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            at=p['attributes'];v=accessor(doc,binary,at['POSITION']).astype(float)@matrix.T
            ids=accessor(doc,binary,p['indices']).reshape(-1,3)
            c=accessor(doc,binary,at['COLOR_0'])[:,:3].astype(float)
            if doc['accessors'][at['COLOR_0']]['componentType']==5121:c/=255
            n=accessor(doc,binary,at['NORMAL']).astype(float)@matrix.T
            light=np.array([-.35,.6,1]);light/=np.linalg.norm(light)
            shade=.23+.82*np.maximum(0,n@light)
            color=np.clip(c*shade[:,None],0,1)**(1/2.2)
            parts.append((v[ids],np.round(color[ids].mean(1)*255).astype(np.uint8)))
    triangles=np.concatenate([p[0] for p in parts]);colors=np.concatenate([p[1] for p in parts])
    low=triangles.min((0,1));high=triangles.max((0,1));center=(low+high)/2
    scale=min(650/(high[0]-low[0]),475/(high[1]-low[1]))
    screen=np.stack(((triangles[...,0]-center[0])*scale+400,-(triangles[...,1]-center[1])*scale+435),axis=-1)
    aa=2;im=Image.new('RGB',(1200*aa,800*aa),'#081321');draw=ImageDraw.Draw(im)
    for i in np.argsort(triangles[...,2].mean(1)):
        draw.polygon([tuple(v*aa) for v in screen[i]],fill=tuple(colors[i]))
    im=im.resize((1200,800),Image.Resampling.LANCZOS);draw=ImageDraw.Draw(im)
    def label(x,y,t,size=28,color='#edf4fc'):
        draw.text((x,y),t,font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',size),fill=color)
    draw.line((56,39,100,39),fill='#ffd398',width=4)
    label(56,58,'Ribosome',46)
    label(56,119,'A complete eukaryotic particle · yeast 80S · PDB 4V88',25,'#a5b8cd')
    label(823,290,'RNA',35,'#ffd398');label(823,343,'Gold',26,'#a5b8cd')
    label(823,429,'Proteins',35,'#83d8f2');label(823,482,'Other chain colors',26,'#a5b8cd')
    label(56,698,'Coordinate-based illustration · smooth display surface and colors are authored',23,'#a5b8cd')
    draw.line((56,741,1144,741),fill='#24364a')
    label(56,759,'Original molecular illustration · CC0',20,'#a5b8cd')
    label(780,759,'Ben-Shem et al. (2011)',20,'#a5b8cd')
    original=HERE/'diagrams/ribosome-render.png';original.parent.mkdir(exist_ok=True);im.save(original)
    export(im,'length_ribosome.jpg')
    record=dict(file='images/length_ribosome.jpg',source='https://www.rcsb.org/structure/4V88',
        title='Complete yeast 80S ribosome — original coordinate-based illustration',
        author='Universe Scales (rendering); Ben-Shem et al. (2011), PDB 4V88 (structural data)',
        license='CC0',license_url='https://creativecommons.org/publicdomain/zero/1.0/',
        changes='New CPU rendering of biological assembly 1 of PDB 4V88 using the existing authored GLB; includes the complete deposited yeast 80S particle and Stm1. RNA gold; protein chain colors illustrative. Smooth surface is a display envelope around atomic sites, not experimental electron density. Unresolved residues, waters and ions omitted. JPEG 1200 × 800; matching 300 × 200 thumbnail.')
    (HERE/'ribosome-credits.json').write_text(json.dumps([record],ensure_ascii=False,indent=2)+'\n')
    (HERE/'sources/ribosome.json').write_text(json.dumps(dict(source=record['source'],accessed='2026-10-16',
        license_source='https://www.wwpdb.org/about/usage-policies',data_license='CC0 1.0',
        citation='Ben-Shem et al., The structure of the eukaryotic ribosome at 3.0 angstrom resolution, Science (2011), doi:10.1126/science.1212642',
        mesh=str(source.relative_to(ROOT)),mesh_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        representation=record['changes']),ensure_ascii=False,indent=2)+'\n')
    print('Rendered complete 4V88 yeast 80S ribosome.')


if __name__=='__main__':main()
