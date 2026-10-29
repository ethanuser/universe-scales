// Reuse already licensed assets without copying or changing any model geometry.
// node scripts/register_volume_reuse.mjs [--check]
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { measureVolume, readScene } from './mesh_volume.mjs';

const root = new URL('../', import.meta.url);
const registryPath = new URL('content/visualizations/models.json', root);
const originalText = fs.readFileSync(registryPath, 'utf8');
const registry = JSON.parse(originalText);
const original = JSON.stringify(registry);
const reference = 'content/visualizations/models/sources/volume-reuse.md';
const configs = [
    { sourceId: 'sand-atlas-caicos-ooid-80', id: 'volume-sand-atlas-ooid', name: 'Grain of sand volume',
        hash: 'fa38bd147e40a1b3fb36c296f9611701b691b1884c0f9516063e17cbf6643e13', extent: 1.9,
        note: 'A micro-CT-derived Caicos carbonate ooid (Sand Atlas particle 00080), uniformly rescaled to the representative volume listed here. The enclosed volume of the existing smoothed surface, not its longest dimension or bounding box, sets the scale. This is not the original scanned grain\'s measured volume, nor a quartz grain; sand has no universal shape. Original vertices, faces and materials are unchanged from the credited Length asset.' },
    { sourceId: 'sketchfab-red-blood-cell', id: 'volume-educational-rbc', name: 'Red blood cell volume',
        hash: '775b9af388386acab5eec230407e8f4b2771ef442bda21f0072a02b23f6eab2c', extent: 2.3,
        note: 'IMU eLearning\'s existing biconcave red-blood-cell teaching model, not a microscopy reconstruction. The enclosed mesh volume is uniformly scaled to the listed representative 90 femtoliters. No geometry is redrawn; its shape is illustrative and individual cells vary. This uses mesh volume, not the cube of the cell diameter. The separate Length entry remains calibrated by diameter.' },
];
const measurements = [];
for (const c of configs) {
    const source = registry.models.find(m => m.id === c.sourceId);
    if (!source) throw new Error(`Missing source ${c.sourceId}`);
    const file = new URL(source.src, root);
    if (createHash('sha256').update(fs.readFileSync(file)).digest('hex') !== c.hash || source.sha256 !== c.hash)
        throw new Error(`Source changed: re-audit ${c.sourceId}`);
    const stats = measureVolume(await readScene(file));
    const entry = structuredClone(source);
    entry.id = c.id;
    entry.matches = { volume: [c.name] };
    entry.reference = reference;
    entry.note = c.note;
    entry.representation = c.sourceId.startsWith('sand') ? 'data-derived' : 'illustration';
    entry.volume_semantics = 'closed_mesh_volume_scaled_to_representative_quantity';
    entry.closed_volume_checked = true;
    entry.presentation = { ...source.presentation, reference_size: stats.referenceSize,
        layout_width_factor: c.extent, display_extent_factor: c.extent, focus_scale_factor: c.extent };
    delete entry.presentation.measure_axis;
    delete entry.presentation.measure_fraction;
    entry.processing.operations = entry.processing.operations.filter(op => !op.startsWith('Normalize scanned maximum extent'));
    entry.processing.operations.push('Uniformly normalize the enclosed source mesh volume to the representative Volume datum at render time');
    entry.processing.volume_calibration = { script: 'scripts/register_volume_reuse.mjs',
        source_model_id: c.sourceId, source_glb_sha256: c.hash, ...stats,
        method: 'Signed tetrahedral sum after source node transforms; one connected, consistently oriented closed shell; seam copies welded only for topology. No geometry edits. Self-intersection is not certified by this topology check.' };
    const index = registry.models.findIndex(m => m.id === c.id);
    if (index === -1) registry.models.push(entry); else registry.models[index] = entry;
    measurements.push({ id: c.id, ...stats });
}
const jupiter = registry.models.find(m => m.id === 'nasa-jupiter');
if (!jupiter || jupiter.geometry !== 'sphere' || jupiter.volume_semantics !== 'analytic_sphere')
    throw new Error('Jupiter spherical calibration changed');
if (!jupiter.matches.volume.includes('Jupiter volume')) jupiter.matches.volume.push('Jupiter volume');
const matches = new Set();
for (const entry of registry.models) for (const name of entry.matches?.volume || []) {
    if (matches.has(name)) throw new Error(`Duplicate Volume mapping: ${name}`);
    matches.add(name);
}
if (process.argv.includes('--check')) {
    if (original !== JSON.stringify(registry)) throw new Error('Volume calibration registry is stale');
} else {
    // Preserve unrelated entry formatting and escaped prose. Only update this batch.
    const updated = new Map(registry.models.filter(m => configs.some(c => c.id === m.id) || m.id === 'nasa-jupiter')
        .map(m => [m.id, m]));
    const serialize = entry => JSON.stringify(entry, null, 2).split('\n').map(line => '    ' + line).join('\n');
    let text = originalText.replace(/^    \{\n[\s\S]*?^    \}(,?)/gm, (block, comma) => {
        let entry;
        try { entry = JSON.parse(comma ? block.slice(0, -1) : block); } catch { return block; }
        const next = updated.get(entry.id);
        if (!next) return block;
        updated.delete(entry.id);
        return JSON.stringify(entry) === JSON.stringify(next) ? block : serialize(next) + comma;
    });
    if (updated.size) text = text.replace(/\n  \],\n  "coverage_gaps"/, ',\n' + [...updated.values()].map(serialize).join(',\n') + '\n  ],\n  "coverage_gaps"');
    if (JSON.stringify(JSON.parse(text)) !== JSON.stringify(registry)) throw new Error('Registry formatting merge failed');
    fs.writeFileSync(registryPath, text);
}
console.log(JSON.stringify(measurements, null, 2));
