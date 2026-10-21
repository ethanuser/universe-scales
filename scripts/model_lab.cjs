#!/usr/bin/env node
// Model lab: drive the production renderer headlessly to review Length models.
// Serves the repo itself on a free port, so no dev server is needed.
//
//   node scripts/model_lab.cjs audit [--json]
//       Every Length item: model kind, rendered extent in units of its listed
//       size (1.0 = matches), layout width, triangles, load time, warnings.
//   node scripts/model_lab.cjs shot OUT_DIR "Item" ["Item" ...]
//       [--views rest,front,side,top,back] [--bg light|dark|sky] [--time 1.5] [--zoom 1]
//       One PNG per item and view from model-review.html, plus printed metrics.
//   node scripts/model_lab.cjs sheet OUT.png [--filter regex] [--cols 6] [--bg auto|light|dark|sky]
//       Contact sheet of every Length item that has a model, labeled with its
//       extent ratio, for a quick visual pass over the whole scale.
//   node scripts/model_lab.cjs explorer OUT_DIR "Item" [...] [--size 1280x800]
//       The real explorer, after the camera spring settles on each item.
//   node scripts/model_lab.cjs coverage [--gap 1] [--json]
//       Model provenance and largest logarithmic gaps; not a visual approval.
//   node scripts/model_lab.cjs angular OUT_DIR ["Item" ...]
//       Every observation (including duplicate names and orbital diagrams) at
//       rest/quarter/half/three-quarter/0.37 rad; rotor/housing checks.
//       --times 0.1,1,2 adds screenshots at these simulated seconds per item.
//   node scripts/model_lab.cjs mobile OUT_DIR
//       Real touch gestures, slider isolation, mobile/fullscreen layout and exits.
//   node scripts/model_lab.cjs navigation OUT_DIR
//       Adjacent-item camera continuity, repeated arrow keys and toolbar/search controls.
//   node scripts/model_lab.cjs performance ["Item"] [--mobile] [--gpu] [--trace /tmp/trace.json]
//       Actual frame and JS timings; --gpu isolates visible models, --trace records Chromium GPU/paint work.
//   node scripts/model_lab.cjs labels ["Item" ...] [--zooms 0.35,0.6,1,1.5] [--views rest,side]
//       Check rendered label collisions over zoom/rotation; exits nonzero on overlap or load errors.
//
// Needs playwright-core and a Chromium build (see scripts/preview_glb.cjs).
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { loadPlaywright, executablePath } = require('./preview_glb.cjs');
const { coverageReport } = require('./model_coverage.cjs');

const ROOT = path.resolve(__dirname, '..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
    '.json': 'application/json', '.glb': 'model/gltf-binary', '.png': 'image/png', '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml', '.yaml': 'text/yaml', '.geojson': 'application/json',
    '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.wav': 'audio/wav', '.woff2': 'font/woff2' };

function serve() {
    const server = http.createServer((request, response) => {
        const url = new URL(request.url, 'http://localhost');
        let file = path.normalize(path.join(ROOT, decodeURIComponent(url.pathname)));
        if (!file.startsWith(ROOT)) { response.writeHead(403).end(); return; }
        if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
        fs.readFile(file, (error, data) => {
            if (error) { response.writeHead(404).end(); return; }
            response.writeHead(200, { 'content-type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream',
                'cache-control': 'no-store' });
            response.end(data);
        });
    });
    return new Promise(resolve => server.listen(0, '127.0.0.1', () => resolve(server)));
}

function parse(argv) {
    const options = {}, positional = [];
    for (let index = 0; index < argv.length; index++) {
        if (argv[index].startsWith('--')) {
            const key = argv[index].slice(2), next = argv[index + 1];
            options[key] = next == null || next.startsWith('--') ? true : (index++, next);
        } else positional.push(argv[index]);
    }
    return { command: positional.shift(), positional, options };
}
const slug = name => name.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '').toLowerCase();

async function withBrowser(size, work, mobile = false) {
    const server = await serve();
    const base = `http://127.0.0.1:${server.address().port}`;
    const { chromium } = loadPlaywright();
    const browser = await chromium.launch({ executablePath: executablePath(),
        args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
    const [width, height] = (size || '1280x900').split('x').map(Number);
    const page = await browser.newPage({ viewport: { width, height },
        ...(mobile ? { isMobile: true, hasTouch: true, deviceScaleFactor: 3 } : {}) });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => {
        if (message.type() === 'error' && !message.text().startsWith('Failed to load resource')) errors.push(message.text());
    });
    page.on('response', response => { if (response.status() >= 400) errors.push(`HTTP ${response.status()} ${response.url().replace(base, '')}`); });
    try { return await work(page, base, errors); } finally { await browser.close(); server.close(); }
}
async function openLab(page, base) {
    await page.goto(`${base}/model-review.html`);
    await page.waitForFunction(() => window.modelLab, null, { timeout: 60000 });
    await page.evaluate(() => window.modelLab.ready());
}
const describe = m => `${m.name.padEnd(34)} ${String(m.model || 'photo').padEnd(38)} ` +
    (m.loaded ? `extent ${m.extent.toFixed(2).padStart(5)}x  w ${m.width.toFixed(2)} h ${m.height.toFixed(2)}  ` +
        `layout ${String(m.layoutWidthFactor).padEnd(5)} ${String(m.triangles).padStart(7)} tris ${String(m.loadMs).padStart(6)} ms` +
        (m.warnings.length ? `  !! ${m.warnings.join('; ')}` : '') : m.model ? 'FAILED TO LOAD' : '');

const commands = {
    async navigation({ positional }) {
        const [out = '/tmp/navigation-model-lab'] = positional;
        fs.mkdirSync(out, { recursive: true });
        await withBrowser('1280x900', async (page, base, errors) => {
            await page.goto(`${base}/?dimension=length&item=Hydrogen%20Atom`);
            await page.waitForFunction(() => globalThis.app?.experiences?.renderer && globalThis.ScaleModels);
            await page.waitForTimeout(2500);
            const result = await page.evaluate(async () => {
                const view = app.experiences, original = ScaleJourney.layout;
                ScaleJourney.layout = (...args) => {
                    const entries = original(...args);
                    globalThis.navigationLayout = entries;
                    return entries;
                };
                view.renderer.render();
                const index = view.index, before = navigationLayout[index].x;
                view.next.click();
                const immediateJump = Math.abs(navigationLayout[index].x - before);
                const samples = [];
                for (let i = 0; i < 90; i++) {
                    await new Promise(requestAnimationFrame);
                    samples.push({ x: navigationLayout[index].x, index: view.index });
                }
                const settled = view.index;
                const direction = Math.sign(samples.at(-1).x - before);
                const monotonic = samples.every((point,i) => (point.x-(i ? samples[i-1].x : before))*direction >= -.01);
                document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
                await new Promise(requestAnimationFrame);
                const during = view.index;
                document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
                await new Promise(requestAnimationFrame);
                const repeated = view.index;
                const closeSizeHops = [];
                const redCell = view.items.findIndex(item => item.name === 'Red Blood Cell');
                view.focus(redCell);
                await new Promise(resolve => setTimeout(resolve, 1200));
                for (const key of ['ArrowRight', 'ArrowLeft']) {
                    const target = view.index + (key === 'ArrowRight' ? 1 : -1);
                    const tracked = [redCell, redCell + 1];
                    const positions = () => tracked.map(index => navigationLayout[index].x);
                    const samples = [positions()];
                    const start = performance.now();
                    document.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true }));
                    let lastMovement = start;
                    while (performance.now() - start < 1800) {
                        await new Promise(requestAnimationFrame);
                        const next = positions();
                        if (next.some((x,i) => Math.abs(x-samples.at(-1)[i]) > .01)) lastMovement = performance.now();
                        samples.push(next);
                    }
                    const endpoint = samples.at(-1);
                    const monotonic = tracked.every((_,i) => {
                        const direction = Math.sign(endpoint[i] - samples[0][i]);
                        return samples.slice(1).every((point,j) => (point[i]-samples[j][i])*direction >= -.01);
                    });
                    closeSizeHops.push({ key, monotonic, durationMs: lastMovement-start,
                        centered: Math.abs(navigationLayout[target].x-500)<.01,
                        selected: view.index === target });
                }
                const rect = element => element.getBoundingClientRect().toJSON();
                const picker = rect(view.pickerToggle), previous = rect(view.previous), next = rect(view.next);
                return { immediateJump, monotonic, closeSizeHops, maxFrameStep: Math.max(...samples.slice(1).map((p,i)=>Math.abs(p.x-samples[i].x))),
                    targetHeld: samples.every(p => p.index === index + 1), settled, expectedSettled: index + 1,
                    repeatedAdvance: during === settled + 1 && repeated === settled + 2,
                    arrowsAfterSelector: previous.left >= picker.right && next.left >= previous.right,
                    equalButtonSizes: rect(view.fullscreenButton).height === rect(document.querySelector('.experience-info__button')).height };
            });
            await page.keyboard.press('Control+k');
            result.searchFocused = await page.locator('.experience-picker-search').evaluate(node => node === document.activeElement);
            await page.keyboard.press('Escape');
            await page.locator('.experience-toolbar').screenshot({ path: path.join(out, 'toolbar.png') });
            console.log(JSON.stringify({ ...result, errors }, null, 2));
            if (result.immediateJump > 0.01 || !result.monotonic || !result.targetHeld ||
                result.settled !== result.expectedSettled || !result.repeatedAdvance || !result.arrowsAfterSelector ||
                !result.equalButtonSizes || !result.searchFocused ||
                result.closeSizeHops.some(hop => !hop.monotonic || !hop.centered || !hop.selected) || errors.length) process.exitCode = 1;
        });
    },
    async mobile({ positional }) {
        const [out = '/tmp/mobile-model-lab'] = positional;
        fs.mkdirSync(out, { recursive: true });
        const results = [];
        await withBrowser('393x852', async (page, base, errors) => {
            await page.goto(`${base}/?dimension=length&item=Earth%20Diameter`);
            await page.waitForFunction(() => globalThis.app?.experiences?.renderer && globalThis.ScaleModels);
            await page.evaluate(() => {
                const draw = ScaleModels.ModelStage.prototype.draw;
                ScaleModels.ModelStage.prototype.draw = function (...args) {
                    globalThis.mobileStage = this;
                    return draw.apply(this, args);
                };
                app.experiences.renderer.render();
            });
            await page.waitForFunction(() => globalThis.mobileStage?.instances.get(app.experiences.item));
            await page.waitForTimeout(2000);
            await page.locator('.experience-stage-frame').scrollIntoViewIfNeeded();
            const session = await page.context().newCDPSession(page);
            const touch = (type, point) => session.send('Input.dispatchTouchEvent', {
                type, touchPoints: type === 'touchEnd' ? [] : [{ ...point, id: 1, radiusX: 2, radiusY: 2 }]
            });
            const point = await page.evaluate(() => {
                const rect = mobileStage.renderer.domElement.getBoundingClientRect();
                const item = app.experiences.item, hull = mobileStage.hulls.get(item).polygon;
                for (let y = Math.max(30, rect.top); y < Math.min(innerHeight - 90, rect.bottom - 90); y += 8) {
                    for (let x = Math.max(30, rect.left); x < Math.min(innerWidth - 55, rect.right - 55); x += 8) {
                        if (mobileStage.pick(x, y) === item) return { x, y };
                    }
                }
                throw new Error(`No visible touch target: ${item.name}, ${JSON.stringify(rect.toJSON())}, ${hull.length} hull vertices`);
            });
            await page.evaluate(() => {
                globalThis.touchObservations = { canceled: 0, moves: 0, capture: false };
                const frame = app.experiences.stageFrame;
                frame.addEventListener('pointercancel', () => touchObservations.canceled++);
                frame.addEventListener('pointermove', event => {
                    touchObservations.moves++;
                    touchObservations.capture ||= frame.hasPointerCapture(event.pointerId);
                });
            });
            await touch('touchStart', point);
            for (let step = 1; step <= 4; step++) {
                await touch('touchMove', { x: point.x + step * 9, y: point.y + step * 12 });
                await page.waitForTimeout(16);
            }
            const rotation = await page.evaluate(() => ({ ...touchObservations,
                yaw: mobileStage.rotations.get(app.experiences.item)?.yaw,
                pitch: mobileStage.rotations.get(app.experiences.item)?.pitch,
                hovered: Boolean(mobileStage.hovered) }));
            await touch('touchEnd', point);
            results.push({ test: 'touch rotation', ...rotation,
                passed: rotation.capture && rotation.moves >= 3 && !rotation.canceled && !rotation.hovered && rotation.pitch > 0.1 && rotation.yaw > 0.1 });
            const empty = await page.evaluate(() => {
                const rect = app.experiences.stageFrame.getBoundingClientRect();
                for (let y = Math.max(24, rect.top + 24); y < Math.min(innerHeight - 60, rect.bottom - 80); y += 20)
                    for (let x = 40; x < innerWidth - 90; x += 20)
                        if (!mobileStage.pick(x, y)) return { x, y };
                throw new Error('No empty pan target');
            });
            const slider = '.experience-camera-slider input';
            const beforePan = Number(await page.locator(slider).inputValue());
            await touch('touchStart', empty);
            await touch('touchMove', { x: empty.x + 45, y: empty.y + 4 });
            const duringPan = Number(await page.locator(slider).inputValue());
            await touch('touchEnd', empty);
            results.push({ test: 'immediate touch pan', before: beforePan, during: duringPan, passed: duringPan < beforePan - 0.02 });
            const range = await page.locator(slider).boundingBox();
            await touch('touchStart', { x: range.x + range.width * 0.55, y: range.y + range.height / 2 });
            await touch('touchMove', { x: range.x + range.width * 0.59, y: range.y + range.height / 2 });
            const sliderDragging = await page.locator('.experience-stage-frame').evaluate(node => node.classList.contains('is-dragging'));
            await touch('touchEnd', empty);
            results.push({ test: 'native slider is not a background drag', passed: !sliderDragging });
            const earthTarget = await page.evaluate(() => {
                const view = app.experiences;
                const index = view.items.findIndex(item => item.name === 'Earth Diameter');
                const pose = mobileStage.entry(view.items[index])?.presentation || {};
                const target = ScaleJourney.frameExponent(view.items, index, 1, {
                    widthFactor: item => mobileStage.entry(item)?.presentation?.layout_width_factor ?? 1
                }) + Math.log10(pose.focus_scale_factor || 1);
                view.focus(index);
                return target;
            });
            await page.waitForFunction(target => app.experiences.item.name === 'Earth Diameter' &&
                Math.abs(Number(document.querySelector('.experience-camera-slider input').value) - target) < 0.0001,
            earthTarget, { timeout: 45000 });
            // iPhone Safari without element fullscreen follows this same fallback path.
            await page.evaluate(() => { app.experiences.host.requestFullscreen = undefined; });
            await page.locator('.experience-fullscreen-button').click();
            await page.waitForFunction(() => app.experiences.fullscreenState?.fallback);
            await page.waitForTimeout(300);
            const fullscreen = await page.evaluate(() => {
                const view = app.experiences, host = view.host.getBoundingClientRect(), stage = view.stageFrame.getBoundingClientRect();
                const button = view.fullscreenButton.getBoundingClientRect();
                return { host: { x: host.x, y: host.y, width: host.width, height: host.height },
                    stageHeight: stage.height, overflow: view.host.scrollWidth > innerWidth + 1,
                    buttonSize: Math.min(button.width, button.height), label: view.fullscreenButton.getAttribute('aria-label') };
            });
            results.push({ test: 'mobile immersive fallback', ...fullscreen,
                passed: fullscreen.host.y === 0 && fullscreen.host.height >= 850 && fullscreen.stageHeight > 400 && !fullscreen.overflow && fullscreen.buttonSize >= 44 && fullscreen.label === 'Exit fullscreen' });
            await page.screenshot({ path: path.join(out, 'length-fullscreen.png') });
            await page.keyboard.press('Escape');
            results.push({ test: 'fallback Escape restores scrolling', passed: await page.evaluate(() => !app.experiences.fullscreenState && document.body.style.overflow !== 'hidden') });
            await page.evaluate(() => {
                app.experiences.setMode('log');
                app.experiences.setMode('interactive');
            });
            results.push({ test: 'explorer mode switch disposes touch handlers', passed: await page.evaluate(() => app.experiences.active && app.experiences.stageFrame.style.touchAction === 'none') });
            await page.evaluate(() => {
                app.experiences.host.requestFullscreen = undefined;
                app.experiences.enterFullscreen();
            });
            await page.evaluate(() => app.setDimension('angular-velocity'));
            results.push({ test: 'dimension switch exits fullscreen', passed: await page.evaluate(() => !app.experiences.fullscreenState && !document.body.classList.contains('experience-fullscreen-active') && document.body.style.overflow !== 'hidden') });
            await page.goto(`${base}/?dimension=angular-velocity&item=Ceiling%20fan`);
            await page.waitForFunction(() => globalThis.app?.experiences?.renderer?.modelStage?.instances.get(app.experiences.item));
            await page.evaluate(() => { app.experiences.host.requestFullscreen = undefined; });
            await page.locator('.experience-fullscreen-button').click();
            await page.waitForFunction(() => app.experiences.fullscreenState?.fallback);
            await page.screenshot({ path: path.join(out, 'angular-fullscreen.png') });
            results.push({ test: 'angular mobile fullscreen layout', passed: await page.evaluate(() => {
                const host = app.experiences.host;
                return host.scrollWidth <= innerWidth + 1 && app.experiences.stageFrame.getBoundingClientRect().height >= 220;
            }) });
            await page.locator('.experience-fullscreen-button').click();
            results.push({ test: 'fallback button exit', passed: await page.evaluate(() => !app.experiences.fullscreenState) });
            results.push({ test: 'mobile page errors', errors, passed: !errors.length });
        }, true);
        await withBrowser('1280x900', async (page, base, errors) => {
            await page.goto(`${base}/?dimension=length&item=Earth%20Diameter`);
            await page.waitForFunction(() => globalThis.app?.experiences?.renderer);
            await page.locator('.experience-fullscreen-button').click();
            await page.waitForFunction(() => document.fullscreenElement === app.experiences.host);
            results.push({ test: 'native desktop fullscreen', passed: true });
            await page.screenshot({ path: path.join(out, 'length-desktop-fullscreen.png') });
            await page.evaluate(() => document.exitFullscreen());
            await page.waitForFunction(() => !app.experiences.fullscreenState);
            results.push({ test: 'native browser exit restores UI', passed: await page.locator('.experience-fullscreen-button').getAttribute('aria-label') === 'Enter fullscreen' });
            results.push({ test: 'desktop page errors', errors, passed: !errors.length });
        });
        fs.writeFileSync(path.join(out, 'audit.json'), JSON.stringify(results, null, 2));
        console.log(JSON.stringify(results, null, 2));
        if (results.some(result => !result.passed)) process.exitCode = 1;
    },
    async performance({ positional, options }) {
        const name = positional[0] || 'Galaxy Diameter';
        await withBrowser(options.mobile ? '393x852' : '1280x900', async (page, base, errors) => {
            await page.goto(`${base}/?dimension=length&item=${encodeURIComponent(name)}`);
            await page.waitForFunction(() => globalThis.app?.experiences?.renderer && globalThis.ScaleModels);
            await page.evaluate(() => {
                const draw = ScaleModels.ModelStage.prototype.draw;
                ScaleModels.ModelStage.prototype.draw = function (...args) {
                    globalThis.performanceStage = this;
                    return draw.apply(this, args);
                };
                app.experiences.renderer.render();
            });
            await page.waitForFunction(() => globalThis.performanceStage?.instances.get(app.experiences.item));
            await page.waitForTimeout(2000);
            const session = options.trace ? await page.context().newCDPSession(page) : null;
            if (session) await session.send('Tracing.start', { categories: 'devtools.timeline,gpu,disabled-by-default-devtools.timeline.frame', transferMode: 'ReturnAsStream' });
            const result = await page.evaluate(async (gpu) => {
                const view = app.experiences, stage = performanceStage, times = [], intervals = [];
                const gpuCases = [];
                if (gpu) {
                    const instances = [...stage.instances].filter(([, instance]) => instance?.visible);
                    const measure = async (label, includes) => {
                        for (const [item, instance] of instances) instance.visible = includes(item);
                        const durations = [];
                        let previous;
                        for (let i = 0; i < 25; i++) {
                            const now = await new Promise(requestAnimationFrame);
                            if (i > 5) durations.push(now - previous);
                            previous = now;
                            stage.renderer.render(stage.scene, stage.camera);
                        }
                        gpuCases.push({ label, frameMedianMs: durations.sort((a,b) => a-b)[Math.floor(durations.length / 2)],
                            ...stage.renderer.info.render });
                    };
                    await measure('whole scene', () => true);
                    for (const [item] of instances) await measure(item.name, other => other === item);
                    for (const [, instance] of instances) instance.visible = true;
                }
                let bufferResizes = 0, stationaryHullReuses = 0;
                const setSize = stage.renderer.setSize.bind(stage.renderer);
                stage.renderer.setSize = (...args) => { bufferResizes++; return setSize(...args); };
                const state = { yaw: 0, pitch: 0, velocity: 0, pitchVelocity: 0, dragging: true };
                stage.rotations.set(view.item, state);
                let previous;
                for (let frame = 0; frame < 65; frame++) {
                    const now = await new Promise(requestAnimationFrame);
                    if (frame > 5 && previous) intervals.push(now - previous);
                    previous = now;
                    state.yaw += 0.015;
                    const hulls = new Map([...stage.instances].filter(([item]) => item !== view.item)
                        .map(([item, instance]) => [item, instance?.userData.projectedHull]));
                    const start = performance.now();
                    view.renderer.render();
                    if (frame > 5) times.push(performance.now() - start);
                    for (const [item, hull] of hulls)
                        if (hull && hull === stage.instances.get(item)?.userData.projectedHull) stationaryHullReuses++;
                }
                const percentile = (values, p) => [...values].sort((a, b) => a - b)[Math.floor((values.length - 1) * p)];
                const visible = [...stage.instances].filter(([, instance]) => instance?.visible).map(([item, instance]) => {
                    let points = 0, drawn = 0;
                    const clouds = [];
                    instance.traverse(node => {
                        if (!node.isPoints || !node.visible) return;
                        points += node.geometry.attributes.position.count;
                        drawn += Math.min(node.geometry.drawRange.count, node.geometry.attributes.position.count);
                        clouds.push({ name: node.name, pointSize: node.material.size, attenuated: node.material.sizeAttenuation });
                    });
                    return { name: item.name, points, drawn, pickPoints: instance.userData.pickPoints.length, ...(gpu ? { clouds } : {}) };
                });
                return { item: view.item.name, medianMs: percentile(times, 0.5), p95Ms: percentile(times, 0.95),
                    frameMedianMs: percentile(intervals, 0.5), bufferResizes, stationaryHullReuses,
                    pixelRatio: stage.renderer.getPixelRatio(), visible, ...(gpu ? { gpuCases } : {}) };
            }, Boolean(options.gpu));
            if (session) {
                const completed = new Promise(resolve => session.once('Tracing.tracingComplete', resolve));
                await session.send('Tracing.end');
                const { stream } = await completed;
                let raw = '';
                for (;;) {
                    const chunk = await session.send('IO.read', { handle: stream });
                    raw += chunk.data;
                    if (chunk.eof) break;
                }
                await session.send('IO.close', { handle: stream });
                const events = JSON.parse(raw).traceEvents, totals = {};
                for (const event of events) if (event.ph === 'X' && event.dur)
                    totals[event.name] = (totals[event.name] || 0) + event.dur / 1000;
                result.trace = Object.entries(totals).sort((a,b) => b[1]-a[1]).slice(0,25);
                if (typeof options.trace === 'string') fs.writeFileSync(options.trace, raw);
            }
            console.log(JSON.stringify({ ...result, errors }, null, 2));
        }, Boolean(options.mobile));
    },
    async angular({ positional, options }) {
        const [out = '/tmp/angular-model-lab', ...requested] = positional;
        fs.mkdirSync(out, { recursive: true });
        await withBrowser(options.size || '1280x900', async (page, base, errors) => {
            await page.goto(`${base}/?dimension=angular-velocity&item=${encodeURIComponent(options.start || 'Ceiling fan')}`);
            await page.waitForFunction(() => globalThis.app?.experiences?.renderer?.modelStage?.entries.length);
            const observations = await page.evaluate(requested => {
                const view = app.experiences;
                return view.items.map((item, index) => ({ index, name: item.name, id: item.id, value: item.value }))
                    .filter(item => !requested.length || requested.includes(item.name));
            }, requested);
            for (const name of requested) if (!observations.some(item => item.name === name)) throw new Error(`Unknown angular item: ${name}`);
            const times = options.times || options.time;
            const seconds = times == null ? [] : String(times).split(',').map(Number);
            if (seconds.some(time => !Number.isFinite(time) || time < 0)) throw new Error('--times must contain nonnegative simulated seconds');
            const results = [];
            for (const observation of observations) {
                const { name, index } = observation;
                const prefix = `${String(index).padStart(2, '0')}-${slug(name)}`;
                const modeled = await page.evaluate(index => {
                    const view = app.experiences; view.pause();
                    view.focus(index);
                    [...view.settings.querySelectorAll('button')].find(button => button.textContent === 'Fit time to item').click();
                    return !!view.modelEntry(view.item);
                }, index);
                if (modeled && /\borbit\b/i.test(name)) {
                    await page.waitForFunction(() => {
                        const view = app.experiences, stage = view.renderer.modelStage;
                        const bodies = stage.orbitalBodies(view.item);
                        return bodies && stage.instances.get(bodies.body) && stage.instances.get(bodies.center);
                    }, null, { timeout: 30000 });
                    const poses = [];
                    for (const [sample, phase] of [0, Math.PI / 2, Math.PI, 3 * Math.PI / 2].entries()) {
                        poses.push(await page.evaluate(phase => {
                            const view = app.experiences, stage = view.renderer.modelStage;
                            view.clock.time = phase / view.item.value; view.renderer.render(view.clock.time);
                            const bodies = stage.orbitalBodies(view.item);
                            const state = item => {
                                const model = stage.instances.get(item);
                                return { position: model.position.toArray(), rotation: model.quaternion.toArray(),
                                    visible: model.visible, source: stage.entry(item).source, rig: !!model.userData.angularRig };
                            };
                            return { body: state(bodies.body), center: state(bodies.center) };
                        }, phase));
                        await page.locator('.experience-stage-frame').screenshot({ path: path.join(out, `${prefix}-${sample}.png`) });
                    }
                    const centerFixed = poses.every(pose => JSON.stringify(pose.center) === JSON.stringify(poses[0].center));
                    const fixedAttitude = poses.every(pose => JSON.stringify(pose.body.rotation) === JSON.stringify(poses[0].body.rotation));
                    const moved = poses.every((pose,i) => !i || JSON.stringify(pose.body.position) !== JSON.stringify(poses[i-1].body.position));
                    const passed = centerFixed && fixedAttitude && moved && poses.every(pose =>
                        pose.body.visible && pose.center.visible && !pose.body.rig && !pose.center.rig);
                    results.push({ ...observation, orbital: true, passed, poses });
                    if (!passed) throw new Error(`Orbital body placement failed: ${name}`);
                    console.log(`${index}: ${name}: sourced 3D bodies, fixed center/attitude, moving orbiter`);
                    continue;
                }
                if (!modeled) {
                    const orbital = /\borbit\b/i.test(name);
                    for (const [sample, phase] of [0, Math.PI / 2, Math.PI, 3 * Math.PI / 2, ...seconds.map(time => time * observation.value)].entries()) {
                        await page.evaluate(phase => {
                            const view = app.experiences;
                            view.clock.time = phase / view.item.value; view.renderer.render(view.clock.time);
                        }, phase);
                        await page.locator('.experience-stage-frame').screenshot({ path: path.join(out, `${prefix}-${sample}.png`) });
                    }
                    results.push({ ...observation, orbital, missingModel: !orbital });
                    console.log(`${index}: ${name}: ${orbital ? 'circular mean-speed orbit diagram' : 'MISSING MODEL'}`);
                    continue;
                }
                await page.waitForFunction(() => {
                    const view = app.experiences;
                    return view.renderer.modelStage.instances.get(view.item)?.userData.angularRig;
                }, null, { timeout: 30000 });
                const snapshots = [];
                for (const [sample, phase] of [0, Math.PI / 2, Math.PI, 3 * Math.PI / 2, 0.37, ...seconds.map(time => time * observation.value)].entries()) {
                    snapshots.push(await page.evaluate(phase => {
                        const view = app.experiences;
                        view.clock.time = phase / view.item.value;
                        view.renderer.render(view.clock.time);
                        const instance = view.renderer.modelStage.instances.get(view.item);
                        instance.updateMatrixWorld(true);
                        const rig = instance.userData.angularRig;
                        const moving = new Set();
                        rig.rotations.forEach(({ node }) => node.traverse(child => moving.add(child)));
                        const stationary = [];
                        instance.traverse(node => { if (node.isMesh && !moving.has(node)) stationary.push(node); });
                        return { rotors: rig.rotations.map(rotation => ({ name: rotation.node.name,
                            quaternion: rotation.node.quaternion.toArray(), pivot: rotation.node.position.toArray(),
                            axis: rotation.axis.clone().transformDirection(rotation.node.matrixWorld).toArray(),
                            ratio: rotation.ratio })),
                            actualModelId: instance.userData.modelEntryId,
                            expectedModelId: view.modelEntry(view.item).id,
                            tilt: view.modelEntry(view.item).angular_motion.view_tilt || 0,
                            housing: stationary.map(node => ({ name: node.name, matrix: node.matrixWorld.toArray() })) };
                    }, phase));
                    await page.locator('.experience-stage-frame').screenshot({ path: path.join(out,
                        `${prefix}-${sample}.png`) });
                }
                const moved = snapshots[0].rotors.every((rotor, index) =>
                    rotor.quaternion.some((value, axis) => Math.abs(value - snapshots[1].rotors[index].quaternion[axis]) > 1e-6));
                const correctAsset = snapshots.every(snapshot => snapshot.actualModelId === snapshot.expectedModelId);
                const fixed = snapshots.every(snapshot => JSON.stringify(snapshots[0].housing) === JSON.stringify(snapshot.housing));
                const pivotsFixed = snapshots.every(snapshot => snapshots[0].rotors.every((rotor, index) =>
                    JSON.stringify(rotor.pivot) === JSON.stringify(snapshot.rotors[index].pivot)));
                // Capsule leveling deliberately counter-rotates about the same axis.
                const clockwiseAxial = snapshots.every(snapshot => snapshot.rotors.every((rotor, index) =>
                    Math.abs(Math.abs(rotor.axis[2]) - Math.cos(snapshot.tilt * Math.PI / 180)) < 1e-5 &&
                    (index > 0 || rotor.axis[2] * rotor.ratio < 0)));
                const frozen = await page.evaluate(() => {
                    const view = app.experiences;
                    const rig = view.renderer.modelStage.instances.get(view.item).userData.angularRig;
                    view.clock.rate = 32 * Math.PI / view.item.value;
                    view.renderer.render(0);
                    const before = rig.rotations.map(rotation => rotation.node.quaternion.toArray());
                    view.renderer.render(1.7 / view.item.value);
                    return JSON.stringify(before) === JSON.stringify(rig.rotations.map(rotation => rotation.node.quaternion.toArray()))
                        && view.stage.textContent.includes('Too fast to resolve');
                });
                results.push({ ...observation, correctAsset, moved, fixed, pivotsFixed, clockwiseAxial, frozen, snapshots });
                console.log(`${name}: asset ${correctAsset ? 'correct' : 'WRONG'}, rotor ${moved ? 'turns' : 'FAILED'}, housing ${fixed ? 'fixed' : 'MOVED'}, pivot ${pivotsFixed ? 'fixed' : 'MOVED'}, axial CW ${clockwiseAxial ? 'yes' : 'FAILED'}, high-rate ${frozen ? 'static' : 'FAILED'}`);
            }
            fs.writeFileSync(path.join(out, 'audit.json'), JSON.stringify({ results, errors }, null, 2));
            if (results.some(result => result.missingModel || (!result.orbital &&
                (!result.correctAsset || !result.moved || !result.fixed || !result.pivotsFixed || !result.clockwiseAxial || !result.frozen))) || errors.length) {
                console.log(errors); process.exitCode = 1;
            }
        });
    },
    async labels({ positional, options }) {
        const zooms = String(options.zooms || '0.35,0.6,1,1.5').split(',').map(Number);
        if (zooms.some(value => !Number.isFinite(value) || value <= 0)) throw new Error('Invalid --zooms');
        const views = String(options.views || 'rest,side').split(',');
        await withBrowser(options.size || '1280x800', async (page, base, errors) => {
            await openLab(page, base);
            const names = positional.length ? positional : (await page.evaluate(() => window.modelLab.items()))
                .filter(item => item.model).map(item => item.name);
            let checked = 0, failures = 0;
            for (const name of names) for (const view of views) for (const zoom of zooms) {
                const metrics = await page.evaluate(([name, view, zoom]) => window.modelLab.show(name, { view, zoom }),
                    [name, view, zoom]);
                if (!metrics.loaded) { failures++; console.log(`Not loaded: ${name}`); continue; }
                const collisions = await page.evaluate(() => {
                    const labels = [...document.querySelectorAll('#stage-frame .journey-object-label, #stage-frame .journey-model-label')]
                        .filter(node => getComputedStyle(node).visibility !== 'hidden' && Number(getComputedStyle(node).opacity) > 0.1)
                        .map(node => ({ text: node.textContent, ...Object.fromEntries(
                            ['left','right','top','bottom'].map(key => [key, node.getBoundingClientRect()[key]])) }));
                    return labels.flatMap((a, i) => labels.slice(i + 1).filter(b =>
                        a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top)
                        .map(b => [a.text, b.text]));
                });
                checked++;
                if (collisions.length) { failures++; console.log(JSON.stringify({ name, view, zoom, collisions })); }
            }
            console.log(`${checked} rendered label checks; ${failures} failures; ${errors.length} page errors.`);
            if (errors.length) console.log([...new Set(errors)].join('\n'));
            if (failures || errors.length) process.exitCode = 1;
        });
    },
    async coverage({ options }) {
        const minimumGap = Number(options.gap ?? 1);
        if (!Number.isFinite(minimumGap) || minimumGap < 0) throw new Error('--gap must be a nonnegative number of decades');
        await withBrowser('1000x700', async (page, base, errors) => {
            await openLab(page, base);
            const report = coverageReport(await page.evaluate(() => window.modelLab.catalog()), minimumGap);
            report.errors = [...new Set(errors)];
            if (options.json) { console.log(JSON.stringify(report, null, 2)); return; }
            console.log(`${report.modeled}/${report.total} Length items modeled; ${report.photoOnly.length} photo-only.`);
            for (const key of ['photoOnly', 'missingModelNotes', 'missingModelReferences', 'unclassifiedRepresentations'])
                console.log(`${key}: ${report[key].join(', ') || 'none'}`);
            console.log(`\nGaps of at least ${minimumGap} decades (largest first):`);
            for (const gap of report.gaps) console.log(`  ${gap.decades.toFixed(2)} decades: ${gap.lower} -> ${gap.upper}`);
            if (report.errors.length) console.log(`Page errors:\n  ${report.errors.join('\n  ')}`);
        });
    },
    async audit({ options }) {
        await withBrowser('1000x700', async (page, base, errors) => {
            await openLab(page, base);
            const items = await page.evaluate(() => window.modelLab.items());
            const results = [];
            for (const item of items) {
                if (!item.model) { results.push({ name: item.name, value: item.value, model: null, kind: 'photo' }); continue; }
                results.push(await page.evaluate(name => window.modelLab.show(name), item.name));
            }
            if (options.json) { console.log(JSON.stringify({ results, errors }, null, 1)); return; }
            for (const result of results) console.log(describe(result));
            const flagged = results.filter(result => result.warnings?.length || (result.model && !result.loaded));
            console.log(`\n${results.filter(r => r.model).length} models, ${results.filter(r => !r.model).length} photo-only items, ${flagged.length} flagged.`);
            if (errors.length) console.log(`Page errors:\n  ${[...new Set(errors)].join('\n  ')}`);
        });
    },
    async shot({ positional, options }) {
        const [out, ...names] = positional;
        if (!out || !names.length) throw new Error('Usage: shot OUT_DIR "Item" [...]');
        fs.mkdirSync(out, { recursive: true });
        const views = String(options.views || 'rest').split(',');
        await withBrowser(options.size, async (page, base, errors) => {
            await openLab(page, base);
            for (const name of names) for (const view of views) {
                const metrics = await page.evaluate(([name, settings]) => window.modelLab.show(name, settings),
                    [name, { view, background: options.bg || 'light', zoom: Number(options.zoom || 1),
                        time: options.time == null ? null : Number(options.time), neighbors: Boolean(options.neighbors) }]);
                const file = path.join(out, `${slug(name)}${views.length > 1 ? `-${view}` : ''}.png`);
                await (await page.$('#stage-frame')).screenshot({ path: file });
                console.log(`${file}\n  ${describe(metrics)}`);
            }
            if (errors.length) console.log(`Page errors:\n  ${[...new Set(errors)].join('\n  ')}`);
        });
    },
    async sheet({ positional, options }) {
        const [out] = positional;
        if (!out) throw new Error('Usage: sheet OUT.png [--filter regex] [--cols 6]');
        const filter = options.filter ? new RegExp(options.filter, 'i') : null;
        const columns = Number(options.cols || 6);
        await withBrowser('900x640', async (page, base) => {
            await openLab(page, base);
            const items = (await page.evaluate(() => window.modelLab.items()))
                .filter(item => item.model && (!filter || filter.test(item.name)));
            const tiles = [];
            for (const item of items) {
                // Match the explorer's sky: space-scale items on dark, the rest on light.
                const background = !options.bg || options.bg === 'auto' ? (item.value > 1e7 ? 'dark' : 'light') : options.bg;
                const metrics = await page.evaluate(([name, bg]) => window.modelLab.show(name, { background: bg }),
                    [item.name, background]);
                const image = (await (await page.$('#stage-frame')).screenshot({ type: 'jpeg', quality: 80 })).toString('base64');
                tiles.push({ image, caption: `${item.name}: ${metrics.loaded ? `${metrics.extent.toFixed(2)}x` : 'not loaded'}`,
                    warn: Boolean(metrics.warnings?.length || !metrics.loaded) });
            }
            const html = `<body style="margin:0;background:#1d2329;font:13px sans-serif;display:grid;
                grid-template-columns:repeat(${columns},300px);align-items:start;align-content:start;gap:6px;padding:6px;width:max-content">${tiles.map(tile =>
                `<figure style="margin:0;background:#fff"><img src="data:image/jpeg;base64,${tile.image}" style="width:300px;display:block">
                <figcaption style="padding:3px 6px;color:${tile.warn ? '#b3261e' : '#223'}">${tile.caption.replace(/</g, '&lt;')}</figcaption></figure>`).join('')}</body>`;
            await page.setViewportSize({ width: columns * 306 + 6, height: 800 });
            await page.setContent(html);
            await page.screenshot({ path: out, fullPage: true });
            console.log(`${out}: ${tiles.length} models, ${tiles.filter(tile => tile.warn).length} flagged (red captions)`);
        });
    },
    async explorer({ positional, options }) {
        const [out, ...names] = positional;
        if (!out || !names.length) throw new Error('Usage: explorer OUT_DIR "Item" [...]');
        fs.mkdirSync(out, { recursive: true });
        await withBrowser(options.size || '1280x800', async (page, base, errors) => {
            for (const name of names) {
                await page.goto(`${base}/?dimension=${options.dimension || 'length'}&item=${encodeURIComponent(name)}`);
                await page.waitForSelector('.experience-stage-frame', { timeout: 30000 });
                await page.waitForTimeout(Number(options.wait || 4500));
                const file = path.join(out, `explorer-${slug(name)}.png`);
                await (await page.$('.experience-stage-frame')).screenshot({ path: file });
                console.log(file);
            }
            if (errors.length) console.log(`Page errors:\n  ${[...new Set(errors)].join('\n  ')}`);
        });
    }
};

const args = parse(process.argv.slice(2));
if (!commands[args.command]) {
    console.error(fs.readFileSync(__filename, 'utf8').split('\n').slice(1, 19).map(line => line.replace(/^\/\/ ?/, '')).join('\n'));
    process.exit(2);
}
commands[args.command](args).catch(error => { console.error(error.stack || error); process.exit(1); });
