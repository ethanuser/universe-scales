#!/usr/bin/env node
// Screenshot explorer items headlessly once the camera has settled.
//
//   node scripts/screenshot_explorer.cjs OUT_DIR "Item name" ["Another item" ...]
//        [--dimension length] [--size 1280x800] [--base http://localhost:8000]
//
// Needs the site served (python3 -m http.server 8000) and the same
// playwright-core/Chromium setup as scripts/preview_glb.cjs. Writes one PNG of
// the explorer stage per item and prints any page errors.
const fs = require('node:fs');
const path = require('node:path');
const { loadPlaywright, executablePath } = require('./preview_glb.cjs');

(async () => {
    const args = process.argv.slice(2);
    const options = { dimension: 'length', size: '1280x800', base: 'http://localhost:8000' };
    const items = [];
    for (let index = 0; index < args.length; index++) {
        if (args[index].startsWith('--')) options[args[index].slice(2)] = args[++index];
        else items.push(args[index]);
    }
    const output = items.shift();
    if (!output || !items.length) {
        console.error('Usage: node scripts/screenshot_explorer.cjs OUT_DIR "Item name" [...] [--dimension length]');
        process.exit(2);
    }
    fs.mkdirSync(output, { recursive: true });
    const [width, height] = options.size.split('x').map(Number);
    const { chromium } = loadPlaywright();
    const browser = await chromium.launch({ executablePath: executablePath(),
        args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
    try {
        const page = await browser.newPage({ viewport: { width, height } });
        page.on('pageerror', error => console.error('page error:', error.message));
        for (const item of items) {
            const url = `${options.base}/?dimension=${options.dimension}&item=${encodeURIComponent(item)}`;
            await page.goto(url);
            await page.waitForSelector('.experience-stage-frame', { timeout: 30000 });
            // Wait for the camera spring to settle and models to load.
            await page.waitForTimeout(4500);
            const frame = await page.$('.experience-stage-frame');
            const file = path.join(output, `${item.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}.png`);
            await frame.screenshot({ path: file });
            console.log(file);
        }
    } finally {
        await browser.close();
    }
})().catch(error => { console.error(error.message || error); process.exit(1); });
