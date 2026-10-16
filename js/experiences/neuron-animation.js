// Electrical annotations on the actual NeuroMorpho axon. Distances are original
// SWC tree-path distances in micrometers, so the wave follows every bifurcation.
import { registerAnimation } from './model-animation.js?v=540ebe0ea0';

const states = new WeakMap();

export function pulseState(animation, elapsed) {
    let phase = elapsed % animation.period;
    if (phase < 0) phase += animation.period;
    const speed = (animation.maxDistanceUm - animation.aisDistanceUm) / animation.travelSeconds;
    return { head: animation.aisDistanceUm + (phase - animation.launch) * speed,
        active: phase + 1e-9 >= animation.launch && phase <= animation.launch + animation.travelSeconds + .35 };
}

function prepare(root) {
    const uniforms = { neuronHead: { value: -1e6 }, neuronActive: { value: 0 },
        neuronWidth: { value: root.userData.animation.pulseWidthUm },
        neuronAIS: { value: root.userData.animation.aisDistanceUm } };
    root.traverse(node => {
        if (!node.geometry?.getAttribute('_path_distance') || !node.userData.neurite) return;
        const halo = node.userData.neurite === 'pulse-halo';
        // GLTF instances share materials; shader state belongs to this clone.
        const material = node.material = node.material.clone();
        if (halo) {
            material.opacity = .85;
            material.depthWrite = false;
            material.alphaTest = .005;
        }
        material.onBeforeCompile = shader => {
            Object.assign(shader.uniforms, uniforms);
            shader.vertexShader = 'attribute float _path_distance; varying float neuronDistance;\n' + shader.vertexShader;
            shader.vertexShader = shader.vertexShader.replace('#include <begin_vertex>',
                '#include <begin_vertex>\nneuronDistance = _path_distance;');
            shader.fragmentShader = `varying float neuronDistance;
                uniform float neuronHead, neuronActive, neuronWidth, neuronAIS;
                float neuronPulse() {
                    float gap = (neuronDistance - neuronHead) / neuronWidth;
                    return neuronActive * step(neuronAIS, neuronDistance) * exp(-gap * gap * 2.0);
                }\n` + shader.fragmentShader;
            if (halo) {
                shader.fragmentShader = shader.fragmentShader.replace('#include <color_fragment>',
                    '#include <color_fragment>\ndiffuseColor.a *= neuronPulse();');
            } else {
                shader.fragmentShader = shader.fragmentShader.replace('#include <emissivemap_fragment>',
                    '#include <emissivemap_fragment>\ntotalEmissiveRadiance += vec3(2.8, 1.5, 0.22) * neuronPulse();');
            }
        };
        material.customProgramCacheKey = () => `neuron-pulse-${halo ? 'halo' : 'membrane'}-v1`;
        material.needsUpdate = true;
    });
    states.set(root, uniforms);
    return uniforms;
}

export function updateReconstructedNeuron(root, elapsed) {
    if (!Number.isFinite(elapsed)) return;
    const uniforms = states.get(root) || prepare(root);
    const state = pulseState(root.userData.animation, elapsed);
    uniforms.neuronHead.value = state.head;
    uniforms.neuronActive.value = Number(state.active);
}

registerAnimation('reconstructed-neuron', updateReconstructedNeuron);
