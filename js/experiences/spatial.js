(function (root) {
    const R = (root.ScaleRenderers = root.ScaleRenderers || {});
    const { svg, dom, Slider, number, button } = ScaleControls;
    const { log, power, clamp, countCluster } = ScaleMath;
    const line = (x1, y1, x2, y2) => svg('line', { x1, y1, x2, y2, stroke: 'currentColor', 'stroke-width': 2 });
    let worldPromise;
    function viewport(ctx) {
        const box = ctx.stage.getBoundingClientRect();
        const width = box.width < 600 ? 560 : 1000;
        const left = (1000 - width) / 2;
        ctx.stage.setAttribute('viewBox', `${left} 0 ${width} 500`);
        return { left, width, scale: Math.min(box.width / width, box.height / 500) || 1 };
    }
    function readableText(ctx, scale) {
        ctx.stage.querySelectorAll('text').forEach(text => { text.style.fontSize = `${Math.max(16, 12 / scale)}px`; });
    }
    function world() {
        return worldPromise ||= fetch('content/visualizations/land.geojson').then(r => r.json()).then(data => {
            for (const feature of data.features) {
                const polygons = feature.geometry.type === 'Polygon' ? [feature.geometry.coordinates] : feature.geometry.coordinates;
                for (const polygon of polygons)
                    if (d3.geoArea({ type: 'Polygon', coordinates: polygon }) > 2 * Math.PI)
                        polygon.forEach(ring => ring.reverse());
            }
            return data;
        }).catch(() => null);
    }
    function navigation(ctx, order, zoom, render, layoutOptions = () => ({})) {
        ctx.comparison.hidden = true;
        ctx.updateComparison = () => {};
        const camera = new ScaleJourney.Camera(zoom.value, Number(zoom.input.min), Number(zoom.input.max));
        const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
        let frame, previousTime, disposed = false;
        const apply = () => {
            zoom.set(camera.value);
            const options = layoutOptions();
            const entries = ScaleJourney.layout(ctx.items,camera.value*(options.exponentFactor??1),options.order??order,options);
            const index = entries.reduce((best,p)=>Math.abs(p.x-500)<Math.abs(entries[best].x-500)?p.index:best,0);
            if (index !== ctx.index) ctx.focus(index, false);
            render();
        };
        const animate = now => {
            if (disposed) return;
            const moving = camera.step(Math.min(0.05, (now - (previousTime ?? now - 16)) / 1000));
            previousTime = now;
            apply();
            frame = moving ? requestAnimationFrame(animate) : null;
            if (!moving) previousTime = null;
        };
        const aim = value => {
            camera.aim(value);
            if (reduceMotion.matches) { camera.snap(value); apply(); }
            else if (!frame) frame = requestAnimationFrame(animate);
        };
        const move = amount => aim(camera.target + amount);
        zoom.input.addEventListener('input', e => {
            e.stopImmediatePropagation();
            aim(Number(zoom.input.value));
        }, true);
        ctx.stageFrame.addEventListener('wheel', e => {
            e.preventDefault();
            const pixels = (Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY) * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 400 : 1);
            move(clamp(pixels * 0.0015, -0.4, 0.4));
        }, { passive: false });
        let previous, dragged = 0, velocity = 0, movedAt = 0;
        ctx.stageFrame.addEventListener('pointerdown', e => {
            if (e.button !== 0) return;
            previous = e.clientX; dragged = 0; velocity = 0; movedAt = e.timeStamp;
            camera.aim(camera.value);
            e.preventDefault();
            ctx.stageFrame.classList.add('is-dragging');
        });
        ctx.stageFrame.addEventListener('pointermove', e => {
            if (previous == null) return;
            const delta = previous - e.clientX; previous = e.clientX;
            dragged += Math.abs(delta);
            const dt = Math.max(8, e.timeStamp - movedAt) / 1000;
            movedAt = e.timeStamp;
            velocity = 0.65 * velocity + 0.35 * delta * 0.004 / dt;
            if (dragged > 5) {
                ctx.stageFrame.setPointerCapture(e.pointerId);
                move(delta * 0.004); e.preventDefault();
            }
        });
        const release = e => {
            if (previous == null) return;
            previous = null;
            if (e.type === 'pointerup' && dragged > 5 && e.timeStamp - movedAt < 100) move(clamp(velocity * 0.16, -0.6, 0.6));
            if (ctx.stageFrame.hasPointerCapture(e.pointerId)) ctx.stageFrame.releasePointerCapture(e.pointerId);
            ctx.stageFrame.classList.remove('is-dragging');
        };
        for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) ctx.stageFrame.addEventListener(event, release);
        ctx.stageFrame.addEventListener('pointerleave', e => { if (!ctx.stageFrame.hasPointerCapture(e.pointerId)) release(e); });
        ctx.stageFrame.addEventListener('dragstart', e => e.preventDefault());
        ctx.stageFrame.addEventListener('click', e => { if (dragged > 5) { e.preventDefault(); e.stopPropagation(); dragged = 0; } }, true);
        ctx.stageFrame.style.touchAction = 'pan-y';
        ctx.stageFrame.tabIndex = 0;
        ctx.stageFrame.setAttribute('aria-label', 'Scale journey. Drag or use arrow keys to zoom.');
        ctx.stageFrame.addEventListener('keydown', e => { if (['ArrowLeft', 'ArrowRight'].includes(e.key)) { e.preventDefault(); move(e.key === 'ArrowRight' ? 0.15 : -0.15); } });
        return { update: () => { ctx.updateComparison(); }, frameTo: aim,
            dispose: () => { disposed = true; cancelAnimationFrame(frame); delete ctx.updateComparison; } };
    }
    R.spatial = ctx => {
        const order = { length: 1, area: 2, volume: 3 }[ctx.dimension];
        const zoom = ctx.zoomControl(order, 'Travel through scale');
        let yaw = 0.25, land, modelStage, disposed = false;
        const widthFactor = item => order===2 && /cross-section|surface area|disk|boundary/i.test(item.name) ? 2/Math.sqrt(Math.PI)
            : order===2 && item.name==='Earth surface area' ? 1.6
            : modelStage?.entry(item) ? 1.5*(order===3&&modelStage.entry(item).geometry==='sphere'?Math.cbrt(6/Math.PI):1) : 1;
        const navigationControl = navigation(ctx, order, zoom, render, () => ({widthFactor}));
        ctx.host.classList.add('experience--spatial');
        ctx.live.hidden = true;
        const ruler = dom('div', 'experience-corner-ruler');
        const rulerLine = dom('span');
        const rulerLabel = dom('span');
        ruler.append(rulerLine, rulerLabel); ctx.stageFrame.append(ruler);
        const attachModels = () => {
            if (disposed || modelStage || !root.ScaleModels) return;
            modelStage = new ScaleModels.ModelStage(ctx, render); render();
        };
        window.addEventListener('scale-models-ready', attachModels);
        attachModels();
        if (order === 2) world().then(data => { land = data; if (!disposed) render(); });
        function render() {
            if (disposed) return;
            ctx.stage.replaceChildren(); modelStage?.begin();
            const view = viewport(ctx);
            const blend = (a,b,t) => a.map((v,i)=>Math.round(v+(b[i]-v)*clamp(t,0,1)));
            const sky = zoom.value<1 ? blend([250,252,255],[162,214,250],(zoom.value+3)/4)
                : zoom.value<7 ? blend([162,214,250],[71,151,212],(zoom.value-1)/6)
                : blend([71,151,212],[4,11,29],(zoom.value-7)/6);
            const fg = zoom.value < 8 ? 25 : 235;
            ctx.stageFrame.style.background = `radial-gradient(ellipse at 35% 35%,rgb(${sky.join(',')}),rgb(${sky.map(v=>Math.max(0,v-8)).join(',')}))`;
            ctx.stage.style.color = `rgb(${fg},${fg},${fg})`;
            ruler.style.color = ctx.stage.style.color;
            const entries = ScaleJourney.layout(ctx.items, zoom.value, order, {...view,widthFactor});
            const labels = [];
            let renderedModels = 0;
            let clipped = false;
            entries.filter(p => p.visible).forEach(({item, x, y, size}) => {
                if (size * view.scale < 0.2) return;
                const entry = modelStage?.entry(item);
                // A sphere's diameter differs from the cube root of its volume.
                const visualSize = order === 3 && entry?.geometry === 'sphere' ? size * Math.cbrt(6 / Math.PI) : size;
                const extent = order === 2 && /cross-section|surface area|disk|boundary/i.test(item.name) ? size * 2/Math.sqrt(Math.PI) : visualSize;
                clipped ||= y - extent < 0 || x - extent/2 < view.left || x + extent/2 > view.left + view.width;
                const g = ctx.object(ctx.stage, item, x, y, visualSize, visualSize, { image: false });
                const isModel = order !== 2 && modelStage?.draw(item, x, y, visualSize, yaw);
                if (isModel) renderedModels++;
                else if (order === 2 && item.name === 'Earth surface area' && land) {
                    const projection = d3.geoEqualEarth().scale(1).translate([0, 0]);
                    const path = d3.geoPath(projection);
                    projection.scale(size / Math.sqrt(path.area({ type: 'Sphere' })));
                    const mapBottom = path.bounds({ type: 'Sphere' })[1][1];
                    projection.translate([x, y - mapBottom]);
                    g.append(svg('path', { d: path({ type: 'Sphere' }), fill: '#719ec0', stroke: 'currentColor' }));
                    g.append(svg('path', { d: path(land), fill: '#64875c' }));
                } else {
                    const src = ctx.image(item);
                    if (order === 2) {
                        const circular = /cross-section|surface area|disk|boundary/i.test(item.name);
                        if (circular) g.append(svg('circle', { cx:x, cy:y-size/Math.sqrt(Math.PI), r:size/Math.sqrt(Math.PI), class:'shape' }));
                        else g.append(svg('rect', { x:x-size/2,y:y-size,width:size,height:size,class:'shape',rx:2 }));
                    }
                    if (src) g.append(svg('image', { href:src, x:x-size/2,y:y-size,width:size,height:size,
                        preserveAspectRatio:'xMidYMax meet', opacity:order===2?0.6:1 }));
                    else if (order !== 2) g.append(svg('circle', { cx:x,cy:y-size/2,r:size/2,class:'shape' }));
                }
                const fontSize = 20 * size / 200;
                if (fontSize * view.scale > 0.5) {
                    const text = svg('text',{x,y:y+fontSize*1.8,'text-anchor':'middle',class:'journey-object-label',style:`font-size:${fontSize}px`},item.name);
                    labels.push(text);
                }
            });
            ctx.stage.append(...labels);
            modelStage?.finish();
            rulerLine.style.width = `${200 * view.scale}px`;
            rulerLabel.textContent = `${number(power(zoom.value))} m`;
            ctx.caption.textContent = order === 1
                ? 'All objects share a continuous camera. The ruler and image span use the listed length; image framing is approximate. Spacing is arranged for reading, not physical distance. Distances, radii and object diameters retain their dataset definitions. Downloaded models are used when available.'
                : order === 2
                ? 'Outlined disks or squares have the listed area; photos identify the subject and do not define its outline. Earth uses an Equal Earth map whose entire footprint includes land and ocean. This is a continuous area journey, not a geographic map. Model/photo sources and geometry conventions are documented with the assets.'
                : 'Downloaded spherical models are sized using diameter = (6V/pi)^(1/3). Non-spherical models and photos use an equivalent-volume span V^(1/3), not a measured physical outline or mesh volume. A bottle capacity is not the volume of its glass. Object spacing is editorial, not a real spatial distribution.';
            ctx.attribution.replaceChildren();
            const current = modelStage?.entry(ctx.item);
            if (current) { const a=dom('a','',`3D: ${current.author} · ${current.license}`); a.href=current.source;a.target='_blank';a.rel='noopener noreferrer';ctx.attribution.append(a); }
            navigationControl.update();
        }
        return { render, focus: frame => { if (frame) navigationControl.frameTo(ScaleJourney.frameExponent(ctx.items,ctx.index,order,{widthFactor})); },
            dispose: () => { disposed=true; ctx.host.classList.remove('experience--spatial'); modelStage?.dispose(); window.removeEventListener('scale-models-ready',attachModels); navigationControl.dispose(); } };
    };
    function board(parent, x, y, width, seed) {
        const cell=width/20;
        parent.append(svg('rect',{x,y,width,height:width,fill:'#dcb779',stroke:'#735329'}));
        for(let i=1;i<=19;i++) { parent.append(line(x+cell,y+i*cell,x+width-cell,y+i*cell));parent.append(line(x+i*cell,y+cell,x+i*cell,y+width-cell)); }
        for(let r=2;r<19;r+=2) for(let c=2;c<19;c+=2) {
            seed=(1664525*seed+1013904223)>>>0;
            if(seed%3)parent.append(svg('circle',{cx:x+c*cell,cy:y+r*cell,r:cell*.43,fill:seed%2?'#202020':'#fafafa'}));
        }
    }
    R.counts = ctx => {
        const zoom=ctx.zoomControl(1,'Count window');
        let examples=0,disposed=false;
        const nav=navigation(ctx,1,zoom,render,()=>({order:2,exponentFactor:.5}));
        const variants=button(ctx.settings,'Different Go examples',()=>{examples++;render();});
        function render(){
            if(disposed)return;
            ctx.stage.replaceChildren();
            const view=viewport(ctx);
            const each=power(Math.max(0,Math.ceil(zoom.value-3.5)));
            const rows=ScaleJourney.layout(ctx.items,zoom.value/2,2);
            const defs=svg('defs'); ctx.stage.append(defs);
            let totalShown=0, imagesShown=false, clipped=false;
            variants.hidden=!/Legal Go positions/i.test(ctx.item.name);
            for(const {item,x,y,size} of rows.filter(p=>p.visible&&p.size>1&&p.size<=5000)){
                const g=ctx.object(ctx.stage,item,x,y,size,size,{image:false});
                const go=/Legal Go positions/i.test(item.name);
                if(go) {
                    const w=Math.min(210,size)/2;
                    for(let i=0;i<4;i++)board(g,x-w+(i%2)*w,y-2*w+Math.floor(i/2)*w,w-4,examples*7+i+1);
                }else{
                    const represented=item.value/each, visible=Math.min(12000,Math.floor(represented));
                    totalShown+=visible;
                    clipped ||= represented > 12000;
                    const columns=Math.max(1,Math.ceil(Math.sqrt(visible)));
                    const extent=Math.min(800,size), cell=extent/columns;
                    const src=ctx.image(item);
                    const id=`count-tile-${ctx.items.indexOf(item)}`;
                    const pattern=svg('pattern',{id,patternUnits:'userSpaceOnUse',x:x-extent/2,y:y-extent,width:cell,height:cell});
                    if(src) {
                        pattern.append(svg('image',{href:src,x:cell*.07,y:cell*.07,width:cell*.86,height:cell*.86,preserveAspectRatio:'xMidYMid meet'}));
                        imagesShown=true;
                    } else pattern.append(svg('circle',{cx:cell/2,cy:cell/2,r:cell*.34,fill:'var(--accent-color)'}));
                    defs.append(pattern);
                    // A tiled image pattern draws thousands of replicas without thousands of DOM nodes.
                    const fullRows=Math.floor(visible/columns), remainder=visible%columns;
                    if(fullRows)g.append(svg('rect',{x:x-extent/2,y:y-extent,width:extent,height:fullRows*cell,fill:`url(#${id})`,'data-replicas':fullRows*columns}));
                    if(remainder)g.append(svg('rect',{x:x-extent/2,y:y-extent+fullRows*cell,width:remainder*cell,height:cell,fill:`url(#${id})`,'data-replicas':remainder}));
                    if(represented<1)g.append(svg('circle',{cx:x,cy:y-size/2,r:size/2,fill:'var(--accent-color)'}));
                }
                if(item===ctx.item)ctx.label(item,500,405);
            }
            ctx.stage.append(svg('text',{x:view.left+20,y:485},`1 ${imagesShown?'tile':'dot'} = ${number(each)} counted units`));
            readableText(ctx, view.scale);
            ctx.live.textContent=`${ctx.index+1} / ${ctx.items.length} · ${/Legal Go positions/i.test(ctx.item.name)?'Four legal examples, not an enumeration':`${totalShown.toLocaleString()} replicas drawn${clipped?' · Larger neighbors truncated at 12,000':''}`}`;
            ctx.caption.textContent='The image tiles identify what is being counted, using illustrative photographs rather than measured outlines. A tile represents one object only when its multiplier is 1; otherwise it represents the explicit cluster size shown. All items share that multiplier. Totals below one cluster shrink in dot area; large neighboring totals are truncated at 12,000 tiles. Zoom closer to enlarge the tiles, or out to change the cluster multiplier. Count alternatives (such as Go positions) are not physically coexisting objects. The four Go boards are valid illustrative positions, not a uniform random sample.';
            nav.update();
        }
        return {render,focus:frame=>{if(frame)nav.frameTo(2*ScaleJourney.frameExponent(ctx.items,ctx.index,2));},dispose:()=>{disposed=true;nav.dispose();}};
    };
})(globalThis);
