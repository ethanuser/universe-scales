import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from '../js/vendor/three/three.module.min.js';
import {
    atomicModelMetadata, atomicScenes, BOHR_RADIUS_PM, CARBON_EFFECTIVE_CHARGES,
    CARBON_ORBITAL_BOUNDARIES_BOHR, CARBON_ORBITAL_CDFS, CARBON_RADIAL_PROBABILITY,
    HYDROGEN_BOUNDARY_BOHR, HYDROGEN_ENCLOSED_PROBABILITY,
    HYDROGEN_RADIUS_PROBABILITY, hydrogenAtomScene, carbonAtomScene, pContourRadius, P_CONTOUR_PEAK_FRACTION
} from '../js/experiences/atomic-models.js';
import { additionalWavelengthRows, update, waveAnimation, waveModelMetadata, waveScene, waveScenes }
    from '../js/experiences/wave-models.js';

function positionsAreFinite(scene) {
    let count = 0;
    scene.traverse(node => {
        const attribute = node.geometry?.getAttribute('position');
        if (!attribute) return;
        for (let index = 0; index < attribute.array.length; index++)
            assert.ok(Number.isFinite(attribute.array[index]), `${node.name} position ${index}`);
        count += attribute.count;
    });
    assert.ok(count > 0);
}

function triangleCount(scene) {
    let count = 0;
    scene.traverse(node => {
        if (!node.isMesh) return;
        const geometry = node.geometry;
        count += (geometry.index?.count ?? geometry.getAttribute('position').count) / 3;
    });
    return count;
}

test('hydrogen cloud is clipped at the calibrated one-Bohr radius', () => {
    const scene = hydrogenAtomScene();
    const cloud = scene.getObjectByName('hydrogen-1s-probability');
    const points = cloud.geometry.getAttribute('position');
    let maximum = 0;
    for (let index = 0; index < points.count; index++) {
        const radius = new THREE.Vector3().fromBufferAttribute(points, index).length();
        maximum = Math.max(maximum, radius);
        assert.ok(radius <= HYDROGEN_BOUNDARY_BOHR + 1e-7);
    }
    assert.equal(HYDROGEN_BOUNDARY_BOHR, 1);
    assert.ok(maximum > 0.99);
    assert.ok(Math.abs(HYDROGEN_RADIUS_PROBABILITY(1) - HYDROGEN_ENCLOSED_PROBABILITY) < 1e-14);
    assert.ok(Math.abs(HYDROGEN_ENCLOSED_PROBABILITY - 0.3233235838) < 1e-9);
    assert.equal(atomicModelMetadata['Hydrogen Atom'].presentation.reference_size, 1);
    assert.equal(atomicModelMetadata['Hydrogen Atom'].value, 5.3e-11);
    assert.match(atomicModelMetadata['Hydrogen Atom'].source, /^https:\/\//);
    assert.ok(Math.abs(BOHR_RADIUS_PM - 52.9177) < 0.001);
    positionsAreFinite(scene);
});

test('carbon shows the independent-electron 1s2 2s2 2p2 orbital set', () => {
    const scene = carbonAtomScene();
    assert.deepEqual(CARBON_EFFECTIVE_CHARGES, { '1s': 5.6727, '2s': 3.22, '2p': 3.14 });
    assert.deepEqual(Object.keys(CARBON_ORBITAL_BOUNDARIES_BOHR), ['1s', '2s', '2p']);
    for (const orbital of ['1s', '2s', '2p'])
        assert.ok(Math.abs(CARBON_ORBITAL_CDFS[orbital](CARBON_ORBITAL_BOUNDARIES_BOHR[orbital] * CARBON_EFFECTIVE_CHARGES[orbital]) - CARBON_RADIAL_PROBABILITY) < 1e-12);
    const expected = {
        'carbon-1s-electron-pair': 3000,
        'carbon-2s-electron-pair': 3000,
        'carbon-2px-electron': 1500,
        'carbon-2py-electron': 1500
    };
    for (const [name, count] of Object.entries(expected)) {
        const cloud = scene.getObjectByName(name);
        assert.ok(cloud, name);
        assert.equal(cloud.geometry.getAttribute('position').count, count);
        const orbital = name.includes('1s') ? '1s' : name.includes('2s') ? '2s' : '2p';
        const boundary = CARBON_ORBITAL_BOUNDARIES_BOHR[orbital];
        const points = cloud.geometry.getAttribute('position');
        for (let index = 0; index < points.count; index++)
            assert.ok(new THREE.Vector3().fromBufferAttribute(points, index).length() <= boundary + 1e-6);
    }
    assert.equal(scene.getObjectByName('carbon-2px-electron').userData.waveAxis, undefined);
    scene.updateMatrixWorld(true);
    for (const orbital of ['1s', '2s', '2p']) {
        const boundary = scene.getObjectByName(`carbon-${orbital}-90-percent-boundary`);
        assert.ok(Math.abs(boundary.geometry.parameters.radius - CARBON_ORBITAL_BOUNDARIES_BOHR[orbital]) < 1e-12);
    }
    assert.deepEqual(scene.scale.toArray(), [1, 1, 1]);
    assert.ok(Math.abs(atomicModelMetadata['Carbon Atom'].presentation.reference_size - 70 / BOHR_RADIUS_PM) < 1e-12);
    for (const [name, axis] of [['carbon-2px-electron', 0], ['carbon-2py-electron', 1]]) {
        const points = scene.getObjectByName(name).geometry.getAttribute('position');
        let axial = 0, other = 0;
        for (let index = 0; index < points.count; index++) {
            const vector = new THREE.Vector3().fromBufferAttribute(points, index);
            const squaredRadius = vector.lengthSq();
            axial += vector.getComponent(axis) ** 2 / squaredRadius;
            other += vector.getComponent(1 - axis) ** 2 / squaredRadius;
        }
        assert.ok(axial / points.count > 0.5);
        assert.ok(other / points.count < 0.3);
    }
    assert.equal(atomicModelMetadata['Carbon Atom'].value, 7e-11);
    assert.match(atomicModelMetadata['Carbon Atom'].source, /^https:\/\//);
    assert.ok(atomicModelMetadata['Carbon Atom'].sources.some(source => source.includes('10.1063/1.1733573')));
    assert.match(atomicModelMetadata['Carbon Atom'].note, /not an exact correlated six-electron solution/);
    assert.match(atomicModelMetadata['Carbon Atom'].note, /not a van der Waals radius/);
    assert.match(atomicModelMetadata['Carbon Atom'].note, /2:2:1:1 electron occupancy/);
    assert.ok(triangleCount(scene) < 15000);
    assert.ok(atomicModelMetadata['Carbon Atom'].presentation.layout_width_factor >
        2 * CARBON_ORBITAL_BOUNDARIES_BOHR['2s'] / atomicModelMetadata['Carbon Atom'].presentation.reference_size);
    positionsAreFinite(scene);
});

test('carbon p contours use one density threshold, not arbitrary ellipsoid lobes', () => {
    const z = CARBON_EFFECTIVE_CHARGES['2p'];
    for (const theta of [0, 0.3, 0.7, 1.1]) for (const outer of [false, true]) {
        const r = pContourRadius(theta, outer), x = z * r;
        const relativeDensity = x * x * Math.exp(-x) * Math.cos(theta) ** 2 / (4 * Math.exp(-2));
        assert.ok(Math.abs(relativeDensity - P_CONTOUR_PEAK_FRACTION) < 1e-12);
    }
});

test('wave module supplies seven calibrated band metadata entries and a clone-safe animation hook', () => {
    assert.deepEqual(Object.keys(waveModelMetadata), [
        'Gamma Ray Wavelength', 'X-ray Wavelength', 'UV Wavelength',
        'Visible Light Wavelength', 'Infrared Wavelength', 'Microwave Wavelength', 'Radio Wavelength'
    ]);
    for (const entry of Object.values(waveModelMetadata)) {
        assert.ok(entry.wavelength_m > 0);
        assert.equal(entry.value, entry.wavelength_m);
        assert.match(entry.source, /^https:\/\//);
        assert.ok(entry.source_title);
        assert.equal(entry.procedural, 'traveling-em-wave');
        assert.equal(entry.presentation.reference_size, 1);
    }
    assert.equal(additionalWavelengthRows.length, 6);
    assert.deepEqual(additionalWavelengthRows.map(row => row.name), [
        'Gamma Ray Wavelength', 'X-ray Wavelength', 'UV Wavelength', 'Infrared Wavelength',
        'Microwave Wavelength', 'Radio Wavelength'
    ]);
    assert.deepEqual(additionalWavelengthRows.map(row => row.value), [
        1.057e-12, 0.15405925e-9, 253.7e-9, 9.35e-6, 0.12236, 2.9979
    ]);
    assert.match(waveModelMetadata['Gamma Ray Wavelength'].note, /Co-60 1\.17323 MeV/);
    assert.match(waveModelMetadata['X-ray Wavelength'].note, /Cu K-alpha1/);
    assert.match(waveModelMetadata['UV Wavelength'].note, /253\.7 nm/);
    assert.match(waveModelMetadata['Infrared Wavelength'].note, /310 K/);
    assert.match(waveModelMetadata['Microwave Wavelength'].note, /2\.45 GHz/);
    assert.match(waveModelMetadata['Radio Wavelength'].note, /100 MHz FM/);
    for (const row of additionalWavelengthRows) assert.ok(row.sources.length >= 1);
    const scene = waveScene();
    const copy = scene.clone(true);
    assert.doesNotThrow(() => structuredClone(copy.userData));
    const electric = copy.getObjectByName('electric-field-wave');
    const magnetic = copy.getObjectByName('magnetic-field-wave');
    for (const field of [electric, magnetic]) {
        const positions = field.geometry.getAttribute('position');
        const normals = field.geometry.getAttribute('normal');
        const sample = 30, firstVertex = sample * 6;
        let centerY = 0, centerZ = 0;
        for (let side = 0; side < 5; side++) {
            centerY += positions.getY(firstVertex + side) / 5;
            centerZ += positions.getZ(firstVertex + side) / 5;
        }
        const radialY = positions.getY(firstVertex + 1) - centerY;
        const radialZ = positions.getZ(firstVertex + 1) - centerZ;
        assert.ok(normals.getY(firstVertex + 1) * radialY + normals.getZ(firstVertex + 1) * radialZ > 0,
            `${field.name} tube normals point outward`);
    }
    const crestSample = 15, verticesPerRing = 6;
    const eCrest = electric.geometry.getAttribute('position'), bCrest = magnetic.geometry.getAttribute('position');
    let eY = 0, bZ = 0;
    for (let side = 0; side < 5; side++) {
        eY += eCrest.getY(crestSample * verticesPerRing + side) / 5;
        bZ += bCrest.getZ(crestSample * verticesPerRing + side) / 5;
    }
    // At this crest E points +y and B points +z, so E cross B propagates +x.
    assert.ok(eY > 0 && bZ > 0 && eY * bZ > 0);
    const positions = electric.geometry.getAttribute('position');
    const before = positions.getY(30 * 6);
    update(copy, 1 / (4 * copy.userData.waveAnimation.cyclesPerSecond));
    const after = positions.getY(30 * 6);
    assert.notEqual(after, before);
    assert.ok(Math.abs(after - before) > 0.2);
    assert.equal(waveAnimation.update, update);
    assert.equal(waveScenes['traveling-em-wave'], waveScene);
    const labels = [];
    copy.traverse(node => { if (node.userData.label) labels.push(node.userData.label); });
    assert.deepEqual(labels.filter(label => label === 'E\u0302' || label === 'B\u0302'), ['E\u0302', 'B\u0302']);
    assert.ok(!labels.includes('Electric field'));
    assert.ok(!labels.includes('Magnetic field'));
    assert.equal(labels.filter(label => label.includes('E')).length, 1);
    assert.equal(labels.filter(label => label.includes('B')).length, 1);
    assert.ok(triangleCount(copy) < 5000);
    positionsAreFinite(copy);
});

test('module metadata and factories have stable, explicit integration keys', () => {
    assert.deepEqual(Object.keys(atomicModelMetadata), ['Hydrogen Atom', 'Carbon Atom']);
    assert.deepEqual(Object.keys(atomicScenes), ['hydrogen-1s-quantum', 'carbon-independent-electron']);
    assert.equal(atomicScenes['hydrogen-1s-quantum'], hydrogenAtomScene);
    assert.equal(atomicScenes['carbon-independent-electron'], carbonAtomScene);
});

test('wave animation survives production normalization wrappers and keeps both fields in phase', () => {
    const normalized = new THREE.Group(), calibrated = new THREE.Group();
    calibrated.add(waveScene());
    normalized.add(calibrated);
    const instance = normalized.clone(true);
    const roots = waveAnimation.animationRoots(instance);
    assert.equal(roots.length, 1);
    const e = instance.getObjectByName('electric-field-wave').geometry.getAttribute('position');
    const b = instance.getObjectByName('magnetic-field-wave').geometry.getAttribute('position');
    const before = e.array.slice();
    for (const time of [0, 0.2, 0.71, 1.9]) {
        roots.forEach(root => waveAnimation.update(root, time));
        for (let ring = 0; ring <= 120; ring++) {
            const center = attribute => {
                const point = new THREE.Vector3();
                for (let side = 0; side < 5; side++)
                    point.add(new THREE.Vector3().fromBufferAttribute(attribute, ring * 6 + side));
                return point.divideScalar(5);
            };
            const electric = center(e), magnetic = center(b);
            assert.ok(Math.abs(electric.x - magnetic.x) < 1e-7);
            assert.ok(Math.abs(electric.y - magnetic.z) < 1e-7);
            assert.ok(Math.abs(electric.z) < 1e-7 && Math.abs(magnetic.y) < 1e-7);
        }
    }
    assert.notDeepEqual(e.array, before);
    assert.ok(waveModelMetadata['Visible Light Wavelength'].presentation.pitch >= 30);
});
