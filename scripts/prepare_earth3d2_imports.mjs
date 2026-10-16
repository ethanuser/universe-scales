#!/usr/bin/env node
// Input: Python-baked static animal; output: final GLB; modules: glTF Transform 4.5.0 + mikktspace.
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const [input, output, modules, kind = 'whale'] = process.argv.slice(2);
if (!input || !output || !modules || !['whale', 'elephant'].includes(kind))
    throw new Error('Expected STATIC_ANIMAL_GLB OUTPUT_GLB MODULE_ROOT [whale|elephant]');
const moduleAt = relative => import(pathToFileURL(path.resolve(modules, relative)).href);
const { NodeIO } = await moduleAt('@gltf-transform/core/dist/index.js');
const { ALL_EXTENSIONS } = await moduleAt('@gltf-transform/extensions/dist/index.js');
const { dedup, flatten, join, weld, unweld, tangents, simplify, prune, quantize } = await moduleAt('@gltf-transform/functions/dist/index.js');
const { MeshoptSimplifier } = await moduleAt('meshoptimizer/index.js');
const { generateTangents } = await moduleAt('mikktspace/dist/main/mikktspace_main.js');
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc = await io.read(input);
if (doc.getRoot().listSkins().length || doc.getRoot().listAnimations().length)
    throw new Error('Expected static bind-pose geometry');
await doc.transform(dedup(), flatten(), join(), weld());
const count = doc.getRoot().listMeshes().reduce((sum, mesh) => sum + mesh.listPrimitives().reduce((s, p) => {
    if (p.getMode() !== 4) throw new Error('Curated animals must contain triangles only');
    return s + (p.getIndices()?.getCount() || p.getAttribute('POSITION').getCount()) / 3;
}, 0), 0);
if (count > 45000) await doc.transform(simplify({ simplifier: MeshoptSimplifier, ratio: 45000 / count, error: .01 }));
// The source provides no base-color map. Neutral gray-blue is authored display color.
if (kind === 'whale') for (const mat of doc.getRoot().listMaterials())
    mat.setBaseColorFactor([.20, .245, .27, 1]).setMetallicFactor(0).setRoughnessFactor(.74);
await doc.transform(unweld(), tangents({ generateTangents }), weld());
await doc.transform(prune(), quantize({ quantizePosition: 16, quantizeNormal: 12, quantizeTexcoord: 14 }));
await io.write(output, doc);
