const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const root = path.resolve(__dirname, '..');
const registry = JSON.parse(readFileSync(path.join(root, 'content/visualizations/models.json')));
const byId = id => registry.models.find(model => model.id === id);

test('DNA model is credited, local, and calibrated by helix width', () => {
    const model = byId('sketchfab-dna-helix');
    assert.equal(model.presentation.measure_axis, 'x');
    assert.equal(model.presentation.flatten_static, true);
    assert.match(model.source, /^https:\/\/sketchfab\.com\//);
    assert.equal(model.license, 'CC-BY-4.0');
    const audit = JSON.parse(execFileSync(process.execPath,
        ['scripts/audit_glb_geometry.mjs', model.src], { cwd: root, encoding: 'utf8' }));
    assert.ok(audit.size[1] > audit.size[0]);
    assert.ok(Math.abs(audit.size[0] - audit.size[2]) / audit.size[0] < 0.1);
    assert.ok(audit.primitives > 1000);
    assert.equal(audit.bytes, model.bytes);
});

test('virus uses a sourced 28 nm capsid rather than a generic hollow shell', () => {
    const model = byId('nih-porcine-parvovirus-capsid');
    assert.deepEqual(model.matches.length, ['Virus']);
    assert.equal(model.processing.pdb_id, '1K3V');
    assert.match(model.note, /28 nm/);
    assert.match(model.source, /^https:\/\/3d\.nih\.gov\//);
    assert.ok(model.bytes < 1_000_000);
    assert.ok(!byId('sketchfab-virus-capsid'));
    const length = JSON.parse(readFileSync(path.join(root, 'exports/json/dimensions/length.json')));
    assert.equal(length.items.find(item => item.name === 'Virus').value, 2.8e-8);
});

test('bacterium has one body with separately omitted long flagellum', () => {
    const model = byId('sketchfab-bacterium-rod');
    assert.deepEqual(model.matches.length, ['Bacteria']);
    assert.deepEqual(model.presentation.remove_nodes, ['Bacterium geo node body end']);
    assert.equal(model.presentation.measure_axis, 'x');
    assert.ok(model.presentation.measure_fraction > 0.8);
    assert.ok(!model.presentation.backing_color);
    assert.ok(!byId('sketchfab-e-coli'));
});

test('insulin example is compact and its label does not claim a measured diameter', () => {
    const model = byId('sketchfab-insulin-monomer');
    assert.deepEqual(model.matches.length, ['Protein (Small)']);
    assert.match(model.note, /monomer/);
    assert.match(model.note, /not a measured diameter/);
    assert.ok(model.bytes < 500_000);
    assert.equal(model.license, 'CC-BY-4.0');
});

test('new length and volume models have exact matches, credits, and bounded files', () => {
    const expected = {
        'sketchfab-housefly-v2': ['length', 'Housefly'],
        'family-car': ['volume', 'Family car envelope volume'],
        bucket: ['volume', 'Bucket'],
        'wine-glass': ['volume', 'Wine glass volume'],
        'freight-train-car': ['volume', 'Freight train car volume'],
        'sketchfab-isuzu-city-bus': ['volume', 'City bus envelope volume'],
        'shipping-container': ['volume', 'Shipping container'],
        'sketchfab-teaspoon': ['volume', 'Teaspoon'],
    };
    for (const [id, [dimension, name]] of Object.entries(expected)) {
        const model = byId(id);
        assert.ok(model, id);
        assert.ok(model.matches[dimension].includes(name), id);
        assert.ok(model.source && model.author && model.license_url, id);
        assert.ok(model.bytes < 3_000_000, id);
        assert.equal(readFileSync(path.join(root, model.src)).length, model.bytes);
    }
    assert.deepEqual(byId('sketchfab-housefly-v2').presentation.remove_nodes,
        ['Cylinder001_Material #175_0']);
    assert.match(byId('freight-train-car').note, /open-topped/);
    assert.match(byId('sketchfab-teaspoon').note, /not calibrated/);
});
