import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from '../js/vendor/three/three.module.min.js';
import {
    atomicModelMetadata, atomicScenes, BOHR_RADIUS_PM, CARBON_BOUNDARY_BOHR, CARBON_EFFECTIVE_CHARGES,
    CARBON_ENCLOSED, CARBON_ENCLOSED_ELECTRONS, HYDROGEN_BOUNDARY_BOHR, HYDROGEN_ENCLOSED_PROBABILITY,
    hydrogenAtomScene, carbonAtomScene, pContourRadius, P_CONTOUR_PEAK_FRACTION, radialCdf
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

function maxRadius(points) {
    let maximum = 0;
    for (let index = 0; index < points.count; index++)
        maximum = Math.max(maximum, new THREE.Vector3().fromBufferAttribute(points, index).length());
    return maximum;
}
function extent(scene) {
    const size = new THREE.Box3().setFromObject(scene).getSize(new THREE.Vector3());
    return Math.max(size.x, size.y, size.z);
}

test('hydrogen is cut off at one Bohr radius and drawn at its listed diameter', () => {
    const scene = hydrogenAtomScene();
    const cloud = scene.getObjectByName('hydrogen-1s-probability').geometry.getAttribute('position');
    assert.ok(maxRadius(cloud) <= HYDROGEN_BOUNDARY_BOHR + 1e-7);
    assert.ok(maxRadius(cloud) > 0.97);
    // 1 - 5/e^2 of the 1s probability lies within one Bohr radius.
    assert.ok(Math.abs(HYDROGEN_ENCLOSED_PROBABILITY - (1 - 5 * Math.exp(-2))) < 1e-15);
    assert.ok(Math.abs(BOHR_RADIUS_PM - 52.9177) < 0.001);
    const entry = atomicModelMetadata['Hydrogen Atom'];
    assert.ok(Math.abs(entry.value - 2 * BOHR_RADIUS_PM * 1e-12) < 1e-15);
    // Model extent in listed-value units: the boundary diameter / reference size.
    assert.ok(Math.abs(extent(scene) / entry.presentation.reference_size - 1) < 0.02);
    assert.match(entry.note, /32\.3%/);
    positionsAreFinite(scene);
});

test('carbon orbitals stay inside the 70 pm sphere with half-peak 2p lobes', () => {
    assert.deepEqual(CARBON_EFFECTIVE_CHARGES, { '1s': 5.6727, '2s': 3.2166, '2p': 3.1358 });
    assert.ok(Math.abs(CARBON_BOUNDARY_BOHR * BOHR_RADIUS_PM - 70) < 1e-9);
    // Enclosed fractions from the hydrogen-like radial CDFs at x = Z r / a0.
    assert.ok(CARBON_ENCLOSED['1s'] > 0.9999);
    assert.ok(Math.abs(CARBON_ENCLOSED['2s'] - 0.2154) < 0.001);
    assert.ok(Math.abs(CARBON_ENCLOSED['2p'] - 0.4001) < 0.001);
    assert.ok(Math.abs(CARBON_ENCLOSED_ELECTRONS / 6 - 0.5385) < 0.001);
    assert.ok(Math.abs(P_CONTOUR_PEAK_FRACTION - 0.502) < 0.001);
    const scene = carbonAtomScene();
    for (const name of ['carbon-1s-pair', 'carbon-2s-pair', 'carbon-2px-electron', 'carbon-2py-electron']) {
        const cloud = scene.getObjectByName(name);
        assert.ok(cloud, name);
        assert.ok(maxRadius(cloud.geometry.getAttribute('position')) <= CARBON_BOUNDARY_BOHR + 1e-6, name);
    }
    // Equal dots per enclosed electron: the 1s pair outnumbers each 2p electron
    // by the ratio of their enclosed electron counts.
    const count = name => scene.getObjectByName(name).geometry.getAttribute('position').count;
    assert.ok(Math.abs(count('carbon-1s-pair') / count('carbon-2px-electron') - 2 / CARBON_ENCLOSED['2p']) < 0.01);
    // The 2p lobes are elongated along their own axis.
    for (const [name, axis] of [['carbon-2px-electron', 0], ['carbon-2py-electron', 1]]) {
        const points = scene.getObjectByName(name).geometry.getAttribute('position');
        let axial = 0;
        for (let index = 0; index < points.count; index++) {
            const vector = new THREE.Vector3().fromBufferAttribute(points, index);
            axial += vector.getComponent(axis) ** 2 / vector.lengthSq();
        }
        assert.ok(axial / points.count > 0.5, name);
    }
    // Lobe tips touch the boundary, so the whole model spans the listed diameter.
    assert.ok(Math.abs(pContourRadius(0, true) - CARBON_BOUNDARY_BOHR) < 1e-6);
    const entry = atomicModelMetadata['Carbon Atom'];
    assert.equal(entry.value, 1.4e-10);
    assert.ok(Math.abs(extent(scene) / entry.presentation.reference_size - 1) < 0.03);
    assert.ok(entry.sources.some(source => source.includes('10.1063/1.1733573')));
    assert.match(entry.note, /53\.8%/);
    assert.ok(triangleCount(scene) < 20000);
    positionsAreFinite(scene);
});

test('carbon p contours use one density threshold, not arbitrary ellipsoid lobes', () => {
    const z = CARBON_EFFECTIVE_CHARGES['2p'];
    for (const theta of [0, 0.3, 0.6, 0.75]) for (const outer of [false, true]) {
        const r = pContourRadius(theta, outer), x = z * r;
        const relativeDensity = x * x * Math.exp(-x) * Math.cos(theta) ** 2 / (4 * Math.exp(-2));
        assert.ok(Math.abs(relativeDensity - P_CONTOUR_PEAK_FRACTION) < 1e-9);
    }
    assert.ok(Math.abs(radialCdf['2p'](50) - 1) < 1e-12);
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
    const crestSample = 30, verticesPerRing = 6; // a quarter of the single cycle
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
    assert.deepEqual(labels.filter(label => label === 'E' || label === 'B'), ['E', 'B']);
    assert.ok(labels.some(label => label.startsWith('λ =')));
    // The window is one wavelength: fields span x = 0..1 from the shared origin,
    // and the propagation arrow starts at that origin.
    const fieldBounds = new THREE.Box3().setFromObject(electric);
    assert.ok(Math.abs(fieldBounds.min.x) < 0.02 && Math.abs(fieldBounds.max.x - 1) < 0.02);
    assert.equal(waveScene({ wavelength_m: 500e-9 }).children.some(node => node.userData.label === 'λ = 500 nm'), true);
    assert.ok(triangleCount(copy) < 5000);
    positionsAreFinite(copy);
});

test('module metadata and factories have stable, explicit integration keys', () => {
    assert.deepEqual(Object.keys(atomicModelMetadata), ['Hydrogen Atom', 'Carbon Atom']);
    assert.deepEqual(Object.keys(atomicScenes), ['iron-56-nucleus', 'hydrogen-1s-quantum', 'carbon-atom-quantum']);
    assert.equal(atomicScenes['hydrogen-1s-quantum'], hydrogenAtomScene);
    assert.equal(atomicScenes['carbon-atom-quantum'], carbonAtomScene);
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
    assert.ok(waveModelMetadata['Visible Light Wavelength'].presentation.pitch >= 15);
});
