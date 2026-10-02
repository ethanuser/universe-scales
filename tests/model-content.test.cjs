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

test('virus is the NIAID SARS-CoV-2 virion calibrated by envelope, not spikes', () => {
    const model = byId('coronavirus-sars-cov-2');
    assert.deepEqual(model.matches.length, ['Virus']);
    assert.match(model.source, /^https:\/\/3d\.nih\.gov\//);
    assert.equal(model.license, 'CC-BY-4.0');
    assert.ok(model.presentation.measure_fraction > 0.6 && model.presentation.measure_fraction < 0.75);
    assert.match(model.note, /91 nm/);
    assert.ok(model.bytes < 1_000_000);
    assert.ok(!byId('nih-porcine-parvovirus-capsid'));
    const length = JSON.parse(readFileSync(path.join(root, 'exports/json/dimensions/length.json')));
    assert.equal(length.items.find(item => item.name === 'Virus').value, 9.1e-8);
});

test('bacterium is calibrated by body length with shortened flagella', () => {
    const model = byId('sketchfab-bacterium-teal');
    assert.deepEqual(model.matches.length, ['Bacteria']);
    assert.equal(model.presentation.measure_axis, 'x');
    // Body is about 79% of the full length once the flagella are shortened.
    assert.ok(model.presentation.measure_fraction > 0.75 && model.presentation.measure_fraction < 0.85);
    assert.match(model.note, /flagella are shortened/);
    assert.ok(model.bytes < 500_000);
});

test('Everest is an opaque DEM block with a surveyed-height summit', () => {
    const model = byId('mapzen-everest-dem');
    assert.deepEqual(model.matches.length, ['Mount Everest']);
    assert.match(model.source, /terrain-tiles/);
    assert.ok(!byId('sketchfab-mount-everest'));
    const bytes = readFileSync(path.join(root, model.src));
    const jsonLength = bytes.readUInt32LE(12);
    const gltf = JSON.parse(bytes.subarray(20, 20 + jsonLength));
    assert.ok(gltf.materials.every(material => material.alphaMode !== 'BLEND'));
    const audit = JSON.parse(execFileSync(process.execPath,
        ['scripts/audit_glb_geometry.mjs', model.src], { cwd: root, encoding: 'utf8' }));
    assert.ok(Math.abs(audit.min[1]) < 0.01);
    assert.ok(Math.abs(audit.max[1] - 8848.86) < 0.01);
    assert.ok(model.bytes < 1_000_000);
});

test('Liberty is the whole authored monument, calibrated ground to torch', () => {
    const model = byId('sketchfab-statue-of-liberty-monument');
    assert.deepEqual(model.matches.length, ['Statue of Liberty']);
    assert.equal(model.license, 'CC-BY-4.0');
    assert.equal(model.presentation.measure_axis, 'y');
    assert.equal(model.presentation.measure_fraction, undefined);
    assert.match(model.note, /92\.99 m/);
    assert.ok(!byId('sketchfab-liberty-gravity-jack'));
    const length = JSON.parse(readFileSync(path.join(root, 'exports/json/dimensions/length.json')));
    assert.equal(length.items.find(item => item.name === 'Statue of Liberty').value, 92.99);
});

test('bacterium teal replaces earlier versions; mitochondrion and neuron are procedural', () => {
    assert.ok(!byId('sketchfab-mitochondrion-cristae') && !byId('sketchfab-neuron-soma'));
    assert.ok(!byId('sketchfab-mitochondrion-v2') && !byId('sketchfab-bacterium-piliated-v3'));
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
