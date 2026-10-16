#!/usr/bin/env python3
"""Recreate this job's explicitly curated JPEGs and credits; never runs a broad backfill.
Uses saved verified Commons metadata where available, requests at least 3 seconds
apart, and backs off on 429. Run from the repository root with its venv Python.
"""
import argparse,hashlib,html,io,json,re,time
from pathlib import Path
from urllib.parse import quote, urlsplit
import requests
from PIL import Image, ImageOps, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SESSION=requests.Session()
SESSION.headers['User-Agent']='UniverseScalesImageSourcing/1.0 (educational static-site project)'
last=0

def get(url,**kw):
 global last
 for attempt in range(6):
  time.sleep(max(0,3.1-(time.monotonic()-last)))
  last=time.monotonic()
  r=SESSION.get(url.split('?')[0] if 'upload.wikimedia.org' in url else url,timeout=60,**kw)
  if r.status_code!=429:
   r.raise_for_status();return r
  delay=max(float(r.headers.get('Retry-After','0')),15*2**attempt)
  print(f'HTTP 429; backing off {delay}s',flush=True);time.sleep(delay)
 raise RuntimeError('Repeated HTTP 429: '+url)

def plain(s):return html.unescape(re.sub('<[^>]+>','',s)).strip()
def slug(name):return re.sub(r'[-\s]+','_',re.sub(r'[^\w\s-]','',name,flags=re.ASCII)).lower()
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--external-only',action='store_true')
 args=parser.parse_args()
 selections=json.loads((HERE/'selections.json').read_text())
 evidence=HERE/'sources';evidence.mkdir(exist_ok=True)
 records=[]
 for spec in selections:
  if args.external_only and 'commons' in spec:continue
  name=spec['item'];stem='length_'+slug(name); saved=evidence/(stem+'.json')
  if 'commons' in spec:
   if saved.exists():p=json.loads(saved.read_text())
   else:
    data=get('https://commons.wikimedia.org/w/api.php',params={'action':'query','format':'json','titles':spec['commons'],'prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':1280}).json()
    p=next(iter(data['query']['pages'].values()));saved.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
   ii=dict(p['imageinfo'][0]);ii['url']=ii['url'].split('?')[0];meta=ii['extmetadata'];license=meta['LicenseShortName']['value']
   record={'file':'images/'+stem+'.jpg','source':ii['descriptionurl'],'title':p['title'],'author':plain(meta['Artist']['value']),'license':license,'license_url':meta.get('LicenseUrl',{}).get('value',''),'changes':spec.get('changes','Resized to at most 1200 px and converted to JPEG; 300 px-wide thumbnail.')}
   url=ii['thumburl'] if ii['url'].endswith('.svg') else ii['url']
  else:
   record={'file':'images/'+stem+'.jpg',**spec['credit']}
   url=spec['asset_url']
  assert re.fullmatch(r'CC BY [0-9.]+(?: [a-z]+)?|CC0|Public domain|Public Domain',record['license']),record['license']
  out=ROOT/record['file'];thumb=ROOT/'images/thumbs'/out.name
  cache=Path('/tmp/images2-originals');cache.mkdir(exist_ok=True)
  suffix='.pdf' if 'pdf_page' in spec else Path(urlsplit(url).path).suffix
  if not suffix or suffix=='.svg':suffix='.png'
  raw=cache/(stem+suffix)
  if not raw.exists():raw.write_bytes(get(url).content)
  if 'pdf_page' in spec:
   import pymupdf
   doc=pymupdf.open(raw)
   pix=doc[spec['pdf_page']].get_pixmap(matrix=pymupdf.Matrix(4,4),clip=pymupdf.Rect(*spec['pdf_crop']))
   im=Image.open(io.BytesIO(pix.tobytes('png')))
  else:im=ImageOps.exif_transpose(Image.open(raw))
  if 'crop' in spec:im=im.crop(spec['crop'])
  if im.mode in ('RGBA','LA') or 'transparency' in im.info:
   rgba=im.convert('RGBA');im=Image.new('RGB',im.size,'white');im.paste(rgba,mask=rgba.getchannel('A'))
  else:im=im.convert('RGB')
  im.thumbnail((1200,1100 if spec.get('caption') else 1200),Image.Resampling.LANCZOS)
  if spec.get('caption'):
   font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',max(14,round(im.width/36)))
   canvas=Image.new('RGB',(im.width,im.height+round(im.width/15)),(248,249,251));canvas.paste(im,(0,0))
   ImageDraw.Draw(canvas).text((im.width//2,im.height+round(im.width/30)),spec['caption'],font=font,fill=(28,36,49),anchor='mm');im=canvas
  im.save(out,quality=90,optimize=True)
  im.resize((300,round(im.height*300/im.width)),Image.Resampling.LANCZOS).save(thumb,quality=86,optimize=True)
  records.append(record)
  if 'commons' not in spec:
   saved.write_text(json.dumps({'source':spec['credit']['source'],'asset_url':url,'sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'license':record['license'],'license_url':record['license_url'],'evidence':spec['evidence']},ensure_ascii=False,indent=2)+'\n')
  print(name,record['license'],im.size,flush=True)
 credits=ROOT/'images/credits/length.json';existing=json.loads(credits.read_text());byfile={r['file']:r for r in records}
 existing['images']=[r for r in existing['images'] if r['file'] not in byfile]+records
 credits.write_text(json.dumps(existing,ensure_ascii=True,indent=1)+'\n')
 requested={'images/length_'+slug(n)+'.jpg' for n in json.loads((HERE/'requested.json').read_text())}
 (HERE/'credits-added.json').write_text(json.dumps([r for r in existing['images'] if r['file'] in requested],ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
