import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { readScene, measureVolume } from '../scripts/mesh_volume.mjs';

const root = new URL('../', import.meta.url);
const read = name => JSON.parse(fs.readFileSync(new URL(name, root)));
const registry = read('content/visualizations/models.json').models;
const planets = ['Mercury', 'Venus', 'Mars', 'Saturn', 'Uranus', 'Neptune', 'Pluto'];

test('Planet Volume entries reuse source assets but have independent enclosed-volume calibration', async () => {
    for (const planet of planets) {
        const matches = registry.filter(entry => entry.matches?.volume?.includes(`${planet} volume`));
        assert.equal(matches.length, 1, planet);
        const entry = matches[0], calibration = entry.processing.volume_calibration;
        const source = registry.find(item => item.id === calibration.source_model_id);
        assert.notEqual(entry.id, source.id);
        assert.equal(entry.src, source.src);
        assert.equal(entry.sha256, source.sha256);
        assert.equal(entry.geometry, 'mesh');
        assert.equal(entry.closed_volume_checked, true);
        assert.equal(entry.volume_semantics, 'closed_mesh_volume_scaled_to_representative_quantity');
        const measured = measureVolume(await readScene(new URL(entry.src, root)));
        assert.ok(Math.abs(measured.volume / entry.presentation.reference_size ** 3 - 1) < 1e-10);
        assert.equal(calibration.source_glb_sha256, source.sha256);
    }
});

test('New planet examples remain displayed without displacing Earth or Jupiter', () => {
    const area = read('exports/json/dimensions/area.json').items;
    const volume = read('exports/json/dimensions/volume.json').items;
    for (const planet of [...planets, 'Earth', 'Jupiter']) {
        assert.equal(area.filter(item => item.name === `${planet} surface area`).length, 1);
        assert.equal(volume.filter(item => item.name === `${planet} volume`).length, 1);
    }
    for (const dimension of ['area', 'volume']) for (const planet of planets) {
        const image = `${dimension}_${planet.toLowerCase()}_${dimension === 'area' ? 'surface_area' : 'volume'}.jpg`;
        for (const prefix of ['images/', 'images/thumbs/']) assert.ok(fs.existsSync(new URL(prefix + image, root)));
    }
});
