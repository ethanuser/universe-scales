#!/usr/bin/env python3
"""Audit only this handoff's assets and make a contact sheet in requested order."""
import json,re,hashlib,textwrap
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
names=json.loads((HERE/'requested.json').read_text())
def slug(s):return re.sub(r'[-\s]+','_',re.sub(r'[^\w\s-]','',s,flags=re.ASCII)).lower()
credits=json.loads((ROOT/'images/credits/length.json').read_text())['images'];byfile={r['file']:r for r in credits}
font_path='/System/Library/Fonts/Supplemental/Arial.ttf';font=ImageFont.truetype(font_path,19);small=ImageFont.truetype(font_path,15)
w,h=320,290;sheet=Image.new('RGB',(5*w,5*h+70),(14,22,34));d=ImageDraw.Draw(sheet)
d.text((18,14),'Length image review — photos, scientific figures and explicitly labeled diagrams',font=ImageFont.truetype(font_path,25),fill='white')
report=[];added=[]
for i,name in enumerate(names):
 x=i%5*w;y=i//5*h+60;f='images/length_'+slug(name)+'.jpg';p=ROOT/f;thumbnail=ROOT/'images/thumbs'/p.name
 if p.exists() and f in byfile:
  im=Image.open(p);im.load();assert im.format=='JPEG' and max(im.size)<=1200,(name,im.size)
  thumb=Image.open(thumbnail);thumb.load();assert thumb.format=='JPEG' and thumb.width==300,(name,thumb.size)
  credit=byfile[f];assert set(credit)=={'file','source','title','author','license','license_url','changes'}
  assert credit['license'] in {'Public domain','Public Domain','CC0'} or re.fullmatch(r'CC BY [0-9.]+(?: [a-z]+)?',credit['license'])
  im.thumbnail((w-20,210),Image.Resampling.LANCZOS);sheet.paste(im,(x+(w-im.width)//2,y+(210-im.height)//2))
  d.text((x+10,y+255),credit['license'],font=small,fill=(140,210,185))
  r={'item':name,'file':f,'size':list(Image.open(p).size),'thumbnail':list(thumb.size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'license':credit['license']};added.append(credit)
 else:
  d.rectangle((x+10,y+10,x+w-10,y+210),outline=(206,97,87),width=2)
  d.text((x+w//2,y+100),'NO APPROVED SOURCE',font=font,fill=(245,145,130),anchor='mm')
  r={'item':name,'file':f,'status':'missing approved source'}
 for j,label in enumerate(textwrap.wrap(name,width=30)):d.text((x+10,y+217+j*20),label,font=font,fill='white')
 report.append(r)
sheet.save(HERE/'contact-sheet.jpg',quality=93,optimize=True)
(HERE/'asset-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(HERE/'credits-added.json').write_text(json.dumps(added,ensure_ascii=False,indent=2)+'\n')
print(f'{len(added)}/{len(names)} images have credits, valid JPEG dimensions and 300 px-wide thumbnails.')
print('Missing:',', '.join(r['item'] for r in report if 'status' in r))
print('Total JPEG bytes:',sum(r.get('bytes',0) for r in report))
