// Separate dimension calibrations; never duplicate or alter the licensed source GLBs.
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { readScene, measureVolume } from './mesh_volume.mjs';
const root = new URL('../', import.meta.url);
const registryPath = new URL('content/visualizations/models.json', root);
const text = fs.readFileSync(registryPath, 'utf8'), registry = JSON.parse(text);
const mappings = JSON.parse(fs.readFileSync(new URL('handoff/planet-area-volume/entries.json', root))).volume_mappings;
const entries = [];
for (const mapping of mappings) {
    const source = registry.models.find(m => m.id === mapping.asset_id);
    if (!source) throw Error('Missing source: ' + mapping.asset_id);
    const file = new URL(source.src, root);
    if (createHash('sha256').update(fs.readFileSync(file)).digest('hex') !== source.sha256)
        throw Error('Source checksum changed: ' + source.id);
    const stats = measureVolume(await readScene(file));
    const entry = structuredClone(source);
    entry.id = 'volume-' + mapping.item.replace(/ volume$/, '').toLowerCase();
    entry.geometry = 'mesh';
    entry.matches = { volume: [mapping.item] };
    entry.volume_semantics = 'closed_mesh_volume_scaled_to_representative_quantity';
    entry.closed_volume_checked = true;
    entry.presentation = { ...source.presentation, reference_size: stats.referenceSize,
        display_extent_factor: 1.4, layout_width_factor: 1.4, focus_scale_factor: 1.4 };
    delete entry.presentation.measure_axis;
    delete entry.presentation.measure_fraction;
    entry.note = source.note + ' For this Volume view, the enclosed source mesh is uniformly scaled to the volume derived from JPL\'s equivalent-volume mean radius. No new geometry is created. Rings, satellites and any atmosphere beyond the reference globe are excluded.';
    entry.processing = { ...source.processing, volume_calibration: { ...stats,
        script: 'scripts/register_planet_volumes.mjs', source_model_id: source.id, source_glb_sha256: source.sha256 } };
    entry.additional_sources = [...(source.additional_sources || []),
        { label: 'Radius and volume convention', url: 'https://ssd.jpl.nasa.gov/planets/phys_par.html' }];
    entries.push(entry);
    console.log(entry.id, stats.volume, 'source units cubed');
}
const desired = structuredClone(registry);
for (const entry of entries) {
    const index = desired.models.findIndex(m => m.id === entry.id);
    if (index < 0) desired.models.push(entry); else desired.models[index] = entry;
}
const matches = new Set();
for (const entry of desired.models) for (const name of entry.matches?.volume || []) {
    if (matches.has(name)) throw Error('Duplicate mapping: ' + name);
    matches.add(name);
}
if (process.argv.includes('--check')) {
    if (JSON.stringify(desired) !== JSON.stringify(registry)) throw Error('Stale planet volume calibration');
} else {
    const pending = new Map(entries.map(e => [e.id, e]));
    const serialize = entry => JSON.stringify(entry, null, 2).split('\n').map(line => '    ' + line).join('\n');
    let updated = text.replace(/^    \{\n[\s\S]*?^    \}(,?)/gm, (block, comma) => {
        let entry; try { entry = JSON.parse(comma ? block.slice(0, -1) : block); } catch { return block; }
        const next = pending.get(entry.id); if (!next) return block;
        pending.delete(entry.id);
        return JSON.stringify(entry) === JSON.stringify(next) ? block : serialize(next) + comma;
    });
    if (pending.size) updated = updated.replace(/\n  \],\n  "coverage_gaps"/,
        ',\n' + [...pending.values()].map(serialize).join(',\n') + '\n  ],\n  "coverage_gaps"');
    if (JSON.stringify(JSON.parse(updated)) !== JSON.stringify(desired)) throw Error('Registry merge failed');
    fs.writeFileSync(registryPath, updated);
}
