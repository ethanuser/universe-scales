import * as THREE from '../vendor/three/three.module.min.js';

// Phase is supplied by the shared simulation clock, never by wall-clock time.
// Each rotation is absolute relative to the authored pose, so pause, seeking and
// full revolutions cannot accumulate drift or rotate a stationary parent.
export function createAngularRig(root, specification) {
    if (!specification?.rotations?.length) return null;
    const rotations = specification.rotations.map(({ node: name, axis, ratio = 1 }) => {
        const node = name === '$model' ? root.children[0] : root.getObjectByName(name);
        if (!node) throw new Error(`Missing angular rotor: ${name}`);
        const direction = new THREE.Vector3(...axis);
        if (!direction.lengthSq() || !Number.isFinite(ratio)) throw new Error(`Invalid angular axis: ${name}`);
        return { node, axis: direction.normalize(), ratio, rest: node.quaternion.clone() };
    });
    const delta = new THREE.Quaternion();
    return {
        rotations,
        setPhase(phase) {
            if (!Number.isFinite(phase)) throw new Error('Angular phase must be finite');
            for (const { node, axis, ratio, rest } of rotations) {
                delta.setFromAxisAngle(axis, phase * ratio);
                node.quaternion.copy(rest).multiply(delta);
            }
        }
    };
}
