#!/usr/bin/env python3
"""CPU approximation of GLB soft points, not a WebGL or explorer certification."""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from render_glb_preview import accessor, read_glb

ROOT=Path(__file__).resolve().parents[1]


def render(entry, yaw=0, drawn_pixels=430, canvas_size=560):
    doc,binary=read_glb(ROOT/entry["src"])
    cfg=entry["presentation"]
    image=np.zeros((canvas_size,canvas_size,3),float)
    reference=cfg["reference_size"]
    angle=math.radians(yaw)
    rotation=np.array([[math.cos(angle),0,math.sin(angle)],[0,1,0],[-math.sin(angle),0,math.cos(angle)]])
    extent=None
    for node in doc["nodes"]:
        if "mesh" not in node:continue
        for prim in doc["meshes"][node["mesh"]]["primitives"]:
            if prim.get("mode")!=0:raise ValueError("Preview expects catalog POINTS")
            p=accessor(doc,binary,prim["attributes"]["POSITION"])
            p=p-(p.min(0)+p.max(0))/2
            p=p@rotation.T
            extent=np.ptp(p,axis=0)
            rgba=accessor(doc,binary,prim["attributes"]["COLOR_0"])/255
            # Approximate Three.js output color conversion and additive soft sprite.
            rgb=np.where(rgba[:,:3]<=.0031308,rgba[:,:3]*12.92,1.055*rgba[:,:3]**(1/2.4)-.055)
            setting=node["extras"]["pointSize"]
            wanted=drawn_pixels*setting["perPixel"]
            size=np.clip(wanted,.35,setting["max"])
            gain=max(1,wanted/size)**2
            x=p[:,0]/reference*drawn_pixels+canvas_size/2
            y=-p[:,1]/reference*drawn_pixels+canvas_size/2
            # Subpixel supersampling avoids dropping tiny distant catalog points.
            radius=max(1,int(math.ceil(size/2)))
            for dy in range(-radius,radius+1):
                for dx in range(-radius,radius+1):
                    ix=np.floor(x).astype(int)+dx;iy=np.floor(y).astype(int)+dy
                    r=np.hypot((ix+.5-x)*2/size,(iy+.5-y)*2/size)
                    t=np.clip((r-.55)/.45,0,1)
                    weight=np.exp(-3*r*r)*(1-t*t*(3-2*t))*rgba[:,3]*gain
                    keep=(ix>=0)&(ix<canvas_size)&(iy>=0)&(iy<canvas_size)&(weight>0)
                    for c in range(3):np.add.at(image[:,:,c],(iy[keep],ix[keep]),rgb[keep,c]*weight[keep])
    image+=np.array([7,13,24])/255
    return Image.fromarray(np.uint8(np.clip(image,0,1)*255)),extent


def main():
    dest=ROOT/"handoff/deepsky3d/previews";dest.mkdir(parents=True,exist_ok=True)
    tiles=[]
    for path in sorted((ROOT/"handoff/deepsky3d").glob("*.entry.json")):
        e=json.loads(path.read_text())
        panel=Image.new("RGB",(1120,640),"#070d18");draw=ImageDraw.Draw(panel)
        for k,yaw in enumerate([0,90]):
            im,extent=render(e,yaw)
            panel.paste(im,(560*k,35))
            draw.text((10+560*k,15),e["matches"]["length"][0]+(" | rest" if k==0 else " | quarter-turn"),fill="white")
        small,_=render(e,drawn_pixels=120,canvas_size=150)
        small.save(dest/(e["id"]+"-small.png"))
        draw.text((10,610),"CPU soft-point approximation | physical coordinates retained | no WebGL, perspective, explorer or mobile verification",fill="#e0be81")
        panel.save(dest/(e["id"]+".png"));tiles.append(panel.resize((896,512)))
    sheet=Image.new("RGB",(1792,512*math.ceil(len(tiles)/2)),"#070d18")
    for i,tile in enumerate(tiles):sheet.paste(tile,(i%2*896,i//2*512))
    sheet.save(dest/"overview.png")


if __name__=="__main__":main()
