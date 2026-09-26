const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../js/experiences/models.js'), 'utf8')
    .replace(/^import .*;\n/gm, '');
let now = 0;
let nextFrame;
const context = {
    THREE: {
        MathUtils: { clamp: (value, low, high) => Math.max(low, Math.min(high, value)) },
        Vector3: class {
            set(x, y, z) { this.x = x; this.y = y; this.z = z; return this; }
            clone() { return new this.constructor().set(this.x, this.y, this.z); }
            applyMatrix4() { return this; }
            getComponent(axis) { return [this.x, this.y, this.z][axis]; }
            fromBufferAttribute(attribute, index) { return this.set(...attribute.vertices[index]); }
        }
    },
    GLTFLoader: class {},
    clone: value => value,
    fetch: async () => ({ ok: false }),
    window: { dispatchEvent() {} },
    Event: class {},
    performance: { now: () => now },
    requestAnimationFrame: callback => { nextFrame = callback; return 1; },
    cancelAnimationFrame() {}
};
vm.runInNewContext(`${source}\nwindow.__sampledModelPoints = sampledModelPoints;`, context);

test('released model coasts briefly before returning near its starting pose', () => {
    const stage = Object.create(context.window.ScaleModels.ModelStage.prototype);
    stage.rotations = new Map();
    stage.redraw = () => {};
    const item = {};
    stage.beginRotate(item);
    for (let step = 0; step < 8; step++) {
        now += 16;
        stage.rotate(item, 5, 2);
    }
    stage.releaseRotate(item);
    const state = stage.rotations.get(item);
    const releasedYaw = state.yaw;
    assert.ok(state.velocity > 0);
    for (let frame = 0; frame < 8; frame++) {
        const callback = nextFrame;
        assert.ok(callback);
        now += 16;
        callback(now);
    }
    assert.ok(state.yaw > releasedYaw, 'the model should keep turning just after release');
    let mostNegativeYaw = 0;
    for (let frame = 0; frame < 360 && nextFrame; frame++) {
        const callback = nextFrame;
        nextFrame = null;
        now += 16;
        callback(now);
        mostNegativeYaw = Math.min(mostNegativeYaw, state.yaw);
    }
    assert.ok(mostNegativeYaw > -0.25, `the return should not swing far past front: ${mostNegativeYaw}`);
    assert.ok(Math.abs(state.yaw) < 0.01);
    assert.ok(Math.abs(state.pitch) < 0.01);
});

test('release travel scales with the speed of the flick', () => {
    function coast(dx) {
        nextFrame = null;
        const stage = Object.create(context.window.ScaleModels.ModelStage.prototype);
        stage.rotations = new Map();
        stage.redraw = () => {};
        const item = {};
        stage.beginRotate(item);
        for (let step = 0; step < 6; step++) {
            now += 16;
            stage.rotate(item, dx);
        }
        stage.releaseRotate(item);
        const state = stage.rotations.get(item);
        const releaseYaw = state.yaw;
        const releaseVelocity = state.velocity;
        let peakTravel = 0;
        for (let frame = 0; frame < 25; frame++) {
            const callback = nextFrame;
            nextFrame = null;
            now += 16;
            callback(now);
            peakTravel = Math.max(peakTravel, state.yaw - releaseYaw);
        }
        return { peakTravel, releaseVelocity };
    }
    const slow = coast(2);
    const fast = coast(12);
    assert.ok(fast.releaseVelocity > slow.releaseVelocity * 3);
    assert.ok(fast.peakTravel > 0.35);
    assert.ok(fast.peakTravel > slow.peakTravel * 3);
});

test('a fast flick settles near its front pose without prolonged oscillation', () => {
    nextFrame = null;
    const stage = Object.create(context.window.ScaleModels.ModelStage.prototype);
    stage.rotations = new Map();
    stage.redraw = () => {};
    const item = {};
    stage.beginRotate(item);
    for (let step = 0; step < 6; step++) {
        now += 16;
        stage.rotate(item, 12);
    }
    stage.releaseRotate(item);
    const state = stage.rotations.get(item);
    let crossings = 0;
    let previousSign = Math.sign(state.yaw);
    for (let frame = 0; frame < 125; frame++) {
        const callback = nextFrame;
        nextFrame = null;
        now += 16;
        callback(now);
        const sign = Math.sign(state.yaw);
        if (sign && sign !== previousSign) crossings++;
        if (sign) previousSign = sign;
    }
    assert.ok(Math.abs(state.yaw) < 0.05, `still rotated after two seconds: ${state.yaw}`);
    assert.ok(crossings <= 1, `crossed the rest pose ${crossings} times`);
});

test('vertical drag reaches both 90-degree viewing limits', () => {
    const stage = Object.create(context.window.ScaleModels.ModelStage.prototype);
    stage.rotations = new Map();
    stage.redraw = () => {};
    const item = {};
    stage.beginRotate(item);
    now += 16;
    stage.rotate(item, 0, 1000);
    assert.equal(stage.rotations.get(item).pitch, Math.PI / 2);
    now += 16;
    stage.rotate(item, 0, -1000);
    assert.equal(stage.rotations.get(item).pitch, -Math.PI / 2);
});

test('model hover turns off as soon as rotation begins', () => {
    const stage = Object.create(context.window.ScaleModels.ModelStage.prototype);
    stage.rotations = new Map();
    let redraws = 0;
    stage.redraw = () => { redraws++; };
    const item = {};
    stage.setHover(item);
    stage.setHover(item);
    assert.equal(redraws, 1);
    stage.beginRotate(item);
    assert.equal(stage.hovered, null);
    assert.equal(redraws, 2);
});

test('projected convex hull is also the model picking boundary', () => {
    const { convexHull, insideHull, ModelStage } = context.window.ScaleModels;
    const polygon = convexHull([
        { x: 10, y: 10 }, { x: 90, y: 10 }, { x: 90, y: 90 },
        { x: 10, y: 90 }, { x: 50, y: 50 }
    ]);
    assert.equal(polygon.length, 4);
    assert.equal(insideHull({ x: 50, y: 50 }, polygon), true);
    assert.equal(insideHull({ x: 95, y: 50 }, polygon), false);
    const stage = Object.create(ModelStage.prototype);
    const item = {};
    stage.renderer = { domElement: { getBoundingClientRect: () => ({
        left: 100, top: 200, right: 200, bottom: 300, width: 100, height: 100
    }) } };
    stage.hulls = new Map([[item, { item, polygon, depth: 0 }]]);
    assert.equal(stage.pick(150, 250), item);
    stage.hulls.clear();
    assert.equal(stage.pick(150, 250), null);
});

test('skinned model hull uses posed vertices rather than bind-pose positions', () => {
    const position = { count: 2, vertices: [[-1, 0, 0], [1, 0, 0]] };
    const child = {
        isMesh: true,
        geometry: { getAttribute: () => position },
        matrixWorld: {},
        getVertexPosition(index, point) { return point.set(10 + index * 2, 0, 0); }
    };
    const instance = {
        updateMatrixWorld() {},
        traverse(callback) { callback(child); },
        matrixWorld: { clone: () => ({ invert: () => ({}) }) }
    };
    const points = context.window.__sampledModelPoints(instance);
    assert.deepEqual([...new Set(points.map(point => point.x))], [10, 12]);
});
