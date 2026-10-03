const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

class Target {
    constructor() { this.listeners = new Map(); }
    addEventListener(type, listener) {
        if (!this.listeners.has(type)) this.listeners.set(type, new Set());
        this.listeners.get(type).add(listener);
    }
    removeEventListener(type, listener) { this.listeners.get(type)?.delete(listener); }
    emit(type) { for (const listener of this.listeners.get(type) || []) listener({ type }); }
}
class Classes {
    values = new Set();
    add(value) { this.values.add(value); }
    remove(value) { this.values.delete(value); }
    contains(value) { return this.values.has(value); }
}

function fixture() {
    const document = new Target();
    Object.assign(document, {
        body: { style: { overflow: 'clip' }, classList: new Classes() },
        documentElement: { style: { overflow: 'scroll' } },
        fullscreenElement: null
    });
    const window = {
        scrollX: 11,
        scrollY: 29,
        restored: null,
        scrollTo(x, y) { this.restored = [x, y]; }
    };
    const host = { classList: new Classes() };
    const button = {
        attributes: {},
        setAttribute(name, value) { this.attributes[name] = String(value); }
    };
    const sandbox = vm.createContext({
        document, window, ScaleControls: {}, ScaleMath: {},
        fetch: () => Promise.resolve({ ok: false, json: async () => ({}) })
    });
    vm.runInContext(fs.readFileSync(path.join(__dirname, '../js/experiences/controller.js'), 'utf8'), sandbox);
    const controller = Object.create(sandbox.DimensionExperiences.prototype);
    Object.assign(controller, {
        host, fullscreenButton: button, active: true, clock: { time: 2 },
        fullscreenRequest: 0,
        renderer: { render() {} }
    });
    return { controller, document, window, host, button };
}

test('unsupported fullscreen uses fallback and restores page state on exit', async () => {
    const { controller, document, window, host, button } = fixture();
    controller.enterFullscreen();
    await Promise.resolve();
    assert.equal(host.classList.contains('experience-fullscreen-fallback'), true);
    assert.equal(document.body.classList.contains('experience-fullscreen-active'), true);
    assert.equal(document.documentElement.style.overflow, 'hidden');
    assert.equal(button.attributes['aria-label'], 'Exit fullscreen');
    assert.equal(button.attributes['aria-pressed'], 'true');
    controller.exitFullscreen();
    assert.equal(host.classList.contains('experience-fullscreen-fallback'), false);
    assert.equal(document.body.classList.contains('experience-fullscreen-active'), false);
    assert.equal(document.documentElement.style.overflow, 'scroll');
    assert.equal(document.body.style.overflow, 'clip');
    assert.deepEqual(window.restored, [11, 29]);
    assert.equal(button.attributes['aria-label'], 'Enter fullscreen');
    assert.equal(button.attributes['aria-pressed'], 'false');
});

test('native fullscreen change from browser Escape restores state and button', () => {
    const { controller, document, button } = fixture();
    controller.fullscreenState = {
        native: true, fallback: false, scrollX: 0, scrollY: 0,
        htmlOverflow: '', bodyOverflow: ''
    };
    document.documentElement.style.overflow = 'hidden';
    document.body.style.overflow = 'hidden';
    controller.updateFullscreenButton(true);
    controller.handleFullscreenChange();
    assert.equal(controller.fullscreenState, null);
    assert.equal(button.attributes['aria-label'], 'Enter fullscreen');
    assert.equal(document.documentElement.style.overflow, '');
});

test('rejected native entry falls back without an unhandled rejection', async () => {
    const { controller, host } = fixture();
    host.requestFullscreen = () => Promise.reject(new Error('denied'));
    controller.enterFullscreen();
    await new Promise((resolve) => setImmediate(resolve));
    assert.equal(host.classList.contains('experience-fullscreen-fallback'), true);
    controller.exitFullscreen();
});
