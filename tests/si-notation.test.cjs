const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const formattingSource = fs.readFileSync(path.join(__dirname, '../js/formatting.js'), 'utf8');
const formattingContext = { d3: { format: () => value => String(value) } };
vm.runInNewContext(`${formattingSource}\nglobalThis.TestFormatter = NumberFormatter;`, formattingContext);
const scriptSource = fs.readFileSync(path.join(__dirname, '../js/script.js'), 'utf8');
const scriptContext = { document: { addEventListener() {} } };
vm.runInNewContext(`${scriptSource}\nglobalThis.TestApp = UniversalScales;`, scriptContext);

const formatter = new formattingContext.TestFormatter('si');

test('SI prefixes cover the supported range and preserve signs and zero', () => {
    assert.equal(formatter.formatSIValue(0, 'm', 2), '0 m');
    assert.equal(formatter.formatSIValue(-0.001, 'm', 2), '-1 mm');
    assert.equal(formatter.formatSIValue(1.2e24, 'm', 2), '1.2 Ym');
    assert.equal(formatter.formatSIValue(1.2e-24, 'm', 2), '1.2 ym');
});

test('rounding carries into the next prefix and extreme values cap the prefix', () => {
    assert.equal(formatter.formatSIValue(999.9, 'm', 0), '1 km');
    assert.equal(formatter.formatSIValue(12.3456, 'm', 5), '12.3 m');
    assert.equal(formatter.formatSIValue(999.9, 'm', 5), '1 km');
    assert.equal(formatter.formatSIValue(0.000123456, 'm', 5), '123 μm');
    assert.equal(formatter.formatSIValue(1e30, 'm', 2), '1e6 Ym');
    assert.equal(formatter.formatSIValue(1e-30, 'm', 2), '1e-6 ym');
    assert.equal(formatter.formatSINumber(1.23456e30, 5), '1.23e+6Y');
});

test('powered and already-prefixed units are converted without changing their meaning', () => {
    assert.equal(formatter.formatSIValue(1e6, 'm^2', 2), '1 km²');
    assert.equal(formatter.formatSIValue(1e6, 'km^2', 2), '1 Mm²');
    assert.equal(formatter.formatSIValue(1e4, 'cm^2', 2), '1 m²');
    assert.equal(formatter.formatSIValue(0.1, 'm^2', 2), '10 dm²');
    assert.equal(formatter.formatSIValue(1e4, 'm^{2}', 2), '1 hm²');
    assert.equal(formatter.formatSIValue(60, 'min', 2), '60 min');
});

test('compound-unit prefixes multiply the whole expression and capped number prefixes remain numerically correct', () => {
    assert.equal(formatter.formatSIValue(1500, 'kg/m^3', 2), '1.5 k(kg/m³)');
    assert.equal(formatter.formatSIValue(1e10, 'm^2', 2), '10 G(m²)');
    assert.equal(formatter.formatSINumber(1e30, 2), '1e+6Y');
    assert.equal(formatter.formatSINumber(1e-30, 2), '1e-6y');
});

test('main values, alternate units, and axis ticks use selected-unit SI expressions', () => {
    const app = Object.create(scriptContext.TestApp.prototype);
    app.notationMode = 'si';
    app.currentDimension = 'length';
    app.currentUnit = 'meters';
    app.dimensionData = { scale_mode: 'log', units: [
        { name: 'meters', symbol: 'm', conversion_factor: 1 },
        { name: 'kilometers', symbol: 'km', conversion_factor: 0.001 }
    ] };
    app.formatter = formatter;
    app.convertValue = value => value;
    app.escapeHtml = value => String(value);
    app.formatUnitSymbolHTML = value => value;

    assert.equal(app.formatValueForCurrentUnit(1500, 2, true), '1.5 km');
    assert.equal(app.formatValueInUnit(1500, app.dimensionData.units[1]), '1.5 km');
    assert.equal(app.formatAxisValue(1500, 0), '2 km');
    assert.equal(app.formatTooltipValueHTML('1.5 km', 'm'), '1.5 km');
});

test('linear and logarithmic special units retain their regular numeric formatting', () => {
    const app = Object.create(scriptContext.TestApp.prototype);
    app.notationMode = 'si';
    app.currentDimension = 'sound-intensity';
    app.currentUnit = 'decibels';
    app.dimensionData = { scale_mode: 'log', units: [
        { name: 'decibels', symbol: 'dB', special_conversion: 'sound_intensity_db' }
    ] };
    app.formatter = { formatLinearNumber: value => String(value), formatSIValue: () => 'should not be used' };
    app.isLinearScale = () => false;
    app.convertValue = value => value;

    assert.equal(app.formatValueForCurrentUnit(60, 1), '60');
    assert.equal(app.formatAxisValue(1, 0), '120');
    assert.equal(app.formatValueInUnit(1e-6, app.dimensionData.units[0]), '60');
});
