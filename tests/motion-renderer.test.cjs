const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const motionImages = require('../content/visualizations/motion-images.json');
const settle = () => new Promise((resolve) => setImmediate(resolve));

class Element {
    constructor(tag) {
        this.tag = tag;
        this.children = [];
        this.attributes = {};
        this.events = {};
        this.dataset = {};
        this.content = '';
    }
    append(...nodes) {
        this.children.push(...nodes);
    }
    replaceChildren(...nodes) {
        this.children = nodes;
        this.content = '';
    }
    setAttribute(name, value) {
        this.attributes[name] = String(value);
    }
    addEventListener(name, action) {
        this.events[name] = action;
    }
    set textContent(value) {
        this.content = String(value);
        this.children = [];
    }
    get textContent() {
        return (
            this.content +
            this.children.map((node) => node.textContent).join(' ')
        );
    }
    fire(name) {
        this.events[name]?.({ preventDefault() {} });
    }
    all(predicate) {
        return [
            ...(predicate(this) ? [this] : []),
            ...this.children.flatMap((node) => node.all(predicate))
        ];
    }
}

function fixture(dimension, values = [3, 6], names = [], options = {}) {
    const requests = [];
    const sandbox = vm.createContext({
        document: {
            createElement: (tag) => new Element(tag),
            createElementNS: (_namespace, tag) => new Element(tag)
        },
        ScaleRenderers: {},
        ScaleModels: options.models,
        fetch: (url) => {
            requests.push(url);
            return options.fetch
                ? options.fetch(url)
                : Promise.resolve({ ok: true, json: async () => motionImages });
        },
        requestAnimationFrame: () => 1,
        cancelAnimationFrame: () => {}
    });
    for (const file of [
        'math.js',
        'controls.js',
        'motion-math.js',
        'motion.js',
        'controller.js'
    ]) {
        vm.runInContext(
            fs.readFileSync(
                path.join(__dirname, '../js/experiences', file),
                'utf8'
            ),
            sandbox
        );
    }
    // Exercise the real reusable controls and controller object / label APIs.
    const ctx = Object.create(sandbox.DimensionExperiences.prototype);
    let noteWrites = 0;
    Object.assign(ctx, {
        items: values.map((value, index) => ({
            name: names[index] || `Example ${index}`,
            value
        })),
        index: values.length - 1,
        stage: new Element('svg'),
        stageFrame: new Element('div'),
        settings: new Element('div'),
        caption: new Element('p'),
        live: new Element('p'),
        image: options.image || (() => ''),
        app: {
            currentDimension: dimension,
            setRichText(element, content) {
                element.textContent = content;
                noteWrites++;
            }
        }
    });
    ctx.clock = new sandbox.ScaleControls.Clock((time) =>
        ctx.renderer.render(time)
    );
    ctx.renderer = sandbox.ScaleRenderers.motion(ctx);
    ctx.renderer.focus(true);
    ctx.renderer.render(0);
    return {
        ctx,
        requests,
        noteWrites: () => noteWrites,
        click(label) {
            const button = ctx.settings.all(
                (node) => node.tag === 'button' && node.textContent === label
            )[0];
            assert.ok(button, `Missing ${label} button`);
            button.fire('click');
        }
    };
}

test('all six motion dimensions mount and select at exactly 1x', () => {
    for (const dimension of [
        'speed',
        'acceleration',
        'jerk',
        'frequency',
        'sound-frequency',
        'angular-velocity'
    ]) {
        const { ctx, click } = fixture(dimension, [1e-9, 1e20]);
        assert.equal(ctx.clock.rate, 1);
        assert.equal(ctx.timeSlider.value, 0);
        assert.match(ctx.timeSlider.output.textContent, /1x.*real time/);
        assert.ok(Number(ctx.timeSlider.input.min) <= 0);
        assert.ok(Number(ctx.timeSlider.input.max) >= 0);
        click('Fit time to item');
        assert.notEqual(ctx.clock.rate, 1);
        ctx.index = 0;
        ctx.clock.reset();
        ctx.renderer.focus(true);
        assert.equal(ctx.clock.rate, 1);
        assert.equal(ctx.timeSlider.value, 0);
        assert.ok(Number(ctx.timeSlider.input.min) > -10);
    }
});

test('fit and real-time buttons immediately redraw even when paused', () => {
    const { ctx, click } = fixture('sound-frequency', [440]);
    assert.match(ctx.stage.textContent, /static diagram/);
    const rate = ctx.clock.rate;
    click('Fit time to item');
    assert.equal(ctx.clock.playing, false);
    assert.ok(ctx.clock.rate < rate);
    assert.doesNotMatch(ctx.stage.textContent, /static diagram/);
    ctx.clock.time = 42;
    click('Real time (1x)');
    assert.equal(ctx.clock.time, 0);
    assert.equal(ctx.clock.rate, 1);
    assert.match(ctx.stage.textContent, /static diagram/);
});

test('track changes recompute bounds without silently auto-fitting time', () => {
    const { ctx, click } = fixture('speed', [20]);
    const oldMax = Number(ctx.timeSlider.input.max);
    click('Human height (1.7 m)');
    assert.equal(ctx.clock.rate, 1);
    assert.ok(Number(ctx.timeSlider.input.max) < oldMax);
    assert.match(ctx.stage.textContent, /1\.7 m/);
    click('Football field (100 m)');
    assert.equal(Number(ctx.timeSlider.input.max), oldMax);
    const track = ctx.settings.all((node) => node.tag === 'input')[0];
    track.value = 3;
    track.fire('input');
    assert.match(ctx.stage.textContent, /1,000 m/);
    assert.equal(ctx.clock.rate, 1);
});

test('acceleration and jerk show derivatives, unequal distance dots and no rotation', () => {
    for (const dimension of ['acceleration', 'jerk']) {
        const { ctx, noteWrites } = fixture(
            dimension,
            [3],
            ["Earth's Rotation at Equator"]
        );
        ctx.renderer.render(2);
        assert.match(ctx.live.textContent, /v 6 m\/s/);
        assert.match(
            ctx.live.textContent,
            dimension === 'jerk' ? /a 6 m\/s\^2/ : /\+3 m\/s each/
        );
        assert.match(
            ctx.caption.textContent,
            /not a rotation rate|not speed or angular acceleration/
        );
        const transforms = ctx.stage.all((node) =>
            /rotate/.test(node.attributes.transform || '')
        );
        assert.equal(transforms.length, 0);
        const dots = ctx.stage.all(
            (node) => node.attributes.class === 'motion-time-sample'
        );
        assert.equal(dots.length, 5);
        const gaps = dots
            .slice(1)
            .map(
                (node, i) =>
                    Number(node.attributes.cx) - Number(dots[i].attributes.cx)
            );
        assert.ok(gaps.every((gap, i) => i === 0 || gap > gaps[i - 1]));
        assert.equal(noteWrites(), 1, 'do not re-typeset notes every frame');
    }
});

test('comparison lanes share elapsed time and restart together', () => {
    const { ctx } = fixture('jerk', [3, 6]);
    ctx.renderer.render(2);
    assert.match(ctx.stage.textContent, /x 4 m/);
    assert.match(ctx.stage.textContent, /x 8 m/);
    const span = (600 / 6) ** (1 / 3);
    ctx.renderer.render(span + 1);
    assert.match(ctx.stage.textContent, /x 0\.5 m/);
    assert.match(ctx.stage.textContent, /x 1 m/);
    assert.match(ctx.caption.textContent, /reset is not a physical reversal/);
});

test('angular orbit moves its object, spin advances phase without rotating photos, sound does neither', () => {
    const orbit = fixture(
        'angular-velocity',
        [2 * Math.PI],
        ['Earth orbit around the Sun']
    ).ctx;
    orbit.renderer.render(0.25);
    assert.equal(
        orbit.stage.all((node) => Boolean(node.attributes.transform)).length,
        0
    );
    const spin = fixture(
        'angular-velocity',
        [2 * Math.PI],
        ['Ceiling fan']
    ).ctx;
    spin.renderer.render(0.25);
    const guide = spin.stage.all((node) => node.attributes.class === 'motion-phase-guide')[0];
    assert.equal(Number(guide.attributes.x2), 500);
    assert.equal(Number(guide.attributes.y2), 110);
    assert.equal(spin.stage.all((node) => Boolean(node.attributes.transform)).length, 0);
    const sound = fixture('sound-frequency', [1], ['Ceiling fan']).ctx;
    sound.renderer.render(0.25);
    assert.equal(
        sound.stage.all((node) => Boolean(node.attributes.transform)).length,
        0
    );
    assert.match(
        sound.caption.textContent,
        /not the movement of a pictured animal/
    );
});

test('ceiling fan uses the licensed local photo with visible attribution and a stationary fixture', async () => {
    const { ctx, requests } = fixture('angular-velocity', [2 * Math.PI], ['Ceiling fan']);
    await settle();
    assert.deepEqual(requests, ['content/visualizations/motion-images.json']);
    const entry = motionImages.images['angular-velocity']['Ceiling fan'];
    const photo = () => ctx.stage.all((node) => node.tag === 'image')[0];
    assert.equal(photo().attributes.href, entry.src);
    const before = { ...photo().attributes };
    ctx.renderer.render(0.25);
    assert.deepEqual(photo().attributes, before);
    assert.match(ctx.stage.textContent, /Photo reference; marker shows phase/);
    assert.match(ctx.stage.textContent, /Vikramdeep Sidhu/);
    assert.match(ctx.stage.textContent, /CC BY 2\.0/);
    assert.deepEqual(
        ctx.stage.all((node) => node.tag === 'a').map((node) => node.attributes.href),
        [entry.source, entry.license_url]
    );
    assert.equal(photo().attributes.preserveAspectRatio, 'xMidYMid meet');
    assert.equal(ctx.stage.all((node) => node.tag === 'path' || node.attributes.transform).length, 0);
    assert.doesNotMatch(ctx.stage.textContent, /rotor schematic/i);
    assert.match(ctx.caption.textContent, /reference photos stay fixed/);
});

test('existing photos replace generic rotors for uncovered spin items', () => {
    for (const name of ['Blender blade', 'Drone propeller', 'Bicycle wheel', 'Hour hand', '33 1/3 rpm record', 'Hard drive spindle', 'Washing machine spin']) {
        const { ctx } = fixture('angular-velocity', [1], [name], { image: () => 'existing-photo.jpg' });
        ctx.renderer.render(0.5);
        assert.equal(ctx.stage.all((node) => node.tag === 'image')[0].attributes.href, 'existing-photo.jpg');
        assert.equal(ctx.stage.all((node) => node.tag === 'path' || node.attributes.transform).length, 0);
        assert.match(ctx.stage.textContent, /Photo reference/);
    }
});

test('downloaded models get first refusal and retain the shared phase indicator', async () => {
    const draws = [];
    let disposed = false;
    class ModelStage {
        begin() {}
        finish() {}
        draw(...args) { draws.push(args); return true; }
        dispose() { disposed = true; }
    }
    const { ctx } = fixture('angular-velocity', [2 * Math.PI], ['Ceiling fan'], { models: { ModelStage } });
    await settle();
    ctx.renderer.render(0.25);
    assert.equal(draws.at(-1)[0].name, 'Ceiling fan');
    assert.equal(draws.at(-1)[4], Math.PI / 2);
    assert.equal(ctx.stage.all((node) => node.tag === 'image' || node.tag === 'path').length, 0);
    assert.equal(ctx.stage.all((node) => node.attributes.class === 'motion-phase-guide').length, 1);
    assert.doesNotMatch(ctx.stage.textContent, /Photo reference/);
    ctx.renderer.dispose();
    assert.equal(disposed, true);
});

test('failed models and registry requests retain real photos rather than drawn substitutes', async () => {
    class ModelStage {
        begin() {}
        finish() {}
        draw() { return false; }
    }
    for (const fetch of [
        async () => { throw new Error('offline'); },
        async () => ({ ok: false }),
        async () => ({ ok: true, json: async () => { throw new Error('invalid JSON'); } })
    ]) {
        const { ctx, requests } = fixture('angular-velocity', [1], ['Ceiling fan'], {
            fetch, models: { ModelStage }, image: () => 'existing-photo.jpg'
        });
        await settle();
        ctx.renderer.render(1);
        assert.equal(requests.length, 1);
        assert.equal(ctx.stage.all((node) => node.tag === 'image')[0].attributes.href, 'existing-photo.jpg');
        assert.equal(ctx.stage.all((node) => node.tag === 'path' || node.attributes.transform).length, 0);
    }
});

test('broken image URLs are not retried on every frame and never become rotor drawings', async () => {
    const { ctx } = fixture('angular-velocity', [1], ['Ceiling fan'], { image: () => 'fallback.jpg' });
    await settle();
    ctx.stage.all((node) => node.tag === 'image')[0].fire('error');
    const fallback = ctx.stage.all((node) => node.tag === 'image')[0];
    assert.equal(fallback.attributes.href, 'fallback.jpg');
    fallback.fire('error');
    ctx.renderer.render(2);
    assert.equal(ctx.stage.all((node) => node.tag === 'image' || node.tag === 'path').length, 0);
    assert.match(ctx.stage.textContent, /Photo unavailable/);
});

test('late registry results render current time but cannot redraw a disposed renderer', async () => {
    for (const dispose of [false, true]) {
        let resolve;
        const { ctx } = fixture('angular-velocity', [2 * Math.PI], ['Ceiling fan'], {
            fetch: () => new Promise((done) => { resolve = done; })
        });
        const before = ctx.stage.children;
        ctx.clock.time = 0.25;
        if (dispose) ctx.renderer.dispose();
        resolve({ ok: true, json: async () => motionImages });
        await settle();
        if (dispose) assert.equal(ctx.stage.children, before);
        else {
            const guide = ctx.stage.all((node) => node.attributes.class === 'motion-phase-guide')[0];
            assert.equal(Number(guide.attributes.y2), 110);
        }
    }
});

test('high angular rates freeze the phase guide until fitted; other modes do not fetch the image registry', () => {
    const { ctx, click } = fixture('angular-velocity', [1000], ['Ceiling fan']);
    const guide = () => ctx.stage.all((node) => node.attributes.class === 'motion-phase-guide')[0];
    const before = { ...guide().attributes };
    ctx.renderer.render(1);
    assert.deepEqual(guide().attributes, before);
    assert.match(ctx.stage.textContent, /Too fast to resolve/);
    click('Fit time to item');
    ctx.renderer.render(0.001);
    assert.notDeepEqual(guide().attributes, before);
    for (const dim of ['speed', 'acceleration', 'jerk', 'frequency', 'sound-frequency']) {
        assert.equal(fixture(dim).requests.length, 0);
    }
});

test('renderer geometry and displayed rates stay finite at corpus extremes and bounds', () => {
    for (const dimension of [
        'speed',
        'acceleration',
        'jerk',
        'frequency',
        'sound-frequency',
        'angular-velocity'
    ]) {
        for (const value of [2.285e-18, 1e-9, 9.81, 1e20, 5.56e51]) {
            const { ctx, click } = fixture(dimension, [value / 10, value]);
            for (const exponent of [
                Number(ctx.timeSlider.input.min),
                0,
                Number(ctx.timeSlider.input.max)
            ]) {
                ctx.timeSlider.input.value = exponent;
                ctx.timeSlider.input.fire('input');
                ctx.renderer.render(ctx.clock.rate * 2);
                assert.ok(
                    Number.isFinite(ctx.clock.rate) && ctx.clock.rate > 0
                );
                const attributes = ctx.stage
                    .all(() => true)
                    .map((node) => Object.values(node.attributes).join(' '))
                    .join(' ');
                assert.doesNotMatch(
                    attributes + ctx.stage.textContent + ctx.live.textContent,
                    /NaN|Infinity/
                );
            }
            click('Fit time to item');
            assert.doesNotMatch(
                ctx.stage.textContent,
                /static diagram|Static timing diagram/
            );
        }
    }
});
