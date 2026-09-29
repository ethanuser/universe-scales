// Animated schematic plane waves for representative electromagnetic wavelengths.
import * as THREE from '../vendor/three/three.module.min.js';

const presentation = Object.freeze({ reference_size: 1, layout_width_factor: 2.25,
    focus_scale_factor: 2.6, display_extent_factor: 2.6, pitch: 38, yaw: -8 });
const wave = (name, id, wavelength_m, band, source, sourceTitle, note, additionalSources = []) => Object.freeze({
    id, name, dimension: 'length', value: wavelength_m, unit: 'm', wavelength_m, band,
    procedural: 'traveling-em-wave', geometry: 'mesh', presentation,
    source, source_title: sourceTitle, sources: Object.freeze([source, ...additionalSources]),
    note: `${note} Red E and blue B are perpendicular, in-phase fields propagating along +x. Their amplitudes use separate normalized units (E = cB in vacuum); this is not the path of a photon. Animation is slowed to 0.35 cycles per second for visibility.`, basis_url: source
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

const CYCLES = 2;
const START = -CYCLES / 2;
const AMPLITUDE = 0.28;
const SAMPLES = 120;
const RADIAL_SEGMENTS = 5;
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

function addAnchor(scene, label, position, labelClass) {
    const anchor = new THREE.Object3D();
    anchor.position.copy(position);
    anchor.userData.label = label;
    if (labelClass) anchor.userData.labelClass = labelClass;
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
    mesh.geometry.computeVertexNormals();
    mesh.geometry.computeBoundingSphere();
}

export function waveScene() {
    const scene = new THREE.Group();
    const electric = new THREE.MeshStandardMaterial({ color: 0xd94f43, roughness: 0.55 });
    const magnetic = new THREE.MeshStandardMaterial({ color: 0x3978c5, roughness: 0.55 });
    const neutral = new THREE.MeshStandardMaterial({ color: 0x59636e, roughness: 0.7 });
    const eWave = fieldTube('y', 0xd94f43), bWave = fieldTube('z', 0x3978c5);
    scene.add(eWave, bWave);
    writeFieldGeometry(eWave, 0);
    writeFieldGeometry(bWave, 0);
    const axis = new THREE.Line(new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(START, 0, 0), new THREE.Vector3(START + CYCLES, 0, 0)
    ]), new THREE.LineBasicMaterial({ color: 0x88939e, transparent: true, opacity: 0.65 }));
    axis.name = 'shared-zero-field-axis';
    scene.add(axis);

    // Compact orthogonal field-direction glyphs, with no redundant text labels.
    const origin = new THREE.Vector3(START - 0.12, 0, 0);
    scene.add(arrow(origin, origin.clone().add(new THREE.Vector3(0, AMPLITUDE + 0.1, 0)), 0.009, electric));
    scene.add(arrow(origin, origin.clone().add(new THREE.Vector3(0, 0, AMPLITUDE + 0.1)), 0.009, magnetic));
    addAnchor(scene, 'E\u0302', origin.clone().add(new THREE.Vector3(0, AMPLITUDE + 0.17, 0)), 'is-electric');
    addAnchor(scene, 'B\u0302', origin.clone().add(new THREE.Vector3(0, 0, AMPLITUDE + 0.17)), 'is-magnetic');
    const propagationEnd = START + CYCLES + 0.2;
    scene.add(arrow(new THREE.Vector3(START - 0.08, -0.43, 0),
        new THREE.Vector3(propagationEnd, -0.43, 0), 0.007, neutral));
    addAnchor(scene, 'Direction of propagation', new THREE.Vector3(propagationEnd - 0.08, -0.53, 0));

    const wavelengthStart = START + 0.25, wavelengthEnd = wavelengthStart + 1;
    const bracketY = AMPLITUDE + 0.31;
    scene.add(new THREE.Mesh(new THREE.BoxGeometry(1, 0.008, 0.008), neutral));
    const bracket = scene.children.at(-1);
    bracket.position.set((wavelengthStart + wavelengthEnd) / 2, bracketY, 0);
    for (const x of [wavelengthStart, wavelengthEnd]) {
        const tick = new THREE.Mesh(new THREE.BoxGeometry(0.008, 0.1, 0.008), neutral);
        tick.position.set(x, bracketY - 0.045, 0);
        scene.add(tick);
    }
    addAnchor(scene, 'Wavelength \u03bb', new THREE.Vector3((wavelengthStart + wavelengthEnd) / 2,
        bracketY + 0.12, 0));
    scene.userData.waveAnimation = { cyclesPerSecond: 0.35, phase: 0 };
    return scene;
}

// elapsed is seconds from the caller's animation clock; state is clone-safe data.
export function update(scene, elapsed) {
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
    instance.traverse(node => { if (node.userData.waveAnimation) roots.push(node); });
    return roots;
}
export const waveAnimation = Object.freeze({ update, animationRoots });
