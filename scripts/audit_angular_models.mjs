#!/usr/bin/env node
// Browser-free geometry/rig review. Textures, lighting and UI still need model_lab.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import * as THREE from '../js/vendor/three/three.module.min.js';
import { angularEntry, angularScene } from '../js/experiences/angular-models.js';
import { createAngularRig, angularSweepBounds } from '../js/experiences/angular-rig.js';
import '../js/experiences/motion-math.js';

const root = fileURLToPath(new URL('../', import.meta.url));
const out = path.resolve(process.argv[2] || '/tmp/angular-geometry');
fs.mkdirSync(out, { recursive: true });
// Use the vendored loader, resolving the browser's import map in memory.
const threeURL = new URL('../js/vendor/three/three.module.min.js', import.meta.url).href;
const moduleURL = source => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const utilities = moduleURL(fs.readFileSync(new URL('../js/vendor/three/addons/utils/BufferGeometryUtils.js', import.meta.url), 'utf8')
    .replace("from 'three'", `from '${threeURL}'`));
const loaderURL = moduleURL(fs.readFileSync(new URL('../js/vendor/three/addons/loaders/GLTFLoader.js', import.meta.url), 'utf8')
    .replace("from 'three'", `from '${threeURL}'`)
    .replace("from '../utils/BufferGeometryUtils.js'", `from '${utilities}'`));
const { GLTFLoader } = await import(loaderURL);
const loader = new GLTFLoader();
loader.register(() => ({ name: 'geometry-review', loadTexture: () => Promise.resolve(new THREE.Texture()) }));
const registry = JSON.parse(fs.readFileSync(path.join(root, 'content/visualizations/models.json'))).models;
const items = JSON.parse(execFileSync(path.join(root, 'venv/bin/python'), ['-c',
    'import json,yaml; print(json.dumps(yaml.safe_load(open("data/angular-velocity.yaml"))["items"]))'], { cwd: root }));
const results = [];
for (const [index, item] of items.entries()) {
    const entry = angularEntry(item, registry);
    const result = { index, name: item.name, value: item.value, id: item.id,
        kind: ScaleMotionMath.visualKind('angular-velocity', item.name), model: entry?.id || null };
    if (!entry) { results.push(result); continue; }
    try {
        let scene;
        if (entry.procedural) scene = angularScene(entry.angular_kind);
        else {
            const bytes = fs.readFileSync(path.join(root, entry.src));
            scene = (await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '')).scene;
        }
        const pose = entry.presentation || {};
        for (const name of pose.remove_nodes || []) scene.getObjectByName(name)?.removeFromParent();
        if (pose.pre_rotation) scene.rotation.set(...['x', 'y', 'z'].map(axis => THREE.MathUtils.degToRad(pose.pre_rotation[axis] || 0)));
        const bounds = new THREE.Box3().setFromObject(scene, true), extent = bounds.getSize(new THREE.Vector3());
        const reference = pose.reference_size || extent[pose.measure_axis] || Math.max(...extent.toArray());
        scene.position.sub(bounds.getCenter(new THREE.Vector3()));
        const normalized = new THREE.Group(), scale = new THREE.Group();
        scale.add(scene); scale.scale.setScalar(1 / (reference * (pose.measure_fraction || 1))); normalized.add(scale);
        normalized.rotation.set(...['pitch', 'yaw', 'roll'].map(axis => THREE.MathUtils.degToRad(pose[axis] || 0)));
        const rig = createAngularRig(normalized, entry.angular_motion);
        rig.faceCamera(entry.angular_motion.view_side, entry.angular_motion.view_tilt);
        const envelope = angularSweepBounds(normalized, rig);
        result.envelope = { min: envelope.min.toArray(), max: envelope.max.toArray() };
        const moving = new Set(rig.rotations.flatMap(rotation => {
            const nodes = []; rotation.node.traverse(node => nodes.push(node)); return nodes;
        }));
        normalized.updateMatrixWorld(true);
        const stationary = [];
        normalized.traverse(node => { if (node.isMesh && !moving.has(node)) stationary.push({ node, matrix: node.matrixWorld.clone() }); });
        const pivots = rig.rotations.map(({ node }) => node.position.clone());
        result.fixed = true; result.pivotsFixed = true; result.clockwiseAxial = true; result.framed = true;
        result.samples = [];
        const union = new THREE.Box3();
        for (const phase of [0, 0.37, Math.PI / 2, Math.PI, 3 * Math.PI / 2, 2 * Math.PI]) {
            rig.setPhase(phase); normalized.updateMatrixWorld(true);
            const box = new THREE.Box3().setFromObject(normalized, true);
            union.union(box);
            result.framed &&= envelope.containsBox(box);
            result.fixed &&= stationary.every(({ node, matrix }) => node.matrixWorld.equals(matrix));
            result.pivotsFixed &&= rig.rotations.every(({ node }, i) => node.position.equals(pivots[i]));
            const axis = rig.rotations[0].axis.clone().transformDirection(rig.rotations[0].node.matrixWorld);
            result.clockwiseAxial &&= Math.abs(Math.abs(axis.z) - Math.cos(THREE.MathUtils.degToRad(entry.angular_motion.view_tilt || 0))) < 1e-6
                && axis.z * rig.rotations[0].ratio < 0;
            result.samples.push({ phase, seconds: phase / item.value, extent: box.getSize(new THREE.Vector3()).toArray() });
            if (process.argv.includes('--previews') && phase < 2 * Math.PI) {
                const parts = [];
                normalized.traverse(node => {
                    if (!node.isMesh || !node.visible) return;
                    const geo = node.geometry, positions = geo.getAttribute('position'), triangles = geo.index?.count / 3 || positions.count / 3;
                    for (let instance = 0; instance < (node.isInstancedMesh ? node.count : 1); instance++) {
                        const matrix = node.matrixWorld.clone();
                        if (node.isInstancedMesh) { const local = new THREE.Matrix4(); node.getMatrixAt(instance, local); matrix.multiply(local); }
                        const faces = [];
                        for (let face = 0; face < triangles; face++) {
                            faces.push([0, 1, 2].map(corner => new THREE.Vector3().fromBufferAttribute(positions,
                                geo.index ? geo.index.getX(face * 3 + corner) : face * 3 + corner).applyMatrix4(matrix).toArray()));
                        }
                        const material = Array.isArray(node.material) ? node.material[0] : node.material;
                        const color = (material.color || new THREE.Color(0x999999)).clone().convertLinearToSRGB().toArray();
                        parts.push([faces, color, material.transparent ? material.opacity : 1]);
                    }
                });
                const file = path.join(out, `${String(index).padStart(2, '0')}-${result.samples.length - 1}.json`);
                fs.writeFileSync(file, JSON.stringify(parts));
            }
        }
        result.sweepExtent = union.getSize(new THREE.Vector3()).toArray();
        result.realTime = ScaleMotionMath.cycleState('angular-velocity', item.value, 1, 1, entry.angular_motion?.repetitions || 1);
        const rate = 10 ** ScaleMotionMath.timeBounds('angular-velocity', item.value).fit;
        result.fitTime = ScaleMotionMath.cycleState('angular-velocity', item.value, 1, rate, entry.angular_motion?.repetitions || 1);
        console.log(`${index}: ${item.name}: fixed=${result.fixed} pivots=${result.pivotsFixed} axialCW=${result.clockwiseAxial}`);
    } catch (error) { result.error = error.message; console.error(`${item.name}: ${error.message}`); }
    results.push(result);
}
fs.writeFileSync(path.join(out, 'audit.json'), JSON.stringify({ note: 'Geometry only; no browser, textures or production UI rendering.', results }, null, 2));
if (results.some(result => result.error || (result.kind === 'spin' && !result.model) ||
    (result.model && (!result.fixed || !result.pivotsFixed || !result.clockwiseAxial || !result.framed || result.fitTime.unresolved)))) process.exitCode = 1;
