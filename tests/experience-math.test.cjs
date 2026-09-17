const { test } = require('node:test');
const assert = require('node:assert/strict');
const M = require('../js/experiences/math.js');
const close = (a, b) =>
    assert.ok(
        Math.abs(a - b) <= 1e-10 * Math.max(Math.abs(b), 1e-100),
        `${a} != ${b}`
    );

test('length, area and volume compare the correct linear sizes', () => {
    close(M.sizeRatio(9, 1, 1), 9);
    close(M.sizeRatio(9, 1, 2), 3);
    close(M.sizeRatio(27, 1, 3), 3);
    close(M.sizeRatio(1e-90, 1e90, 3), 1e-60);
});
test('motion integrates with explicit zero initial conditions', () => {
    close(M.displacement('speed', 3, 2), 6);
    close(M.displacement('acceleration', 3, 2), 6);
    close(M.displacement('jerk', 3, 2), 4);
});
test('angle width uses a physical viewing distance and rejects flat-screen impossibilities', () => {
    close(M.angularWidth(Math.PI / 2, 1), 2);
    close(M.angularWidth(0, 1), 0);
    assert.equal(M.angularWidth(Math.PI, 1), null);
    assert.equal(M.angularWidth(2 * Math.PI, 1), null);
});
test('count rendering stays bounded across the entire corpus range', () => {
    for (const count of [12, 64, 1e6, 1e50, 1e160, 2.08e170]) {
        const c = M.countCluster(count);
        assert.ok(Number.isFinite(c.each));
        assert.ok(c.visible <= 300);
        close(c.represented * c.each, count);
    }
    assert.equal(M.countCluster(12).each, 1);
    assert.equal(M.countCluster(12).visible, 12);
    assert.ok(M.countCluster(12, 100).represented < 1);
    assert.equal(M.countCluster(1e170, 0).overflow, true);
});
test('decibels never become amplitude exponents or playback volume', () => {
    close(M.soundLevel(1e-12), 0);
    close(M.soundLevel(1e6), 180);
});
test('luminance clipping and sRGB encoding are explicit', () => {
    assert.equal(M.luminance(300, 300, 0).gray, 255);
    assert.equal(M.luminance(0, 300, 0).gray, 0);
    assert.equal(M.luminance(1e9, 300, 0.3).clipped, 'above');
    assert.equal(M.luminance(1e-10, 300, 0.3).clipped, 'below');
    assert.equal(M.luminance(0.5, 1, 0).gray, 188);
});
test('nearest camera anchor compares log size not raw area/volume', () => {
    const items = [{ value: 1 }, { value: 10000 }];
    assert.equal(M.nearest(items, 1.5, 2), items[1]);
});

test('local audio assets have traceable sources, valid containers, and matching hashes', () => {
    const fs = require('node:fs');
    const path = require('node:path');
    const { createHash } = require('node:crypto');
    const root = path.resolve(__dirname, '..');
    const manifest = JSON.parse(
        fs.readFileSync(
            path.join(root, 'content/visualizations/assets.json'),
            'utf8'
        )
    );
    for (const clip of Object.values(manifest.audio)) {
        assert.match(
            clip.source,
            /^https:\/\/(commons\.wikimedia\.org\/wiki\/File:|freesound\.org\/people\/)/
        );
        assert.ok(clip.author && clip.license && clip.title);
        const bytes = fs.readFileSync(path.join(root, clip.src));
        assert.ok(['OggS', 'RIFF'].includes(bytes.subarray(0, 4).toString()));
        if (clip.extract) {
            assert.match(clip.source_sha256, /^[a-f0-9]{64}$/);
            assert.ok(clip.extract.duration <= 6 && clip.extract.start >= 0);
            assert.ok(clip.changes);
        }
        assert.equal(
            createHash('sha256').update(bytes).digest('hex'),
            clip.sha256
        );
    }
    const land = JSON.parse(
        fs.readFileSync(
            path.join(root, 'content/visualizations/land.geojson'),
            'utf8'
        )
    );
    assert.equal(land.type, 'FeatureCollection');
    assert.ok(land.features.length > 50);
});
