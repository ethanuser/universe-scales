#!/usr/bin/env python3
"""Scoped, pinned photo/illustration import; no API search or broad image backfill.

Uses downloaded originals in /tmp/images4-originals, fetching pinned URLs if absent.
Source identity/license evidence is recorded with source hashes in sources/imports.json.
Run with ./venv/bin/python. Does not change credits; review_images.py integrates them.
"""
import hashlib
import json
import time
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CACHE = Path('/tmp/images4-originals')
CCBY = 'https://creativecommons.org/licenses/by/4.0/'
CC0 = 'https://creativecommons.org/publicdomain/zero/1.0/'
NASA = 'https://www.nasa.gov/nasa-brand-center/images-and-media/'
SPECS = [
    dict(item='Lolong the Crocodile', original='lolong.jpg',
         url='https://thumb.wikimedia.org/wikipedia/commons/thumb/e/ef/9542National_Museum_of_Natural_History_17.jpg/960px-9542National_Museum_of_Natural_History_17.jpg',
         source='https://commons.wikimedia.org/wiki/File:9542National_Museum_of_Natural_History_17.jpg',
         title='Lolong skeleton at the National Museum of Natural History, Manila', author='Judgefloro', license='CC0', license_url=CC0,
         caption='Lolong’s skeleton · National Museum of Natural History, Manila',
         evidence='Creator’s source page identifies the Lolong museum exhibit, including replica and skeleton, and explicitly dedicates the photograph under CC0. The selected frame visibly shows the suspended crocodile skeleton; the caption explicitly identifies a skeleton display rather than the living animal. No claim that photographic perspective measures his full 6.17 m body length.'),
    dict(item='Titanosaur Cast', original='AMNHTitanosaur.jpg',
         url='https://thumb.wikimedia.org/wikipedia/commons/thumb/2/28/AMNHTitanosaur.jpg/3840px-AMNHTitanosaur.jpg',
         source='https://commons.wikimedia.org/wiki/File:AMNHTitanosaur.jpg',
         title='AMNH titanosaur skeletal cast', author='D. Benjamin Miller', license='CC0', license_url=CC0,
         crop=[0, 0, 3000, 836], gamma=.78,
         caption='Patagotitan skeletal cast · American Museum of Natural History',
         evidence='Commons identifies this as the titanosaur skeleton cast at AMNH, photographed 18 January 2016, and the creator dedicates it under CC0. Used the original creator’s image, not the BY-SA derivative AMNHTitanosaur-03.jpg. Crop retains the visible head-to-tail cast and removes the separate fossil display on the right.'),
    dict(item='Grain of Sand', original='Observation_microscopique_de_grains_de_sable.jpg',
         url='https://thumb.wikimedia.org/wikipedia/commons/thumb/9/99/Observation_microscopique_de_grains_de_sable.jpg/1280px-Observation_microscopique_de_grains_de_sable.jpg',
         source='https://commons.wikimedia.org/wiki/File:Observation_microscopique_de_grains_de_sable.jpg',
         title='Individual sand grains through a microscope', author='Thelasthedgehog', license='CC BY 4.0', license_url=CCBY,
         crop=[130, 430, 830, 1230], caption='Individual sand grains · microscope view',
         evidence='Source identifies microscopic observation of smooth sand and licenses the photograph CC BY 4.0. Crop isolates the resolved grains and excludes the dark eyepiece surroundings. No scale bar is invented; the pictured grains are not claimed to be exactly the representative 1 mm catalog size.'),
    dict(item='El Reno Tornado', original='May_31_2013_El_Reno,_OK_EF3.png',
         url='https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c3/May_31_2013_El_Reno%2C_OK_EF3.png/960px-May_31_2013_El_Reno%2C_OK_EF3.png',
         source='https://commons.wikimedia.org/wiki/File:May_31_2013_El_Reno,_OK_EF3.png',
         title='El Reno tornado in its multiple-vortex stage, 31 May 2013', author='Richard Thompson / NOAA Storm Prediction Center',
         license='Public domain', license_url='https://www.weather.gov/disclaimer',
         evidence='Commons describes the El Reno 31 May 2013 tornado in its multiple-vortex stage, credits Richard Thompson at SPC, and marks it PD-USGov. The image itself carries the event/date/SPC attribution. It shows the tornado, not the parent storm from orbit; visible funnels are not asserted to outline the maximum damage width.'),
    dict(item='Chloroplast', original='201710_chloroplast.png',
         url='https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0f/201710_chloroplast.svg/960px-201710_chloroplast.svg.png',
         source='https://commons.wikimedia.org/wiki/File:201710_chloroplast.svg',
         title='Chloroplast cutaway illustration', author='DataBase Center for Life Science (DBCLS)', license='CC BY 4.0', license_url=CCBY,
         caption='Chloroplast · cutaway illustration',
         evidence='Commons identifies an isolated chloroplast illustration by DBCLS, originally doi:10.7875/togopic.2017.50, under CC BY 4.0 with a completed license review. This is a teaching cutaway showing thylakoid stacks, not a micrograph or measured architecture.'),
    dict(item='Hunga Tonga Eruption Plume', original='Tonga.gif', frame=80,
         url='https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c6/Tonga_Volcano_Eruption_2022-01-15_0320Z_to_0610Z_Himawari-8_visible.gif/500px-Tonga_Volcano_Eruption_2022-01-15_0320Z_to_0610Z_Himawari-8_visible.gif',
         source='https://commons.wikimedia.org/wiki/File:Tonga_Volcano_Eruption_2022-01-15_0320Z_to_0610Z_Himawari-8_visible.gif',
         title='Hunga Tonga eruption plume, Himawari-8, 15 January 2022 05:20 UTC',
         author='Japan Meteorological Agency (Himawari-8); Digital Typhoon / NII', license='CC BY 4.0', license_url=CCBY,
         caption='Hunga Tonga plume · 15 January 2022 · 05:20 UTC',
         evidence='Source is the JMA / Digital Typhoon animation with explicit CC BY 4.0 terms, also linked to the compatible Japanese government data terms. Zero-based frame 80 visibly reads 2022-01-15 05:20:00 UTC and shows a large textured umbrella plume. Frame was fully decoded/composited by Pillow before export. Top-down view does not directly measure the plume’s height.'),
    dict(item='TRAPPIST-1 System', original='trappist.jpg',
         url='https://assets.science.nasa.gov/content/dam/science/missions/webb/outreach/migrated/2026/STScI-01KE7FAESZABCMJCQ5G56GYH2V.jpg',
         source='https://science.nasa.gov/asset/webb/trappist-1-system-orbit-comparison/',
         title='TRAPPIST-1 system versus the Solar System — orbit comparison',
         author='NASA, ESA, CSA, Joseph Olmsted (STScI)', license='Public domain', license_url=NASA,
         evidence='NASA’s asset caption explicitly identifies all seven planet orbits b–h and compares their compact orbital span with the inner Solar System. This is the 2026 orbital comparison diagram, not a travel poster or a literal photograph of exoplanets. NASA image-use guidance applies (the Hubble/Webb copyright pages redirect there); the asset has no third-party copyright notice.'),
    dict(item='Andromeda Gas Halo', original='halo.png',
         url='https://assets.science.nasa.gov/content/dam/science/missions/hubble/releases/2020/08/STScI-01EVST4Q90FFF55TNZPRJWTTR5.tif/jcr:content/renditions/2000x1600.png',
         source='https://science.nasa.gov/asset/hubble/halo-around-the-andromeda-galaxy-illustration/',
         title='Andromeda gaseous halo and 43 background-quasar sightlines — illustration',
         author='NASA, ESA, and E. Wheatley (STScI)', license='Public domain', license_url=NASA,
         caption='Andromeda gas halo · illustration with quasar sightlines',
         evidence='NASA identifies this as a gas-halo illustration with the 43 background quasars used to probe absorption, not an optical image of visible halo gas. The source title says Illustration; the new caption preserves that distinction. NASA image-use guidance applies (Hubble copyright page redirects there); no third-party copyright notice appears on the asset.'),
]


def slug(name):
    import re
    return re.sub(r'[-\s]+', '_', re.sub(r'[^\w\s-]', '', name, flags=re.ASCII)).lower()


def export(im, file, caption=None):
    im.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
    if caption:
        band = max(54, round(im.width*.065))
        canvas = Image.new('RGB', (im.width, im.height+band), '#081321')
        canvas.paste(im, (0, 0))
        font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', max(14, round(im.width*.023)))
        # Keep the whole caption inside the image even for narrow square sources.
        while ImageDraw.Draw(canvas).textlength(caption, font=font) > im.width-24:
            font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', font.size-1)
        ImageDraw.Draw(canvas).text((im.width/2, im.height+band/2), caption, fill='#edf4fc', font=font, anchor='mm')
        im=canvas
    im.save(ROOT/'images'/file, 'JPEG', quality=92, optimize=True)
    thumb=im.resize((300, round(im.height*300/im.width)), Image.Resampling.LANCZOS)
    thumb.save(ROOT/'images/thumbs'/file,'JPEG',quality=88,optimize=True)


def main():
    CACHE.mkdir(exist_ok=True)
    records=[];evidence=[]
    for spec in SPECS:
        p=CACHE/spec['original']
        if not p.exists():
            r=requests.get(spec['url'],headers={'User-Agent':'UniverseScalesImageSourcing/1.0'},timeout=60)
            r.raise_for_status();p.write_bytes(r.content)
            time.sleep(3.2)
        im=Image.open(p)
        if 'frame' in spec:im.seek(spec['frame'])
        im=ImageOps.exif_transpose(im)
        if 'A' in im.getbands() or 'transparency' in im.info:
            rgba=im.convert('RGBA');im=Image.new('RGB',rgba.size,'#081321');im.paste(rgba,mask=rgba.getchannel('A'))
        else:im=im.convert('RGB')
        if 'crop' in spec:im=im.crop(spec['crop'])
        if 'gamma' in spec:im=im.point([round(255*(i/255)**spec['gamma']) for i in range(256)]*3)
        file='length_'+slug(spec['item'])+'.jpg'
        export(im,file,spec.get('caption'))
        changes=[]
        if 'frame' in spec:changes.append(f"Selected animation frame {spec['frame']} (zero-based)")
        if 'crop' in spec:changes.append(f"Cropped downloaded source to {spec['crop']}")
        if 'gamma' in spec:changes.append(f"Lifted shadows using gamma {spec['gamma']}")
        if 'caption' in spec:changes.append('Added subject/representation caption')
        changes.append('Converted to JPEG at at most 1200 px image width; matching 300 px-wide thumbnail')
        record={k:spec[k] for k in ['source','title','author','license','license_url']}
        record.update(file='images/'+file,changes='; '.join(changes)+'. '+spec['evidence'])
        records.append(record)
        evidence.append({**spec,'accessed':'2026-10-16','downloaded_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'downloaded_bytes':p.stat().st_size})
        print(spec['item'],im.size,flush=True)
    (HERE/'import-credits.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    (HERE/'sources/imports.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
