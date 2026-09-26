// Procedural Length models and model decorations. Imported by models.js; the
// relative three.js import resolves to the same module as the page's import map
// and also works under Node for tests.
import * as THREE from '../vendor/three/three.module.min.js';

// Overlay conventions read by ModelStage.finish():
//   userData.screenLine = { axis: 'x' | 'y' | 'z', length }  box drawn at a constant pixel width
//   userData.label = text, userData.labelClass = extra CSS class  upright SVG text at the node
//   userData.outline = true (with userData.sphere = true)  thin SVG circle around a unit sphere
//   userData.pointSize = { max, perPixel }  Points size follows the drawn model size
export const SCREEN_LINE_PX = 1.4;
const lineMaterials = new Map();
const unitBox = () => (unitBox.geometry ||= new THREE.BoxGeometry(1, 1, 1));
export function screenLine(axis, length, position, color = 0xffffff) {
    if (!lineMaterials.has(color)) lineMaterials.set(color, new THREE.MeshBasicMaterial({ color }));
    const mesh = new THREE.Mesh(unitBox(), lineMaterials.get(color));
    mesh.position.copy(position);
    mesh.userData.screenLine = { axis, length };
    mesh.scale.set(axis === 'x' ? length : 1e-6, axis === 'y' ? length : 1e-6, axis === 'z' ? length : 1e-6);
    return mesh;
}
function anchor(label, position, labelClass) {
    const node = new THREE.Object3D();
    node.position.copy(position);
    node.userData.label = label;
    if (labelClass) node.userData.labelClass = labelClass;
    return node;
}

// Distance diagrams (Earth-Moon, AU) get a U-shaped bracket below the two
// bodies. Distances are center to center, so each vertical line drops from the
// bottom of its body's center; the horizontal line joins their lower ends. The
// bracket is part of the model and rotates with it.
export const BRACKET_DROP = 0.1; // below the larger body, as a fraction of the center distance
export function addDistanceBracket(scene, config) {
    scene.updateMatrixWorld(true);
    const bodies = config.bodies.map(name => {
        const node = scene.getObjectByName(name);
        if (!node) return null;
        Object.assign(node.userData, { label: name, outline: true, sphere: true });
        return { x: node.getWorldPosition(new THREE.Vector3()).x, radius: node.matrixWorld.getMaxScaleOnAxis() };
    });
    if (bodies.length !== 2 || bodies.some(body => !body)) return;
    const [left, right] = bodies[0].x <= bodies[1].x ? bodies : [bodies[1], bodies[0]];
    const bottom = -(Math.max(left.radius, right.radius) + BRACKET_DROP * (right.x - left.x));
    const bracket = new THREE.Group();
    bracket.name = 'distance-bracket';
    for (const body of [left, right])
        bracket.add(screenLine('y', -body.radius - bottom, new THREE.Vector3(body.x, (bottom - body.radius) / 2, 0)));
    bracket.add(screenLine('x', right.x - left.x, new THREE.Vector3((left.x + right.x) / 2, bottom, 0)));
    scene.add(bracket);
}

// Enclosed probability of hydrogen's 1s state within r Bohr radii is
// 1 - e^(-2r)(1 + 2r + 2r^2); 95% is reached at r = 3.148.
export const HYDROGEN_95_RADIUS = 3.1479;
// Pluto's orbit spans about 80 au, the dataset's Solar System diameter.
const AU = 149_597_870_700;

export const proceduralLength = {
    'Hydrogen Atom': { id: 'hydrogen-1s', procedural: 'hydrogen-1s', geometry: 'mesh',
        presentation: { reference_size: 1, layout_width_factor: 2 * HYDROGEN_95_RADIUS,
            focus_scale_factor: 2 * HYDROGEN_95_RADIUS, display_extent_factor: 2 * HYDROGEN_95_RADIUS },
        basis_url: 'https://ocw.mit.edu/courses/5-111-principles-of-chemical-science-fall-2008/8a0da0346f1d611fbbd5c31a54865c2d_lecnotes06.pdf',
        note: 'A sample of hydrogen’s 1s electron probability cloud. The listed 53 pm is the Bohr radius, the most probable electron distance, marked by the line from the nucleus; it is a radius, not a diameter. The faint sphere at 3.15 Bohr radii encloses 95% of the probability, and the dots stop there, so the whole picture is about six times wider than the listed value.' },
    'Water Molecule': { id: 'nist-water-molecule', procedural: 'molecule', molecule: 'water',
        geometry: 'mesh', presentation: { reference_size: 2.75 },
        source: 'https://cccbdb.nist.gov/expgeom2x.asp?casno=7732185',
        link_label: 'Model geometry',
        note: 'Gas-phase H2O with oxygen below two hydrogens. NIST gives O–H center distances of 0.958 Å and a 104.4776° H–O–H angle. The listed 2.75 Å is a representative molecular diameter, not an O–H bond length; ball radii and bond rods are illustrative.' },
    'Glucose Molecule': { id: 'pubchem-alpha-d-glucose', procedural: 'molecule', molecule: 'glucose',
        geometry: 'mesh', presentation: { reference_size: 10,
            pre_rotation: { x: 60, y: -15, z: -8 } },
        source: 'https://pubchem.ncbi.nlm.nih.gov/compound/79025',
        link_label: '3D conformer',
        note: 'Alpha-D-glucopyranose, shown as PubChem CID 79025’s 3D conformer. Its six-membered pyranose ring has a chair-like pucker; atom centers and bonds come from the conformer. The listed 1 nm is a rough molecular envelope, not a bond length; ball radii are illustrative.' },
    'Human Hair': { id: 'hair-fiber', procedural: 'hair-fiber', geometry: 'mesh',
        presentation: { measure_axis: 'x', layout_width_factor: 1.1, focus_scale_factor: 1.5, roll: 6 },
        basis_url: 'https://wellcomecollection.org/works/wxgqyf66',
        basis_label: 'Cuticle reference: Wellcome Collection',
        note: 'A scalp hair shaft modeled on electron micrographs: overlapping cuticle scales about 8 micrometers tall, with irregular free edges pointing toward the tip, around a slightly oval shaft. Its diameter is calibrated to the listed 100 micrometers; the shaft is cropped, and its color and luster are those of medium-brown hair rather than a false-colored micrograph.' },
    'Visible Light Wavelength': { id: 'light-wave', procedural: 'light-wave', geometry: 'mesh',
        presentation: { reference_size: 1, layout_width_factor: 2.3, focus_scale_factor: 2.3,
            display_extent_factor: 2.3, yaw: -32, pitch: 14 },
        basis_url: 'https://en.wikipedia.org/wiki/Electromagnetic_radiation',
        basis_label: 'Wave basis: electromagnetic radiation',
        note: 'A schematic plane light wave, two cycles long, traveling left to right. The crest-to-crest distance is calibrated to the listed 500 nm of green light. Field strengths are not lengths, so the wave heights are arbitrary; by convention the electric field is drawn red and the magnetic field blue, oscillating at right angles to each other and to the direction of travel.' },
    'Solar System': { id: 'solar-system-today', procedural: 'solar-system', geometry: 'mesh',
        presentation: { reference_size: 1.2e13 / AU, pitch: 62, layout_width_factor: 1.05 },
        basis_url: 'https://ssd.jpl.nasa.gov/planets/approx_pos.html',
        basis_label: 'Orbits: JPL approximate planetary positions',
        note: 'The Sun, eight planets and Pluto at their positions for today, computed from JPL’s approximate orbital elements, with each orbit drawn to the same scale. Planet sizes are true to scale too, so every body is far smaller than a pixel; the faint circles only mark where they are. The listed 80 au is roughly the span of Pluto’s orbit (Neptune’s is 60 au).' }
};

export function moleculeScene(data) {
    const scene = new THREE.Group();
    const colors = { C: 0x424950, O: 0xd8433e, H: 0xf7f9fc };
    const radii = { C: 0.29, O: 0.27, H: 0.18 };
    const sphere = new THREE.SphereGeometry(1, 20, 14);
    const rod = new THREE.CylinderGeometry(1, 1, 1, 10);
    const materials = Object.fromEntries(Object.entries(colors).map(([element, color]) =>
        [element, new THREE.MeshStandardMaterial({ color, roughness: 0.65, metalness: 0 })]));
    const rodMaterial = new THREE.MeshStandardMaterial({ color: 0x8a9198, roughness: 0.82 });
    const positions = data.atoms.map(atom => new THREE.Vector3(...atom.position));
    data.atoms.forEach((atom, index) => {
        const ball = new THREE.Mesh(sphere, materials[atom.element]);
        ball.position.copy(positions[index]);
        ball.scale.setScalar(radii[atom.element]);
        scene.add(ball);
    });
    for (const [a, b] of data.bonds) {
        const direction = positions[b].clone().sub(positions[a]);
        const bond = new THREE.Mesh(rod, rodMaterial);
        bond.position.copy(positions[a]).add(positions[b]).multiplyScalar(0.5);
        bond.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.clone().normalize());
        bond.scale.set(0.065, direction.length(), 0.065);
        scene.add(bond);
    }
    return scene;
}

function seeded(seed) {
    return () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) + 0.5) / 4294967296;
}

// A hair shaft one unit across (x), cropped to 2.4 units tall. Cuticle scales
// overlap like roof tiles: each rises gently toward its free upper edge, then
// the surface steps back down to the next scale. Edges wander around the shaft.
function hairFiber() {
    const random = seeded(0x5eed1234);
    const radius = 0.5, length = 2, radial = 160, rows = 560;
    const step = 0.028, oval = 0.045;
    // Scale heights vary (about 5-10 micrometers on a 100 micrometer hair), and
    // each free edge meanders around the shaft with a jagged, torn look.
    const edges = [];
    for (let base = -0.12; base < length + 0.2; base += 0.055 + random() * 0.045)
        edges.push({ base, waves: [[1 + Math.floor(random() * 2), 0.018 + random() * 0.02],
            [2 + Math.floor(random() * 4), 0.006 + random() * 0.012],
            [7 + Math.floor(random() * 8), 0.002 + random() * 0.004],
            [23 + Math.floor(random() * 20), 0.0008 + random() * 0.0014]].map(([n, a]) => [n, a, random() * 2 * Math.PI]) });
    const bands = edges.length;
    // Per column, edge heights are forced upward so neighboring edges never cross.
    const edgeColumns = Array.from({ length: radial + 1 }, (_, column) => {
        const angle = 2 * Math.PI * column / radial;
        let previous = -Infinity;
        return edges.map(({ base, waves }) => (previous = Math.max(previous + 0.018,
            waves.reduce((y, [n, a, phase]) => y + a * Math.sin(n * angle + phase), base))));
    });
    const positions = [], colors = [], uvs = [], indices = [];
    const base = new THREE.Color(0x7a4a2c), shade = new THREE.Color();
    for (let row = 0; row <= rows; row++) {
        const s = length * row / rows;
        for (let column = 0; column <= radial; column++) {
            const angle = 2 * Math.PI * column / radial;
            const heights = edgeColumns[column];
            let band = 0;
            while (band < bands - 2 && heights[band + 1] <= s) band++;
            const t = THREE.MathUtils.clamp((s - heights[band]) / (heights[band + 1] - heights[band]), 0, 1);
            // Flat plate with a raised lip at its free (upper) edge, then a step down.
            const lip = t > 0.88 ? (t - 0.88) / 0.12 : 0;
            const r = radius * (1 + step * (0.25 + 0.55 * t + 0.35 * lip * lip) + 0.0012 * Math.sin(angle * 41 + s * 7));
            positions.push(r * (1 + oval) * Math.cos(angle), s - length / 2, r * (1 - oval) * Math.sin(angle));
            // The overlapping edge shades the lower part of the next scale.
            shade.copy(base).multiplyScalar(0.72 + 0.3 * Math.pow(t, 0.45) + 0.05 * Math.sin(s * 3.1 + band));
            colors.push(shade.r, shade.g, shade.b);
            uvs.push(column / radial, row / rows);
        }
    }
    for (let row = 0; row < rows; row++)
        for (let column = 0; column < radial; column++) {
            const a = row * (radial + 1) + column, b = a + radial + 1;
            indices.push(a, a + 1, b, a + 1, b + 1, b);
        }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
    geometry.setIndex(indices);
    geometry.computeVertexNormals();
    const cuticle = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.4, metalness: 0 });
    cuticle.userData.environment = 0.55; // keratin has a soft sheen
    const scene = new THREE.Group();
    scene.add(new THREE.Mesh(geometry, cuticle));
    // Cut end: cortex with a darker medulla core.
    const cap = new THREE.Mesh(new THREE.CircleGeometry(radius * 1.005, radial),
        new THREE.MeshStandardMaterial({ color: 0x5c3822, roughness: 0.7 }));
    cap.rotation.x = -Math.PI / 2;
    cap.scale.set(1 + oval, 1 - oval, 1);
    cap.position.y = length / 2;
    const medulla = new THREE.Mesh(new THREE.CircleGeometry(radius * 0.16, 48),
        new THREE.MeshStandardMaterial({ color: 0x3a261a, roughness: 0.9 }));
    medulla.rotation.x = -Math.PI / 2;
    medulla.position.y = length / 2 + 0.002;
    scene.add(cap, medulla);
    return scene;
}

function arrow(from, to, radius, material) {
    const direction = to.clone().sub(from), length = direction.length();
    const group = new THREE.Group();
    if (length < 1e-6) return group;
    const head = Math.min(length * 0.45, radius * 7);
    const shaft = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, length - head, 8), material);
    shaft.position.y = (length - head) / 2;
    const cone = new THREE.Mesh(new THREE.ConeGeometry(radius * 2.6, head, 12), material);
    cone.position.y = length - head / 2;
    group.add(shaft, cone);
    group.position.copy(from);
    group.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
    return group;
}

// Two wavelengths along +X (one model unit is one wavelength): electric field
// in Y (red), magnetic field in Z (blue), with field-vector arrows, an axis
// triad at the origin, the travel direction, and a one-wavelength bracket.
function lightWave() {
    const scene = new THREE.Group();
    const cycles = 2, amplitude = 0.3, samples = 200, start = -cycles / 2;
    const curve = axis => new THREE.CatmullRomCurve3(Array.from({ length: samples + 1 }, (_, index) => {
        const x = cycles * index / samples, wave = amplitude * Math.sin(2 * Math.PI * x);
        return new THREE.Vector3(start + x, axis === 'y' ? wave : 0, axis === 'z' ? wave : 0);
    }));
    const electric = new THREE.MeshStandardMaterial({ color: 0xe0443a, emissive: 0x7a1510, emissiveIntensity: 0.5, roughness: 0.5 });
    const magnetic = new THREE.MeshStandardMaterial({ color: 0x3a7be0, emissive: 0x10307a, emissiveIntensity: 0.5, roughness: 0.5 });
    const neutral = new THREE.MeshStandardMaterial({ color: 0x59636e, roughness: 0.7 });
    scene.add(new THREE.Mesh(new THREE.TubeGeometry(curve('y'), 400, 0.012, 10), electric));
    scene.add(new THREE.Mesh(new THREE.TubeGeometry(curve('z'), 400, 0.012, 10), magnetic));
    const fieldArrows = (axis, material) => {
        const faded = material.clone();
        faded.transparent = true;
        faded.opacity = 0.55;
        for (let index = 1; index < cycles * 16; index++) {
            const x = index / 16, value = amplitude * Math.sin(2 * Math.PI * x);
            if (Math.abs(value) < 0.05) continue;
            const tip = new THREE.Vector3(start + x, axis === 'y' ? value : 0, axis === 'z' ? value : 0);
            scene.add(arrow(new THREE.Vector3(start + x, 0, 0), tip, 0.0035, faded));
        }
    };
    fieldArrows('y', electric);
    fieldArrows('z', magnetic);
    // Propagation axis, extending past the wave to an arrowhead.
    const end = start + cycles + 0.18;
    scene.add(arrow(new THREE.Vector3(start - 0.04, 0, 0), new THREE.Vector3(end, 0, 0), 0.006, neutral));
    // Axis triad at the origin: E up, B toward the viewer.
    scene.add(arrow(new THREE.Vector3(start - 0.04, 0, 0), new THREE.Vector3(start - 0.04, amplitude + 0.12, 0), 0.006, electric));
    scene.add(arrow(new THREE.Vector3(start - 0.04, 0, 0), new THREE.Vector3(start - 0.04, 0, amplitude + 0.12), 0.006, magnetic));
    scene.add(anchor('E', new THREE.Vector3(start - 0.04, amplitude + 0.2, 0), 'is-electric'));
    scene.add(anchor('B', new THREE.Vector3(start - 0.04, 0, amplitude + 0.2), 'is-magnetic'));
    scene.add(anchor('Direction of travel', new THREE.Vector3(end - 0.05, -0.1, 0)));
    scene.add(anchor('Electric field', new THREE.Vector3(start + 1.25, amplitude + 0.07, 0), 'is-electric'));
    scene.add(anchor('Magnetic field', new THREE.Vector3(start + 0.75, -0.07, amplitude + 0.05), 'is-magnetic'));
    // One wavelength, crest to crest, above the first two electric crests.
    const bracketY = amplitude + 0.2, from = start + 0.25, to = start + 1.25, ink = 0x2f3a45;
    scene.add(screenLine('x', to - from, new THREE.Vector3((from + to) / 2, bracketY, 0), ink));
    for (const x of [from, to])
        scene.add(screenLine('y', 0.14, new THREE.Vector3(x, bracketY - 0.05, 0), ink));
    scene.add(anchor('Wavelength λ = 500 nm', new THREE.Vector3((from + to) / 2, bracketY + 0.1, 0)));
    return scene;
}

// Hydrogen 1s: radius r (Bohr radii) follows Gamma(k=3, rate=2); dots stop at
// the 95% sphere. A line marks the Bohr radius, which is the listed value.
function hydrogen1s() {
    const scene = new THREE.Group();
    const random = seeded(0x1234abcd);
    const positions = [];
    while (positions.length < 3 * 9000) {
        const radius = -Math.log(random() * random() * random()) / 2;
        if (radius > HYDROGEN_95_RADIUS) continue;
        const z = 2 * random() - 1, angle = 2 * Math.PI * random();
        const circle = Math.sqrt(1 - z * z);
        positions.push(radius * circle * Math.cos(angle), radius * circle * Math.sin(angle), radius * z);
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    const cloud = new THREE.Points(geometry, new THREE.PointsMaterial({
        color: 0x2675ae, size: 1.6, sizeAttenuation: false, transparent: true, opacity: 0.3, depthWrite: false }));
    cloud.userData.pointSize = { max: 1.7, perPixel: 1 / 45 };
    const boundary = new THREE.Mesh(new THREE.SphereGeometry(HYDROGEN_95_RADIUS, 48, 32),
        new THREE.MeshBasicMaterial({ color: 0x2675ae, transparent: true, opacity: 0.05, depthWrite: false }));
    const ink = 0x2f3a45;
    scene.add(boundary, cloud, screenLine('x', 1, new THREE.Vector3(0.5, 0, 0), ink),
        screenLine('y', 0.18, new THREE.Vector3(1, 0, 0), ink),
        anchor('Bohr radius (listed size)', new THREE.Vector3(0.5, 0.16, 0)),
        anchor('95% boundary', new THREE.Vector3(0, HYDROGEN_95_RADIUS + 0.12, 0)));
    return scene;
}

// JPL "Approximate Positions of the Planets", Table 1 (valid 1800-2050):
// a (au), e, I, L, long. perihelion, long. node (deg) at J2000 and per century.
const PLANETS = [
    ['Mercury', 2_439_700, 0x9a9590, [0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628, 48.33076593], [0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081]],
    ['Venus', 6_051_800, 0xe3c58f, [0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255], [0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329, -0.27769418]],
    ['Earth', 6_371_000, 0x4a7fc1, [1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0], [0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0]],
    ['Mars', 3_389_500, 0xc1603a, [1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891], [0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343]],
    ['Jupiter', 69_911_000, 0xd2b48c, [5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909], [-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106]],
    ['Saturn', 58_232_000, 0xe6d3a0, [9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448], [-0.00125060, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794]],
    ['Uranus', 25_362_000, 0x9fd8e0, [19.18916464, 0.04725744, 0.77263783, 313.23810451, 170.95427630, 74.01692503], [-0.00196176, -0.00004397, -0.00242939, 428.48202785, 0.40805281, 0.04240589]],
    ['Neptune', 24_622_000, 0x4b70dd, [30.06992276, 0.00859048, 1.77004347, -55.12002969, 44.96476227, 131.78422574], [0.00026291, 0.00005105, 0.00035372, 218.45945325, -0.32241464, -0.00508664]],
    ['Pluto', 1_188_300, 0xc9b8a4, [39.48211675, 0.24882730, 17.14001206, 238.92903833, 224.06891629, 110.30393684], [-0.00031596, 0.00005170, 0.00004818, 145.20780515, -0.04062942, -0.01183482]]
];
const radians = THREE.MathUtils.degToRad;
function orbitalElements(elements, rates, centuries) {
    const [a, e, inclination, meanLongitude, perihelion, node] = elements.map((value, index) => value + rates[index] * centuries);
    return { a, e, inclination: radians(inclination), node: radians(node),
        argument: radians(perihelion - node), meanAnomaly: radians(meanLongitude - perihelion) };
}
// Heliocentric ecliptic (J2000) coordinates in au for an eccentric anomaly.
function orbitPoint({ a, e, inclination, node, argument }, eccentricAnomaly) {
    const x = a * (Math.cos(eccentricAnomaly) - e), y = a * Math.sqrt(1 - e * e) * Math.sin(eccentricAnomaly);
    const cw = Math.cos(argument), sw = Math.sin(argument), cn = Math.cos(node), sn = Math.sin(node);
    const ci = Math.cos(inclination), si = Math.sin(inclination);
    return [(cw * cn - sw * sn * ci) * x + (-sw * cn - cw * sn * ci) * y,
        (cw * sn + sw * cn * ci) * x + (-sw * sn + cw * cn * ci) * y,
        sw * si * x + cw * si * y];
}
export function planetPositions(date = new Date()) {
    const centuries = (date.getTime() / 86_400_000 + 2_440_587.5 - 2_451_545) / 36_525;
    return PLANETS.map(([name, , , elements, rates]) => {
        const orbit = orbitalElements(elements, rates, centuries);
        const M = Math.atan2(Math.sin(orbit.meanAnomaly), Math.cos(orbit.meanAnomaly));
        let E = M + orbit.e * Math.sin(M);
        for (let step = 0; step < 12; step++) E -= (E - orbit.e * Math.sin(E) - M) / (1 - orbit.e * Math.cos(E));
        return { name, position: orbitPoint(orbit, E) };
    });
}

// Ecliptic x/y map to scene X/-Z so the orbital plane is horizontal; the
// registry pitch tilts it toward the viewer. One scene unit is one au.
function solarSystem(date = new Date()) {
    const scene = new THREE.Group();
    const centuries = (date.getTime() / 86_400_000 + 2_440_587.5 - 2_451_545) / 36_525;
    const toScene = ([x, y, z]) => new THREE.Vector3(x, z, -y);
    const sphere = new THREE.SphereGeometry(1, 24, 16);
    const sun = new THREE.Mesh(sphere, new THREE.MeshBasicMaterial({ color: 0xffd36b }));
    sun.scale.setScalar(695_700_000 / AU);
    Object.assign(sun.userData, { outline: true, sphere: true });
    scene.add(sun);
    const positions = new Map(planetPositions(date).map(({ name, position }) => [name, position]));
    for (const [name, radius, color, elements, rates] of PLANETS) {
        const orbit = orbitalElements(elements, rates, centuries);
        const points = Array.from({ length: 721 }, (_, index) => toScene(orbitPoint(orbit, 2 * Math.PI * index / 720)));
        const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points),
            new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: name === 'Pluto' ? 0.16 : 0.3 }));
        const planet = new THREE.Mesh(sphere, new THREE.MeshStandardMaterial({ color, roughness: 0.8 }));
        planet.position.copy(toScene(positions.get(name)));
        planet.scale.setScalar(radius / AU);
        Object.assign(planet.userData, { outline: true, sphere: true });
        scene.add(line, planet);
    }
    return scene;
}

export function proceduralScene(kind) {
    if (kind === 'hair-fiber') return hairFiber();
    if (kind === 'light-wave') return lightWave();
    if (kind === 'hydrogen-1s') return hydrogen1s();
    if (kind === 'solar-system') return solarSystem();
    return new THREE.Group();
}
