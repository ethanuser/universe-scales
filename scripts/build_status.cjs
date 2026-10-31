#!/usr/bin/env node
// Writes content/dimension_status.json: each dimension's item counts by completeness, for the
// dimension browser, which cannot load all 63 datasets to work this out. Item levels come from
// js/item-status.js. Run it after the dataset changes; `--check` fails if the file is stale.
const fs = require('fs');
const path = require('path');
const { summarize } = require('../js/item-status.js');

const root = path.join(__dirname, '..');
const folder = path.join(root, 'exports/json/dimensions');
const target = path.join(root, 'content/dimension_status.json');
const status = {};
for (const file of fs.readdirSync(folder).filter(name => name.endsWith('.json')).sort()) {
    const data = JSON.parse(fs.readFileSync(path.join(folder, file), 'utf8'));
    status[file.replace(/\.json$/, '')] = summarize(data.items || []);
}
const text = `${JSON.stringify(status, null, 2)}\n`;
if (process.argv.includes('--check')) {
    if (!fs.existsSync(target) || fs.readFileSync(target, 'utf8') !== text) {
        console.error('content/dimension_status.json is stale: run node scripts/build_status.cjs');
        process.exit(1);
    }
    console.log('Dimension status is current.');
} else {
    fs.writeFileSync(target, text);
    console.log(`Wrote status for ${Object.keys(status).length} dimensions.`);
}
