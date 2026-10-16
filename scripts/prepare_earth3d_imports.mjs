#!/usr/bin/env node
// Offline preparation of the four curated earth3d imports. Run stage first.
// Usage: node scripts/prepare_earth3d_imports.mjs STAGED_DIR OUTPUT_DIR MODULE_ROOT
// MODULE_ROOT contains @gltf-transform/{core,extensions,functions}@4.5.0 and meshoptimizer.
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [staged, output, modules] = process.argv.slice(2);
if (!staged || !output || !modules) throw new Error('Expected STAGED_DIR OUTPUT_DIR MODULE_ROOT');
const moduleAt = relative => import(pathToFileURL(path.resolve(modules, relative)).href);
const { NodeIO } = await moduleAt('@gltf-transform/core/dist/index.js');
const { ALL_EXTENSIONS } = await moduleAt('@gltf-transform/extensions/dist/index.js');
const { dedup, flatten, join, weld, simplify, prune, quantize } = await moduleAt('@gltf-transform/functions/dist/index.js');
const { MeshoptSimplifier } = await moduleAt('meshoptimizer/index.js');
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const sources = [
    ['earth3d-elephant-bird-egg', 'c46a999a49d547d8bab39706d7a6b6ee'],
    ['earth3d-boeing-747-8', 'cd1977bedc32412fa1ce2cda23520b84'],
    ['earth3d-komodo-dragon', 'a3bb3a390dd1466e9bbab4a994329d45'],
    ['earth3d-hindenburg', 'b347e808f561465dab568fa61734e262'],
];
fs.mkdirSync(output, { recursive: true });
for (const [id, uid] of sources) {
    const metadata = JSON.parse(fs.readFileSync(path.join(staged, `${uid}.json`)));
    if (metadata.uid !== uid || metadata.license !== 'by') throw new Error(`Unexpected source/license: ${uid}`);
    const doc = await io.read(path.join(staged, `${uid}.glb`));
    if (doc.getRoot().listSkins().length || doc.getRoot().listAnimations().length)
        throw new Error(`Expected static source: ${uid}`);
    await doc.transform(dedup(), flatten(), join(), weld());
    const count = doc.getRoot().listMeshes().reduce((sum, mesh) => sum + mesh.listPrimitives().reduce((sum, p) => {
        if (p.getMode() !== 4) throw new Error('Curated imports must contain triangles only');
        return sum + (p.getIndices()?.getCount() || p.getAttribute('POSITION').getCount()) / 3;
    }, 0), 0);
    const ratio = Math.min(1, 45000 / count);
    if (ratio < 1) await doc.transform(simplify({ simplifier: MeshoptSimplifier, ratio, error: .0008 }));
    if (id === 'earth3d-hindenburg') {
        // Raise only the neutral envelope material; retain markings and other colors.
        const envelope = doc.getRoot().listMaterials().find(m => m.getName() === 'Material.001');
        if (!envelope) throw new Error('Hindenburg envelope material missing');
        envelope.setBaseColorFactor([.65, .65, .65, 1]).setRoughnessFactor(.58).setMetallicFactor(.08);
    }
    await doc.transform(prune(), quantize({ quantizePosition: 16, quantizeNormal: 12, quantizeTexcoord: 14 }));
    await io.write(path.join(output, `${id}.glb`), doc);
    console.log(`${id}: ${fs.statSync(path.join(output, `${id}.glb`)).size.toLocaleString()} bytes`);
}
