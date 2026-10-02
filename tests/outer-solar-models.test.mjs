import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import * as THREE from '../js/vendor/three/three.module.min.js';
import { HELIOSPHERE, OORT_CLOUD, outerSolarModelMetadata, outerSolarScenes,
    heliosphereScene, oortCloudScene } from '../js/experiences/outer-solar-models.js';
import { proceduralLength, proceduralScene } from '../js/experiences/procedural-models.js';

function pointCount(points) {
    return points.geometry.getAttribute('position').count;
}

function triangleCount(root) {
    let triangles = 0;
    root.traverse(node => {
        if (node.isMesh) {
            const geometry = node.geometry;
            triangles += geometry.index ? geometry.index.count / 3 : geometry.getAttribute('position').count / 3;
        }
    });
    return triangles;
}

test('Oort Cloud separates a flattened inner component from the diffuse spherical outer sample', () => {
    const scene = oortCloudScene();
    const hills = scene.getObjectByName('Flattened inner Hills-cloud sample');
    const outer = scene.getObjectByName('Diffuse outer-cloud sample');
    assert.equal(scene.userData.sceneUnit, 'AU');
    assert.deepEqual(hills.userData.radialRangeAU, [2_000, 20_000]);
    assert.deepEqual(outer.userData.radialRangeAU, [20_000, 100_000]);
    assert.equal(pointCount(hills), 7_000);
    assert.equal(pointCount(outer), 16_000);
    assert.ok(pointCount(outer) <= 30_000);
    const edge = scene.getObjectByName('Contextual 100000 AU radius');
    assert.equal(edge.userData.notObservedGasShell, true);
    assert.equal(edge.children.length, 3);
    const size = new THREE.Box3().setFromObject(scene).getSize(new THREE.Vector3());
    assert.ok(Math.abs(size.x - OORT_CLOUD.referenceSizeAU) < 1e-3);
    assert.ok(Math.abs(size.y - OORT_CLOUD.referenceSizeAU) < 1e-3);
    assert.ok(Math.abs(size.z - OORT_CLOUD.referenceSizeAU) < 1e-3);
    assert.equal(outerSolarModelMetadata['Oort Cloud'].presentation.reference_size, size.x);
    assert.equal(scene.children.some(node => node.userData.label === 'Hills cloud'), true);
    assert.equal(scene.children.some(node => node.userData.label === 'Outer cloud'), true);
});

test('Heliosphere marks Voyager shock crossings, the upwind heliopause, and an explicitly illustrative tail', () => {
    const scene = heliosphereScene();
    assert.equal(scene.userData.sceneUnit, 'AU');
    assert.equal(scene.userData.upwindAxis, '+X');
    const shock = scene.getObjectByName('Termination shock ~90 AU');
    const heliopause = scene.getObjectByName('Heliopause ~120 AU upwind');
    assert.equal(shock.userData.radiusAU, HELIOSPHERE.terminationShockDiagramAU);
    assert.deepEqual(shock.userData.observedVoyagerCrossingsAU, [84, 94]);
    assert.equal(heliopause.userData.upwindExtentAU, HELIOSPHERE.heliopauseUpwindAU);
    assert.equal(heliopause.userData.shapeIsSchematic, true);
    const tail = scene.getObjectByName('Illustrative, truncated heliotail tracers');
    assert.equal(tail.userData.notToScale, true);
    assert.equal(tail.userData.notPhysicalLength, true);
    assert.equal(shock.userData.partialBoundary, true);
    assert.equal(heliopause.userData.partialBoundary, true);
    assert.equal(outerSolarModelMetadata.Heliosphere.presentation.reference_size, 240);
    assert.ok(scene.getObjectByName('Rounded heliopause radial-distance cue'));
    assert.ok(scene.children.some(node => node.userData.label === 'Upwind'));
    assert.equal(scene.children.some(node => node.userData.label === 'Nose-side cutaway'), false);
    assert.equal(scene.children.filter(node => node.name === 'Solar-wind streamline').length, 12);
    for (const flow of scene.children.filter(node => node.name === 'Solar-wind streamline')) {
        const endpoint = flow.geometry.parameters.path.points.at(-1);
        assert.ok(Math.hypot(endpoint.x / 90, endpoint.y / 64, endpoint.z / 64) < 1);
    }
    const sheath = scene.getObjectByName('Heliosheath particle tracers');
    assert.ok(pointCount(sheath) <= 30_000);
    const positions = sheath.geometry.getAttribute('position');
    for (let index = 0; index < positions.count; index++)
        assert.ok(positions.getX(index) >= 0, 'do not invent a downstream sheath boundary');
    assert.ok(triangleCount(scene) <= 60_000);
});

test('metadata provides scientific basis links, bounded notes, and matching scene registries', () => {
    for (const [name, id, sceneKey, factory] of [
        ['Oort Cloud', 'oort-cloud-schematic', 'oort-cloud', oortCloudScene],
        ['Heliosphere', 'heliosphere-schematic', 'heliosphere', heliosphereScene]
    ]) {
        const metadata = outerSolarModelMetadata[name];
        const words = metadata.note.trim().split(/\s+/);
        assert.equal(metadata.id, id);
        assert.equal(metadata.procedural, sceneKey);
        assert.equal(outerSolarScenes[sceneKey], factory);
        assert.match(metadata.basis_url, /^https:\/\//);
        assert.ok(words.length >= 60 && words.length <= 120, `${name} note has ${words.length} words`);
        assert.ok(Number.isFinite(metadata.presentation.reference_size));
    }
    assert.match(outerSolarModelMetadata['Oort Cloud'].note, /not an observed gas shell/);
    assert.match(outerSolarModelMetadata.Heliosphere.note, /not a scaled estimate/);
});

test('production integration preserves the physical AU scale used by the exported Length values', () => {
    const data = JSON.parse(readFileSync(new URL('../exports/json/dimensions/length.json', import.meta.url), 'utf8'));
    for (const [name, referenceAU] of [['Oort Cloud', 200_000], ['Heliosphere', 240]]) {
        const item = data.items.find(item => item.name === name);
        const entry = proceduralLength[name];
        assert.deepEqual(entry, outerSolarModelMetadata[name]);
        assert.equal(item.value, referenceAU * 149_597_870_700);
        assert.equal(entry.presentation.reference_size, referenceAU);
        assert.equal(item.value_type, 'derived');
        assert.match(item.qualifiers.measurement, /diameter/);
        assert.match(item.source, /^https:\/\/science\.nasa\.gov\//);
        assert.ok(proceduralScene(entry.procedural, entry).children.length > 0);
    }
});
