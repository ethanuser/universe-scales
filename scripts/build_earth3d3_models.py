#!/usr/bin/env python3
"""Offline dimensioned illustrations, with measured envelopes and authored detail.

No downloaded artwork or invented scans. Each entry and sources/earth3d3-*.md
distinguishes factual dimensions from illustrative shape controls.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from build_everyday_models import image_texture, mesh
from build_earth3d2_structures import Batch
from geo_glb_common import GLB, grid_indices
from fetch_model_assets import inspect_glb

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT/'handoff/earth3d3'
SOURCES = {
    'rafflesia': 'https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:316069-1/general-information',
    'giant-squid': 'https://ocean.si.edu/ocean-life/invertebrates/giant-squid',
    'hoover-dam': 'https://www.usbr.gov/history/hoover.html',
    'prelude-flng': 'https://www.shell.com.au/about-us/what-we-do/gas-and-lng/prelude-flng-facility/prelude-overview.html',
    'lolong': 'https://www.guinnessworldrecords.com/world-records/117291-largest-crocodile-in-captivity-ever',
}


class Smooth:
    """Merge independently authored smooth surfaces by material."""
    def __init__(self, glb):
        self.glb, self.groups = glb, {}

    def add(self, mat, points, faces):
        points = np.asarray(points, float)
        p, f, count = self.groups.setdefault(mat, [[], [], 0])
        p.append(points); f.append(np.asarray(faces, int).reshape(-1, 3)+count)
        self.groups[mat][2] += len(points)

    def ellipsoid(self, center, radii, mat, rows=20, cols=32):
        lon, lat = np.meshgrid(np.linspace(0, 2*np.pi, cols+1), np.linspace(-np.pi/2, np.pi/2, rows+1))
        p = np.stack((np.cos(lat)*np.cos(lon), np.sin(lat), np.cos(lat)*np.sin(lon)), -1)
        self.add(mat, np.asarray(center)+p.reshape(-1, 3)*radii, grid_indices(rows+1, cols+1))

    def tube(self, points, radius, mat, sides=12):
        points = np.asarray(points, float)
        radius = np.broadcast_to(np.asarray(radius), (len(points),))
        tangent = np.gradient(points, axis=0)
        tangent /= np.linalg.norm(tangent, axis=1)[:, None]
        axis = np.eye(3)[np.argmin(np.abs(tangent), axis=1)]
        side = np.cross(tangent, axis); side /= np.linalg.norm(side, axis=1)[:, None]
        up = np.cross(tangent, side)
        # Prevent frame flips when the reference axis changes along a curve.
        for i in range(1, len(side)):
            projected = side[i-1]-tangent[i]*np.dot(side[i-1], tangent[i])
            if np.linalg.norm(projected) > .01:
                side[i] = projected/np.linalg.norm(projected)
                up[i] = np.cross(tangent[i], side[i])
        a = np.linspace(0, 2*np.pi, sides+1)
        p = points[:, None, :]+radius[:, None, None]*(side[:, None, :]*np.cos(a)[None, :, None]+up[:, None, :]*np.sin(a)[None, :, None])
        self.add(mat, p.reshape(-1, 3), grid_indices(len(points), sides+1).reshape(-1, 3)[:, ::-1])

    def ring(self, center, normal, radius, thickness, mat, sides=12, tube_sides=6):
        normal = np.asarray(normal, float); normal /= np.linalg.norm(normal)
        side = np.cross(normal, np.eye(3)[np.argmin(np.abs(normal))]); side /= np.linalg.norm(side)
        up = np.cross(normal, side)
        a, b = np.meshgrid(np.linspace(0, 2*np.pi, sides+1), np.linspace(0, 2*np.pi, tube_sides+1))
        p = np.asarray(center)+(radius+thickness*np.cos(b))[..., None]*(side*np.cos(a)[..., None]+up*np.sin(a)[..., None])+normal*(thickness*np.sin(b))[..., None]
        self.add(mat, p.reshape(-1, 3), grid_indices(tube_sides+1, sides+1).reshape(-1, 3)[:, ::-1])

    def write(self):
        for mat, (p, f, _) in self.groups.items():
            mesh(self.glb, self.glb.doc['materials'][mat]['name'], np.concatenate(p), np.concatenate(f), mat)


def save(glb, slug, name, reference, presentation, note, measurements):
    model_id = 'earth3d3-'+slug
    # Collapsed polar/terminal rings can leave vertices unused after degenerate
    # triangles are removed. Give only those unused normals a valid fallback.
    # A zero normal on a rendered vertex remains an error, rather than hidden.
    for m in glb.doc['meshes']:
        for prim in m['primitives']:
            a=glb.doc['accessors'][prim['attributes']['NORMAL']]
            view=glb.doc['bufferViews'][a['bufferView']]
            normals=np.ndarray((a['count'],3),'<f4',buffer=glb.bin,offset=view['byteOffset'])
            bad=np.flatnonzero(np.linalg.norm(normals,axis=1)<.5)
            ia=glb.doc['accessors'][prim['indices']];iv=glb.doc['bufferViews'][ia['bufferView']]
            indices=np.ndarray(ia['count'],dtype='<u4' if ia['componentType']==5125 else '<u2',buffer=glb.bin,offset=iv['byteOffset'])
            if np.isin(bad,indices).any():
                raise ValueError('A rendered vertex has no normal')
            normals[bad]=[0,1,0]
    path = ROOT/f'content/visualizations/models/{model_id}.glb'; glb.write(path)
    entry = dict(id=model_id, source=SOURCES[slug], basis_url=SOURCES[slug],
                 basis_label='Dimensions and anatomical or structural basis',
                 author='Universe Scales', license='CC0-1.0', license_url='https://creativecommons.org/publicdomain/zero/1.0/',
                 license_files=['licenses/CC0-1.0.txt'], matches={'length': [name]},
                 geometry='mesh', representation='dimensioned_illustration', volume_semantics='not_applicable',
                 closed_volume_checked=False, presentation=dict(reference_size=reference, **presentation), note=note,
                 processing=dict(script='scripts/build_earth3d3_models.py', units='metres',
                                 source_note=f'content/visualizations/models/sources/{model_id}.md',
                                 measured_constraints=measurements,
                                 details='All other shapes, placements, surface pattern and colors are authored illustration controls, not measured data.'),
                 src=str(path.relative_to(ROOT)), **inspect_glb(path.read_bytes()))
    HANDOFF.mkdir(parents=True, exist_ok=True)
    (HANDOFF/f'{model_id}.entry.json').write_text(json.dumps(entry, indent=2)+'\n')
    print(model_id, entry['bytes'], entry['triangle_count'])


def rafflesia():
    glb = GLB('Universe Scales: Rafflesia arnoldii botanical illustration')
    n = 1024
    rng = np.random.default_rng(317069)
    # Original warty red-brown surface. No photograph or botanical art is copied.
    im = Image.new('RGB', (n, n), '#984638'); draw = ImageDraw.Draw(im)
    for _ in range(1000):
        x, y = rng.uniform(0, n, 2); r = rng.uniform(3, 10)
        c = rng.choice(['#d0a778', '#dcbc91', '#bc946d', '#b98b66'])
        draw.ellipse((x-r, y-r*.7, x+r, y+r*.7), fill=c)
    tex = image_texture(glb, np.asarray(im))
    lobe_mat = glb.material('Authored red-brown lobes and pale warts', rough=.9, texture=tex)
    cup = glb.material('Floral tube, red-brown', (.37, .11, .07, 1), rough=.92)
    disc = glb.material('Central disk and processes', (.55, .26, .12, 1), rough=.92)
    lip = glb.material('Diaphragm, pale rim', (.68, .39, .22, 1), rough=.92, texture=tex)
    bract = glb.material('Basal bracts', (.18, .105, .055, 1), rough=.98)
    s = Smooth(glb)
    # Five distinct thick lobes. Curves and diaphragm proportions are schematic.
    for k in range(5):
        a = 2*np.pi*k/5+np.pi/2
        t, q = np.meshgrid(np.linspace(0, 1, 34), np.linspace(-1, 1, 28), indexing='ij')
        r = .19+.34*t
        width = .14*np.sin(np.pi*t)**.55+.055*(1-t)
        x = r*np.cos(a)-q*width*np.sin(a)
        z = r*np.sin(a)+q*width*np.cos(a)
        y = .12+.115*np.sin(np.pi*t)-.075*t+.025*q*q
        upper = np.stack((x, y, z), -1).reshape(-1, 3)
        lower = upper.copy(); lower[:, 1] -= .022
        f = grid_indices(*t.shape).reshape(-1, 3)
        uv = np.column_stack(((x.ravel()+.55)/1.1, (z.ravel()+.55)/1.1))
        mesh(glb, 'Perigone lobe '+str(k+1), upper, f, lobe_mat, uv=uv)
        mesh(glb, 'Lobe underside '+str(k+1), lower, f[:, ::-1], cup)
        boundary = list(range(t.shape[1]))+[i*t.shape[1]+t.shape[1]-1 for i in range(1,t.shape[0])]+list(range((t.shape[0]-1)*t.shape[1]+t.shape[1]-2,(t.shape[0]-1)*t.shape[1]-1,-1))+[i*t.shape[1] for i in range(t.shape[0]-2,0,-1)]
        wall = np.array([p for i in boundary for p in [upper[i], lower[i]]])
        wf = [(2*i, 2*((i+1)%len(boundary)), 2*i+1) for i in range(len(boundary))]+[(2*i+1, 2*((i+1)%len(boundary)), 2*((i+1)%len(boundary))+1) for i in range(len(boundary))]
        mesh(glb, 'Fleshy lobe edge '+str(k+1), wall, wf, cup)
    # Open floral chamber: real hole in the diaphragm, disk visible inside.
    theta, t = np.meshgrid(np.linspace(0, 2*np.pi, 97), np.linspace(0, 1, 20))
    r = .13+.105*t
    y = .19+.065*np.sin(t*np.pi/2)
    p = np.stack((r*np.cos(theta), y, r*np.sin(theta)), -1)
    uv = np.stack((theta/(2*np.pi), t), -1).reshape(-1, 2)
    mesh(glb, 'Open diaphragm', p.reshape(-1,3), grid_indices(*theta.shape), lip, uv=uv)
    r = .235-.065*t; y=.19-.18*t
    p = np.stack((r*np.cos(theta), y, r*np.sin(theta)), -1)
    mesh(glb, 'Perigone tube',p.reshape(-1,3),grid_indices(*theta.shape),cup)
    s.ellipsoid([0,.045,0],[.17,.04,.17],cup)
    s.ellipsoid([0,.085,0],[.045,.065,.045],disc)
    s.ellipsoid([0,.13,0],[.105,.017,.105],disc)
    # Process count is an illustrative sampling, not a species diagnostic claim.
    for radius, count in [(0,1),(.038,9),(.078,17)]:
        for a in np.linspace(0,2*np.pi,count,endpoint=False):
            x,z=radius*np.cos(a),radius*np.sin(a)
            s.tube([[x,.14,z],[x*1.05,.175,z*1.05],[x*1.07,.192,z*1.07]],[.007,.004,.0005],disc,8)
    for k in range(7):
        a=2*np.pi*k/7
        s.ellipsoid([.13*np.cos(a),.018,.13*np.sin(a)],[.065,.018,.065],bract,8,16)
    s.write()
    # Uniform rescale the complete geometry to an exact 1 m maximum flower span.
    positions = [a for a in glb.doc['accessors'] if a['type']=='VEC3' and 'min' in a]
    lo=np.min([a['min'] for a in positions],axis=0);hi=np.max([a['max'] for a in positions],axis=0)
    scale=1/max((hi-lo)[[0,2]])
    for a in positions:
        v=glb.doc['bufferViews'][a['bufferView']]
        p=np.ndarray((a['count'],3),'<f4',buffer=glb.bin,offset=v['byteOffset'])
        p*=scale;a['min']=p.min(0).tolist();a['max']=p.max(0).tolist()
    save(glb,'rafflesia','Rafflesia',1,dict(pitch=62,yaw=-8,layout_width_factor=1.04),
         'Original botanical illustration of a representative 1 m Rafflesia arnoldii flower. Five fleshy, pale-spotted red-brown perigone lobes surround an open diaphragm and floral chamber with a central column and disk bearing processes. These anatomical relationships follow Kew, Nikolov et al. (2013) and the SIU Parasitic Plant Connection. Only the overall 1 m flower span is calibrated; lobe contours, thickness, chamber proportions, process count, bracts, colors and spot pattern are authored, not a measured specimen or scan. No leaves or independent stem are invented; the host and internal parasite are omitted.',
         {'flower_span_m':1,'perigone_lobes':5})


def squid():
    glb=GLB('Universe Scales: Architeuthis giant squid anatomical illustration')
    skin=glb.material('Authored muted red mantle and arms',(.62,.25,.18,1),rough=.65)
    light=glb.material('Pale sucker rims and underside',(.76,.59,.43,1),rough=.7)
    eye=glb.material('Dark eyes',(.012,.02,.025,1),rough=.12)
    iris=glb.material('Silvery eye surround',(.32,.32,.26,1),rough=.3,metal=.15)
    s=Smooth(glb)
    # The posterior mantle tip and distal feeding club define the 13 m axis.
    # All intermediate profiles and relative lengths are authored, not a specimen.
    x=np.linspace(-6.5,-4.25,80)
    t=(x+6.5)/2.25
    r=.43*np.sin(t*np.pi/2)**.85
    s.tube(np.column_stack((x,np.zeros(len(x)),np.zeros(len(x)))),r,skin,48)
    s.ellipsoid([-4.02,0,0],[.35,.31,.29],skin,24,40)
    for sign in [-1,1]:
        s.ellipsoid([-4.03,.015,sign*.265],[.15,.15,.05],iris,20,28)
        s.ellipsoid([-4.02,.025,sign*.306],[.108,.119,.026],eye,20,28)
        # Small terminal fins, not the large rhomboid fins of a colossal squid.
        f=np.array([[-6.4,0,0],[-5.93,.025,sign*.63],[-5.26,0,sign*.34],[-5.13,0,0]])
        s.add(skin,f,[[0,1,2],[0,2,3]])
    # Eight short arms, two rows of suckers on their inward faces.
    for k in range(8):
        a=2*np.pi*k/8
        t=np.linspace(0,1,65)
        spread=.22+.62*np.sin(np.pi*t*.8)
        center=np.column_stack((-3.72+2.15*t,spread*np.cos(a),spread*np.sin(a)))
        center[:,1]+=.17*np.sin(t*2*np.pi+k*.5)*t*t
        rad=.095*(1-t)**.9+.004
        s.tube(center,rad,skin,12)
        for q in range(3,57,3):
            normal=np.array([0,-np.cos(a),-np.sin(a)])
            lateral=np.array([0,-np.sin(a),np.cos(a)])
            for side in [-1,1]:
                c=center[q]+normal*rad[q]*.85+lateral*rad[q]*.4*side
                s.ring(c,normal,rad[q]*.34,rad[q]*.10,light,10,5)
    for sign in [-1,1]:
        t=np.linspace(0,1,180)
        center=np.column_stack((-3.72+10.22*t,sign*(.18+.32*np.sin(np.pi*t)),.12*np.sin(2*np.pi*t)))
        # Distal clubs widen and taper; stalks stay visibly slender.
        rad=.026+.055*np.exp(-((t-.94)/.055)**2)
        rad[-1]=.002
        s.tube(center,rad,skin,12)
        for q in range(159,178,2):
            for row in [-1,1]:
                c=center[q]+[0,-sign*rad[q]*.8,row*rad[q]*.45]
                s.ring(c,[0,-sign,0],.020,.005,light,10,5)
    s.write()
    save(glb,'giant-squid','Giant Squid',13,dict(yaw=-8,pitch=10,roll=-8,layout_width_factor=1.02),
         'Original Architeuthis anatomical illustration at a 13 m posterior-tip-to-feeding-club span, following the Smithsonian and Natural History Museum female maximum-length estimate. Eight shorter arms, two long feeding tentacles with distal clubs, terminal fins and large lateral eyes follow the Smithsonian anatomical diagram. All intermediate proportions, arm poses, sucker sizes/counts, surface colors and fin contours are authored; this is not a specimen reconstruction, scan, or claim that all squid reach this size. Feeding tentacles are extended to make the total-length definition visible. There are no colossal-squid hooks.',
         {'total_length_m':13,'arms':8,'feeding_tentacles':2})


def hoover():
    glb=GLB('Universe Scales: Hoover Dam dimensioned arch-gravity diagram')
    concrete=glb.material('Warm concrete',(.67,.59,.46,1),rough=.96)
    seams=glb.material('Construction joint recesses',(.33,.29,.23,1),rough=.98)
    roadway=glb.material('Crest roadway',(.14,.15,.15,1),rough=.94)
    cap=glb.material('Crest parapets',(.74,.67,.55,1),rough=.9)
    # USBR: structural height, developed crest length, base and crest thickness.
    height=726.4*.3048; length=1244*.3048; thick0=660*.3048; thick1=45*.3048
    # The 500 ft arch-axis radius is documented in the CEC-hosted historical
    # study (2008, p. 5). Intermediate elevation sections remain schematic.
    radius=500*.3048; half=length/(2*radius)
    theta,t=np.meshgrid(np.linspace(-half,half,97),np.linspace(0,1,49))
    # Illustrative canyon narrows to 23% of crest width at foundation level.
    theta=theta*(.23+.77*t)
    upstream=radius
    thickness=thick1+(thick0-thick1)*(1-t)**1.45
    front=np.stack((upstream*np.sin(theta),height*t,upstream*(1-np.cos(theta))),-1)
    back=front.copy();back[:,:,2]+=thickness
    shape=theta.shape
    # Continuous smooth faces retain the real mass rather than a thin curved wall.
    mesh(glb,'Upstream face, schematic curvature',front.reshape(-1,3),grid_indices(*shape),concrete)
    mesh(glb,'Downstream face, schematic section',back.reshape(-1,3),grid_indices(*shape).reshape(-1,3)[:,::-1],concrete)
    for name,ids in [('Left abutment',[(i,0) for i in range(shape[0])]),('Right abutment',[(i,shape[1]-1) for i in range(shape[0])]),('Foundation',[(0,j) for j in range(shape[1])]),('Crest',[(shape[0]-1,j) for j in range(shape[1])])]:
        p=np.array([p for i,j in ids for p in [front[i,j],back[i,j]]])
        mesh(glb,name,p,grid_indices(len(ids),2),concrete)
    b=Batch(glb)
    # Parapets and contraction-joint lines are illustrative exterior details.
    for j in range(shape[1]-1):
        a,c=front[-1,j].copy(),front[-1,j+1].copy()
        a[1]+=.12;c[1]+=.12;a[2]+=thick1/2;c[2]+=thick1/2
        b.beam(a,c,.18,thick1-.4,roadway)
        for dz in [0,thick1]:
            u,v=a.copy(),c.copy();u[2]+=dz-thick1/2;v[2]+=dz-thick1/2;u[1]+=.8;v[1]+=.8
            b.beam(u,v,1.6,.8,cap)
    for j in range(4,shape[1]-1,4):
        points=back[:,j].copy();points[:,2]+=.05
        b.tube(points,.08,seams,5)
    # Four 395 ft intake towers from USBR; diameter, cap and placement are
    # approximate readings of USACE WCM Plate 3, not surveyed coordinates.
    s=Smooth(glb)
    for x in [-98,98]:
        for z in [-39,-4]:
            top=height+10
            s.tube([[x,top-395*.3048,z],[x,top-9,z]],[8.5,6.5],concrete,32)
            s.tube([[x,top-9,z],[x,top-6,z]],[8,8],cap,32)
            s.tube([[x,top-6,z],[x,top,z]],[6.2,5],concrete,32)
            for a in np.linspace(0,2*np.pi,12,endpoint=False):
                xx,zz=x+6.5*np.cos(a),z+6.5*np.sin(a)
                b.beam([xx,top-8,zz],[xx,top-2,zz],.55,.55,seams)
            b.beam([x,height+1,z],[x,height+1,43],2.8,3.2,concrete)
    s.write()
    b.write()
    save(glb,'hoover-dam','Hoover Dam',height,dict(yaw=78,pitch=5,layout_width_factor=1.28),
         'Original dimensioned arch-gravity illustration of Hoover Dam, with Bureau of Reclamation constraints: 726.4 ft structural height, 1,244 ft developed crest length, 660 ft base thickness, 45 ft crest thickness, and four 395 ft intake towers. The 500 ft arch-axis radius is documented in a CEC-hosted historical study; developed crest length is an arc length, not the straight chord. Tower positions and profiles follow the broad arrangement in USACE Water Control Manual Plate 3. Intermediate curvature, canyon narrowing, thickness interpolation, tower diameters/caps/placement, contraction joints, roadway and parapets are schematic authored geometry, not engineering sections or a surveyed mesh. Canyon terrain, powerhouses, spillways and bypass bridge are omitted. The oblique resting view exposes the massive wedge section while keeping the displayed extent near the listed structural height.',
         {'structural_height_m':height,'developed_crest_length_m':length,'base_thickness_m':thick0,'crest_thickness_m':thick1,'crest_axis_radius_m':radius,'intake_towers':4,'intake_tower_height_m':395*.3048})


def prelude():
    glb=GLB('Universe Scales: Prelude FLNG dimensioned exterior illustration')
    hull=glb.material('Red hull, authored paint',(.46,.045,.024,1),rough=.75)
    bottom=glb.material('Lower hull',(.23,.035,.026,1),rough=.85)
    steel=glb.material('Pale process steel',(.64,.66,.63,1),rough=.55,metal=.18)
    dark=glb.material('Process skid shadow',(.15,.19,.19,1),rough=.86)
    yellow=glb.material('Yellow safety steel',(.8,.51,.045,1),rough=.63,metal=.15)
    white=glb.material('Stern accommodation',(.83,.83,.75,1),rough=.72)
    blue=glb.material('Bridge glazing',(.055,.13,.17,1),rough=.24,metal=.2)
    deck=glb.material('Deck',(.23,.27,.23,1),rough=.88)
    b=Batch(glb)
    s=Smooth(glb)
    # Shell: 488 m long x 74 m wide. IGU 2015–18 FLNG report: 42 m depth.
    # Full hull is shown, not a variable operational waterline.
    sections=[[-244,21,5],[-232,32,1],[-213,37,0],[180,37,0],[217,32,3],[239,14,11],[244,0,17]]
    rings=[]
    for x,w,y in sections:
        rings.append([[x,42,-w],[x,42,w],[x,18,w],[x,y,w*.7],[x,y,-w*.7],[x,18,-w]])
    p=np.array(rings)
    for i in range(len(rings)-1):
        for j in range(6):
            k=(j+1)%6
            mat=deck if j==0 else hull if j in [1,5] else bottom
            b.add(mat,[p[i,j],p[i,k],p[i+1,k],p[i+1,j]],[[0,1,2],[0,2,3]])
    for i in [0,len(rings)-1]:
        b.add(hull,[p[i].mean(0),*p[i]],[(0,j+1,(j+1)%6+1) for j in range(6)])
    # Main organization follows Shell construction footage: stern accommodation,
    # low central pipe corridor, process modules amidships, forward turret.
    # Sizes and member counts below are illustration controls, not a plant plan.
    for y in np.arange(44,73,3.2):
        b.beam([-201,y,-31],[-201,y,31],27,3.05,white)
        for z in [-31.1,31.1]:
            for x in np.arange(-212,-190,3):
                b.beam([x,y+.2,z],[x+1.25,y+.2,z],.8,.08,blue)
    b.beam([-199,74,-35],[-199,74,35],31,3.4,white)
    b.beam([-183.4,74.5,-33],[-183.4,74.5,33],.2,1.7,blue)
    # Two rows of seven schematic process modules, matching Shell's 14-module description.
    for x in np.linspace(-148,142,7):
        for sign in [-1,1]:
            z=sign*21
            b.beam([x-18,45,z],[x+18,45,z],4,25,dark)
            top=68+6*np.sin(x*.03)**2
            for dx in [-17,17]:
                for dz in [-12,12]:
                    b.beam([x+dx,46,z+dz],[x+dx,top,z+dz],.65,.65,steel)
            for y in [52,60,top]:
                for dz in [-12,12]:
                    b.beam([x-17,y,z+dz],[x+17,y,z+dz],.65,.65,steel)
                for dx in [-17,17]:
                    b.beam([x+dx,y,z-12],[x+dx,y,z+12],.65,.65,steel)
            for dx in [-11,0,11]:
                s.tube([[x+dx,48,z-9],[x+dx,48,z+9]],2.3,steel,12)
                s.tube([[x+dx,59,z-8],[x+dx,59,z+8]],1.6,steel,12)
            b.beam([x-17,top,z-12],[x+17,top,z+12],.35,.35,yellow)
    for z in [-4,-2,0,2,4]:
        b.tube([[-165,51,z],[166,51,z]],.48,steel,8)
    # Forward turret is context above the hull; subsea moorings are omitted.
    s.tube([[193,42,0],[193,57,0]],[15,15],steel,40)
    # Authored flare lattice and crane booms, visually checked against Shell footage.
    for a in np.linspace(0,2*np.pi,4,endpoint=False):
        b.beam([186+7*np.cos(a),55,7*np.sin(a)],[186+2*np.cos(a),119,2*np.sin(a)],.55,.55,yellow)
    for y in np.arange(58,118,7):
        f=(119-y)/64
        for a in np.linspace(0,2*np.pi,4,endpoint=False):
            b.beam([186+7*f*np.cos(a),y,7*f*np.sin(a)],[186+7*(f-.109)*np.cos(a+np.pi/2),y+7,7*(f-.109)*np.sin(a+np.pi/2)],.3,.3,steel)
    for x,z in [(-157,-29),(101,29)]:
        b.beam([x,44,z],[x,72,z],2,2,yellow)
        b.beam([x,72,z],[x+36,84,z],.9,.9,yellow)
        b.beam([x+36,84,z],[x+36,56,z],.12,.12,dark)
    s.write();b.write()
    save(glb,'prelude-flng','Prelude FLNG',488,dict(yaw=-20,pitch=13,layout_width_factor=1.05),
         'Original exterior illustration of Prelude FLNG, using Shell’s 488 m overall length and 74 m width and the International Gas Union 2015–2018 FLNG report’s 42 m hull depth. The full hull is shown. Stern accommodation, the central pipe corridor, process modules and forward turret follow the broad arrangement visible in Shell’s construction films; fourteen module frames refer to Shell’s stated fourteen topside modules. Hull sections, module dimensions/equipment, crane and flare geometry, colors and all smaller details are authored schematic approximations, not a shipyard or process-engineering model. Subsea turret extent, mooring chains, risers, internal tanks and operational waterline are omitted.',
         {'length_m':488,'beam_m':74,'hull_depth_m':42,'topside_modules':14})


def crocodile():
    glb=GLB('Universe Scales: saltwater crocodile illustration at Lolong total length')
    skin=glb.material('Authored grey-olive adult skin',(.25,.27,.18,1),rough=.88)
    plate=glb.material('Dorsal osteoderms',(.19,.21,.13,1),rough=.92)
    belly=glb.material('Cream-colored ventral skin',(.55,.50,.34,1),rough=.9)
    dark=glb.material('Mouth seam and nostrils',(.032,.035,.023,1),rough=.95)
    iris=glb.material('Bronze iris',(.48,.33,.085,1),rough=.36)
    pupil=glb.material('Vertical pupil',(.012,.014,.009,1),rough=.18)
    tooth=glb.material('Small exposed teeth and claws',(.69,.65,.48,1),rough=.65)
    s=Smooth(glb)
    s.ellipsoid([.7,.41,0],[1.12,.34,.45],skin,28,48)
    s.ellipsoid([.7,.23,0],[1.03,.12,.39],belly,16,36)
    s.ellipsoid([1.81,.46,0],[.48,.24,.32],skin,20,32)
    # Heavy, broad, low snout. These are an authored adult's proportions;
    # no specimen-specific head or girth dimensions are asserted.
    x=np.linspace(2.08,3.085,50)
    width=np.interp(x,[2.08,2.30,2.65,3.00,3.085],[.26,.26,.20,.15,0])
    height=np.interp(x,[2.08,2.30,2.65,3.00,3.085],[.19,.19,.105,.085,0])
    a=np.linspace(0,2*np.pi,49)
    y=.45+height[:,None]*np.sin(a)
    z=width[:,None]*np.cos(a)
    p=np.stack((np.broadcast_to(x[:,None],y.shape),y,z),-1)
    s.add(skin,p.reshape(-1,3),grid_indices(len(x),len(a)))
    for sign in [-1,1]:
        s.ellipsoid([2.33,.59,sign*.20],[.15,.10,.09],skin,16,24)
        s.ellipsoid([2.35,.62,sign*.265],[.062,.048,.015],iris,14,20)
        s.ellipsoid([2.36,.624,sign*.278],[.009,.037,.004],pupil,12,16)
        s.ellipsoid([3.005,.525,sign*.063],[.035,.01,.019],dark,10,16)
        xs=np.linspace(2.26,3.055,35)
        zs=np.interp(xs,x,width)*sign
        s.tube(np.column_stack((xs,np.full(len(xs),.414),zs)),.008,dark,6)
        for q in range(8):
            xx=2.39+q*.072; zz=float(np.interp(xx,x,width))*sign
            s.tube([[xx,.413,zz],[xx+.005,.385,zz+sign*.004]],[.009,.001],tooth,7)
    # Long muscular tail; low lateral bend is illustrative and does not change
    # its calibrated straight nose-to-tail extent.
    x=np.linspace(-.3,-3.085,110)
    t=(-x-.3)/2.785
    a=np.linspace(0,2*np.pi,33)
    ry=.29*(1-t)**.65+.001;rz=.34*(1-t)**1.15+.0002
    cy=.35*(1-t)+.08*t;cz=.12*np.sin(np.pi*t)
    p=np.stack((np.broadcast_to(x[:,None],(len(x),len(a))),cy[:,None]+ry[:,None]*np.sin(a),cz[:,None]+rz[:,None]*np.cos(a)),-1)
    s.add(skin,p.reshape(-1,3),grid_indices(len(x),len(a)).reshape(-1,3)[:,::-1])
    # Raised back plates and paired-to-single tail keels are visible anatomy,
    # with schematic count/size rather than an identification-key scute map.
    for xx in np.linspace(-.14,1.57,18):
        for zz in [-.28,-.14,0,.14,.28]:
            yy=.41+.34*np.sqrt(max(0,1-((xx-.7)/1.12)**2-(zz/.48)**2))
            s.ellipsoid([xx,yy,zz],[.058,.023,.057],plate,6,10)
            s.tube([[xx-.045,yy+.008,zz],[xx,yy+.06,zz],[xx+.044,yy+.008,zz]],[.008,.014,.008],plate,6)
    for q in range(3,105,4):
        for sign in ([-1,1] if t[q]<.5 else [0]):
            zz=cz[q]+sign*rz[q]*.5;yy=cy[q]+ry[q]*.92
            points=[[x[q]-.065,yy,zz-.016],[x[q]+.06,yy,zz-.016],[x[q]+.025,yy+.10*(1-t[q])+.015,zz],
                    [x[q]-.065,yy,zz+.016],[x[q]+.06,yy,zz+.016]]
            s.add(plate,points,[[0,1,2],[4,3,2],[0,2,3],[1,4,2],[0,3,4],[0,4,1]])
    # Four short splayed limbs; the hind feet have four toes, forefeet five.
    for front in [False,True]:
        xx=1.35 if front else -.10
        for sign in [-1,1]:
            hip=np.array([xx,.38,sign*.31])
            elbow=np.array([xx+(.15 if front else -.27),.17,sign*.66])
            foot=np.array([xx+(.40 if front else -.02),.075,sign*.78])
            s.tube([hip,elbow,foot],[.13,.105,.05],skin,16)
            for k in range(5 if front else 4):
                a=(k-2)*.24
                end=foot+np.array([.15+.07*np.cos(a),-.02,sign*.11*np.sin(a*2)])
                s.tube([foot,end],[.029,.008],skin,8)
                if k<3:
                    s.tube([end,end+[.025,-.008,0]],[.009,.0005],tooth,6)
    s.write()
    save(glb,'lolong','Lolong the Crocodile',6.17,dict(yaw=-15,pitch=20,layout_width_factor=1.02),
         'Original adult saltwater crocodile (Crocodylus porosus) anatomical illustration uniformly calibrated to Lolong’s Guinness-verified 6.17 m nose-to-tail length. The Australian Museum supplies the broad snout, heavy adult build, dorsal eyes/nostrils, osteoderms, muscular tail and cream-colored belly. Head, girth, limbs, scute pattern/count, tail profile, colors and pose are authored generic adult geometry, not measurements or a reconstruction of Lolong himself. Mouth is almost closed; visible teeth are schematic and not a dental inventory. This is not a scan, juvenile, freshwater crocodile, alligator or game asset.',
         {'nose_to_tail_length_m':6.17})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('models',nargs='*',choices=['rafflesia','squid','hoover','prelude','crocodile'])
    args=parser.parse_args()
    for name in args.models or ['rafflesia','squid','hoover','prelude','crocodile']:
        globals()[name]()
