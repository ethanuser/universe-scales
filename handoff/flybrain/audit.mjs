// Decode the final asset with the vendored production GLTFLoader under Node.
// This tests loading, materials and calibration; it cannot test GPU rendering.
import { registerHooks } from 'node:module';
import { readFileSync } from 'node:fs';
const root = new URL('../../', import.meta.url);
registerHooks({ resolve(specifier, context, nextResolve) {
    if (specifier === 'three') return { url: new URL('js/vendor/three/three.module.min.js', root).href, shortCircuit: true };
    return nextResolve(specifier, context);
} });
const THREE = await import(new URL('js/vendor/three/three.module.min.js', root));
const { GLTFLoader } = await import(new URL('js/vendor/three/addons/loaders/GLTFLoader.js', root));
const registry = JSON.parse(readFileSync(new URL('content/visualizations/models.json', root)));
const entry = registry.models.find(entry => entry.id === 'fruit-fly-brain-flywire');
const bytes = readFileSync(new URL(entry.src, root));
const { scene } = await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
scene.updateMatrixWorld(true);
const native = new THREE.Box3().setFromObject(scene, true).getSize(new THREE.Vector3());
const group = new THREE.Group();
group.add(scene);
group.scale.setScalar(1 / entry.presentation.reference_size);
group.rotation.set(entry.presentation.pitch * Math.PI / 180, entry.presentation.yaw * Math.PI / 180, 0);
group.updateMatrixWorld(true);
const size = new THREE.Box3().setFromObject(group, true).getSize(new THREE.Vector3());
let lines = 0, triangles = 0;
scene.traverse(node => {
    if (node.isLine) lines += node.geometry.index.count / 2;
    if (node.isMesh) triangles += node.geometry.index.count / 3;
});
const extent = Math.max(size.x, size.y);
console.log(JSON.stringify({ units: 'micrometres', nativeExtent: native.toArray(),
    restExtentRelativeTo800um: size.toArray(), extent, lineSegmentsIncludingRuler: lines, triangles }, null, 2));
if (extent < .6 || extent > 1.3) throw new Error('Resting extent outside size rule');
