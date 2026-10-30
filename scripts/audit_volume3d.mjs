#!/usr/bin/env node
// Production GLTFLoader and CPU geometry checks; no browser/WebGL certification.
// node scripts/audit_volume3d.mjs [OUTPUT_JSON]
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { readScene, measureVolume } from './mesh_volume.mjs';
import * as THREE from '../js/vendor/three/three.module.min.js';

const root = new URL('../', import.meta.url);
const registry = JSON.parse(fs.readFileSync(new URL('content/visualizations/models.json', root))).models;
const entries = fs.readdirSync(new URL('handoff/volume3d', root))
    .filter(f => f.endsWith('.entry.json')).sort()
    .map(f => JSON.parse(fs.readFileSync(new URL(`handoff/volume3d/${f}`, root))));
const results = [];
for (const entry of entries) {
    const registered = registry.find(m => m.id === entry.id);
    if (JSON.stringify(registered) !== JSON.stringify(entry)) throw new Error(`Handoff mismatch: ${entry.id}`);
    const file = new URL(entry.src, root), bytes = fs.readFileSync(file);
    if (createHash('sha256').update(bytes).digest('hex') !== entry.sha256)
        throw new Error(`Hash mismatch: ${entry.id}`);
    const scene = await readScene(file), p = entry.presentation;
    const raw = new THREE.Box3().setFromObject(scene, true);
    const extent = raw.getSize(new THREE.Vector3());
    scene.position.sub(raw.getCenter(new THREE.Vector3()));
    const normalized = new THREE.Group(); normalized.add(scene);
    normalized.scale.setScalar(1 / p.reference_size);
    normalized.updateMatrixWorld(true);
    const measured = entry.closed_volume_checked ? measureVolume(normalized) : null;
    const normalizedLongestSpan = Math.max(...extent.toArray()) / p.reference_size;
    const posed = new THREE.Group(); posed.add(normalized);
    posed.rotation.set(...['pitch', 'yaw', 'roll'].map(k => THREE.MathUtils.degToRad(p[k] || 0)));
    posed.updateMatrixWorld(true);
    const resting = new THREE.Box3().setFromObject(posed, true).getSize(new THREE.Vector3());
    const restingExtent = Math.max(resting.x, resting.y);
    let triangles = 0, flatShadedMeshes = 0;
    scene.traverse(n => {
        if (!n.isMesh) return;
        triangles += (n.geometry.index?.count || n.geometry.attributes.position.count) / 3;
        if (!n.geometry.attributes.normal) {
            const materials = Array.isArray(n.material) ? n.material : [n.material];
            if (materials.some(m => !m.flatShading)) throw new Error(`Missing normal fallback: ${entry.id}`);
            flatShadedMeshes++;
        }
    });
    const pass = bytes.length < 3000000
        && restingExtent >= .6 && restingExtent <= 1.3
        && resting.x <= p.layout_width_factor
        && (measured ? Math.abs(measured.volume - 1) < 1e-5 : Math.abs(normalizedLongestSpan - 1) < 1e-7);
    const result = { id: entry.id, names: entry.matches.volume, bytes: bytes.length, triangles,
        rawExtent: extent.toArray(), normalizedLongestSpan, restingExtent,
        normalizedEnclosedVolume: measured?.volume ?? null,
        semantics: entry.volume_semantics, flatShadedMeshes, pass };
    results.push(result); console.log(JSON.stringify(result));
}
const report = { method: 'Vendored production GLTFLoader with placeholder image decoding, exact per-vertex bounds and registry rest pose. Closed exterior volume checked only for the sugar scan. Equivalent-span proxies checked by longest source span, never treated as enclosed-volume measurements. CPU geometry only; no WebGL, perspective, explorer or mobile review.', models: results };
fs.writeFileSync(process.argv[2] || new URL('handoff/volume3d/loader-audit.json', root), JSON.stringify(report, null, 2) + '\n');
if (results.length !== 4 || results.some(r => !r.pass)) process.exitCode = 1;
