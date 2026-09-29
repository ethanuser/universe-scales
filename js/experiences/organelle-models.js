// Cell-scale procedural models: a mitochondrion in longitudinal section and a
// pyramidal neuron whose action potential animates along its axon.
// Units are the model's own (mitochondrion: 1 = its length; neuron: micrometers).
import * as THREE from '../vendor/three/three.module.min.js';
import { labelNode } from './model-overlay-nodes.js';
import { registerAnimation } from './model-animation.js';

function seeded(seed) {
    return () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) + 0.5) / 4294967296;
}
const smooth = x => { const t = Math.min(1, Math.max(0, x)); return t * t * (3 - 2 * t); };

// Concatenates indexed or plain geometries into one non-indexed geometry.
function mergeSimple(geometries, attributes = ['position', 'normal']) {
    const parts = geometries.map(geometry => geometry.index ? geometry.toNonIndexed() : geometry);
    const merged = new THREE.BufferGeometry();
    for (const name of attributes) {
        const size = parts[0].getAttribute(name).itemSize;
        const data = new Float32Array(parts.reduce((sum, part) => sum + part.getAttribute(name).array.length, 0));
        let offset = 0;
        for (const part of parts) { data.set(part.getAttribute(name).array, offset); offset += part.getAttribute(name).array.length; }
        merged.setAttribute(name, new THREE.BufferAttribute(data, size));
    }
    return merged;
}

// ---------------------------------------------------------------- mitochondrion
// A longitudinal section: the back half of the organelle is kept and the cut
// plane faces the viewer. Cristae are perforated lamellar sheets ("baffles")
// perpendicular to the long axis, as seen in electron tomography of most
// animal mitochondria: each is an annulus attached to the inner boundary
// membrane, so the section shows them as bands reaching in from both walls.
export const MITOCHONDRION = Object.freeze({ radius: 0.17, exponent: 2.6, innerFactor: 0.9, cristae: 17 });
const wallRadius = (x, factor) => {
    const u = Math.min(1, Math.abs(x) / 0.5);
    return factor * MITOCHONDRION.radius * Math.pow(Math.max(0, 1 - Math.pow(u, MITOCHONDRION.exponent)), 1 / MITOCHONDRION.exponent);
};

function halfShell(factor, material, name) {
    const columns = 64, rows = 32, positions = [], indices = [];
    for (let i = 0; i <= columns; i++) {
        const x = -0.5 + i / columns, radius = wallRadius(x, factor);
        for (let j = 0; j <= rows; j++) {
            const angle = Math.PI * j / rows;
            positions.push(x, radius * Math.cos(angle), -radius * Math.sin(angle));
        }
    }
    for (let i = 0; i < columns; i++) for (let j = 0; j < rows; j++) {
        const a = i * (rows + 1) + j, b = a + rows + 1;
        indices.push(a, a + 1, b, a + 1, b + 1, b);
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setIndex(indices);
    geometry.computeVertexNormals();
    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = name;
    return mesh;
}
// A flat strip between two polylines that share x positions, in the plane z = level.
function planeStrip(topPoints, bottomPoints, material, name, level = 0) {
    const positions = [], indices = [];
    topPoints.forEach(([x, y], index) => positions.push(x, y, level, ...bottomPoints[index], level));
    for (let index = 0; index < topPoints.length - 1; index++) {
        const a = 2 * index;
        indices.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions.flatMap((value, index) => value), 3));
    geometry.setIndex(indices);
    geometry.computeVertexNormals();
    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = name;
    return mesh;
}

export function mitochondrionScene() {
    const scene = new THREE.Group();
    const random = seeded(0x31c0);
    const R = MITOCHONDRION.radius, inner = MITOCHONDRION.innerFactor;
    const membrane = (color, opacity) => new THREE.MeshStandardMaterial({ color, roughness: 0.55,
        side: THREE.DoubleSide, transparent: opacity < 1, opacity, depthWrite: opacity >= 1 });
    scene.add(halfShell(1, membrane(0xe9c49b, 0.42), 'outer-membrane'));
    // The inner boundary membrane is orange from outside; seen from inside (through
    // the cut) it shows the pale matrix.
    scene.add(halfShell(inner, new THREE.MeshStandardMaterial({ color: 0xd9834c, roughness: 0.5 }), 'inner-boundary-membrane'));
    const matrixShell = halfShell(inner * 0.996, new THREE.MeshStandardMaterial({ color: 0xf5dfc6, roughness: 0.85,
        side: THREE.BackSide }), 'matrix-wall');
    scene.add(matrixShell);
    // Cut edge: the double membrane seen in section, drawn at z = 0.
    const xs = Array.from({ length: 65 }, (_, i) => -0.5 + i / 64);
    const line = (factor, sign) => xs.map(x => [x, sign * wallRadius(x, factor)]);
    const rimMaterial = new THREE.MeshStandardMaterial({ color: 0xe1a06a, roughness: 0.7, side: THREE.DoubleSide });
    for (const sign of [1, -1])
        scene.add(planeStrip(line(1, sign), line(inner, sign), rimMaterial, `membrane-rim-${sign > 0 ? 'top' : 'bottom'}`, 0));

    // Cristae: annular sheets at x_c, reaching in from the inner wall.
    const cristaMaterial = new THREE.MeshStandardMaterial({ color: 0xd8562f, roughness: 0.5, side: THREE.DoubleSide });
    const sheets = [];
    for (let c = 0; c < MITOCHONDRION.cristae; c++) {
        const x0 = -0.395 + c * (0.79 / (MITOCHONDRION.cristae - 1)) + (random() - 0.5) * 0.006;
        const phase = random() * 6.28, base = 0.34 + 0.34 * random(), fold = 0.003 + 0.005 * random();
        const depth = angle => base + 0.14 * Math.sin(2 * angle + phase) + 0.06 * Math.sin(5 * angle + 2 * phase);
        const ripple = (radiusFraction, angle) => fold * Math.sin(5 * radiusFraction + 2 * angle + phase);
        const wall = wallRadius(x0, inner) * 0.995, arcs = 28, rings = 7, positions = [], indices = [];
        for (let j = 0; j <= arcs; j++) {
            const angle = Math.PI * j / arcs, edge = wall * (1 - depth(angle));
            for (let k = 0; k <= rings; k++) {
                const radius = edge + (wall - edge) * k / rings;
                positions.push(x0 + ripple(k / rings, angle), radius * Math.cos(angle), -radius * Math.sin(angle));
            }
        }
        for (let j = 0; j < arcs; j++) for (let k = 0; k < rings; k++) {
            const a = j * (rings + 1) + k, b = a + rings + 1;
            indices.push(a, a + 1, b, a + 1, b + 1, b);
        }
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        geometry.setIndex(indices);
        geometry.computeVertexNormals();
        sheets.push(geometry);
    }
    const cristae = new THREE.Mesh(mergeSimple(sheets), cristaMaterial);
    cristae.name = 'cristae';
    scene.add(cristae);
    // Matrix contents: ribosomes and two circular mitochondrial DNA molecules.
    const ribosomes = [], dot = new THREE.SphereGeometry(0.0042, 6, 4);
    for (let index = 0; index < 110; index++) {
        const x = (random() - 0.5) * 0.86, limit = wallRadius(x, inner) * 0.85;
        const y = (random() * 2 - 1) * limit, z = -Math.abs(random() * limit * 0.9);
        ribosomes.push(dot.clone().translate(x, y, z - 0.004));
    }
    const ribosomeMesh = new THREE.Mesh(mergeSimple(ribosomes), new THREE.MeshStandardMaterial({ color: 0x7a4a8a, roughness: 0.6 }));
    ribosomeMesh.name = 'matrix-ribosomes';
    scene.add(ribosomeMesh);
    const dna = new THREE.MeshStandardMaterial({ color: 0x3b73c4, roughness: 0.5 });
    for (const [x, y, z] of [[0.09, -0.02, -0.035], [-0.2, 0.03, -0.05]]) {
        const ring = new THREE.Mesh(new THREE.TorusGeometry(0.02, 0.0035, 8, 32), dna);
        ring.position.set(x, y, z); ring.rotation.set(0.5, 0.9, 0);
        ring.name = 'mitochondrial-dna';
        scene.add(ring);
    }
    const at = (text, x, y, z = 0, labelClass) => scene.add(Object.assign(labelNode(text, new THREE.Vector3(x, y, z), labelClass)));
    at('Outer membrane', -0.24, R * 1.03 + 0.015);
    at('Inner membrane', 0.26, -R * 1.03 - 0.045);
    at('Cristae', 0.1, R * 0.83, 0.02);
    at('Matrix', -0.05, 0.02, 0.01);
    return scene;
}

// --------------------------------------------------------------------- neuron
// A pyramidal neuron, in micrometers: soma about 20 um across at the origin, an
// apical dendrite rising to +52, basal dendrites reaching about 40 to each side,
// and an axon leaving the base of the soma through the axon hillock and initial
// segment, cropped at -50. The whole model spans 100 um, the listed size.
export const NEURON = Object.freeze({ span: 100, somaRadius: 9.5, axonEnd: -50, period: 5.2, axonSpeed: 46 });

// Membrane potential at the axon initial segment through one spike, in mV.
export function membranePotential(seconds) {
    const s = ((seconds % NEURON.period) + NEURON.period) % NEURON.period;
    if (s < 0.6) return -70;
    if (s < 1.3) return -70 + 15 * smooth((s - 0.6) / 0.7);
    if (s < 1.42) return -55 + 95 * smooth((s - 1.3) / 0.12);
    if (s < 1.7) return 40 - 120 * smooth((s - 1.42) / 0.28);
    if (s < 2.4) return -80 + 10 * smooth((s - 1.7) / 0.7);
    return -70;
}

const REST = { dendrite: [0.55, 0.2, 0.34], axon: [0.66, 0.42, 0.44] };
function tubeSegments(points, radii, sides, out, meta) {
    // Parallel-transport frames along a polyline; appends rings to `out`.
    const tangents = points.map((point, i) => (points[Math.min(points.length - 1, i + 1)].clone()
        .sub(points[Math.max(0, i - 1)])).normalize());
    let normal = new THREE.Vector3(0, 0, 1);
    if (Math.abs(tangents[0].dot(normal)) > 0.9) normal = new THREE.Vector3(1, 0, 0);
    const first = out.positions.length / 3;
    points.forEach((point, i) => {
        normal = normal.clone().sub(tangents[i].clone().multiplyScalar(normal.dot(tangents[i]))).normalize();
        const binormal = tangents[i].clone().cross(normal);
        for (let side = 0; side < sides; side++) {
            const angle = 2 * Math.PI * side / sides;
            const offset = normal.clone().multiplyScalar(Math.cos(angle)).add(binormal.clone().multiplyScalar(Math.sin(angle)));
            out.positions.push(...point.clone().add(offset.multiplyScalar(radii[i])).toArray());
            out.dist.push(meta.dist[i]); out.maxDist.push(meta.maxDist); out.kind.push(meta.kind); out.delay.push(meta.delay);
        }
    });
    for (let i = 0; i < points.length - 1; i++) for (let side = 0; side < sides; side++) {
        const a = first + i * sides + side, b = first + i * sides + (side + 1) % sides;
        out.indices.push(a, a + sides, b, b, a + sides, b + sides);
    }
}

function grow(out, random, start, direction, length, radius, taper, depth, distance, kind, delay = random() * 0.45) {
    const steps = Math.max(4, Math.round(length / 3.2)), points = [start.clone()], radii = [radius];
    let position = start.clone(), heading = direction.clone().normalize();
    const distances = [distance];
    for (let i = 1; i <= steps; i++) {
        heading.add(new THREE.Vector3(random() - 0.5, random() - 0.5, random() - 0.5).multiplyScalar(0.34)).normalize();
        position = position.clone().add(heading.clone().multiplyScalar(length / steps));
        points.push(position);
        radii.push(Math.max(0.3, radius * (1 - (1 - taper) * i / steps)));
        distances.push(distance + length * i / steps);
    }
    out.branches.push({ points, radii, distances, delay, depth, kind, tip: position.clone(), tipDist: distances.at(-1) });
    const branch = out.branches.at(-1);
    if (depth > 0) {
        const children = depth > 1 ? 2 : (random() < 0.6 ? 2 : 1);
        for (let child = 0; child < children; child++) {
            const side = new THREE.Vector3(random() - 0.5, random() - 0.5, random() - 0.5).normalize();
            const childDirection = heading.clone().add(side.multiplyScalar(0.8)).normalize();
            grow(out, random, position, childDirection, length * (0.66 + 0.16 * random()), radii.at(-1), 0.6,
                depth - 1, distances.at(-1), kind, delay);
        }
    }
    return branch;
}

export function neuronScene() {
    const scene = new THREE.Group();
    const random = seeded(0x4e55);
    const out = { branches: [] };
    const v = (x, y, z) => new THREE.Vector3(x, y, z);
    const R = NEURON.somaRadius;
    // Apical dendrite: a long trunk with a tuft; basal dendrites: five spread around the base.
    grow(out, random, v(0, R * 0.8, 0), v(0.04, 1, 0.02), 30, 3.0, 0.5, 2, 0, 'dendrite');
    const basal = [[-0.95, 0.15], [-0.7, -0.35], [0.9, 0.2], [0.65, -0.4], [0.05, 0.05]];
    basal.forEach(([x, y], index) => {
        const z = index % 2 ? 0.5 : -0.4;
        const direction = v(x, y, z).normalize();
        grow(out, random, direction.clone().multiplyScalar(R * 0.85), direction, 15 + 5 * random(), 2.1, 0.5, 2, 0, 'dendrite');
    });
    // Rescale so the apical tip sits at +52 um and no dendrite passes about 41 um sideways.
    let top = 0, side = 0;
    for (const branch of out.branches) for (const point of branch.points) { top = Math.max(top, point.y); side = Math.max(side, Math.hypot(point.x, point.z)); }
    const fit = Math.min(52 / top, 41 / side);
    for (const branch of out.branches) {
        branch.points = branch.points.map(point => point.clone().multiplyScalar(fit));
        branch.distances = branch.distances.map(d => d * fit); branch.tipDist *= fit;
    }
    // Axon: hillock, initial segment, then a cropped run at -50 um.
    const axonPoints = [], axonRadii = [], axonDistances = [];
    const axonStart = -R * 0.9, axonLength = NEURON.axonEnd - axonStart;
    for (let i = 0; i <= 26; i++) {
        const t = i / 26, y = axonStart + axonLength * t;
        axonPoints.push(v(3.2 * Math.sin(t * 2.4) * t, y, 0));
        axonRadii.push(0.85 + 2.4 * Math.pow(1 - smooth(t * 5), 2));
        axonDistances.push(Math.abs(y - axonStart) * 1.0);
    }
    const axonTotal = axonDistances.at(-1);
    out.branches.push({ points: axonPoints, radii: axonRadii, distances: axonDistances, delay: 0, depth: 0, kind: 'axon',
        tip: axonPoints.at(-1), tipDist: axonTotal });

    const data = { positions: [], indices: [], dist: [], maxDist: [], kind: [], delay: [] };
    const sides = 7;
    for (const branch of out.branches)
        tubeSegments(branch.points, branch.radii, sides, data,
            { dist: branch.distances, maxDist: branch.tipDist, kind: branch.kind === 'axon' ? 1 : 0, delay: branch.delay });
    // Subtree extent for the input wave: each dendritic ring gets its branch's farthest tip.
    const tree = new THREE.BufferGeometry();
    tree.setAttribute('position', new THREE.Float32BufferAttribute(data.positions, 3));
    tree.setIndex(data.indices);
    tree.computeVertexNormals();
    tree.setAttribute('pathDist', new THREE.Float32BufferAttribute(data.dist, 1));
    tree.setAttribute('maxDist', new THREE.Float32BufferAttribute(data.maxDist, 1));
    tree.setAttribute('kind', new THREE.Float32BufferAttribute(data.kind, 1));
    tree.setAttribute('delay', new THREE.Float32BufferAttribute(data.delay, 1));
    const count = data.dist.length, baseColors = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) baseColors.set(data.kind[i] ? REST.axon : REST.dendrite, i * 3);
    tree.setAttribute('color', new THREE.BufferAttribute(baseColors.slice(), 3));
    tree.userData.baseColors = baseColors;
    const processes = new THREE.Mesh(tree, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.55 }));
    processes.name = 'neuron-processes';
    scene.add(processes);

    // Dendritic spines: small heads on necks, scattered along the dendrites.
    const spineGeometries = [], spineRandom = seeded(0x5b1e);
    for (const branch of out.branches) if (branch.kind !== 'axon') {
        const spines = Math.round(branch.points.length * 1.4);
        for (let s = 0; s < spines; s++) {
            const position = branch.points[Math.floor(spineRandom() * (branch.points.length - 1))].clone();
            const direction = v(spineRandom() - 0.5, spineRandom() - 0.5, spineRandom() - 0.5).normalize();
            const head = new THREE.SphereGeometry(0.42, 6, 4).translate(0, 2.2, 0);
            const neck = new THREE.CylinderGeometry(0.16, 0.16, 2, 5).translate(0, 1.1, 0);
            const spine = mergeSimple([head, neck]);
            spine.applyMatrix4(new THREE.Matrix4().compose(position.clone().addScaledVector(direction, 0.7),
                new THREE.Quaternion().setFromUnitVectors(v(0, 1, 0), direction), v(1, 1, 1)));
            spineGeometries.push(spine);
        }
    }
    const spines = new THREE.Mesh(mergeSimple(spineGeometries), new THREE.MeshStandardMaterial({ color: 0xd6b0a8, roughness: 0.6 }));
    spines.name = 'dendritic-spines';
    scene.add(spines);

    // Soma: a rounded pyramid (tapering toward the apical dendrite), translucent so the nucleus shows.
    const somaGeometry = new THREE.IcosahedronGeometry(1, 5);
    const somaPosition = somaGeometry.getAttribute('position');
    for (let i = 0; i < somaPosition.count; i++) {
        const p = new THREE.Vector3().fromBufferAttribute(somaPosition, i);
        const taper = 1 - 0.32 * smooth(p.y);
        somaPosition.setXYZ(i, p.x * taper * R * 1.02, p.y * R * (p.y > 0 ? 1.18 : 0.92), p.z * taper * R * 0.95);
    }
    somaGeometry.computeVertexNormals();
    const somaMaterial = new THREE.MeshStandardMaterial({ color: 0xc9636f, roughness: 0.5, transparent: true, opacity: 0.66,
        depthWrite: false, emissive: 0xffe066, emissiveIntensity: 0 });
    const soma = new THREE.Mesh(somaGeometry, somaMaterial);
    soma.name = 'soma';
    scene.add(soma);
    const nucleus = new THREE.Mesh(new THREE.SphereGeometry(R * 0.5, 24, 16), new THREE.MeshStandardMaterial({ color: 0x5a5fb0, roughness: 0.6 }));
    nucleus.position.set(0, R * 0.08, 0);
    nucleus.name = 'nucleus';
    const nucleolus = new THREE.Mesh(new THREE.SphereGeometry(R * 0.16, 12, 8), new THREE.MeshStandardMaterial({ color: 0x2d2f6b, roughness: 0.7 }));
    nucleolus.position.set(R * 0.1, R * 0.16, R * 0.22);
    scene.add(nucleus, nucleolus);

    // Myelin sheath around the axon after its initial segment.
    const sheathStart = 0.56, sheath = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(
        axonPoints.filter((_, i) => i / 26 >= sheathStart)), 20, 2.5, 12, false),
    new THREE.MeshStandardMaterial({ color: 0xdfeafc, roughness: 0.35, transparent: true, opacity: 0.6, depthWrite: false }));
    sheath.name = 'myelin-sheath';
    scene.add(sheath);

    // Labels. The axon-initial-segment readout is rewritten every frame.
    const initial = axonPoints[7];
    const label = (text, x, y, z, labelClass) => { const n = labelNode(text, v(x, y, z), labelClass); scene.add(n); return n; };
    label('Dendrites', -30, 12, 0);
    label('Soma (cell body)', 24, -8, 0);
    label('Nucleus', -2, R * 0.7, R * 0.4);
    label('Myelin sheath', 12, -43, 0);
    label('Axon, cropped: it runs on to its terminals', 0, -54, 0);
    const readout = label('Axon initial segment: −70 mV', initial.x + 26, initial.y, 0);
    readout.name = 'ais-readout';
    scene.userData.animation = { kind: 'action-potential', period: NEURON.period };
    return scene;
}

function lerpInto(target, offset, color, amount) {
    for (let channel = 0; channel < 3; channel++)
        target[offset + channel] += (color[channel] - target[offset + channel]) * amount;
}
const INPUT = [1, 0.62, 0.22], SPIKE = [1, 0.96, 0.55], REFRACTORY = [0.28, 0.4, 0.88];

// Colors the membrane by its state at `elapsed` seconds: synaptic input closing in on the
// soma (orange), the spike leaving the axon initial segment (yellow-white) with a brief
// hyperpolarized tail (blue), and a weaker spike running back into the dendrites.
export function updateNeuron(root, elapsed) {
    const processes = root.getObjectByName('neuron-processes');
    if (!processes || !Number.isFinite(elapsed)) return;
    const geometry = processes.geometry;
    const dist = geometry.getAttribute('pathDist').array, maxDist = geometry.getAttribute('maxDist').array;
    const kind = geometry.getAttribute('kind').array, delay = geometry.getAttribute('delay').array;
    const colors = geometry.getAttribute('color'), base = geometry.userData.baseColors;
    const s = ((elapsed % NEURON.period) + NEURON.period) % NEURON.period;
    const head = (s - 1.3) * NEURON.axonSpeed;
    for (let i = 0; i < dist.length; i++) {
        const offset = i * 3;
        colors.array[offset] = base[offset]; colors.array[offset + 1] = base[offset + 1]; colors.array[offset + 2] = base[offset + 2];
        if (kind[i]) {
            if (head > 0) {
                const behind = head - dist[i];
                if (behind > 0) lerpInto(colors.array, offset, REFRACTORY, 0.55 * Math.exp(-behind / 15));
                lerpInto(colors.array, offset, SPIKE, Math.exp(-(behind * behind) / 40));
            }
        } else {
            const u = smooth((s - 0.3 - delay[i]) / 0.85);
            if (u > 0 && u < 1) {
                const front = maxDist[i] * (1 - u), gap = dist[i] - front;
                lerpInto(colors.array, offset, INPUT, 0.8 * Math.exp(-(gap * gap) / 30));
            }
            if (head > 0) {
                const gap = dist[i] - head * 0.75;
                lerpInto(colors.array, offset, SPIKE, 0.4 * Math.exp(-(gap * gap) / 50));
            }
        }
    }
    colors.needsUpdate = true;
    const potential = membranePotential(elapsed);
    const soma = root.getObjectByName('soma');
    if (soma) soma.material.emissiveIntensity = 0.5 * smooth((potential + 65) / 90);
    const readout = root.getObjectByName('ais-readout');
    if (readout) readout.userData.label = `Axon initial segment: ${potential > 0 ? '+' : '−'}${Math.abs(Math.round(potential))} mV`;
}
registerAnimation('action-potential', updateNeuron);

export const organelleModelMetadata = Object.freeze({
    'Mitochondrion': Object.freeze({ id: 'mitochondrion-lamellar-section', procedural: 'mitochondrion-section', geometry: 'mesh',
        presentation: Object.freeze({ reference_size: 1, layout_width_factor: 1.05, focus_scale_factor: 1.3,
            display_extent_factor: 1, pitch: 26, yaw: -30 }),
        basis_url: 'https://doi.org/10.1016/j.bbabio.2009.09.010',
        basis_label: 'Cristae architecture: electron tomography',
        note: 'A mitochondrion cut lengthwise. Its double membrane (a tan outer membrane around an orange inner membrane) encloses the matrix, where the inner membrane folds inward as about 17 perforated, plate-like cristae, the lamellar form seen in electron tomography of many animal cells. The long axis is the listed 10 micrometers. Real mitochondria vary a lot in shape and in cristae count and spacing, and are often much thinner; sizes and folds here are a schematic, not a reconstruction of one organelle.' }),
    'Neuron': Object.freeze({ id: 'pyramidal-neuron-action-potential', procedural: 'neuron-action-potential', geometry: 'mesh',
        presentation: Object.freeze({ reference_size: NEURON.span, layout_width_factor: 1.0, focus_scale_factor: 1.3,
            display_extent_factor: 1, yaw: 18, pitch: 4 }),
        basis_url: 'https://en.wikipedia.org/wiki/Action_potential',
        basis_label: 'Action potential',
        note: 'A pyramidal neuron and its local dendritic tree, spanning the listed 100 micrometers: a soma about 20 micrometers across with its nucleus, an apical dendrite, basal dendrites with spines, and an axon that leaves through the axon hillock and initial segment into a myelin sheath. The animation repeats one signal: orange input waves converge on the soma from the dendrites, the membrane at the axon initial segment crosses threshold (−55 mV) and fires a spike (peak +40 mV, watch the live readout), the yellow pulse runs down the axon with a bluish hyperpolarized tail, and a weaker spike echoes back into the dendrites. It is slowed roughly 20,000 times; a real spike lasts about a millisecond and is millimeters long, far longer than this whole cell. The axon, which can be a meter long, is cropped.' })
});

export const organelleScenes = Object.freeze({
    'mitochondrion-section': mitochondrionScene,
    'neuron-action-potential': neuronScene
});
