// Procedural galaxies, in kiloparsecs. Structure parameters come from the
// cited literature; individual star positions are a random sample, not a
// catalog. Disks lie in the x-z plane (y is "galactic north").
import * as THREE from '../vendor/three/three.module.min.js';

export const KPC = 3.0856775814913673e19; // meters
const TAU = 2 * Math.PI;

function randomSource(seed) {
    return () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) + 0.5) / 4294967296;
}
function gaussian(random) {
    return Math.sqrt(-2 * Math.log(random())) * Math.cos(TAU * random());
}

// Milky Way: disk radius set by the listed 1e21 m diameter; bar half-length
// about 5 kpc at 27 degrees to the Sun-center line and four arms with about
// 12 degree pitch (Bland-Hawthorn & Gerhard 2016; Vallee 2017); exponential
// scale length 2.6 kpc; Sun at R0 = 8.18 kpc (GRAVITY Collaboration 2019).
export const MILKY_WAY = Object.freeze({ radius: 1e21 / KPC / 2, scaleLength: 2.6, barHalfLength: 5,
    barAngle: 27, arms: 4, majorArms: [0, 2], pitch: 12, armStart: 3.3, armWidth: 0.7, bulgeFraction: 0.2,
    barFraction: 0.7, sunRadius: 8.18 });
// Andromeda (M31): about 46.6 kpc across (D25), a prominent star-forming ring
// near 10 kpc, a larger bulge, and a 77 degree inclination.
export const ANDROMEDA = Object.freeze({ radius: 23.3, scaleLength: 5.3, barHalfLength: 2, barAngle: 0,
    arms: 2, pitch: 8, armStart: 5, armWidth: 0.9, bulgeFraction: 0.3, barFraction: 0.15, ring: 10, inclination: 77 });

export function galaxyPoints(parameters, count, seed) {
    const random = randomSource(seed), positions = [], colors = [];
    const { radius, scaleLength, barHalfLength, barAngle, arms, pitch, armStart, armWidth, bulgeFraction, ring,
        majorArms, barFraction = 0.7 } = parameters;
    const bar = THREE.MathUtils.degToRad(barAngle), cotPitch = 1 / Math.tan(THREE.MathUtils.degToRad(pitch));
    const push = (x, y, z, [r, g, b], brightness) => {
        if (Math.hypot(x, z) > radius) return false;
        positions.push(x, y, z);
        colors.push(r * brightness, g * brightness, b * brightness);
        return true;
    };
    while (positions.length < count * 3) {
        const choice = random();
        if (choice < bulgeFraction) {
            // Boxy bar plus a small spheroidal bulge: old, yellowish stars.
            const along = (random() + random() - 1) * barHalfLength, across = gaussian(random) * 0.7;
            const inBar = random() < barFraction;
            const x = inBar ? along * Math.cos(bar) - across * Math.sin(bar) : gaussian(random) * 0.9;
            const z = inBar ? along * Math.sin(bar) + across * Math.cos(bar) : gaussian(random) * 0.9;
            push(x, gaussian(random) * (inBar ? 0.35 : 0.6), z, [1, 0.82, 0.58], 0.9 + 0.3 * random());
            continue;
        }
        // Disk: radius from an exponential surface density (pdf ~ r e^(-r/h)).
        const r = -scaleLength * Math.log(random() * random());
        if (r > radius) continue;
        const height = gaussian(random) * 0.12;
        let angle, color, brightness;
        const armRoll = random();
        if (ring && armRoll < 0.22) {
            const ringRadius = ring + gaussian(random) * 0.8, ringAngle = TAU * random();
            push(ringRadius * Math.cos(ringAngle), height, ringRadius * Math.sin(ringAngle),
                random() < 0.12 ? [1, 0.5, 0.68] : [0.72, 0.82, 1], 1);
            continue;
        }
        if (armRoll < 0.55 && r > armStart * 0.8) {
            // Logarithmic arm: angle grows with ln(r) at the pitch angle.
            // Major arms (e.g. Scutum-Centaurus, Perseus) hold most arm stars.
            const arm = majorArms && random() < 0.72
                ? majorArms[Math.floor(random() * majorArms.length)] : Math.floor(random() * arms);
            // Arms broaden outward (roughly 0.5-1.5 kpc across).
            angle = bar + arm * TAU / arms + Math.log(r / armStart) * cotPitch + gaussian(random) * armWidth * (0.7 + r / radius) / r;
            const hii = random() < 0.06;
            color = hii ? [1, 0.5, 0.68] : [0.72, 0.82, 1];
            brightness = hii ? 1.2 : 0.8 + 0.4 * random();
        } else {
            angle = TAU * random();
            color = [0.92, 0.88, 0.82];
            brightness = 0.45 + 0.25 * random();
        }
        push(r * Math.cos(angle), height, r * Math.sin(angle), color, brightness);
    }
    return { positions, colors };
}

// Normal alpha blending keeps star colors (yellow bulge, blue arms, pink
// nebulae) where stars crowd; additive blending saturates them to flat white.
function galaxyCloud(parameters, count, seed, name, { brightness = 1, opacity = 0.5, maxSize = 1.6 } = {}) {
    const { positions, colors } = galaxyPoints(parameters, count, seed);
    for (let index = 0; index < colors.length; index++) colors[index] *= brightness;
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    const points = new THREE.Points(geometry, new THREE.PointsMaterial({ size: 1.3, sizeAttenuation: false,
        vertexColors: true, transparent: true, opacity, depthWrite: false }));
    points.name = name;
    points.userData.pointSize = { max: maxSize, perPixel: 1 / 160 };
    return points;
}

export function milkyWayScene() {
    const scene = new THREE.Group();
    scene.add(galaxyCloud(MILKY_WAY, 42000, 0x3a11, 'milky-way-stars'));
    // The Sun, 8.18 kpc from the center; its outline marks where we are.
    const sun = new THREE.Mesh(new THREE.SphereGeometry(1, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffe08a }));
    sun.scale.setScalar(695_700_000 / KPC);
    sun.position.set(0, 0, MILKY_WAY.sunRadius);
    Object.assign(sun.userData, { label: 'Sun', outline: true, sphere: true, markerRadius: 3, markerPadding: 0.5 });
    sun.name = 'Sun';
    scene.add(sun);
    return scene;
}

// Two galaxies at the listed center-to-center distance, as unit-radius point
// clouds inside nodes scaled by each galaxy's radius, so the shared
// distance-bracket code can treat them like spheres.
export function andromedaDistanceScene(entry = {}) {
    const distance = (entry.value ?? 2.37e22) / KPC;
    const scene = new THREE.Group();
    const unit = parameters => ({ ...parameters, radius: 1, scaleLength: parameters.scaleLength / parameters.radius,
        barHalfLength: parameters.barHalfLength / parameters.radius, armStart: parameters.armStart / parameters.radius,
        armWidth: parameters.armWidth / parameters.radius, ring: parameters.ring ? parameters.ring / parameters.radius : 0 });
    const milkyWay = new THREE.Group();
    milkyWay.name = 'Milky Way';
    const small = { opacity: 0.45, maxSize: 1.1 };
    milkyWay.add(galaxyCloud(unit(MILKY_WAY), 5000, 0x3a12, 'milky-way-stars', small));
    milkyWay.scale.setScalar(MILKY_WAY.radius);
    milkyWay.position.x = -distance / 2;
    // Disks start edge-on to the viewer (normal +y); inclination i needs 90 - i.
    milkyWay.rotation.x = THREE.MathUtils.degToRad(90 - 40);
    const andromeda = new THREE.Group();
    andromeda.name = 'Andromeda';
    andromeda.add(galaxyCloud(unit(ANDROMEDA), 6500, 0x3131, 'andromeda-stars', small));
    andromeda.scale.setScalar(ANDROMEDA.radius);
    andromeda.position.x = distance / 2;
    // Tilt first, then turn about the line of sight (position angle 38 degrees),
    // which leaves the inclination unchanged: matrix Rz * Rx, i.e. order ZYX.
    andromeda.rotation.set(THREE.MathUtils.degToRad(90 - ANDROMEDA.inclination), 0, THREE.MathUtils.degToRad(38), 'ZYX');
    scene.add(milkyWay, andromeda);
    return scene;
}

export const cosmicModelMetadata = Object.freeze({
    'Galaxy Diameter': Object.freeze({ id: 'milky-way-procedural', procedural: 'milky-way', geometry: 'mesh',
        presentation: Object.freeze({ reference_size: 2 * MILKY_WAY.radius, pitch: 58, layout_width_factor: 1,
            focus_scale_factor: 1.2, display_extent_factor: 1 }),
        basis_url: 'https://doi.org/10.1146/annurev-astro-081915-023441',
        basis_label: 'Structure: Bland-Hawthorn & Gerhard (2016)',
        note: 'The Milky Way drawn to scale from its measured structure: a central bar about 10 kpc long, four spiral arms winding out at about 12 degrees, a disk whose stars thin out exponentially, and the Sun 26,700 light-years (8.2 kpc) from the center. The disk is cut at the listed 100,000-light-year diameter. The stars are a random sample shaped by those parameters, not a map, and because we see the galaxy from inside, the exact arm layout is still debated.' }),
    'Andromeda Distance': Object.freeze({ id: 'andromeda-distance-procedural', procedural: 'andromeda-distance', geometry: 'mesh',
        presentation: Object.freeze({ reference_size: 2.37e22 / KPC, distance_bracket: Object.freeze({ bodies: ['Milky Way', 'Andromeda'] }),
            layout_width_factor: 1, focus_scale_factor: 1.1, display_extent_factor: 1 }),
        basis_url: 'https://en.wikipedia.org/wiki/Andromeda_Galaxy',
        basis_label: 'Andromeda: distance and size',
        note: 'The Milky Way and the Andromeda Galaxy at their center-to-center distance of 2.5 million light-years (765 kpc), with both galaxies drawn to the same scale: Andromeda is about 150,000 light-years across and tilted 77 degrees to our line of sight. Even the nearest large galaxy is about 25 Milky Way widths away. Star positions are illustrative samples.' })
});

export const cosmicScenes = Object.freeze({
    'milky-way': milkyWayScene,
    'andromeda-distance': andromedaDistanceScene
});
