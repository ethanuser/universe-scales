import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from '../js/vendor/three/three.module.min.js';
import { angularModelEntries, angularScene, angularEntry } from '../js/experiences/angular-models.js';
import { createAngularRig } from '../js/experiences/angular-rig.js';

test('axial presentation keeps spindles camera-parallel and primary rotation clockwise', () => {
    for (const entry of Object.values(angularModelEntries)) {
        const root = new THREE.Group(); root.add(angularScene(entry.angular_kind));
        const pose = entry.presentation;
        root.rotation.set(THREE.MathUtils.degToRad(pose.pitch || 0), THREE.MathUtils.degToRad(pose.yaw || 0), 0);
        const rig = createAngularRig(root, entry.angular_motion);
        rig.faceCamera();
        const housing = root.getObjectByName('Housing');
        const fixed = housing.matrixWorld.clone();
        for (const phase of [0, 0.3, Math.PI / 2, 5]) {
            rig.setPhase(phase); root.updateMatrixWorld(true);
            assert.ok(housing.matrixWorld.equals(fixed), entry.id);
            for (const rotation of rig.rotations) {
                const axis = rotation.axis.clone().transformDirection(rotation.node.matrixWorld);
                assert.ok(Math.hypot(axis.x, axis.y) < 1e-10, entry.id);
                if (rotation === rig.rotations[0]) assert.ok(axis.z * rotation.ratio < 0, `${entry.id}: clockwise screen rotation`);
            }
        }
    }
});

test('every procedural angular observation has a valid moving assembly and a fixed housing', () => {
    const corpus = JSON.parse(fs.readFileSync(new URL('../dataset/raw/curated/angular-velocity.json', import.meta.url), 'utf8'));
    for (const [name, entry] of Object.entries(angularModelEntries)) {
        assert.ok(corpus.some(item => item.canonical_name === name), `${name} matches the source dataset or a retained alias`);
        assert.ok(entry.source.startsWith('https://'));
        const scene = angularScene(entry.angular_kind);
        const rig = createAngularRig(scene, entry.angular_motion);
        const housing = scene.getObjectByName('Housing');
        assert.ok(housing, name);
        scene.updateMatrixWorld(true);
        const original = housing.matrixWorld.clone();
        const before = rig.rotations.map(rotation => rotation.node.quaternion.clone());
        rig.setPhase(Math.PI / 2); scene.updateMatrixWorld(true);
        assert.ok(housing.matrixWorld.equals(original), `${name}: housing stays fixed`);
        rig.rotations.forEach((rotation, index) =>
            assert.ok(Math.abs(rotation.node.quaternion.angleTo(before[index]) - Math.PI / 2) < 1e-7,
                `${name}: quarter turn at the observation's phase`));
    }
});

test('downloaded fan targets only its blades and planet rigs are angular-only overlays', () => {
    const registry = JSON.parse(fs.readFileSync(new URL('../content/visualizations/models.json', import.meta.url)));
    const before = JSON.stringify(registry);
    const fan = angularEntry({ name: 'Ceiling fan' }, registry.models);
    assert.deepEqual(fan.angular_motion.rotations, [{ node: 'ceiling_fan_blades', axis: [0, 1, 0] }]);
    for (const name of ['Earth rotation', 'Jupiter rotation']) {
        assert.equal(angularEntry({ name }, registry.models).angular_motion.rotations[0].node, '$model');
    }
    assert.equal(JSON.stringify(registry), before, 'Length/Area/Volume registry is unchanged');
    assert.equal(angularEntry({ name: 'Unknown' }, registry.models), null);
});

test('Sketchfab drone rotates its bell and blades while stator and coils remain outside that subtree', () => {
    const registry = JSON.parse(fs.readFileSync(new URL('../content/visualizations/models.json', import.meta.url)));
    const entry = angularEntry({ name: 'Drone propeller' }, registry.models);
    assert.equal(entry.license, 'CC-BY-4.0');
    assert.deepEqual(entry.angular_motion.rotations, [{ node: 'motor_rotor', axis: [0, 0, 1] }]);
    const bytes = fs.readFileSync(new URL(`../${entry.src}`, import.meta.url));
    const gltf = JSON.parse(bytes.subarray(20, 20 + bytes.readUInt32LE(12)));
    const index = gltf.nodes.findIndex(node => node.name === 'motor_rotor');
    const descendants = current => [current, ...(gltf.nodes[current].children || []).flatMap(descendants)];
    const moving = descendants(index).map(i => gltf.nodes[i].name);
    assert.ok(moving.includes('blades'));
    assert.ok(!moving.includes('motor_stator') && !moving.includes('motor_coils'));
    assert.ok(entry.bytes < 500000 && entry.triangle_count < 10000);
});

test('new sourced angular assets bind real components without spinning unrelated geometry', () => {
    const registry = JSON.parse(fs.readFileSync(new URL('../content/visualizations/models.json', import.meta.url)));
    for (const name of ['Car engine', 'Saturn rotation']) {
        const entry = angularEntry({ name }, registry.models);
        const bytes = fs.readFileSync(new URL(`../${entry.src}`, import.meta.url));
        const gltf = JSON.parse(bytes.subarray(20, 20 + bytes.readUInt32LE(12)));
        const rotation = entry.angular_motion.rotations[0];
        const rotor = gltf.nodes.find(node => THREE.PropertyBinding.sanitizeNodeName(node.name) === rotation.node);
        assert.ok(rotor, `${name}: binding survives loader name sanitization`);
        assert.ok(entry.bytes < 1500000);
        if (name === 'Car engine') {
            assert.ok(!gltf.nodes.some(node => /Piston|Connecting Rod/.test(node.name)), 'no disconnected stationary pistons');
        } else {
            assert.deepEqual(rotation.axis, [0, 1, 0]);
            assert.equal(entry.angular_motion.view_side, 'negative');
            for (const ring of ['RingsTop', 'RingsBottom']) {
                assert.ok(gltf.nodes.some(node => node.name === ring));
                assert.ok(!(rotor.children || []).includes(gltf.nodes.findIndex(node => node.name === ring)));
            }
        }
    }
});

test('downloaded bicycle replaces the fallback and rotates wheels separately from its frame', () => {
    const registry = JSON.parse(fs.readFileSync(new URL('../content/visualizations/models.json', import.meta.url)));
    const entry = angularEntry({name: 'Bicycle wheel at 20 km/h'}, registry.models);
    assert.equal(entry.id, 'innerscene-city-bicycle-angular');
    assert.equal(entry.license, 'CC0-1.0');
    assert.ok(entry.bytes < 500000 && entry.triangle_count < 15000);
    const bytes = fs.readFileSync(new URL(`../${entry.src}`, import.meta.url));
    const gltf = JSON.parse(bytes.subarray(20, 20 + bytes.readUInt32LE(12)));
    const housing = gltf.nodes.find(node => node.name === 'Housing');
    const fixedNames = housing.children.map(index => gltf.nodes[index].name);
    assert.ok(fixedNames.includes('Fork') && fixedNames.includes('Chain') && fixedNames.includes('Pedal'));
    for (const side of ['Front', 'Rear']) {
        const rotor = gltf.nodes.find(node => node.name === `${side}WheelRotor`);
        assert.deepEqual(entry.angular_motion.rotations.find(rotation => rotation.node === rotor.name).axis, [1,0,0]);
        assert.equal(rotor.children.length, 31);
        const hub = rotor.children.map(index => gltf.nodes[index]).find(node => node.name === `${side} hub`);
        assert.deepEqual(hub.translation, [0,0,0]);
        assert.ok(rotor.children.every(index => !housing.children.includes(index)));
    }
});
