// The orbital distance bracket is built from the registry's body nodes with the
// real vendored three.js, so this checks geometry rather than a stub.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import * as THREE from '../js/vendor/three/three.module.min.js';

const source = readFileSync(new URL('../js/experiences/models.js', import.meta.url), 'utf8');
const start = source.indexOf('const BRACKET_LINE_PX');
const end = source.indexOf('const proceduralLength');
const { addDistanceBracket, BRACKET_DROP } = new Function('THREE',
    `${source.slice(start, end)}; return { addDistanceBracket, BRACKET_DROP };`)(THREE);

function diagram(left, right) {
    const scene = new THREE.Group();
    for (const [name, x, radius] of [left, right]) {
        const body = new THREE.Mesh(new THREE.SphereGeometry(1), new THREE.MeshBasicMaterial());
        body.name = name;
        body.position.x = x;
        body.scale.setScalar(radius);
        scene.add(body);
    }
    return scene;
}

test('bracket lines are tangent to the facing edges and joined below both bodies', () => {
    const earth = 6_371_000 / 384_400_000, moon = 1_737_500 / 384_400_000;
    const scene = diagram(['Earth', -0.5, earth], ['Moon', 0.5, moon]);
    addDistanceBracket(scene, { bodies: ['Earth', 'Moon'] });
    const bars = scene.getObjectByName('distance-bracket').children;
    const vertical = bars.filter(bar => bar.userData.bracketAxis === 'y')
        .sort((a, b) => a.position.x - b.position.x);
    const [horizontal] = bars.filter(bar => bar.userData.bracketAxis === 'x');
    assert.equal(vertical.length, 2);
    assert.ok(Math.abs(vertical[0].position.x - (-0.5 + earth)) < 1e-12);
    assert.ok(Math.abs(vertical[1].position.x - (0.5 - moon)) < 1e-12);
    const bottom = -(earth + BRACKET_DROP);
    for (const bar of vertical) {
        // Each line runs from the tangent point (body equator, y = 0) down to the bottom.
        assert.ok(Math.abs(bar.position.y - bottom / 2) < 1e-12);
        assert.ok(Math.abs(bar.userData.bracketLength + bottom) < 1e-12);
    }
    assert.ok(Math.abs(horizontal.position.y - bottom) < 1e-12);
    assert.ok(Math.abs(horizontal.userData.bracketLength - (1 - earth - moon)) < 1e-12);
    assert.equal(scene.getObjectByName('Earth').userData.bodyLabel, 'Earth');
    assert.equal(scene.getObjectByName('Moon').userData.bodyLabel, 'Moon');
});

test('bracket works when the larger body is listed second and skips missing nodes', () => {
    const scene = diagram(['Earth', 0.5, 0.001], ['Sun', -0.5, 0.05]);
    addDistanceBracket(scene, { bodies: ['Earth', 'Sun'] });
    const xs = scene.getObjectByName('distance-bracket').children
        .filter(bar => bar.userData.bracketAxis === 'y').map(bar => bar.position.x).sort((a, b) => a - b);
    assert.deepEqual(xs.map(x => Number(x.toFixed(6))), [-0.45, 0.499]);
    const missing = diagram(['Earth', -0.5, 0.01], ['Moon', 0.5, 0.01]);
    addDistanceBracket(missing, { bodies: ['Earth', 'Mars'] });
    assert.equal(missing.getObjectByName('distance-bracket'), undefined);
});
