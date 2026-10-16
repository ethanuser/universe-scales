#!/usr/bin/env python3
"""Original CC0 explanatory figures; render editable SVG sources with PyMuPDF.
No source image pixels, invented catalog coordinates, or measured density data.
Run with a Python containing pymupdf and Pillow (temporary venv is sufficient).
"""
import json,math,random
from pathlib import Path
import pymupdf
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'diagrams';OUT.mkdir(exist_ok=True)
BG='#081322';INK='#ecf3fc';MUTED='#a8b9d0';BLUE='#77cff5';GOLD='#ffd398'

def text(x,y,s,size=28,fill=INK,anchor='start'):
 return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" text-anchor="{anchor}" font-family="Arial,Helvetica,sans-serif">{s}</text>'
def line(x1,y1,x2,y2,color=BLUE,width=3,dash=''):
 return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}"/>'
def circle(x,y,r,fill,stroke='none',sw=2):
 return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def frame(title,subtitle):
 return '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">'+f'<rect width="1200" height="800" fill="{BG}"/>'+text(64,81,title,44)+text(64,124,subtitle,24,MUTED)
def save(stem,s):
 p=OUT/(stem+'.svg');p.write_text(s+'</svg>')
 doc=pymupdf.open(p);png=doc[0].get_pixmap(matrix=pymupdf.Matrix(2,2));png.save(OUT/(stem+'.png'))
 im=Image.open(OUT/(stem+'.png')).convert('RGB');im.thumbnail((1200,1200),Image.Resampling.LANCZOS)
 name='length_'+stem+'.jpg';im.save(ROOT/'images'/name,quality=92,optimize=True)
 im.resize((300,round(im.height*300/im.width)),Image.Resampling.LANCZOS).save(ROOT/'images/thumbs'/name,quality=88,optimize=True)
 (OUT/(stem+'.png')).unlink()

s=frame('Hubble radius','The distance where expansion gives a recession speed of light')
# A dimensional schematic, not a map or a physical shell.
s+=circle(302,400,182,'#0c2034',BLUE,2)+circle(302,400,5,INK)
s+=line(302,400,483,400,GOLD,4)+text(397,382,'R = c / H₀',29,GOLD,'middle')
s+=text(302,623,'A distance marker',27,INK,'middle')+text(302,660,'No physical wall at this radius',23,MUTED,'middle')
x0,y0=692,583;scale=195
for k in [0,1,2]:
 x=x0+k*scale;y=y0-k*scale
 s+=line(x0,y,x0+2*scale,y,'#21344a',1)+line(x,y0,x,y0-2*scale,'#21344a',1)
 s+=text(x,y0+34,str(k),21,MUTED,'middle')+text(x0-18,y+7,str(k),21,MUTED,'end')
s+=line(x0,y0,x0+2*scale,y0,INK,2)+line(x0,y0,x0,y0-2*scale,INK,2)
s+=line(x0,y0,x0+2*scale,y0-2*scale,BLUE,5)
s+=line(x0+scale,y0,x0+scale,y0-scale,GOLD,2,'8 7')+line(x0,y0-scale,x0+scale,y0-scale,GOLD,2,'8 7')
s+=circle(x0+scale,y0-scale,8,GOLD)+text(x0+scale+20,y0-scale-18,'v = c',29,GOLD)
s+=text(892,665,'Distance / Hubble radius',23,MUTED,'middle')+text(691,175,'Recession speed / c',23,MUTED)
s+=text(650,716,'v = H₀ d · expansion at one cosmic time',23,INK)
s+=text(64,756,'Original explanatory diagram · NASA/WMAP Hubble law · CC0',20,MUTED)
save('hubble_radius',s)

s=frame('One-nanometer transistor gate','The 2016 carbon-nanotube gate experiment · cross-section schematic')
# Only the nanotube diameter is dimensioned. Layer heights and contacts are illustrative.
s+=f'<rect x="145" y="290" width="740" height="167" rx="4" fill="#263d56"/>'
s+=f'<rect x="145" y="457" width="740" height="150" fill="#344b60"/>'
s+=f'<rect x="145" y="278" width="740" height="12" fill="{BLUE}"/>'
s+=f'<rect x="145" y="207" width="165" height="71" fill="{GOLD}"/><rect x="720" y="207" width="165" height="71" fill="{GOLD}"/>'
s+=text(227,249,'Source',27,BG,'middle')+text(802,249,'Drain',27,BG,'middle')
s+=text(515,242,'MoS₂ channel',27,BLUE,'middle')
s+=circle(515,397,60,BG,GOLD,7)
for i in range(12):
 a=i*math.tau/12;s+=circle(515+60*math.cos(a),397+60*math.sin(a),4,GOLD)
s+=line(455,478,575,478,GOLD,3)+line(455,468,455,488,GOLD,3)+line(575,468,575,488,GOLD,3)
s+=text(515,520,'1 nm',30,GOLD,'middle')
s+=line(576,397,886,397,GOLD,2)+text(913,392,'Nanotube',27,GOLD)+text(913,429,'gate',27,GOLD)
s+=text(181,358,'ZrO₂ insulator',25,MUTED)+text(181,582,'SiO₂ support',25,MUTED)
s+=text(64,686,'The nanotube’s diameter defines the physical gate length.',27)
s+=text(64,730,'Schematic only · contact spacing and layer thicknesses are not to scale.',23,MUTED)
s+=text(64,769,'Original diagram from Desai et al. / Berkeley Lab (2016) device description · CC0',20,MUTED)
save('one_nanometer_transistor_gate',s)

s=frame('Boötes Void','A vast region with unusually few galaxies')
# Illustrative glyphs explicitly NOT an observational catalog or measured boundary.
rng=random.Random(530)
for i in range(610):
 x=rng.uniform(72,1127);y=rng.uniform(175,638)
 r=math.hypot((x-600)/355,(y-402)/205)
 keep=.88 if r>1.18 else (.035 if r<.9 else .13+.75*(r-.9)/.28)
 if rng.random()>keep:continue
 radius=rng.uniform(1.4,3.0);s+=circle(round(x,1),round(y,1),round(radius,1),'#8ea7bf')
# No closed, hard boundary: a leader identifies the low-density region.
s+=text(600,374,'Boötes Void',38,INK,'middle')+text(600,418,'Low galaxy density',26,BLUE,'middle')
s+=text(600,700,'Conceptual sketch · dots are illustrative, not catalog positions',24,MUTED,'middle')
s+=text(600,738,'A void is underdense space, not a dark cloud blocking the view.',24,INK,'middle')
s+=text(64,779,'Original explanatory figure · subject basis: NASA Universe / Richard Powell · CC0',19,MUTED)
save('bootes_void',s)

s=frame('One light-year','The distance light travels through vacuum in one year')
s+=line(150,382,1050,382,'#1b344a',5)
# A stylized wave symbolizes traveling light; its wavelength is not dimensioned.
points=' '.join(f'{150+i*3},{382-32*math.sin(i*math.tau/22)}' for i in range(301))
s+=f'<polyline points="{points}" stroke="{BLUE}" stroke-width="4" fill="none"/>'
s+=circle(150,382,8,GOLD)+circle(1050,382,8,GOLD)
s+=text(150,302,'Start',30,INK,'middle')+text(1050,302,'One year later',30,INK,'middle')
s+=line(150,494,1050,494,GOLD,3)+line(150,480,150,508,GOLD,3)+line(1050,480,1050,508,GOLD,3)
s+=text(600,554,'1 light-year',44,GOLD,'middle')
s+=text(600,656,'A unit of distance',29,INK,'middle')
s+=text(600,701,'Explanatory diagram · the wave is symbolic',24,MUTED,'middle')
s+=text(64,764,'Original explanatory figure · definition: NASA Space Place · CC0',21,MUTED)
save('light_year',s)

records=[]
for stem,title,source,basis in [
('hubble_radius','Hubble radius — original Hubble-law explanatory diagram','https://map.gsfc.nasa.gov/universe/WMAP_Universe.pdf','Derives R = c/H₀ algebraically from v = H₀d. Dimensionless axes. The circle denotes a distance marker, not an opaque shell or visibility boundary.'),
('one_nanometer_transistor_gate','One-nanometer transistor gate — original device cross-section schematic','https://newscenter.lbl.gov/2016/10/06/smallest-transistor-1-nm-gate/','Original geometric schematic of the reported 2016 MoS₂ channel, carbon-nanotube gate, ZrO₂ insulator and SiO₂ support. Only 1 nm nanotube diameter is dimensioned. No source artwork or microscopy pixels copied.'),
('bootes_void','Boötes Void — original conceptual underdensity illustration','https://www.flickr.com/photos/nasablueshift/9402300439','Source caption describes an underdense region and foreground galaxies. The source map itself is BY-SA and was NOT copied. This is an original explanatory sketch with explicitly illustrative dots; no measured density field, member catalog, size or boundary is implied.'),
('light_year','One light-year — original explanatory distance diagram','https://spaceplace.nasa.gov/light-year/en/','NASA Space Place defines one light-year as the distance light travels in one Earth year. The wave is symbolic; no physical wavelength, cosmic expansion model or numerical conversion is claimed.')]:
 record={'file':'images/length_'+stem+'.jpg','source':source,'title':title,'author':'Universe Scales (original explanatory diagram)','license':'CC0','license_url':'https://creativecommons.org/publicdomain/zero/1.0/','changes':'New original SVG diagram from cited scientific facts; rasterized to 1200 × 800 JPEG and 300 px-wide thumbnail. '+basis}
 records.append(record)
 (HERE/'sources'/('length_'+stem+'.json')).write_text(json.dumps({'source':source,'license':'CC0','original_svg':'handoff/images2/diagrams/'+stem+'.svg','evidence':basis},ensure_ascii=False,indent=2)+'\n')
credits=ROOT/'images/credits/length.json';data=json.loads(credits.read_text());keys={x['file'] for x in records};data['images']=[x for x in data['images'] if x['file'] not in keys]+records;credits.write_text(json.dumps(data,indent=1)+'\n')
# CC0 public-domain dedication applies to this job's four original diagrams.
(OUT/'LICENSE.txt').write_text('To the extent possible under law, Universe Scales has waived all copyright and related or neighboring rights to the original diagrams in this directory under CC0 1.0 Universal.\nhttps://creativecommons.org/publicdomain/zero/1.0/\nScientific source images were not copied. Sources and representational limits are recorded in ../sources/.\n')
