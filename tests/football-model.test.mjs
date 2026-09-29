import assert from 'node:assert/strict';
import test from 'node:test';
import { FOOTBALL_FIELD, footballFieldScene } from '../js/experiences/football-model.js';

function mesh(scene, name) {
    const result = scene.getObjectByName(name);
    assert.ok(result, `missing ${name}`);
    return result;
}

test('NFL field uses the requested goal-to-goal and overall dimensions', () => {
    const scene = footballFieldScene();
    assert.equal(FOOTBALL_FIELD.playingLength, 100);
    assert.equal(FOOTBALL_FIELD.endZoneLength, 10);
    assert.equal(FOOTBALL_FIELD.fullLength, 120);
    assert.equal(FOOTBALL_FIELD.width, 160 / 3);
    assert.deepEqual(scene.userData.dimensions, FOOTBALL_FIELD);
    for (const [name, expectedX, expectedZ] of [
        ['turf-substrate', 120, 160 / 3],
        ['end-line-west', 1 / 9, 160 / 3],
        ['end-line-east', 1 / 9, 160 / 3]
    ]) {
        const object = mesh(scene, name);
        assert.ok(Math.abs(object.geometry.parameters.width - expectedX) < 1e-12);
        assert.ok(Math.abs(object.geometry.parameters.depth - expectedZ) < 1e-12);
    }
    assert.ok(mesh(scene, 'turf-substrate').geometry.parameters.height < 0.04,
        'turf underlay remains a thin turf edge, not a deep block');
});

test('five-yard lines and NFL hashes have correct spacing, gap, and scale', () => {
    const scene = footballFieldScene();
    const lines = [];
    for (let yard = -50; yard <= 50; yard += 5) {
        const line = mesh(scene, `yard-line-${yard}`);
        assert.equal(line.position.x, yard);
        lines.push(line.position.x);
    }
    assert.deepEqual(lines, Array.from({ length: 21 }, (_, index) => -50 + index * 5));
    assert.ok(Math.abs(mesh(scene, 'yard-line-0').geometry.parameters.width - 1 / 9) < 1e-12,
        'ordinary painted stripes are four inches wide');

    const nearOuter = mesh(scene, 'hash-1-near-1');
    const nearInner = mesh(scene, 'hash-1-near-2');
    const farOuter = mesh(scene, 'hash-1-far-1');
    const nearInboundEdge = nearOuter.position.z + FOOTBALL_FIELD.hashWidth / 2;
    const farInboundEdge = farOuter.position.z - FOOTBALL_FIELD.hashWidth / 2;
    assert.ok(Math.abs(nearInboundEdge - (-FOOTBALL_FIELD.width / 2 + FOOTBALL_FIELD.hashFromSideline)) < 1e-12);
    assert.ok(Math.abs(farInboundEdge - (FOOTBALL_FIELD.width / 2 - FOOTBALL_FIELD.hashFromSideline)) < 1e-12);
    assert.ok(Math.abs(Math.abs(nearOuter.position.z - nearInner.position.z) - 18.5 / 3) < 1e-12);
    assert.ok(Math.abs(nearOuter.geometry.parameters.width - 2 / 3) < 1e-12,
        'hash is two feet long along the field');
    assert.equal(mesh(scene, 'hash-1-near-1').position.x, 1);
    assert.equal(mesh(scene, 'hash-2-near-1').position.x, 2);
    assert.ok(mesh(scene, 'sideline-tick-1-near'));
});

test('yard numbers face both sidelines at each correct yard line', () => {
    const scene = footballFieldScene();
    for (const yard of [10, 20, 30, 40]) {
        for (const end of [-1, 1]) for (const side of [-1, 1]) {
            const name = `yard-number-${yard}-${side < 0 ? 'near' : 'far'}`;
            const matches = [];
            scene.traverse(node => { if (node.name === name && Math.abs(node.position.x - end * (50 - yard)) < 1e-12) matches.push(node); });
            assert.equal(matches.length, 1, `${yard} at end ${end}, side ${side}`);
            assert.equal(matches[0].userData.number, String(yard));
            assert.equal(matches[0].userData.side, side);
            assert.ok(Math.abs(Math.abs(matches[0].position.z) - (FOOTBALL_FIELD.width / 2 - 13)) < 1e-12);
        }
    }
    for (const side of [-1, 1]) {
        const midfield = mesh(scene, `yard-number-50-${side < 0 ? 'near' : 'far'}`);
        assert.ok(Math.abs(midfield.position.x) < 1e-12);
    }
});

test('goalposts align with the end-line plane and NFL crossbar dimensions', () => {
    const scene = footballFieldScene();
    for (const end of [-1, 1]) {
        const direction = end < 0 ? 'west' : 'east';
        const crossbar = mesh(scene, `goalpost-crossbar-${direction}`);
        assert.ok(Math.abs(crossbar.position.x - end * 60) < 1e-12);
        assert.ok(Math.abs(crossbar.position.y - 10 / 3) < 1e-12);
        assert.ok(Math.abs(crossbar.geometry.parameters.height - 18.5 / 3) < 1e-12);
        const near = mesh(scene, `goalpost-upright-${direction}-near`);
        const far = mesh(scene, `goalpost-upright-${direction}-far`);
        assert.ok(Math.abs(near.geometry.parameters.radiusTop * 2 - 3 / 36) < 1e-12,
            'uprights use the NFL minimum three-inch diameter');
        assert.ok(Math.abs(Math.abs(near.position.z - far.position.z) - 18.5 / 3) < 1e-12);
        assert.ok(Math.abs((near.position.y + near.geometry.parameters.height / 2) - 15) < 1e-12,
            'uprights extend 35 feet above the 10-foot crossbar');
        assert.ok(mesh(scene, `goalpost-stem-${direction}`).position.x * end > 60);
    }
});
