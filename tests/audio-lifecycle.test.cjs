const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Minimal DOM/Web Audio doubles keep lifecycle tests dependency-free and silent.
class Target {
    listeners = new Map();
    addEventListener(type, listener) {
        if (!this.listeners.has(type)) this.listeners.set(type, new Set());
        this.listeners.get(type).add(listener);
    }
    removeEventListener(type, listener) { this.listeners.get(type)?.delete(listener); }
    emit(type) { for (const listener of [...(this.listeners.get(type) || [])]) listener({ type }); }
    get listenerCount() { return [...this.listeners.values()].reduce((n, set) => n + set.size, 0); }
}
class Element extends Target {
    constructor(tag) {
        super();
        this.tagName = tag;
        this.children = [];
        this.dataset = {};
        this.attrs = {};
        this.value = '';
        this.className = '';
        this.classList = { add: (x) => { this.className += ` ${x}`; }, remove() {} };
    }
    append(...nodes) {
        for (const node of nodes) { node.parentNode = this; this.children.push(node); }
    }
    insertBefore(node, before) {
        node.parentNode = this;
        this.children.splice(this.children.indexOf(before), 0, node);
    }
    replaceChildren(...nodes) {
        for (const child of this.children) child.parentNode = null;
        this.children = [];
        this.append(...nodes);
    }
    set textContent(value) { this.replaceChildren(); this.text = String(value); }
    get textContent() { return (this.text || '') + this.children.map((x) => x.textContent).join(''); }
    setAttribute(key, value) { this.attrs[key] = String(value); }
    getAttribute(key) { return this.attrs[key] ?? null; }
    removeAttribute(key) { delete this.attrs[key]; }
    get valueAsNumber() { return this.value === '' ? NaN : Number(this.value); }
    get isConnected() { return this.connected || this.parentNode?.isConnected || false; }
    click() { if (!this.disabled) this.emit('click'); }
}
const deferred = () => {
    let resolve, reject;
    const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
    return { promise, resolve, reject };
};
const settle = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };
const all = (element) => [element, ...element.children.flatMap(all)];
const rain = { name: 'Rainfall', value: 1e-7 };
const rocket = { name: 'Rocket launch pad', value: 1e6 };

function fixture(options = {}) {
    const frames = new Map(), timers = new Map(), nodes = [], fetches = [];
    let id = 0;
    const document = new Target();
    document.createElement = (tag) => new Element(tag);
    document.createTextNode = (text) => Object.assign(new Element('#text'), { textContent: text });
    const window = new Target();
    const mediaDevices = new Target();
    const makeBuffer = (channels = 1, length = 600, sampleRate = 100) => {
        const data = Array.from({ length: channels }, () => new Float32Array(length).fill(0.1));
        return { numberOfChannels: channels, length, sampleRate, duration: length / sampleRate,
            getChannelData: (channel) => data[channel], copyToChannel: (from, channel) => data[channel].set(from) };
    };
    const makeNode = (kind) => {
        const node = { kind, disconnected: false, stopped: false,
            connect(next) { this.next = next; return next; },
            disconnect() { this.disconnected = true; this.next = null; },
            start() { if (options.startFails) throw new Error('start'); this.started = true; },
            stop() { this.stopped = true; },
            gain: { value: 1, calls: [],
                setValueAtTime(value, time) { this.value = value; this.calls.push(['set', value, time]); },
                linearRampToValueAtTime(value, time) { this.calls.push(['ramp', value, time]); },
                cancelScheduledValues() {},
                setTargetAtTime(value, time, constant) { this.value = value; this.calls.push(['target', value, time, constant]); }
            },
            getFloatTimeDomainData(samples) { samples.fill(0.001); }
        };
        nodes.push(node);
        return node;
    };
    class Context extends Target {
        currentTime = 0;
        destination = {};
        resume() { return options.resume?.promise || Promise.resolve(); }
        decodeAudioData() { return options.decode?.promise || Promise.resolve(makeBuffer()); }
        createBuffer = makeBuffer;
        createBufferSource() { return makeNode('source'); }
        createGain() { return makeNode('gain'); }
        createAnalyser() { return makeNode('analyser'); }
    }
    if (!options.unsupported) window.AudioContext = Context;
    const clip = { src: 'rain.ogg', title: 'Rain', author: 'Recordist', license: 'CC0', source: 'https://example.test/rain' };
    const clips = options.clips || { Rainfall: clip, [rocket.name]: { ...clip, src: 'rocket.wav' } };
    const sandbox = {
        document, window, navigator: { mediaDevices }, AbortController, Float32Array,
        fetch: async (url, args) => {
            fetches.push({ url, args });
            if (url.endsWith('assets.json')) return options.manifest?.promise || { ok: true, json: async () => ({ audio: clips }) };
            return options.download?.promise || { ok: !options.downloadFails, arrayBuffer: async () => new ArrayBuffer(100) };
        },
        requestAnimationFrame: (fn) => { frames.set(++id, fn); return id; },
        cancelAnimationFrame: (key) => frames.delete(key),
        setTimeout: (fn, delay) => { timers.set(++id, { fn, delay }); return id; },
        clearTimeout: (key) => timers.delete(key)
    };
    vm.createContext(sandbox);
    for (const file of ['controls.js', 'math.js', 'audio-math.js', 'audio.js']) {
        vm.runInContext(fs.readFileSync(path.join(__dirname, '../js/experiences', file), 'utf8'), sandbox);
    }
    const app = { backgroundMusic: { paused: false, pause() { this.paused = true; } } };
    const audio = new sandbox.ScaleAudio(app);
    const parent = new Element('main');
    parent.connected = true;
    audio.controls(parent, options.item || rain);
    const view = audio.view;
    const play = (item = options.item || rain, reference = false) => audio.play(item, reference ? view.reference : view.play, view.status, reference);
    const frame = (time = 100) => {
        const entries = [...frames];
        frames.clear();
        for (const [, fn] of entries) fn(time);
    };
    const clean = () => {
        assert.equal(audio.node, null);
        assert.equal(audio.gain, null);
        assert.equal(audio.attenuation, null);
        assert.equal(audio.analyser, null);
        assert.equal(audio.abort, null);
        assert.equal(frames.size, 0);
        assert.equal(timers.size, 0);
        assert.equal(document.listenerCount, 0);
        assert.equal(window.listenerCount, 0);
        assert.ok(nodes.every((node) => node.disconnected));
        assert.ok(nodes.filter((node) => node.kind === 'source').every((node) => node.stopped));
    };
    return { audio, view, app, parent, play, frame, clean, frames, timers, nodes, fetches, document, window, mediaDevices, makeBuffer };
}

test('controls retain the public API, quiet start and accessible collapsed information', async () => {
    const f = fixture();
    await f.audio.ready;
    assert.equal(all(f.parent).find((x) => x.tagName === 'button'), f.view.play);
    assert.equal(f.view.play.disabled, false);
    assert.equal(f.audio.trim, -12);
    assert.equal(f.view.apply.disabled, true);
    assert.equal(f.view.input.disabled, true);
    assert.equal(f.view.reset.hidden, true);
    assert.ok(all(f.parent).filter((x) => x.tagName === 'details').every((x) => !x.open));
    assert.match(f.parent.textContent, /Start with low device volume/);
    assert.match(f.parent.textContent, /cannot read OS volume/);
    f.clean();
});
test('meter reads post-attenuation audio and stop releases every playback resource', async () => {
    const f = fixture();
    await f.play();
    assert.equal(f.audio.node.next, f.audio.gain);
    assert.equal(f.audio.gain.next, f.audio.attenuation);
    assert.equal(f.audio.attenuation.next, f.audio.analyser);
    assert.equal(f.app.backgroundMusic.paused, true);
    f.frame();
    assert.ok(Math.abs(f.view.meter.value + 60) < 0.01);
    assert.match(f.view.meterText.textContent, /dBFS/);
    assert.equal(f.view.play.getAttribute('aria-pressed'), 'true');
    f.audio.stop(); f.audio.stop();
    assert.equal(f.view.play.textContent, 'Play sound');
    assert.equal(f.view.meterText.textContent, 'Idle');
    f.clean();
});
test('capped sounds attenuate immediately without stopping or restarting the source', async () => {
    const f = fixture({ item: rocket });
    await f.play();
    const source = f.audio.node;
    const slider = all(f.parent).find((x) => x.type === 'range');
    slider.value = -20;
    slider.emit('input');
    assert.equal(f.audio.node, source);
    assert.equal(source.stopped, false);
    assert.equal(f.audio.attenuation.gain.value, 0.1);
    assert.match(f.view.status.textContent, /20 dB quieter.*capped/);
    assert.equal(slider.getAttribute('aria-valuetext'), '20 dB quieter');
    f.audio.stop(); f.clean();
});
test('only a complete rain reference unlocks session-only measurement, with visible reset', async () => {
    const f = fixture();
    await f.play(rocket, true);
    assert.equal(f.fetches.at(-1).url, 'rain.ogg');
    assert.equal(f.audio.referencePlayed, false);
    assert.equal(f.audio.attenuation.gain.value, 1);
    const slider = all(f.parent).find((x) => x.type === 'range');
    slider.value = -40; slider.emit('input');
    assert.equal(f.audio.attenuation.gain.value, 1);
    const interrupted = f.audio.node.onended;
    f.audio.stop(); interrupted();
    assert.equal(f.audio.referencePlayed, false);
    assert.equal(f.mediaDevices.listenerCount, 0);
    await f.play(rain, true);
    f.audio.node.onended();
    assert.equal(f.audio.referencePlayed, true);
    assert.equal(f.view.input.disabled, false);
    f.view.input.value = 100; f.view.apply.click();
    assert.equal(f.audio.referenceDb, null);
    f.view.input.value = 65; f.view.apply.click();
    assert.equal(f.audio.referenceDb, 65);
    assert.match(f.view.badge.textContent, /Measurement applied.*this session/);
    assert.equal(f.view.reset.hidden, false);
    await f.play();
    assert.doesNotMatch(f.view.status.textContent, /\d.*dB SPL/);
    f.audio.stop();
    f.parent.replaceChildren();
    f.audio.controls(f.parent, rain);
    assert.match(f.audio.view.badge.textContent, /Measurement applied/);
    f.audio.view.reset.click();
    assert.equal(f.audio.referenceDb, null);
    assert.equal(f.audio.referencePlayed, false);
    assert.equal(f.mediaDevices.listenerCount, 0);
    assert.equal(f.audio.context.listenerCount, 0);
    f.clean();
    assert.equal(fixture().audio.referenceDb, null);
});
test('output changes invalidate measurement even between previews', async () => {
    for (const event of ['devicechange', 'sinkchange']) {
        const f = fixture();
        await f.play(rain, true);
        f.audio.node.onended();
        f.view.input.value = 65; f.view.apply.click();
        (event === 'devicechange' ? f.mediaDevices : f.audio.context).emit(event);
        assert.equal(f.audio.referenceDb, null);
        assert.equal(f.audio.referencePlayed, false);
        assert.match(f.view.status.textContent, /devices changed/);
        assert.equal(f.mediaDevices.listenerCount, 0);
        f.clean();
    }
});
test('natural end, hidden page, pagehide, mode change and detached UI all stop sound', async () => {
    for (const reason of ['ended', 'hidden', 'pagehide', 'mode', 'detached']) {
        const f = fixture();
        await f.play();
        if (reason === 'ended') f.audio.node.onended();
        if (reason === 'hidden') { f.document.hidden = true; f.document.emit('visibilitychange'); }
        if (reason === 'pagehide') f.window.emit('pagehide');
        if (reason === 'mode') f.view.play.clearPreview.emit('change');
        if (reason === 'detached') { f.parent.replaceChildren(); f.frame(); }
        f.clean();
    }
});
test('cancel during resume, manifest, download or decode cannot restart sound', async () => {
    for (const stage of ['resume', 'manifest', 'download', 'decode']) {
        const pending = deferred();
        const f = fixture({ [stage]: pending });
        const playback = f.play();
        await settle();
        f.audio.stop();
        if (stage === 'manifest') pending.resolve({ ok: true, json: async () => ({ audio: { Rainfall: { src: 'rain.ogg' } } }) });
        else if (stage === 'download') pending.resolve({ ok: true, arrayBuffer: async () => new ArrayBuffer(100) });
        else if (stage === 'decode') pending.resolve(f.makeBuffer());
        else pending.resolve();
        await playback;
        assert.equal(f.audio.cache.size, 0);
        f.clean();
    }
});
test('stale end and download timeout callbacks cannot stop replacement playback', async () => {
    const f = fixture();
    const first = f.play();
    const oldTimeout = [...f.timers.values()][0].fn;
    await first;
    const oldEnd = f.audio.node.onended;
    await f.play(rocket);
    const replacement = f.audio.node;
    oldEnd(); oldTimeout();
    assert.equal(f.audio.node, replacement);
    f.audio.stop(); f.clean();
});
test('download failure, partial graph failure and timeout reset controls and resources', async () => {
    for (const options of [{ downloadFails: true }, { startFails: true }, { unsupported: true }]) {
        const f = fixture(options);
        await f.play();
        assert.match(f.view.status.textContent, /could not be played/);
        f.clean();
    }
    const resume = deferred();
    const f = fixture({ resume });
    const pending = f.play();
    [...f.timers.values()][0].fn();
    assert.match(f.view.status.textContent, /timed out/);
    resume.resolve(); await pending;
    f.clean();
});
test('missing recordings stay disabled and repeated play/stop does not accumulate resources', async () => {
    const missing = fixture({ item: { name: 'No recording', value: 1 } });
    await missing.audio.ready;
    assert.equal(missing.view.play.disabled, true);
    assert.match(missing.view.status.textContent, /No verified recording/);
    const f = fixture();
    for (let i = 0; i < 20; i++) { await f.play(); f.audio.stop(); f.clean(); }
    assert.equal(f.fetches.filter((x) => x.url === 'rain.ogg').length, 1);
});
