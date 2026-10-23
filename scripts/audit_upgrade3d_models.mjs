#!/usr/bin/env node
// Actual production loader + precise orthographic bounds. No WebGL certification.
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
// Geometry-only audit: texture pixels are reviewed separately in CPU previews.
globalThis.createImageBitmap = async () => ({ width: 1, height: 1, close() {} });
globalThis.ProgressEvent = class { constructor(type, init) { Object.assign(this, init); } };
const { GLTFLoader } = await import(loaderURL);
const registry = JSON.parse(fs.readFileSync(new URL('content/visualizations/models.json', root))).models;
const files = fs.readdirSync(new URL('handoff/upgrade3d', root)).filter(p => p.endsWith('.entry.json')).sort();
const results = [];
for (const file of files) {
    const entry = JSON.parse(fs.readFileSync(new URL(`handoff/upgrade3d/${file}`, root)));
    const registered = registry.find(m => m.id === entry.id);
    const bytes = fs.readFileSync(new URL(entry.src, root));
    const sha = createHash('sha256').update(bytes).digest('hex');
    if (!registered || registered.sha256 !== sha || entry.sha256 !== sha)
        throw new Error(`Registry/handoff/file mismatch: ${entry.id}`);
    const scene = (await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '')).scene;
    const p = entry.presentation;
    scene.rotation.set(...['x', 'y', 'z'].map(k => THREE.MathUtils.degToRad(p.pre_rotation?.[k] || 0)));
    scene.updateMatrixWorld(true);
    const raw = new THREE.Box3().setFromObject(scene, true);
    const nativeExtent = raw.getSize(new THREE.Vector3());
    const reference = p.reference_size || (p.measure_axis ? nativeExtent[p.measure_axis] : Math.max(...nativeExtent.toArray()));
    scene.position.sub(raw.getCenter(new THREE.Vector3()));
    const scale = new THREE.Group(); scale.add(scene); scale.scale.setScalar(1 / (reference * (p.measure_fraction || 1)));
    const pose = new THREE.Group(); pose.add(scale);
    pose.rotation.set(...['pitch', 'yaw', 'roll'].map(k => THREE.MathUtils.degToRad(p[k] || 0)));
    pose.updateMatrixWorld(true);
    const extent = new THREE.Box3().setFromObject(pose, true).getSize(new THREE.Vector3());
    let triangles = 0, meshes = 0;
    scene.traverse(n => {
        if (!n.isMesh) return;
        meshes++;
        triangles += (n.geometry.index?.count || n.geometry.attributes.position.count) / 3;
        if (!n.geometry.attributes.normal) throw new Error(`Missing normals: ${entry.id}`);
    });
    const displayedExtentPerValue = Math.max(extent.x, extent.y);
    const pass = displayedExtentPerValue >= .6 && displayedExtentPerValue <= 1.3
        && extent.x <= (p.layout_width_factor || 1) && bytes.length < 3000000;
    const result = { id: entry.id, bytes: bytes.length, sha256: sha, triangles, meshes,
        nativeExtent: nativeExtent.toArray(), calibrationReference: reference,
        normalizedRestExtent: extent.toArray(), displayedExtentPerValue, pass };
    results.push(result); console.log(JSON.stringify(result));
}
fs.writeFileSync(new URL('handoff/upgrade3d/loader-audit.json', root), JSON.stringify({
    method: 'Vendored production GLTFLoader, placeholder image decoding, exact per-vertex bounds with registry pre-rotation/calibration/rest pose. No WebGL, transparency, perspective, explorer or mobile verification.',
    models: results,
}, null, 2) + '\n');
if (!results.length || results.some(r => !r.pass)) process.exitCode = 1;
