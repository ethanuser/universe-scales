import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from '../js/vendor/three/three.module.min.js';
import { createAngularRig } from '../js/experiences/angular-rig.js';

test('face-on clockwise convention preserves geared counter-rotation', () => {
    const root = new THREE.Group(), rotor = new THREE.Group(), geared = new THREE.Group();
    rotor.name = 'Rotor'; geared.name = 'Geared'; root.add(rotor, geared);
    root.rotation.x = Math.PI / 6;
    const rig = createAngularRig(root, { rotations: [
        { node: 'Rotor', axis: [0, 1, 0] }, { node: 'Geared', axis: [0, 1, 0], ratio: -0.5 }
    ] });
    rig.faceCamera();
    assert.equal(rig.rotations[1].ratio / rig.rotations[0].ratio, -0.5);
    rig.setPhase(Math.PI / 2);
    assert.ok(Math.abs(rotor.quaternion.angleTo(new THREE.Quaternion()) - Math.PI / 2) < 1e-7);
    assert.ok(Math.abs(geared.quaternion.angleTo(new THREE.Quaternion()) - Math.PI / 4) < 1e-7);
});

test('rotor turns about its own spindle without moving the fixture or accumulating phase', () => {
    const root = new THREE.Group(), fixture = new THREE.Group(), rotor = new THREE.Group();
    fixture.name = 'Housing'; rotor.name = 'Rotor';
    root.add(fixture, rotor); root.rotation.set(0.3, -0.4, 0.1);
    rotor.position.set(0.4, 0.8, -0.2);
    const tip = new THREE.Object3D(); tip.position.set(1, 0, 0); rotor.add(tip);
    const axisEnd = new THREE.Object3D(); axisEnd.position.set(0, 1, 0); rotor.add(axisEnd);
    const rig = createAngularRig(root, { rotations: [{ node: 'Rotor', axis: [0, 1, 0] }] });
    root.updateMatrixWorld(true);
    const fixed = fixture.matrixWorld.clone(), center = rotor.getWorldPosition(new THREE.Vector3());
    const pole = axisEnd.getWorldPosition(new THREE.Vector3());
    rig.setPhase(Math.PI / 2); root.updateMatrixWorld(true);
    assert.ok(tip.position.clone().applyQuaternion(rotor.quaternion).distanceTo(new THREE.Vector3(0, 0, -1)) < 1e-12);
    assert.deepEqual(fixture.matrixWorld, fixed);
    assert.ok(rotor.getWorldPosition(new THREE.Vector3()).distanceTo(center) < 1e-12);
    assert.ok(axisEnd.getWorldPosition(new THREE.Vector3()).distanceTo(pole) < 1e-12);
    for (let index = 0; index < 100; index++) rig.setPhase(Math.PI / 2);
    assert.ok(Math.abs(rotor.quaternion.angleTo(new THREE.Quaternion()) - Math.PI / 2) < 1e-12);
    rig.setPhase(2 * Math.PI);
    assert.ok(rotor.quaternion.angleTo(new THREE.Quaternion()) < 1e-7);
});

test('authored orientation is preserved and negative phase ratios rotate clock hands clockwise', () => {
    const root = new THREE.Group(), hand = new THREE.Group(); hand.name = 'Hand'; root.add(hand);
    hand.rotation.y = 0.3;
    const rest = hand.quaternion.clone();
    const rig = createAngularRig(root, { rotations: [{ node: 'Hand', axis: [0, 0, 1], ratio: -1 }] });
    rig.setPhase(Math.PI / 2);
    const relative = rest.clone().invert().multiply(hand.quaternion);
    assert.ok(new THREE.Vector3(0, 1, 0).applyQuaternion(relative).distanceTo(new THREE.Vector3(1, 0, 0)) < 1e-12);
    rig.setPhase(0); assert.deepEqual(hand.quaternion.toArray(), rest.toArray());
    assert.throws(() => createAngularRig(root, { rotations: [{ node: 'Missing', axis: [0, 1, 0] }] }), /Missing angular rotor/);
});
