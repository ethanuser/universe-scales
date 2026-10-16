import * as THREE from '../vendor/three/three.module.min.js';

const material = (color, roughness = 0.6, metalness = 0) => new THREE.MeshStandardMaterial({
    color, roughness, metalness
});

const MAT = {
    enamel: material(0xd9dedc, 0.3, 0.12),
    darkEnamel: material(0x343b3d, 0.38, 0.28),
    rubber: material(0x171b1d, 0.9),
    steel: material(0xc4cecc, 0.2, 0.56),
    brightSteel: material(0xf0f3ed, 0.14, 0.48),
    shadowSteel: material(0x465154, 0.38, 0.68),
    black: material(0x111619, 0.33, 0.35),
    brass: material(0xb88743, 0.32, 0.72),
    red: material(0x9e3026, 0.42, 0.2),
    wood: material(0x634934, 0.52, 0.08),
    glass: new THREE.MeshPhysicalMaterial({ color: 0xc4e0df, roughness: 0.12, metalness: 0,
        transmission: 0.72, transparent: true, opacity: 0.25, thickness: 0.008, side: THREE.DoubleSide }),
    glassDark: new THREE.MeshPhysicalMaterial({ color: 0x283839, roughness: 0.2, transparent: true,
        opacity: 0.35, side: THREE.DoubleSide }),
    blue: material(0x26383b, 0.35, 0.48),
    label: new THREE.MeshStandardMaterial({ color: 0xe7dcc1, roughness: 0.8 })
};

// ModelStage supplies this room-map reflection when it sees the material hint.
for (const mat of Object.values(MAT)) {
    if (mat.metalness > 0.2) mat.userData.environment = 0.6;
}

function group(parent, name, position) {
    const node = new THREE.Group();
    node.name = name;
    if (position) node.position.set(...position);
    parent.add(node);
    return node;
}

function mesh(parent, name, geometry, mat, position, rotation) {
    const node = new THREE.Mesh(geometry, mat);
    node.name = name;
    if (position) node.position.set(...position);
    if (rotation) node.rotation.set(...rotation);
    parent.add(node);
    return node;
}

function box(parent, name, size, position, mat, bevel = 0) {
    // Rounded boxes keep sheet-metal edges from reading as unrefined blocks.
    const geo = bevel > 0 ? roundedBoxGeometry(size, bevel) : new THREE.BoxGeometry(...size);
    return mesh(parent, name, geo, mat, position);
}

function roundedBoxGeometry(size, radius) {
    const [x, y, z] = size;
    const geometry = new THREE.BoxGeometry(x, y, z, 3, 3, 3);
    const p = geometry.getAttribute('position');
    const half = new THREE.Vector3(x / 2 - radius, y / 2 - radius, z / 2 - radius);
    for (let i = 0; i < p.count; i++) {
        const v = new THREE.Vector3(p.getX(i), p.getY(i), p.getZ(i));
        const core = new THREE.Vector3(
            THREE.MathUtils.clamp(v.x, -half.x, half.x),
            THREE.MathUtils.clamp(v.y, -half.y, half.y),
            THREE.MathUtils.clamp(v.z, -half.z, half.z));
        const delta = v.sub(core).normalize().multiplyScalar(radius);
        p.setXYZ(i, core.x + delta.x, core.y + delta.y, core.z + delta.z);
    }
    geometry.computeVertexNormals();
    return geometry;
}

function cylinder(parent, name, radiusTop, radiusBottom, height, position, mat, radial = 48, axis = 'y') {
    const rotation = axis === 'z' ? [Math.PI / 2, 0, 0] : axis === 'x' ? [0, 0, -Math.PI / 2] : undefined;
    return mesh(parent, name, new THREE.CylinderGeometry(radiusTop, radiusBottom, height, radial), mat, position, rotation);
}

function torus(parent, name, radius, tube, position, mat, rotation = [0, 0, 0], segments = 96, tubeSegments = 8) {
    return mesh(parent, name, new THREE.TorusGeometry(radius, tube, tubeSegments, segments), mat, position, rotation);
}

function addRotorRoot(kind, dimensions, axis, pivot) {
    const root = new THREE.Group();
    root.name = `${kind}-procedural`;
    root.userData.dimensionsMeters = dimensions;
    root.userData.illustrative = true;
    const housing = group(root, 'Housing');
    housing.userData.stationary = true;
    const rotor = group(root, 'Rotor', pivot);
    rotor.userData.stationary = false;
    rotor.userData.axis = axis;
    rotor.userData.pivot = [0, 0, 0];
    return { root, housing, rotor };
}

function washer() {
    const d = { width: 0.68, height: 0.84, depth: 0.59, drumDiameter: 0.49, drumLength: 0.34 };
    const { root, housing, rotor } = addRotorRoot('washing-machine', d, 'Z', [0, 0.015, 0]);
    // Open-front cabinet cutaway: side shells, top, rear panel and lower plinth remain fixed.
    box(housing, 'left cabinet cheek', [0.055, 0.78, 0.56], [-0.312, 0.01, 0], MAT.enamel, 0.012);
    box(housing, 'right cabinet cheek', [0.055, 0.78, 0.56], [0.312, 0.01, 0], MAT.enamel, 0.012);
    box(housing, 'cabinet crown', [0.65, 0.055, 0.56], [0, 0.402, 0], MAT.enamel, 0.012);
    box(housing, 'rear cabinet skin', [0.60, 0.70, 0.025], [0, 0.015, -0.275], MAT.darkEnamel, 0.008);
    box(housing, 'lower plinth', [0.65, 0.07, 0.57], [0, -0.38, 0], MAT.darkEnamel, 0.012);
    for (const x of [-0.22, 0.22]) box(housing, `foot ${x}`, [0.09, 0.035, 0.09], [x, -0.432, -0.19], MAT.rubber, 0.008);

    // The stationary outer tub is open at the front and shown as a partial shell.
    const tub = group(housing, 'stationary outer tub', [0, 0.015, -0.02]);
    cylinder(tub, 'outer tub rear bulkhead', 0.258, 0.258, 0.025, [0, 0, -0.22], MAT.shadowSteel, 64, 'z');
    torus(tub, 'outer tub front lip', 0.259, 0.014, [0, 0, 0.145], MAT.shadowSteel, [0, 0, 0]);
    // Three broad arc panels leave a generous inspection window into the drum.
    for (let part = 0; part < 3; part++) {
        const start = -Math.PI * 0.78 + part * Math.PI * 0.55;
        const geo = new THREE.CylinderGeometry(0.258, 0.258, 0.25, 32, 1, true, start, Math.PI * 0.43);
        geo.rotateX(Math.PI / 2);
        mesh(tub, `outer tub cutaway panel ${part + 1}`, geo, MAT.shadowSteel, [0, 0, 0.015]);
    }
    for (const x of [-0.26, 0.26]) {
        cylinder(housing, `suspension damper ${x}`, 0.011, 0.014, 0.16, [x, -0.26, -0.12], MAT.steel, 12);
        cylinder(housing, `counterweight boss ${x}`, 0.032, 0.032, 0.025, [x * 0.8, 0.02, -0.24], MAT.darkEnamel, 24, 'z');
    }

    // The drum is built around the Rotor origin; its shaft runs exactly on local Z.
    const r = 0.242, half = d.drumLength / 2;
    const shell = mesh(rotor, 'perforated stainless drum shell',
        new THREE.CylinderGeometry(r, r, d.drumLength, 96, 1, true), MAT.steel.clone(),
        [0, 0, 0], [Math.PI / 2, 0, 0]);
    shell.material.side = THREE.DoubleSide;
    cylinder(rotor, 'perforated drum rear plate', r, r, 0.008, [0, 0, -half], MAT.steel, 64, 'z');
    cylinder(rotor, 'drum hub', 0.045, 0.052, 0.045, [0, 0, -half - 0.025], MAT.brightSteel, 32, 'z');
    torus(rotor, 'rolled stainless drum mouth', r - 0.002, 0.008, [0, 0, half], MAT.brightSteel);
    // Thin longitudinal ribs and staggered dark perforation wells give the shell depth.
    const holes = new THREE.InstancedMesh(new THREE.SphereGeometry(0.0035, 6, 4), MAT.black, 14 * 8 + 6 * 24);
    holes.name = 'drum perforation recesses';
    const dummy = new THREE.Object3D();
    let index = 0;
    for (let row = 0; row < 8; row++) for (let col = 0; col < 14; col++) {
        const a = col / 14 * Math.PI * 2 + (row % 2) * 0.12;
        const z = -half + 0.025 + row * (d.drumLength - 0.05) / 7;
        dummy.position.set(Math.cos(a) * (r - 0.001), Math.sin(a) * (r - 0.001), z);
        dummy.scale.set(1, 1, 0.42);
        dummy.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), new THREE.Vector3(Math.cos(a), Math.sin(a), 0));
        dummy.updateMatrix(); holes.setMatrixAt(index++, dummy.matrix);
    }
    // Rear-face recesses make the turning drum visible in the axial view.
    dummy.quaternion.identity();
    for (let row = 0; row < 6; row++) for (let col = 0; col < 24; col++) {
        const a = col * Math.PI / 12 + (row % 2) * Math.PI / 24, radius = 0.06 + row * 0.028;
        dummy.position.set(Math.cos(a) * radius, Math.sin(a) * radius, -half + 0.006);
        dummy.updateMatrix(); holes.setMatrixAt(index++, dummy.matrix);
    }
    rotor.add(holes);
    for (let i = 0; i < 3; i++) {
        const angle = i * Math.PI * 2 / 3;
        const lifter = box(rotor, `drum interior lifter ${i + 1}`, [0.024, 0.028, 0.29],
            [Math.cos(angle) * 0.222, Math.sin(angle) * 0.222, 0], MAT.darkEnamel, 0.008);
        lifter.rotation.z = angle;
        const edge = box(rotor, `lifter reflective edge ${i + 1}`, [0.004, 0.006, 0.27],
            [Math.cos(angle) * 0.234, Math.sin(angle) * 0.234, 0], MAT.steel, 0.002);
        edge.rotation.z = angle;
    }
    // The door is omitted in this teaching cutaway so the rotating drum remains unobstructed.
    torus(housing, 'stationary door bezel', 0.277, 0.025, [0, 0.015, 0.286], MAT.enamel);
    torus(housing, 'door inner rubber seal', 0.251, 0.012, [0, 0.015, 0.291], MAT.rubber);
    box(housing, 'control fascia', [0.60, 0.095, 0.045], [0, 0.31, 0.286], MAT.enamel, 0.012);
    cylinder(housing, 'program selector', 0.026, 0.026, 0.018, [-0.195, 0.31, 0.317], MAT.darkEnamel, 32, 'z');
    box(housing, 'display glass', [0.11, 0.035, 0.006], [0.075, 0.31, 0.311], MAT.blue, 0.004);
    return root;
}

function hardDrive() {
    const d = { width: 0.102, height: 0.026, depth: 0.147, platterDiameter: 0.096 };
    const { root, housing, rotor } = addRotorRoot('hard-drive', d, 'Y', [0, 0, 0]);
    box(housing, 'cast base pan', [0.102, 0.006, 0.147], [0, -0.012, 0], MAT.shadowSteel, 0.003);
    for (const x of [-0.048, 0.048]) box(housing, `side rail ${x}`, [0.006, 0.015, 0.139], [x, -0.003, 0], MAT.steel, 0.001);
    for (const z of [-0.069, 0.069]) box(housing, `end rail ${z}`, [0.096, 0.015, 0.006], [0, -0.003, z], MAT.steel, 0.001);
    // Narrow perimeter cover flanges make the open chassis read as a removed-lid drive.
    for (const x of [-0.047, 0.047]) box(housing, `lid flange ${x}`, [0.006, 0.002, 0.12], [x, 0.010, 0], MAT.brightSteel, 0.001);
    cylinder(housing, 'fixed spindle bearing', 0.012, 0.014, 0.019, [0, -0.001, 0], MAT.darkEnamel, 32);
    const diskYs = [-0.0062, 0, 0.0062];
    diskYs.forEach((y, i) => {
        cylinder(rotor, `aluminum platter ${i + 1}`, 0.047, 0.047, 0.0028, [0, y, 0], MAT.brightSteel, 96);
        cylinder(rotor, `magnetic recording surface ${i + 1}`, 0.045, 0.045, 0.00045,
            [0, y + 0.00165, 0], MAT.steel, 96);
        for (let track = 0; track < 7; track++) {
            const rr = 0.018 + track * 0.0038;
            torus(rotor, `etched data track ${i + 1}-${track + 1}`, rr, 0.00011,
                [0, y + 0.0019, 0], track % 2 ? MAT.brightSteel : MAT.shadowSteel, [-Math.PI / 2, 0, 0], 96, 4);
        }
    });
    cylinder(rotor, 'spindle hub', 0.010, 0.010, 0.018, [0, 0.001, 0], MAT.steel, 32);
    box(rotor, 'off-axis spindle witness tab', [0.009, 0.001, 0.002], [0.009, 0.0102, 0], MAT.brass, 0.0004);
    cylinder(housing, 'actuator bearing post', 0.005, 0.006, 0.027, [0.039, 0.001, -0.050], MAT.brightSteel, 24);
    // Connect the bearing, arm, suspension and slider. All clear the top
    // platter at y=0.0081; the old slider was buried inside that platter.
    const a = new THREE.Vector3(0.039, 0.014, -0.050), b = new THREE.Vector3(-0.009, 0.014, -0.006);
    const arm = box(housing, 'stationary actuator arm', [a.distanceTo(b), 0.0015, 0.005],
        a.clone().add(b).multiplyScalar(0.5).toArray(), MAT.brightSteel, 0.0005);
    arm.rotation.y = -Math.atan2(b.z - a.z, b.x - a.x);
    cylinder(housing, 'actuator pivot cap', 0.008, 0.008, 0.003, [0.039, 0.016, -0.050], MAT.steel, 32);
    const end = new THREE.Vector3(-0.019, 0.0105, 0.003), delta = end.clone().sub(b);
    const flexure = box(housing, 'head suspension flexure', [delta.length(), 0.0008, 0.0018],
        b.clone().add(end).multiplyScalar(0.5).toArray(), MAT.brass, 0.0002);
    flexure.quaternion.setFromUnitVectors(new THREE.Vector3(1, 0, 0), delta.normalize());
    box(housing, 'read write head slider', [0.0045, 0.0015, 0.0035], [-0.019, 0.0098, 0.003], MAT.darkEnamel, 0.0003);
    for (const [x, z] of [[-0.043, -0.062], [0.043, -0.062], [-0.043, 0.062], [0.043, 0.062]])
        cylinder(housing, `cover screw ${x}-${z}`, 0.0022, 0.0022, 0.0012, [x, 0.011, z], MAT.brass, 12);
    return root;
}

function recordPlayer() {
    const d = { width: 0.34, height: 0.085, depth: 0.30, recordDiameter: 0.300 };
    const axisY = 0.051;
    const { root, housing, rotor } = addRotorRoot('record-player', d, 'Y', [0, axisY, 0]);
    box(housing, 'damped plinth', [0.34, 0.062, 0.30], [0, 0.005, 0], MAT.wood, 0.016);
    box(housing, 'plinth underside', [0.31, 0.012, 0.27], [0, -0.033, 0], MAT.darkEnamel, 0.006);
    for (const x of [-0.13, 0.13]) for (const z of [-0.11, 0.11])
        cylinder(housing, `isolation foot ${x}-${z}`, 0.018, 0.021, 0.018, [x, -0.048, z], MAT.rubber, 24);
    cylinder(housing, 'fixed spindle bearing well', 0.013, 0.018, 0.008, [0, 0.039, 0], MAT.darkEnamel, 40);
    // The platter, felt mat, record, label and spindle cap are one coherent rotating group.
    cylinder(rotor, 'cast aluminum platter', 0.146, 0.146, 0.006, [0, -0.002, 0], MAT.steel, 96);
    torus(rotor, 'platter machined outer lip', 0.142, 0.002, [0, 0.001, 0], MAT.brightSteel, [-Math.PI / 2, 0, 0]);
    cylinder(rotor, 'charcoal platter mat', 0.139, 0.139, 0.0018, [0, 0.0025, 0], MAT.rubber, 96);
    cylinder(rotor, 'vinyl record', 0.15, 0.15, 0.0016, [0, 0.0042, 0], MAT.black, 128);
    // Sparse, low-poly groove cues stay legible without dense concentric moire.
    for (let i = 0; i < 14; i++) {
        const radius = 0.060 + i * 0.0061;
        torus(rotor, `vinyl groove ${i + 1}`, radius, 0.00022, [0, 0.00512, 0],
            i % 4 === 0 ? MAT.shadowSteel : MAT.black, [-Math.PI / 2, 0, 0], 48, 4);
    }
    cylinder(rotor, 'record center label', 0.047, 0.047, 0.0011, [0, 0.0056, 0], MAT.red, 64);
    cylinder(rotor, 'label center ring', 0.006, 0.006, 0.0015, [0, 0.0064, 0], MAT.label, 32);
    box(rotor, 'offset label rule', [0.021, 0.0007, 0.002], [0.018, 0.00655, 0.010], MAT.label, 0.0004);
    cylinder(rotor, 'offset label dot', 0.0021, 0.0021, 0.0008, [-0.018, 0.00655, -0.014], MAT.brass, 12);
    cylinder(rotor, 'spindle pin', 0.0023, 0.0023, 0.020, [0, 0.010, 0], MAT.brightSteel, 16);
    // Fixed radial tonearm, gimbal, counterweight and stylus remain attached to the plinth.
    cylinder(housing, 'tonearm gimbal', 0.015, 0.015, 0.022, [0.115, 0.055, -0.105], MAT.darkEnamel, 40);
    cylinder(housing, 'tonearm bearing cap', 0.009, 0.009, 0.005, [0.115, 0.069, -0.105], MAT.brightSteel, 32);
    cylinder(housing, 'tonearm counterweight', 0.012, 0.012, 0.026, [0.149, 0.064, -0.105], MAT.steel, 40, 'z');
    const armPath = new THREE.CatmullRomCurve3([
        new THREE.Vector3(0.115, 0.066, -0.105), new THREE.Vector3(0.080, 0.071, -0.075),
        new THREE.Vector3(0.055, 0.073, -0.025), new THREE.Vector3(0.020, 0.073, 0.025),
        new THREE.Vector3(-0.005, 0.071, 0.066)
    ]);
    mesh(housing, 'fixed tubular tonearm', new THREE.TubeGeometry(armPath, 32, 0.0027, 8, false), MAT.brightSteel);
    box(housing, 'headshell', [0.018, 0.004, 0.009], [-0.006, 0.068, 0.066], MAT.darkEnamel, 0.002);
    cylinder(housing, 'stylus', 0.0011, 0.0007, 0.014, [-0.006, 0.063, 0.067], MAT.brass, 12);
    return root;
}

function bicycleWheel() {
    const d = { diameter: 0.70, width: 0.032, hubWidth: 0.10 };
    const { root, housing, rotor } = addRotorRoot('bicycle-wheel', d, 'Z', [0, 0, 0]);
    // A fixed fork and axle straddle the wheel; the rotating assembly is a side-on XY wheel.
    box(housing, 'fork crown', [0.065, 0.045, 0.13], [0, 0.39, 0], MAT.blue, 0.012);
    for (const side of [-0.060, 0.060]) {
        const path = new THREE.CatmullRomCurve3([
            new THREE.Vector3(0, 0.39, side), new THREE.Vector3(0, 0.28, side),
            new THREE.Vector3(0, 0.19, side), new THREE.Vector3(0, 0.08, side),
            new THREE.Vector3(0, 0, side)
        ]);
        mesh(housing, `fixed fork blade ${side}`, new THREE.TubeGeometry(path, 32, 0.012, 12, false), MAT.blue);
        box(housing, `fork dropout ${side}`, [0.030, 0.045, 0.020], [0, 0, side], MAT.steel, 0.007);
    }
    cylinder(housing, 'fixed through axle', 0.007, 0.007, 0.17, [0, 0, 0], MAT.brightSteel, 32, 'z');
    const R = 0.333;
    torus(rotor, 'black pneumatic tire', R, 0.019, [0, 0, 0], MAT.rubber, [0, 0, 0], 128, 16);
    torus(rotor, 'tire sidewall bead', R - 0.008, 0.002, [0, 0, 0.014], MAT.shadowSteel);
    torus(rotor, 'machined alloy rim', R - 0.024, 0.005, [0, 0, 0], MAT.brightSteel, [0, 0, 0], 128, 12);
    torus(rotor, 'rim inner well', R - 0.029, 0.0017, [0, 0, 0], MAT.steel);
    for (const side of [-1, 1]) {
        cylinder(rotor, `hub flange ${side}`, 0.034, 0.034, 0.004, [0, 0, side * 0.026], MAT.steel, 48, 'z');
        cylinder(rotor, `hub end cap ${side}`, 0.014, 0.014, 0.012, [0, 0, side * 0.044], MAT.darkEnamel, 32, 'z');
    }
    cylinder(rotor, 'rotating hub shell', 0.021, 0.021, 0.070, [0, 0, 0], MAT.brightSteel, 48, 'z');
    // Thirty-two crossed stainless spokes connect alternating hub flanges to rim eyelets.
    const spokeGeo = new THREE.CylinderGeometry(0.00065, 0.00065, 1, 6, 1);
    const spokes = new THREE.InstancedMesh(spokeGeo, MAT.steel, 32);
    spokes.name = 'cross-laced stainless spokes';
    const tmp = new THREE.Object3D();
    for (let i = 0; i < 32; i++) {
        const a = i / 32 * Math.PI * 2;
        const cross = i % 2 ? 1 : -1;
        const hubAngle = a + cross * 0.40;
        const start = new THREE.Vector3(Math.cos(hubAngle) * 0.033, Math.sin(hubAngle) * 0.033, cross * 0.028);
        const end = new THREE.Vector3(Math.cos(a) * (R - 0.027), Math.sin(a) * (R - 0.027), 0);
        const delta = end.clone().sub(start);
        tmp.position.copy(start).add(end).multiplyScalar(0.5);
        tmp.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), delta.clone().normalize());
        tmp.scale.set(1, delta.length(), 1); tmp.updateMatrix(); spokes.setMatrixAt(i, tmp.matrix);
    }
    rotor.add(spokes);
    for (let i = 0; i < 32; i++) {
        const a = i / 32 * Math.PI * 2;
        cylinder(rotor, `spoke nipple ${i + 1}`, 0.0015, 0.0015, 0.006,
            [Math.cos(a) * (R - 0.027), Math.sin(a) * (R - 0.027), 0], MAT.brass, 8, 'z');
    }
    return root;
}

function blender() {
    const d = { width: 0.19, height: 0.40, depth: 0.19, jarHeight: 0.255, jarDiameter: 0.145 };
    const pivotY = 0.13;
    const { root, housing, rotor } = addRotorRoot('blender', d, 'Y', [0, pivotY, 0]);
    box(housing, 'weighted motor base', [0.18, 0.105, 0.18], [0, 0.052, 0], MAT.darkEnamel, 0.025);
    box(housing, 'base lower trim', [0.175, 0.018, 0.175], [0, 0.012, 0], MAT.steel, 0.008);
    box(housing, 'front control panel', [0.105, 0.036, 0.008], [0, 0.068, 0.092], MAT.black, 0.006);
    cylinder(housing, 'speed dial', 0.017, 0.017, 0.012, [-0.034, 0.068, 0.099], MAT.brightSteel, 32, 'z');
    for (let i = 0; i < 3; i++) box(housing, `status light ${i + 1}`, [0.008, 0.006, 0.003], [0.012 + i * 0.016, 0.068, 0.098], MAT.red, 0.002);
    // The jar is stationary, slightly open at the top and optically clear for blade visibility.
    const jarR = 0.072;
    // Missing front arc makes a clear inspection cutaway instead of relying on refraction alone.
    const wall = new THREE.CylinderGeometry(jarR * 0.91, jarR, d.jarHeight, 64, 1, true,
        Math.PI * 0.36, Math.PI * 1.28);
    const jarWall = mesh(housing, 'transparent tapered pitcher cutaway wall', wall, MAT.glass, [0, 0.238, 0]);
    jarWall.userData.openFrontCutaway = true;
    torus(housing, 'pitcher glass foot ring', 0.064, 0.008, [0, 0.132, 0], MAT.glassDark, [Math.PI / 2, 0, 0]);
    torus(housing, 'pitcher mouth rolled rim', jarR * 0.91, 0.003, [0, 0.366, 0], MAT.glass, [Math.PI / 2, 0, 0]);
    torus(housing, 'pitcher lower reinforcing bead', 0.071, 0.0025, [0, 0.128, 0], MAT.glass, [Math.PI / 2, 0, 0]);
    // A removable-looking lid rests above the jar; its center plug has no raised carrying loop.
    cylinder(housing, 'pitcher lid', 0.074, 0.074, 0.012, [0, 0.372, 0], MAT.black, 64);
    torus(housing, 'lid perimeter seal', 0.070, 0.0025, [0, 0.366, 0], MAT.rubber, [Math.PI / 2, 0, 0]);
    cylinder(housing, 'lid center plug', 0.021, 0.021, 0.009, [0, 0.383, 0], MAT.darkEnamel, 40);
    // A narrow stationary bearing ring holds the Y-axis rotor without burying the blades.
    torus(housing, 'blade bearing collar', 0.021, 0.004, [0, pivotY - 0.009, 0], MAT.steel, [Math.PI / 2, 0, 0]);
    cylinder(rotor, 'vertical drive shaft', 0.004, 0.004, 0.035, [0, -0.012, 0], MAT.brightSteel, 20);
    cylinder(rotor, 'four-blade hub', 0.014, 0.015, 0.010, [0, 0, 0], MAT.steel, 32);
    for (let i = 0; i < 4; i++) {
        const angle = i * Math.PI / 2 + Math.PI / 4;
        const blade = box(rotor, `pitched stainless blade ${i + 1}`, [0.058, 0.0035, 0.014],
            [Math.cos(angle) * 0.028, 0.002, Math.sin(angle) * 0.028], MAT.brightSteel, 0.003);
        blade.rotation.y = -angle;
        blade.rotation.z = i % 2 ? -0.22 : 0.22;
    }
    const handlePath = new THREE.CatmullRomCurve3([
        new THREE.Vector3(0.066, 0.300, 0), new THREE.Vector3(0.098, 0.295, 0),
        new THREE.Vector3(0.116, 0.273, 0), new THREE.Vector3(0.116, 0.205, 0),
        new THREE.Vector3(0.098, 0.184, 0), new THREE.Vector3(0.066, 0.180, 0)
    ]);
    mesh(housing, 'side pitcher handle', new THREE.TubeGeometry(handlePath, 36, 0.007, 12, false), MAT.darkEnamel);
    return root;
}

const builders = Object.freeze({ 'washing-machine': washer, 'hard-drive': hardDrive, 'record-player': recordPlayer,
    'bicycle-wheel': bicycleWheel, blender });

export function buildAngularMachine(kind) {
    const build = builders[kind];
    if (!build) throw new RangeError(`Unknown angular machine kind: ${kind}`);
    return build();
}
