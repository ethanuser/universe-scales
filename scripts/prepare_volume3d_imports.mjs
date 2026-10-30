#!/usr/bin/env node
// Light processing of pinned public models; no authored surface geometry.
// node scripts/prepare_volume3d_imports.mjs STAGED_DIR MODULE_ROOT [OUTPUT_DIR]
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import * as THREE from '../js/vendor/three/three.module.min.js';

const [staged, modules, output = 'content/visualizations/models'] = process.argv.slice(2);
if (!staged || !modules) throw new Error('Expected STAGED_DIR MODULE_ROOT [OUTPUT_DIR]');
const moduleAt = relative => import(pathToFileURL(path.resolve(modules, relative)).href);
const { NodeIO } = await moduleAt('@gltf-transform/core/dist/index.js');
const { ALL_EXTENSIONS } = await moduleAt('@gltf-transform/extensions/dist/index.js');
const { dedup, weld, prune, simplify } = await moduleAt('@gltf-transform/functions/dist/index.js');
const { MeshoptSimplifier } = await moduleAt('meshoptimizer/index.js');
await MeshoptSimplifier.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const configs = [
    { id: 'volume3d-sugar-scan', file: '0227084e92ed4dc79e48e0bf271edd32.glb',
        hash: '021dca72c7715c9b20b342eefe98a776201ed815ebd4ff0e5060b0f16218c87b', ratio: .50 },
    { id: 'volume3d-nih-influenza', file: 'nih-influenza.glb',
        hash: '2fb62fa7544538e6d304901b0e690abfc8beffc9babf5b1772c67641eb2c54e8', ratio: .24, error: .01 },
    { id: 'volume3d-classic-bathtub', file: '7427e2c0c32c44b89deb058f6583742a.glb',
        hash: 'a9a5f7e4ba458cd7ac310bf0d80336cf1533c3522a271531e0edd99f2015cf30' },
];
fs.mkdirSync(output, { recursive: true });
for (const config of configs) {
    const file = path.join(staged, config.file);
    const hash = createHash('sha256').update(fs.readFileSync(file)).digest('hex');
    if (hash !== config.hash) throw new Error(`Unreviewed input: ${config.file}`);
    const doc = await io.read(file);
    if (doc.getRoot().listSkins().length || doc.getRoot().listAnimations().length)
        throw new Error('Expected static models');
    if (config.id === 'volume3d-sugar-scan') {
        // Select the source's exterior bulk envelope. Four tiny, reversed internal
        // shells describe enclosed pores, not the outside of the sugar cube.
        // Nothing is added, patched, stretched or moved.
        const primitives = doc.getRoot().listMeshes().flatMap(m => m.listPrimitives());
        if (primitives.length !== 1) throw new Error('Sugar scan structure changed');
        const primitive = primitives[0], pos = primitive.getAttribute('POSITION');
        const indices = primitive.getIndices().getArray();
        const parent = Array.from({ length: pos.getCount() }, (_, i) => i);
        const find = i => parent[i] === i ? i : (parent[i] = find(parent[i]));
        const unite = (a, b) => { parent[find(a)] = find(b); };
        // Identify coincident seam copies for connectivity only. Attributes and
        // coordinates in the retained triangles remain untouched.
        const seam = new Map();
        for (let i = 0; i < pos.getCount(); i++) {
            const key = pos.getElement(i, []).join(',');
            if (seam.has(key)) unite(i, seam.get(key)); else seam.set(key, i);
        }
        for (let i = 0; i < indices.length; i += 3) {
            unite(indices[i], indices[i + 1]); unite(indices[i], indices[i + 2]);
        }
        const groups = new Map();
        for (let i = 0; i < indices.length; i += 3) {
            const key = find(indices[i]);
            if (!groups.has(key)) groups.set(key, []);
            groups.get(key).push(...indices.slice(i, i + 3));
        }
        const shells = [...groups.values()].sort((a, b) => b.length - a.length);
        const sizes = shells.map(g => g.length / 3);
        if (JSON.stringify(sizes) !== JSON.stringify([107320, 122, 52, 52, 8]))
            throw new Error(`Sugar scan components changed: ${sizes}`);
        // Check the interpretation, rather than assuming all small components
        // are debris: these are reverse-wound interior pore shells. Every
        // source vertex in them must lie inside the exterior shell.
        const exterior = new THREE.BufferGeometry();
        exterior.setAttribute('position', new THREE.BufferAttribute(pos.getArray(), 3));
        exterior.setIndex(shells[0]);
        const mesh = new THREE.Mesh(exterior, new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }));
        mesh.updateMatrixWorld(true);
        const direction = new THREE.Vector3(.371, .529, .763).normalize();
        const signedVolume = shell => {
            let sum = 0;
            for (let i = 0; i < shell.length; i += 3) {
                const [a, b, c] = shell.slice(i, i + 3).map(k => new THREE.Vector3().fromArray(pos.getElement(k, [])));
                sum += a.dot(b.cross(c)) / 6;
            }
            return sum;
        };
        const volumes = shells.map(signedVolume);
        let checkedInteriorVertices = 0;
        for (const shell of shells.slice(1)) for (const index of new Set(shell)) {
            const point = new THREE.Vector3().fromArray(pos.getElement(index, []));
            const hits = new THREE.Raycaster(point, direction).intersectObject(mesh);
            const distances = hits.map(h => h.distance).filter((d, i, a) => !i || Math.abs(d - a[i - 1]) > 1e-7);
            if (distances.length % 2 !== 1) throw new Error('Sugar pore vertex outside exterior');
            checkedInteriorVertices++;
        }
        if (volumes.slice(1).some(v => v * volumes[0] >= 0)
            || Math.abs(volumes.slice(1).reduce((a, b) => a + b, 0) / volumes[0]) > .001)
            throw new Error('Sugar internal shell winding/size differs from reviewed source');
        console.log(JSON.stringify({ id: config.id, checkedInteriorVertices,
            removedSignedVolumeFraction: volumes.slice(1).reduce((a, b) => a + b, 0) / volumes[0],
            method: 'Odd ray-intersection parity for every removed source vertex; reverse winding and small volume verified. Not a general self-intersection certificate.' }));
        exterior.dispose(); mesh.material.dispose();
        primitive.getIndices().setArray(new Uint32Array(shells[0]));
        console.log(JSON.stringify({ id: config.id, sourceShellTriangles: sizes,
            retained: 'Exterior envelope; four internal reversed shells excluded' }));
    }
    // The NIH PLY-derived GLB supplies vertex colors and relies on glTF's
    // implicit white material. Make that default explicit, preserving colors.
    for (const mesh of doc.getRoot().listMeshes()) for (const primitive of mesh.listPrimitives()) {
        if (!primitive.getMaterial()) primitive.setMaterial(doc.createMaterial('Source vertex colors'));
    }
    await doc.transform(dedup(), weld());
    if (config.ratio) await doc.transform(simplify({ simplifier: MeshoptSimplifier,
        ratio: config.ratio, error: config.error || .001 }));
    await doc.transform(prune());
    const destination = path.join(output, `${config.id}.glb`);
    await io.write(destination, doc);
    if (fs.statSync(destination).size > 3000000) throw new Error(`Over budget: ${config.id}`);
    console.log(`${config.id}: ${fs.statSync(destination).size} bytes`);
}
