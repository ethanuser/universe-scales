#!/usr/bin/env node
// Headless, textured GLB preview using the site's vendored three.js and the
// explorer's lighting. Use it to judge candidate models before importing them.
//
//   node scripts/preview_glb.cjs MODEL.glb OUT.png [--views 4] [--pitch 12]
//        [--yaw 0] [--size 1200x900] [--bg #dfe6ec] [--hide "Node name"]...
//
// Prints scene bounds, node names, triangle and draw-call counts as JSON.
// Needs playwright-core plus a Chromium build (`npx playwright install chromium`).
// PLAYWRIGHT_CORE may point at a playwright-core directory; otherwise the npx
// cache is searched.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');

function loadPlaywright() {
    const candidates = [process.env.PLAYWRIGHT_CORE, 'playwright-core'].filter(Boolean);
    const cache = path.join(os.homedir(), '.npm/_npx');
    if (fs.existsSync(cache)) for (const dir of fs.readdirSync(cache))
        candidates.push(path.join(cache, dir, 'node_modules/playwright-core'));
    for (const candidate of candidates) {
        try { return require(candidate); } catch { /* try the next location */ }
    }
    throw new Error('playwright-core not found; set PLAYWRIGHT_CORE or run `npx playwright install chromium`');
}

// playwright-core may expect a newer browser build than the one cached, so
// fall back to any cached headless shell, then to an installed Chrome.
function executablePath() {
    if (process.env.CHROMIUM_PATH) return process.env.CHROMIUM_PATH;
    const cache = path.join(os.homedir(), 'Library/Caches/ms-playwright');
    const shells = fs.existsSync(cache) ? fs.readdirSync(cache).filter(d => d.startsWith('chromium_headless_shell-')).sort().reverse() : [];
    for (const dir of shells) for (const arch of ['mac-arm64', 'mac-x64', 'linux']) {
        const candidate = path.join(cache, dir, `chrome-headless-shell-${arch}`, 'chrome-headless-shell');
        if (fs.existsSync(candidate)) return candidate;
    }
    const chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
    return fs.existsSync(chrome) ? chrome : undefined;
}

function parseArgs(argv) {
    const options = { views: 4, pitch: 12, yaw: 0, size: '1200x900', bg: '#dfe6ec', hide: [] };
    const positional = [];
    for (let index = 0; index < argv.length; index++) {
        const arg = argv[index];
        if (!arg.startsWith('--')) { positional.push(arg); continue; }
        const key = arg.slice(2), value = argv[++index];
        if (key === 'hide') options.hide.push(value);
        else options[key] = ['views', 'pitch', 'yaw'].includes(key) ? Number(value) : value;
    }
    if (positional.length !== 2) {
        console.error('Usage: node scripts/preview_glb.cjs MODEL.glb OUT.png [--views N] [--pitch DEG] [--yaw DEG] [--size WxH] [--bg COLOR] [--hide NODE]');
        process.exit(2);
    }
    [options.model, options.output] = positional.map(p => path.resolve(p));
    return options;
}

const PAGE = options => `<!doctype html><html><body style="margin:0;background:${options.bg}">
<script type="importmap">{"imports":{"three":"/js/vendor/three/three.module.min.js"}}</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from '/js/vendor/three/addons/loaders/GLTFLoader.js';
const options = ${JSON.stringify(options)};
const [width, height] = options.size.split('x').map(Number);
try {
    const gltf = await new GLTFLoader().loadAsync('/model.glb');
    const hidden = new Set(options.hide);
    const doomed = [];
    gltf.scene.traverse(node => { if (hidden.has(node.name) || hidden.has(node.userData?.name)) doomed.push(node); });
    doomed.forEach(node => node.removeFromParent());
    const scene = new THREE.Scene();
    scene.add(new THREE.HemisphereLight(0xffffff, 0x667788, 2));
    const light = new THREE.DirectionalLight(0xffffff, 2.5);
    light.position.set(-500, 800, 1500);
    scene.add(light);
    scene.add(gltf.scene);
    const bounds = new THREE.Box3().setFromObject(gltf.scene);
    const center = bounds.getCenter(new THREE.Vector3());
    const radius = bounds.getBoundingSphere(new THREE.Sphere()).radius || 1;
    const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setScissorTest(true);
    document.body.append(renderer.domElement);
    const columns = Math.ceil(Math.sqrt(options.views)), rows = Math.ceil(options.views / columns);
    const cellW = Math.floor(width / columns), cellH = Math.floor(height / rows);
    const camera = new THREE.PerspectiveCamera(30, cellW / cellH, radius / 100, radius * 100);
    for (let view = 0; view < options.views; view++) {
        const yaw = THREE.MathUtils.degToRad(options.yaw + view * 360 / options.views);
        const pitch = THREE.MathUtils.degToRad(options.pitch);
        const distance = radius / Math.sin(THREE.MathUtils.degToRad(15)) * 0.9;
        camera.position.set(center.x + distance * Math.sin(yaw) * Math.cos(pitch),
            center.y + distance * Math.sin(pitch), center.z + distance * Math.cos(yaw) * Math.cos(pitch));
        camera.lookAt(center);
        // Keep the light fixed relative to the viewer, as in the explorer.
        light.position.copy(camera.position).add(new THREE.Vector3(-0.3, 0.5, 0).multiplyScalar(distance));
        const x = (view % columns) * cellW, y = height - (Math.floor(view / columns) + 1) * cellH;
        renderer.setViewport(x, y, cellW, cellH);
        renderer.setScissor(x, y, cellW, cellH);
        renderer.render(scene, camera);
    }
    let triangles = 0, drawCalls = 0;
    const nodes = [];
    gltf.scene.traverse(node => {
        if (node.name) nodes.push(node.name);
        if (!node.isMesh) return;
        drawCalls++;
        const geometry = node.geometry;
        triangles += (geometry.index ? geometry.index.count : geometry.attributes.position.count) / 3;
    });
    const size = bounds.getSize(new THREE.Vector3());
    window.report = { bounds: { min: bounds.min.toArray(), max: bounds.max.toArray(), size: size.toArray() },
        triangles, drawCalls, nodes: nodes.slice(0, 200), nodeCount: nodes.length,
        views: 'yaw ' + options.yaw + ' + k*' + (360 / options.views) + ' deg, row-major from top-left' };
} catch (error) { window.report = { error: String(error && error.stack || error) }; }
</script></body></html>`;

module.exports = { loadPlaywright, executablePath };

if (require.main === module) (async () => {
    const options = parseArgs(process.argv.slice(2));
    const [width, height] = options.size.split('x').map(Number);
    const { chromium } = loadPlaywright();
    const browser = await chromium.launch({ executablePath: executablePath(), args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
    try {
        const page = await browser.newPage({ viewport: { width, height } });
        page.on('pageerror', error => console.error('page error:', error.message));
        await page.route('http://preview.local/**', route => {
            const url = new URL(route.request().url());
            if (url.pathname === '/') return route.fulfill({ contentType: 'text/html', body: PAGE(options) });
            if (url.pathname === '/model.glb') return route.fulfill({ contentType: 'model/gltf-binary', body: fs.readFileSync(options.model) });
            const file = path.join(ROOT, decodeURIComponent(url.pathname));
            if (!file.startsWith(path.join(ROOT, 'js')) || !fs.existsSync(file)) return route.fulfill({ status: 404, body: '' });
            return route.fulfill({ contentType: 'text/javascript', body: fs.readFileSync(file) });
        });
        await page.goto('http://preview.local/');
        await page.waitForFunction(() => window.report, null, { timeout: 120000 });
        const report = await page.evaluate(() => window.report);
        if (report.error) throw new Error(report.error);
        fs.mkdirSync(path.dirname(options.output), { recursive: true });
        await page.screenshot({ path: options.output, omitBackground: false });
        console.log(JSON.stringify({ output: options.output, ...report }, null, 1));
    } finally {
        await browser.close();
    }
})().catch(error => { console.error(error.message || error); process.exit(1); });
