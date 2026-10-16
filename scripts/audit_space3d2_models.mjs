#!/usr/bin/env node
// Actual vendored GLTFLoader + orthographic geometry check. No WebGL/browser.
import fs from 'node:fs';
import * as THREE from '../js/vendor/three/three.module.min.js';

const root = new URL('../', import.meta.url);
const threeURL = new URL('../js/vendor/three/three.module.min.js', import.meta.url).href;
const moduleURL = s => `data:text/javascript;base64,${Buffer.from(s).toString('base64')}`;
const utilities = moduleURL(fs.readFileSync(new URL('js/vendor/three/addons/utils/BufferGeometryUtils.js', root), 'utf8')
    .replace("from 'three'", `from '${threeURL}'`));
const loaderURL = moduleURL(fs.readFileSync(new URL('js/vendor/three/addons/loaders/GLTFLoader.js', root), 'utf8')
    .replace("from 'three'", `from '${threeURL}'`)
    .replace("from '../utils/BufferGeometryUtils.js'", `from '${utilities}'`));
// Image pixels are not decoded here: only geometry and hierarchy are tested.
globalThis.self = globalThis;
globalThis.createImageBitmap = async () => ({ width: 1, height: 1, close() {} });
globalThis.ProgressEvent = class { constructor(type, init) { Object.assign(this, init); } };
const { GLTFLoader } = await import(loaderURL);
const registry = JSON.parse(fs.readFileSync(new URL('content/visualizations/models.json', root))).models;
const files = fs.readdirSync(new URL('handoff/space3d2', root)).filter(p => p.endsWith('.entry.json')).sort();
const results = [];
for (const file of files) {
    const entry = JSON.parse(fs.readFileSync(new URL(`handoff/space3d2/${file}`, root)));
    const registered = registry.find(m => m.id === entry.id);
    if ((!registered || registered.sha256 !== entry.sha256) && entry.id !== 'cassini-hyperion-shape') {
        throw new Error(`Entry/registry mismatch: ${entry.id}`);
    }
    const bytes = fs.readFileSync(new URL(entry.src, root));
    const scene = (await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset+bytes.byteLength), '')).scene;
    const raw = new THREE.Box3().setFromObject(scene, true);
    const nativeExtent = raw.getSize(new THREE.Vector3()).toArray();
    scene.position.sub(raw.getCenter(new THREE.Vector3()));
    const scale = new THREE.Group(); scale.add(scene); scale.scale.setScalar(1/entry.presentation.reference_size);
    const pose = new THREE.Group(); pose.add(scale);
    pose.rotation.set(...['pitch', 'yaw', 'roll'].map(k => THREE.MathUtils.degToRad(entry.presentation[k] || 0)));
    pose.updateMatrixWorld(true);
    const extent = new THREE.Box3().setFromObject(pose, true).getSize(new THREE.Vector3());
    const displayedExtentPerValue = Math.max(extent.x, extent.y);
    let triangles = 0, points = 0, lines = 0;
    scene.traverse(n => {
        if (n.isMesh) triangles += (n.geometry.index?.count || n.geometry.attributes.position.count)/3;
        if (n.isPoints) points += n.geometry.attributes.position.count;
        if (n.isLineSegments) lines += n.geometry.attributes.position.count/2;
    });
    const pass = displayedExtentPerValue >= .6 && displayedExtentPerValue <= 1.3 && extent.x <= (entry.presentation.layout_width_factor || 1)+1e-7;
    const result = { id: entry.id, registered: !!registered, nativeExtent, normalizedRestExtent: extent.toArray(),
        displayedExtentPerValue, triangles, points, lines, pass };
    results.push(result); console.log(JSON.stringify(result));
}
fs.writeFileSync(new URL('handoff/space3d2/loader-audit.json', root), JSON.stringify({
    method: 'Vendored production GLTFLoader, with placeholder image decoding; native geometry + orthographic rest bounds. No WebGL, texture appearance, perspective, actual explorer or mobile certification.',
    models: results
}, null, 2)+'\n');
if (results.some(r => !r.pass)) process.exitCode = 1;
