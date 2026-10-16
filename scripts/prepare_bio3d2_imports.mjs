#!/usr/bin/env node
// Offline static-scene preparation. Stage licensed sources with sketchfab_models.py.
// node scripts/prepare_bio3d2_imports.mjs STAGED OUTPUT MODULE_ROOT
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
const [staged, output, modules] = process.argv.slice(2);
if (!modules) throw new Error('Expected STAGED OUTPUT MODULE_ROOT');
const at = p => import(pathToFileURL(path.resolve(modules, p)).href);
const { NodeIO } = await at('@gltf-transform/core/dist/index.js');
const { ALL_EXTENSIONS } = await at('@gltf-transform/extensions/dist/index.js');
const { dedup, flatten, join, weld, simplify, prune, quantize, metalRough } = await at('@gltf-transform/functions/dist/index.js');
const { MeshoptSimplifier } = await at('meshoptimizer/index.js');
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
fs.mkdirSync(output, { recursive: true });
const sources = [
    '4c02b0c865d440f0a0b971d77d6e315e', // montanhabio chloroplast cutaway
    'f300e988fa5d4e749b04445efebfba8a', // .hapto / Senckenberg bdelloid
    '7621abd3b4604d95bad90f9a1aaac51f', // ScannerDev external eye
    'ee629bd30e4a47899de1b30b9b71c905', // ETAIN / Thielens worker microCT
];
for (const uid of sources) {
    const meta = JSON.parse(fs.readFileSync(path.join(staged, `${uid}.json`)));
    if (meta.uid !== uid || !['by', 'cc0'].includes(meta.license)) throw new Error('Unapproved license');
    const pins = new URL('../content/visualizations/models/sources/bio3d2/', import.meta.url);
    const pin = fs.readdirSync(pins).filter(n => n.endsWith('.json')).map(n => JSON.parse(fs.readFileSync(new URL(n, pins))))
        .find(p => p.uid === uid);
    const hash = createHash('sha256').update(fs.readFileSync(path.join(staged, `${uid}.glb`))).digest('hex');
    if (!pin || hash !== pin.staged_glb_sha256 || meta.source_sha256 !== pin.source_archive_sha256)
        throw new Error(`Source differs from the reviewed pin: ${uid}`);
    const doc = await io.read(path.join(staged, `${uid}.glb`));
    if (doc.getRoot().listSkins().length || doc.getRoot().listAnimations().length)
        throw new Error(`Static source required: ${uid}`);
    await doc.transform(metalRough());
    if (uid === '4c02b0c865d440f0a0b971d77d6e315e') {
        for (const n of doc.getRoot().listNodes()) {
            if (n.getName() === 'Object_49') n.dispose(); // Floating title, not anatomy.
            const mesh = n.getMesh();
            if (!mesh) continue;
            for (const p of mesh.listPrimitives()) {
                const m = p.getMaterial().clone();
                m.setBaseColorFactor(['Object_31', 'Object_33', 'Object_35', 'Object_37'].includes(n.getName()) ? [.78, .43, .12, 1] :
                    ['Object_4', 'Object_5'].includes(n.getName()) ? [.22, .48, .11, 1] : [.10, .32, .08, 1]);
                m.setRoughnessFactor(.78).setMetallicFactor(0); p.setMaterial(m);
            }
        }
    }
    if (uid === 'f300e988fa5d4e749b04445efebfba8a') {
        // Source stores its painted educational colours in an emissive map.
        // Use that map as ordinary base colour so the animal responds to light.
        for (const m of doc.getRoot().listMaterials()) {
            const texture = m.getEmissiveTexture();
            if (!texture) throw new Error('Expected Rotifera painted map');
            m.setBaseColorTexture(texture).setBaseColorFactor([1, 1, 1, 1]);
            m.setEmissiveTexture(null).setEmissiveFactor([0, 0, 0]).setRoughnessFactor(.72);
        }
    }
    if (uid === 'ee629bd30e4a47899de1b30b9b71c905') {
        for (const m of doc.getRoot().listMaterials())
            m.setBaseColorFactor([.62, .38, .12, 1]).setRoughnessFactor(.76).setMetallicFactor(0);
    }
    await doc.transform(dedup(), flatten(), join(), weld());
    const count = doc.getRoot().listMeshes().reduce((s, m) => s+m.listPrimitives().reduce((n, p) => {
        if (p.getMode() !== 4) throw new Error('Expected triangles');
        return n+(p.getIndices()?.getCount() || p.getAttribute('POSITION').getCount())/3;
    }, 0), 0);
    if (count > 50000) await doc.transform(simplify({ simplifier: MeshoptSimplifier, ratio: 50000/count, error: .005 }));
    await doc.transform(prune(), quantize({ quantizePosition: 16, quantizeNormal: 12, quantizeTexcoord: 14 }));
    await io.write(path.join(output, `${uid}.glb`), doc);
    console.log(`${uid}: ${fs.statSync(path.join(output, `${uid}.glb`)).size} bytes`);
}
