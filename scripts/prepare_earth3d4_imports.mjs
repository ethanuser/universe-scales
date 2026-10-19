#!/usr/bin/env node
// Light processing of two existing, licensed scans. No authored geometry.
// node scripts/prepare_earth3d4_imports.mjs STAGED_DIR OUTPUT_DIR MODULE_ROOT
// Stage with sketchfab_models.py first; see handoff/earth3d4/REPORT.md.
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
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
    {
        id: 'earth3d4-fruit-fly', uid: 'ad29b897bd2b4e27bb04ab9d31baa117', triangles: 90000,
        stagedSha256: '00e14941b30e3a017426984ec45372972501235bc41d54e7e193f5ddccb7ef6e',
        archiveSha256: '210b91eb9bb8bbb8bbbb69c9372cf954c53aca7c1428769af5c5766f07ef661e',
    },
    {
        id: 'earth3d4-trex-skeleton', uid: '77e21c4e5d65468bbe11780ae0557b95', triangles: 55000,
        stagedSha256: '7c5a120a081f6b0b3f574ce44807fd533933dccf8ea9d51bd506a7059da11e74',
        archiveSha256: '8b9e4c5c9af64593eb2c44b920ce58fae1411501a6d0ee61e6034b9e05c04d16',
    },
];
fs.mkdirSync(output, { recursive: true });
for (const source of sources) {
    const metadata = JSON.parse(fs.readFileSync(path.join(staged, `${source.uid}.json`)));
    const file = path.join(staged, `${source.uid}.glb`);
    const hash = createHash('sha256').update(fs.readFileSync(file)).digest('hex');
    if (metadata.uid !== source.uid || metadata.license !== 'by'
        || metadata.source_sha256 !== source.archiveSha256 || hash !== source.stagedSha256)
        throw new Error(`Source/license/hash mismatch: ${source.uid}`);
    const doc = await io.read(file);
    if (doc.getRoot().listSkins().length || doc.getRoot().listAnimations().length)
        throw new Error(`Expected a static scan: ${source.uid}`);
    await doc.transform(dedup(), flatten(), join(), weld());
    const count = doc.getRoot().listMeshes().reduce((sum, mesh) => sum + mesh.listPrimitives().reduce((sum, p) => {
        if (p.getMode() !== 4) throw new Error('Expected triangles');
        return sum + (p.getIndices()?.getCount() || p.getAttribute('POSITION').getCount()) / 3;
    }, 0), 0);
    await doc.transform(
        simplify({ simplifier: MeshoptSimplifier, ratio: Math.min(1, source.triangles / count), error: .002 }),
        prune(), quantize({ quantizePosition: 16, quantizeNormal: 12, quantizeTexcoord: 14 }),
    );
    const destination = path.join(output, `${source.id}.glb`);
    await io.write(destination, doc);
    const bytes = fs.statSync(destination).size;
    if (bytes > 3000000) throw new Error(`Asset exceeds 3 MB: ${source.id}`);
    console.log(`${source.id}: ${bytes.toLocaleString()} bytes`);
}
