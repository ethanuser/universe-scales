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

export function prepareModelPoints(scene) {
    scene.traverse(node => {
        if (!node.isPoints || !node.userData.softPoints) return;
        node.material = node.material.clone();
        node.material.map = softPointSprite();
        node.material.transparent = true;
        node.material.depthWrite = false;
        node.material.alphaTest = 0.005;
    });
}
