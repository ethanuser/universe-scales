#!/usr/bin/env node
// Actual vendored GLTFLoader; browser-free geometry check, not model_lab approval.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as THREE from '../js/vendor/three/three.module.min.js';
const root = fileURLToPath(new URL('../', import.meta.url));
const handoff = path.join(root, 'handoff/bio3d2');
const threeURL = new URL('../js/vendor/three/three.module.min.js', import.meta.url).href;
const asModule = s => `data:text/javascript;base64,${Buffer.from(s).toString('base64')}`;
const utilities = asModule(fs.readFileSync(new URL('../js/vendor/three/addons/utils/BufferGeometryUtils.js', import.meta.url), 'utf8')
    .replace("from 'three'", `from '${threeURL}'`));
const loader = asModule(fs.readFileSync(new URL('../js/vendor/three/addons/loaders/GLTFLoader.js', import.meta.url), 'utf8')
    .replace("from 'three'", `from '${threeURL}'`)
    .replace("from '../utils/BufferGeometryUtils.js'", `from '${utilities}'`));
const { GLTFLoader } = await import(loader);
const registry = JSON.parse(fs.readFileSync(path.join(root, 'content/visualizations/models.json'))).models;
const results = [];
for (const name of fs.readdirSync(handoff).filter(p => p.endsWith('.entry.json'))) {
    const entry = JSON.parse(fs.readFileSync(path.join(handoff, name)));
    if (registry.find(e => e.id === entry.id)?.sha256 !== entry.sha256) throw new Error('Stale registry entry');
    const bytes = fs.readFileSync(path.join(root, entry.src));
    // Material-free copy prevents DOM-dependent image loading. Binary geometry,
    // transforms and accessors are unchanged; material checks use glTF Validator.
    const jsonSize = bytes.readUInt32LE(12);
    const doc = JSON.parse(bytes.subarray(20, 20+jsonSize).toString());
    delete doc.images; delete doc.textures; delete doc.samplers; delete doc.materials;
    for (const mesh of doc.meshes) for (const p of mesh.primitives) delete p.material;
    const json = Buffer.from(JSON.stringify(doc));
    const padded = Buffer.concat([json, Buffer.alloc((4-json.length%4)%4, 32)]);
    const bin = bytes.subarray(28+jsonSize);
    const packed = Buffer.alloc(28+padded.length+bin.length);
    packed.write('glTF'); packed.writeUInt32LE(2, 4); packed.writeUInt32LE(packed.length, 8);
    packed.writeUInt32LE(padded.length, 12); packed.write('JSON', 16); padded.copy(packed, 20);
    packed.writeUInt32LE(bin.length, 20+padded.length); packed.write('BIN\0', 24+padded.length);
    bin.copy(packed, 28+padded.length);
    const scene = (await new GLTFLoader().parseAsync(packed.buffer.slice(packed.byteOffset,
        packed.byteOffset+packed.byteLength), '')).scene;
    const pose = entry.presentation;
    const raw = new THREE.Box3().setFromObject(scene, true);
    const size = raw.getSize(new THREE.Vector3());
    const reference = pose.reference_size ?? (pose.measure_axis ? size[pose.measure_axis] : Math.max(...size.toArray()));
    scene.position.sub(raw.getCenter(new THREE.Vector3()));
    const scaled = new THREE.Group(); scaled.add(scene); scaled.scale.setScalar(1/(reference*(pose.measure_fraction || 1)));
    const group = new THREE.Group(); group.add(scaled);
    group.rotation.set(...['pitch', 'yaw', 'roll'].map(k => THREE.MathUtils.degToRad(pose[k] || 0)));
    group.updateMatrixWorld(true);
    const extent = new THREE.Box3().setFromObject(group, true).getSize(new THREE.Vector3());
    const ratio = Math.max(extent.x, extent.y), width = pose.layout_width_factor || 1;
    const pass = ratio >= .6 && ratio <= 1.3 && extent.x <= width;
    const result = { id: entry.id, rawExtent: size.toArray(), reference, normalizedRestExtent: extent.toArray(),
        displayedExtentPerValue: ratio, layoutWidthFactor: width, pass };
    results.push(result); console.log(JSON.stringify(result));
}
fs.writeFileSync(path.join(handoff, 'loader-audit.json'), JSON.stringify({
    method: 'Vendored GLTFLoader with material-free copy; native geometry and transforms; orthographic resting extents. Not browser, perspective, textures, transparency, lighting or UI verification.',
    requiredDatasetChange: 'Tardigrade must become 152 um body length before publishing; native model reference is 152 um.',
    models: results
}, null, 2)+'\n');
if (results.some(r => !r.pass)) process.exitCode = 1;
