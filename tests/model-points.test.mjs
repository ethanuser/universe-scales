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
    assert.equal(soft.material.forceSinglePass, true);
});

test('LOD prefixes sample the entire scientific cloud without editing source coordinates', () => {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(Array.from({ length: 6000 }, (_, i) => i), 3));
    const source = geometry.attributes.position.array.slice();
    const make = () => {
        const cloud = new THREE.Points(geometry, new THREE.PointsMaterial());
        cloud.userData = { softPoints: true, pointSize: { max: 4, perPixel: 0.01 } };
        const group = new THREE.Group(); group.add(cloud); prepareModelPoints(group); return cloud;
    };
    const a = make(), b = make(), indices = [...a.geometry.index.array];
    assert.equal(new Set(indices).size, 2000);
    assert.equal(Math.min(...indices), 0);
    assert.equal(Math.max(...indices), 1999);
    assert.deepEqual(a.geometry.index.array, b.geometry.index.array);
    assert.deepEqual(a.geometry.attributes.position.array, source);
    assert.equal(geometry.index, null, 'shared source geometry remains unchanged');
    const buckets = new Set(indices.slice(0, 128).map(i => Math.floor(i / 200)));
    assert.equal(buckets.size, 10, 'small LOD covers every scanline band');
    assert.equal(a.userData.pointLOD.minimum, 128);
});
