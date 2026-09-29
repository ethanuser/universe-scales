import assert from 'node:assert/strict';
import test from 'node:test';
import { proceduralScene } from '../js/experiences/procedural-models.js';
import { layoutModelLabels } from '../js/experiences/model-labels.js';

test('hair has outward-facing skin and closed, oppositely oriented cuts', () => {
    const scene = proceduralScene('hair-fiber');
    const skin = scene.children[0], positions = skin.geometry.getAttribute('position');
    const normals = skin.geometry.getAttribute('normal');
    for (let index = 0; index < positions.count; index += 97)
        assert.ok(positions.getX(index) * normals.getX(index) + positions.getZ(index) * normals.getZ(index) > 0);
    for (const [name, sign] of [['hair-top-cut', 1], ['hair-bottom-cut', -1]]) {
        const cap = scene.getObjectByName(name);
        assert.ok(cap);
        const points = cap.geometry.getAttribute('position'), normal = cap.geometry.getAttribute('normal');
        for (let index = 0; index < points.count; index++) {
            assert.equal(points.getY(index), sign);
            assert.ok(normal.getY(index) * sign > 0.999);
        }
        const bodyRow = sign > 0 ? positions.count - 97 : 0;
        for (let column = 0; column < 96; column++) {
            assert.equal(points.getX(column + 1), positions.getX(bodyRow + column));
            assert.equal(points.getZ(column + 1), positions.getZ(bodyRow + column));
        }
    }
    assert.ok(scene.children.reduce((sum, mesh) => sum + mesh.geometry.index.count / 3, 0) < 50000);
});

test('clustered planetary labels remain separated inside the viewport', () => {
    const names = ['Sun', 'Mercury', 'Venus', 'Earth', 'Mars', 'Asteroid belt', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'];
    const labels = layoutModelLabels(names.map(text => ({ text, x: 500, y: 250 })),
        { left: 0, right: 1000, top: 0, bottom: 460 });
    for (let index = 0; index < labels.length; index++) {
        const a = labels[index].box;
        assert.ok(a.left >= 0 && a.right <= 1000 && a.top >= 0 && a.bottom <= 460);
        for (const other of labels.slice(index + 1)) {
            const b = other.box;
            assert.ok(a.right < b.left || b.right < a.left || a.bottom < b.top || b.bottom < a.top);
        }
    }
});

test('solar system has planet labels and a bounded main asteroid belt', () => {
    const scene = proceduralScene('solar-system');
    const labels = [];
    scene.traverse(node => { if (node.userData.label) labels.push(node.userData.label); });
    assert.ok(['Sun', 'Earth', 'Neptune', 'Pluto', 'Asteroid belt'].every(name => labels.includes(name)));
    const belt = scene.getObjectByName('Main asteroid belt').geometry.getAttribute('position');
    for (let index = 0; index < belt.count; index++) {
        const radius = Math.hypot(belt.getX(index), belt.getZ(index));
        assert.ok(radius >= 2.1 && radius <= 3.3);
    }
});
