// Quantum atom point-cloud models. Coordinates are in Bohr radii (a0).
//
// Size rule: each atom is drawn inside one boundary sphere whose DIAMETER is the
// listed Length value, so the model renders at exactly its listed size. Dots
// sample the electron probability density and stop at that sphere; the notes
// state how much of the probability the sphere holds.
import * as THREE from '../vendor/three/three.module.min.js';

export const BOHR_RADIUS_PM = 52.9177210903; // CODATA 2018
const TAU = 2 * Math.PI;

// Radial cumulative probabilities for hydrogen-like orbitals, in x = Z r / a0.
// 1s: P(r) ~ r^2 e^(-2x); 2s: r^2 (2 - x)^2 e^(-x); 2p: r^4 e^(-x).
export const radialCdf = Object.freeze({
    '1s': x => 1 - Math.exp(-2 * x) * (1 + 2 * x + 2 * x * x),
    '2s': x => 1 - Math.exp(-x) * (x ** 4 + 4 * x * x + 8 * x + 8) / 8,
    '2p': x => 1 - Math.exp(-x) * (1 + x + x * x / 2 + x ** 3 / 6 + x ** 4 / 24)
});

// Hydrogen: the boundary is one Bohr radius, the most probable electron distance.
export const HYDROGEN_BOUNDARY_BOHR = 1;
export const HYDROGEN_ENCLOSED_PROBABILITY = radialCdf['1s'](HYDROGEN_BOUNDARY_BOHR); // 1 - 5e^-2

// Carbon, 1s2 2s2 2p2, as hydrogen-like orbitals with Clementi and Raimondi's
// (1963) screened effective charges. The boundary is carbon's 70 pm empirical
// atomic radius, close to the 2p most probable radius 4 a0 / Z_2p = 67.5 pm.
export const CARBON_EFFECTIVE_CHARGES = Object.freeze({ '1s': 5.6727, '2s': 3.2166, '2p': 3.1358 });
export const CARBON_RADIUS_PM = 70;
export const CARBON_BOUNDARY_BOHR = CARBON_RADIUS_PM / BOHR_RADIUS_PM;
export const CARBON_ENCLOSED = Object.freeze(Object.fromEntries(Object.entries(CARBON_EFFECTIVE_CHARGES)
    .map(([orbital, z]) => [orbital, radialCdf[orbital](z * CARBON_BOUNDARY_BOHR)])));
export const CARBON_ENCLOSED_ELECTRONS = 2 * (CARBON_ENCLOSED['1s'] + CARBON_ENCLOSED['2s'] + CARBON_ENCLOSED['2p']);
// 2p lobes are outlined where density falls to this fraction of its peak;
// the level is chosen so the lobe tips touch the boundary sphere (about 50%).
const pDensity = x => x * x * Math.exp(-x); // along the lobe axis, in x = Z r / a0
export const P_CONTOUR_PEAK_FRACTION = pDensity(CARBON_EFFECTIVE_CHARGES['2p'] * CARBON_BOUNDARY_BOHR) / pDensity(2);

function randomSource(seed) {
    return () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) + 0.5) / 4294967296;
}
function inverseCdf(cdf, target, max) {
    let low = 0, high = max;
    for (let index = 0; index < 40; index++) {
        const middle = (low + high) / 2;
        if (cdf(middle) < target) low = middle; else high = middle;
    }
    return (low + high) / 2;
}
// Samples |psi|^2 inside radius `limit` (a0): radial by inverse CDF, angular
// uniformly for s or by rejection on cos^2 for real p orbitals.
function orbitalSamples({ orbital, z, limit, count, angular = 's', seed }) {
    const random = randomSource(seed), positions = [], xmax = z * limit, cdf = radialCdf[orbital];
    const top = cdf(xmax);
    while (positions.length < count * 3) {
        const radius = inverseCdf(cdf, random() * top, xmax) / z;
        const cosine = 2 * random() - 1, angle = TAU * random(), planar = Math.sqrt(1 - cosine * cosine);
        const direction = [planar * Math.cos(angle), planar * Math.sin(angle), cosine];
        if (angular === 'px' && random() > direction[0] ** 2) continue;
        if (angular === 'py' && random() > direction[1] ** 2) continue;
        positions.push(radius * direction[0], radius * direction[1], radius * direction[2]);
    }
    return positions;
}
function addCloud(scene, name, positions, color, opacity) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    const points = new THREE.Points(geometry, new THREE.PointsMaterial({ color, size: 1.5,
        sizeAttenuation: false, transparent: true, opacity, depthWrite: false }));
    points.name = name;
    points.userData.pointSize = { max: 1.6, perPixel: 1 / 48 };
    scene.add(points);
}
// A barely-there sphere plus three great circles marks the boundary.
function addBoundary(scene, name, radius, color, label) {
    const sphere = new THREE.Mesh(new THREE.SphereGeometry(radius, 32, 20),
        new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.035, depthWrite: false }));
    sphere.name = name;
    scene.add(sphere);
    const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.35, depthWrite: false });
    for (const axis of ['x', 'y', 'z']) {
        const ring = new THREE.Line(new THREE.BufferGeometry().setFromPoints(Array.from({ length: 97 }, (_, index) => {
            const a = TAU * index / 96, u = radius * Math.cos(a), v = radius * Math.sin(a);
            return axis === 'x' ? new THREE.Vector3(0, u, v) : axis === 'y' ? new THREE.Vector3(u, 0, v) : new THREE.Vector3(u, v, 0);
        })), material);
        ring.name = `${name}-${axis}`;
        scene.add(ring);
    }
    const anchor = new THREE.Object3D();
    anchor.position.set(0, radius * 1.06, 0);
    anchor.userData.label = label;
    scene.add(anchor);
}
function addNucleus(scene, name, color) {
    // Enlarged about 2,000x so it is visible; a real nucleus is femtometers across.
    const nucleus = new THREE.Mesh(new THREE.SphereGeometry(0.012, 10, 8), new THREE.MeshBasicMaterial({ color }));
    nucleus.name = name;
    scene.add(nucleus);
}

// A 2p isodensity lobe: density ~ x^2 e^-x cos^2(theta) at level c solves
// r(theta) on both sides of the peak, closing a lobe along +/- the axis.
export function pContourRadius(theta, outer) {
    const target = P_CONTOUR_PEAK_FRACTION * pDensity(2) / Math.cos(theta) ** 2;
    let low = outer ? 2 : 0, high = outer ? 30 : 2;
    for (let index = 0; index < 48; index++) {
        const x = (low + high) / 2;
        if ((pDensity(x) > target) === outer) low = x; else high = x;
    }
    return (low + high) / 2 / CARBON_EFFECTIVE_CHARGES['2p'];
}
function addPContours(scene, axis, color) {
    const thetaMax = Math.acos(Math.sqrt(P_CONTOUR_PEAK_FRACTION)), rings = 40, sides = 24;
    const pointAt = (ring, phi, sign) => {
        const outer = ring <= rings / 2;
        const theta = thetaMax * (outer ? ring : rings - ring) / (rings / 2);
        const radius = pContourRadius(Math.min(theta, thetaMax - 1e-9), outer);
        const axial = sign * radius * Math.cos(theta);
        const u = radius * Math.sin(theta) * Math.cos(phi), v = radius * Math.sin(theta) * Math.sin(phi);
        return axis === 'x' ? new THREE.Vector3(axial, u, v) : new THREE.Vector3(u, axial, v);
    };
    for (const sign of [-1, 1]) {
        const positions = [], indices = [];
        for (let ring = 0; ring <= rings; ring++) for (let side = 0; side <= sides; side++)
            positions.push(...pointAt(ring, TAU * side / sides, sign).toArray());
        for (let ring = 0; ring < rings; ring++) for (let side = 0; side < sides; side++) {
            const a = ring * (sides + 1) + side, b = a + sides + 1;
            indices.push(a, b, a + 1, b, b + 1, a + 1);
        }
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        geometry.setIndex(indices);
        const surface = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({ color, transparent: true,
            opacity: 0.07, side: THREE.DoubleSide, depthWrite: false }));
        surface.name = `carbon-2p${axis}-${sign > 0 ? 'plus' : 'minus'}-lobe`;
        scene.add(surface);
        for (const phi of [0, Math.PI / 2, Math.PI, 1.5 * Math.PI]) {
            const outline = new THREE.Line(new THREE.BufferGeometry().setFromPoints(
                Array.from({ length: rings + 1 }, (_, ring) => pointAt(ring, phi, sign))),
            new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.45, depthWrite: false }));
            outline.name = `${surface.name}-outline`;
            scene.add(outline);
        }
    }
    const anchor = new THREE.Object3D();
    anchor.position[axis] = CARBON_BOUNDARY_BOHR * 0.72;
    anchor.userData.label = axis === 'x' ? '2pₓ' : '2pᵧ';
    anchor.userData.labelClass = axis === 'x' ? 'is-orbital-x' : 'is-orbital-y';
    scene.add(anchor);
}

const percent = value => `${(100 * value).toFixed(1)}%`;
export const atomicModelMetadata = Object.freeze({
    'Hydrogen Atom': Object.freeze({ id: 'hydrogen-1s-quantum', procedural: 'hydrogen-1s-quantum',
        name: 'Hydrogen Atom', dimension: 'length', value: 2 * BOHR_RADIUS_PM * 1e-12, unit: 'm', geometry: 'mesh',
        // Two Bohr radii (the boundary diameter) equal the listed value.
        presentation: Object.freeze({ reference_size: 2 * HYDROGEN_BOUNDARY_BOHR, layout_width_factor: 1,
            focus_scale_factor: 1.3, display_extent_factor: 1 }),
        source: 'https://physics.nist.gov/cgi-bin/cuu/Value?bohrrada0',
        basis_url: 'https://openstax.org/books/university-physics-volume-3/pages/8-1-the-hydrogen-atom',
        basis_label: 'Orbital basis: OpenStax University Physics',
        note: `Hydrogen's 1s electron cloud, sampled from its exact probability density and cut off at one Bohr radius (52.9 pm), the electron's most probable distance from the proton. That sphere holds ${percent(HYDROGEN_ENCLOSED_PROBABILITY)} of the probability (exactly 1 - 5/e²); the real cloud has no edge and thins out exponentially beyond it. The listed 106 pm is the sphere's diameter. The red nucleus is enlarged about 2,000 times to be visible.` }),
    'Carbon Atom': Object.freeze({ id: 'carbon-atom-quantum', procedural: 'carbon-atom-quantum',
        name: 'Carbon Atom', dimension: 'length', value: 2 * CARBON_RADIUS_PM * 1e-12, unit: 'm', geometry: 'mesh',
        presentation: Object.freeze({ reference_size: 2 * CARBON_BOUNDARY_BOHR, layout_width_factor: 1,
            focus_scale_factor: 1.3, display_extent_factor: 1, yaw: -20, pitch: 14 }),
        source: 'https://webelements.co.uk/carbon/atom_sizes.html',
        sources: Object.freeze(['https://webelements.co.uk/carbon/atom_sizes.html', 'https://doi.org/10.1063/1.1733573']),
        basis_url: 'https://doi.org/10.1063/1.1733573',
        basis_label: 'Effective charges: Clementi and Raimondi (1963)',
        note: `Carbon's six electrons (1s² 2s² 2p²) as hydrogen-like orbitals with screened effective charges (Clementi and Raimondi, 1963), an approximation rather than an exact six-electron solution. Dots sample each orbital's density and stop at carbon's 70 pm empirical atomic radius; the listed 140 pm is that sphere's diameter. The sphere holds ${percent(CARBON_ENCLOSED_ELECTRONS / 6)} of the electron probability: all of the tight blue 1s pair, ${percent(CARBON_ENCLOSED['2s'])} of the amber 2s pair, and ${percent(CARBON_ENCLOSED['2p'])} of each 2p electron. The two occupied 2p orbitals (green 2pₓ, rose 2pᵧ) are outlined where their density falls to half its peak, which is where their lobes reach the sphere. The nucleus is enlarged for visibility.` })
});

export function hydrogenAtomScene() {
    const scene = new THREE.Group();
    addCloud(scene, 'hydrogen-1s-probability', orbitalSamples({ orbital: '1s', z: 1,
        limit: HYDROGEN_BOUNDARY_BOHR, count: 7000, seed: 0x1a70a0 }), 0x2675ae, 0.38);
    addBoundary(scene, 'bohr-radius-boundary', HYDROGEN_BOUNDARY_BOHR, 0x2675ae,
        `Bohr radius: ${percent(HYDROGEN_ENCLOSED_PROBABILITY)} inside`);
    addNucleus(scene, 'proton', 0xd9534f);
    return scene;
}

// Dots per enclosed electron are equal across orbitals, so the cloud is a fair
// sample of the total electron density inside the boundary.
const DOTS_PER_ELECTRON = 2600;
export function carbonAtomScene() {
    const scene = new THREE.Group();
    const limit = CARBON_BOUNDARY_BOHR, z = CARBON_EFFECTIVE_CHARGES;
    const dots = orbital => Math.round(DOTS_PER_ELECTRON * CARBON_ENCLOSED[orbital] * (orbital === '2p' ? 1 : 2));
    addCloud(scene, 'carbon-1s-pair', orbitalSamples({ orbital: '1s', z: z['1s'], limit, count: dots('1s'), seed: 0xc001 }), 0x3f7fc8, 0.3);
    addCloud(scene, 'carbon-2s-pair', orbitalSamples({ orbital: '2s', z: z['2s'], limit, count: dots('2s'), seed: 0xc002 }), 0xe39a2e, 0.42);
    addCloud(scene, 'carbon-2px-electron', orbitalSamples({ orbital: '2p', z: z['2p'], limit, count: dots('2p'), angular: 'px', seed: 0xc003 }), 0x2f9a6c, 0.45);
    addCloud(scene, 'carbon-2py-electron', orbitalSamples({ orbital: '2p', z: z['2p'], limit, count: dots('2p'), angular: 'py', seed: 0xc004 }), 0xcf5a66, 0.45);
    addPContours(scene, 'x', 0x2f9a6c);
    addPContours(scene, 'y', 0xcf5a66);
    addBoundary(scene, 'carbon-atomic-radius-boundary', limit, 0x5f6b76,
        `70 pm radius: ${percent(CARBON_ENCLOSED_ELECTRONS / 6)} of electrons inside`);
    addNucleus(scene, 'carbon-nucleus', 0x343a40);
    return scene;
}

// Iron-56 nucleus: 26 protons and 30 neutrons packed into the uniform sphere
// implied by its measured rms charge radius, 3.7377 fm (Angeli & Marinova
// 2013): R = sqrt(5/3) * r_rms = 4.83 fm, about 9.7 fm across. Nucleons are
// drawn at the proton charge radius, 0.84 fm. Coordinates are femtometers.
export const IRON_56 = Object.freeze({ protons: 26, neutrons: 30, rmsChargeRadius: 3.7377,
    nucleonRadius: 0.8409 });
export const IRON_56_RADIUS = Math.sqrt(5 / 3) * IRON_56.rmsChargeRadius;
export function nucleonCenters({ protons, neutrons, nucleonRadius }, radius, seed = 0x56fe) {
    const random = randomSource(seed), count = protons + neutrons;
    // Jittered close packing: the lattice points nearest the center, then
    // scaled so the outermost nucleons touch the nuclear surface.
    const spacing = 2 * nucleonRadius * 0.93, points = [];
    const span = Math.ceil(radius / spacing) + 2;
    for (let i = -span; i <= span; i++) for (let j = -span; j <= span; j++) for (let k = -span; k <= span; k++) {
        const offset = (j + k) % 2 === 0 ? 0 : 0.5; // face-centered stacking
        points.push(new THREE.Vector3((i + offset) * spacing, j * spacing * 0.8165, (k + (j % 2) * 0.5) * spacing)
            .add(new THREE.Vector3(random() - 0.5, random() - 0.5, random() - 0.5).multiplyScalar(0.25 * spacing)));
    }
    points.sort((a, b) => a.length() - b.length());
    const chosen = points.slice(0, count);
    const outer = Math.max(...chosen.map(point => point.length()));
    const scale = (radius - nucleonRadius) / outer;
    const kinds = Array.from({ length: count }, (_, index) => index < protons ? 'proton' : 'neutron');
    for (let index = kinds.length - 1; index > 0; index--) {
        const swap = Math.floor(random() * (index + 1));
        [kinds[index], kinds[swap]] = [kinds[swap], kinds[index]];
    }
    return chosen.map((point, index) => ({ position: point.multiplyScalar(scale), kind: kinds[index] }));
}
export function ironNucleusScene() {
    const scene = new THREE.Group();
    const sphere = new THREE.SphereGeometry(IRON_56.nucleonRadius, 28, 20);
    const materials = { proton: new THREE.MeshStandardMaterial({ color: 0xd8483f, roughness: 0.45 }),
        neutron: new THREE.MeshStandardMaterial({ color: 0x8796ab, roughness: 0.45 }) };
    for (const { position, kind } of nucleonCenters(IRON_56, IRON_56_RADIUS)) {
        const nucleon = new THREE.Mesh(sphere, materials[kind]);
        nucleon.position.copy(position);
        nucleon.name = kind;
        scene.add(nucleon);
    }
    const anchor = new THREE.Object3D();
    anchor.position.set(0, IRON_56_RADIUS * 1.12, 0);
    anchor.userData.label = 'Iron-56: 26 protons, 30 neutrons';
    scene.add(anchor);
    return scene;
}
export const nuclearModelMetadata = Object.freeze({
    'Atomic Nucleus': Object.freeze({ id: 'iron-56-nucleus', procedural: 'iron-56-nucleus', geometry: 'mesh',
        // Model units are femtometers; 10 fm is the listed typical diameter.
        presentation: Object.freeze({ reference_size: 10, layout_width_factor: 1, focus_scale_factor: 1.3,
            display_extent_factor: 1, yaw: 20, pitch: 10 }),
        basis_url: 'https://doi.org/10.1016/j.adt.2011.12.006',
        basis_label: 'Charge radii: Angeli & Marinova (2013)',
        note: 'An iron-56 nucleus, the most tightly bound kind, drawn as 26 red protons and 30 gray neutrons packed into a sphere 9.7 fm across, the size implied by its measured charge radius. That is about 14,000 times smaller than a carbon atom. Real nucleons are not hard balls: they are fuzzy quantum objects in constant motion, so this is the conventional picture, not a snapshot.' })
});

export const atomicScenes = Object.freeze({
    'iron-56-nucleus': ironNucleusScene,
    'hydrogen-1s-quantum': hydrogenAtomScene,
    'carbon-atom-quantum': carbonAtomScene
});
