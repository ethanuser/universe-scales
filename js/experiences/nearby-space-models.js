// Compact, referenced depictions of nearby stars and Local Group galaxies.
// Positions and galaxy radii use the same kpc scale in the Local Group scene.
import * as THREE from '../vendor/three/three.module.min.js';
import { MILKY_WAY, ANDROMEDA, galaxyCloud } from './cosmic-models.js?v=bd847e9b00';

export const KPC = 3.0856775814913673e19;
export const PROXIMA_DISTANCE_PC = 1.301971;
export const PROXIMA_DISTANCE_M = (PROXIMA_DISTANCE_PC / 1000) * KPC;
const LY = 9.4607304725808e15;
export const GALAXY_DISPLAY_FACTOR = 1;
const CALLOUTS = Object.freeze({
    'Milky Way': { x: -70, y: -20 },
    'Andromeda (M31)': { x: -25, y: -35 },
    'Triangulum (M33)': { x: 80, y: 32 },
    'Large Magellanic Cloud': { x: -100, y: 40 },
    'Small Magellanic Cloud': { x: -50, y: 75 }
});
const STAGE_LABELS = Object.freeze({
    'Milky Way': 'Milky Way',
    'Andromeda (M31)': 'M31',
    'Triangulum (M33)': 'M33',
    'Large Magellanic Cloud': 'LMC',
    'Small Magellanic Cloud': 'SMC'
});

function seeded(seed) {
    return () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) + 0.5) / 4294967296;
}

function spiralGalaxy({ radius, seed, arms = 2, inclination = 0, positionAngle = 0,
    color = 0x91bce8, points = 900, spheroid = false }) {
    const random = seeded(seed), positions = [], colors = [];
    for (let index = 0; index < points; index++) {
        const angle0 = random() * Math.PI * 2;
        const radial = spheroid ? radius * Math.cbrt(random()) : radius * Math.sqrt(random());
        let angle = angle0;
        if (!spheroid && random() < 0.78) {
            const arm = Math.floor(random() * arms);
            // Schematic logarithmic arms at a 15-degree pitch, not fitted spirals.
            angle = arm * Math.PI * 2 / arms + Math.log(Math.max(radial / radius, 0.025))
                / Math.tan(THREE.MathUtils.degToRad(15)) + (random() - 0.5) * 0.5;
        }
        const thickness = spheroid ? 0.38 : 0.045;
        const x = radial * Math.cos(angle), z = radial * Math.sin(angle);
        const y = (random() - 0.5) * radius * thickness;
        positions.push(x, y, z);
        const warm = radial < radius * 0.2;
        const tint = warm ? [1, 0.78, 0.53] : [0.68, 0.82, 1];
        colors.push(...tint.map(channel => channel * (0.62 + random() * 0.38)));
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    const cloud = new THREE.Points(geometry, new THREE.PointsMaterial({ size: 1.5, sizeAttenuation: false,
        vertexColors: true, transparent: true, opacity: 0.48, depthWrite: false }));
    cloud.userData.pointSize = { max: 1.1, perPixel: 1 / 200 };
    const disk = new THREE.Mesh(new THREE.CircleGeometry(radius, 32), new THREE.MeshBasicMaterial({
        color, transparent: true, opacity: 0.18, side: THREE.DoubleSide, depthWrite: false
    }));
    disk.rotation.x = -Math.PI / 2;
    const galaxy = new THREE.Group();
    galaxy.add(disk, cloud);
    galaxy.rotation.order = 'ZYX';
    galaxy.rotation.set(THREE.MathUtils.degToRad(90 - inclination), 0,
        THREE.MathUtils.degToRad(positionAngle), 'ZYX');
    galaxy.userData.galaxyRadiusKpc = radius;
    return galaxy;
}

function equatorialPosition(raDeg, decDeg, distanceKpc) {
    const ra = raDeg * Math.PI / 180, dec = decDeg * Math.PI / 180;
    return new THREE.Vector3(distanceKpc * Math.cos(dec) * Math.cos(ra),
        distanceKpc * Math.sin(dec), distanceKpc * Math.cos(dec) * Math.sin(ra));
}

function labeledGalaxy({ name, ra, dec, distance, radius, seed, type = 'spiral', arms = 2,
    inclination = 0, positionAngle = 0, color }, index) {
    const spheroid = type === 'dwarf';
    const galaxy = spiralGalaxy({ radius, seed, arms, inclination, positionAngle, color,
        points: spheroid ? 120 : 800, spheroid });
    const shared = name === 'Milky Way' ? MILKY_WAY : name === 'Andromeda (M31)' ? ANDROMEDA : null;
    if (shared) {
        const old = galaxy.children.find(child => child.isPoints);
        galaxy.remove(old);
        old.geometry.dispose(); old.material.dispose();
        galaxy.add(galaxyCloud(shared, 1200, seed, `${name}-stars`, { maxSize: 1.1 }));
    }
    galaxy.name = name;
    galaxy.position.copy(equatorialPosition(ra, dec, distance));
    if (STAGE_LABELS[name]) {
        galaxy.userData.label = STAGE_LABELS[name];
        galaxy.userData.labelClass = 'major';
        galaxy.userData.labelLayout = 'orbit';
        galaxy.userData.labelPriority = index;
    }
    if (CALLOUTS[name]) galaxy.userData.labelOffset = CALLOUTS[name];
    galaxy.userData.catalogDistanceKpc = distance;
    galaxy.userData.catalogRaDeg = ra;
    galaxy.userData.catalogDecDeg = dec;
    return galaxy;
}

export function proximaCentauriDistanceScene(entry = {}) {
    const distance = PROXIMA_DISTANCE_M / KPC;
    const scene = new THREE.Group();
    const sun = new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8), new THREE.MeshBasicMaterial({ color: 0xffdc85 }));
    sun.name = 'Sun';
    sun.position.x = -distance / 2;
    sun.scale.setScalar(distance * 0.004);
    Object.assign(sun.userData, { label: 'Sun', outline: true, sphere: true, markerRadius: 5, markerPadding: 1 });
    const proxima = new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8), new THREE.MeshBasicMaterial({ color: 0xff7057 }));
    proxima.name = 'Proxima Centauri';
    proxima.position.x = distance / 2;
    proxima.scale.setScalar(distance * 0.003);
    Object.assign(proxima.userData, { label: 'Proxima', outline: true, sphere: true, markerRadius: 5, markerPadding: 1 });
    scene.add(sun, proxima);
    scene.userData.actualCenterSeparationKpc = distance;
    scene.userData.listedDistanceMeters = entry.value ?? 4e16;
    return scene;
}

// Heliocentric J2000 positions are calculated from catalog RA, Dec and distance.
// Distances/radii are rounded representative values; orientation is sky-frame,
// not a reconstructed dynamical model. No galaxy-size exaggeration is applied.
export const LOCAL_GROUP_GALAXIES = Object.freeze([
    { name: 'Milky Way', ra: 0, dec: 0, distance: 0, radius: MILKY_WAY.radius, seed: 0x3a11, type: 'spiral', arms: 4, inclination: 40, color: 0x9bbbe6 },
    { name: 'Andromeda (M31)', ra: 10.6847, dec: 41.269, distance: 783, radius: 23.3, seed: 0x3131, type: 'spiral', arms: 2, inclination: 77, positionAngle: 38, color: 0xa8bde3 },
    { name: 'Triangulum (M33)', ra: 23.4621, dec: 30.6602, distance: 809, radius: 9, seed: 0x3331, type: 'spiral', arms: 2, inclination: 56, positionAngle: 23, color: 0x8bbbe9 },
    { name: 'Large Magellanic Cloud', ra: 80.8942, dec: -69.7561, distance: 51, radius: 4.3, seed: 0x1a2c, type: 'spiral', arms: 1, inclination: 35, positionAngle: 170, color: 0xc8a7dc },
    { name: 'Small Magellanic Cloud', ra: 13.1867, dec: -72.8286, distance: 64, radius: 1.6, seed: 0x5a11, type: 'dwarf', color: 0xd4b8d8 },
    { name: 'Sagittarius Dwarf', ra: 283.8313, dec: -30.5453, distance: 26.5, radius: 1.2, seed: 0x501, type: 'dwarf', color: 0xc8a8da },
    { name: 'Fornax Dwarf', ra: 39.997, dec: -34.449, distance: 147, radius: 1.4, seed: 0x502, type: 'dwarf', color: 0xc8a8da },
    { name: 'Sculptor Dwarf', ra: 15.0392, dec: -33.7092, distance: 86, radius: 1.1, seed: 0x503, type: 'dwarf', color: 0xc8a8da },
    { name: 'Leo I', ra: 152.1171, dec: 12.3064, distance: 254, radius: 1.2, seed: 0x504, type: 'dwarf', color: 0xc8a8da },
    { name: 'M32', ra: 10.6742, dec: 40.8652, distance: 805, radius: 1.1, seed: 0x320, type: 'dwarf', color: 0xc8a8da },
    { name: 'M110 (NGC 205)', ra: 10.0919, dec: 41.6854, distance: 824, radius: 2.4, seed: 0x205, type: 'dwarf', color: 0xc8a8da },
    { name: 'NGC 147', ra: 8.3001, dec: 48.5088, distance: 676, radius: 1.8, seed: 0x147, type: 'dwarf', color: 0xc8a8da },
    { name: 'NGC 185', ra: 9.7416, dec: 48.3375, distance: 617, radius: 1.7, seed: 0x185, type: 'dwarf', color: 0xc8a8da },
    { name: 'NGC 6822', ra: 296.2358, dec: -14.7892, distance: 459, radius: 2.2, seed: 0x6822, type: 'dwarf', color: 0xd1a9c7 },
    { name: 'IC 1613', ra: 16.1992, dec: 2.1178, distance: 755, radius: 2.3, seed: 0x1613, type: 'dwarf', color: 0xd1a9c7 },
    { name: 'WLM', ra: 0.4929, dec: -15.4609, distance: 933, radius: 2.1, seed: 0x0a11, type: 'dwarf', color: 0xd1a9c7 }
]);

export function localGroupScene(entry = {}) {
    const scene = new THREE.Group();
    for (const [index, galaxy] of LOCAL_GROUP_GALAXIES.entries()) {
        if (galaxy.name === 'Milky Way') {
            const milkyWay = labeledGalaxy(galaxy, index);
            milkyWay.position.set(0, 0, 0);
            scene.add(milkyWay);
        } else scene.add(labeledGalaxy(galaxy, index));
    }
    const spanKpc = (entry.value ?? 1e23) / KPC;
    const boundary = new THREE.Group();
    boundary.name = 'Approximate Local Group span';
    const lineMaterial = new THREE.LineBasicMaterial({ color: 0x7795b8, transparent: true,
        opacity: 0.25, depthWrite: false });
    for (const axis of ['x', 'y', 'z']) {
        const vertices = [];
        for (let index = 0; index < 96; index++) {
            const angle = index / 96 * Math.PI * 2;
            const a = spanKpc / 2 * Math.cos(angle), b = spanKpc / 2 * Math.sin(angle);
            vertices.push(axis === 'x' ? new THREE.Vector3(0, a, b)
                : axis === 'y' ? new THREE.Vector3(a, 0, b) : new THREE.Vector3(a, b, 0));
        }
        boundary.add(new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(vertices), lineMaterial));
    }
    scene.add(boundary);
    scene.userData.positionBasis = 'Heliocentric J2000 equatorial coordinates converted to Cartesian kpc';
    return scene;
}

const localGroupNote = 'Sixteen Local Group galaxies positioned from rounded J2000 coordinates and heliocentric distances in McConnachie’s nearby-galaxy catalog, with the Milky Way at the origin. M31 is 783 kpc away and M33 is 809 kpc away. Galaxy radii and distances share one physical scale, without enlarged glyphs. The Milky Way uses the same diameter and stellar distribution as its standalone model. Individual stars, disk orientations and dwarf shapes are illustrative, not a dynamical/orbital solution or observed 3D structure. The three faint rings mark the listed approximate 10.6-million-light-year span, not a measured physical edge; membership of peripheral galaxies is uncertain.';

export const nearbySpaceModelMetadata = Object.freeze({
    'Proxima Centauri': Object.freeze({ id: 'proxima-centauri-distance-procedural', procedural: 'proxima-centauri-distance', geometry: 'mesh',
        presentation: Object.freeze({ reference_size: PROXIMA_DISTANCE_M / KPC,
            distance_bracket: Object.freeze({ bodies: ['Sun', 'Proxima Centauri'] }), layout_width_factor: 1.1,
            focus_scale_factor: 1.1, display_extent_factor: 1 }),
        basis_url: 'https://doi.org/10.3847/1538-3881/addabe', basis_label: 'A Demonstration of Interstellar Navigation Using New Horizons: Gaia DR3 parallax distance',
        note: `The Sun and Proxima Centauri are separated by 1.301971 pc (${(PROXIMA_DISTANCE_M / LY).toFixed(3)} light-years), using the reciprocal Gaia DR3 parallax quoted in the cited astrometric analysis. Their rendered marker spheres are enlarged to 0.8% and 0.6% of the separation respectively; the stars are not drawn at physical diameter. The ${((PROXIMA_DISTANCE_M / 4e16 - 1) * 100).toFixed(1)}% difference from the listed 4e16 m is the catalog value used for the diagram; separation is represented in the source-derived physical units. NASA overview: https://science.nasa.gov/asset/hubble/proxima-centauri/` }),
    'Local Group': Object.freeze({ id: 'local-group-procedural', procedural: 'local-group', geometry: 'mesh',
        presentation: Object.freeze({ reference_size: 1e23 / KPC, layout_width_factor: 1.15,
            focus_scale_factor: 1.15, display_extent_factor: 1 }),
        basis_url: 'https://doi.org/10.1088/0004-6256/144/1/4', basis_label: 'McConnachie (2012) nearby-galaxy catalog; NASA Local Group overview', note: localGroupNote })
});

export const cosmicScenes = Object.freeze({
    'proxima-centauri-distance': proximaCentauriDistanceScene,
    'local-group': localGroupScene
});
