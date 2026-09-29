// Deliberately uses the production stage: a second preview renderer can hide
// normalization, lighting, pose and animation integration bugs.
import { ModelStage } from './experiences/models.js?v=36';
import * as THREE from './vendor/three/three.module.min.js';
const $ = id => document.getElementById(id);
const dataset = await fetch('exports/json/dimensions/length.json', { cache: 'no-cache' }).then(r => r.json());
const items = dataset.items.filter(item => item.value > 0).sort((a, b) => a.value - b.value);
let filtered = items, item = items.find(i => i.name === new URLSearchParams(location.search).get('item')) || items[0];
let localEntry, blobUrl, paused = false, seconds = 0, pending, dragging, lastStatus = 0;
const context = { dimension: 'length', stageFrame: $('stage-frame'), stage: $('stage'), updateDetail: showDetail };
const stage = new ModelStage(context, queueRender, () => { showDetail(); queueRender(); });
const productionEntry = stage.entry.bind(stage);
stage.entry = current => localEntry && current === item ? localEntry : productionEntry(current);
function queueRender() { pending ||= requestAnimationFrame(render); }
function populate() {
    $('item').replaceChildren(...filtered.map(current => {
        const option = new Option(current.name, current.name); option.selected = current === item; return option;
    }));
}
function showDetail() {
    if (!item || !stage) return;
    const entry = stage.entry(item);
    $('title').textContent = `${item.name} | ${item.value.toPrecision(3)} m`;
    $('note').textContent = entry?.note || 'No registered 3D model. The explorer uses a photograph for this item.';
    $('sources').replaceChildren();
    for (const [label, url] of [['Model source', entry?.source || entry?.source_url || entry?.basis_url], ['Item source', item.source]]) {
        if (!url || !/^https?:/.test(url)) continue;
        const link = document.createElement('a'); link.textContent = label; link.href = url; link.target = '_blank'; link.rel = 'noopener';
        $('sources').append(link, '  ');
    }
    $('explorer-link').href = `./?dimension=length&item=${encodeURIComponent(item.name)}`;
}
function choose(name) {
    const next = items.find(i => i.name === name);
    if (!next) return;
    item = next; localEntry = null; $('view').value = 'rest'; $('zoom').value = '1';
    stage.rotations.clear();
    history.replaceState(null, '', `?item=${encodeURIComponent(item.name)}`);
    populate(); showDetail(); queueRender();
}
function pose() {
    const entry = stage.entry(item), resting = entry?.presentation || {};
    const presets = { front: [0, 0], side: [0, 90], top: [90, 0], back: [0, 180] };
    const chosen = presets[$('view').value];
    stage.rotations.set(item, { yaw: chosen ? (chosen[1] - (resting.yaw || 0)) * Math.PI / 180 : 0,
        pitch: chosen ? (chosen[0] - (resting.pitch || 0)) * Math.PI / 180 : 0, velocity: 0, pitchVelocity: 0 });
    queueRender();
}
function render(now) {
    pending = null;
    const selectedEntry = stage.entry(item);
    const fit = selectedEntry?.presentation?.focus_scale_factor || 1.4;
    const exponent = Math.log10(item.value * fit / Number($('zoom').value));
    stage.animationTime = paused ? seconds : null;
    context.stage.replaceChildren(); stage.begin(exponent);
    let modelsReady = 0;
    const neighbors = $('neighbors').checked;
    const instance = stage.instances.get(item);
    const bounds = instance ? new THREE.Box3().setFromObject(instance).getSize(new THREE.Vector3())
        .divideScalar(instance.scale.x) : null;
    const fittedSize = bounds ? Math.min(740 / bounds.x, 340 / bounds.y) : 370 / fit;
    const draws = neighbors ? ScaleJourney.layout(items, exponent, 1, {
        widthFactor: current => stage.entry(current)?.presentation?.layout_width_factor || 1,
        focusIndex: items.indexOf(item), focusExponent: exponent
    }).filter(draw => draw.visible && draw.size > 0.5) : [{ item, x: 500, y: 405, size: fittedSize * Number($('zoom').value) }];
    for (const draw of draws) {
        if (stage.draw(draw.item, draw.x, draw.y, draw.size)) modelsReady++;
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', draw.x); text.setAttribute('y', 440);
        text.setAttribute('text-anchor', 'middle'); text.setAttribute('class', 'journey-model-label');
        text.textContent = draw.item.name; context.stage.append(text);
    }
    stage.finish(exponent);
    if (now - lastStatus > 200 || paused) {
        const instance = stage.instances.get(item);
        const roots = instance?.userData.waveRoots || [];
        const phase = roots[0]?.userData.waveAnimation.phase;
        $('status').textContent = `${modelsReady ? 'Rendered' : selectedEntry ? 'Loading' : 'No model'} | ${selectedEntry?.id || item.name} | ${stage.renderer?.info.render.triangles || 0} triangles | ${roots.length} animated wave root(s)${phase == null ? '' : ` | phase ${phase.toFixed(3)} rad`} | ${paused ? `paused at ${seconds.toFixed(2)} s` : 'playing'} | drag to rotate`;
        lastStatus = now;
    }
}
$('search').addEventListener('input', () => { filtered = items.filter(i => i.name.toLowerCase().includes($('search').value.toLowerCase())); populate(); });
$('item').addEventListener('change', () => choose($('item').value));
for (const [id, direction] of [['previous', -1], ['next', 1]]) $(id).addEventListener('click', () => {
    choose(filtered[Math.max(0, Math.min(filtered.length - 1, filtered.indexOf(item) + direction))]?.name);
});
$('view').addEventListener('change', pose);
$('background').addEventListener('change', () => { context.stageFrame.className = `experience--spatial ${$('background').value}`; });
for (const id of ['zoom', 'neighbors']) $(id).addEventListener('input', queueRender);
function pauseAt(time) { seconds = time; paused = true; $('pause').textContent = 'Play animation'; queueRender(); }
$('pause').addEventListener('click', () => {
    if (!paused) pauseAt((performance.now() - stage.waveStart) / 1000);
    else { paused = false; stage.waveStart = performance.now() - seconds * 1000; $('pause').textContent = 'Pause animation'; queueRender(); }
});
$('step').addEventListener('click', () => pauseAt((paused ? seconds : 0) + 0.25));
$('file').addEventListener('change', () => {
    const file = $('file').files[0]; if (!file) return;
    if (blobUrl) URL.revokeObjectURL(blobUrl);
    blobUrl = URL.createObjectURL(file);
    const previous = stage.instances.get(item); if (previous) stage.scene.remove(previous);
    stage.instances.delete(item);
    localEntry = { id: `local-${file.name}-${Date.now()}`, src: blobUrl,
        note: `Local preview only: ${file.name}, ${(file.size / 1048576).toFixed(2)} MB. Not uploaded or registered. Uncalibrated longest extent normalized to 1.`, presentation: {} };
    showDetail(); queueRender();
});
context.stageFrame.addEventListener('pointerdown', event => {
    if (!stage.pick(event.clientX, event.clientY)) return;
    dragging = { x: event.clientX, y: event.clientY };
    stage.beginRotate(item, event.timeStamp); context.stageFrame.setPointerCapture(event.pointerId);
});
context.stageFrame.addEventListener('pointermove', event => {
    if (dragging) {
        stage.rotate(item, event.clientX - dragging.x, event.clientY - dragging.y, event.timeStamp);
        dragging = { x: event.clientX, y: event.clientY };
    } else stage.setHover(null, { x: event.clientX, y: event.clientY });
});
function release(event) { if (dragging) { dragging = null; stage.releaseRotate(item, event.timeStamp); } }
context.stageFrame.addEventListener('pointerup', release);
context.stageFrame.addEventListener('pointercancel', release);
context.stageFrame.addEventListener('pointerleave', () => stage.setHover(null, null));
new ResizeObserver(queueRender).observe(context.stageFrame);
window.addEventListener('pagehide', () => { stage.dispose(); if (blobUrl) URL.revokeObjectURL(blobUrl); });
populate(); showDetail(); queueRender();
