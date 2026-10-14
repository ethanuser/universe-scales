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
        faceCamera(side) {
            root.updateMatrixWorld(true);
            const axis = rotations[0].axis.clone().transformDirection(rotations[0].node.matrixWorld);
            // Keep the visible end of the spindle, then look straight along it.
            const sign = side === 'negative' ? -1 : side === 'positive' ? 1 : axis.z < -1e-6 ? -1 : 1;
            const target = new THREE.Vector3(0, 0, sign);
            root.quaternion.premultiply(new THREE.Quaternion().setFromUnitVectors(axis, target));
            root.updateMatrixWorld(true);
            // Reverse the whole mechanism together, retaining gearing and any
            // counter-rotation (e.g. level gondolas on a Ferris wheel).
            const direction = rotations[0].axis.clone().transformDirection(rotations[0].node.matrixWorld);
            const flip = -Math.sign(direction.z * rotations[0].ratio);
            for (const rotation of rotations) rotation.ratio *= flip;
            return root.quaternion.clone();
        },
        setPhase(phase) {
            if (!Number.isFinite(phase)) throw new Error('Angular phase must be finite');
            for (const { node, axis, ratio, rest } of rotations) {
                delta.setFromAxisAngle(axis, phase * ratio);
                node.quaternion.copy(rest).multiply(delta);
            }
        }
    };
}
