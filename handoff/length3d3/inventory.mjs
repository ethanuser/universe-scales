// Browser-free inventory only. Does not certify meshes, framing, or rendering.
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { proceduralLength } from '../../js/experiences/procedural-models.js';

const root = new URL('../../', import.meta.url);
const read = name => fs.readFileSync(new URL(name, root));
const registry = JSON.parse(read('content/visualizations/models.json')).models;
const items = JSON.parse(read('exports/json/dimensions/length.json')).items
    .filter(item => item.value > 0).sort((a, b) => a.value - b.value);
// Same precedence as ModelStage.entry(): procedural override, then exact match.
const catalog = items.map(item => ({ name: item.name, value: item.value,
    model: proceduralLength[item.name]?.id ||
        registry.find(entry => entry.matches?.length?.includes(item.name))?.id || null }));
const photoOnly = catalog.filter(item => !item.model).map(item => item.name);
const prior = JSON.parse(read('handoff/length-source-completion/ledger.json'));
if (JSON.stringify(photoOnly) !== JSON.stringify(prior.items.map(item => item.name)))
    throw new Error('Current photo-only inventory differs from the previous ledger; reconcile it first.');
const result = {
    method: 'Browser-free inventory: current Length export, actual imported proceduralLength overrides, exact-name registry lookup. No browser or mesh validation.',
    inputs: Object.fromEntries(['exports/json/dimensions/length.json',
        'content/visualizations/models.json', 'js/experiences/procedural-models.js'].map(name =>
        [name, createHash('sha256').update(read(name)).digest('hex')])),
    total: items.length, modeled: catalog.filter(item => item.model).length, photoOnly,
    previous_ledger_matches: true,
};
fs.writeFileSync(new URL('coverage.json', import.meta.url), JSON.stringify(result, null, 2) + '\n');
console.log(`${result.modeled}/${result.total} modeled; ${photoOnly.length} photo-only; previous ledger agrees.`);
