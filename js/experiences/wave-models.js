// Animated schematic plane waves for representative electromagnetic wavelengths.
import * as THREE from '../vendor/three/three.module.min.js';
import { runAnimation } from './model-animation.js';

// One wavelength fills the model, so it renders at the listed size.
const presentation = Object.freeze({ reference_size: 1, layout_width_factor: 1.4,
    focus_scale_factor: 1.35, display_extent_factor: 1.15, pitch: 24, yaw: -24 });
const wave = (name, id, wavelength_m, band, source, sourceTitle, note, additionalSources = []) => Object.freeze({
    id, name, dimension: 'length', value: wavelength_m, unit: 'm', wavelength_m, band,
    procedural: 'traveling-em-wave', geometry: 'mesh', presentation,
    source, source_title: sourceTitle, sources: Object.freeze([source, ...additionalSources]),
    note: `${note} Exactly one wavelength is shown, so the model is the listed length. Red E and blue B are perpendicular, in-phase fields starting at a shared origin and traveling along +x, the direction of E × B. Their heights are field strengths in separate normalized units (E = cB in vacuum), not lengths, and this is not the path of a photon. The animation is slowed to 0.35 cycles per second.`, basis_url: source
});
const nasa = 'https://imagine.gsfc.nasa.gov/science/toolbox/spectrum_chart.html';
const nasaTitle = 'NASA Imagine: Wavelength, Frequency, and Energy';
const c0 = 'https://physics.nist.gov/cuu/Constants/Value/c.html';

// Representative values let the same one-wavelength schematic represent any band.
export const waveModelMetadata = Object.freeze({
    'Gamma Ray Wavelength': wave('Gamma Ray Wavelength', 'em-wave-gamma', 1.057e-12, 'gamma ray',
        'https://nvlpubs.nist.gov/nistpubs/jres/088/3/V88-3.pdf', 'NIST: Cobalt-60 decay gamma energies',
        'Co-60 1.17323 MeV gamma line; wavelength is derived from hc/E. This is an example gamma-ray wavelength, not a band boundary.'),
    'X-ray Wavelength': wave('X-ray Wavelength', 'em-wave-x-ray', 0.15405925e-9, 'X-ray',
        'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=920358', 'NIST: High-precision measurement of the X-ray Cu K-alpha spectrum',
        'Cu K-alpha1 emission line at 0.15405925 nm. This is an example X-ray wavelength, not a band boundary.'),
    'UV Wavelength': wave('UV Wavelength', 'em-wave-ultraviolet', 253.7e-9, 'ultraviolet',
        'https://www.cdc.gov/infection-control/hcp/environmental-control/air.html', 'CDC: Low-pressure mercury germicidal lamps',
        'Low-pressure mercury germicidal lamp resonance line at 253.7 nm. This is an example ultraviolet wavelength, not a band boundary.'),
    'Visible Light Wavelength': wave('Visible Light Wavelength', 'em-wave-visible', 500e-9, 'visible', nasa, nasaTitle,
        'Representative green visible light at 500 nm; visible wavelengths cover a range, not one value.'),
    'Infrared Wavelength': wave('Infrared Wavelength', 'em-wave-infrared', 9.35e-6, 'infrared',
        'https://lhea.gsfc.nasa.gov/archive/mwmw/mmw_bbody.html', 'NASA: Multiwavelength Milky Way - Radiation Laws',
        'Approximate Wien peak for a 310 K blackbody: 2.8978e-3 m K / 310 K = 9.35 micrometers. This is an example thermal infrared wavelength, not a band boundary.'),
    'Microwave Wavelength': wave('Microwave Wavelength', 'em-wave-microwave', 0.12236, 'microwave',
        'https://www.fda.gov/media/103619/download', 'FDA: Frequencies used for microwave food processing',
        'Household microwave-oven frequency 2.45 GHz; wavelength c/f = 12.236 cm. This is an example microwave wavelength, not a band boundary.', [c0]),
    'Radio Wavelength': wave('Radio Wavelength', 'em-wave-radio', 2.9979, 'radio',
        'https://www.ecfr.gov/current/title-47/chapter-I/subchapter-C/part-73/subpart-H/section-73.201', 'eCFR 47 CFR 73.201: FM broadcast band',
        '100 MHz FM broadcast example; wavelength c/f = 2.9979 m using exact c. The US FM broadcast band is 88-108 MHz, not a single wavelength.', [c0])
});

// The six entries other than Visible Light Wavelength are ready-to-ingest
// Length rows; values are representative within the cited broad spectrum bands.
export const additionalWavelengthRows = Object.freeze(Object.values(waveModelMetadata)
    .filter(entry => entry.name !== 'Visible Light Wavelength'));

// The origin is where both fields start and the propagation axis begins.
const CYCLES = 1;
const START = 0;
const AMPLITUDE = 0.26;
const SAMPLES = 120;
const RADIAL_SEGMENTS = 5;
const STEMS = 16;
const TWO_PI = 2 * Math.PI;

function arrow(from, to, radius, material) {
    const delta = to.clone().sub(from), length = delta.length();
    const group = new THREE.Group();
    const headLength = Math.min(radius * 7, length * 0.35);
    group.add(new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, length - headLength, 6), material));
    group.children[0].position.y = (length - headLength) / 2;
    const head = new THREE.Mesh(new THREE.ConeGeometry(radius * 2.6, headLength, 8), material);
    head.position.y = length - headLength / 2;
    group.add(head);
    group.position.copy(from);
    group.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), delta.normalize());
    return group;
}

const lineMaterials = new Map();
// Same convention as procedural-models.js: ModelStage redraws these boxes at a
// constant pixel width every frame.
function screenLine(axis, length, position, color) {
    if (!lineMaterials.has(color)) lineMaterials.set(color, new THREE.MeshBasicMaterial({ color }));
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), lineMaterials.get(color));
    mesh.position.copy(position);
    mesh.userData.screenLine = { axis, length };
    mesh.scale.set(axis === 'x' ? length : 1e-6, axis === 'y' ? length : 1e-6, axis === 'z' ? length : 1e-6);
    return mesh;
}

function addAnchor(scene, label, position, labelClass, vector = false) {
    const anchor = new THREE.Object3D();
    anchor.position.copy(position);
    anchor.userData.label = label;
    if (labelClass) anchor.userData.labelClass = labelClass;
    // Draws a small arrow over the letter, the usual vector notation.
    if (vector) anchor.userData.labelVector = true;
    scene.add(anchor);
}

function fieldTube(axis, color) {
    const geometry = new THREE.BufferGeometry();
    const verticesPerRing = RADIAL_SEGMENTS + 1;
    const positions = new Float32Array((SAMPLES + 1) * verticesPerRing * 3);
    const indices = [];
    for (let sample = 0; sample < SAMPLES; sample++) {
        for (let side = 0; side < RADIAL_SEGMENTS; side++) {
            const a = sample * verticesPerRing + side, b = a + verticesPerRing;
            if (axis === 'y') indices.push(a, a + 1, b, b, a + 1, b + 1);
            else indices.push(a, b, a + 1, b, b + 1, a + 1);
        }
    }
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setIndex(indices);
    const material = new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.12,
        roughness: 0.55, metalness: 0 });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = axis === 'y' ? 'electric-field-wave' : 'magnetic-field-wave';
    mesh.userData.waveAxis = axis;
    // Field vectors: stems from the propagation axis to the field value.
    const stems = new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position',
        new THREE.BufferAttribute(new Float32Array((STEMS + 1) * 6), 3)),
    new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.55 }));
    stems.name = `${mesh.name}-vectors`;
    mesh.add(stems);
    return mesh;
}

function writeFieldGeometry(mesh, phase) {
    const axis = mesh.userData.waveAxis;
    const attribute = mesh.geometry.getAttribute('position');
    const radius = 0.009;
    for (let sample = 0; sample <= SAMPLES; sample++) {
        const fraction = sample / SAMPLES;
        const x = START + CYCLES * fraction;
        const angle = TWO_PI * fraction * CYCLES - phase;
        const displacement = AMPLITUDE * Math.sin(angle);
        const slope = AMPLITUDE * TWO_PI * Math.cos(angle);
        for (let side = 0; side <= RADIAL_SEGMENTS; side++) {
            const around = TWO_PI * side / RADIAL_SEGMENTS;
            const inPlane = radius * Math.cos(around) / Math.hypot(1, slope);
            const outOfPlane = radius * Math.sin(around);
            const offset = (sample * (RADIAL_SEGMENTS + 1) + side) * 3;
            attribute.setXYZ(offset / 3,
                x - slope * inPlane,
                axis === 'y' ? displacement + inPlane : outOfPlane,
                axis === 'z' ? displacement + inPlane : outOfPlane);
        }
    }
    attribute.needsUpdate = true;
    const stems = mesh.children[0].geometry.getAttribute('position');
    for (let stem = 0; stem <= STEMS; stem++) {
        const fraction = stem / STEMS, x = START + CYCLES * fraction;
        const value = AMPLITUDE * Math.sin(TWO_PI * fraction * CYCLES - phase);
        stems.setXYZ(2 * stem, x, 0, 0);
        stems.setXYZ(2 * stem + 1, x, axis === 'y' ? value : 0, axis === 'z' ? value : 0);
    }
    stems.needsUpdate = true;
    mesh.children[0].geometry.computeBoundingSphere();
    mesh.geometry.computeVertexNormals();
    mesh.geometry.computeBoundingSphere();
}

const SI = [[1e3, 'km'], [1, 'm'], [1e-3, 'mm'], [1e-6, 'µm'], [1e-9, 'nm'], [1e-12, 'pm'], [1e-15, 'fm']];
export function formatLength(meters) {
    const [scale, unit] = SI.find(([factor]) => meters >= factor * 0.9999) || SI.at(-1);
    return `${Number((meters / scale).toPrecision(3))} ${unit}`;
}

export function waveScene(entry = {}) {
    const scene = new THREE.Group();
    const electric = new THREE.MeshStandardMaterial({ color: 0xd94f43, roughness: 0.55 });
    const magnetic = new THREE.MeshStandardMaterial({ color: 0x3978c5, roughness: 0.55 });
    const neutral = new THREE.MeshStandardMaterial({ color: 0x59636e, roughness: 0.7 });
    const eWave = fieldTube('y', 0xd94f43), bWave = fieldTube('z', 0x3978c5);
    scene.add(eWave, bWave);
    writeFieldGeometry(eWave, 0);
    writeFieldGeometry(bWave, 0);

    // Right-handed axes from the shared origin: E along +y, B along +z, and
    // propagation along +x (the direction of E x B), running through the waves.
    const origin = new THREE.Vector3(START, 0, 0);
    const propagationEnd = START + CYCLES + 0.14;
    scene.add(arrow(origin, new THREE.Vector3(propagationEnd, 0, 0), 0.006, neutral));
    scene.add(arrow(origin, new THREE.Vector3(START, AMPLITUDE + 0.1, 0), 0.008, electric));
    scene.add(arrow(origin, new THREE.Vector3(START, 0, AMPLITUDE + 0.1), 0.008, magnetic));
    addAnchor(scene, 'E', new THREE.Vector3(START, AMPLITUDE + 0.16, 0), 'is-electric', true);
    addAnchor(scene, 'B', new THREE.Vector3(START, 0, AMPLITUDE + 0.18), 'is-magnetic', true);
    addAnchor(scene, 'Propagation', new THREE.Vector3(propagationEnd + 0.02, 0.07, 0));

    // The model is exactly one wavelength long, so this bracket stays true while
    // the crests travel: any window this long holds exactly one full cycle.
    const bracketY = -AMPLITUDE - 0.12, ink = 0x2f3a45;
    scene.add(screenLine('x', CYCLES, new THREE.Vector3(START + CYCLES / 2, bracketY, 0), ink));
    for (const x of [START, START + CYCLES])
        scene.add(screenLine('y', 0.08, new THREE.Vector3(x, bracketY + 0.04, 0), ink));
    const wavelength = entry.wavelength_m ?? entry.value;
    addAnchor(scene, `λ = ${wavelength ? formatLength(wavelength) : 'one wavelength'}`,
        new THREE.Vector3(START + CYCLES / 2, bracketY - 0.09, 0));
    scene.userData.waveAnimation = { cyclesPerSecond: 0.35, phase: 0 };
    return scene;
}

// elapsed is seconds from the caller's animation clock; state is clone-safe data.
export function update(scene, elapsed) {
    if (scene.userData.animation) { runAnimation(scene, elapsed); return; }
    const animation = scene.userData.waveAnimation;
    if (!animation || !Number.isFinite(elapsed)) return;
    animation.phase = TWO_PI * animation.cyclesPerSecond * elapsed;
    scene.traverse(child => {
        if (child.isMesh && child.userData.waveAxis) writeFieldGeometry(child, animation.phase);
    });
}

export const waveScenes = Object.freeze({ 'traveling-em-wave': waveScene });
// Normalization and GLTF-style cloning wrap the procedural scene. Never assume
// its animation descriptor is on the outer instance itself.
export function animationRoots(instance) {
    const roots = [];
    instance.traverse(node => { if (node.userData.waveAnimation || node.userData.animation) roots.push(node); });
    return roots;
}
export const waveAnimation = Object.freeze({ update, animationRoots });
