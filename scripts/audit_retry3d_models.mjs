#!/usr/bin/env node
// Vendored loader, exact vertices/bounds; no WebGL or sprite/lighting approval.
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import * as THREE from '../js/vendor/three/three.module.min.js';

const root = new URL('../', import.meta.url);
const threeURL = new URL('../js/vendor/three/three.module.min.js', import.meta.url).href;
const moduleURL = source => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const utilities = moduleURL(fs.readFileSync(new URL('js/vendor/three/addons/utils/BufferGeometryUtils.js', root), 'utf8')
    .replace("from 'three'", `from '${threeURL}'`));
const loaderURL = moduleURL(fs.readFileSync(new URL('js/vendor/three/addons/loaders/GLTFLoader.js', root), 'utf8')
    .replace("from 'three'", `from '${threeURL}'`)
    .replace("from '../utils/BufferGeometryUtils.js'", `from '${utilities}'`));
globalThis.self = globalThis;
globalThis.ProgressEvent = class { constructor(type, init) { Object.assign(this, init); } };
const { GLTFLoader } = await import(loaderURL);
const registry = JSON.parse(fs.readFileSync(new URL('content/visualizations/models.json', root))).models;
const results = [];
for (const file of fs.readdirSync(new URL('handoff/retry3d', root)).filter(p => p.endsWith('.entry.json')).sort()) {
    const entry = JSON.parse(fs.readFileSync(new URL(`handoff/retry3d/${file}`, root)));
    const bytes = fs.readFileSync(new URL(entry.src, root));
    const sha256 = createHash('sha256').update(bytes).digest('hex');
    if (entry.sha256 !== sha256) throw new Error(`Handoff/file mismatch: ${entry.id}`);
    const registered = registry.find(m => m.id === entry.id);
    if (registered && registered.sha256 !== sha256) throw new Error(`Registry mismatch: ${entry.id}`);
    const scene = (await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '')).scene;
    scene.updateMatrixWorld(true);
    const nativeExtent = new THREE.Box3().setFromObject(scene, true).getSize(new THREE.Vector3());
    let points = 0, triangles = 0;
    scene.traverse(n => {
        if (n.isPoints) points += n.geometry.attributes.position.count;
        if (n.isMesh) {
            triangles += (n.geometry.index?.count || n.geometry.attributes.position.count) / 3;
            if (!n.geometry.attributes.normal) throw new Error(`Missing normals: ${entry.id}`);
        }
    });
    const p = entry.presentation;
    const normalized = new THREE.Group(); normalized.add(scene); normalized.scale.setScalar(1 / p.reference_size);
    const pose = new THREE.Group(); pose.add(normalized);
    pose.rotation.set(...['pitch', 'yaw', 'roll'].map(k => THREE.MathUtils.degToRad(p[k] || 0)));
    pose.updateMatrixWorld(true);
    const extent = new THREE.Box3().setFromObject(pose, true).getSize(new THREE.Vector3());
    const overallRatio = Math.max(extent.x, extent.y);
    const passesOverallExtentRule = overallRatio >= .6 && overallRatio <= 1.3;
    const budget = bytes.length < 3000000 && triangles <= 60000;
    const result = { id: entry.id, registered: !!registered, bytes: bytes.length, sha256, points, triangles,
        nativeExtent: nativeExtent.toArray(), referenceSize: p.reference_size,
        normalizedRestExtent: extent.toArray(), passesOverallExtentRule,
        nativeVerticalExtentPerValue: nativeExtent.y / p.reference_size,
        fitsDeclaredLayoutWidth: extent.x <= p.layout_width_factor,
        pass: budget && (!registered || passesOverallExtentRule) && extent.x <= p.layout_width_factor };
    results.push(result); console.log(JSON.stringify(result));
}
fs.writeFileSync(new URL('handoff/retry3d/loader-audit.json', root), JSON.stringify({
    method: 'Actual vendored GLTFLoader; exact vertex bounds. Registered map must pass 0.6–1.3x; terrain candidates explicitly remain unregistered with overall extent failures reported. No WebGL/picking/LOD/mobile certification.',
    models: results,
}, null, 2) + '\n');
if (results.length !== 3 || results.some(r => !r.pass)) process.exitCode = 1;
