#!/usr/bin/env node
// Vendored-loader and physical-calibration check; no WebGL or UI verification.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as THREE from '../js/vendor/three/three.module.min.js';

const root = fileURLToPath(new URL('../', import.meta.url));
const destination = path.resolve(process.argv[2] || path.join(root, 'handoff/bio3d/loader-audit.json'));
const threeURL = new URL('../js/vendor/three/three.module.min.js', import.meta.url).href;
const moduleURL = source => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const utilities = moduleURL(fs.readFileSync(new URL('../js/vendor/three/addons/utils/BufferGeometryUtils.js', import.meta.url), 'utf8')
    .replace("from 'three'", `from '${threeURL}'`));
const loaderURL = moduleURL(fs.readFileSync(new URL('../js/vendor/three/addons/loaders/GLTFLoader.js', import.meta.url), 'utf8')
    .replace("from 'three'", `from '${threeURL}'`)
    .replace("from '../utils/BufferGeometryUtils.js'", `from '${utilities}'`));
const { GLTFLoader } = await import(loaderURL);
const registry = JSON.parse(fs.readFileSync(path.join(root, 'content/visualizations/models.json'))).models;
const entries = fs.readdirSync(path.join(root, 'handoff/bio3d')).filter(p => p.endsWith('.entry.json'))
    .map(p => JSON.parse(fs.readFileSync(path.join(root, 'handoff/bio3d', p))));
const results = [];
for (const entry of entries) {
    const registered = registry.find(m => m.id === entry.id);
    if (!registered || registered.sha256 !== entry.sha256) throw new Error(`Registry mismatch: ${entry.id}`);
    const bytes = fs.readFileSync(path.join(root, entry.src));
    const scene = (await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset+bytes.byteLength), '')).scene;
    const pose = entry.presentation;
    const raw = new THREE.Box3().setFromObject(scene, true);
    const physicalExtentNm = raw.getSize(new THREE.Vector3()).toArray();
    scene.position.sub(raw.getCenter(new THREE.Vector3()));
    const scaled = new THREE.Group(); scaled.add(scene); scaled.scale.setScalar(1/pose.reference_size);
    const group = new THREE.Group(); group.add(scaled);
    group.rotation.set(...['pitch', 'yaw', 'roll'].map(key => THREE.MathUtils.degToRad(pose[key] || 0)));
    group.updateMatrixWorld(true);
    const extent = new THREE.Box3().setFromObject(group, true).getSize(new THREE.Vector3());
    const displayedExtentPerValue = Math.max(extent.x, extent.y);
    const widthFactor = pose.layout_width_factor || 1;
    let meshes = 0, triangles = 0;
    scene.traverse(node => {
        if (node.isMesh) {
            meshes++;
            triangles += (node.geometry.index?.count || node.geometry.attributes.position.count)/3;
            if (!node.geometry.attributes.normal) throw new Error(`Missing normals: ${entry.id}`);
        }
    });
    const pass = displayedExtentPerValue >= .6 && displayedExtentPerValue <= 1.3 && extent.x <= widthFactor;
    const result = { id: entry.id, physicalExtentNm, normalizedRestExtent: extent.toArray(),
        displayedExtentPerValue, widthFactor, meshes, triangles, pass };
    results.push(result); console.log(JSON.stringify(result));
}
fs.mkdirSync(path.dirname(destination), { recursive: true });
fs.writeFileSync(destination, JSON.stringify({
    method: 'Production vendored GLTFLoader; native coordinates; orthographic geometry extent; no browser, perspective, lighting or UI verification',
    models: results
}, null, 2)+'\n');
if (results.some(r => !r.pass)) process.exitCode = 1;
