import test from 'node:test';
import assert from 'node:assert/strict';
import { modelBytes, retainModelResources, releaseModelResources } from '../js/experiences/model-resources.js';

const scene = (...nodes) => ({ traverse(callback) { nodes.forEach(callback); } });
const resource = extra => ({ disposals: 0, dispose() { this.disposals++; }, ...extra });

test('shared geometry/material/bitmap survives until its final source owner is evicted', () => {
    const image = { width: 64, height: 64, closed: 0, close() { this.closed++; } };
    const geometry = resource({ isBufferGeometry: true, attributes: {} });
    const texture = resource({ isTexture: true, source: { data: image } });
    const material = resource({ map: texture });
    const a = retainModelResources(scene({ geometry, material }));
    const b = retainModelResources(scene({ geometry, material }));
    releaseModelResources(a);
    releaseModelResources(a);
    assert.equal(geometry.disposals + texture.disposals + material.disposals + image.closed, 0);
    releaseModelResources(b);
    assert.equal(geometry.disposals, 1);
    assert.equal(texture.disposals, 1);
    assert.equal(material.disposals, 1);
    assert.equal(image.closed, 1);
});

test('distinct textures sharing one bitmap do not close it while the other is retained', () => {
    const image = { closed: 0, close() { this.closed++; } };
    const a = retainModelResources(scene({ material: resource({ map: resource({ isTexture: true, image }) }) }));
    const b = retainModelResources(scene({ material: resource({ map: resource({ isTexture: true, image }) }) }));
    releaseModelResources(a);
    assert.equal(image.closed, 0);
    releaseModelResources(b);
    assert.equal(image.closed, 1);
});

test('decoded memory estimates count shared attribute buffers/textures once, including mipmaps', () => {
    const array = new Float32Array(12);
    const geometry = resource({ isBufferGeometry: true,
        attributes: { position: { array }, normal: { array } }, morphAttributes: {} });
    const texture = resource({ isTexture: true, image: { width: 32, height: 24 }, generateMipmaps: true });
    const material = resource({ map: texture });
    assert.equal(modelBytes(scene({ geometry, material }, { geometry, material })), 48 + 32 * 24 * 4 * 4 / 3);
});

test('small module-owned sprite/number textures stay reusable across model evictions', () => {
    const texture = resource({ isTexture: true, userData: { modelCachePersistent: true } });
    const model = retainModelResources(scene({ material: resource({ map: texture }) }));
    releaseModelResources(model);
    assert.equal(texture.disposals, 0);
});

test('source snapshots release removed/flattened geometry but retain shared output materials', () => {
    const oldGeometry = resource(), keptGeometry = resource(), newGeometry = resource();
    const material = resource();
    const nodes = [{ geometry: oldGeometry, material }, { geometry: keptGeometry, material }];
    const original = retainModelResources({ traverse(callback) { nodes.forEach(callback); } });
    nodes.shift();
    const normalized = retainModelResources(scene({ geometry: keptGeometry, material }, { geometry: newGeometry, material }));
    releaseModelResources(original);
    assert.equal(oldGeometry.disposals, 1);
    assert.equal(keptGeometry.disposals + newGeometry.disposals + material.disposals, 0);
    releaseModelResources(normalized);
    assert.equal(keptGeometry.disposals, 1);
    assert.equal(newGeometry.disposals, 1);
    assert.equal(material.disposals, 1);
});
