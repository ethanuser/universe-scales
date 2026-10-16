import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from '../js/vendor/three/three.module.min.js';
import { angularModelEntries, angularScene } from '../js/experiences/angular-models.js';
import { buildAngularMachine } from '../js/experiences/angular-machine-models.js';
import { createAngularRig, angularSweepBounds } from '../js/experiences/angular-rig.js';

test('observation-wheel capsule centers orbit while floors stay level through seeking and full turns', () => {
    const root = angularScene('observation-wheel');
    const rig = createAngularRig(root, angularModelEntries['London Eye'].angular_motion);
    rig.faceCamera();
    const floors = rig.rotations.slice(1).map(({ node }) => node.getObjectByName('level capsule floor'));
    assert.equal(floors.length, 32);
    root.updateMatrixWorld(true);
    const original = floors.map(node => node.getWorldQuaternion(new THREE.Quaternion()));
    const centers = rig.rotations.slice(1).map(({ node }) => node.getWorldPosition(new THREE.Vector3()));
    for (const phase of [0.37, Math.PI / 2, Math.PI, 5.1, 0, 2 * Math.PI]) {
        rig.setPhase(phase); root.updateMatrixWorld(true);
        floors.forEach((node, index) => {
            assert.ok(node.getWorldQuaternion(new THREE.Quaternion()).angleTo(original[index]) < 1e-7);
            const center = rig.rotations[index + 1].node.getWorldPosition(new THREE.Vector3());
            assert.ok(Math.abs(center.length() - centers[index].length()) < 1e-10);
            if (phase === Math.PI / 2) assert.ok(center.distanceTo(centers[index]) > 1);
        });
    }
});

test('new inspection models have finite geometry and bounded triangle budgets', () => {
    for (const kind of ['observation-wheel', 'gas-turbine', 'dental-turbine', 'pulsar']) {
        const root = angularScene(kind);
        let triangles = 0;
        root.traverse(node => {
            if (!node.isMesh) return;
            assert.ok(Array.from(node.geometry.getAttribute('position').array).every(Number.isFinite));
            triangles += (node.geometry.index?.count || node.geometry.getAttribute('position').count) / 3;
        });
        assert.ok(triangles < 25000, `${kind}: ${triangles} triangles`);
    }
});

test('hard-drive head and suspension clear the highest platter and spindle at every phase', () => {
    const root = buildAngularMachine('hard-drive');
    const rig = createAngularRig(root, angularModelEntries['Hard drive spindle'].angular_motion);
    for (const phase of [0, 0.37, Math.PI / 2, Math.PI]) {
        rig.setPhase(phase); root.updateMatrixWorld(true);
        const surface = new THREE.Box3().setFromObject(root.getObjectByName('magnetic recording surface 3'), true);
        for (const name of ['stationary actuator arm', 'head suspension flexure', 'read write head slider']) {
            const part = new THREE.Box3().setFromObject(root.getObjectByName(name), true);
            assert.ok(part.min.y > surface.max.y, name);
        }
    }
});

test('washer fixed rear wall and counterweights stay behind its rotating back plate', () => {
    const root = buildAngularMachine('washing-machine'); root.updateMatrixWorld(true);
    const drum = new THREE.Box3().setFromObject(root.getObjectByName('perforated drum rear plate'), true);
    root.getObjectByName('Housing').traverse(node => {
        if (node.name === 'outer tub rear bulkhead' || node.name.startsWith('counterweight boss')) {
            assert.ok(new THREE.Box3().setFromObject(node, true).max.z < drum.min.z, node.name);
        }
    });
});

test('blade row clears its casing and dental neck stays behind its rotor', () => {
    const turbine = angularScene('gas-turbine');
    const casing = turbine.getObjectByName('stationary outer casing').geometry.parameters;
    const clearance = casing.radius - casing.tube;
    turbine.traverse(node => {
        if (node.name !== 'turbine rotor blade') return;
        const positions = node.geometry.getAttribute('position');
        for (let i = 0; i < positions.count; i++) assert.ok(Math.hypot(positions.getX(i), positions.getY(i)) < clearance);
    });
    const dental = angularScene('dental-turbine'); dental.updateMatrixWorld(true);
    const neck = new THREE.Box3().setFromObject(dental.getObjectByName('fixed handpiece neck'), true);
    const bucket = new THREE.Box3().setFromObject(dental.getObjectByName('air turbine bucket'), true);
    assert.ok(neck.max.z < bucket.min.z);
});

test('oblique inspection exposes a shaft without reversing its projected rotation', () => {
    const root = new THREE.Group(), rotor = new THREE.Group(); rotor.name = 'Rotor'; root.add(rotor);
    rotor.add(new THREE.Mesh(new THREE.BoxGeometry(1, 1, 5)));
    const rig = createAngularRig(root, { rotations: [{ node: 'Rotor', axis: [0, 0, 1] }] });
    rig.faceCamera(undefined, 55);
    const bounds = angularSweepBounds(root, rig), axis = new THREE.Vector3(0, 0, 1).transformDirection(rotor.matrixWorld);
    assert.ok(bounds.getSize(new THREE.Vector3()).x > 4);
    assert.ok(axis.z * rig.rotations[0].ratio < 0);
    assert.ok(Math.abs(axis.z - Math.cos(55 * Math.PI / 180)) < 1e-12);
});
