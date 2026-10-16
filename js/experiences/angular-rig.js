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
        faceCamera(side, tilt = 0) {
            root.updateMatrixWorld(true);
            const axis = rotations[0].axis.clone().transformDirection(rotations[0].node.matrixWorld);
            // Keep the visible end of the spindle, then look straight along it.
            const sign = side === 'negative' ? -1 : side === 'positive' ? 1 : axis.z < -1e-6 ? -1 : 1;
            const target = new THREE.Vector3(0, 0, sign);
            root.quaternion.premultiply(new THREE.Quaternion().setFromUnitVectors(axis, target));
            // Long shafts disappear behind their end flange in an axial view.
            // An optional inspection tilt exposes the journals while preserving
            // the same near end and clockwise projected rotation.
            if (!Number.isFinite(tilt) || Math.abs(tilt) >= 90) throw new Error('Angular inspection tilt must be below 90 degrees');
            root.quaternion.premultiply(new THREE.Quaternion().setFromAxisAngle(
                new THREE.Vector3(0, 1, 0), THREE.MathUtils.degToRad(tilt)));
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

// Thin propellers can be almost horizontal at rest. Framing only that pose
// clips later phases and lets blades sweep through the item label. Measure a
// complete turn once, including stationary structure and geared descendants.
export function angularSweepBounds(root, rig) {
    const bounds = new THREE.Box3();
    for (let sample = 0; sample < 32; sample++) {
        rig.setPhase(sample * 2 * Math.PI / 32);
        root.updateMatrixWorld(true);
        bounds.union(new THREE.Box3().setFromObject(root, true));
    }
    rig.setPhase(0); root.updateMatrixWorld(true);
    // Margin covers the unsampled tips between phases for these rigid 1:1 rigs.
    const size = bounds.getSize(new THREE.Vector3());
    bounds.expandByVector(size.multiplyScalar(0.003));
    return bounds;
}
