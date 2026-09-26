const {test}=require('node:test');
const assert=require('node:assert/strict');
const {layout,frameExponent,Camera,BASELINE}=require('../js/experiences/journey.js');
test('tight clusters remain ordered and move continuously',()=>{
    const items=[1,1,1.5,10,100].map(value=>({value}));
    for(let exponent=-1;exponent<=2;exponent+=.01){
        const entries=layout(items,exponent);
        for(let index=1;index<entries.length;index++) assert.ok(entries[index].x>entries[index-1].x);
    }
    const a=layout(items,.5-1e-6),b=layout(items,.5+1e-6);
    a.forEach((entry,index)=>{
        if (entry.visible || b[index].visible) assert.ok(Math.abs(entry.x-b[index].x)<.05);
    });
    assert.ok(Math.abs(layout(items,2)[4].x-500)<1e-8);
});
test('journey admission follows object bounds at both viewport edges',()=>{
    const items=[1,10,10000].map(value=>({value}));
    for(let e=-2;e<5;e+=.02)for(const p of layout(items,e))
        assert.equal(p.visible,p.x+p.width/2>=0&&p.x-p.width/2<=1000);
});
test('overscan keeps nearby offscreen objects mounted for natural viewport clipping',()=>{
    const items=[1,10,10000].map(value=>({value}));
    const regular=layout(items,0,1,{left:0,width:1000});
    const buffered=layout(items,0,1,{left:0,width:1000,overscan:750});
    buffered.forEach((entry,index)=>{
        assert.equal(entry.visible,
            entry.rightEdge>=-750&&entry.leftEdge<=1750);
        if(regular[index].visible) assert.equal(entry.visible,true);
    });
});
test('larger neighbors never overlap anything to their left',()=>{
    const items=[1,3,10,100,10000].map(value=>({value}));
    for(let exponent=-1;exponent<=4;exponent+=.01){
        const entries=layout(items,exponent);
        for(let index=1;index<entries.length;index++){
            const current=entries[index], previous=entries[index-1];
            assert.ok(current.leftEdge>=previous.rightEdge);
        }
    }
});
test('object world positions and clearances do not change with zoom',()=>{
    const items=[1,1.5,3,100,330,828].map(value=>({value}));
    const options={widthFactor:item=>item.value===3?2.1:1.5};
    const reference=layout(items,0,1,options);
    for(const exponent of [-1,-.25,0,.2,.8,1.5,2,2.8,3]){
        const entries=layout(items,exponent,1,options);
        entries.forEach((entry,index)=>{
            assert.equal(entry.worldX,reference[index].worldX);
            if(index){
                const previous=entries[index-1];
                assert.ok(entry.leftEdge>=previous.rightEdge-1e-7);
                assert.ok(Math.abs((entry.x-previous.x)/entry.pixelsPerUnit-
                    (entry.worldX-previous.worldX))<1e-7*Math.max(1,entry.worldX));
            }
        });
    }
});
test('near-sized neighbors use a compact, fixed clearance',()=>{
    const items=[1,1.25,1.5,2.5].map(value=>({value}));
    for(const exponent of [-1,0,.1,.5,1]){
        const entries=layout(items,exponent);
        for(let index=1;index<entries.length;index++){
            const gap=(entries[index].leftEdge-entries[index-1].rightEdge)/entries[index].size;
            assert.ok(gap>=.08-1e-8 && gap<.09,`gap ${gap} at ${exponent}`);
        }
    }
});
test('smaller objects approach the left edge while continuously shrinking',()=>{
    const items=[1,10,100,1000].map(value=>({value}));
    let previous=layout(items,0)[0], disappearance;
    for(let exponent=.01;exponent<=3;exponent+=.01){
        const entry=layout(items,exponent)[0];
        assert.ok(entry.leftEdge<previous.leftEdge);
        assert.ok(entry.x<previous.x);
        assert.ok(entry.rightEdge<previous.rightEdge);
        assert.ok(entry.size<previous.size);
        if (!entry.visible && disappearance === undefined) disappearance=entry.size;
        previous=entry;
    }
    assert.ok(disappearance<12);
});
test('framing uses the item physical scale and keeps its center footprint large',()=>{
    const items=[1,1,10,100].map(value=>({value}));
    items.forEach((_,i)=>assert.ok(Math.abs(layout(items,frameExponent(items,i))[i].size-370)<1e-8));
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
test('a selected item can be centered among equal-sized neighbors without moving objects',()=>{
    const items=[1,10,10,100].map(value=>({value}));
    const baseline=layout(items,1);
    for(const focusIndex of [1,2]){
        const entries=layout(items,1,1,{focusIndex});
        assert.ok(Math.abs(entries[focusIndex].x-500)<1e-8);
        entries.forEach((entry,index)=>assert.equal(entry.worldX,baseline[index].worldX));
        const almost=layout(items,1+1e-6,1,{focusIndex});
        assert.ok(Math.abs(almost[focusIndex].x-entries[focusIndex].x)<.01);
    }
});
test('a radius-defined cloud can be framed farther out without changing its physical span',()=>{
    const items=[{value:5.3e-11},{value:7e-11},{value:2.7e-10}];
    const exponent=Math.log10(items[0].value*4);
    const focused=layout(items,exponent,1,{focusIndex:0,focusExponent:exponent,focusWindow:1});
    assert.ok(Math.abs(focused[0].x-500)<1e-8);
    assert.ok(Math.abs(focused[0].size*4-370)<1e-8);
    assert.deepEqual(focused.map(entry=>entry.worldX),layout(items,exponent).map(entry=>entry.worldX));
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
    assert.ok(layout(items,0).some(p=>p.visible));
});
test('length/area/volume ratios remain dimensionally correct',()=>{
    for(const order of [1,2,3]){
        const entries=layout([{value:1},{value:8}],0,order);
        assert.ok(Math.abs((entries[1].size/entries[0].size)**order-8)<1e-8);
    }
});
test('readable center silhouettes move left and all visible silhouettes remain continuous',()=>{
    const items=[1,3,10,100,10000].map(value=>({value}));
    let previous=layout(items,-1);
    for(let exponent=-.999;exponent<=4;exponent+=.001){
        const entries=layout(items,exponent);
        const before=layout(items,exponent-1e-7), after=layout(items,exponent+1e-7);
        entries.forEach((entry,index)=>{
            if (entry.visible && entry.width >= 40 && entry.leftEdge >= 130) {
                assert.ok(entry.leftEdge<=previous[index].leftEdge+1e-8);
                assert.ok(entry.x<=previous[index].x+1e-8);
                assert.ok(entry.rightEdge<=previous[index].rightEdge+1e-8);
            }
            if (entry.visible)
                assert.ok(Math.abs(after[index].x-before[index].x)<.02);
        });
        previous=entries;
    }
});
test('narrow landmarks fit beside each other at their own scale',()=>{
    const items=[{value:100},{value:330},{value:828}];
    const widthFactor=item=>item.value===330?.48:item.value===828?.2:1;
    const eiffel=layout(items,Math.log10(330),1,{widthFactor});
    assert.ok(eiffel[2].leftEdge<1000);
    const burj=layout(items,Math.log10(828),1,{widthFactor});
    assert.ok(burj[1].rightEdge>0);
    assert.ok(burj[1].rightEdge<burj[2].leftEdge);
});
test('distant shapes retain exact size and finite positions for culling',()=>{
    const entries=layout([{value:1e-35},{value:1},{value:1e90}],0);
    assert.ok(Math.abs(entries[2].size/3.7e92-1)<1e-12);
    assert.ok(entries.every(e=>Number.isFinite(e.x)&&Number.isFinite(e.size)));
});
