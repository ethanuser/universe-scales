#!/usr/bin/env node
// Curated, static imports. Stage with sketchfab_models.py outside the repository.
// Usage: node scripts/prepare_earth3d3_imports.mjs STAGED_DIR OUTPUT_DIR MODULE_ROOT
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

const [staged, output, modules] = process.argv.slice(2);
if (!staged || !output || !modules) throw new Error('Expected STAGED_DIR OUTPUT_DIR MODULE_ROOT');
const at = relative => import(pathToFileURL(path.resolve(modules, relative)).href);
const { NodeIO } = await at('@gltf-transform/core/dist/index.js');
const { ALL_EXTENSIONS } = await at('@gltf-transform/extensions/dist/index.js');
const { dedup, flatten, join, weld, simplify, prune, quantize, metalRough, compactPrimitive } = await at('@gltf-transform/functions/dist/index.js');
const { MeshoptSimplifier } = await at('meshoptimizer/index.js');
const sharp = createRequire(path.resolve(modules, 'package.json'))('sharp');
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const sources = [
    ['earth3d3-giant-pacific-octopus', '7fb48f6cbcd54149bb23837a3ac09b2e', 'cc0'],
    ['earth3d3-hyperion-redwood', '2c34fb28a756474eb8072a450c8f632b', 'by'],
    ['earth3d3-titanic', 'fa41e6b093b84010a462ef190210d90b', 'by'],
];
fs.mkdirSync(output, { recursive: true });
for (const [id, uid, license] of sources) {
    const metadata = JSON.parse(fs.readFileSync(path.join(staged, `${uid}.json`)));
    if (metadata.uid !== uid || metadata.license !== license) throw new Error(`Unexpected identity/license: ${uid}`);
    const doc = await io.read(path.join(staged, `${uid}.glb`));
    if (doc.getRoot().listSkins().length || doc.getRoot().listAnimations().length)
        throw new Error(`Expected static source: ${uid}`);
    await doc.transform(metalRough());
    // The octopus scan includes a disconnected color calibration cube, not anatomy.
    if (id === 'earth3d3-giant-pacific-octopus') {
        const cube = doc.getRoot().listNodes().find(n => n.getName() === 'Object_4');
        if (!cube) throw new Error('Expected octopus calibration cube');
        cube.dispose();
    }
    // Alpha testing keeps overlapping leaf cards from sorting as large transparent planes.
    if (id === 'earth3d3-hyperion-redwood') for (const m of doc.getRoot().listMaterials()) {
        if (m.getAlphaMode() === 'BLEND') m.setAlphaMode('MASK').setAlphaCutoff(.45).setDoubleSided(true);
    }
    await doc.transform(dedup(), flatten(), join(), weld());
    if (id === 'earth3d3-giant-pacific-octopus') {
        // The second atlas uses U in [1,2] with REPEAT wrapping. An integer
        // translation preserves every texture lookup and permits 16-bit UVs.
        for (const m of doc.getRoot().listMeshes()) for (const p of m.listPrimitives()) {
            const uv = p.getAttribute('TEXCOORD_0');
            const values = uv.getArray();
            let minU = Infinity;
            for (let i = 0; i < values.length; i += 2) minU = Math.min(minU, values[i]);
            const shift = Math.floor(minU);
            for (let i = 0; i < values.length; i += 2) values[i] -= shift;
            uv.setArray(values);
        }
    }
    for (const t of doc.getRoot().listTextures()) {
        const alpha = doc.getRoot().listMaterials().some(m => m.getBaseColorTexture() === t && m.getAlphaMode() !== 'OPAQUE');
        let encoder = sharp(t.getImage()).resize(alpha ? 512 : 1024, alpha ? 512 : 1024, { fit: 'inside', withoutEnlargement: true });
        encoder = alpha ? encoder.png({ compressionLevel: 9 }) : encoder.removeAlpha().jpeg({ quality: 86 });
        t.setImage(await encoder.toBuffer()).setMimeType(alpha ? 'image/png' : 'image/jpeg');
    }
    const count = doc.getRoot().listMeshes().reduce((sum, m) => sum + m.listPrimitives().reduce((s, p) => {
        if (p.getMode() !== 4) return s; // Titanic retains its source linework.
        return s + (p.getIndices()?.getCount() || p.getAttribute('POSITION').getCount()) / 3;
    }, 0), 0);
    if (id === 'earth3d3-giant-pacific-octopus') {
        await MeshoptSimplifier.ready;
        for (const m of doc.getRoot().listMeshes()) for (const p of m.listPrimitives()) {
            const uv = p.getAttribute('TEXCOORD_0');
            const [indices] = MeshoptSimplifier.simplifyWithAttributes(
                new Uint32Array(p.getIndices().getArray()), p.getAttribute('POSITION').getArray(), 3,
                uv.getArray(), 2, [.2, .2], null,
                Math.floor(p.getIndices().getCount() * Math.min(1, 55000 / count) / 3) * 3,
                .008, ['Permissive']);
            p.setIndices(p.getIndices().clone().setArray(indices));
            compactPrimitive(p);
        }
    } else if (count > 55000) {
        await doc.transform(simplify({ simplifier: MeshoptSimplifier, ratio: 55000 / count, error: .012 }));
    }
    await doc.transform(prune(), quantize({ quantizePosition: 16, quantizeNormal: 12, quantizeTexcoord: 14 }));
    await io.write(path.join(output, `${id}.glb`), doc);
    console.log(`${id}: ${fs.statSync(path.join(output, `${id}.glb`)).size} bytes`);
}
