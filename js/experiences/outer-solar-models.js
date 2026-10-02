// Outer-solar-system diagrams use AU as their scene unit. The particles and
// flow lines are visual samples, not object counts or a dynamical simulation.
import * as THREE from '../vendor/three/three.module.min.js';
import { screenLine } from './model-overlay-nodes.js?v=26a046c0b3';

export const OORT_CLOUD = Object.freeze({
    innerHillsMinAU: 2_000,
    innerHillsMaxAU: 20_000,
    outerMinAU: 20_000,
    outerMaxAU: 100_000,
    referenceSizeAU: 200_000
});

export const HELIOSPHERE = Object.freeze({
    terminationShockMinAU: 84,
    terminationShockMaxAU: 94,
    terminationShockDiagramAU: 90,
    heliopauseUpwindAU: 120,
    referenceSizeAU: 240
});

function seeded(seed) {
    return () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) + 0.5) / 4294967296;
}

function pointCloud(positions, { color, opacity, maxSize = 1.6 }) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    const points = new THREE.Points(geometry, new THREE.PointsMaterial({ color, size: 1.5,
        sizeAttenuation: false, transparent: true, opacity, depthWrite: false }));
    points.userData.pointSize = { max: maxSize, perPixel: 1 / 180 };
    points.userData.softPoints = true;
    return points;
}

function label(scene, text, position, offset, priority) {
    const anchor = new THREE.Object3D();
    anchor.position.set(...position);
    Object.assign(anchor.userData, { label: text, labelOffset: offset,
        labelLayout: 'orbit', labelPriority: priority });
    scene.add(anchor);
    return anchor;
}

function sunMarker(scene) {
    const sun = new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8),
        new THREE.MeshBasicMaterial({ color: 0xffd991 }));
    sun.name = 'Sun';
    sun.scale.setScalar(0.00465047); // Physical solar radius in AU.
    Object.assign(sun.userData, { outline: true, sphere: true, markerRadius: 3, markerPadding: 1 });
    scene.add(sun);
}

function lineLoop(axis, radius, material, segments = 128) {
    const positions = [];
    for (let index = 0; index < segments; index++) {
        const angle = 2 * Math.PI * index / segments;
        const a = radius * Math.cos(angle), b = radius * Math.sin(angle);
        positions.push(...(axis === 'x' ? [0, a, b] : axis === 'y' ? [a, 0, b] : [a, b, 0]));
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    const loop = new THREE.LineLoop(geometry, material);
    if (material.isLineDashedMaterial) loop.computeLineDistances();
    return loop;
}

function sphericalDirection(random) {
    const z = random() * 2 - 1, angle = random() * 2 * Math.PI;
    const planar = Math.sqrt(1 - z * z);
    return [planar * Math.cos(angle), z, planar * Math.sin(angle)];
}

// Two smooth, unclustered samples suggest a flattened inner Hills component
// and a much broader, approximately isotropic outer reservoir.
export function oortCloudScene() {
    const scene = new THREE.Group();
    scene.name = 'Oort Cloud schematic';
    const random = seeded(0x00a47c10);
    const hills = [], outer = [];
    for (let index = 0; index < 7_000; index++) {
        const radius = OORT_CLOUD.innerHillsMinAU
            + (OORT_CLOUD.innerHillsMaxAU - OORT_CLOUD.innerHillsMinAU) * Math.sqrt(random());
        const angle = random() * 2 * Math.PI;
        const vertical = (random() * 2 - 1) * 0.13 * radius;
        hills.push(radius * Math.cos(angle), vertical, radius * Math.sin(angle));
    }
    for (let index = 0; index < 16_000; index++) {
        const direction = sphericalDirection(random);
        const radius = OORT_CLOUD.outerMinAU
            + (OORT_CLOUD.outerMaxAU - OORT_CLOUD.outerMinAU) * Math.cbrt(random());
        outer.push(direction[0] * radius, direction[1] * radius, direction[2] * radius);
    }
    const hillsCloud = pointCloud(hills, { color: 0x8ba9c5, opacity: 0.33, maxSize: 1.25 });
    hillsCloud.name = 'Flattened inner Hills-cloud sample';
    hillsCloud.userData.radialRangeAU = [OORT_CLOUD.innerHillsMinAU, OORT_CLOUD.innerHillsMaxAU];
    const outerCloud = pointCloud(outer, { color: 0xc1d5e8, opacity: 0.48, maxSize: 1.8 });
    outerCloud.name = 'Diffuse outer-cloud sample';
    outerCloud.userData.radialRangeAU = [OORT_CLOUD.outerMinAU, OORT_CLOUD.outerMaxAU];
    scene.add(hillsCloud, outerCloud);

    // These faint great circles are a scale cue only, not a shell of detected gas.
    const edgeMaterial = new THREE.LineDashedMaterial({ color: 0x9db4ca, transparent: true,
        opacity: 0.045, depthWrite: false, dashSize: 2_000, gapSize: 4_000 });
    const edge = new THREE.Group();
    edge.name = 'Contextual 100000 AU radius';
    edge.userData.contextualBoundary = true;
    edge.userData.notObservedGasShell = true;
    for (const axis of ['x', 'y', 'z']) edge.add(lineLoop(axis, OORT_CLOUD.outerMaxAU, edgeMaterial));
    scene.add(edge);
    sunMarker(scene);
    label(scene, 'Sun', [0, 0, 0], { x: -20, y: -35 }, 0);
    label(scene, 'Hills cloud', [14_000, 0, 0], { x: 90, y: 40 }, 1);
    label(scene, 'Outer cloud', [-65_000, 30_000, 0], { x: -25, y: -35 }, 2);
    scene.userData.sceneUnit = 'AU';
    scene.userData.representativeOuterRadiusAU = OORT_CLOUD.outerMaxAU;
    return scene;
}

function ellipsoid(radiusX, radiusY, radiusZ, color, opacity, name) {
    // Only a nose-side cutaway sector: the unmeasured downstream shape is open.
    const mesh = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 32, Math.PI / 2, Math.PI),
        new THREE.MeshBasicMaterial({ color, transparent: true, opacity, side: THREE.DoubleSide,
            depthWrite: false }));
    mesh.scale.set(radiusX, radiusY, radiusZ);
    mesh.name = name;
    mesh.userData.partialBoundary = true;
    return mesh;
}

function streamline(points, material, radius = 0.42) {
    const curve = new THREE.CatmullRomCurve3(points);
    return new THREE.Mesh(new THREE.TubeGeometry(curve, 48, radius, 4, false), material);
}

// The +X nose is the upwind direction. Cross-sections are compressed to keep
// the shock/sheath legible; tail tracers are explicitly illustrative only.
export function heliosphereScene() {
    const scene = new THREE.Group();
    scene.name = 'Heliosphere schematic';
    const terminationShock = ellipsoid(HELIOSPHERE.terminationShockDiagramAU, 64, 64,
        0xe4a15c, 0.045, 'Termination shock ~90 AU');
    terminationShock.userData.radiusAU = HELIOSPHERE.terminationShockDiagramAU;
    terminationShock.userData.observedVoyagerCrossingsAU = [
        HELIOSPHERE.terminationShockMinAU, HELIOSPHERE.terminationShockMaxAU
    ];
    const heliopause = ellipsoid(HELIOSPHERE.heliopauseUpwindAU, 82, 82,
        0x5797bd, 0.035, 'Heliopause ~120 AU upwind');
    heliopause.userData.upwindExtentAU = HELIOSPHERE.heliopauseUpwindAU;
    heliopause.userData.shapeIsSchematic = true;
    scene.add(heliopause, terminationShock);

    const windMaterial = new THREE.MeshBasicMaterial({ color: 0xf0c17e, transparent: true,
        opacity: 0.36, depthWrite: false });
    for (let index = 0; index < 12; index++) {
        // Near-radial bulk solar wind, sampled over solid angle. These are
        // not spiral magnetic-field lines, and stop inside the drawn shock.
        const cosine = 1 - 2 * (index + 0.5) / 12;
        const angle = index * Math.PI * (3 - Math.sqrt(5));
        const planar = Math.sqrt(1 - cosine * cosine);
        const endpoint = new THREE.Vector3(planar * Math.cos(angle) * 90,
            cosine * 64, planar * Math.sin(angle) * 64).multiplyScalar(0.96);
        const points = [endpoint.clone().multiplyScalar(0.12), endpoint.clone()];
        const flow = streamline(points, windMaterial, 0.32);
        flow.name = 'Solar-wind streamline';
        scene.add(flow);
        const arrow = new THREE.Mesh(new THREE.ConeGeometry(1.25, 3.5, 6), windMaterial);
        arrow.position.copy(endpoint);
        arrow.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), endpoint.clone().normalize());
        scene.add(arrow);
    }

    const random = seeded(0x1b3e5eed), sheathParticles = [];
    for (let index = 0; index < 12_000; index++) {
        const direction = sphericalDirection(random);
        if (direction[0] < 0) continue; // The downstream density is not depicted.
        let radius = 0.79 + random() * 0.2;
        let x = direction[0] * HELIOSPHERE.heliopauseUpwindAU * radius;
        let y = direction[1] * 82 * radius, z = direction[2] * 82 * radius;
        const shockNorm = Math.hypot(x / HELIOSPHERE.terminationShockDiagramAU, y / 64, z / 64);
        if (shockNorm < 1) {
            const scale = 1.015 / shockNorm;
            x *= scale; y *= scale; z *= scale;
        }
        sheathParticles.push(x, y, z);
    }
    const sheath = pointCloud(sheathParticles, { color: 0x86c5df, opacity: 0.3, maxSize: 1.3 });
    sheath.name = 'Heliosheath particle tracers';
    scene.add(sheath);

    const tailMaterial = new THREE.MeshBasicMaterial({ color: 0x83b9d2, transparent: true,
        opacity: 0.11, depthWrite: false });
    const tail = new THREE.Group();
    tail.name = 'Illustrative, truncated heliotail tracers';
    tail.userData.notToScale = true;
    tail.userData.notPhysicalLength = true;
    for (let lobe = 0; lobe < 4; lobe++) {
        const angle = Math.PI / 4 + lobe * Math.PI / 2;
        const points = Array.from({ length: 9 }, (_, index) => {
            const t = index / 8, x = -38 - 78 * t;
            const r = 8 + 32 * t;
            return new THREE.Vector3(x, r * Math.cos(angle), r * Math.sin(angle));
        });
        tail.add(streamline(points, tailMaterial, 0.35));
    }
    scene.add(tail);
    sunMarker(scene);
    label(scene, 'Sun', [0, 0, 0], { x: -20, y: -35 }, 1);
    // A radius ruler, not a declaration of the unknowable downstream extent.
    const ruler = new THREE.Group();
    ruler.name = 'Rounded heliopause radial-distance cue';
    ruler.add(screenLine('x', 120, new THREE.Vector3(60, -97, 0), 0x9db9cc));
    for (const x of [0, 90, 120])
        ruler.add(screenLine('y', 4, new THREE.Vector3(x, -97, 0), 0x9db9cc));
    scene.add(ruler);
    label(scene, 'Shock ~90 AU', [90, 0, 0], { x: -5, y: -75 }, 2);
    label(scene, 'Heliopause ~120 AU', [120, -97, 0], { x: -30, y: 30 }, 3);
    const upwind = new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0),
        new THREE.Vector3(70, 30, 0), 40, 0x9db9cc, 4, 2);
    scene.add(upwind);
    const upwindLabel = label(scene, 'Upwind', [90, 30, 0], { x: 45, y: -40 }, 0);
    upwindLabel.userData.labelAxis = { axis: 'x', length: 40, minPixelLength: 10 };
    scene.userData.sceneUnit = 'AU';
    scene.userData.upwindAxis = '+X';
    scene.userData.tailIsIllustrative = true;
    return scene;
}

const oortNote = 'A schematic of the hypothesized comet reservoir: a flattened inner Hills-cloud component from 2,000 to 20,000 AU and a diffuse outer component from 20,000 to 100,000 AU. NASA gives an uncertain outer edge of 10,000–100,000 AU; the upper estimate sets this diagram’s 200,000 AU diameter. The transition between components is illustrative, not a measured boundary. Points are visual samples, not individual cataloged comets or a population-density map. The faint great circles are scale guides, not an observed gas shell; the Sun’s ring is enlarged for visibility. Geometry references: NASA Oort Cloud facts and the NASA technical review https://ntrs.nasa.gov/api/citations/19910013647/downloads/19910013647.pdf.';

const heliosphereNote = 'A nose-side cutaway of the solar-wind cavity, with upwind on +X. Voyager 1 and 2 crossed the termination shock at 94 and 84 AU; the ruler shows rounded 90 and 120 AU shock/heliopause radii. The listed 240 AU is twice the radial scale, not a measured full-tail length. Boundary sectors are schematic, leaving the uncertain downstream shape open. NASA’s IBEX observations suggest tail structure, but global-shape models disagree; four faint, short tail tracers are illustrative, not a scaled estimate of its length. Particle points are visual tracers, not a count; the Sun’s ring is enlarged. Tail reference: https://www.nasa.gov/news-release/nasa-satellite-provides-first-view-of-the-solar-systems-tail/.';

export const outerSolarModelMetadata = Object.freeze({
    'Oort Cloud': Object.freeze({ id: 'oort-cloud-schematic', procedural: 'oort-cloud', geometry: 'mesh',
        presentation: Object.freeze({ reference_size: OORT_CLOUD.referenceSizeAU,
            pitch: 18, layout_width_factor: 1.05, focus_scale_factor: 1.15, display_extent_factor: 1 }),
        basis_url: 'https://science.nasa.gov/solar-system/oort-cloud/facts/',
        basis_label: 'NASA Oort Cloud facts', note: oortNote }),
    'Heliosphere': Object.freeze({ id: 'heliosphere-schematic', procedural: 'heliosphere', geometry: 'mesh',
        presentation: Object.freeze({ reference_size: HELIOSPHERE.referenceSizeAU,
            pitch: 12, yaw: 15, layout_width_factor: 1.05, focus_scale_factor: 1.15, display_extent_factor: 1 }),
        basis_url: 'https://science.nasa.gov/mission/voyager/interstellar-mission/',
        basis_label: 'Voyager boundary crossings; NASA IBEX context', note: heliosphereNote })
});

export const outerSolarScenes = Object.freeze({
    'oort-cloud': oortCloudScene,
    heliosphere: heliosphereScene
});
