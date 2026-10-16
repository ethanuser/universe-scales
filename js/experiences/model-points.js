import * as THREE from '../vendor/three/three.module.min.js';

let sprite;

export function softPointSprite() {
    if (sprite) return sprite;
    const size = 32, rgba = new Uint8Array(size * size * 4);
    for (let y = 0; y < size; y++) {
        for (let x = 0; x < size; x++) {
            const radius = Math.hypot((x + 0.5) / size * 2 - 1, (y + 0.5) / size * 2 - 1);
            const edge = 1 - THREE.MathUtils.smoothstep(radius, 0.55, 1);
            const offset = 4 * (y * size + x);
            rgba.set([255, 255, 255, Math.round(255 * Math.exp(-3 * radius * radius) * edge)], offset);
        }
    }
    sprite = new THREE.DataTexture(rgba, size, size, THREE.RGBAFormat);
    sprite.magFilter = THREE.LinearFilter;
    sprite.minFilter = THREE.LinearFilter;
    sprite.needsUpdate = true;
    return sprite;
}

// Material.clone() does not copy shader hooks, so every clone of a glowing
// material must call this again.
function brightnessAlpha(material) {
    material.onBeforeCompile = shader => {
        shader.fragmentShader = shader.fragmentShader.replace('#include <premultiplied_alpha_fragment>',
            '#include <premultiplied_alpha_fragment>\n\tgl_FragColor.a = max(gl_FragColor.r, max(gl_FragColor.g, gl_FragColor.b));');
    };
    material.customProgramCacheKey = () => 'additive-brightness-alpha';
    return material;
}

// glTF extras `additive: true` (copied to userData) make a mesh or cloud glow:
// overlapping parts add up and black is transparent, as for gas and starlight.
function makeAdditive(node) {
    const apply = material => {
        const glowing = material.clone();
        // The canvas is transparent over the CSS sky. Adding color while leaving alpha
        // at zero relies on how a browser composites "invalid" premultiplied pixels:
        // Chrome shows them, Safari and Firefox drop them (the glow then appeared only
        // under the hover outline). So output premultiplied color with alpha equal to
        // its brightness and add both: rgb never exceeds alpha, black stays clear.
        glowing.premultipliedAlpha = true;
        glowing.blending = THREE.CustomBlending;
        glowing.blendEquation = THREE.AddEquation;
        glowing.blendSrc = THREE.OneFactor;
        glowing.blendDst = THREE.OneFactor;
        glowing.blendSrcAlpha = THREE.OneFactor;
        glowing.blendDstAlpha = THREE.OneFactor;
        glowing.transparent = true;
        glowing.depthWrite = false;
        return brightnessAlpha(glowing);
    };
    node.material = Array.isArray(node.material) ? node.material.map(apply) : apply(node.material);
}

export function prepareModelPoints(scene) {
    scene.traverse(node => {
        if ((node.isMesh || node.isPoints) && node.userData.additive) makeAdditive(node);
    });
    scene.traverse(node => {
        if (!node.isPoints || !node.userData.softPoints) return;
        node.material = node.material.clone();
        if (node.userData.additive) brightnessAlpha(node.material);
        node.material.map = softPointSprite();
        node.material.transparent = true;
        node.material.depthWrite = false;
        node.material.alphaTest = 0.005;
        // Points have no front/back faces. GLTF's double-sided transparent
        // material otherwise sends the entire cloud through the GPU twice.
        node.material.forceSinglePass = true;
        const count = node.geometry.getAttribute('position')?.count || 0;
        if (!node.userData.pointSize || count < 1000 || node.userData.pointLOD) return;
        node.geometry = node.geometry.clone();
        const indices = node.geometry.index ? Array.from(node.geometry.index.array)
            : Array.from({ length: count }, (_, index) => index);
        // Image-derived clouds arrive in scanline order. A deterministic
        // permutation keeps every reduced prefix spread across the whole cloud.
        let seed = 0x5ca1e;
        for (let i = indices.length - 1; i > 0; i--) {
            seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
            const j = Math.floor(seed / 4294967296 * (i + 1));
            [indices[i], indices[j]] = [indices[j], indices[i]];
        }
        node.geometry.setIndex(indices);
        node.userData.pointLOD = { fullPixels: 240, minimum: 128, mobileMaximum: 10000 };
    });
}
