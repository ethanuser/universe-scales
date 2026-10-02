import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from '../js/vendor/three/three.module.min.js';
import {
    CLASSICAL_ELECTRON_RADIUS_M, NEUTRINO_WAVELENGTH_1MEV_M, PLANCK_LENGTH_M,
    PROTON_RMS_CHARGE_RADIUS_M, QUARK_RADIUS_LIMIT_M,
    particleScaleMetadata, particleScaleScenes, PROTON_CLOUD_CROP_RMS, protonRadialCdf
} from '../js/experiences/particle-scale-models.js';
import { waveAnimation } from '../js/experiences/wave-models.js';

test('particle scale catalog has five exact dataset names and matching scene factories', () => {
    assert.deepEqual(Object.keys(particleScaleMetadata), [
        'Planck Length', 'Quark', 'Proton Radius', 'Electron', '1 MeV Neutrino Wavelength'
    ]);
    for (const entry of Object.values(particleScaleMetadata)) {
        assert.ok(entry.id);
        assert.ok(entry.procedural);
        assert.equal(entry.geometry, 'mesh');
        assert.equal(entry.representation, 'measurement_diagram');
        assert.equal(entry.name, Object.keys(particleScaleMetadata).find(name => particleScaleMetadata[name] === entry));
        assert.equal(entry.dimension, 'length');
        assert.equal(entry.unit, 'm');
        assert.ok(Number.isFinite(entry.value));
        assert.equal(entry.presentation.reference_size, 1);
        assert.equal(typeof particleScaleScenes[entry.procedural], 'function');
    }
    assert.equal(Object.keys(particleScaleScenes).length, 5);
    assert.equal(particleScaleMetadata['1 MeV Neutrino Wavelength'].value, NEUTRINO_WAVELENGTH_1MEV_M);
});

test('scene bounds remain close to one reference unit and geometry budgets stay small', () => {
    for (const [id, makeScene] of Object.entries(particleScaleScenes)) {
        const scene = makeScene();
        const dimensions = new THREE.Box3().setFromObject(scene, true).getSize(new THREE.Vector3());
        const extent = Math.max(dimensions.x, dimensions.y, dimensions.z);
        const maxExtent = id === 'proton-rms-charge-radius' ? 2 * PROTON_CLOUD_CROP_RMS : 1.3;
        assert.ok(extent > 0.9 && extent <= maxExtent, `${id} extent ${extent}`);
        assert.ok(scene.children.length <= 80, `${id} has ${scene.children.length} children`);
        let triangles = 0;
        scene.traverse(node => {
            const geometry = node.geometry;
            if (!geometry) return;
            triangles += geometry.index ? geometry.index.count / 3 : (geometry.getAttribute('position')?.count ?? 0) / 3;
        });
        assert.ok(triangles <= 60_000, `${id} has ${triangles} triangles`);
        assert.ok(scene.children.some(node => node.geometry), `${id} has no pickable geometry`);
    }
});

test('the Planck span has only two endpoints and no subdivisions or scene prose', () => {
    const scene = particleScaleScenes['planck-length-ruler']();
    const endpoints = scene.children.filter(node => node.name === 'endpoint');
    assert.equal(endpoints.length, 2);
    assert.deepEqual(endpoints.map(node => node.position.x), [-0.5, 0.5]);
    assert.equal(scene.children.length, 3);
    scene.traverse(node => assert.equal(node.userData.label, undefined));
});

test('proton cloud is calibrated to its rms radius and samples the stated 3D dipole profile', () => {
    const scene = particleScaleScenes['proton-rms-charge-radius']();
    const marker = scene.getObjectByName('rms-radius-marker').geometry.attributes.position;
    assert.equal(new THREE.Vector3().fromBufferAttribute(marker, 0).distanceTo(
        new THREE.Vector3().fromBufferAttribute(marker, 1)), 1);
    const points = scene.getObjectByName('proton-dipole-charge-illustration').geometry.attributes.position;
    let secondMoment = 0;
    for (let i = 0; i < points.count; i++) {
        const p = new THREE.Vector3().fromBufferAttribute(points, i);
        assert.ok(p.length() <= PROTON_CLOUD_CROP_RMS + 1e-6);
        secondMoment += p.lengthSq() / points.count;
    }
    const x = Math.sqrt(12) * PROTON_CLOUD_CROP_RMS;
    const gamma5 = 1 - Math.exp(-x) * (1 + x + x*x/2 + x**3/6 + x**4/24);
    assert.ok(Math.abs(secondMoment - gamma5 / protonRadialCdf(PROTON_CLOUD_CROP_RMS)) < 0.015);
    assert.ok(Math.abs(protonRadialCdf(PROTON_CLOUD_CROP_RMS) - 0.8067) < 0.002);
    assert.ok(particleScaleMetadata['Proton Radius'].presentation.layout_width_factor >= 2 * PROTON_CLOUD_CROP_RMS);
});

test('neutrino animation advances phase while keeping its one-wavelength reference fixed', () => {
    const scene = particleScaleScenes['neutrino-wavelength-1mev']().clone(true);
    const wave = scene.getObjectByName('one-de-broglie-wavelength');
    waveAnimation.update(scene, 0);
    const first = Array.from(wave.geometry.attributes.position.array);
    waveAnimation.update(scene, 2);
    assert.notDeepEqual(Array.from(wave.geometry.attributes.position.array), first);
    const bracket = scene.getObjectByName('wavelength-bracket');
    assert.equal(bracket.scale.x, 1);
    for (const value of wave.geometry.attributes.position.array) assert.ok(Number.isFinite(value));
});

test('scene factories return independent, reproducible diagrams', () => {
    for (const makeScene of Object.values(particleScaleScenes)) {
        const first = makeScene(), second = makeScene();
        assert.notEqual(first, second);
        assert.notEqual(first.children[0].geometry, second.children[0].geometry);
        assert.deepEqual(first.children.map(node => node.name), second.children.map(node => node.name));
    }
});

test('metadata distinguishes theoretical, upper-bound, rms, and conventional scales', () => {
    assert.equal(PLANCK_LENGTH_M, 1.616255e-35);
    assert.equal(QUARK_RADIUS_LIMIT_M, 4.3e-19);
    assert.equal(PROTON_RMS_CHARGE_RADIUS_M, 0.84075e-15);
    assert.equal(CLASSICAL_ELECTRON_RADIUS_M, 2.8179403205e-15);
    assert.match(particleScaleMetadata.Quark.note, /95% confidence upper limit/);
    assert.match(particleScaleMetadata['Proton Radius'].note, /not a hard surface/);
    assert.match(particleScaleMetadata.Electron.note, /not the physical radius/);
    assert.match(particleScaleMetadata['Planck Length'].note, /not an experimentally observed minimum/);
    for (const entry of Object.values(particleScaleMetadata)) {
        assert.equal('proposed_value' in entry, false);
        assert.equal('proposed_name' in entry, false);
        assert.doesNotMatch(entry.note, /legacy|proposed/);
    }
});

test('neutrino value is a 1 MeV de Broglie wavelength, not particle size', () => {
    const h = 6.62607015e-34;
    const c = 299_792_458;
    const energy = 1e6 * 1.602176634e-19;
    assert.ok(Math.abs(NEUTRINO_WAVELENGTH_1MEV_M - h * c / energy) < 5e-22);
    assert.equal(particleScaleMetadata['1 MeV Neutrino Wavelength'].value, NEUTRINO_WAVELENGTH_1MEV_M);
    assert.match(particleScaleMetadata['1 MeV Neutrino Wavelength'].note, /not an intrinsic neutrino size/);
});
