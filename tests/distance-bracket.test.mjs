// Model decorations built with the real vendored three.js.
import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from '../js/vendor/three/three.module.min.js';
import { BRACKET_DROP, addDistanceBracket, planetPositions }
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

test('bracket touches the facing limbs and lies below both bodies', () => {
    const earth = 6_371_000 / 384_400_000, moon = 1_737_500 / 384_400_000;
    const scene = diagram(['Earth', -0.5, earth], ['Moon', 0.5, moon]);
    addDistanceBracket(scene, { bodies: ['Earth', 'Moon'] });
    const lines = scene.getObjectByName('distance-bracket').children;
    const vertical = lines.filter(line => line.userData.screenLine.axis === 'y')
        .sort((a, b) => a.position.x - b.position.x);
    const [horizontal] = lines.filter(line => line.userData.screenLine.axis === 'x');
    const bottom = -(earth + BRACKET_DROP);
    for (const [line, x] of [[vertical[0], -0.5 + earth], [vertical[1], 0.5 - moon]]) {
        assert.ok(close(line.position.x, x));
        assert.ok(close(line.position.y + line.userData.screenLine.length / 2, 0));
        assert.ok(close(line.position.y - line.userData.screenLine.length / 2, bottom));
    }
    assert.ok(close(horizontal.position.y, bottom));
    assert.ok(close(horizontal.userData.screenLine.length, 1 - earth - moon));
    for (const name of ['Earth', 'Moon'])
        assert.deepEqual(scene.getObjectByName(name).userData, { label: name, sphere: true });
});

test('bracket skips diagrams whose named bodies are missing', () => {
    const scene = diagram(['Earth', -0.5, 0.01], ['Moon', 0.5, 0.01]);
    addDistanceBracket(scene, { bodies: ['Earth', 'Mars'] });
    assert.equal(scene.getObjectByName('distance-bracket'), undefined);
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
