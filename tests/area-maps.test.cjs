const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { forward, inverse, sphereDimensions } = require('../js/experiences/area-maps.js');
test('Equal Earth round-trips positions including the poles and antimeridian', () => {
    for (const lon of [-180,-135,-15,0,45,179.99,180]) for (const lat of [-90,-80,-30,0,60,89.99,90]) {
        const p = [lon,lat].map(x=>x*Math.PI/180), q=inverse(...forward(...p));
        assert.ok(Math.abs(q[0]-p[0])<1e-9);
        assert.ok(Math.abs(q[1]-p[1])<1e-7);
    }
});
test('Equal Earth local area Jacobian equals cos(latitude), not Mercator inflation', () => {
    const h=1e-6;
    for (const lat of [-80,-50,0,30,75]) {
        const p=lat*Math.PI/180;
        const a=forward(h,p),b=forward(-h,p),c=forward(0,p+h),d=forward(0,p-h);
        const determinant=((a[0]-b[0])*(c[1]-d[1])-(c[0]-d[0])*(a[1]-b[1]))/(4*h*h);
        assert.ok(Math.abs(determinant-Math.cos(p))<1e-8);
    }
});
test('Sourced planet map footprints, not their rectangles, are calibrated to one area unit', () => {
    const root=path.resolve(__dirname,'..');
    const manifest=JSON.parse(fs.readFileSync(path.join(root,'content/visualizations/area-maps/manifest.json')));
    const registry=JSON.parse(fs.readFileSync(path.join(root,'content/visualizations/models.json'))).models;
    assert.equal(manifest.entries.length,11);
    assert.ok(sphereDimensions[0]*sphereDimensions[1]>1);
    for (const entry of manifest.entries) {
        assert.ok(Math.abs(entry.raster_area_ratio-1)<.005);
        assert.ok(entry.bytes<1500000);
        assert.equal(createHash('sha256').update(fs.readFileSync(path.join(root,entry.src))).digest('hex'),entry.sha256);
        assert.equal(registry.find(m=>m.id===entry.source_model_id).sha256,entry.source_glb_sha256);
        assert.ok(entry.note && entry.source && entry.license);
    }
});
test('Published map entries have unique display matches and pinned geographic files', () => {
    const root=path.resolve(__dirname,'..');
    const manifest=JSON.parse(fs.readFileSync(path.join(root,'content/visualizations/area-maps.json')));
    const geographic=JSON.parse(fs.readFileSync(path.join(root,'content/visualizations/area-sources/manifest.json')));
    const names=new Set(JSON.parse(fs.readFileSync(path.join(root,'exports/json/dimensions/area.json'))).items.map(i=>i.name));
    assert.equal(new Set(manifest.entries.map(e=>e.id)).size,manifest.entries.length);
    assert.equal(new Set(manifest.entries.map(e=>e.name)).size,manifest.entries.length);
    for (const entry of manifest.entries) {
        assert.ok(names.has(entry.name),entry.name);
        assert.match(entry.source,/^https:\/\//);
        assert.ok(entry.license && entry.author && entry.note);
        if (!entry.geojson) continue;
        const source=geographic.items.find(item=>item.id===entry.id);
        const bytes=fs.readFileSync(path.join(root,entry.geojson));
        assert.equal(createHash('sha256').update(bytes).digest('hex'),source.output_sha256);
        assert.equal(bytes.length,source.output_bytes);
        const data=JSON.parse(bytes);
        assert.equal(data.features.length,1);
        assert.ok(['Polygon','MultiPolygon'].includes(data.features[0].geometry.type));
    }
    assert.ok(!manifest.entries.some(e=>['Manhattan','Rhode Island'].includes(e.name)),
        'Rejected land/water boundary mismatches must not silently return');
});
