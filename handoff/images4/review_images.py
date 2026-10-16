#!/usr/bin/env python3
"""Integrate only these 25 image credits, audit assets, and make review sheets.

Default is read-only for images/credits; use --integrate after generating assets.
The integration preserves other jobs' credit records and removes superseded ones.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageChops, ImageStat

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'handoff/images3'))
from review_images import sheet, resolve, slug  # noqa: E402


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--integrate',action='store_true')
    args=parser.parse_args()
    names=json.loads((HERE/'requested.json').read_text())
    records=[]
    for f in ['diagram-credits.json','import-credits.json','ribosome-credits.json']:
        records+=json.loads((HERE/f).read_text())
    targets={'images/length_'+slug(n)+'.jpg' for n in names}
    stems={Path(f).stem for f in targets}
    assert len(targets)==len(records)==25
    assert {r['file'] for r in records}==targets
    path=ROOT/'images/credits/length.json'
    data=json.loads(path.read_text())
    baseline=json.loads(subprocess.check_output(['git','show','HEAD:images/credits/length.json'],cwd=ROOT))
    old=[r for r in baseline['images'] if Path(r['file']).stem in stems]
    if args.integrate:
        data['images']=[r for r in data['images'] if Path(r['file']).stem not in stems]+records
        path.write_text(json.dumps(data,ensure_ascii=True,indent=1)+'\n')
        # The old alternate PNG depicts an unverified galaxy clump. Keeping it
        # beside the new JPEG would retain contradictory artwork for this item.
        (ROOT/'images/length_hercules_corona_borealis_great_wall.png').unlink(missing_ok=True)
    assert len({r['file'] for r in data['images']})==len(data['images'])
    assert [r for r in data['images'] if Path(r['file']).stem not in stems]==[r for r in baseline['images'] if Path(r['file']).stem not in stems]
    byfile={r['file']:r for r in data['images']}
    audit=[]
    for name in names:
        p=resolve(name);assert p is not None,name
        file=str(p.relative_to(ROOT));assert file in targets
        t=ROOT/'images/thumbs'/p.name
        with Image.open(p) as im, Image.open(t) as thumb:
            assert im.format==thumb.format=='JPEG'
            assert im.mode==thumb.mode=='RGB'
            assert im.width<=1200 and thumb.width==300
            assert thumb.height==round(im.height*300/im.width)
            expected=im.resize(thumb.size,Image.Resampling.LANCZOS)
            difference=sum(ImageStat.Stat(ImageChops.difference(expected,thumb)).mean)/3
            assert difference<5,(name,difference)
            record=byfile[file]
            assert record==next(r for r in records if r['file']==file)
            assert record['license'] in ['CC0','CC BY 4.0','Public domain']
            assert all(record[k] for k in ['author','source','license_url','changes'])
            audit.append(dict(item=name,file=file,dimensions=list(im.size),bytes=p.stat().st_size,
                              sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                              thumbnail=str(t.relative_to(ROOT)),thumbnail_dimensions=list(thumb.size),
                              thumbnail_sha256=hashlib.sha256(t.read_bytes()).hexdigest(),
                              thumbnail_mean_pixel_difference=round(difference,3),license=record['license']))
    sheet(names,HERE/'contact-sheet.jpg',4,390,330,'images4 · 16 replacements + 9 missing image slots')
    for i in range(0,len(names),8):
        sheet(names[i:i+8],HERE/f'contact-{i//8+1:02}.jpg',2,600,470,f'images4 · {i+1}–{min(i+8,len(names))} / 25')
    for f,value in [('asset-audit.json',audit),('credits-upsert.json',records),('credits-removed.json',old)]:
        (HERE/f).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    items=yaml.safe_load((ROOT/'dataset/raw/legacy_yaml/length.yaml').read_text())['items']
    missing=[i['name'] for i in items if resolve(i['name']) is None]
    (HERE/'coverage.json').write_text(json.dumps(dict(total=len(items),populated=len(items)-len(missing),missing=missing,
        requested=len(names),credit_records=len(data['images']),superseded_credit_records=len(old)),indent=2)+'\n')
    print(f'25/25 requested assets and thumbnails pass. {len(old)} obsolete credits replaced; {len(data["images"])} total credits.')
    print(f'{len(items)-len(missing)}/{len(items)} Length slots populated; missing: {missing}')


if __name__=='__main__':main()
