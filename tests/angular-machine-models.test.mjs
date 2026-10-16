import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from '../js/vendor/three/three.module.min.js';
import { buildAngularMachine } from '../js/experiences/angular-machine-models.js';

const EXPECTED = {
    'washing-machine': { axis: 'Z', dimensions: { width: 0.68, height: 0.84, depth: 0.59, drumDiameter: 0.49, drumLength: 0.34 } },
    'hard-drive': { axis: 'Y', dimensions: { width: 0.102, height: 0.026, depth: 0.147, platterDiameter: 0.096 } },
    'record-player': { axis: 'Y', dimensions: { width: 0.34, height: 0.085, depth: 0.30, recordDiameter: 0.300 } },
    'bicycle-wheel': { axis: 'Z', dimensions: { diameter: 0.70, width: 0.032, hubWidth: 0.10 } },
    blender: { axis: 'Y', dimensions: { width: 0.19, height: 0.40, depth: 0.19, jarHeight: 0.255, jarDiameter: 0.145 } }
};

function triangles(root) {
    let count = 0;
    root.traverse(node => {
        if (!node.isMesh) return;
        const geometry = node.geometry;
        count += geometry.index ? geometry.index.count / 3 : geometry.getAttribute('position').count / 3;
    });
    return count;
}

test('all machine builders expose a fixed Housing and a separately pivoted Rotor', () => {
    for (const [kind, expected] of Object.entries(EXPECTED)) {
        const root = buildAngularMachine(kind);
        const housing = root.getObjectByName('Housing');
        const rotor = root.getObjectByName('Rotor');
        assert.ok(housing, `${kind} has Housing`);
        assert.ok(rotor, `${kind} has Rotor`);
        assert.equal(housing.parent, root);
        assert.equal(rotor.parent, root);
        assert.equal(housing.userData.stationary, true);
        assert.equal(rotor.userData.stationary, false);
        assert.equal(rotor.userData.axis, expected.axis);
        assert.deepEqual(rotor.userData.pivot, [0, 0, 0]);
        assert.deepEqual(root.userData.dimensionsMeters, expected.dimensions);
        assert.equal(root.userData.illustrative, true);
        assert.ok(triangles(root) < 25_000, `${kind} has a bounded geometry budget`);

        let fixedCount = 0, movingCount = 0;
        housing.traverse(node => { if (node.isMesh) fixedCount++; });
        rotor.traverse(node => { if (node.isMesh) movingCount++; });
        assert.ok(fixedCount >= 5, `${kind} includes substantive fixed structure`);
        assert.ok(movingCount >= 3, `${kind} includes a substantive moving assembly`);
        for (const child of rotor.children) assert.equal(child.parent, rotor);
    }
});

test('each rotor origin is on the mechanical axis and rotates independently of its housing', () => {
    for (const [kind, expected] of Object.entries(EXPECTED)) {
        const root = buildAngularMachine(kind);
        const housing = root.getObjectByName('Housing');
        const rotor = root.getObjectByName('Rotor');
        const housingMatrix = housing.matrix.clone();
        const rotorPosition = rotor.position.clone();
        root.updateMatrixWorld(true);
        const rotorOrigin = new THREE.Vector3().setFromMatrixPosition(rotor.matrixWorld);
        assert.ok(rotorOrigin.distanceTo(rotor.getWorldPosition(new THREE.Vector3())) < 1e-12);
        assert.deepEqual(rotor.userData.axis, expected.axis);
        rotor.rotation[expected.axis.toLowerCase()] = 0.37;
        root.updateMatrixWorld(true);
        assert.ok(housing.matrix.equals(housingMatrix), `${kind} housing remains stationary`);
        assert.ok(rotor.position.equals(rotorPosition), `${kind} pivot does not shift while spinning`);
        assert.equal(rotor.rotation[expected.axis.toLowerCase()], 0.37);
    }
});

test('machine-specific fixed and rotating details are assigned to the correct hierarchy', () => {
    const checks = [
        ['washing-machine', 'perforated drum rear plate', 'stationary door bezel'],
        ['hard-drive', 'aluminum platter 1', 'stationary actuator arm'],
        ['record-player', 'vinyl record', 'fixed tubular tonearm'],
        ['bicycle-wheel', 'black pneumatic tire', 'fixed fork blade -0.06'],
        ['blender', 'pitched stainless blade 1', 'transparent tapered pitcher cutaway wall']
    ];
    for (const [kind, movingName, fixedName] of checks) {
        const root = buildAngularMachine(kind);
        const rotor = root.getObjectByName('Rotor');
        const housing = root.getObjectByName('Housing');
        assert.equal(root.getObjectByName(movingName).parent, rotor, `${movingName} turns with Rotor`);
        assert.equal(root.getObjectByName(fixedName).parent, housing, `${fixedName} stays with Housing`);
    }
    const washer = buildAngularMachine('washing-machine');
    const shell = washer.getObjectByName('perforated stainless drum shell');
    assert.ok(shell);
    assert.equal(shell.geometry.parameters.openEnded, true, 'drum has an open front, not a solid shell cap');
    assert.ok(washer.getObjectByName('drum perforation recesses'));
    assert.ok(washer.getObjectByName('drum interior lifter 1'));
    assert.ok(washer.getObjectByName('lifter reflective edge 1'));
    assert.equal(washer.getObjectByName('fixed tinted door glass'), undefined,
        'open cutaway leaves the spinning drum unobstructed');
    assert.ok(buildAngularMachine('hard-drive').getObjectByName('off-axis spindle witness tab'));
    assert.ok(buildAngularMachine('record-player').getObjectByName('offset label rule'));
    const wheel = buildAngularMachine('bicycle-wheel');
    assert.ok(Math.abs(wheel.getObjectByName('fork dropout -0.06').position.y) < 0.01,
        'fixed fork terminates at the axle, not at the tire bottom');
    const blender = buildAngularMachine('blender');
    const handle = blender.getObjectByName('side pitcher handle');
    assert.ok(handle.geometry.parameters.path.getPoints(24).every(point => point.x > 0.06));
    assert.ok(handle.geometry.parameters.path.getPoints(24).every(point => point.y < 0.31),
        'handle stays on the vessel side below the lid');
    for (const name of ['pitcher glass foot ring', 'pitcher mouth rolled rim',
        'pitcher lower reinforcing bead', 'lid perimeter seal']) {
        const ring = blender.getObjectByName(name);
        assert.ok(Math.abs(ring.rotation.x - Math.PI / 2) < 1e-12,
            `${name} is oriented horizontally around the Y axis`);
    }
});

test('metallic finishes request the ModelStage environment and blender blades remain exposed', () => {
    for (const kind of Object.keys(EXPECTED)) {
        const root = buildAngularMachine(kind);
        root.traverse(node => {
            if (!node.isMesh) return;
            const materials = Array.isArray(node.material) ? node.material : [node.material];
            for (const mat of materials)
                if (mat.metalness > 0.2) assert.equal(mat.userData.environment, 0.6, `${kind} metal gets room reflections`);
        });
    }
    const blenderRoot = buildAngularMachine('blender');
    const cutaway = blenderRoot.getObjectByName('transparent tapered pitcher cutaway wall');
    assert.equal(cutaway.userData.openFrontCutaway, true);
    const blade = blenderRoot.getObjectByName('pitched stainless blade 1');
    assert.ok(blade.geometry.parameters.width > 0.05, 'blade is large enough to read in the open pitcher');
    assert.equal(blade.parent.name, 'Rotor');
});

test('unknown machine kinds fail explicitly', () => {
    assert.throws(() => buildAngularMachine('washing'), { name: 'RangeError', message: /Unknown angular machine kind/ });
});

test('the drum is open at the front and blender reinforcing rings lie in the horizontal plane', () => {
    const washer = buildAngularMachine('washing-machine');
    assert.equal(washer.getObjectByName('perforated stainless drum shell').geometry.parameters.openEnded, true);
    const blender = buildAngularMachine('blender');
    for (const name of ['pitcher glass foot ring', 'pitcher lower reinforcing bead', 'lid perimeter seal']) {
        const ring = blender.getObjectByName(name);
        const axis = new THREE.Vector3(0, 0, 1).applyQuaternion(ring.quaternion);
        assert.ok(Math.abs(axis.y) > 0.999, name);
    }
});
