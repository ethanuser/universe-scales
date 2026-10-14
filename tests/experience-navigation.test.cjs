const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const sandbox = vm.createContext({
    ScaleControls: {},
    ScaleMath: {},
    document: {},
    window: {},
    fetch: () => Promise.resolve({ ok: false, json: async () => ({}) })
});
vm.runInContext(
    fs.readFileSync(path.join(__dirname, '../js/experiences/controller.js'), 'utf8'),
    sandbox
);

function fixture(index = 1, target = {}) {
    const controller = Object.create(sandbox.DimensionExperiences.prototype);
    const visited = [];
    Object.assign(controller, {
        active: true,
        index,
        items: [{ name: 'Small' }, { name: 'Medium' }, { name: 'Large' }],
        focus(next) { this.index = next; visited.push(next); }
    });
    let prevented = 0;
    const event = (key, modifiers = {}) => ({
        key,
        target,
        preventDefault() { prevented++; },
        ...modifiers
    });
    return { controller, visited, event, prevented: () => prevented };
}

test('explorer arrow navigation selects one adjacent item per press and stops at boundaries', () => {
    const { controller, visited, event, prevented } = fixture();
    assert.equal(controller.handleNavigationKey(event('ArrowRight')), true);
    assert.equal(controller.handleNavigationKey(event('ArrowRight', { repeat: true })), true);
    assert.equal(controller.index, 2);
    assert.equal(controller.handleNavigationKey(event('ArrowRight', { repeat: true })), true);
    assert.equal(controller.index, 2);
    assert.deepEqual(visited, [2]);
    assert.equal(controller.handleNavigationKey(event('ArrowLeft')), true);
    assert.equal(controller.index, 1);
    assert.equal(prevented(), 4);
});

test('arrow navigation yields to editable controls and modified shortcuts', () => {
    const editable = { closest: () => ({}) };
    const { controller, visited, event, prevented } = fixture(1, editable);
    assert.equal(controller.handleNavigationKey(event('ArrowRight')), false);
    assert.equal(controller.handleNavigationKey(event('ArrowLeft', { shiftKey: true })), false);
    assert.equal(controller.handleNavigationKey(event('ArrowLeft', { ctrlKey: true })), false);
    assert.equal(controller.handleNavigationKey(event('ArrowLeft', { altKey: true })), false);
    assert.equal(controller.handleNavigationKey(event('ArrowLeft', { metaKey: true })), false);
    assert.deepEqual(visited, []);
    assert.equal(prevented(), 0);
});

test('inactive explorers and unrelated keys are left untouched', () => {
    const { controller, visited, event, prevented } = fixture();
    controller.active = false;
    assert.equal(controller.handleNavigationKey(event('ArrowRight')), false);
    controller.active = true;
    assert.equal(controller.handleNavigationKey(event('ArrowUp')), false);
    assert.deepEqual(visited, []);
    assert.equal(prevented(), 0);
});
