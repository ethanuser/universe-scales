#!/usr/bin/env node
// Register this job's pinned imports/reuse with independent Volume calibration.
// node scripts/register_volume3d.mjs [--check]
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { readScene, measureVolume } from './mesh_volume.mjs';
import * as THREE from '../js/vendor/three/three.module.min.js';

const root = new URL('../', import.meta.url);
const registryPath = new URL('content/visualizations/models.json', root);
const originalText = fs.readFileSync(registryPath, 'utf8');
const registry = JSON.parse(originalText);
const configs = JSON.parse(fs.readFileSync(new URL('handoff/volume3d/imports.json', root)));
const notes = {
    'volume3d-sugar-scan': "Arkify's sugar-cube scan, uniformly scaled to the listed representative bulk volume. Scale comes from the enclosed exterior mesh volume, including the cube's pores rather than only solid sucrose. Four tiny reversed internal shells were excluded; the existing outer surface was simplified, without filling or inventing geometry. The source specimen was larger than this representative cube, and its original proportions are retained. This is not a measurement of that specimen's original volume.",
    'volume3d-classic-bathtub': "renderartestudio's ceramic clawfoot bathtub illustrates the listed representative 150 L water capacity. This is an exterior tub prop, not a mesh of water or a measured 150 L basin. Its longest source span is displayed at the cube root of the listed volume (an equivalent-volume span); neither tub-material volume nor basin capacity was measured from this open mesh. No fill level, real-world tub dimensions or enclosed-volume calibration is asserted.",
    'volume3d-nih-influenza': "NIAID's PathogenAR influenza teaching model, retaining its existing cutaway and source colors for hemagglutinin, neuraminidase and internal components. This is a scientific illustration, not a measured virion reconstruction. The complete model's longest source span is displayed at the cube root of the listed representative volume (an equivalent-volume span). The cutaway does not enclose that volume; spike extent, membrane boundary and strain-dependent particle volume are not measured here.",
    'volume3d-nih-coronavirus': "NIAID's existing SARS-CoV-2 teaching model from NIH 3D, reused without any geometry or material changes. The source combines imaging-informed modeling with authored surface and spike placement; it is not an unmodified single-particle reconstruction. The complete model, including spikes, has its longest source span displayed at the cube root of the listed representative volume (an equivalent-volume span). This is not an enclosed mesh-volume measurement or a calibrated lipid-envelope volume. The separate Length entry retains its original envelope-diameter calibration.",
};
const measurements = [];
for (const config of configs) {
    const source = config.reuse && registry.models.find(m => m.id === config.reuse);
    if (config.reuse && !source) throw new Error(`Missing reused source: ${config.reuse}`);
    const src = source?.src || `content/visualizations/models/${config.id}.glb`;
    const file = new URL(src, root);
    const hash = createHash('sha256').update(fs.readFileSync(file)).digest('hex');
    if (hash !== config.processed_sha256) throw new Error(`Re-audit changed asset: ${config.id}`);
    const entry = source ? structuredClone(source) : {
        source: config.source, author: config.author, license: config.license,
        license_url: 'https://creativecommons.org/licenses/by/4.0/',
        license_files: ['licenses/CC-BY-4.0.txt'], geometry: 'mesh', src,
        ...JSON.parse(execFileSync('python3', ['-c',
            'import sys,json;sys.path.insert(0,"scripts");from fetch_model_assets import inspect_glb;print(json.dumps(inspect_glb(open(sys.argv[1],"rb").read())))',
            fileURLToPath(file)], { cwd: fileURLToPath(root), encoding: 'utf8' })),
        source_sha256: config.source_sha256, source_bytes: config.source_bytes,
    };
    if (config.sketchfab_uid) entry.sketchfab_uid = config.sketchfab_uid;
    if (config.download_url) entry.download_url = config.download_url;
    entry.id = config.id;
    entry.matches = { volume: config.names };
    entry.reference = `content/visualizations/models/sources/${config.id}.md`;
    if (config.id.includes('-nih-')) {
        // The source API says CC-BY without specifying a version. Do not turn
        // that into an unsupported assertion of a particular license version.
        entry.license = 'CC-BY (version unspecified in NIH source metadata)';
        entry.license_url = entry.source;
        entry.license_files = [`sources/${config.id}.md`];
    }
    entry.note = notes[config.id];
    entry.representation = config.calibration === 'closed' ? 'scan' : 'illustration';
    entry.closed_volume_checked = config.calibration === 'closed';
    entry.volume_semantics = entry.closed_volume_checked
        ? 'closed_mesh_volume_scaled_to_representative_quantity'
        : 'cubic_linear_equivalent_approximation';
    const scene = await readScene(file);
    const extent = new THREE.Box3().setFromObject(scene, true).getSize(new THREE.Vector3()).toArray();
    const stats = entry.closed_volume_checked ? measureVolume(scene)
        : { extent, referenceSize: Math.max(...extent), closedVolumeMeasured: false };
    entry.presentation = { reference_size: stats.referenceSize,
        layout_width_factor: entry.closed_volume_checked ? 1.3 : 1.1,
        display_extent_factor: entry.closed_volume_checked ? 1.3 : 1.1,
        focus_scale_factor: entry.closed_volume_checked ? 1.3 : 1.1 };
    // Show the open tub basin at rest without changing its source proportions.
    if (config.calibration === 'capacity') Object.assign(entry.presentation, { yaw: -18, pitch: 22 });
    entry.processing ||= {};
    entry.processing.script = source ? 'scripts/register_volume3d.mjs' : 'scripts/prepare_volume3d_imports.mjs';
    entry.processing.operations = source ? [...(source.processing?.operations || [])] :
        config.calibration === 'closed'
            ? ['Retain the scanned exterior shell (107320 triangles); exclude four internal reverse-wound pore shells (122, 52, 52, 8 triangles)',
                'Deduplicate, weld, simplify to 53660 triangles with relative error 0.001, prune; retain source color and proportions']
            : config.calibration === 'capacity'
                ? ['Embed source buffers/textures, resize source textures to at most 1024 px', 'Deduplicate, weld and prune; preserve source geometry and materials']
                : ['Make implicit default material explicit; retain original vertex colors',
                    'Deduplicate, weld, simplify with target ratio 0.24 and relative error 0.01, prune'];
    entry.processing.volume_calibration = {
        script: 'scripts/register_volume3d.mjs', source_glb_sha256: hash,
        ...(source ? { source_model_id: source.id } : {}), ...stats,
        method: entry.closed_volume_checked
            ? 'Enclosed exterior bulk-envelope volume by signed tetrahedral sum; one consistently oriented closed shell. Self-intersection is not certified.'
            : 'Longest native source span normalized to 1, so displayed span is V^(1/3). Equivalent-span illustration only; no enclosed, material or capacity volume measured.',
    };
    const index = registry.models.findIndex(m => m.id === entry.id);
    if (process.argv.includes('--check')) {
        if (index < 0 || JSON.stringify(registry.models[index]) !== JSON.stringify(entry))
            throw new Error(`Stale registration: ${entry.id}`);
        const handoff = JSON.parse(fs.readFileSync(new URL(`handoff/volume3d/${entry.id}.entry.json`, root)));
        if (JSON.stringify(handoff) !== JSON.stringify(entry)) throw new Error(`Stale handoff: ${entry.id}`);
    } else {
        if (index < 0) registry.models.push(entry); else registry.models[index] = entry;
        fs.writeFileSync(new URL(`handoff/volume3d/${entry.id}.entry.json`, root), JSON.stringify(entry, null, 2) + '\n');
    }
    measurements.push({ id: entry.id, ...stats });
}
const matches = new Set();
for (const entry of registry.models) for (const name of entry.matches?.volume || []) {
    if (matches.has(name)) throw new Error(`Duplicate Volume mapping: ${name}`);
    matches.add(name);
}
if (!process.argv.includes('--check')) {
    // Preserve unrelated entries byte for byte, including source prose escapes.
    const updates = new Map(registry.models.filter(m => configs.some(c => c.id === m.id)).map(m => [m.id, m]));
    const serialize = entry => JSON.stringify(entry, null, 2).split('\n').map(line => '    ' + line).join('\n');
    let text = originalText.replace(/^    \{\n[\s\S]*?^    \}(,?)/gm, (block, comma) => {
        let entry;
        try { entry = JSON.parse(comma ? block.slice(0, -1) : block); } catch { return block; }
        const next = updates.get(entry.id);
        if (!next) return block;
        updates.delete(entry.id);
        return JSON.stringify(entry) === JSON.stringify(next) ? block : serialize(next) + comma;
    });
    if (updates.size) text = text.replace(/\n  \],\n  "coverage_gaps"/,
        ',\n' + [...updates.values()].map(serialize).join(',\n') + '\n  ],\n  "coverage_gaps"');
    if (JSON.stringify(JSON.parse(text)) !== JSON.stringify(registry)) throw new Error('Registry merge failed');
    fs.writeFileSync(registryPath, text);
}
console.log(JSON.stringify(measurements, null, 2));
