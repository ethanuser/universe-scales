#!/usr/bin/env node
// Production vendored GLTFLoader, physical units and precise per-vertex bounds.
// Browser-free; no claim about WebGL appearance, perspective, or explorer UI.
import fs from 'node:fs';
import crypto from 'node:crypto';
import * as THREE from '../js/vendor/three/three.module.min.js';

const root = new URL('../', import.meta.url);
const threeURL = new URL('../js/vendor/three/three.module.min.js', import.meta.url).href;
const asModule = source => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const utils = asModule(fs.readFileSync(new URL('js/vendor/three/addons/utils/BufferGeometryUtils.js',root),'utf8')
    .replace("from 'three'", `from '${threeURL}'`));
const loaderURL = asModule(fs.readFileSync(new URL('js/vendor/three/addons/loaders/GLTFLoader.js',root),'utf8')
    .replace("from 'three'", `from '${threeURL}'`)
    .replace("from '../utils/BufferGeometryUtils.js'", `from '${utils}'`));
globalThis.ProgressEvent = class { constructor(type,init) { Object.assign(this,init); } };
const { GLTFLoader } = await import(loaderURL);
const registry = JSON.parse(fs.readFileSync(new URL('content/visualizations/models.json',root))).models;
const files = fs.readdirSync(new URL('handoff/deepsky3d/',root)).filter(p=>p.endsWith('.entry.json')).sort();
const models = [];
for (const file of files) {
    const entry = JSON.parse(fs.readFileSync(new URL(`handoff/deepsky3d/${file}`,root)));
    const registered = registry.find(m=>m.id===entry.id);
    const bytes = fs.readFileSync(new URL(entry.src,root));
    const hash = crypto.createHash('sha256').update(bytes).digest('hex');
    if (!registered || hash!==entry.sha256 || hash!==registered.sha256) throw new Error(`Hash/registration mismatch: ${entry.id}`);
    const scene = (await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'')).scene;
    const raw = new THREE.Box3().setFromObject(scene,true);
    scene.position.sub(raw.getCenter(new THREE.Vector3()));
    const scale = new THREE.Group(); scale.add(scene); scale.scale.setScalar(1/entry.presentation.reference_size);
    const pose = new THREE.Group(); pose.add(scale);
    pose.rotation.set(...['pitch','yaw','roll'].map(k=>THREE.MathUtils.degToRad(entry.presentation[k]||0)));
    pose.updateMatrixWorld(true);
    const extent = new THREE.Box3().setFromObject(pose,true).getSize(new THREE.Vector3());
    let points=0, triangles=0, lines=0, draws=0;
    scene.traverse(n=>{
        if (n.isMesh || n.isPoints || n.isLine) draws++;
        if (n.isPoints) points+=n.geometry.attributes.position.count;
        if (n.isMesh) triangles+=(n.geometry.index?.count||n.geometry.attributes.position.count)/3;
        if (n.isLine) lines+=(n.geometry.index?.count||n.geometry.attributes.position.count)/2;
    });
    const ratio = Math.max(extent.x,extent.y);
    const pass = ratio>=.6 && ratio<=1.3 && extent.x<=entry.presentation.layout_width_factor &&
        points===entry.derived_statistics.records && triangles===0 && lines===0 && draws===1;
    const result = {id:entry.id,bytes:bytes.length,points,triangles,lines,draws,
        nativeExtent:raw.getSize(new THREE.Vector3()).toArray(),normalizedRestExtent:extent.toArray(),ratio,pass};
    models.push(result); console.log(JSON.stringify(result));
}
fs.writeFileSync(new URL('handoff/deepsky3d/loader-audit.json',root),JSON.stringify({
    method:'Actual vendored GLTFLoader; precise point coordinates and physical rest normalization. No WebGL, perspective, actual explorer or mobile certification.',models
},null,2)+'\n');
if (models.some(m=>!m.pass)) process.exitCode=1;
