import assert from 'node:assert/strict';
import test from 'node:test';
import { labelVisibility } from '../js/experiences/model-labels.js';

test('an enlarged annotation cannot cover the selected item name', () => {
    const visible = labelVisibility([
        { index: 0, priority: 10, left: 180, right: 780, top: 350, bottom: 374 },
        { index: 1, priority: 200, left: 545, right: 660, top: 332, bottom: 377 },
        { index: 2, priority: 10, left: 840, right: 1060, top: 75, bottom: 98 }
    ]);
    assert.deepEqual([...visible].sort(), [1, 2]);
});

test('labels retain stable anchors, with selection winning conflicts between names', () => {
    const boxes = [
        { index: 0, priority: 100, left: 10, right: 70, top: 40, bottom: 60 },
        { index: 1, priority: 200, left: 65, right: 120, top: 40, bottom: 60 },
        { index: 2, priority: 100, left: 140, right: 190, top: 40, bottom: 60 }
    ];
    const original = structuredClone(boxes);
    assert.deepEqual([...labelVisibility(boxes)].sort(), [1, 2]);
    assert.deepEqual(boxes, original);
});
