const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

class Element {
    constructor(parent = null) {
        this.parent = parent;
        this.style = { touchAction: 'auto', userSelect: '' };
        this.listeners = new Map();
        this.classes = new Set();
        this.captured = new Set();
    }
    addEventListener(name, listener) {
        const values = this.listeners.get(name) || new Set();
        values.add(listener);
        this.listeners.set(name, values);
    }
    removeEventListener(name, listener) { this.listeners.get(name)?.delete(listener); }
    setPointerCapture(id) { this.captured.add(id); }
    hasPointerCapture(id) { return this.captured.has(id); }
    releasePointerCapture(id) { this.captured.delete(id); }
    closest(selector) {
        return this.isControl && selector.includes(this.controlSelector) ? this : this.parent?.closest(selector) || null;
    }
    classList = {
        add: name => this.classes.add(name),
        remove: (...names) => names.forEach(name => this.classes.delete(name)),
        toggle: (name, value) => value ? this.classes.add(name) : this.classes.delete(name)
    };
    fire(type, properties = {}) {
        const event = {
            type, pointerId: 1, pointerType: 'touch', button: 0,
            clientX: 0, clientY: 0, timeStamp: 0, target: this,
            preventDefault() { this.defaultPrevented = true; },
            ...properties
        };
        for (const listener of this.listeners.get(type) || []) listener(event);
        return event;
    }
}

const spatialSource = fs.readFileSync(path.join(__dirname, '../js/experiences/spatial.js'), 'utf8');
const context = vm.createContext({
    ScaleControls: { svg() {}, dom() {}, Slider() {}, number() {}, button() {} },
    ScaleMath: { log() {}, power() {}, clamp(value) { return value; }, countCluster() {} },
    ScaleRenderers: {}
});
vm.runInContext(spatialSource, context);
const createSpatialInput = context.ScaleRenderers.createSpatialInput;

test('model-ready listener cleanup stays with the spatial renderer that owns it', () => {
    const navigationSource = spatialSource.match(/function navigation\([\s\S]*?\n    }\n    R\.spatial/)[0];
    const spatialRendererSource = spatialSource.match(/R\.spatial = ctx => \{[\s\S]*?\n    \};\n    function board/)[0];
    assert.doesNotMatch(navigationSource, /attachModels|scale-models-ready/);
    assert.match(spatialRendererSource, /addEventListener\('scale-models-ready', attachModels\)/);
    assert.match(spatialRendererSource, /removeEventListener\('scale-models-ready',\s*attachModels\)/);
    assert.match(spatialSource, /R\.counts = ctx => \{[\s\S]*?navigation\(ctx,[\s\S]*?dispose:[\s\S]*?nav\.dispose\(\)/);
});

test('captures the initiating pointer immediately and ignores other pointer identities', () => {
    const element = new Element();
    const pans = [];
    createSpatialInput(element, { onPan: (dx, dy) => pans.push([dx, dy]) });
    const down = element.fire('pointerdown', { pointerId: 7, pointerType: 'mouse' });
    assert.equal(element.hasPointerCapture(7), true);
    assert.equal(down.defaultPrevented, true);
    element.fire('pointermove', { pointerId: 8, clientX: 100 });
    element.fire('pointermove', { pointerId: 7, clientX: 12, clientY: 4, timeStamp: 16 });
    assert.deepEqual(pans, [[12, 4]]);
});

test('start hook runs once before movement, including for model rotation', () => {
    const element = new Element();
    let cameraMoving = true;
    let starts = 0;
    createSpatialInput(element, {
        onStart: () => { starts++; cameraMoving = false; },
        interaction: { pick: () => ({}) }
    });
    element.fire('pointerdown', { pointerId: 1 });
    element.fire('pointerdown', { pointerId: 2 });
    assert.equal(starts, 1);
    assert.equal(cameraMoving, false);
});

test('touch movement reaches the immediate pan callback in CSS pixels without hover', () => {
    const element = new Element();
    const values = [];
    const hovers = [];
    let exponent = 0;
    createSpatialInput(element, {
        onPan: dx => { exponent -= dx * 0.0012; values.push(exponent); },
        interaction: { hover: (...args) => hovers.push(args) }
    });
    element.fire('pointerdown', { clientX: 20, clientY: 10, timeStamp: 0 });
    element.fire('pointermove', { clientX: 30, clientY: 22, timeStamp: 16 });
    assert.equal(values.length, 1);
    assert.ok(Math.abs(values[0] + 0.012) < 1e-12);
    assert.ok(hovers.every(([item, pointer]) => item === null && pointer === null));
});

test('a vertical touch drag rotates a picked model synchronously', () => {
    const element = new Element();
    const rotations = [];
    const item = {};
    createSpatialInput(element, {
        interaction: {
            pick: () => item,
            rotate: (...args) => rotations.push(args)
        }
    });
    element.fire('pointerdown', { clientX: 8, clientY: 12, timeStamp: 0 });
    element.fire('pointermove', { clientX: 8, clientY: 31, timeStamp: 16 });
    assert.equal(rotations.length, 1);
    assert.equal(rotations[0][0], item);
    assert.equal(rotations[0][1], 0);
    assert.equal(rotations[0][2], 19);
});

test('pointer cancellation ends the gesture without camera momentum and releases capture', () => {
    const element = new Element();
    const endings = [];
    const input = createSpatialInput(element, { onPan() {}, onEnd: (...args) => endings.push(args) });
    element.fire('pointerdown', { pointerId: 4, timeStamp: 0 });
    element.fire('pointermove', { pointerId: 4, clientX: 30, timeStamp: 10 });
    element.fire('pointercancel', { pointerId: 4, timeStamp: 20 });
    assert.equal(element.hasPointerCapture(4), false);
    assert.equal(element.classes.has('is-dragging'), false);
    assert.equal(endings.length, 1);
    assert.equal(endings[0][0], 0);
    assert.equal(endings[0][2], true);
    assert.equal(input.consumeDraggedClick(), true);
});

test('native controls, including nested fullscreen buttons, are left to their own input', () => {
    for (const selector of ['button', 'input', 'select', 'textarea', 'option', 'a', '[contenteditable="true"]', '[role="button"]', '.experience-camera-slider']) {
        const element = new Element();
        const control = new Element(element);
        control.isControl = true;
        control.controlSelector = selector;
        const input = createSpatialInput(element, { onPan() {} });
        assert.equal(input.isControlTarget(control), true, selector);
        const down = element.fire('pointerdown', { target: control, pointerId: 2 });
        assert.equal(down.defaultPrevented, undefined, selector);
        assert.equal(element.hasPointerCapture(2), false, selector);
        input.dispose();
    }
});

test('disposal removes handlers and restores inline interaction styles', () => {
    const element = new Element();
    let ends = 0;
    const input = createSpatialInput(element, { onEnd: () => ends++ });
    assert.equal(element.style.touchAction, 'none');
    element.fire('pointerdown');
    input.dispose();
    assert.equal(element.style.touchAction, 'auto');
    assert.equal(element.classes.has('is-dragging'), false);
    assert.equal(ends, 1);
    element.fire('pointerdown');
    assert.equal(element.hasPointerCapture(1), false);
});
