const test = require('node:test');
const assert = require('node:assert/strict');
const { rank } = require('../js/item-search.js');

const items = [
    { name: 'Large Hadron Collider Ring', description: 'A particle accelerator ring near Geneva.' },
    { name: 'International Space Station', description: 'Crewed orbital laboratory.' },
    { name: 'Tyrannosaurus Rex SUE', description: 'A famous fossil skeleton.' },
    { name: 'Galaxy Diameter', description: 'The span of the Milky Way.' },
    { name: 'Burj Khalifa', description: 'The tallest building in the world.' },
    { name: 'Bennu', description: 'A near-Earth asteroid, roughly round but with a ridge at its equator.' }
];
const top = query => rank(items, query)[0]?.item.name;

test('names, initials, synonyms, plurals and descriptions all find items', () => {
    assert.equal(top('lhc'), 'Large Hadron Collider Ring');
    assert.equal(top('iss'), 'International Space Station');
    assert.equal(top('t rex'), 'Tyrannosaurus Rex SUE');
    assert.equal(top('dinosaur'), 'Tyrannosaurus Rex SUE');
    assert.equal(top('galaxies'), 'Galaxy Diameter');
    assert.equal(top('tallest building'), 'Burj Khalifa');
    assert.equal(top('Space-Station'), 'International Space Station');
});

test('description matches need word starts and rank below name matches', () => {
    assert.ok(!rank(items, 't rex').some(result => result.item.name === 'Bennu'));
    const results = rank(items, 'milky way');
    assert.equal(results[0].item.name, 'Galaxy Diameter');
    assert.equal(rank(items, 'zzz').length, 0);
});
