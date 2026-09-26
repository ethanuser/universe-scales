#!/usr/bin/env node
// Report scene-space bounds and draw-call count before approving a model for the explorer.
import { readFileSync } from 'node:fs';
import * as THREE from '../js/vendor/three/three.module.min.js';

const path = process.argv[2];
if (!path) throw new Error('Usage: node scripts/audit_glb_geometry.mjs MODEL.glb');
const excluded = new Set(process.argv.slice(3));
const bytes = readFileSync(path);
if (bytes.toString('ascii', 0, 4) !== 'glTF') throw new Error('Not a GLB file');
const jsonLength = bytes.readUInt32LE(12);
const gltf = JSON.parse(bytes.subarray(20, 20 + jsonLength).toString());
const nodes = gltf.nodes || [];
const bounds = new THREE.Box3();
let primitives = 0;

function visit(index, parent) {
    const node = nodes[index];
    if (excluded.has(node.name)) return;
    const local = node.matrix
        ? new THREE.Matrix4().fromArray(node.matrix)
        : new THREE.Matrix4().compose(
            new THREE.Vector3().fromArray(node.translation || [0, 0, 0]),
            new THREE.Quaternion().fromArray(node.rotation || [0, 0, 0, 1]),
            new THREE.Vector3().fromArray(node.scale || [1, 1, 1])
        );
    const world = parent.clone().multiply(local);
    if (node.mesh != null) {
        for (const primitive of gltf.meshes[node.mesh].primitives) {
            const accessor = gltf.accessors[primitive.attributes.POSITION];
            if (!accessor.min || !accessor.max) throw new Error('POSITION accessor lacks bounds');
            const box = new THREE.Box3(
                new THREE.Vector3().fromArray(accessor.min),
                new THREE.Vector3().fromArray(accessor.max)
            );
            box.applyMatrix4(world);
            bounds.union(box);
            primitives++;
        }
    }
    for (const child of node.children || []) visit(child, world);
}

for (const index of gltf.scenes[gltf.scene || 0].nodes) visit(index, new THREE.Matrix4());
const size = bounds.getSize(new THREE.Vector3());
console.log(JSON.stringify({ path, bytes: bytes.length, nodes: nodes.length,
    meshes: gltf.meshes?.length || 0, primitives,
    min: bounds.min.toArray(), max: bounds.max.toArray(), size: size.toArray() }, null, 2));
