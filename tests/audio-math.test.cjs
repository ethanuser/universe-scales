const test = require('node:test');
const assert = require('node:assert/strict');
const { playbackLevel, referenceRms, attenuationGain, digitalLevel } = require('../js/experiences/audio-math.js');

test('20 dB gives tenfold amplitude below the ceiling', () => {
    const quiet = playbackLevel(0.1, 0.5, 30);
    const louder = playbackLevel(0.1, 0.5, 50);
    assert.ok(Math.abs(louder.gain / quiet.gain - 10) < 1e-10);
});
test('recording mastering volume does not determine preview loudness', () => {
    const a = playbackLevel(0.1, 0.5, 50);
    const b = playbackLevel(0.01, 0.05, 50);
    assert.ok(Math.abs(a.gain * 0.1 - b.gain * 0.01) < 1e-12);
});
test('rocket level is capped, not reproduced', () => {
    const level = playbackLevel(0.1, 0.5, 180);
    assert.ok(level.limited);
    assert.ok(level.gain * 0.1 <= referenceRms);
    assert.ok(level.gain * 0.5 <= 0.18);
});
test('measured reference maps quieter targets and caps estimated output', () => {
    assert.equal(playbackLevel(0.1, 0.5, 50, 65, true).estimatedDb, 50);
    assert.ok(playbackLevel(0.1, 0.5, 180, 85, true).estimatedDb <= 75);
});
test('invalid and silent data are rejected', () => {
    assert.throws(() => playbackLevel(0, 0, 50));
    assert.throws(() => playbackLevel(0.1, 0.5, NaN));
    assert.throws(() => playbackLevel(Infinity, 0.5, 50));
    assert.throws(() => playbackLevel(0.1, Infinity, 50));
});
test('attenuation works after both RMS and peak limiting', () => {
    for (const [rms, peak] of [[0.1, 0.5], [0.001, 1]]) {
        const full = playbackLevel(rms, peak, 180);
        const quieter = playbackLevel(rms, peak, 180, 70, false, -20);
        assert.ok(full.limited && quieter.limited);
        assert.ok(Math.abs(quieter.gain / full.gain - 0.1) < 1e-12);
        assert.ok(Math.abs(quieter.relativeDb - full.relativeDb + 20) < 1e-12);
    }
});
test('attenuation cannot amplify or corrupt the signal', () => {
    assert.equal(attenuationGain(0), 1);
    assert.equal(attenuationGain(-40), 0.01);
    for (const bad of [1, -41, NaN, Infinity]) assert.throws(() => attenuationGain(bad));
});
test('digital meter measures RMS dBFS with a finite silence floor', () => {
    assert.equal(digitalLevel([1, -1]), 0);
    assert.equal(digitalLevel([0.1, -0.1]), -20);
    assert.equal(digitalLevel([0, 0]), -96);
    assert.equal(digitalLevel([]), -96);
    assert.equal(digitalLevel([NaN]), -96);
    assert.equal(digitalLevel([2, -2]), 0);
});
