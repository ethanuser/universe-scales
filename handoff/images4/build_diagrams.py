#!/usr/bin/env python3
"""Original CC0 SVG diagrams. Render with Pillow + CairoSVG; no downloaded art.

DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib /tmp/images3-tools/bin/python handoff/images4/build_diagrams.py
Scientific references and explicit representation limits are retained in facts.json.
"""
import html
import io
import json
import math
import re
from pathlib import Path

import cairosvg
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'diagrams'
BG, INK, MUTED = '#081321', '#edf4fc', '#a5b8cd'
BLUE, GOLD, GREEN = '#83d8f2', '#ffd398', '#8ed4ae'
RECORDS, FACTS = [], []


def slug(name):
    return re.sub(r'[-\s]+', '_', re.sub(r'[^\w\s-]', '', name, flags=re.ASCII)).lower()


def text(x, y, s, size=28, color=INK, anchor='start', bold=False):
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'text-anchor="{anchor}" font-weight="{"bold" if bold else "normal"}" '
            f'font-family="Arial,Helvetica,sans-serif">{html.escape(s)}</text>')


def line(x1, y1, x2, y2, color=BLUE, width=2, dash=''):
    return f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}"/>'


def circle(x, y, r, fill='none', stroke='none', width=2, opacity=1):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"/>'


def path(d, color=BLUE, width=3, fill='none', opacity=1):
    return f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="{fill}" opacity="{opacity}" stroke-linecap="round" stroke-linejoin="round"/>'


def rect(x, y, w, h, fill, rx=0, stroke='none'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'


def frame(title, subtitle, size=46):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">'
            + rect(0, 0, 1200, 800, BG) + line(56, 39, 100, 39, GOLD, 4)
            + text(56, 101, title, size, bold=True) + text(56, 148, subtitle, 25, MUTED))


def bracket(x1, x2, y, label, size=40):
    return (line(x1, y, x2, y, GOLD, 3) + line(x1, y-12, x1, y+12, GOLD, 3)
            + line(x2, y-12, x2, y+12, GOLD, 3) + text((x1+x2)/2, y+57, label, size, GOLD, 'middle'))


def save(name, s, source, basis, evidence, extra_sources=None):
    s += line(56, 741, 1144, 741, '#24364a', 1)
    s += text(56, 780, 'Original explanatory diagram · CC0', 20, MUTED)
    s += text(1144, 780, basis, 19, MUTED, 'end') + '</svg>\n'
    OUT.mkdir(exist_ok=True)
    stem = slug(name)
    p = OUT / (stem + '.svg')
    p.write_text(s)
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=s.encode(), output_width=2400, output_height=1600))).convert('RGB')
    im = im.resize((1200, 800), Image.Resampling.LANCZOS)
    file = 'length_' + stem + '.jpg'
    im.save(ROOT/'images'/file, quality=93, optimize=True)
    im.resize((300, 200), Image.Resampling.LANCZOS).save(ROOT/'images/thumbs'/file, quality=90, optimize=True)
    RECORDS.append(dict(file='images/'+file, source=source, title=name+' — original explanatory diagram',
                        author='Universe Scales (original artwork)', license='CC0',
                        license_url='https://creativecommons.org/publicdomain/zero/1.0/',
                        changes='New original SVG; 1200 × 800 JPEG and 300 × 200 thumbnail. '+evidence))
    FACTS.append(dict(item=name, source=source, extra_sources=extra_sources or [], accessed='2026-10-16',
                      original_svg=str(p.relative_to(ROOT)), evidence=evidence))


def main():
    s = frame('String length', 'A hypothetical scale in string theory')
    s += '<defs><linearGradient id="string"><stop stop-color="#83d8f2"/><stop offset="1" stop-color="#eabaff"/></linearGradient></defs>'
    s += path('M140 397 C230 190 350 600 450 397 S650 190 735 397', '#244559', 24)
    s += path('M140 397 C230 190 350 600 450 397 S650 190 735 397', 'url(#string)', 7)
    s += circle(140, 397, 8, BLUE) + circle(735, 397, 8, '#eabaff')
    s += text(420, 578, 'Open string', 34, BLUE, 'middle')
    s += path('M900 315 C1020 260 1140 400 1030 465 C925 520 825 385 900 315 Z', '#bda4ee', 7)
    s += text(970, 578, 'Closed string', 34, '#d1b7f4', 'middle')
    s += text(600, 654, 'Quantum strings are theoretical objects, not strands of material.', 28, INK, 'middle')
    s += text(600, 704, 'Shapes and thickness are illustrative; no string has been directly observed.', 23, MUTED, 'middle')
    save('String Length', s, 'https://home.cern/science/physics/extra-dimensions-gravitons-and-tiny-black-holes', 'CERN · string theory',
         'Conceptual open and closed strings, not a photograph, measured geometry, physical cord, or fixed universal string-length prediction. No numerical string/Planck equivalence is asserted.')

    s = frame('Carbon atom', 'Neutral carbon · a quantum electron cloud')
    s += '<defs><radialGradient id="cloud"><stop stop-color="#badff0" stop-opacity="0.8"/><stop offset="0.4" stop-color="#76badc" stop-opacity="0.4"/><stop offset="1" stop-color="#76badc" stop-opacity="0"/></radialGradient></defs>'
    s += circle(360, 402, 238, 'url(#cloud)')
    for angle in [0, 90]:
        s += f'<g transform="translate(360 402) rotate({angle})"><ellipse cx="82" rx="130" ry="65" fill="url(#cloud)"/><ellipse cx="-82" rx="130" ry="65" fill="url(#cloud)"/></g>'
    s += circle(360, 402, 170, 'none', '#7995af', 1.5)
    s += circle(360, 402, 7, GOLD) + line(190, 402, 190, 606, MUTED, 1, '5 7') + line(530, 402, 530, 606, MUTED, 1, '5 7')
    s += bracket(190, 530, 603, '140 pm')
    s += text(700, 290, '1s²  2s²  2p²', 53, BLUE, bold=True)
    s += text(700, 351, 'Six electrons', 31)
    s += text(700, 416, 'Empirical size convention', 29, GOLD)
    s += text(700, 461, '2 × 70 pm atomic radius', 27, MUTED)
    s += text(700, 522, 'The cloud has no hard edge.', 27)
    s += text(600, 705, 'Schematic orbital shapes and enlarged nucleus · not a measured probability-density map.', 22, MUTED, 'middle')
    save('Carbon Atom', s, 'https://www.webelements.com/carbon/atom_sizes.html', 'WebElements · carbon radii',
         '140 pm is twice the tabulated 70 pm empirical atomic radius. Cloud/lobes are qualitative, not an ab initio density, enclosed-probability contour or literal surface. Nucleus enlarged.',
         ['https://www.webelements.com/carbon/atoms.html'])

    s = frame('Hyperion', 'Coast redwood · Sequoia sempervirens · California')
    s += line(140, 665, 700, 665, '#40605d', 2)
    s += path('M354 665 Q376 505 380 204 L386 204 Q390 505 410 665 Z', '#9c6950', 1, '#80553e')
    for y in range(250, 610, 23):
        half = 18+(y-240)*.14
        s += path(f'M383 {y-40} Q{383-half*.4} {y-6} {383-half} {y+20} Q383 {y+5} {383+half*.8} {y+23} Q396 {y-15} 383 {y-40}', '#367f67', 1, '#245d4d')
    s += line(605, 204, 605, 665, GOLD, 3)+line(592,204,618,204,GOLD,3)+line(592,665,618,665,GOLD,3)
    s += text(744, 329, '≈ 116 m', 65, GOLD, bold=True)
    s += text(748, 392, 'A single living tree', 33)
    s += text(748, 451, 'Height above its base', 28, MUTED)
    s += text(748, 519, 'Schematic coast redwood', 27, GREEN)
    s += text(600, 710, 'Height diagram · crown and branch arrangement do not reconstruct the named tree.', 23, MUTED, 'middle')
    save('Hyperion', s, 'https://www.guinnessworldrecords.com/world-records/tallest-tree-living', 'Guinness · 2019 measurement',
         'Guinness reports Hyperion at 116.07 m in 2019, rounded here to approximately 116 m. Original generic coast-redwood silhouette, not a verified photograph or reconstruction of its crown. Does not corroborate the dataset’s unsourced 116.2 m / 2026 claim.')

    s = frame('Longest lightning flash', '22 October 2017 · United States · satellite-detected megaflash')
    for x,w in [(135,205),(300,260),(510,285),(760,230)]:
        s += f'<ellipse cx="{x+80}" cy="340" rx="{w}" ry="90" fill="#173349" opacity="0.6"/>'
    d='M150 408 L224 388 L258 409 L330 356 L389 379 L445 343 L502 369 L571 340 L636 365 L694 329 L744 352 L817 318 L871 343 L945 312 L1050 332'
    s += path(d, '#28516a', 20) + path(d, BLUE, 6) + path(d, INK, 2)
    s += path('M330 356 L346 314 L387 294 M636 365 L622 415 L661 444 M817 318 L826 278 L875 256', BLUE, 3)
    s += bracket(150, 1050, 526, '829 ± 8 km', 66)
    s += text(600, 646, 'Maximum great-circle separation across one flash', 28, INK, 'middle')
    s += text(600, 705, 'Conceptual discharge paths · not the event’s mapped channels or an ordinary ground strike.', 22, MUTED, 'middle')
    save('Longest Lightning Flash', s, 'https://wmo.int/news/media-centre/wmo-certifies-megaflash-lightning-record-usa', 'WMO · certified 31 July 2025',
         'WMO reports 829 ± 8 km for the 22 October 2017 US megaflash, measured by maximum great-circle separation. Authored channels/clouds are conceptual, not satellite data or traced channel geometry.')

    s = frame('Kuiper Belt', 'Our Solar System · a broad population of icy bodies beyond Neptune')
    cx,cy,scale=360,416,4.2
    s += circle(cx,cy,50*scale,'#19465a') + circle(cx,cy,30*scale,BG)
    for radius in [30,50]:s += circle(cx,cy,radius*scale,'none',BLUE,1.5)
    s += circle(cx,cy,5,GOLD) + text(cx,cy+37,'Sun',24,GOLD,'middle')
    s += line(cx,cy,cx+50*scale,cy,GOLD,2)
    s += text(cx+40*scale,cy-20,'30–50 AU',25,GOLD,'middle')
    s += circle(cx,cy,30.1*scale,'none','#8daac5',1)
    s += text(700,306,'≈ 100 AU across',49,GOLD,bold=True)
    s += text(700,370,'Main belt: about 30–50 AU',27)
    s += text(700,437,'Neptune orbits near',27,MUTED)
    s += text(700,476,'the belt’s inner region.',27,MUTED)
    s += text(700,546,'Face-on distance diagram',27,BLUE)
    s += bracket(cx-210,cx+210,658,'')
    s += text(600,709,'Shaded band indicates a region, not measured object locations or a continuous solid ring.',22,MUTED,'middle')
    save('Kuiper Belt',s,'https://science.nasa.gov/solar-system/kuiper-belt/facts/','NASA · Kuiper Belt facts',
         'NASA places the main belt at approximately 30–50 AU, hence approximately 100 AU outer diameter. Original face-on annulus is a regional schematic, with no synthetic catalog points. Band edges are approximate and do not delimit all trans-Neptunian objects.')

    s = frame('Hercules–Corona Borealis Great Wall','A proposed structure inferred from gamma-ray bursts',40)
    s += text(600,265,'14 of 31 bursts',58,GOLD,'middle',True)
    s += text(600,316,'in roughly one eighth of the sky · original study',28,MUTED,'middle')
    # A count diagram, explicitly not invented sky coordinates.
    for i in range(31):
        x=128+(i%16)*62; y=400+(i//16)*64
        s+=circle(x,y,13,GOLD if i<14 else '#3b526a')
    s+=bracket(136,1064,548,'Proposed span: 2,000–3,000 Mpc',39)
    s+=text(600,657,'A disputed inference, not a photographed galaxy wall',29,INK,'middle')
    s+=text(600,707,'Count symbols summarize the 2014 sample; their layout is not a sky map.',23,MUTED,'middle')
    save('Hercules-Corona Borealis Great Wall',s,'https://arxiv.org/abs/1401.0533','Horváth, Hakkila & Bagoly (2014)',
         'The paper reports 14 of 31 GRBs at 1.6 < z < 2.1 in roughly 1/8 of the sky and infers a 2000–3000 Mpc span. A simple count strip conveys those published counts, not measured angular positions, structure membership or a mapped boundary. The proposed wall is explicitly disputed; no galaxy-wall artwork is copied.')

    s=frame('DVD track pitch','Center-to-center separation of adjacent turns of the spiral')
    for y in [255,345,435,525]:
        s+=rect(125,y-17,950,34,'#17435c',17)
        for x,w in [(170,95),(340,150),(590,90),(810,160)]:s+=rect(x,y-10,w,20,BLUE,10)
        s+=line(125,y,1075,y,'#bacfdd',1,'6 9')
    s+=line(692,345,692,435,GOLD,4)+line(680,345,704,345,GOLD,3)+line(680,435,704,435,GOLD,3)
    s+=text(600,633,'740 nm = 0.74 µm',57,GOLD,'middle',True)
    s+=text(600,704,'Original magnified schematic · pitch is track spacing, not pit width or pit length.',24,MUTED,'middle')
    save('DVD Track Pitch',s,'https://ecma-international.org/wp-content/uploads/ECMA-267_2nd_edition_december_1999.pdf','ECMA-267 · track geometry',
         'ECMA-267 specifies a 0.74 µm nominal track pitch (±0.03 µm). Parallel strips are a locally straightened view of adjacent spiral turns; drawn mark widths, lengths and sequence are illustrative, not a micrograph or encoded data.')

    s=frame('Prelude FLNG','Floating gas-liquefaction facility · dimensioned schematic')
    s+=path('M110 342 L1035 342 Q1095 342 1095 403 L1061 491.36 L142 491.36 Q110 471 110 432 Z','#99c7dc',2,'#244a65')
    s+=rect(185,358,785,117,'#396679',6)
    # Generic processing-module symbols, with no asserted as-built arrangement.
    for x in [260,390,520,650,780]:
        s+=rect(x,372,75,46,'#8da7a9',3)+line(x,395,x+75,395,'#d5e5e7',2)
        s+=circle(x+23,394,10,'#597c87')+circle(x+53,394,10,'#597c87')
    s+=rect(170,366,48,64,'#d3d9d9',3)
    s+=line(125,505,1080,505,'#30506a',2)
    s+=bracket(110,1095,541,'488 m',61)
    s+=text(600,656,'Hull width: 74 m',31,BLUE,'middle')
    s+=text(600,707,'Plan-view size diagram · outline and deck symbols are illustrative, not engineering plans.',22,MUTED,'middle')
    save('Prelude FLNG',s,'https://www.shell.com/news-and-insights/newsroom/news-and-media-releases/_jcr_content/root/main/section/simple_1285915735/call_to_action_11159_578483303/links/item0.stream/1669043581418/ef8aa6eff3694727cb88fdbd0d68fa3bb60d3586/2014-media-releases.pdf','Shell · Prelude project dimensions',
         'Shell states 488 m length and 74 m width. The bounding hull proportions follow those dimensions; hull contours and generic equipment symbols are original illustrative design, not a traced Shell rendering, photograph or as-built deck layout. No qualifying facility photo was established in the prior images3 search.')

    s=frame('Danyang–Kunshan Grand Bridge','China · high-speed railway viaduct')
    s+=rect(90,352,1020,22,'#9fc4d3',3)
    s+=line(90,343,1110,343,BLUE,3)
    for x in range(120,1100,77):s+=rect(x,374,13,120,'#4f7389',2)
    s+=line(90,497,1110,497,'#2e5d59',3)
    for x in range(165,1050,165):s+=path(f'M{x} 505 q40 20 80 0','#305f62',2)
    s+=rect(422,307,350,30,'#e7eff2',13)+rect(438,314,320,9,'#527d99',3)
    s+=bracket(100,1100,558,'≈ 164 km',60)
    s+=text(600,669,'One continuous total-length ruler',30,INK,'middle')
    s+=text(600,710,'Illustrative viaduct segment · pier count, spacing and scenery do not depict the full bridge.',22,MUTED,'middle')
    save('Danyang-Kunshan Grand Bridge',s,'https://www.guinnessworldrecords.com/world-records/longest-bridge','Guinness World Records',
         'The opened Guinness record page gives the bridge length rounded to 164 km; this image uses that coarse figure rather than claiming the page states 164.8 km. The ruler represents total length, while the generic viaduct segment and train are illustrative, not a route map, engineering elevation or claim that the pictured segment spans 164 km. Prior images3 photo candidates were BY-SA or all rights reserved.')

    s=frame('Credit card','Unbranded generic ID-1 card · standard physical dimensions')
    # Exactly 85.60:53.98 rectangular proportions, ignoring corner radius tolerances.
    w=690;h=w*53.98/85.60;x=255;y=198
    s+=rect(x+9,y+12,w,h,'#040b14',25)
    s+=rect(x,y,w,h,'#244f70',25,'#86b7cf')
    s+=rect(x+55,y+103,100,76,'#d2bd82',13)
    for xx in [x+89,x+121]:s+=line(xx,y+106,xx,y+176,'#867856',2)
    s+=line(x+56,y+141,x+154,y+141,'#867856',2)
    # No name, brand, account number, signature or payment-network mark.
    s+=bracket(x,x+w,668,'85.60 mm',34)
    s+=line(980,y,980,y+h,BLUE,2)+line(971,y,989,y,BLUE,2)+line(971,y+h,989,y+h,BLUE,2)
    s+=text(1014,435,'53.98 mm',27,BLUE,'middle')
    s+=text(600,600,'GENERIC CARD',34,BLUE,'middle')
    save('Credit Card',s,'https://www.cardprinting.com/faq','ISO/IEC 7810 · ID-1 format',
         'ID-1 length 85.60 mm and width 53.98 mm. Original unbranded card with generic chip motif; no actual account, personal data, company logo or copied card design. Corner shape and chip geometry are illustrative.',
         ['https://www.iso.org/standard/70483.html'])

    s=frame('Weak force range','A characteristic length from the mass of the W boson')
    x0,y0=155,543
    s+=line(x0,245,x0,y0,MUTED,2)+line(x0,y0,1070,y0,MUTED,2)
    pts=[]
    for i in range(240):
        u=i/239*5;pts.append((x0+u*175,y0-270*math.exp(-u)))
    s+=path('M'+' L'.join(f'{x:.2f} {y:.2f}' for x,y in pts),BLUE,5)
    s+=line(x0+175,265,x0+175,y0,GOLD,2,'6 8')
    s+=text(730,291,'h / (2π mW c)',48,GOLD,'middle',True)
    # Explicit positions avoid Cairo's inherited text-anchor / tspan bug.
    s+=text(548,364,'≈ 2.46 × 10',44)+text(774,341,'-18',27)+text(827,364,'m',44)
    s+=text(730,418,'Characteristic decay length',27,MUTED,'middle')
    s+=text(x0+175,588,'1 range',25,GOLD,'middle')
    s+=text(1045,588,'Distance',25,MUTED,'end')
    s+=text(600,671,'The interaction fades continuously; there is no sharp boundary.',28,INK,'middle')
    s+=text(600,711,'Curve shows the exponential suppression factor only, not a measured force law.',23,MUTED,'middle')
    save('Weak Force Range',s,'https://pdg.lbl.gov/2024/listings/rpp2024-list-w-boson.pdf','PDG 2024 · W-boson mass',
         'Using PDG 2024 W mass 80.3692 GeV/c² and NIST ℏc = 197.3269804 MeV fm gives ℏ/(mW c) ≈ 2.45526e-18 m. Curve is exp(-r/range), the exponential factor only, not the full Yukawa potential or a force measurement.',
         ['https://physics.nist.gov/cuu/Constants/Table/allascii.txt'])

    s=frame('Muonic hydrogen atom','A proton bound to one negative muon')
    s+='<defs><radialGradient id="mucloud"><stop stop-color="#83d8f2" stop-opacity="0.85"/><stop offset="0.4" stop-color="#65aed7" stop-opacity="0.25"/><stop offset="1" stop-color="#65aed7" stop-opacity="0"/></radialGradient></defs>'
    s+=circle(355,407,228,'url(#mucloud)')+circle(355,407,9,GOLD)
    s+=circle(355,407,159,'none','#67869e',1.5)
    s+=line(355,407,514,407,GOLD,2)+text(438,388,'aμ',29,GOLD,'middle')
    s+=text(720,292,'≈ 0.57 pm',59,GOLD,bold=True)
    s+=text(720,352,'2 × muonic Bohr radius',28)
    s+=text(720,422,'aμ ≈ 285 fm',35,BLUE)
    s+=text(720,485,'Muon probability cloud',26,MUTED)
    s+=text(720,531,'Proton enlarged for visibility',24,MUTED)
    s+=bracket(196,514,610,'2aμ',38)
    s+=text(600,710,'Characteristic size convention · the bound-state cloud extends beyond this radius.',23,MUTED,'middle')
    save('Muonic Hydrogen Atom',s,'https://doi.org/10.1140/epja/s10050-020-00195-9','FAMU collaboration (2020)',
         'The FAMU paper states a ground-state muonic Bohr radius of about 285 fm, including proton–muon reduced mass. Twice this radius is approximately 570 fm = 0.57 pm. Cloud is schematic, not bounded at aμ, and the proton dot is enlarged. This diameter is a convention, not the full wavefunction extent.')

    for particle,value in [('Tau','0.698 fm'),('Proton','1.32 fm'),('Muon','11.7 fm'),('Electron','2.43 pm')]:
        s=frame(particle+' Compton wavelength','A mass-associated quantum length · not a particle diameter')
        s+=text(600,264,'λC = h / (m c)',57,BLUE,'middle',True)
        pts=[]
        for i in range(241):
            u=i/240;pts.append((165+870*u,410-79*math.sin(math.tau*u)))
        s+=line(140,410,1060,410,'#324b62',1,'5 8')
        s+=path('M'+' L'.join(f'{x:.2f} {y:.2f}' for x,y in pts),BLUE,5)
        s+=line(165,410,165,547,MUTED,1,'4 8')+line(1035,410,1035,547,MUTED,1,'4 8')
        s+=bracket(165,1035,541,value,62)
        s+=text(600,671,'One Compton wavelength',30,INK,'middle')
        s+=text(600,710,'Conceptual wave glyph · not a photon emitted by this particle or a measured particle shape.',22,MUTED,'middle')
        save(particle+' Compton Wavelength',s,'https://physics.nist.gov/cuu/Constants/Table/allascii.txt','NIST · CODATA 2022',
             f'Ordinary (not reduced) Compton wavelength h/(mc), displayed as {value}, rounded from CODATA 2022. A single sine-wave glyph explains a length, with arbitrary amplitude; it is not a particle boundary, observed field oscillation, de Broglie wavelength or emitted-photon measurement.')

    (OUT/'LICENSE.txt').write_text('To the extent possible under law, Universe Scales waives all copyright and related rights in this directory’s original artwork under CC0 1.0 Universal.\nhttps://creativecommons.org/publicdomain/zero/1.0/\nScientific facts are cited in ../sources/facts.json; no source artwork was copied. The separately rendered ribosome uses CC0 PDB coordinates.\n')
    (HERE/'sources/facts.json').write_text(json.dumps(FACTS,ensure_ascii=False,indent=2)+'\n')
    (HERE/'diagram-credits.json').write_text(json.dumps(RECORDS,ensure_ascii=False,indent=2)+'\n')
    print(f'Built {len(RECORDS)} original diagrams and matching thumbnails.')


if __name__=='__main__':main()
