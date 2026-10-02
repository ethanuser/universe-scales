import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from '../js/vendor/three/three.module.min.js';
import { prepareModelPoints, softPointSprite } from '../js/experiences/model-points.js';

test('soft particle sprite has a bright center and transparent boundary', () => {
    const texture = softPointSprite();
    assert.equal(softPointSprite(), texture, 'reuse one small sprite');
    assert.equal(texture.image.width, 32);
    assert.equal(texture.image.height, 32);
    assert.equal(texture.image.data[3], 0);
    assert.ok(texture.image.data[(16 * 32 + 16) * 4 + 3] > 250);
    assert.equal(texture.image.data[(16 * 32) * 4 + 3], 0);
});

test('only opted-in clouds receive cloned, transparent soft materials', () => {
    const shared = new THREE.PointsMaterial();
    const scene = new THREE.Group();
    const soft = new THREE.Points(new THREE.BufferGeometry(), shared);
    const unchanged = new THREE.Points(new THREE.BufferGeometry(), shared);
    soft.userData.softPoints = true;
    scene.add(soft, unchanged);
    prepareModelPoints(scene);
    assert.notEqual(soft.material, shared);
    assert.equal(unchanged.material, shared);
    assert.equal(soft.material.map, softPointSprite());
    assert.equal(soft.material.depthWrite, false);
    assert.equal(soft.material.transparent, true);
    assert.equal(shared.map, null);
});
