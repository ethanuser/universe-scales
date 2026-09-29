import * as THREE from '../vendor/three/three.module.min.js';

export const FOOTBALL_FIELD = Object.freeze({
    playingLength: 100,
    endZoneLength: 10,
    fullLength: 120,
    width: 160 / 3,
    hashFromSideline: (70 * 12 + 9) / 36,
    hashGap: 18.5 / 3,
    hashLength: 2 / 3,
    hashWidth: 4 / 36,
    goalpostGap: 18.5 / 3,
    crossbarHeight: 10 / 3,
    uprightAboveCrossbar: 35 / 3,
    uprightHeight: 45 / 3
});

const white = 0xf5f3df;
const fieldWidth = FOOTBALL_FIELD.width;
const halfWidth = fieldWidth / 2;

function addBox(scene, name, size, position, material) {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material);
    mesh.name = name;
    mesh.position.set(...position);
    scene.add(mesh);
    return mesh;
}

function addLine(scene, name, x, z, length, width, material, y = 0.035) {
    return addBox(scene, name, [length, 0.006, width], [x, y, z], material);
}

function addNumber(scene, label, x, side, material) {
    const canvasAvailable = typeof document !== 'undefined' && typeof document.createElement === 'function';
    if (canvasAvailable) {
        const canvas = document.createElement('canvas');
        canvas.width = 256;
        canvas.height = 192;
        const context = canvas.getContext('2d');
        if (context) {
            context.clearRect(0, 0, canvas.width, canvas.height);
            context.fillStyle = '#f5f3df';
            context.font = '900 150px Arial, sans-serif';
            context.textAlign = 'center';
            context.textBaseline = 'middle';
            context.fillText(label, 128, 96);
            const texture = new THREE.CanvasTexture(canvas);
            texture.colorSpace = THREE.SRGBColorSpace;
            const numberMaterial = new THREE.MeshBasicMaterial({ map: texture, transparent: true,
                side: THREE.DoubleSide, depthWrite: false, polygonOffset: true,
                polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
            const plane = new THREE.Mesh(new THREE.PlaneGeometry(2.7, 2), numberMaterial);
            plane.name = `yard-number-${label}-${side < 0 ? 'near' : 'far'}`;
            plane.rotation.x = -Math.PI / 2;
            if (side > 0) plane.rotation.y = Math.PI;
            plane.position.set(x, 0.043, side * (halfWidth - 13));
            plane.userData.yard = x;
            plane.userData.side = side;
            plane.userData.number = label;
            scene.add(plane);
            return;
        }
    }

    // A compact seven-segment fallback keeps the scene visible in Node and
    // canvas-less renderers while preserving the same yard-number placement.
    const segments = {
        0: ['a', 'b', 'c', 'd', 'e', 'f'], 1: ['b', 'c'], 2: ['a', 'b', 'g', 'e', 'd'],
        3: ['a', 'b', 'g', 'c', 'd'], 4: ['f', 'g', 'b', 'c'],
        5: ['a', 'f', 'g', 'c', 'd'], 6: ['a', 'f', 'g', 'e', 'c', 'd'],
        7: ['a', 'b', 'c'], 8: ['a', 'b', 'c', 'd', 'e', 'f', 'g'],
        9: ['a', 'b', 'c', 'd', 'f', 'g']
    };
    const dimensions = { a: [0.38, 0.08, 0], b: [0.08, 0.34, -0.17],
        c: [0.08, 0.34, 0.17], d: [0.38, 0.08, 0.34],
        e: [0.08, 0.34, 0.17], f: [0.08, 0.34, -0.17], g: [0.38, 0.08, 0.17] };
    const group = new THREE.Group();
    group.name = `yard-number-${label}-${side < 0 ? 'near' : 'far'}`;
    group.userData.yard = x;
    group.userData.side = side;
    group.userData.number = label;
    const chars = [...label];
    chars.forEach((character, index) => {
        const offset = (index - (chars.length - 1) / 2) * 0.52;
        for (const segment of segments[character]) {
            const [length, breadth, vertical] = dimensions[segment];
            const box = new THREE.Mesh(new THREE.BoxGeometry(length, 0.006, breadth), material);
            box.position.set(offset + vertical, 0, side < 0 ? breadth * 0.5 : -breadth * 0.5);
            group.add(box);
        }
    });
    group.rotation.x = -Math.PI / 2;
    if (side > 0) group.rotation.y = Math.PI;
    group.position.set(x, 0.043, side * (halfWidth - 13));
    scene.add(group);
}

function addGoalpost(scene, end, materials) {
    const x = end * 60;
    const gap = FOOTBALL_FIELD.goalpostGap;
    const postRadius = 1.5 / 36;
    const vertical = (name, z, from, to) => {
        const length = to - from;
        const mesh = new THREE.Mesh(new THREE.CylinderGeometry(postRadius, postRadius, length, 10), materials.goalpost);
        mesh.name = name;
        mesh.position.set(x, from + length / 2, z);
        scene.add(mesh);
        return mesh;
    };
    const stem = new THREE.Mesh(new THREE.CylinderGeometry(postRadius, postRadius, FOOTBALL_FIELD.crossbarHeight, 10), materials.goalpost);
    stem.name = `goalpost-stem-${end < 0 ? 'west' : 'east'}`;
    stem.position.set(x + end, FOOTBALL_FIELD.crossbarHeight / 2, 0);
    scene.add(stem);
    const crossbar = new THREE.Mesh(new THREE.CylinderGeometry(postRadius, postRadius, gap, 10), materials.goalpost);
    crossbar.name = `goalpost-crossbar-${end < 0 ? 'west' : 'east'}`;
    crossbar.rotation.x = Math.PI / 2;
    crossbar.position.set(x, FOOTBALL_FIELD.crossbarHeight, 0);
    scene.add(crossbar);
    vertical(`goalpost-upright-${end < 0 ? 'west' : 'east'}-near`, -gap / 2,
        FOOTBALL_FIELD.crossbarHeight, FOOTBALL_FIELD.uprightHeight);
    vertical(`goalpost-upright-${end < 0 ? 'west' : 'east'}-far`, gap / 2,
        FOOTBALL_FIELD.crossbarHeight, FOOTBALL_FIELD.uprightHeight);
    const foot = new THREE.Mesh(new THREE.CylinderGeometry(postRadius * 1.5, postRadius * 1.5, 0.22, 10), materials.goalpost);
    foot.name = `goalpost-foot-${end < 0 ? 'west' : 'east'}`;
    foot.position.set(x + end, 0.11, 0);
    scene.add(foot);
}

export function footballFieldScene() {
    const scene = new THREE.Group();
    scene.name = 'nfl-football-field';
    scene.userData.dimensions = { ...FOOTBALL_FIELD };
    const materials = {
        turf: [0x28643d, 0x2d6d41].map(color => new THREE.MeshStandardMaterial({ color, roughness: 0.94 })),
        endZone: new THREE.MeshStandardMaterial({ color: 0x194d48, roughness: 0.95 }),
        paint: new THREE.MeshBasicMaterial({ color: white, side: THREE.DoubleSide,
            polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }),
        goalpost: new THREE.MeshStandardMaterial({ color: 0xe0a52b, roughness: 0.6, metalness: 0.05 })
    };

    // The slab is deliberately only a few inches thick at this yard scale.
    addBox(scene, 'turf-substrate', [120, 0.035, fieldWidth], [0, -0.018, 0],
        new THREE.MeshStandardMaterial({ color: 0x1b3025, roughness: 1 }));
    for (let band = 0; band < 24; band++) {
        const start = -60 + band * 5;
        const x = start + 2.5;
        const material = x < -50 || x > 50 ? materials.endZone : materials.turf[Math.floor((x + 50) / 5) % 2];
        addBox(scene, `turf-band-${band + 1}`, [5, 0.012, fieldWidth], [x, 0.005, 0], material);
    }

    for (let yard = -50; yard <= 50; yard += 5) {
        addLine(scene, `yard-line-${yard}`, yard, 0, yard === -50 || yard === 50 ? 2 / 9 : 1 / 9,
            fieldWidth, materials.paint);
    }
    for (const side of [-1, 1])
        addLine(scene, `sideline-${side < 0 ? 'near' : 'far'}`, 0, side * halfWidth, 120, 1 / 9, materials.paint, 0.04);
    for (let yard = -59; yard <= 59; yard++) {
        if (yard % 5 !== 0) for (const side of [-1, 1])
            for (let row = 0; row < 2; row++) {
                const z = side * (halfWidth - FOOTBALL_FIELD.hashFromSideline
                    + FOOTBALL_FIELD.hashWidth / 2 - row * FOOTBALL_FIELD.hashGap);
                addLine(scene, `hash-${yard}-${side < 0 ? 'near' : 'far'}-${row + 1}`,
                    yard, z, FOOTBALL_FIELD.hashLength, FOOTBALL_FIELD.hashWidth, materials.paint);
            }
        for (const side of [-1, 1])
            addLine(scene, `sideline-tick-${yard}-${side < 0 ? 'near' : 'far'}`, yard,
                side * (halfWidth - 0.75), 0.55, 1 / 9, materials.paint);
    }
    for (const end of [-1, 1]) {
        addLine(scene, `end-line-${end < 0 ? 'west' : 'east'}`, end * 60, 0, 1 / 9, fieldWidth, materials.paint);
        addGoalpost(scene, end, materials);
    }
    for (let yard = 10; yard <= 50; yard += 10) {
        const label = String(yard);
        for (const end of [-1, 1])
            for (const side of [-1, 1])
                addNumber(scene, label, end * (50 - yard), side, materials.paint);
    }
    return scene;
}
