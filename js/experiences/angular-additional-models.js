import * as THREE from '../vendor/three/three.module.min.js';

// Original inspection diagrams. Proportions, blade counts and beam geometry are
// design choices, not dimensional measurements or manufacturer specifications.
const finish = (color, metalness = 0.65) => {
    const material = new THREE.MeshStandardMaterial({ color, metalness, roughness: 0.32 });
    if (metalness) material.userData.environment = 0.65;
    return material;
};
function group(parent, name, position = [0, 0, 0]) {
    const node = new THREE.Group(); node.name = name; node.position.set(...position); parent.add(node); return node;
}
function mesh(parent, name, geometry, material, position = [0, 0, 0]) {
    const node = new THREE.Mesh(geometry, material); node.name = name; node.position.set(...position); parent.add(node); return node;
}
function cylinder(parent, name, radius, depth, material, position = [0, 0, 0]) {
    const geometry = new THREE.CylinderGeometry(radius, radius, depth, 48); geometry.rotateX(Math.PI / 2);
    return mesh(parent, name, geometry, material, position);
}
function ring(parent, name, radius, tube, material, position = [0, 0, 0], segments = 96, tubeSegments = 8) {
    return mesh(parent, name, new THREE.TorusGeometry(radius, tube, tubeSegments, segments), material, position);
}
function strut(parent, name, a, b, radius, material) {
    const start = new THREE.Vector3(...a), end = new THREE.Vector3(...b), delta = end.clone().sub(start);
    const node = mesh(parent, name, new THREE.CylinderGeometry(radius, radius, delta.length(), 10), material);
    node.position.copy(start).add(end).multiplyScalar(0.5);
    node.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), delta.normalize());
    return node;
}
function assembly() {
    const root = new THREE.Group();
    return { root, housing: group(root, 'Housing'), rotor: group(root, 'Rotor') };
}

export function observationWheel() {
    const { root, housing, rotor } = assembly();
    const white = finish(0xe1e5e3, 0.35), steel = finish(0x7f969f), dark = finish(0x33424c);
    const glazing = new THREE.MeshStandardMaterial({ color: 0x96c8db, metalness: 0.18,
        roughness: 0.22, transparent: true, opacity: 0.48, depthWrite: false });
    // Cantilevered A-frame, behind the wheel; no support crosses its moving rim.
    for (const x of [-0.52, 0.52]) {
        strut(housing, 'fixed support leg', [x, -1.25, -0.30], [0, 0, -0.18], 0.052, white);
        mesh(housing, 'foundation', new THREE.BoxGeometry(0.30, 0.05, 0.35), dark, [x, -1.28, -0.30]);
    }
    cylinder(housing, 'stationary axle', 0.09, 0.48, steel, [0, 0, -0.22]);
    cylinder(rotor, 'rotating hub', 0.13, 0.16, white);
    for (const z of [-0.045, 0.045]) ring(rotor, 'wheel rim', 1, 0.017, white, [0, 0, z]);
    const cableGeometry = new THREE.CylinderGeometry(0.0022, 0.0022, 1, 5);
    for (let i = 0; i < 32; i++) {
        const angle = i * 2 * Math.PI / 32, x = Math.sin(angle), y = Math.cos(angle);
        for (const z of [-0.045, 0.045]) {
            const cable = mesh(rotor, 'tension spoke', cableGeometry, steel, [x / 2, y / 2, z]);
            cable.rotation.z = -angle;
        }
        strut(rotor, 'capsule bracket', [x, y, 0], [x * 1.065, y * 1.065, 0], 0.009, white);
        // Counter-rotation cancels the parent wheel's phase. The capsules travel
        // around the wheel, while their floors keep a constant world orientation.
        const pod = group(rotor, `Capsule${i}`, [x * 1.075, y * 1.075, 0]);
        const glass = mesh(pod, 'capsule glazing', new THREE.SphereGeometry(1, 16, 10), glazing);
        glass.scale.set(0.074, 0.047, 0.055);
        mesh(pod, 'level capsule floor', new THREE.BoxGeometry(0.115, 0.008, 0.074), white, [0, -0.025, 0]);
        const frame = ring(pod, 'capsule frame', 1, 0.035, white, undefined, 24, 4);
        frame.scale.set(0.074, 0.047, 0.055);
    }
    return root;
}

export function gasTurbine() {
    const { root, housing, rotor } = assembly();
    const titanium = finish(0xa9b3b5), warm = finish(0x9b8261), dark = finish(0x3d4d56);
    ring(housing, 'stationary outer casing', 1.09, 0.035, dark);
    ring(housing, 'stationary nozzle outer shroud', 1.01, 0.025, titanium, [0, 0, -0.25]);
    ring(housing, 'stationary nozzle inner shroud', 0.43, 0.027, warm, [0, 0, -0.25]);
    // Nozzle guide vanes stay fixed, behind the exposed rotating blade row.
    for (let i = 0; i < 20; i++) {
        const vane = mesh(housing, 'fixed nozzle guide vane', new THREE.BoxGeometry(0.52, 0.035, 0.11),
            warm, [0.72 * Math.cos(i * Math.PI / 10), 0.72 * Math.sin(i * Math.PI / 10), -0.25]);
        vane.rotation.z = i * Math.PI / 10 + 0.12;
    }
    cylinder(rotor, 'turbine disk', 0.46, 0.13, titanium);
    cylinder(rotor, 'central shaft', 0.13, 0.65, dark, [0, 0, -0.08]);
    cylinder(rotor, 'shaft end', 0.17, 0.07, titanium, [0, 0, 0.27]);
    const bladeShape = new THREE.Shape();
    bladeShape.moveTo(0.43, -0.045); bladeShape.bezierCurveTo(0.60, -0.03, 0.82, 0.10, 0.99, 0.16);
    bladeShape.lineTo(0.98, 0.24); bladeShape.bezierCurveTo(0.78, 0.20, 0.61, 0.045, 0.43, 0.045); bladeShape.closePath();
    const blade = new THREE.ExtrudeGeometry(bladeShape, { depth: 0.10, bevelEnabled: false, curveSegments: 8 });
    // A small twist through the axial chord gives a blade row, not a flat fan.
    const positions = blade.getAttribute('position');
    for (let i = 0; i < positions.count; i++) positions.setY(i, positions.getY(i) + positions.getZ(i) * (positions.getX(i) - 0.4) * 0.6);
    blade.computeVertexNormals();
    for (let i = 0; i < 24; i++) mesh(rotor, 'turbine rotor blade', blade, titanium).rotation.z = i * Math.PI / 12;
    for (let i = 0; i < 8; i++) cylinder(housing, 'casing flange bolt', 0.025, 0.035, titanium,
        [1.09 * Math.cos(i * Math.PI / 4), 1.09 * Math.sin(i * Math.PI / 4), 0.04]);
    return root;
}

export function dentalTurbine() {
    const { root, housing, rotor } = assembly();
    const steel = finish(0xc1cbcb), dark = finish(0x4e646d), brass = finish(0xae8551);
    ring(housing, 'opened handpiece head', 0.64, 0.065, steel, [0, 0, -0.035]);
    ring(housing, 'stationary rear bearing outer race', 0.20, 0.035, dark, [0, 0, -0.20]);
    ring(housing, 'stationary front bearing outer race', 0.20, 0.035, dark, [0, 0, 0.23]);
    strut(housing, 'fixed handpiece neck', [0.58, -0.18, -0.27], [1.35, -0.40, -0.27], 0.17, steel);
    strut(housing, 'fixed handpiece grip', [1.35, -0.40, -0.27], [2.3, -0.48, -0.27], 0.15, steel);
    strut(housing, 'air inlet nozzle', [0.69, 0.10, -0.04], [0.50, 0.22, -0.04], 0.055, brass);
    cylinder(rotor, 'air turbine hub', 0.25, 0.18, brass);
    cylinder(rotor, 'rotating chuck', 0.12, 0.55, steel);
    cylinder(rotor, 'bur shaft', 0.035, 0.60, steel, [0, 0, 0.51]);
    cylinder(rotor, 'bur cutting head', 0.06, 0.14, dark, [0, 0, 0.84]);
    const bucket = new THREE.Shape();
    bucket.moveTo(0.23, -0.08); bucket.quadraticCurveTo(0.42, -0.16, 0.56, -0.02);
    bucket.lineTo(0.54, 0.045); bucket.quadraticCurveTo(0.39, -0.055, 0.23, -0.005); bucket.closePath();
    const geometry = new THREE.ExtrudeGeometry(bucket, { depth: 0.15, bevelEnabled: false, curveSegments: 8 });
    geometry.translate(0, 0, -0.075);
    for (let i = 0; i < 8; i++) mesh(rotor, 'air turbine bucket', geometry, steel).rotation.z = i * Math.PI / 4;
    return root;
}

export function pulsar() {
    const { root, housing, rotor } = assembly();
    const star = new THREE.MeshStandardMaterial({ color: 0x9cd8ef, emissive: 0x236aa7, emissiveIntensity: 0.55, roughness: 0.7 });
    mesh(rotor, 'schematic neutron star', new THREE.SphereGeometry(0.40, 48, 32), star);
    // Magnetic and spin axes differ. No particular pulsar geometry is inferred.
    const magnetic = group(rotor, 'magnetic axis'); magnetic.rotation.x = 0.95;
    const fieldMaterial = new THREE.MeshBasicMaterial({ color: 0x44adcc, transparent: true, opacity: 0.32, depthWrite: false });
    const beamMaterial = new THREE.MeshBasicMaterial({ color: 0x79dfff, transparent: true,
        opacity: 0.22, side: THREE.DoubleSide, depthWrite: false });
    for (const sign of [-1, 1]) {
        const beam = mesh(magnetic, 'emission beam guide', new THREE.CylinderGeometry(0.27, 0.045, 0.88, 32, 1, true), beamMaterial,
            [0, sign * 0.83, 0]);
        if (sign < 0) beam.rotation.z = Math.PI;
        const pole = mesh(magnetic, 'magnetic polar cap', new THREE.SphereGeometry(0.075, 16, 12),
            new THREE.MeshBasicMaterial({ color: 0xe1fbff }), [0, sign * 0.39, 0]);
        pole.scale.y = 0.22;
    }
    for (let azimuth = 0; azimuth < 6; azimuth++) {
        const longitude = azimuth * Math.PI / 3;
        const points = [];
        const start = Math.asin(Math.sqrt(0.40 / 0.90));
        for (let i = 0; i <= 48; i++) {
            const theta = start + (Math.PI - 2 * start) * i / 48, r = 0.90 * Math.sin(theta) ** 2;
            points.push(new THREE.Vector3(r * Math.sin(theta) * Math.cos(longitude), r * Math.cos(theta),
                r * Math.sin(theta) * Math.sin(longitude)));
        }
        mesh(magnetic, 'schematic dipole field guide', new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points), 48, 0.004, 4, false), fieldMaterial);
    }
    // A neutral reference ring is stationary; it is a diagram guide, not matter.
    const guide = ring(housing, 'stationary rotation guide', 0.46, 0.0025,
        new THREE.MeshBasicMaterial({ color: 0x657f8c, transparent: true, opacity: 0.45 }), [0, 0, -0.43]);
    guide.userData.referenceOnly = true;
    return root;
}
