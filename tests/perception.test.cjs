const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const math = require('../js/experiences/math.js');

// Minimal DOM adapter keeps renderer/control regressions dependency-free.
class Element {
    constructor(tag) {
        this.tagName = tag;
        this.children = [];
        this.attributes = {};
        this.dataset = {};
        this.style = {};
        this.events = {};
        this.className = '';
        this.classList = { add: (...names) => { this.className += ` ${names.join(' ')}`; } };
        this.box = { width: 0, height: 0 };
        this.text = '';
    }
    set textContent(value) { this.text = String(value); this.children = []; }
    get textContent() { return this.text + this.children.map((node) => node.textContent).join(' '); }
    set value(value) { this._value = String(value); }
    get value() { return this._value; }
    get firstElementChild() { return this.children[0]; }
    append(...nodes) { nodes.forEach((node) => { node.parent = this; this.children.push(node); }); }
    replaceChildren(...nodes) { this.text = ''; this.children = []; this.append(...nodes); }
    remove() { this.parent.children = this.parent.children.filter((node) => node !== this); }
    setAttribute(key, value) { this.attributes[key] = String(value); }
    getAttribute(key) { return this.attributes[key]; }
    getBoundingClientRect() { return this.box; }
    addEventListener(name, action) { (this.events[name] ||= []).push(action); }
    fire(name) { (this.events[name] || []).forEach((action) => action({ preventDefault() {} })); }
    checkValidity() { return Number.isFinite(Number(this.value)) && Number(this.value) >= Number(this.min) && Number(this.value) <= Number(this.max); }
    reportValidity() {}
}
const find = (root, predicate) => root.children.flatMap((node) => [
    ...(predicate(node) ? [node] : []), ...find(node, predicate)
]);
const nodes = (root, tag) => find(root, (node) => node.tagName === tag);
const item = (value, extra = {}) => ({ name: `Object ${value}`, value, ...extra });
const fixture = ({ dimension = 'brightness', items = [item(30), item(300)], width = 800, missing = false } = {}) => {
    const sandbox = vm.createContext({
        ScaleMath: math, ScaleRenderers: {},
        document: { createElement: (tag) => new Element(tag), createElementNS: (_, tag) => new Element(tag) }
    });
    for (const name of ['screen', 'navigator']) Object.defineProperty(sandbox, name, {
        get() { throw new Error(`Renderer must not read ${name} for brightness`); }
    });
    for (const file of ['controls.js', 'perception.js']) {
        vm.runInContext(fs.readFileSync(path.join(__dirname, '../js/experiences', file), 'utf8'), sandbox);
    }
    const ctx = {
        dimension, items, index: items.length - 1,
        stage: new Element('svg'), settings: new Element('div'),
        caption: new Element('p'), live: new Element('p'),
        get item() { return this.items[this.index]; },
        get pair() { return this.index ? [this.items[this.index - 1], this.item] : [this.item]; },
        image: () => missing ? null : 'images/test-photo.jpg',
        object(parent, selected, x, y, w, h, options) {
            assert.equal(options.image, false);
            const group = new Element('g');
            const hit = new Element('rect');
            hit.setAttribute('fill', 'transparent');
            group.append(hit);
            parent.append(group);
            return group;
        },
        focus(index, frame = true) {
            this.index = index;
            this.renderer.focus?.(frame);
            this.renderer.render();
        }
    };
    ctx.stage.box = { width, height: 400 };
    ctx.stage.getScreenCTM = () => ({ a: 1, b: 0 });
    ctx.renderer = sandbox.ScaleRenderers[dimension === 'brightness' ? 'brightness' : 'angle'](ctx);
    ctx.renderer.render();
    return { ctx, renderers: sandbox.ScaleRenderers };
};
const ranges = (ctx) => nodes(ctx.settings, 'input').filter((node) => node.type === 'range');
const fields = (ctx) => nodes(ctx.settings, 'input').filter((node) => node.type === 'number');
const change = (node, value, event = 'change') => { node.value = value; node.fire(event); };
const finiteGeometry = (ctx) => {
    for (const node of find(ctx.stage, () => true)) {
        const attributes = Object.fromEntries(Object.entries(node.attributes)
            .filter(([key]) => !['aria-label', 'href'].includes(key)));
        assert.doesNotMatch(JSON.stringify(attributes), /NaN|Infinity/);
    }
};

test('brightness uses photos by default, preserves aspect ratio, and has no opaque patches', () => {
    const { ctx } = fixture();
    assert.equal(nodes(ctx.stage, 'image').length, 2);
    for (const photo of nodes(ctx.stage, 'image')) {
        assert.equal(photo.getAttribute('preserveAspectRatio'), 'xMidYMid meet');
        assert.match(photo.getAttribute('aria-label'), /illustrative/);
    }
    assert.ok(nodes(ctx.stage, 'rect').every((rect) => rect.getAttribute('fill') === 'transparent'));
    assert.match(ctx.live.textContent, /manual estimates, not detected/);
    assert.match(ctx.caption.textContent, /not a reproduction/);
    assert.match(ctx.caption.textContent, /standard API to read OS brightness/);
    assert.equal(find(ctx.settings, (node) => node.className === 'experience-note').length, 0);
});

test('item slider and controller focus stay synchronized, including first-item deduplication', () => {
    const { ctx } = fixture();
    change(ranges(ctx)[0], 0, 'input');
    assert.equal(ctx.index, 0);
    assert.equal(nodes(ctx.stage, 'image').length, 1);
    ctx.focus(1);
    assert.equal(ranges(ctx)[0].value, '1');
});

test('brightness matches compact mobile stage bounds and recomputes after resize', () => {
    const { ctx } = fixture({ width: 320 });
    ctx.stage.box.height = 210;
    ctx.renderer.render();
    assert.equal(ctx.stage.getAttribute('viewBox'), '0 0 320 210');
    assert.equal(nodes(ctx.stage, 'image')[1].getAttribute('y'), '12');
    assert.equal(nodes(ctx.stage, 'image')[1].getAttribute('height'), '98');
    ctx.stage.box.width = 900;
    ctx.stage.box.height = 350;
    ctx.renderer.render();
    assert.equal(ctx.stage.getAttribute('viewBox'), '0 0 900 350');
    assert.equal(nodes(ctx.stage, 'image')[1].getAttribute('y'), '12');
    finiteGeometry(ctx);
});

for (const [metadata, unit, reason] of [
    [{ qualifiers: { quantity: 'luminous_flux', unit: 'lm' } }, 'lm', 'flux'],
    [{ qualifiers: { original_unit: 'lumens' } }, 'lm', 'flux'],
    [{ qualifiers: { unit: 'cd' } }, 'cd', 'intensity'],
    [{ qualifiers: { units: 'cd' } }, 'cd', 'intensity'],
    [{ qualifiers: { quantity_kind: 'luminous_intensity' } }, 'cd', 'intensity'],
    [{ unit_symbol: 'cd' }, 'cd', 'intensity'],
    [{ qualifiers: { unit: 'lux' } }, 'lx', 'Illuminance'],
    [{ qualifiers: { unit: 'foot-candles' } }, 'fc', 'Illuminance'],
    [{ qualifiers: { unit: 'W/sr' } }, '(unit unverified)', 'metadata'],
    [{ qualifiers: { quantity: 'radiant_intensity' } }, '(unit unverified)', 'metadata']
]) test(`unit qualifiers prevent false nits mapping: ${JSON.stringify(metadata)}`, () => {
    const { ctx } = fixture({ items: [item(800, metadata)] });
    assert.match(ctx.stage.textContent, /Unadjusted photo/);
    assert.ok(ctx.stage.textContent.includes(`800 ${unit}`));
    assert.ok(ctx.live.textContent.includes(reason));
    assert.doesNotMatch(ctx.stage.textContent, /cd\/m/);
    assert.equal(nodes(ctx.stage, 'image')[0].getAttribute('style'), 'filter: brightness(1)');
    change(ranges(ctx)[1], 10, 'input');
    assert.equal(nodes(ctx.stage, 'image')[0].getAttribute('style'), 'filter: brightness(1)');
});

for (const unit of ['cd/m2', 'cd/m\u00b2', 'cd/m^2', 'nits', 'candela_per_square_meter'])
    test(`explicit luminance units use the model: ${unit}`, () => {
        const { ctx } = fixture({ items: [item(300, { qualifiers: { unit } })] });
        assert.doesNotMatch(ctx.stage.textContent, /Unadjusted/);
        assert.match(ctx.stage.textContent, /cd\/m/);
    });

test('mixed quantity pairs only adjust the eligible luminance photo', () => {
    const { ctx } = fixture({ items: [item(100, { qualifiers: { unit: 'lm' } }), item(300)] });
    const photos = nodes(ctx.stage, 'image');
    assert.equal(photos[0].getAttribute('style'), 'filter: brightness(1)');
    assert.notEqual(photos[1].getAttribute('style'), 'filter: brightness(1)');
});

test('manual and measured settings are explicit; invalid black/white relationships are rejected', () => {
    const { ctx } = fixture();
    change(nodes(ctx.settings, 'select')[0], 'measured');
    assert.match(ctx.live.textContent, /your entered measurements/);
    const [white, black] = fields(ctx);
    change(black, 400);
    assert.equal(black.value, '0.3');
    change(white, 0.1);
    assert.equal(white.value, '300');
    change(black, 0);
    assert.equal(black.value, '0');
    change(white, 0.01);
    assert.equal(white.value, '0.01');
    change(white, '');
    finiteGeometry(ctx);
});

test('exposure communicates model clipping and remains finite over the dataset range', () => {
    const { ctx } = fixture({ items: [item(1e-10), item(1e20)] });
    assert.match(ctx.live.textContent, /below modeled range/);
    change(ranges(ctx)[1], 15, 'input');
    assert.match(ctx.live.textContent, /above modeled range/);
    finiteGeometry(ctx);
    change(ranges(ctx)[1], -35, 'input');
    assert.match(ctx.live.textContent, /below modeled range/);
    finiteGeometry(ctx);
    nodes(ctx.settings, 'button')[0].fire('click');
    assert.doesNotMatch(ctx.stage.textContent, /Above modeled white/);
});

test('missing/failed images have an honest fallback without invented patches', () => {
    const { ctx } = fixture({ missing: true });
    assert.match(ctx.stage.textContent, /Image unavailable/);
    assert.equal(nodes(ctx.stage, 'image').length, 0);
    ctx.image = () => 'missing.jpg';
    ctx.renderer.render();
    nodes(ctx.stage, 'image')[0].fire('error');
    assert.match(ctx.stage.textContent, /Image unavailable/);
});

for (const value of [NaN, Infinity, -1, 0, Number.MAX_VALUE])
    test(`brightness never emits invalid geometry for ${value}`, () => {
        const { ctx } = fixture({ items: [item(value)] });
        finiteGeometry(ctx);
        if (!Number.isFinite(value) || value < 0) assert.match(ctx.stage.textContent, /Value unavailable/);
    });

for (const dimension of ['angle', 'visual-angle']) {
    test(`${dimension} calibrated span is correct and image proportions are preserved`, () => {
        const { ctx } = fixture({ dimension, items: [item(0.1)], width: 500 });
        const photo = nodes(ctx.stage, 'image')[0];
        const expected = math.angularWidth(0.1, 0.6) * 10000 / 2.65;
        assert.ok(Math.abs(Number(photo.getAttribute('width')) - expected) < 1e-8);
        assert.equal(photo.getAttribute('preserveAspectRatio'), 'xMidYMid meet');
        change(ranges(ctx)[1], 30, 'input');
        assert.ok(Math.abs(Number(nodes(ctx.stage, 'image')[0].getAttribute('width')) - expected / 2) < 1e-8);
        change(fields(ctx)[0], 5.3);
        assert.ok(Math.abs(Number(nodes(ctx.stage, 'image')[0].getAttribute('width')) - expected / 4) < 1e-8);
    });
    test(`${dimension} handles tiny, large, straight, and full-turn angles without false physical sizing`, () => {
        const { ctx } = fixture({ dimension, items: [item(1e-9), item(2), item(Math.PI), item(Math.PI * 2)] });
        for (let index = 0; index < ctx.items.length; index++) {
            ctx.focus(index);
            assert.match(ctx.live.textContent, /Diagram only/);
            assert.equal(nodes(ctx.stage, 'image').length, 0);
            finiteGeometry(ctx);
        }
    });
}

test('angle uses screen transform for CSS pixel sizing and responds to a narrower viewport', () => {
    const { ctx } = fixture({ dimension: 'angle', items: [item(0.3)], width: 800 });
    const original = Number(nodes(ctx.stage, 'image')[0].getAttribute('width'));
    ctx.stage.getScreenCTM = () => ({ a: 2, b: 0 });
    ctx.renderer.render();
    assert.ok(Math.abs(Number(nodes(ctx.stage, 'image')[0].getAttribute('width')) - original / 2) < 1e-8);
    ctx.stage.getScreenCTM = () => ({ a: 1, b: 0 });
    ctx.stage.box.width = 320;
    ctx.renderer.render();
    assert.match(ctx.live.textContent, /exceeds this view/);
    assert.equal(ctx.stage.getAttribute('viewBox'), '0 0 320 400');
});

test('angle diagrams reject invalid input and draw finite full circles', () => {
    const { renderers } = fixture();
    const parent = new Element('div');
    for (const value of [-1, NaN, Infinity]) renderers.angleDiagram(parent, value);
    assert.equal(parent.children.length, 0);
    renderers.angleDiagram(parent, Math.PI * 2);
    assert.match(parent.textContent, /1 full turn/);
});

test('brightness stylesheet is scoped to the controller-owned active attribute', () => {
    const css = fs.readFileSync(path.join(__dirname, '../css/perception-experience.css'), 'utf8');
    assert.match(css, /body\[data-experience-dimension='brightness'\]/);
    assert.match(css, /--bg-primary: #000/);
    assert.match(css, /--text-primary: #bdbdbd/);
    assert.doesNotMatch(css, /prefers-color-scheme/);
});
