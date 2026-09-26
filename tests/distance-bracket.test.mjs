// Model decorations built with the real vendored three.js.
import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from '../js/vendor/three/three.module.min.js';
import { BRACKET_DROP, HYDROGEN_95_RADIUS, addDistanceBracket, planetPositions, proceduralScene }
    from '../js/experiences/procedural-models.js';

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
const close = (a, b) => Math.abs(a - b) < 1e-12;

test('bracket marks center-to-center distance below both bodies', () => {
    const earth = 6_371_000 / 384_400_000, moon = 1_737_500 / 384_400_000;
    const scene = diagram(['Earth', -0.5, earth], ['Moon', 0.5, moon]);
    addDistanceBracket(scene, { bodies: ['Earth', 'Moon'] });
    const lines = scene.getObjectByName('distance-bracket').children;
    const vertical = lines.filter(line => line.userData.screenLine.axis === 'y')
        .sort((a, b) => a.position.x - b.position.x);
    const [horizontal] = lines.filter(line => line.userData.screenLine.axis === 'x');
    const bottom = -(earth + BRACKET_DROP);
    for (const [line, x, radius] of [[vertical[0], -0.5, earth], [vertical[1], 0.5, moon]]) {
        // Each line starts at the bottom of its body, directly below the center.
        assert.ok(close(line.position.x, x));
        assert.ok(close(line.position.y + line.userData.screenLine.length / 2, -radius));
        assert.ok(close(line.position.y - line.userData.screenLine.length / 2, bottom));
    }
    assert.ok(close(horizontal.position.y, bottom));
    assert.ok(close(horizontal.userData.screenLine.length, 1));
    for (const name of ['Earth', 'Moon'])
        assert.deepEqual(scene.getObjectByName(name).userData, { label: name, outline: true, sphere: true });
});

test('bracket skips diagrams whose named bodies are missing', () => {
    const scene = diagram(['Earth', -0.5, 0.01], ['Moon', 0.5, 0.01]);
    addDistanceBracket(scene, { bodies: ['Earth', 'Mars'] });
    assert.equal(scene.getObjectByName('distance-bracket'), undefined);
});

test('hydrogen dots stop at the 95% boundary sphere', () => {
    const scene = proceduralScene('hydrogen-1s');
    const cloud = scene.children.find(child => child.isPoints);
    const position = cloud.geometry.getAttribute('position');
    let outside = 0;
    for (let index = 0; index < position.count; index++)
        if (new THREE.Vector3().fromBufferAttribute(position, index).length() > HYDROGEN_95_RADIUS + 1e-9) outside++;
    assert.equal(outside, 0);
    // 1 - e^(-2r)(1 + 2r + 2r^2) at the boundary radius.
    const r = HYDROGEN_95_RADIUS;
    assert.ok(Math.abs(1 - Math.exp(-2 * r) * (1 + 2 * r + 2 * r * r) - 0.95) < 1e-4);
});

test('planet positions match known heliocentric distances', () => {
    const at = date => Object.fromEntries(planetPositions(new Date(date))
        .map(({ name, position }) => [name, Math.hypot(...position)]));
    // Earth is near perihelion in early January and aphelion in early July.
    assert.ok(Math.abs(at('2026-01-03T12:00:00Z').Earth - 0.9833) < 0.001);
    assert.ok(Math.abs(at('2026-07-06T12:00:00Z').Earth - 1.0167) < 0.001);
    const today = at('2026-09-26T00:00:00Z');
    assert.ok(today.Mercury > 0.30 && today.Mercury < 0.47);
    assert.ok(today.Neptune > 29.7 && today.Neptune < 30.4);
});
