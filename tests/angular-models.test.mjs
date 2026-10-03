import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { angularModelEntries, angularScene, angularEntry } from '../js/experiences/angular-models.js';
import { createAngularRig } from '../js/experiences/angular-rig.js';

test('every procedural angular observation has a valid moving assembly and a fixed housing', () => {
    const corpus = fs.readFileSync(new URL('../data/angular-velocity.yaml', import.meta.url), 'utf8');
    for (const [name, entry] of Object.entries(angularModelEntries)) {
        assert.ok(corpus.includes(`  name: ${name}\n`), `${name} matches the dataset`);
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
