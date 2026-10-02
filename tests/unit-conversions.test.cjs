const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../js/script.js'), 'utf8');
const context = { document: { addEventListener() {} } };
vm.runInNewContext(`${source}\nglobalThis.TestApp = UniversalScales;`, context);

function appFor(dimension, units) {
    const app = Object.create(context.TestApp.prototype);
    app.currentDimension = dimension;
    app.currentUnit = units[0].name;
    app.dimensionData = { units, items: [{ value: 1 }] };
    app.notationMode = 'scientific';
    app.formatNumber = value => String(value);
    app.formatter = { formatLinearNumber: value => String(value) };
    return app;
}

test('conversion list excludes the selected and deleted units', () => {
    const units = [
        { name: 'meters', conversion_factor: 1 },
        { name: 'centimeters', conversion_factor: 100 },
        { name: 'kilometers', conversion_factor: 0.001 }
    ];
    const app = appFor('length', units);
    app.editor = { unitOverrides: { length: { 2: { isDeleted: true } } } };
    assert.deepEqual(Array.from(app.getAvailableUnits(), unit => unit.name), ['meters', 'centimeters']);
    assert.equal(app.formatValueInUnit(1.7, units[1]), '170');
});

test('decibel entries convert intensity rather than using a linear factor', () => {
    const units = [
        { name: 'watts per square meter', conversion_factor: 1 },
        { name: 'decibels', special_conversion: 'sound_intensity_db' }
    ];
    const app = appFor('sound-intensity', units);
    assert.equal(app.formatValueInUnit(1e-6, units[1]), '60');
});

test('mathematical notation remains markup when the selected unit is decibels', () => {
    const units = [
        { name: 'decibels', special_conversion: 'sound_intensity_db', symbol: 'dB' },
        { name: 'watts per square meter', conversion_factor: 1, symbol: 'W/m^2' }
    ];
    const app = appFor('sound-intensity', units);
    app.notationMode = 'mathematical';
    app.formatNumber = () => '1\u00d710<sup>-6</sup>';
    assert.match(app.formatValueInUnitHTML(1e-6, units[1]), /10<sup>-6<\/sup>/);
    assert.doesNotMatch(app.formatValueInUnitHTML(1e-6, units[1]), /&lt;sup&gt;/);
});

test('conversion panel stays open around its anchor and during text selection', () => {
    const app = appFor('length', [{ name: 'meters', conversion_factor: 1 }]);
    app.unitPopoverTrigger = {
        isConnected: true,
        getBoundingClientRect: () => ({ left: 100, right: 160, top: 100, bottom: 130 })
    };
    app.unitPopover = {
        isConnected: true,
        getBoundingClientRect: () => ({ left: 100, right: 320, top: 136, bottom: 280 })
    };
    app.unitPopoverPointer = { x: 170, y: 133 };
    assert.equal(app.isNearUnitConversions(), true);
    app.unitPopoverPointer = { x: 500, y: 500 };
    assert.equal(app.isNearUnitConversions(), false);
    app.unitPopoverSelecting = true;
    assert.equal(app.isNearUnitConversions(), true);
});
