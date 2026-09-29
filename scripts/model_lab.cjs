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
//
// Needs playwright-core and a Chromium build (see scripts/preview_glb.cjs).
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { loadPlaywright, executablePath } = require('./preview_glb.cjs');

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

async function withBrowser(size, work) {
    const server = await serve();
    const base = `http://127.0.0.1:${server.address().port}`;
    const { chromium } = loadPlaywright();
    const browser = await chromium.launch({ executablePath: executablePath(),
        args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
    const [width, height] = (size || '1280x900').split('x').map(Number);
    const page = await browser.newPage({ viewport: { width, height } });
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
                grid-template-columns:repeat(${columns},300px);align-items:start;gap:6px;padding:6px;width:max-content">${tiles.map(tile =>
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
