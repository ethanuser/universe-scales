import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';
import * as THREE from '../js/vendor/three/three.module.min.js';
import { measureVolume, readScene } from '../scripts/mesh_volume.mjs';

// Test-only solids; production assets are imported, never synthesized here.
const box = () => new THREE.Mesh(new THREE.BoxGeometry(2, 3, 4));
test('measures enclosed volume, not the cube of the longest extent', () => {
    const result = measureVolume(box());
    assert.equal(result.volume, 24);
    assert.equal(result.referenceSize, Math.cbrt(24));
    assert.equal(result.weldedVertices, 8);
});
test('includes nested transforms, reflection and translation without changing geometry', () => {
    const parent = new THREE.Group(), mesh = box();
    parent.add(mesh); parent.scale.set(-2, 3, 4); parent.rotation.set(.5, .4, .3);
    parent.position.set(10000, -10000, 20000);
    const before = Array.from(mesh.geometry.attributes.position.array);
    assert.ok(Math.abs(measureVolume(parent).volume - 576) < 1e-8);
    assert.deepEqual(Array.from(mesh.geometry.attributes.position.array), before);
});
test('rejects open surfaces, duplicate faces and disjoint shells', () => {
    const open = box(); open.geometry.setIndex(Array.from(open.geometry.index.array).slice(3));
    assert.throws(() => measureVolume(open), /open or nonmanifold/);
    const duplicate = box(); duplicate.geometry.setIndex([...duplicate.geometry.index.array, ...duplicate.geometry.index.array.slice(0, 3)]);
    assert.throws(() => measureVolume(duplicate), /Duplicate/);
    const group = new THREE.Group(), first = box(), second = box(); second.position.x = 10; group.add(first, second);
    assert.throws(() => measureVolume(group), /Multiple shells/);
});
test('rejects inverted individual faces and morphing surfaces', () => {
    const wrong = box(), indices = Array.from(wrong.geometry.index.array);
    [indices[0], indices[1]] = [indices[1], indices[0]]; wrong.geometry.setIndex(indices);
    assert.throws(() => measureVolume(wrong), /winding/);
    const morph = box(); morph.geometry.morphAttributes.position = [morph.geometry.attributes.position.clone()];
    assert.throws(() => measureVolume(morph), /Deformable/);
});
test('Sand Atlas and educational RBC retain closed single-shell source geometry', async () => {
    for (const name of ['sand-atlas-caicos-ooid-80', 'sketchfab-red-blood-cell']) {
        const scene = await readScene(new URL(`../content/visualizations/models/${name}.glb`, import.meta.url));
        const result = measureVolume(scene);
        assert.ok(result.volume > 0);
        assert.equal(result.components, 1);
        scene.scale.setScalar(1 / result.referenceSize);
        assert.ok(Math.abs(measureVolume(scene).volume - 1) < 1e-6);
    }
});
test('Volume entries share source files but leave Length calibration independent', async () => {
    const entries = JSON.parse(fs.readFileSync(new URL('../content/visualizations/models.json', import.meta.url))).models;
    for (const [id, sourceId, item] of [
        ['volume-sand-atlas-ooid', 'sand-atlas-caicos-ooid-80', 'Grain of sand volume'],
        ['volume-educational-rbc', 'sketchfab-red-blood-cell', 'Red blood cell volume'],
    ]) {
        const entry = entries.find(m => m.id === id), source = entries.find(m => m.id === sourceId);
        assert.equal(entry.src, source.src);
        assert.equal(entry.sha256, source.sha256);
        assert.deepEqual(entry.matches, { volume: [item] });
        assert.equal(source.presentation?.reference_size, undefined);
        const scene = await readScene(new URL('../' + entry.src, import.meta.url));
        const r = entry.presentation.pre_rotation || {};
        scene.rotation.set(...['x', 'y', 'z'].map(k => THREE.MathUtils.degToRad(r[k] || 0)));
        scene.scale.setScalar(1 / entry.presentation.reference_size);
        const result = measureVolume(scene);
        assert.ok(Math.abs(result.volume - 1) < 1e-6);
        assert.ok(Math.max(...result.extent) < entry.presentation.display_extent_factor);
        assert.equal(entry.closed_volume_checked, true);
        assert.equal(entry.processing.volume_calibration.selfIntersectionChecked, false);
    }
    const jupiter = entries.find(m => m.id === 'nasa-jupiter');
    assert.ok(jupiter.matches.volume.includes('Jupiter volume'));
    assert.equal(jupiter.volume_semantics, 'analytic_sphere');
});
