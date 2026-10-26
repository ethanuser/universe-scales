const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../js/experiences/journey.js'), 'utf8');
const sandbox = { globalThis: {}, module: { exports: {} } };
sandbox.globalThis = sandbox;
vm.runInNewContext(source, sandbox);
const { radialLayout, radialPlacement, radialFocus, RADIAL_SIZE } = sandbox.module.exports;
const { radialReturnPan } = sandbox.module.exports;

// A realistic spread: ~4 items per decade over 60 decades, with repeats and wide objects.
const items = [];
for (let i = 0; i < 240; i++) items.push({ name: `Item number ${i}`, value: 10 ** (-35 + i * 0.25 + 0.1 * Math.sin(i)) });
items.push({ name: 'Twin A', value: 8e-4 }, { name: 'Twin B', value: 8e-4 });
const widthFactor = item => (item.name.endsWith('7') ? 2.4 : 1);

test('radial placement is deterministic and keeps smaller objects nearer the center', () => {
    const a = radialPlacement(items, 1, { width: 1000, widthFactor });
    const b = radialPlacement(items.map(item => ({ ...item })), 1, { width: 1000, widthFactor });
    assert.deepEqual(a, b);
    const entries = radialLayout(items, -3, 1, { width: 1000, widthFactor });
    const near = entries.filter(e => e.item.value < 1e-4 && e.item.value > 1e-6);
    const far = entries.filter(e => e.item.value > 1e-2 && e.item.value < 1);
    const radius = e => Math.hypot(e.x - 500, e.center - 250);
    assert.ok(Math.max(...near.map(radius)) < Math.min(...far.map(radius)));
});

test('objects within a factor of 60 in size never overlap (boxes include labels)', () => {
    for (const exponent of [-10, -3.1, 0, 7.4, 21]) {
        const entries = radialLayout(items, exponent, 1, { width: 1000, widthFactor });
        const shown = entries.filter(e => e.size > 4 && e.size < 4000);
        for (let i = 0; i < shown.length; i++) for (let j = i + 1; j < shown.length; j++) {
            const [a, b] = [shown[i], shown[j]];
            if (Math.max(a.size, b.size) / Math.min(a.size, b.size) > 60) continue;
            const apart = a.rightEdge <= b.leftEdge || b.rightEdge <= a.leftEdge ||
                a.center + a.size * 0.5 <= b.center - b.size * 0.5 || b.center + b.size * 0.5 <= a.center - a.size * 0.5;
            assert.ok(apart, `${a.item.name} overlaps ${b.item.name} at zoom ${exponent}`);
        }
    }
});

test('the camera only zooms: screen radius scales with drawn size, focus follows the scale', () => {
    const one = radialLayout(items, 0, 1, { width: 1000 });
    const two = radialLayout(items, 1, 1, { width: 1000 });
    const k = 120;
    const ratio = Math.hypot(one[k].x - 500, one[k].center - 250) / Math.hypot(two[k].x - 500, two[k].center - 250);
    assert.ok(Math.abs(ratio - 10) < 1e-6);
    assert.ok(Math.abs(one[k].size / two[k].size - 10) < 1e-6);
    const index = radialFocus(items, Math.log10(items[150].value), 1, 1);
    assert.equal(index, 150);
    assert.ok(RADIAL_SIZE > 0);
});

test('prepared radial placement reuses dimensions without repeating registry lookups', () => {
    const options = { width: 1000, widthFactor, extentFactor: item => item === items[0] ? 1.2 : 1 };
    const placement = radialPlacement(items, 1, options);
    const expected = radialLayout(items, -3, 1, options);
    const actual = radialLayout(items, -3, 1, { width: 1000, placement,
        widthFactor() { throw new Error('presentation must already be prepared'); },
        extentFactor() { throw new Error('presentation must already be prepared'); } });
    assert.deepEqual(actual, expected);
});

test('inward zoom returns the origin monotonically in screen space and reaches exactly zero', () => {
    for (const exponent of [-35, -6, 7, 25]) {
        const point = { x: 1.8 * 10 ** exponent, y: -0.7 * 10 ** exponent };
        let lastDistance = Infinity;
        for (let step = 0; step <= 120; step++) {
            const current = exponent - step / 100;
            const pan = radialReturnPan(point, current, exponent);
            const distance = Math.hypot(pan.x, pan.y) * RADIAL_SIZE / 10 ** current;
            assert.ok(distance <= lastDistance + 1e-8, `origin moves away at ${current}`);
            lastDistance = distance;
            if (step >= 100) assert.deepEqual({ ...pan }, { x: 0, y: 0 });
        }
        assert.deepEqual({ ...radialReturnPan(point, exponent + 5, exponent) }, point);
    }
});

test('origin return is continuous at the selected scale and the end of its return', () => {
    const point = { x: 15, y: -23 }, epsilon = 1e-8;
    const start = radialReturnPan(point, 2 - epsilon, 2);
    const end = radialReturnPan(point, 1 + epsilon, 2);
    assert.ok(Math.hypot(start.x - point.x, start.y - point.y) < 1e-5);
    assert.ok(Math.hypot(end.x, end.y) < 1e-10);
});

test('a pan to an item\'s world point centers that item and shifts everything equally', () => {
    const placement = radialPlacement(items, 1, { width: 1000 });
    const k = 120, exponent = Math.log10(items[k].value);
    const pan = { x: placement[k].u * placement[k].length, y: placement[k].v * placement[k].length };
    const still = radialLayout(items, exponent, 1, { width: 1000, placement });
    const moved = radialLayout(items, exponent, 1, { width: 1000, placement, pan });
    assert.ok(Math.abs(moved[k].x - 500) < 1e-6 && Math.abs(moved[k].center - 250) < 1e-6);
    const dx = moved[110].x - still[110].x, dy = moved[110].center - still[110].center;
    for (const index of [100, 116, 124])
        assert.ok(Math.abs(moved[index].x - still[index].x - dx) < 1e-6 && Math.abs(moved[index].center - still[index].center - dy) < 1e-6);
});
