import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { orbitalAssets, orbitalEntry } from '../js/experiences/angular-orbits.js';

test('all seven distinct orbital observations reuse local credited bodies without modifying spin or length entries', () => {
    const registry = JSON.parse(fs.readFileSync(new URL('../content/visualizations/models.json', import.meta.url)));
    const before = JSON.stringify(registry);
    const names = fs.readFileSync(new URL('../data/angular-velocity.yaml', import.meta.url), 'utf8')
        .split('\n').filter(line => /^  name: .*\borbit\b/.test(line)).map(line => line.slice(8));
    assert.equal(names.length, 7);
    assert.ok(names.includes('Moon orbit around Earth'));
    assert.ok(!names.includes('Moon orbit'));
    for (const name of names) {
        const assets = orbitalAssets({name}, registry.models);
        assert.ok(assets, name);
        assert.equal(assets.center.id, /Moon|ISS/.test(name) ? 'nasa-earth' : 'nasa-sun');
        for (const entry of [assets.body, assets.center]) {
            assert.ok(fs.existsSync(new URL(`../${entry.src}`, import.meta.url)));
            assert.ok(entry.source && entry.license && entry.sha256);
        }
        const entry = orbitalEntry({name}, registry.models);
        assert.equal(entry.angular_motion, undefined, 'orbital rate does not become an axial spin rate');
        assert.equal(entry.src, assets.body.src);
        assert.match(entry.note, /not to scale/);
        assert.match(entry.note, /attitude is held fixed/);
    }
    assert.equal(JSON.stringify(registry), before);
    assert.equal(orbitalAssets({name: 'Earth rotation'}, registry.models), null);
    assert.equal(orbitalEntry({name: 'Moon orbit'}, []), null);
});
