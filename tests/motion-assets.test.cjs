const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const registry = require('../content/visualizations/motion-images.json');

test('motion image registry pins an actual local photograph and its reuse metadata', () => {
    assert.equal(registry.schema_version, 1);
    const entries = registry.images['angular-velocity'];
    assert.ok(entries['Ceiling fan']);
    const corpus = fs.readFileSync(path.join(__dirname, '../exports/frontend/angular-velocity.yaml'), 'utf8');
    for (const [name, entry] of Object.entries(entries)) {
        assert.ok(corpus.includes(`  name: ${name}\n`), `Exact item match: ${name}`);
        for (const field of ['src', 'source', 'license', 'license_url', 'author', 'note', 'changes', 'download_url']) {
            assert.ok(typeof entry[field] === 'string' && entry[field].length, `${name}: ${field}`);
        }
        assert.match(entry.src, /^content\/visualizations\/images\/motion\/[^/]+\.jpg$/);
        for (const field of ['source', 'license_url', 'download_url']) assert.equal(new URL(entry[field]).protocol, 'https:');
        const bytes = fs.readFileSync(path.join(__dirname, '..', entry.src));
        assert.equal(bytes.length, entry.bytes);
        assert.equal(bytes.subarray(0, 3).toString('hex'), 'ffd8ff', 'JPEG, not a renamed drawing');
        assert.equal(createHash('sha256').update(bytes).digest('hex'), entry.sha256);
        assert.match(entry.note, /stationary reference photo/);
    }
});
