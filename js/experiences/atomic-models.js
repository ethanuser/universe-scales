// Quantum atom point-cloud models. All coordinates are in Bohr radii before
// presentation calibration; point counts are deliberately modest for WebGL.
import * as THREE from '../vendor/three/three.module.min.js';

export const BOHR_RADIUS_PM = 52.9177210903;
export const HYDROGEN_BOUNDARY_BOHR = 1;
export const HYDROGEN_ENCLOSED_PROBABILITY = 1 - 5 * Math.exp(-2);
export const CARBON_EFFECTIVE_CHARGES = Object.freeze({ '1s': 5.6727, '2s': 3.22, '2p': 3.14 });
export const CARBON_RADIAL_PROBABILITY = 0.9;

const TAU = 2 * Math.PI;
function randomSource(seed) {
    return () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) + 0.5) / 4294967296;
}

function gammaCdf3(x) {
    return 1 - Math.exp(-x) * (1 + x + x * x / 2);
}
function gammaCdf5(x) {
    return 1 - Math.exp(-x) * (1 + x + x * x / 2 + x ** 3 / 6 + x ** 4 / 24);
}
// In x = Z_eff r/a_0, the 1s radial CDF is Gamma(shape=3, rate=2).
function carbon1sCdf(x) {
    return gammaCdf3(2 * x);
}
function bisectQuantile(cdf, probability) {
    let low = 0, high = 1;
    while (cdf(high) < probability) high *= 2;
    for (let index = 0; index < 64; index++) {
        const middle = (low + high) / 2;
        if (cdf(middle) < probability) low = middle;
        else high = middle;
    }
    return (low + high) / 2;
}

// Hydrogenic radial laws in x = Z_eff r/a_0. The normalized 2s density has
// its radial node at x=2; 2p has a Gamma(shape=5, rate=1) radial law.
function twoSCdf(x) {
    return Math.max(0, Math.min(1,
        1 - Math.exp(-x) * (x ** 4 + 4 * x * x + 8 * x + 8) / 8));
}
function sampleFromCdf(cdf, max, random) {
    const target = random() * cdf(max);
    let low = 0, high = max;
    for (let index = 0; index < 36; index++) {
        const middle = (low + high) / 2;
        if (cdf(middle) < target) low = middle;
        else high = middle;
    }
    return (low + high) / 2;
}
function sphereDirection(random) {
    const z = 2 * random() - 1, angle = TAU * random();
    const planar = Math.sqrt(1 - z * z);
    return [planar * Math.cos(angle), planar * Math.sin(angle), z];
}
function orbitalSamples({ count, cdf, cutoff, zeff, angular = 's', seed }) {
    const random = randomSource(seed), positions = [];
    while (positions.length < count * 3) {
        const radius = sampleFromCdf(cdf, cutoff, random) / zeff;
        const direction = sphereDirection(random);
        if (angular !== 's') {
            const axis = angular === 'px' ? 0 : 1;
            if (random() > direction[axis] ** 2) continue;
        }
        positions.push(radius * direction[0], radius * direction[1], radius * direction[2]);
    }
    return positions;
}
function addCloud(scene, name, positions, color, size, opacity) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    const points = new THREE.Points(geometry, new THREE.PointsMaterial({ color, size, sizeAttenuation: false,
        transparent: true, opacity, depthWrite: false }));
    points.name = name;
    points.userData.pointSize = { max: size + 0.1, perPixel: 1 / 48 };
    scene.add(points);
    return points;
}
function addBoundary(scene, name, radius, color, opacity = 0.075) {
    const boundary = new THREE.Mesh(new THREE.SphereGeometry(radius, 24, 16),
        new THREE.MeshBasicMaterial({ color, transparent: true, opacity: Math.min(opacity, 0.025), depthWrite: false }));
    boundary.name = name;
    scene.add(boundary);
    const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.3, depthWrite: false });
    for (const axis of ['x', 'y', 'z']) {
        const points = Array.from({ length: 97 }, (_, index) => {
            const a = TAU * index / 96, u = radius * Math.cos(a), v = radius * Math.sin(a);
            return new THREE.Vector3(axis === 'x' ? 0 : u, axis === 'y' ? 0 : axis === 'x' ? u : v,
                axis === 'z' ? 0 : v);
        });
        const ring = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), material);
        ring.name = `${name}-${axis}-contour`;
        scene.add(ring);
    }
    return boundary;
}

// Hydrogenic 2p density is proportional to r^2 cos(theta)^2 exp(-Z*r).
// The two roots at each polar angle close into an isodensity lobe, rather
// than drawing an arbitrary ellipsoid and calling it a probability boundary.
export const P_CONTOUR_PEAK_FRACTION = 0.1;
export function pContourRadius(theta, outer) {
    const target = P_CONTOUR_PEAK_FRACTION * 4 * Math.exp(-2) / Math.cos(theta) ** 2;
    let low = outer ? 2 : 0, high = outer ? 20 : 2;
    for (let i = 0; i < 48; i++) {
        const x = (low + high) / 2, density = x * x * Math.exp(-x);
        if ((density > target) === outer) low = x; else high = x;
    }
    return (low + high) / 2 / CARBON_EFFECTIVE_CHARGES['2p'];
}
function addPContours(scene, axis, color) {
    const thetaMax = Math.acos(Math.sqrt(P_CONTOUR_PEAK_FRACTION));
    const rings = 48, sides = 28;
    const pointAt = (ring, phi, sign) => {
        const outer = ring <= rings / 2;
        const theta = thetaMax * (outer ? ring : rings - ring) / (rings / 2);
        const radius = pContourRadius(theta, outer), axial = sign * radius * Math.cos(theta);
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
            opacity: 0.035, side: THREE.DoubleSide, depthWrite: false }));
        surface.name = `carbon-2p${axis}-${sign}-isodensity`;
        scene.add(surface);
        for (const phi of [0, Math.PI / 2, Math.PI, Math.PI * 1.5]) {
            const curve = new THREE.Line(new THREE.BufferGeometry().setFromPoints(
                Array.from({ length: rings + 1 }, (_, ring) => pointAt(ring, phi, sign))),
            new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.4, depthWrite: false }));
            curve.name = `${surface.name}-contour`;
            scene.add(curve);
        }
    }
}

export const atomicModelMetadata = Object.freeze({
    'Hydrogen Atom': Object.freeze({ id: 'hydrogen-1s-quantum', procedural: 'hydrogen-1s-quantum',
        name: 'Hydrogen Atom', dimension: 'length', value: 5.3e-11, unit: 'm',
        geometry: 'mesh', presentation: Object.freeze({ reference_size: 1, layout_width_factor: 2.2,
            focus_scale_factor: 2.2, display_extent_factor: 2.2 }),
        source: 'https://openstax.org/books/university-physics-volume-3/pages/8-1-the-hydrogen-atom',
        basis_url: 'https://openstax.org/books/university-physics-volume-3/pages/8-1-the-hydrogen-atom',
        note: 'A sampled hydrogen 1s probability cloud clipped at exactly one Bohr radius (53 pm, a radius). The enclosed probability at that boundary is exactly 1 - 5e^-2 = 32.33%; the Bohr radius is the most probable radial distance, not a hard orbit.' }),
    'Carbon Atom': Object.freeze({ id: 'carbon-atom-independent-electron', procedural: 'carbon-independent-electron',
        name: 'Carbon Atom', dimension: 'length', value: 7e-11, unit: 'm',
        geometry: 'mesh', presentation: Object.freeze({ reference_size: 70 / BOHR_RADIUS_PM, layout_width_factor: 4.6,
            focus_scale_factor: 4.6, display_extent_factor: 4.6, yaw: -12, pitch: 8 }),
        source: 'https://winter.group.shef.ac.uk/webelements/carbon/atoms.html',
        sources: Object.freeze([
            'https://winter.group.shef.ac.uk/webelements/carbon/atoms.html',
            'https://doi.org/10.1063/1.1733573'
        ]),
        basis_url: 'https://winter.group.shef.ac.uk/webelements/carbon/atoms.html',
        note: 'Independent-electron approximation for neutral carbon: 1s² 2s² 2p², with the two 2p electrons placed in orthogonal real p orbitals to show their distinct dumbbell lobes. Hydrogenic orbitals use Clementi–Raimondi effective charges as an approximation to SCF screening (1s 5.6727, 2s 3.22, 2p 3.14); this is not an exact correlated six-electron solution. Each displayed orbital is clipped at its own 90% radial-probability radius. Blue and amber circles mark the 1s and 2s cutoffs; the green and rose 2p lobe contours mark 10% of each orbital\'s peak density, not a hard edge or a 90% enclosure. Point counts represent the 2:2:1:1 electron occupancy. The listed 70 pm is an empirical atomic radius, not a van der Waals radius. The tiny central nucleus marker is enlarged for visibility and is not to scale.' })
});

export const HYDROGEN_RADIUS_PROBABILITY = radius => 1 - Math.exp(-2 * radius) * (1 + 2 * radius + 2 * radius * radius);
export const CARBON_ORBITAL_CDFS = Object.freeze({ '1s': carbon1sCdf, '2s': twoSCdf, '2p': gammaCdf5 });
export const CARBON_ORBITAL_BOUNDARIES_BOHR = Object.freeze({
    '1s': bisectQuantile(carbon1sCdf, CARBON_RADIAL_PROBABILITY) / CARBON_EFFECTIVE_CHARGES['1s'],
    '2s': bisectQuantile(twoSCdf, CARBON_RADIAL_PROBABILITY) / CARBON_EFFECTIVE_CHARGES['2s'],
    '2p': bisectQuantile(gammaCdf5, CARBON_RADIAL_PROBABILITY) / CARBON_EFFECTIVE_CHARGES['2p']
});

export function hydrogenAtomScene() {
    const scene = new THREE.Group();
    const random = randomSource(0x1a70a0);
    const positions = [];
    while (positions.length < 3 * 7000) {
        const radius = -Math.log(random() * random() * random()) / 2;
        if (radius > HYDROGEN_BOUNDARY_BOHR) continue;
        const [x, y, z] = sphereDirection(random);
        positions.push(radius * x, radius * y, radius * z);
    }
    addCloud(scene, 'hydrogen-1s-probability', positions, 0x2675ae, 1.5, 0.36);
    addBoundary(scene, 'one-bohr-radius-boundary', HYDROGEN_BOUNDARY_BOHR, 0x2675ae, 0.08);
    const nucleus = new THREE.Mesh(new THREE.SphereGeometry(0.004, 8, 6),
        new THREE.MeshBasicMaterial({ color: 0xd9534f }));
    nucleus.name = 'proton';
    scene.add(nucleus);
    return scene;
}

export function carbonAtomScene() {
    const scene = new THREE.Group();
    const cutoffs = {
        '1s': bisectQuantile(carbon1sCdf, CARBON_RADIAL_PROBABILITY),
        '2s': bisectQuantile(twoSCdf, CARBON_RADIAL_PROBABILITY),
        '2p': bisectQuantile(gammaCdf5, CARBON_RADIAL_PROBABILITY)
    };
    addCloud(scene, 'carbon-1s-electron-pair', orbitalSamples({ count: 3000, cdf: carbon1sCdf,
        cutoff: cutoffs['1s'], zeff: CARBON_EFFECTIVE_CHARGES['1s'], seed: 0xc001 }), 0x468bd0, 1.5, 0.38);
    addBoundary(scene, 'carbon-1s-90-percent-boundary', CARBON_ORBITAL_BOUNDARIES_BOHR['1s'], 0x468bd0);
    addCloud(scene, 'carbon-2s-electron-pair', orbitalSamples({ count: 3000, cdf: twoSCdf,
        cutoff: cutoffs['2s'], zeff: CARBON_EFFECTIVE_CHARGES['2s'], seed: 0xc002 }), 0xe9a23b, 1.5, 0.32);
    addBoundary(scene, 'carbon-2s-90-percent-boundary', CARBON_ORBITAL_BOUNDARIES_BOHR['2s'], 0xe9a23b);
    addCloud(scene, 'carbon-2px-electron', orbitalSamples({ count: 1500, cdf: gammaCdf5,
        cutoff: cutoffs['2p'], zeff: CARBON_EFFECTIVE_CHARGES['2p'], angular: 'px', seed: 0xc003 }), 0x4aaa82, 1.5, 0.32);
    addCloud(scene, 'carbon-2py-electron', orbitalSamples({ count: 1500, cdf: gammaCdf5,
        cutoff: cutoffs['2p'], zeff: CARBON_EFFECTIVE_CHARGES['2p'], angular: 'py', seed: 0xc004 }), 0xd56c72, 1.5, 0.32);
    addBoundary(scene, 'carbon-2p-90-percent-boundary', CARBON_ORBITAL_BOUNDARIES_BOHR['2p'], 0x7eaa82);
    addPContours(scene, 'x', 0x29815c);
    addPContours(scene, 'y', 0xb7485b);
    const nucleus = new THREE.Mesh(new THREE.SphereGeometry(0.006, 8, 6),
        new THREE.MeshBasicMaterial({ color: 0x343a40 }));
    nucleus.name = 'carbon-nucleus';
    scene.add(nucleus);
    return scene;
}

export const atomicScenes = Object.freeze({
    'hydrogen-1s-quantum': hydrogenAtomScene,
    'carbon-independent-electron': carbonAtomScene
});
