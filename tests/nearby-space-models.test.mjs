import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from '../js/vendor/three/three.module.min.js';
import { KPC, PROXIMA_DISTANCE_M, PROXIMA_DISTANCE_PC, LOCAL_GROUP_GALAXIES, nearbySpaceModelMetadata, cosmicScenes,
    proximaCentauriDistanceScene, localGroupScene } from '../js/experiences/nearby-space-models.js';
import { addDistanceBracket } from '../js/experiences/procedural-models.js';
import { MILKY_WAY } from '../js/experiences/cosmic-models.js';

test('Proxima parsecs convert to meters and light-years at the expected scale', () => {
    assert.ok(Math.abs(PROXIMA_DISTANCE_M - 4.017e16) < 1e13);
    assert.ok(Math.abs(PROXIMA_DISTANCE_M / 9.4607304725808e15 - 4.246) < 0.002);
    assert.ok(Math.abs(PROXIMA_DISTANCE_M / KPC - PROXIMA_DISTANCE_PC / 1000) < 1e-15);
});

test('Proxima distance model brackets the actual marker spheres at their center separation', () => {
    const scene = proximaCentauriDistanceScene({ value: 4e16 });
    const sun = scene.getObjectByName('Sun'), proxima = scene.getObjectByName('Proxima Centauri');
    assert.ok(Math.abs(proxima.position.distanceTo(sun.position) * KPC - PROXIMA_DISTANCE_M) < 1e5);
    assert.ok(sun.isMesh && proxima.isMesh);
    assert.equal(proxima.userData.label, 'Proxima');
    assert.ok(sun.scale.x > PROXIMA_DISTANCE_M / KPC * 0.003);
    assert.ok(proxima.scale.x > PROXIMA_DISTANCE_M / KPC * 0.002);
    assert.deepEqual(nearbySpaceModelMetadata['Proxima Centauri'].presentation.distance_bracket.bodies,
        ['Sun', 'Proxima Centauri']);
    assert.match(nearbySpaceModelMetadata['Proxima Centauri'].note, /enlarged/);
    assert.equal(nearbySpaceModelMetadata['Proxima Centauri'].presentation.reference_size,
        PROXIMA_DISTANCE_M / KPC);
    addDistanceBracket(scene, nearbySpaceModelMetadata['Proxima Centauri'].presentation.distance_bracket);
    const bracketLines = scene.getObjectByName('distance-bracket').children.map(line => line.userData.screenLine);
    assert.equal(bracketLines.find(line => line.axis === 'x').length, PROXIMA_DISTANCE_M / KPC);
    assert.ok(bracketLines.filter(line => line.axis === 'y').every(line => line.length < PROXIMA_DISTANCE_M / KPC * 0.12),
        'bracket uprights should use the small rendered marker radii, not unit-radius Groups');
    const extent = new THREE.Box3().setFromObject(scene).getSize(new THREE.Vector3()).x;
    assert.ok(extent / (PROXIMA_DISTANCE_M / KPC) < 1.01, 'model bounds should calibrate to approximately 1.0x');
});

test('Local Group uses catalog coordinates and renders recognizable galaxy clouds', () => {
    const scene = localGroupScene({ value: 1e23 });
    assert.equal(scene.children.filter(node => node.userData.catalogDistanceKpc !== undefined).length, LOCAL_GROUP_GALAXIES.length);
    for (const name of ['Milky Way', 'Andromeda (M31)', 'Triangulum (M33)', 'Large Magellanic Cloud', 'Small Magellanic Cloud', 'M110 (NGC 205)']) {
        const galaxy = scene.getObjectByName(name);
        assert.ok(galaxy, `missing ${name}`);
        assert.ok(galaxy.children.some(child => child.isPoints), `${name} has no stellar cloud`);
        assert.ok(galaxy.children.some(child => child.isMesh), `${name} has no disk/spheroid mesh`);
        const points = galaxy.children.find(child => child.isPoints);
        assert.ok(points.userData.pointSize, `${name} cloud is not scaled with the rendered model`);
        const shouldLabel = ['Milky Way', 'Andromeda (M31)', 'Triangulum (M33)',
            'Large Magellanic Cloud', 'Small Magellanic Cloud'].includes(name);
        assert.equal(Boolean(galaxy.userData.label), shouldLabel, `${name} stage label policy`);
        if (shouldLabel) {
            assert.equal(galaxy.userData.labelLayout, 'orbit');
            assert.ok(Number.isInteger(galaxy.userData.labelPriority));
        }
        assert.equal(galaxy.userData.sphere, undefined, 'a galaxy Group is not a unit-radius sphere');
    }
    assert.equal(scene.getObjectByName('Milky Way').position.length(), 0);
    const andromeda = scene.getObjectByName('Andromeda (M31)');
    assert.ok(Math.abs(andromeda.position.length() - 783) < 1e-9);
    assert.ok(Math.abs(scene.getObjectByName('Triangulum (M33)').position.length() - 809) < 1e-9);
    const disk = andromeda.children.find(child => child.isMesh);
    const diskNormal = new THREE.Vector3(0, 0, 1).applyEuler(disk.rotation).applyEuler(andromeda.rotation).normalize();
    assert.ok(Math.abs(Math.abs(diskNormal.z) - Math.cos(THREE.MathUtils.degToRad(77))) < 1e-6);
    const boundary = scene.getObjectByName('Approximate Local Group span');
    assert.equal(boundary.userData.screenLine, undefined);
    assert.equal(boundary.children.length, 3);
    assert.ok(boundary.children.every(node => node.isLineLoop));
    const bounds = new THREE.Box3().setFromObject(boundary);
    assert.ok(Math.abs(bounds.getSize(new THREE.Vector3()).x * KPC / 1e23 - 1) < 1e-6);
    assert.match(nearbySpaceModelMetadata['Local Group'].note, /not a dynamical\/orbital solution/);
    assert.match(nearbySpaceModelMetadata['Local Group'].note, /one physical scale/);
    assert.equal(scene.getObjectByName('Milky Way').userData.galaxyRadiusKpc, MILKY_WAY.radius);
    for (const source of LOCAL_GROUP_GALAXIES)
        assert.equal(scene.getObjectByName(source.name).userData.galaxyRadiusKpc, source.radius);
    assert.equal(scene.getObjectByName('Andromeda (M31)').userData.label, 'M31');
    assert.equal(scene.getObjectByName('Large Magellanic Cloud').userData.label, 'LMC');
});

test('exports follow the procedural scene and metadata registry shape', () => {
    assert.equal(cosmicScenes['proxima-centauri-distance'], proximaCentauriDistanceScene);
    assert.equal(cosmicScenes['local-group'], localGroupScene);
    assert.equal(nearbySpaceModelMetadata['Local Group'].presentation.reference_size, 1e23 / KPC);
    assert.equal(nearbySpaceModelMetadata['Local Group'].basis_url, 'https://doi.org/10.1088/0004-6256/144/1/4');
    assert.ok(LOCAL_GROUP_GALAXIES.length >= 12);
});
