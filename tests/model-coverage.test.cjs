const test = require('node:test');
const assert = require('node:assert/strict');
const { coverageReport } = require('../scripts/model_coverage.cjs');

test('coverage sorts gaps without changing the source catalog', () => {
    const catalog = [{ name: 'large', value: 1e20 }, { name: 'small', value: 1e-20 },
        { name: 'middle', value: 1 }, { name: 'bad', value: 0 }];
    const report = coverageReport(catalog, 2);
    assert.equal(report.total, 3);
    assert.deepEqual(catalog.map(item => item.name), ['large', 'small', 'middle', 'bad']);
    assert.deepEqual(report.gaps.map(gap => gap.decades), [20, 20]);
    assert.equal(report.gaps[0].midpointMeters, 1e-10);
});

test('coverage distinguishes photo fallback, missing provenance, and budget', () => {
    const report = coverageReport([
        { name: 'photo', value: 1 },
        { name: 'unknown', value: 2, model: 'mesh', note: '   ' },
        { name: 'diagram', value: 3, model: 'diagram', representation: 'measurement_diagram',
            note: 'A ruler, not a hard boundary.', basis: 'https://example.org/paper', bytes: 2 * 1024 ** 2 }
    ]);
    assert.deepEqual(report.photoOnly, ['photo']);
    assert.deepEqual(report.missingModelNotes, ['unknown']);
    assert.deepEqual(report.missingModelReferences, ['unknown']);
    assert.deepEqual(report.unclassifiedRepresentations, ['unknown']);
    assert.equal(report.oversizedAssets[0].name, 'diagram');
});
