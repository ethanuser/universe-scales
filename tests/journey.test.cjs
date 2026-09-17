const {test}=require('node:test');
const assert=require('node:assert/strict');
const {layout,frameExponent,Camera,BASELINE}=require('../js/experiences/journey.js');
test('wide footprints never overlap, including equal-size records and sphere areas',()=>{
    const items=[1,1,1.5,4,8,100].map(value=>({value}));
    for(const e of [-1,0,.5,1,2]){
        const rows=layout(items,e,1,{widthFactor:()=>1.9});
        for(let i=1;i<rows.length;i++)assert.ok(rows[i].x-rows[i].width/2>=rows[i-1].x+rows[i-1].width/2);
    }
});
test('culling uses actual bounds and objects do not disappear at a size threshold',()=>{
    const items=[1,10,10000].map(value=>({value}));
    for(let e=-2;e<5;e+=.02)for(const p of layout(items,e))assert.equal(p.visible,p.x+p.width/2>=0&&p.x-p.width/2<=1000);
});
test('horizontal motion has continuous velocity through item sizes and screen center',()=>{
    const items=[1,1,10,100].map(value=>({value}));
    for(const center of [0,1,frameExponent(items,2)]){
        const h=1e-5,a=layout(items,center-h),b=layout(items,center),c=layout(items,center+h);
        b.forEach((p,i)=>assert.ok(Math.abs((p.x-a[i].x)/h-(c[i].x-p.x)/h)<.5));
    }
});
test('framing solves the camera position instead of changing object world positions',()=>{
    const items=[1,1,10,100].map(value=>({value}));
    items.forEach((_,i)=>assert.ok(Math.abs(layout(items,frameExponent(items,i))[i].x-500)<1e-8));
});
test('every item keeps the same baseline throughout a camera move',()=>{
    const items=[1e-10,.1,1,10,1e20].map(value=>({value}));
    for(const exponent of [-8,-1,0,.3,1,10]) assert.ok(layout(items,exponent).every(p=>p.y===BASELINE));
});
test('equal-sized neighboring items do not cause a camera discontinuity',()=>{
    const items=[1,10,10,100].map(value=>({value}));
    const a=layout(items,1-1e-7),b=layout(items,1+1e-7);
    a.forEach((p,i)=>assert.ok(Math.abs(p.x-b[i].x)<.01));
});
test('camera eases over multiple frames and converges without overshooting',()=>{
    const camera=new Camera(0,-2,2);camera.aim(1);
    let previous=0;
    for(let frame=0;frame<180;frame++){
        camera.step(1/60);assert.ok(camera.value>=previous&&camera.value<=1);previous=camera.value;
        if(frame===0)assert.ok(camera.value>0&&camera.value<.1);
    }
    assert.equal(camera.value,1);assert.equal(camera.velocity,0);
});
test('camera is refresh-rate independent and clamps its target to the corpus',()=>{
    const a=new Camera(0,-2,2),b=new Camera(0,-2,2);a.aim(10);b.aim(10);
    for(let i=0;i<30;i++)a.step(1/60);
    for(let i=0;i<60;i++)b.step(1/120);
    assert.ok(Math.abs(a.value-b.value)<1e-12);assert.equal(a.target,2);
    a.snap(-10);assert.equal(a.value,-2);assert.equal(a.velocity,0);
});
test('journey considers the whole corpus, not the selected pair',()=>{
    const items=[.1,.3,1,3,10].map(value=>({value}));
    assert.equal(layout(items,0).length,5);
    assert.ok(layout(items,0).filter(p=>p.visible).length>=3);
});
test('length/area/volume ratios remain dimensionally correct',()=>{
    for(const order of [1,2,3]){
        const entries=layout([{value:1},{value:8}],0,order);
        assert.ok(Math.abs((entries[1].size/entries[0].size)**order-8)<1e-8);
    }
});
test('camera position is continuous across neighboring anchors',()=>{
    const items=[1,10,100].map(value=>({value}));
    const a=layout(items,1-1e-6),b=layout(items,1+1e-6);
    for(let i=0;i<3;i++)assert.ok(Math.abs(a[i].x-b[i].x)<.02);
});
test('distant shapes retain exact size and finite positions for culling',()=>{
    const entries=layout([{value:1e-35},{value:1},{value:1e90}],0);
    assert.ok(Math.abs(entries[2].size/2e92-1)<1e-12);
    assert.ok(entries.every(e=>Number.isFinite(e.x)&&Number.isFinite(e.size)));
});
