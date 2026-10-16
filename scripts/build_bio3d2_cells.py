#!/usr/bin/env python3
"""Offline, dimensioned explanatory cell diagrams; not microscopy reconstructions.

One unit is a micrometre, except the bilayer (nanometres). Only the calibrated
overall dimensions are quantitative. Internal positions, counts, colours and
proportions are authored teaching geometry. See each model's source note.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from geo_glb_common import GLB, grid_indices
from build_bio3d_models import clean_mesh, normals

ROOT = Path(__file__).resolve().parents[1]
BLOOD = 'https://www.histologyguide.org/slideview/MH-033hr-blood-smear/07-slide-1.html'
SPECS = {
    'platelet': ('Human Platelet', 2.5, BLOOD,
        'Resting discoid platelet, 2.5 µm across. An explanatory cutaway exposes granules and the peripheral microtubule band; no nucleus. Disc thickness, granule placement/count and band geometry are authored, not measurements or an EM reconstruction. Colours distinguish structures; they are not natural colours.'),
    'yeast': ('Budding Yeast Cell', 5, 'https://www.open.edu/openlearncreate/mod/oucontent/view.php?id=160725&section=3.9',
        'A 5 µm mother cell with a small early bud. The bud extends beyond the calibrated mother-cell diameter. Cutaway wall, vacuole, nucleus and mitochondria are a sourced explanatory illustration, not segmented microscopy. Internal sizes, counts and positions are authored; wall thickness is a display proxy.'),
    'neutrophil': ('Neutrophil', 12, BLOOD,
        'A 12 µm representative neutrophil diagram with a connected three-lobed nucleus and cytoplasmic granules. The catalog diameter is a blood-smear convention; this rounded explanatory cutaway is not a measured smear or a reconstructed cell. Lobe shape, granule count, organelle proportions and colours are authored.'),
    'egg': ('Human Egg Cell', 120, 'https://www.nichd.nih.gov/research/atNICHD/Investigators/gomez-lobo/research/nomenclature-workshop-2021',
        'A representative 120 µm human MII oocyte (cell diameter, excluding the zona pellucida). A cutaway zona surrounds the oocyte, with a small first polar body in the perivitelline space and an indicated peripheral meiotic spindle. No interphase nucleus is shown. Coat thickness, spindle, granules and polar-body geometry/positions are illustrative, not a patient scan; cumulus cells are omitted.'),
    'capillary': ('Human Capillary', 7, 'https://www.histologyguide.org/EM-view/EM-213-capillary/09-photo-1.html',
        'A short cutaway segment of a continuous capillary with a representative 7 µm outer diameter. The hollow lumen, endothelial wall, basal lamina and one endothelial nucleus are explanatory. Segment ends and viewing opening are authored cuts; segment length is not the catalog quantity. Wall/lamina thickness, nucleus size and cell seams are display proxies, not measurements from the cited TEM.'),
    'membrane': ('Cell Membrane', 4, 'https://pubmed.ncbi.nlm.nih.gov/29689220/',
        'A 4 nm-thick schematic phospholipid bilayer patch. Teal hydrophilic heads face water on both sides; paired gold hydrophobic tails face inward. The small lateral window is authored to keep the thickness legible at true scale. Regular spacing, molecular shape, lipid count and colours are schematic, not atomic coordinates or an MD snapshot. Proteins, sterols and glycans are omitted.'),
    'cone': ('Human Cone Cell', 45, 'https://en.wikipedia.org/wiki/Cone_cell',
        'A representative 45 µm retinal cone-cell diagram, with a tapered folded-membrane outer segment, connecting cilium, mitochondria-rich inner segment, nucleus and synaptic pedicel. The total length follows the catalog’s approximate convention; regional proportions vary across the retina. Internal lengths, visible fold count, mitochondria, colours and cutaway are authored explanatory geometry, not a human cell reconstruction.'),
}


class Diagram:
    def __init__(self):
        self.glb = GLB('Universe Scales: sourced explanatory cell diagram')
        self.parts = {}

    def material(self, name, rgb, rough=.7):
        return self.glb.material(name, (*rgb, 1), rough=rough, double_sided=False)

    def add(self, name, p, f, material):
        p, f = clean_mesh(np.asarray(p, float), np.asarray(f).reshape(-1, 3))
        self.parts.setdefault((name, material), []).append((p, f))

    def ellipsoid(self, name, center, radii, material, half=False, detail=24):
        # Longitude runs around Y; z <= 0 is the retained half of a cutaway.
        lon, lat = np.meshgrid(np.linspace(np.pi if half else 0, 2*np.pi, detail*2+1),
                               np.linspace(-np.pi/2, np.pi/2, detail+1))
        unit = np.stack((np.cos(lat)*np.cos(lon), np.sin(lat), np.cos(lat)*np.sin(lon)), -1).reshape(-1, 3)
        p = unit*np.array(radii)+np.array(center)
        f = grid_indices(detail+1, detail*2+1).reshape(-1, 3)
        self.add(name, p, f, material)

    def shell(self, name, center, radii, thickness, material):
        # Rear hemisphere plus inner face and a solid elliptical cut rim.
        self.ellipsoid(name, center, radii, material, half=True, detail=40)
        inner = np.array(radii)-thickness
        before = len(self.parts[(name, material)])
        self.ellipsoid(name, center, inner, material, half=True, detail=40)
        p, f = self.parts[(name, material)][before]
        self.parts[(name, material)][before] = (p, f[:, ::-1])
        a = np.linspace(0, 2*np.pi, 161)
        p = np.concatenate([np.column_stack((r[0]*np.cos(a), r[1]*np.sin(a), np.zeros(len(a))))+center
                            for r in (radii, inner)])
        n = len(a)
        f = [(i, i+1, n+i) for i in range(n-1)] + [(i+1, n+i+1, n+i) for i in range(n-1)]
        self.add(name, p, f, material)

    def tube(self, name, path, radius, material, sides=10):
        path = np.asarray(path, float)
        tangent = np.gradient(path, axis=0); tangent /= np.linalg.norm(tangent, axis=1)[:, None]
        # Choose a stable frame for each ring, suitable for these gently bent paths.
        axis = np.tile([0., 0., 1.], (len(path), 1))
        axis[np.abs(tangent[:, 2]) > .9] = [0, 1, 0]
        u = np.cross(tangent, axis); u /= np.linalg.norm(u, axis=1)[:, None]
        v = np.cross(tangent, u)
        a = np.linspace(0, 2*np.pi, sides+1)
        p = (path[:, None, :] + radius*(u[:, None, :]*np.cos(a)[None, :, None] + v[:, None, :]*np.sin(a)[None, :, None])).reshape(-1, 3)
        f = grid_indices(len(path), sides+1).reshape(-1, 3)[:, ::-1]
        for ring, reverse in [(0, True), (len(path)-1, False)]:
            offset = ring*(sides+1)
            cap = np.array([(offset, offset+i, offset+i+1) for i in range(1, sides)])
            f = np.concatenate((f, cap[:, ::-1] if reverse else cap))
        self.add(name, p, f, material)

    def finish(self, path):
        # Merge repeated structures by material/name to avoid hundreds of draw calls.
        for (name, mat), pieces in self.parts.items():
            positions, faces, offset = [], [], 0
            for p, f in pieces:
                positions.append(p); faces.append(f+offset); offset += len(p)
            p, f = clean_mesh(np.concatenate(positions), np.concatenate(faces))
            self.glb.mesh_node(name, [self.glb.primitive(p, f.ravel(), mat, normals=normals(p, f))])
        self.glb.write(path)


def granules(d, rng, count, radii, radius, material, name='Illustrative cytoplasmic granules', reject=None):
    for _ in range(count):
        for attempt in range(10000):
            p = rng.uniform(-1, 1, 3)
            if np.dot(p, p) < .78 and p[2] > -.1:
                p *= radii
                if reject is None or not reject(p):
                    break
        else:
            raise ValueError('Granule rejection exhausted')
        d.ellipsoid(name, p, np.repeat(radius*rng.uniform(.75, 1.2), 3), material, detail=6)


def cell(kind):
    d = Diagram(); rng = np.random.default_rng(20261016)
    teal = d.material('Cut cell envelope (illustrative teal)', (.11, .46, .45))
    purple = d.material('Nuclear material (illustrative violet)', (.31, .16, .48))
    gold = d.material('Storage/secretory structures (illustrative gold)', (.85, .43, .13))
    rose = d.material('Cytoplasm / supporting tissue (illustrative rose)', (.66, .36, .35))
    pale = d.material('Inner boundary / vacuole (illustrative pale blue)', (.42, .69, .70))
    if kind == 'platelet':
        d.shell('Resting discoid platelet cutaway', np.zeros(3), (1.25, 1.25, .25), .035, teal)
        a = np.linspace(0, 2*np.pi, 161)
        d.tube('Peripheral marginal band (schematic bundle)', np.column_stack((1.12*np.cos(a), 1.12*np.sin(a), -.03+0*a)), .035, pale)
        granules(d, rng, 28, np.array([1, 1, .15]), .09, gold)
    elif kind == 'yeast':
        d.shell('Mother-cell wall cutaway; 5 um across X', np.zeros(3), (2.5, 2.2, 2.2), .10, teal)
        d.ellipsoid('Early daughter bud', (2.65, 1.0, -.15), (.95, .95, .9), teal)
        d.ellipsoid('Vacuole (illustrative)', (-.6, -.3, -.1), (1.15, 1.25, 1), pale)
        d.ellipsoid('Nucleus (illustrative)', (1, .15, .3), (.7, .8, .65), purple)
        for pos in [(-1.4, 1, .2), (.2, -1.5, .1), (.5, 1.4, .2)]:
            d.ellipsoid('Mitochondria (illustrative)', pos, (.38, .16, .18), gold)
    elif kind == 'neutrophil':
        d.shell('Cell boundary; explanatory viewing cut', np.zeros(3), (6, 6, 6), .15, rose)
        lobes = np.array([[-2.3, 1, 1], [0, 2.2, .5], [2.2, .3, .8]])
        for p in lobes:
            d.ellipsoid('Connected nuclear lobes', p, (1.35, 1.65, 1.2), purple)
        d.tube('Narrow connections between nuclear lobes', lobes, .22, purple)
        granules(d, rng, 125, np.array([5.5, 5.5, 4]), .18, gold,
                 reject=lambda p: np.any(np.linalg.norm((p-lobes)/[1.65, 1.95, 1.5], axis=1) < 1))
    elif kind == 'egg':
        d.shell('Zona pellucida; extracellular coat (cutaway)', np.zeros(3), (68, 68, 68), 3, pale)
        d.shell('Oocyte boundary; 120 um cell diameter', np.zeros(3), (60, 60, 60), .6, rose)
        granules(d, rng, 150, np.array([57, 57, 42]), 1.1, gold)
        d.ellipsoid('First polar body (illustrative)', (0, 62.5, 0), (4, 1.5, 3), purple)
        d.ellipsoid('Peripheral meiotic spindle (schematic)', (43, 23, 6), (3, 6, 3), pale)
        for yy in np.linspace(20, 26, 5):
            d.tube('Chromosomes indicated schematically', [(42, yy, 9), (44, yy+.5, 9)], .45, purple)
    elif kind == 'membrane':
        # Exact outer surfaces at +/- 2 nm. Tails never point into water.
        for sign in (-1, 1):
            for x in np.linspace(-1.5, 1.5, 6):
                for z in np.linspace(-.9, .9, 4):
                    d.ellipsoid('Hydrophilic head groups', (x, sign*1.75, z), (.25, .25, .25), teal, detail=8)
                    for dx in (-.11, .11):
                        bend = -.09 if dx < 0 else .08
                        path = [(x+dx, sign*y, z+shift) for y, shift in [(1.5, 0), (1.15, .015), (.8, bend), (.45, .02), (.025, .04)]]
                        d.tube('Paired inward hydrophobic tails', path, .055, gold, sides=8)
    elif kind == 'cone':
        d.ellipsoid('Synaptic pedicel', (0, 1, 0), (2, 1, 1.6), teal)
        d.tube('Inner fibre', [(0, 2, 0), (0, 8, 0)], .45, teal)
        d.ellipsoid('Nuclear cell body', (0, 11, 0), (1.65, 3.5, 1.5), teal)
        d.ellipsoid('Nucleus', (0, 11, 1.1), (1.15, 2.2, .5), purple)
        d.tube('Continuous cell body to inner segment', [(0, 14, 0), (0, 17, 0)], .55, teal)
        d.ellipsoid('Inner segment; mitochondria-rich ellipsoid', (0, 22, 0), (1.65, 7, 1.4), teal, half=True)
        for x in [-.85, 0, .85]:
            d.ellipsoid('Inner segment mitochondria (schematic)', (x, 24, .1), (.25, 3, .3), gold)
        d.tube('Connecting cilium', [(0, 28, 0), (0, 30, 0)], .24, pale)
        d.tube('Outer-segment central continuity (schematic)', [(0, 30, 0), (0, 44.9, 0)], .07, gold)
        yy, aa = np.meshgrid(np.linspace(30, 44.9, 71), np.linspace(np.pi, 2*np.pi, 33), indexing='ij')
        rr = 1.3*(45-yy)/15+.08
        p = np.stack((rr*np.cos(aa), yy, rr*np.sin(aa)), -1).reshape(-1, 3)
        d.add('Outer membrane joining the folds (rear half)', p, grid_indices(71, 33), gold)
        # Visible stacked folds are a graphic sampling, not the biological count.
        for y in np.linspace(30.2, 44.8, 70):
            r = 1.3*(45-y)/15+.08
            d.ellipsoid('Outer segment membrane folds (schematic)', (0, y, 0), (r, .075, r), gold, detail=8)
        d.ellipsoid('Outer-segment tip', (0, 44.9, 0), (.1, .1, .1), gold, detail=8)
    elif kind == 'capillary':
        # X axis, sector removed toward +Z. Annular cut faces close the wall.
        a = np.linspace(np.radians(150), np.radians(390), 121)
        x = np.array([-2.75, 2.75])
        for name, r0, r1, mat in [('Basal lamina (display thickness)', 3.43, 3.5, purple),
                                  ('Endothelial wall (display thickness)', 3.05, 3.43, rose)]:
            pieces = []
            for radius, reverse in [(r1, False), (r0, True)]:
                xx, aa = np.meshgrid(x, a, indexing='ij')
                p = np.stack((xx, radius*np.cos(aa), radius*np.sin(aa)), -1).reshape(-1, 3)
                f = grid_indices(2, len(a)).reshape(-1, 3)
                d.add(name, p, f if reverse else f[:, ::-1], mat)
            for end in x:
                p = np.array([[end, r*np.cos(t), r*np.sin(t)] for r in [r0, r1] for t in a])
                f = grid_indices(2, len(a)).reshape(-1, 3)
                d.add(name, p, f[:, ::-1] if end < 0 else f, mat)
            for t in [a[0], a[-1]]:
                p = [[xx, r*np.cos(t), r*np.sin(t)] for xx in x for r in [r0, r1]]
                f = [[0, 1, 2], [1, 3, 2]]
                d.add(name, p, f if t == a[0] else np.array(f)[:, ::-1], mat)
        d.ellipsoid('Endothelial nucleus bulging into lumen (illustrative)', (0, -2.7, 0), (1.3, .35, .8), purple)
    else:
        raise ValueError(kind)
    return d


def entry(kind):
    name, ref, basis, note = SPECS[kind]
    pose = {'reference_size': ref, 'yaw': -15, 'pitch': 10, 'layout_width_factor': 1.3}
    if kind == 'platelet': pose.update(yaw=-20, pitch=22)
    if kind == 'cone': pose.update(roll=-16, pitch=0, yaw=-10)
    if kind == 'capillary': pose.update(yaw=-18, pitch=12)
    if kind == 'membrane': pose.update(yaw=-22, pitch=12)
    return dict(id='bio3d2-'+kind, name=name, source=basis, basis_url=basis,
        basis_label='Biological basis and representative dimension', author='Universe Scales contributors',
        license='CC0-1.0', license_url='https://creativecommons.org/publicdomain/zero/1.0/',
        license_files=['licenses/CC0-1.0.txt'], matches={'length': [name]}, geometry='mesh',
        representation='authored_illustration', volume_semantics='not_applicable', closed_volume_checked=False,
        presentation={**pose, 'display_label': name+' (diagram)'}, note=note,
        processing={'script': 'scripts/build_bio3d2_cells.py', 'model_unit': 'nm' if kind == 'membrane' else 'um',
            'calibrated_quantity': 'bilayer thickness' if kind == 'membrane' else 'mother-cell diameter' if kind == 'yeast' else 'outer vessel diameter' if kind == 'capillary' else 'total cell length' if kind == 'cone' else 'cell diameter',
            'provenance': f'content/visualizations/models/sources/bio3d2-{kind}.md'})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=Path('/tmp/bio3d2/cells'))
    args = p.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    for kind in SPECS:
        cell(kind).finish(args.output/f'bio3d2-{kind}.glb')
        (args.output/f'bio3d2-{kind}.entry.json').write_text(json.dumps(entry(kind), indent=2)+'\n')
        print(kind, (args.output/f'bio3d2-{kind}.glb').stat().st_size)


if __name__ == '__main__': main()
