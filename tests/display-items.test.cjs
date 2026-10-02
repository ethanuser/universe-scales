const {test}=require('node:test');
const assert=require('node:assert/strict');
const {displayItems}=require('../js/experiences/math.js');
test('one representative per label, retaining the better documented observation',()=>{
    const seed={name:'Ceiling fan',value:10,qualifiers:{measurement:'blade rotation'}};
    const curated={name:'ceiling fan',value:15.7,facts:{source_trace:{derivation_note:'rpm to radians',source_value_text:'150 rpm'}}};
    assert.deepEqual(displayItems([seed,curated]),[curated]);
});
test('same value alone is never an identity, and distinct conditions survive',()=>{
    const rows=[{name:'Steel',value:.5,qualifiers:{friction_type:'static'}},{name:'Steel',value:.3,qualifiers:{friction_type:'kinetic'}},{name:'Rubber',value:.5}];
    assert.equal(displayItems(rows).length,3);
});
test('does not mutate raw observations or merge distinct snapshots',()=>{
    const rows=[{name:'Menthol',value:1},{name:'menthol',value:1},{name:'Menthol',value:2,snapshot_date:'2025-01-01'}];
    assert.equal(displayItems(rows).length,2);assert.equal(rows.length,3);
});
