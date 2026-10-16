// Particle-scale measurement diagrams. These scenes show named length scales,
// not literal hard boundaries of fundamental particles.
import * as THREE from '../vendor/three/three.module.min.js';
import { registerAnimation } from './model-animation.js?v=540ebe0ea0';
import { labelNode } from './model-overlay-nodes.js?v=ecd7a14690';

export const PLANCK_LENGTH_M = 1.616255e-35;
export const QUARK_RADIUS_LIMIT_M = 4.3e-19;
export const PROTON_RMS_CHARGE_RADIUS_M = 0.84075e-15;
export const CLASSICAL_ELECTRON_RADIUS_M = 2.8179403205e-15;
export const NEUTRINO_WAVELENGTH_1MEV_M = 1.239841984e-12;

const ORIGIN_X = -0.5;
const END_X = 0.5;

function bar(scene, name, from, to, thickness, color, opacity = 1) {
    const delta = to.clone().sub(from);
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshBasicMaterial({
        color, transparent: opacity < 1, opacity, depthWrite: opacity === 1
    }));
    mesh.name = name;
    mesh.position.copy(from).add(to).multiplyScalar(0.5);
    mesh.scale.set(Math.max(Math.abs(delta.x), thickness), Math.max(Math.abs(delta.y), thickness), Math.max(Math.abs(delta.z), thickness));
    scene.add(mesh);
    return mesh;
}

function measurementRail(scene, { color = 0x637f91, openEnd = false } = {}) {
    bar(scene, 'calibrated-length', new THREE.Vector3(ORIGIN_X, 0, 0), new THREE.Vector3(END_X, 0, 0), 0.004, color);
    for (const x of openEnd ? [ORIGIN_X] : [ORIGIN_X, END_X])
        bar(scene, 'endpoint', new THREE.Vector3(x, -0.022, 0), new THREE.Vector3(x, 0.022, 0), 0.004, color);
}

export function planckLengthScene() {
    const scene = new THREE.Group();
    measurementRail(scene);
    return scene;
}

export function quarkRadiusLimitScene() {
    const scene = new THREE.Group();
    measurementRail(scene, { openEnd: true });
    // An open endpoint denotes an exclusion bound, not a detected particle edge.
    const endpoint = new THREE.Mesh(new THREE.TorusGeometry(0.018, 0.002, 6, 48),
        new THREE.MeshBasicMaterial({ color: 0x637f91 }));
    endpoint.name = 'open-upper-limit-marker';
    endpoint.position.set(END_X, 0, 0);
    scene.add(endpoint);
    return scene;
}

export const PROTON_CLOUD_CROP_RMS = 1.25;
export const protonRadialCdf = r => {
    const x = Math.sqrt(12) * r;
    return 1 - Math.exp(-x) * (1 + x + x * x / 2);
};

export function protonRmsRadiusScene() {
    const scene = new THREE.Group(), positions = [], colors = [];
    let seed = 32611;
    const random = () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) + 0.5) / 4294967296;
    const inner = new THREE.Color(0xa8483b), outer = new THREE.Color(0xc58f77);
    // A dipole-form-factor illustration: rho(r) ~ exp(-sqrt(12) r / r_rms).
    // Its radial density is Gamma(3); antipodal samples keep the centroid exact.
    while (positions.length < 18000 * 3) {
        const radius = -Math.log(random() * random() * random()) / Math.sqrt(12);
        if (radius > PROTON_CLOUD_CROP_RMS) continue;
        const z = 2 * random() - 1, angle = 2 * Math.PI * random(), planar = Math.sqrt(1 - z * z);
        const xyz = [radius * planar * Math.cos(angle), radius * planar * Math.sin(angle), radius * z];
        const color = inner.clone().lerp(outer, radius / PROTON_CLOUD_CROP_RMS);
        for (const sign of [1, -1]) {
            positions.push(...xyz.map(value => value * sign));
            colors.push(color.r, color.g, color.b);
        }
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    const cloud = new THREE.Points(geometry, new THREE.PointsMaterial({ vertexColors: true,
        size: 1.7, sizeAttenuation: false, transparent: true, opacity: 0.6, depthWrite: false }));
    cloud.name = 'proton-dipole-charge-illustration';
    cloud.userData.softPoints = true;
    cloud.userData.pointSize = { max: 2.2, perPixel: 1 / 65 };
    scene.add(cloud);
    const guide = new THREE.Line(new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(0, 0, 0), new THREE.Vector3(1, 0, 0)]),
        new THREE.LineBasicMaterial({ color: 0x965443, transparent: true, opacity: 0.8, depthTest: false }));
    guide.name = 'rms-radius-marker';
    scene.add(guide);
    const ring = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(
        Array.from({ length: 160 }, (_, i) => new THREE.Vector3(Math.cos(i * Math.PI / 80), Math.sin(i * Math.PI / 80), 0))),
        new THREE.LineBasicMaterial({ color: 0xae7766, transparent: true, opacity: 0.3, depthWrite: false }));
    ring.name = 'rms-reference-circle';
    scene.add(ring);
    return scene;
}

// Units: r_e = 1. A point charge's field stores energy density u ~ 1/r^4, so the energy
// in a thin shell goes as 1/r^2 and the energy outside radius r is e^2/(8 pi eps0 r) =
// (mc^2/2)(r_e/r): half the electron's rest energy lies outside r_e, all of it outside r_e/2.
export const ELECTRON_FIELD_CROP = 1.3;
export const electronFieldEnergyOutside = r => 0.5 / r;  // in units of mc^2

export function classicalElectronRadiusScene() {
    const scene = new THREE.Group(), positions = [], colors = [];
    let seed = 0xe1ec7;
    const random = () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) + 0.5) / 4294967296;
    const near = new THREE.Color(0x3b2f98), far = new THREE.Color(0x8fb2dc), inner = 0.1;
    // Radii drawn with weight 1/r^2 (inverse CDF), so dot density follows field energy.
    while (positions.length < 12000 * 3) {
        const t = random(), r = 1 / (1 / inner - t * (1 / inner - 1 / ELECTRON_FIELD_CROP));
        if (r > 1 && random() > (ELECTRON_FIELD_CROP - r) / (ELECTRON_FIELD_CROP - 1)) continue;
        const z = 2 * random() - 1, angle = 2 * Math.PI * random(), planar = Math.sqrt(1 - z * z);
        positions.push(r * planar * Math.cos(angle), r * planar * Math.sin(angle), r * z);
        const color = near.clone().lerp(far, Math.sqrt((r - inner) / (ELECTRON_FIELD_CROP - inner)));
        colors.push(color.r, color.g, color.b);
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    const field = new THREE.Points(geometry, new THREE.PointsMaterial({ vertexColors: true,
        size: 1.6, sizeAttenuation: false, transparent: true, opacity: 0.5, depthWrite: false }));
    field.name = 'electric-field-energy';
    field.userData.softPoints = true;
    field.userData.pointSize = { max: 2.2, perPixel: 1 / 70 };
    scene.add(field);
    const shell = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 24), new THREE.MeshBasicMaterial({
        color: 0x7e9cc4, transparent: true, opacity: 0.07, depthWrite: false }));
    shell.name = 'classical-electron-radius-sphere';
    scene.add(shell);
    const ring = (radius, opacity, name) => {
        const loop = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(Array.from({ length: 160 },
            (_, i) => new THREE.Vector3(radius * Math.cos(i * Math.PI / 80), radius * Math.sin(i * Math.PI / 80), 0))),
            new THREE.LineBasicMaterial({ color: 0x4d5f9a, transparent: true, opacity, depthWrite: false }));
        loop.name = name;
        scene.add(loop);
    };
    ring(1, 0.75, 'classical-electron-radius-circle');
    ring(0.5, 0.45, 'half-radius-circle');
    const rail = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(1, 0, 0)]),
        new THREE.LineBasicMaterial({ color: 0x2e3a66, depthTest: false }));
    rail.name = 'radius-marker';
    scene.add(rail);
    const core = new THREE.Mesh(new THREE.SphereGeometry(0.03, 20, 12), new THREE.MeshBasicMaterial({ color: 0x1c1846 }));
    core.name = 'point-electron-marker';
    scene.add(core);
    scene.add(labelNode('r_e = 2.82 fm', new THREE.Vector3(0.55, 0.06, 0)));
    scene.add(labelNode('Field energy outside: half of mc²', new THREE.Vector3(0, 1.08, 0)));
    scene.add(labelNode('Outside r_e/2: all of mc²', new THREE.Vector3(-0.42, -0.42, 0)));
    scene.add(labelNode('Electron: a point, < 10⁻¹⁸ m', new THREE.Vector3(0.02, -0.07, 0)));
    return scene;
}

export function neutrinoWavelengthScene() {
    const scene = new THREE.Group();
    const points = Array.from({ length: 129 }, (_, index) => {
        const t = index / 128;
        return new THREE.Vector3(ORIGIN_X + t, 0.18 * Math.sin(2 * Math.PI * t), 0);
    });
    const wave = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points), 256, 0.0035, 6, false),
        new THREE.MeshStandardMaterial({ color: 0x638da9, roughness: 0.45 }));
    wave.name = 'one-de-broglie-wavelength';
    scene.add(wave);
    bar(scene, 'wavelength-bracket', new THREE.Vector3(ORIGIN_X, -0.24, 0), new THREE.Vector3(END_X, -0.24, 0), 0.003, 0x8293a0);
    for (const x of [ORIGIN_X, END_X])
        bar(scene, 'wavelength-bracket-end', new THREE.Vector3(x, -0.255, 0), new THREE.Vector3(x, -0.225, 0), 0.003, 0x8293a0);
    scene.userData.animation = { kind: 'neutrino-phase' };
    return scene;
}

registerAnimation('neutrino-phase', (root, elapsed) => {
    const wave = root.getObjectByName('one-de-broglie-wavelength');
    if (!wave) return;
    // A slow illustrative phase, independent of the neutrino's physical frequency.
    const position = wave.geometry.attributes.position, normal = wave.geometry.attributes.normal;
    const phase = elapsed * 0.6;
    for (let ring = 0; ring <= 256; ring++) {
        const t = ring / 256, angle = 2 * Math.PI * t - phase;
        const slope = 0.18 * 2 * Math.PI * Math.cos(angle), norm = Math.hypot(1, slope);
        for (let side = 0; side <= 6; side++) {
            const phi = side * Math.PI / 3, c = Math.cos(phi), s = Math.sin(phi), i = ring * 7 + side;
            const nx = -slope / norm * c, ny = c / norm;
            position.setXYZ(i, t - 0.5 + 0.0035 * nx, 0.18 * Math.sin(angle) + 0.0035 * ny, 0.0035 * s);
            normal.setXYZ(i, nx, ny, s);
        }
    }
    position.needsUpdate = true; normal.needsUpdate = true;
});

const presentation = Object.freeze({ reference_size: 1, layout_width_factor: 1.1,
    focus_scale_factor: 1.3, display_extent_factor: 1 });

export const particleScaleMetadata = Object.freeze({
    'Planck Length': Object.freeze({ id: 'planck-length-ruler', procedural: 'planck-length-ruler',
        name: 'Planck Length', dimension: 'length', value: PLANCK_LENGTH_M, unit: 'm',
        geometry: 'mesh', representation: 'measurement_diagram', presentation,
        basis_url: 'https://physics.nist.gov/cuu/Constants/Table/allascii.txt',
        basis_label: 'Planck length: 2022 CODATA',
        note: 'A single, undivided span marks the Planck length, derived as sqrt(hbar G / c^3) = 1.616255e-35 m in 2022 CODATA. It is a scale constructed from constants, not an experimentally observed minimum length or a measured edge of spacetime.' }),
    'Quark': Object.freeze({ id: 'hera-quark-radius-limit', procedural: 'hera-quark-radius-limit',
        display_label: 'Quark Radius Limit',
        name: 'Quark', dimension: 'length', value: QUARK_RADIUS_LIMIT_M, unit: 'm',
        geometry: 'mesh', representation: 'measurement_diagram', presentation,
        basis_url: 'https://arxiv.org/abs/1611.03825',
        basis_label: 'Effective quark-radius limit: HERA combined data',
        note: 'The open marker represents the HERA 95% confidence upper limit Rq < 0.43 x 10^-16 cm = 4.3e-19 m on an effective quark radius in a specified quark-form-factor fit to combined H1 and ZEUS data. It is not a measured quark radius, a universal model-independent bound, or a solid quark boundary.' }),
    'Proton Radius': Object.freeze({ id: 'proton-rms-charge-radius', procedural: 'proton-rms-charge-radius',
        name: 'Proton Radius', dimension: 'length', value: PROTON_RMS_CHARGE_RADIUS_M, unit: 'm',
        geometry: 'mesh', representation: 'measurement_diagram', presentation: Object.freeze({ ...presentation,
            layout_width_factor: 2.6, focus_scale_factor: 3, display_extent_factor: 2.5 }),
        basis_url: 'https://pdgprod.lbl.gov/pdgprod/pdgLive/DataBlock.action?node=S016CR',
        basis_label: 'Proton rms electric charge radius: PDG / 2022 CODATA',
        sources: Object.freeze(['https://doi.org/10.3390/atoms6010002', 'https://arxiv.org/abs/1002.0355']),
        note: 'A three-dimensional dipole-profile charge-cloud illustration. The center-to-circle line is the listed rms electric charge radius, 0.84075(64) fm; the circle is not a hard surface. The sphere therefore spans twice the listed radius, with a sparse tail beyond it. The illustrative density rho(r) is proportional to exp(-sqrt(12) r/r_rms), the nonrelativistic dipole-form-factor approximation discussed by Sick (2018), not a measured proton interior. The view crops at 1.25 rms radii and contains about 80.7% of that model distribution. Relativistic charge density has no unique static 3D interpretation; Miller (2010) discusses that limitation.' }),
    'Electron': Object.freeze({ id: 'classical-electron-radius', procedural: 'classical-electron-radius',
        display_label: 'Classical Electron Radius',
        name: 'Electron', dimension: 'length', value: CLASSICAL_ELECTRON_RADIUS_M, unit: 'm',
        geometry: 'mesh', representation: 'measurement_diagram', presentation: Object.freeze({ ...presentation,
            layout_width_factor: 2.6, focus_scale_factor: 3, display_extent_factor: 2.5 }),
        basis_url: 'https://physics.nist.gov/cgi-bin/cuu/Value?re',
        basis_label: 'Classical electron radius: 2022 CODATA',
        note: 'The electron itself is the dark dot: experiments find it point-like, smaller than 10^-18 m (the dot is enlarged). The blue haze is the energy stored in its electric field, drawn with density proportional to the field energy (which falls as 1/r^4), cropped just beyond the sphere. The sphere marks the classical electron radius r_e = 2.8179403205e-15 m (2022 CODATA): the field outside it holds exactly half the electron\'s rest energy, mc^2/2, and the field outside r_e/2 (inner ring) holds all of it. That is why r_e is the size at which classical physics breaks down for the electron; it is not the physical radius or a measured surface. The sphere spans twice the listed radius.' }),
    '1 MeV Neutrino Wavelength': Object.freeze({ id: 'neutrino-wavelength-1mev', procedural: 'neutrino-wavelength-1mev',
        name: '1 MeV Neutrino Wavelength', dimension: 'length', value: NEUTRINO_WAVELENGTH_1MEV_M, unit: 'm', geometry: 'mesh',
        representation: 'measurement_diagram', presentation,
        basis_url: 'https://pdg.lbl.gov/2024/reviews/rpp2024-rev-neutrino-mixing.pdf',
        basis_label: 'Neutrino mass constraints: Particle Data Group',
        sources: Object.freeze(['https://physics.nist.gov/cuu/Constants/Table/allascii.txt', 'https://pdg.lbl.gov/2024/reviews/rpp2024-rev-neutrino-mixing.pdf']),
        note: 'One de Broglie wavelength for a 1 MeV ultrarelativistic neutrino: lambda = h/p is approximately hc/E = 1.23984e-12 m. This depends on the stated energy and is not an intrinsic neutrino size. The wave is a schematic amplitude, not a trajectory or a measured transverse extent. Its slow phase animation is illustrative and does not reproduce the physical frequency.' })
});

export const particleScaleScenes = Object.freeze({
    'planck-length-ruler': planckLengthScene,
    'hera-quark-radius-limit': quarkRadiusLimitScene,
    'proton-rms-charge-radius': protonRmsRadiusScene,
    'classical-electron-radius': classicalElectronRadiusScene,
    'neutrino-wavelength-1mev': neutrinoWavelengthScene
});
