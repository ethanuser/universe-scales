import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { registerHooks } from 'node:module';
import * as THREE from '../js/vendor/three/three.module.min.js';
import { pulseState, updateReconstructedNeuron } from '../js/experiences/neuron-animation.js';
import { animationRoots, update } from '../js/experiences/wave-models.js';
import { organelleModelMetadata } from '../js/experiences/organelle-models.js';

const animation = { kind: 'reconstructed-neuron', period: 6.5, launch: .8,
    travelSeconds: 4.5, maxDistanceUm: 965, aisDistanceUm: 20, pulseWidthUm: 22 };

function fixture() {
    const root = new THREE.Group();
    root.userData.animation = { ...animation };
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('_path_distance', new THREE.Float32BufferAttribute([0, 20, 400], 1));
    const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial());
    mesh.userData.neurite = 'axon';
    const halo = new THREE.Points(geometry, new THREE.PointsMaterial({ transparent: true, opacity: 0 }));
    halo.userData.neurite = 'pulse-halo';
    root.add(mesh, halo);
    return root;
}

test('pulse starts in the proximal axon and reaches distal branches by tree distance', () => {
    assert.equal(pulseState(animation, .79).active, false);
    assert.equal(pulseState(animation, .8).head, 20);
    assert.equal(pulseState(animation, .8).active, true);
    assert.equal(pulseState(animation, 3.05).head, (965+20)/2);
    assert.ok(Math.abs(pulseState(animation, 5.3).head-965) < 1e-10);
    assert.equal(pulseState(animation, 6).active, false);
    assert.deepEqual(pulseState(animation, 8.5), pulseState(animation, 2));
});

test('GLTF-style clones and normalization wrappers dispatch their own shader uniforms', () => {
    const original = fixture(), clone = original.clone();
    const wrapper = new THREE.Group(); wrapper.add(clone);
    assert.deepEqual(animationRoots(wrapper), [clone]);
    update(clone, 2);
    assert.notEqual(clone.children[0].material, original.children[0].material);
    assert.equal(original.children[1].material.opacity, 0);
    const shader = { uniforms: {}, vertexShader: THREE.ShaderLib.standard.vertexShader,
        fragmentShader: THREE.ShaderLib.standard.fragmentShader };
    clone.children[0].material.onBeforeCompile(shader);
    assert.match(shader.vertexShader, /neuronDistance = _path_distance/);
    assert.match(shader.fragmentShader, /totalEmissiveRadiance \+=/);
    assert.equal(shader.uniforms.neuronActive.value, 1);
    const previous = shader.uniforms.neuronHead.value;
    updateReconstructedNeuron(clone, 3);
    assert.ok(shader.uniforms.neuronHead.value > previous);
    updateReconstructedNeuron(clone, NaN);
    assert.ok(Number.isFinite(shader.uniforms.neuronHead.value));
});

test('pulse halo shader uses the point sprite alpha and shared path-based wave', () => {
    const root = fixture(); updateReconstructedNeuron(root, 2);
    const shader = { uniforms: {}, vertexShader: THREE.ShaderLib.points.vertexShader,
        fragmentShader: THREE.ShaderLib.points.fragmentShader };
    root.children[1].material.onBeforeCompile(shader);
    assert.match(shader.fragmentShader, /diffuseColor.a \*= neuronPulse/);
    assert.ok(root.children[1].material.opacity > 0);
    assert.equal(root.children[1].material.depthWrite, false);
});

test('registry-backed reconstruction is no longer shadowed by the stylized procedural neuron', () => {
    assert.equal(organelleModelMetadata.Neuron, undefined);
});

test('production GLTFLoader preserves custom path attributes and dispatches the asset animation', async () => {
    const hooks = registerHooks({ resolve(specifier, context, nextResolve) {
        return nextResolve(specifier === 'three'
            ? new URL('../js/vendor/three/three.module.min.js', import.meta.url).href : specifier, context);
    } });
    try {
        const { GLTFLoader } = await import('../js/vendor/three/addons/loaders/GLTFLoader.js');
        const file = readFileSync(new URL('../content/visualizations/models/neuromorpho-feldmeyer-neuron-109111.glb', import.meta.url));
        const buffer = file.buffer.slice(file.byteOffset, file.byteOffset + file.byteLength);
        const gltf = await new GLTFLoader().parseAsync(buffer, '');
        const scene = gltf.scene.clone();
        const roots = animationRoots(scene);
        assert.equal(roots.length, 1);
        const root = roots[0];
        const axon = root.children.find(node => node.userData.neurite === 'axon');
        const halo = root.children.find(node => node.userData.neurite === 'pulse-halo');
        assert.ok(axon.geometry.getAttribute('_path_distance').count > 1000);
        assert.ok(halo.isPoints);
        assert.equal(halo.material.opacity, 0);
        update(root, 2.8);
        assert.ok(halo.material.opacity > 0);
        const shader = { uniforms: {}, vertexShader: THREE.ShaderLib.standard.vertexShader,
            fragmentShader: THREE.ShaderLib.standard.fragmentShader };
        axon.material.onBeforeCompile(shader);
        assert.equal(shader.uniforms.neuronActive.value, 1);
        assert.ok(shader.uniforms.neuronHead.value > 400);
        assert.ok(shader.uniforms.neuronHead.value < 500);
    } finally { hooks.deregister(); }
});
