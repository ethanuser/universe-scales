import assert from 'node:assert/strict';
import test from 'node:test';
import { proceduralScene } from '../js/experiences/procedural-models.js';
import { placeLabels } from '../js/experiences/model-labels.js';

test('hair has outward-facing skin and closed, oppositely oriented cuts', () => {
    const scene = proceduralScene('hair-fiber');
    const skin = scene.children[0], positions = skin.geometry.getAttribute('position');
    const normals = skin.geometry.getAttribute('normal');
    assert.ok(skin.material.isMeshPhysicalMaterial);
    assert.equal(skin.material.transparent, false);
    assert.ok(skin.material.anisotropy > 0, 'hair sheen should follow the shaft');
    const colors = skin.geometry.getAttribute('color');
    const red = Array.from({ length: colors.count }, (_, index) => colors.getX(index));
    assert.ok(Math.max(...red) / Math.min(...red) < 1.08, 'cuticles should not look like painted stripes');
    skin.geometry.computeBoundingBox();
    const half = skin.geometry.boundingBox.max.y;
    for (let index = 0; index < positions.count; index += 97)
        assert.ok(positions.getX(index) * normals.getX(index) + positions.getZ(index) * normals.getZ(index) > 0);
    for (const [name, sign] of [['hair-top-cut', 1], ['hair-bottom-cut', -1]]) {
        const cap = scene.getObjectByName(name);
        assert.ok(cap);
        const points = cap.geometry.getAttribute('position'), normal = cap.geometry.getAttribute('normal');
        for (let index = 0; index < points.count; index++) {
            assert.ok(Math.abs(points.getY(index) - sign * half) < 1e-6);
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

test('planet labels stay put and hide by priority instead of moving', () => {
    const viewport = { left: 0, right: 1000, top: 0, bottom: 460 };
    const names = ['Sun', 'Mercury', 'Venus', 'Earth', 'Mars'];
    const clustered = placeLabels(names.map((text, index) => ({ text, x: 500 + index, y: 250, priority: index })), viewport);
    // Every label keeps its fixed offset above its own anchor.
    for (const label of clustered) assert.equal(label.labelY, 250 - 6);
    const visible = clustered.filter(label => label.visible);
    assert.deepEqual(visible.map(label => label.text), ['Sun']);
    // Spread out, all are visible; nudging the anchors moves labels by the same amount.
    const spread = placeLabels(names.map((text, index) => ({ text, x: 100 + index * 150, y: 250 })), viewport);
    assert.ok(spread.every(label => label.visible));
    const nudged = placeLabels(names.map((text, index) => ({ text, x: 103 + index * 150, y: 251 })), viewport);
    nudged.forEach((label, index) => assert.equal(label.labelX - spread[index].labelX, 3));
    for (let index = 0; index < spread.length; index++)
        for (const other of spread.slice(index + 1))
            assert.ok(spread[index].box.right < other.box.left || other.box.right < spread[index].box.left);
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

test('fixed callouts keep their offset and follow their anchor without reflow', () => {
    const viewport = { left: 0, right: 1000, top: 0, bottom: 460 };
    const labels = [{ text: 'Milky Way', x: 500, y: 250, callout: { x: -70, y: -20 } },
        { text: 'LMC', x: 500, y: 250, callout: { x: -100, y: 40 } }];
    const placed = placeLabels(labels, viewport);
    assert.ok(placed.every(label => label.visible));
    assert.equal(placed[0].labelX, 430);
    assert.equal(placed[0].labelY, 230);
    const moved = placeLabels(labels.map(label => ({ ...label, x: label.x + 5 })), viewport);
    moved.forEach((label, index) => assert.equal(label.labelX - placed[index].labelX, 5));
});
