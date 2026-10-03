import * as THREE from '../vendor/three/three.module.min.js';
import { buildAngularMachine } from './angular-machine-models.js?v=1d34c7795e';

const metal = (color, roughness = 0.3) => {
    const material = new THREE.MeshStandardMaterial({ color, metalness: 0.7, roughness });
    material.userData.environment = 0.65;
    return material;
};
const enamel = color => new THREE.MeshStandardMaterial({ color, roughness: 0.35 });
function mesh(parent, geometry, material, position = [0, 0, 0]) {
    const part = new THREE.Mesh(geometry, material);
    part.position.set(...position); parent.add(part); return part;
}
function cylinder(parent, radius, depth, material, position, axis = 'y') {
    const part = mesh(parent, new THREE.CylinderGeometry(radius, radius, depth, 64), material, position);
    if (axis === 'z') part.rotation.x = Math.PI / 2;
    return part;
}
function group(parent, name) {
    const part = new THREE.Group(); part.name = name; parent.add(part); return part;
}
function ring(parent, radius, tube, material, position, axis = 'z') {
    const part = mesh(parent, new THREE.TorusGeometry(radius, tube, 8, 80), material, position);
    if (axis === 'y') part.rotation.x = Math.PI / 2;
    return part;
}

function clock(selected) {
    const root = new THREE.Group(), housing = group(root, 'Housing');
    const steel = metal(0x7b858a), ink = enamel(0x182a35), paper = enamel(0xf3efe3);
    cylinder(housing, 1, 0.12, steel, [0, 0, -0.06], 'z');
    cylinder(housing, 0.94, 0.02, paper, [0, 0, 0.01], 'z');
    ring(housing, 0.965, 0.025, steel, [0, 0, 0.04]);
    for (let index = 0; index < 60; index++) {
        const angle = index * Math.PI / 30, major = index % 5 === 0;
        const mark = mesh(housing, new THREE.BoxGeometry(major ? 0.025 : 0.012, major ? 0.13 : 0.055, 0.008),
            ink, [0.83 * Math.sin(angle), 0.83 * Math.cos(angle), 0.03]);
        mark.rotation.z = -angle;
    }
    for (const [name, length, width, depth, color] of [
        ['HourHand', 0.51, 0.07, 0.052, 0x182a35],
        ['MinuteHand', 0.74, 0.047, 0.075, 0x182a35],
        ['SecondHand', 0.79, 0.018, 0.098, 0xc84c38]
    ]) {
        if (name !== selected) continue;
        const hand = group(root, name); hand.position.z = depth;
        mesh(hand, new THREE.BoxGeometry(width, length, 0.016), enamel(color), [0, length / 2 - 0.06, 0]);
        cylinder(hand, 0.05, 0.025, metal(color), [0, 0, 0], 'z');
    }
    return root;
}

function microwave() {
    const root = new THREE.Group(), housing = group(root, 'Housing');
    const steel = metal(0x828f96, 0.45), white = enamel(0xe4e6e4), dark = enamel(0x16232b);
    // Door opened and roof cut away, so the turntable is visible inside the fixed cavity.
    for (const [size, position] of [
        [[2.5, 0.09, 1.7], [0, -0.62, 0]], [[2.5, 1.4, 0.06], [0, 0.03, -0.82]],
        [[0.08, 1.4, 1.7], [-1.21, 0.03, 0]], [[0.38, 1.4, 1.7], [1.08, 0.03, 0]]
    ]) mesh(housing, new THREE.BoxGeometry(...size), steel, position);
    mesh(housing, new THREE.BoxGeometry(0.27, 0.2, 0.015), dark, [1.08, 0.46, 0.86]);
    for (let index = 0; index < 6; index++)
        mesh(housing, new THREE.BoxGeometry(0.07, 0.04, 0.02), white,
            [1.02 + (index % 2) * 0.12, 0.18 - Math.floor(index / 2) * 0.14, 0.86]);
    cylinder(housing, 0.065, 0.04, dark, [1.08, -0.33, 0.87], 'z');
    const rotor = group(root, 'Rotor'); rotor.position.set(-0.16, -0.5, 0);
    cylinder(rotor, 0.68, 0.035, enamel(0xaebfc0), [0, 0, 0]);
    ring(rotor, 0.65, 0.018, white, [0, 0.02, 0], 'y');
    cylinder(rotor, 0.43, 0.04, white, [0.03, 0.04, 0]);
    ring(rotor, 0.4, 0.018, white, [0.03, 0.065, 0], 'y');
    const food = mesh(rotor, new THREE.SphereGeometry(0.15, 20, 14), enamel(0xd0a05f), [0.18, 0.14, 0.06]);
    food.scale.set(1.1, 0.6, 0.8);
    return root;
}

function centrifuge() {
    const root = new THREE.Group(), housing = group(root, 'Housing');
    const white = enamel(0xdfe7e9), dark = metal(0x31414d, 0.38), steel = metal(0x9da9b5);
    cylinder(housing, 1, 0.22, white, [0, -0.27, 0]);
    ring(housing, 0.92, 0.075, white, [0, -0.08, 0], 'y');
    cylinder(housing, 0.1, 0.22, steel, [0, -0.07, 0]);
    const rotor = group(root, 'Rotor');
    cylinder(rotor, 0.75, 0.19, dark, [0, 0, 0]);
    cylinder(rotor, 0.16, 0.17, steel, [0, 0.15, 0]);
    for (let index = 0; index < 8; index++) {
        const angle = index * Math.PI / 4;
        const tube = group(rotor, `Tube${index}`);
        tube.position.set(0.55 * Math.sin(angle), 0.12, 0.55 * Math.cos(angle));
        tube.rotation.set(0, angle, 0); tube.rotateX(-Math.PI / 6);
        cylinder(tube, 0.09, 0.19, enamel(0xc4ddda), [0, 0, 0]);
        cylinder(tube, 0.1, 0.045, enamel(index === 0 ? 0xe4a04c : 0x568890), [0, 0.105, 0]);
    }
    return root;
}

function carWheel() {
    const root = new THREE.Group(), housing = group(root, 'Housing'), rotor = group(root, 'Rotor');
    const rubber = new THREE.MeshStandardMaterial({ color: 0x202528, roughness: 0.87 });
    const alloy = metal(0xaebbc1, 0.25), brake = metal(0x758087, 0.5);
    const profile = [[0.69, -0.22], [0.77, -0.25], [0.9, -0.245], [0.97, -0.21],
        [1, -0.15], [1, 0.15], [0.97, 0.21], [0.9, 0.245], [0.77, 0.25], [0.69, 0.22]];
    const tire = new THREE.LatheGeometry(profile.map(([r, z]) => new THREE.Vector2(r, z)), 96);
    tire.rotateX(Math.PI / 2);
    mesh(rotor, tire, rubber).name = 'Tire';
    for (const z of [-0.2, 0.2]) ring(rotor, 0.725, 0.035, alloy, [0, 0, z]);
    const barrel = new THREE.CylinderGeometry(0.725, 0.725, 0.4, 64, 1, true);
    barrel.rotateX(Math.PI / 2); mesh(rotor, barrel, alloy);
    cylinder(rotor, 0.6, 0.045, brake, [0, 0, -0.12], 'z').name = 'Brake disc';
    ring(rotor, 0.57, 0.012, brake, [0, 0, -0.09]);
    cylinder(rotor, 0.17, 0.19, alloy, [0, 0, 0.15], 'z');
    const shape = new THREE.Shape();
    shape.moveTo(-0.045, 0.11); shape.bezierCurveTo(-0.045, 0.3, -0.15, 0.53, -0.12, 0.73);
    shape.lineTo(0.035, 0.73); shape.bezierCurveTo(0.015, 0.5, 0.1, 0.3, 0.075, 0.11); shape.closePath();
    const spoke = new THREE.ExtrudeGeometry(shape, { depth: 0.035, bevelEnabled: true,
        bevelSegments: 2, steps: 1, bevelSize: 0.012, bevelThickness: 0.012, curveSegments: 10 });
    for (let index = 0; index < 5; index++) {
        const angle = index * 2 * Math.PI / 5;
        mesh(rotor, spoke, alloy, [0, 0, 0.18]).rotation.z = angle;
        cylinder(rotor, 0.03, 0.024, brake, [0.115 * Math.sin(angle), 0.115 * Math.cos(angle), 0.25], 'z');
    }
    const caliper = group(housing, 'Fixed brake caliper'); caliper.position.set(0.5, 0.18, -0.105);
    const red = enamel(0xa5372d);
    mesh(caliper, new THREE.BoxGeometry(0.16, 0.38, 0.15), red);
    for (const y of [-0.18, 0.18]) {
        const end = mesh(caliper, new THREE.SphereGeometry(0.085, 16, 12), red, [0, y, 0]);
        end.scale.set(1, 1, 0.85);
    }
    cylinder(housing, 0.09, 0.45, brake, [0, 0, -0.36], 'z').name = 'Fixed axle';
    const mount = mesh(housing, new THREE.BoxGeometry(0.46, 0.075, 0.06), brake, [0.25, 0.13, -0.24]);
    mount.rotation.z = 0.35;
    cylinder(rotor, 0.015, 0.06, rubber, [0, 0.66, 0.24], 'z').name = 'Valve stem';
    return root;
}

const specifications = [
    ['car-wheel', ['Car wheel at 60 mph'], [0, 0, 1],
        'The tire, wheel and brake disc turn together around the hub. The axle carrier and red brake caliper stay fixed. This exposed wheel assembly demonstrates rotation without road translation or braking; the wheel style is illustrative.', 8, -28,
        'https://www.brembo.com/en/solutions/for-your-car/sport-disc'],
    ['record-player', ['33 1/3 rpm record', '45 rpm vinyl record', '78 rpm record'], [0, 1, 0],
        'The record and platter turn together. The plinth, spindle axis and tonearm stay fixed; the three records use their own listed rpm. The grooves and surface markings are illustrative.', 28, -15,
        'https://docs.audio-technica.com/eu/AT-LPA2-UM-EN.pdf'],
    ['bicycle-wheel', ['Bicycle wheel', 'Bicycle wheel at 20 km/h', 'Bicycle wheel at city speed'], [0, 0, 1],
        'The tire, rim, spokes and hub rotate about the stationary axle. The fork remains still. This is a wheel on a stand; road translation is omitted.', 7, -25,
        'https://www.parktool.com/en-us/blog/repair-help/wheel-and-rim-truing'],
    ['washing-machine', ['Washing machine spin', 'Washing machine spin cycle'], [0, 0, 1],
        'The perforated inner drum and its lifters rotate about the horizontal shaft. The cabinet, outer tub and door surround stay fixed. The front is opened to expose the drum; water and laundry are omitted.', 12, -18,
        'https://www.bosch-home.com/us/owner-support/washers/troubleshooting/not-spinning'],
    ['hard-drive', ['Hard drive platter at 5400 rpm', 'Hard drive platter at 7200 rpm', 'Hard drive spindle'], [0, 1, 0],
        'The disk platters and spindle rotate together. The exposed housing and read/write actuator stay fixed. The cover is removed for visibility; the diagram does not simulate seeking or magnetic bits.', 38, -15,
        'https://www.seagate.com/support/disc/manuals/ata/1621pma.pdf'],
    ['blender', ['Blender blade'], [0, 1, 0],
        'Only the blade assembly and central shaft rotate. The base and jar remain fixed. The jar is an illustrative cutaway to reveal the blade, with no fluid simulation.', 25, -25,
        'https://www.vitamix.com/media/catalog/product/file/Container-Use-and-Care-Owners-Manual.pdf'],
    ['microwave', ['Microwave turntable'], [0, 1, 0],
        'The turntable, plate and food rotate together inside a stationary cavity. The roof and door are omitted to show the mechanism; this does not simulate the microwave field.', 28, -20,
        'https://www.fda.gov/radiation-emitting-products/resources-you-radiation-emitting-products/microwave-ovens'],
    ['centrifuge', ['Ultracentrifuge rotor'], [0, 1, 0],
        'An exposed fixed-angle rotor: the rotor, tube holders and sealed tubes rotate together about the vertical spindle, inside a stationary base. Tube angles and apparatus proportions are illustrative; the protective cover is omitted.', 36, -15,
        'https://www.beckman.com/centrifuges/rotors']
];
export const angularModelEntries = Object.fromEntries(specifications.flatMap(([kind, names, axis, note, pitch, yaw, source]) => {
    const entry = { id: `angular-${kind}`, procedural: 'angular-machine', angular_kind: kind,
        geometry: 'mesh', representation: 'illustrative-mechanism', author: 'Universe Scales', license: 'MIT',
        matches: { 'angular-velocity': names }, source, note,
        presentation: { pitch, yaw }, angular_motion: { rotations: [{ node: 'Rotor', axis,
            ratio: kind === 'record-player' ? -1 : 1 }] } };
    return names.map(name => [name, entry]);
}));
for (const [name, hand] of [['Hour hand', 'HourHand'], ['Minute hand', 'MinuteHand'], ['Second hand', 'SecondHand']]) {
    angularModelEntries[name] = { id: `angular-clock-${hand}`, procedural: 'angular-machine', angular_kind: `clock-${hand}`,
        geometry: 'mesh', representation: 'illustrative-mechanism', author: 'Universe Scales', license: 'MIT',
        matches: { 'angular-velocity': [name] }, presentation: { yaw: -8 },
        source: 'https://www.nist.gov/pml/time-and-frequency-division/popular-links/walk-through-time',
        note: `A continuous-sweep analog clock with only its ${name.toLowerCase()} shown. The hand follows the listed rate clockwise around the central spindle while the case and dial stay fixed. The other hands are omitted so they do not become unresolvable at time scales chosen for this hand.`,
        angular_motion: { rotations: [{ node: hand, axis: [0, 0, 1], ratio: -1 }] } };
}

export function angularEntry(item, entries) {
    if (angularModelEntries[item.name]) return angularModelEntries[item.name];
    const entry = entries.find(model => model.matches?.['angular-velocity']?.includes(item.name));
    if (!entry) return null;
    if (entry.id === 'ceiling-fan') return { ...entry, presentation: { ...entry.presentation, pitch: -26 },
        angular_motion: { rotations: [{ node: 'ceiling_fan_blades', axis: [0, 1, 0] }] } };
    if (['nasa-earth', 'nasa-jupiter'].includes(entry.id)) return { ...entry,
        presentation: { ...entry.presentation, roll: -12 },
        note: `${entry.note} The globe rotates around its polar axis at the listed angular speed. The camera tilt is for visibility; atmospheric differential rotation is not simulated.`,
        angular_motion: { rotations: [{ node: '$model', axis: [0, 1, 0] }] } };
    return entry.angular_motion ? entry : null;
}

export function angularScene(kind) {
    return kind.startsWith('clock-') ? clock(kind.slice(6)) : kind === 'microwave' ? microwave()
        : kind === 'centrifuge' ? centrifuge() : kind === 'car-wheel' ? carWheel() : buildAngularMachine(kind);
}
