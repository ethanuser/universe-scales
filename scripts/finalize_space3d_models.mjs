#!/usr/bin/env node
// Offline tangent generation. NODE_MODULES must contain glTF Transform 4.5.0
// and mikktspace. No runtime dependencies or geometry decoder are added.
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const modules = process.argv[2];
if (!modules) throw new Error('Usage: finalize_space3d_models.mjs NODE_MODULES');
const require = createRequire(path.join(path.resolve(modules), '_space3d.cjs'));
const { NodeIO } = require('@gltf-transform/core');
const { ALL_EXTENSIONS } = require('@gltf-transform/extensions');
const { tangents, prune, unweld, weld } = require('@gltf-transform/functions');
const { generateTangents } = require('mikktspace');
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
for (const file of fs.readdirSync('handoff/space3d').filter(f => f.endsWith('.entry.json'))) {
    const entryPath = path.join('handoff/space3d', file);
    const entry = JSON.parse(fs.readFileSync(entryPath));
    if (entry.id === 'nasa-moon') continue; // reused asset must remain byte-identical
    const document = await io.read(entry.src);
    if (!document.getRoot().listMaterials().some(m => m.getNormalTexture())) continue;
    await document.transform(unweld(), tangents({ generateTangents }));
    for (const mesh of document.getRoot().listMeshes()) {
        for (const primitive of mesh.listPrimitives()) {
            const tangent = primitive.getAttribute('TANGENT');
            const normal = primitive.getAttribute('NORMAL');
            if (!tangent || !normal) continue;
            const t = tangent.getArray(), n = normal.getArray();
            for (let i = 0; i < tangent.getCount(); i++) {
                if (Math.hypot(t[4*i], t[4*i+1], t[4*i+2]) > .5) continue;
                // Undefined UV-pole directions get an orthogonal unit basis.
                const nx = n[3*i], ny = n[3*i+1], nz = n[3*i+2];
                const axis = Math.abs(nx) < .8 ? [1, 0, 0] : [0, 1, 0];
                const v = [ny*axis[2]-nz*axis[1], nz*axis[0]-nx*axis[2], nx*axis[1]-ny*axis[0]];
                const length = Math.hypot(...v);
                for (let j = 0; j < 3; j++) t[4*i+j] = v[j]/length;
                t[4*i+3] = 1;
            }
        }
    }
    await document.transform(weld(), prune());
    await io.write(entry.src, document);
    const operation = 'Generate MikkTSpace tangents for normal-mapped primitives; prune unused export resources';
    if (!entry.processing.operations.includes(operation)) entry.processing.operations.push(operation);
    fs.writeFileSync(entryPath, JSON.stringify(entry, null, 2) + '\n');
    execFileSync('venv/bin/python', ['scripts/register_model.py', entryPath, entry.src], { stdio: 'inherit' });
    // The registrar refreshes all stats; preserve its final entry for integration.
    const final = JSON.parse(fs.readFileSync('content/visualizations/models.json')).models.find(m => m.id === entry.id);
    fs.writeFileSync(entryPath, JSON.stringify(final, null, 2) + '\n');
}
