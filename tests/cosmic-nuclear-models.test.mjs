// New procedural models: calibrated to their listed sizes and built from the
// cited physical parameters.
import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from '../js/vendor/three/three.module.min.js';
import { KPC, MILKY_WAY, ANDROMEDA, cosmicModelMetadata, milkyWayScene, andromedaDistanceScene, galaxyPoints }
    from '../js/experiences/cosmic-models.js';
import { IRON_56, IRON_56_RADIUS, ironNucleusScene, nuclearModelMetadata } from '../js/experiences/atomic-models.js';

test('Milky Way disk spans the listed diameter with the Sun at 8.18 kpc', () => {
    assert.ok(Math.abs(2 * MILKY_WAY.radius * KPC - 1e21) < 1e12);
    const { positions } = galaxyPoints(MILKY_WAY, 4000, 7);
    let maximum = 0;
    for (let index = 0; index < positions.length; index += 3)
        maximum = Math.max(maximum, Math.hypot(positions[index], positions[index + 2]));
    assert.ok(maximum <= MILKY_WAY.radius + 1e-9 && maximum > 0.9 * MILKY_WAY.radius);
    const scene = milkyWayScene();
    assert.ok(Math.abs(scene.getObjectByName('Sun').position.length() - 8.18) < 1e-9);
    assert.equal(cosmicModelMetadata['Galaxy Diameter'].presentation.reference_size, 2 * MILKY_WAY.radius);
});

test('Andromeda diagram places both galaxies at the listed center distance', () => {
    const entry = cosmicModelMetadata['Andromeda Distance'];
    const scene = andromedaDistanceScene({ value: 2.37e22 });
    const milkyWay = scene.getObjectByName('Milky Way'), andromeda = scene.getObjectByName('Andromeda');
    assert.ok(Math.abs(andromeda.position.x - milkyWay.position.x - entry.presentation.reference_size) < 1e-9);
    assert.equal(andromeda.scale.x, ANDROMEDA.radius);
    // Disks start edge-on (normal +y), so a 77 degree inclination is a 13 degree turn.
    const normal = new THREE.Vector3(0, 1, 0).applyEuler(andromeda.rotation);
    const inclination = THREE.MathUtils.radToDeg(Math.acos(Math.abs(normal.z)));
    assert.ok(Math.abs(inclination - ANDROMEDA.inclination) < 1e-6);
});

test('iron-56 nucleus has 26 protons and 30 neutrons inside its charge-radius sphere', () => {
    const scene = ironNucleusScene();
    const protons = scene.children.filter(node => node.name === 'proton');
    const neutrons = scene.children.filter(node => node.name === 'neutron');
    assert.equal(protons.length, IRON_56.protons);
    assert.equal(neutrons.length, IRON_56.neutrons);
    assert.ok(Math.abs(IRON_56_RADIUS - Math.sqrt(5 / 3) * 3.7377) < 1e-12);
    for (const nucleon of [...protons, ...neutrons])
        assert.ok(nucleon.position.length() + IRON_56.nucleonRadius <= IRON_56_RADIUS + 1e-9);
    assert.equal(nuclearModelMetadata['Atomic Nucleus'].presentation.reference_size, 10);
});
