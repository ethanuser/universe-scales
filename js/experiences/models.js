import * as THREE from 'three';
import { GLTFLoader } from '../vendor/three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from '../vendor/three/addons/utils/BufferGeometryUtils.js';
import { clone } from '../vendor/three/addons/utils/SkeletonUtils.js';

const models = new Map();
const registry = fetch('content/visualizations/models.json', { cache: 'no-store' })
    .then(r => r.ok ? r.json() : { models: [] }).catch(() => ({ models: [] }));
const moleculeData = fetch('content/visualizations/molecules.json', { cache: 'no-store' })
    .then(r => r.ok ? r.json() : null).catch(() => null);
const loader = new GLTFLoader();
const cross2D = (a, b, c) => (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
function convexHull(points) {
    if (points.length < 3) return points;
    const ordered = [...points].sort((a, b) => a.x - b.x || a.y - b.y);
    const lower = [], upper = [];
    for (const point of ordered) {
        while (lower.length > 1 && cross2D(lower.at(-2), lower.at(-1), point) <= 0) lower.pop();
        lower.push(point);
    }
    for (let index = ordered.length - 1; index >= 0; index--) {
        const point = ordered[index];
        while (upper.length > 1 && cross2D(upper.at(-2), upper.at(-1), point) <= 0) upper.pop();
        upper.push(point);
    }
    lower.pop(); upper.pop();
    return lower.concat(upper);
}
function insideHull(point, polygon) {
    let inside = false;
    for (let index = 0, previous = polygon.length - 1; index < polygon.length; previous = index++) {
        const a = polygon[previous], b = polygon[index];
        if (Math.abs(cross2D(a, b, point)) < 0.001 &&
            point.x >= Math.min(a.x, b.x) && point.x <= Math.max(a.x, b.x) &&
            point.y >= Math.min(a.y, b.y) && point.y <= Math.max(a.y, b.y)) return true;
        if ((a.y > point.y) !== (b.y > point.y) &&
            point.x < (b.x - a.x) * (point.y - a.y) / (b.y - a.y) + a.x) inside = !inside;
    }
    return inside;
}
function sampledModelPoints(instance) {
    instance.updateMatrixWorld(true);
    const meshes = [];
    instance.traverse(child => {
        if (child.isMesh || child.isPoints) {
            const position = child.geometry.getAttribute('position');
            if (position) meshes.push({ child, position });
        }
    });
    const total = meshes.reduce((sum, mesh) => sum + mesh.position.count, 0);
    const stride = total <= 6000 ? 1 : Math.ceil(total / 1200);
    const points = [];
    const inverse = instance.matrixWorld.clone().invert();
    for (const { child, position } of meshes) {
        const extremes = [null, null, null, null, null, null];
        for (let index = 0; index < position.count; index++) {
            const point = new THREE.Vector3();
            if (child.isMesh) child.getVertexPosition(index, point);
            else point.fromBufferAttribute(position, index);
            if (index % stride === 0) points.push(point.clone().applyMatrix4(child.matrixWorld).applyMatrix4(inverse));
            for (let axis = 0; axis < 3; axis++) {
                const low = axis * 2, high = low + 1, value = point.getComponent(axis);
                if (!extremes[low] || value < extremes[low].value) extremes[low] = { value, point };
                if (!extremes[high] || value > extremes[high].value) extremes[high] = { value, point };
            }
        }
        for (const extreme of extremes) if (extreme)
            points.push(extreme.point.clone().applyMatrix4(child.matrixWorld).applyMatrix4(inverse));
    }
    return points;
}
function addHoverOverlay(instance) {
    const originals = [];
    instance.traverse(child => {
        if (child.isMesh || child.isPoints) originals.push(child);
    });
    return originals.map(child => {
        const overlay = child.clone(false);
        overlay.material = child.isPoints
            ? new THREE.PointsMaterial({ color: 0xffffff, size: child.material.size,
                sizeAttenuation: child.material.sizeAttenuation, transparent: true,
                opacity: 0.16, depthWrite: false })
            : new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true,
                opacity: 0.16, depthWrite: false, polygonOffset: true,
                polygonOffsetFactor: -1, polygonOffsetUnits: -1 });
        overlay.visible = false;
        overlay.renderOrder = child.renderOrder + 1;
        child.parent.add(overlay);
        return overlay;
    });
}
function flattenStaticScene(scene) {
    scene.updateMatrixWorld(true);
    const meshes = [];
    let unsupported = false;
    scene.traverse(child => {
        if (child.isLine || child.isPoints || child.isSprite) unsupported = true;
        if (!child.isMesh) return;
        if (child.isSkinnedMesh || child.morphTargetInfluences || Array.isArray(child.material))
            unsupported = true;
        else meshes.push(child);
    });
    if (unsupported || !meshes.length) return scene;
    const groups = new Map();
    for (const child of meshes) {
        const geometry = child.geometry.clone();
        geometry.applyMatrix4(child.matrixWorld);
        const attributes = Object.entries(geometry.attributes).sort(([a], [b]) => a.localeCompare(b))
            .map(([name, attribute]) => `${name}:${attribute.itemSize}:${attribute.normalized}:${attribute.array.constructor.name}`)
            .join('|');
        const key = `${child.material.uuid}:${Boolean(geometry.index)}:${attributes}`;
        if (!groups.has(key)) groups.set(key, { material: child.material, geometries: [] });
        groups.get(key).geometries.push(geometry);
    }
    const flattened = new THREE.Group();
    for (const { material, geometries } of groups.values()) {
        const merged = geometries.length === 1 ? geometries[0] : mergeGeometries(geometries);
        if (!merged) {
            for (const group of groups.values())
                for (const geometry of group.geometries) geometry.dispose();
            flattened.traverse(child => child.geometry?.dispose());
            return scene;
        }
        if (merged !== geometries[0]) for (const geometry of geometries) geometry.dispose();
        flattened.add(new THREE.Mesh(merged, material));
    }
    return flattened.children.length ? flattened : scene;
}
const proceduralLength = {
    'Hydrogen Atom': { id: 'hydrogen-1s', procedural: 'hydrogen-1s', geometry: 'mesh',
        presentation: { reference_size: 1, layout_width_factor: 2.6,
            focus_scale_factor: 2.6, display_extent_factor: 2.6 },
        basis_url: 'https://ocw.mit.edu/courses/5-111-principles-of-chemical-science-fall-2008/8a0da0346f1d611fbbd5c31a54865c2d_lecnotes06.pdf',
        note: 'A sparse sample of hydrogen’s 1s electron probability cloud, clipped at 1.3 Bohr radii for legibility. The listed Bohr radius is the most probable electron distance, not a hard atomic edge; the cloud continues beyond these dots.' },
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
        presentation: { measure_axis: 'x', layout_width_factor: 1.1 },
        basis_url: 'https://wellcomecollection.org/works/wxgqyf66',
        basis_label: 'Cuticle reference: Wellcome Collection',
        note: 'An illustrative scalp-hair fiber with overlapping cuticle ridges. Only its horizontal diameter is calibrated to the listed 100 micrometers; the cropped shaft length is not.' }
};

function moleculeScene(data) {
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

function proceduralScene(kind) {
    const scene = new THREE.Group();
    if (kind === 'hair-fiber') {
        const material = new THREE.MeshStandardMaterial({ color: 0x744831, roughness: 0.88 });
        scene.add(new THREE.Mesh(new THREE.CylinderGeometry(0.493, 0.493, 1, 64, 1), material));
        const cuticle = new THREE.MeshStandardMaterial({ color: 0x86573c, roughness: 0.94 });
        for (let index = 0; index < 20; index++) {
            const ridge = new THREE.Mesh(new THREE.CylinderGeometry(0.499, 0.494, 0.06, 64, 1, true), cuticle);
            ridge.position.y = -0.46 + index * 0.048;
            scene.add(ridge);
        }
    } else if (kind === 'hydrogen-1s') {
        let seed = 0x1234abcd;
        const random = () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) + 0.5) / 4294967296;
        const positions = [];
        // The 1s shell distribution is Gamma(k=3, rate=2) in Bohr-radius units.
        for (let index = 0; index < 6200; index++) {
            const radius = -Math.log(random() * random() * random()) / 2;
            if (radius > 1.3) continue;
            const z = 2 * random() - 1, angle = 2 * Math.PI * random();
            const circle = Math.sqrt(1 - z * z);
            positions.push(radius * circle * Math.cos(angle), radius * circle * Math.sin(angle), radius * z);
        }
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        scene.add(new THREE.Points(geometry, new THREE.PointsMaterial({
            color: 0x2675ae, size: 1.6, sizeAttenuation: false,
            transparent: true, opacity: 0.26, depthWrite: false
        })));
    }
    return scene;
}

async function load(entry) {
    const key = entry.src || entry.id;
    if (!models.has(key)) models.set(key, (entry.procedural === 'molecule'
        ? moleculeData.then(data => data?.models?.[entry.molecule]
            ? { scene: moleculeScene(data.models[entry.molecule]) } : null)
        : entry.procedural ? Promise.resolve({ scene: proceduralScene(entry.procedural) })
            : loader.loadAsync(entry.src)).then(gltf => {
        if (!gltf) return null;
        let scene = gltf.scene;
        const removedNames = new Set(entry.presentation?.remove_nodes || []);
        if (removedNames.size) {
            const nodesToRemove = [];
            scene.traverse(node => {
                if (removedNames.has(node.name) || removedNames.has(node.userData?.name)) nodesToRemove.push(node);
            });
            for (const node of nodesToRemove) node.removeFromParent();
        }
        const preRotation = entry.presentation?.pre_rotation;
        if (preRotation) scene.rotation.set(
            THREE.MathUtils.degToRad(preRotation.x || 0),
            THREE.MathUtils.degToRad(preRotation.y || 0),
            THREE.MathUtils.degToRad(preRotation.z || 0)
        );
        if (entry.presentation?.flatten_static) scene = flattenStaticScene(scene);
        scene.updateMatrixWorld(true);
        const bounds = new THREE.Box3().setFromObject(scene);
        const center = bounds.getCenter(new THREE.Vector3());
        const size = bounds.getSize(new THREE.Vector3());
        const reference = entry.presentation?.measure_axis;
        const referenceSize = entry.presentation?.reference_size ||
            (reference && size[reference] > 0 ? size[reference] : Math.max(size.x, size.y, size.z));
        const group = new THREE.Group();
        scene.position.sub(center);
        group.add(scene);
        const measureFraction = entry.presentation?.measure_fraction || 1;
        group.scale.setScalar(1 / (referenceSize * measureFraction));
        const normalized = new THREE.Group();
        normalized.add(group);
        if (entry.presentation && ['tint', 'color_gain', 'roughness', 'metalness', 'opaque', 'double_sided', 'emissive']
            .some(key => key in entry.presentation)) {
            normalized.traverse(child => {
                if (!child.isMesh) return;
                const customize = original => {
                    const material = original.clone();
                    if (entry.presentation.tint) material.color.set(entry.presentation.tint);
                    if (entry.presentation.color_gain) material.color.multiplyScalar(entry.presentation.color_gain);
                    if (entry.presentation.roughness != null) material.roughness = entry.presentation.roughness;
                    if (entry.presentation.metalness != null) material.metalness = entry.presentation.metalness;
                    if (entry.presentation.opaque) {
                        material.transparent = false;
                        material.opacity = 1;
                        material.depthWrite = true;
                    }
                    if (entry.presentation.double_sided) material.side = THREE.DoubleSide;
                    if (entry.presentation.emissive && material.emissive) {
                        material.emissive.set(entry.presentation.emissive);
                        material.emissiveIntensity = entry.presentation.emissive_intensity ?? 0.25;
                    }
                    return material;
                };
                child.material = Array.isArray(child.material)
                    ? child.material.map(customize) : customize(child.material);
            });
        }
        if (entry.presentation?.backing_color) {
            const factor = entry.presentation.backing_scale ?? 0.35;
            const backing = new THREE.Mesh(new THREE.SphereGeometry(1, 28, 20),
                new THREE.MeshStandardMaterial({ color: entry.presentation.backing_color,
                    roughness: 0.95, metalness: 0 }));
            backing.scale.set(size.x, size.y, size.z).multiplyScalar(factor / referenceSize);
            normalized.add(backing);
        }
        return normalized;
    }).catch(() => null));
    return models.get(key);
}
class ModelStage {
    constructor(ctx, redraw) {
        this.ctx = ctx; this.redraw = redraw; this.instances = new Map(); this.entries = [];
        this.rotations = new Map(); this.hulls = new Map();
        try {
            this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
            this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
            this.renderer.domElement.className = 'experience-model-stage';
            this.renderer.domElement.setAttribute('aria-hidden', 'true');
            ctx.stageFrame.insertBefore(this.renderer.domElement, ctx.stage);
            this.scene = new THREE.Scene();
            this.scene.add(new THREE.HemisphereLight(0xffffff, 0x667788, 2));
            const light = new THREE.DirectionalLight(0xffffff, 2.5);
            light.position.set(-500, 800, 1500); this.scene.add(light);
            this.camera = new THREE.PerspectiveCamera(35, 2, 20, 1e8);
            this.camera.position.z = 8000;
            registry.then(data => {
                if (this.disposed) return;
                this.entries = data.models || [];
                this.ctx.updateDetail();
                redraw();
            });
        } catch { this.unavailable = true; }
    }
    entry(item) {
        return (this.ctx.dimension === 'length' && proceduralLength[item.name]) ||
            this.entries.find(e => e.matches?.[this.ctx.dimension]?.includes(item.name));
    }
    pick(clientX, clientY) {
        if (!this.renderer || this.disposed) return null;
        const rect = this.renderer.domElement.getBoundingClientRect();
        if (!rect.width || !rect.height || clientX < rect.left || clientX > rect.right ||
            clientY < rect.top || clientY > rect.bottom) return null;
        const point = { x: clientX - rect.left, y: clientY - rect.top };
        return [...this.hulls.values()]
            .filter(hull => insideHull(point, hull.polygon))
            .sort((a, b) => b.depth - a.depth)[0]?.item || null;
    }
    setHover(item, pointer) {
        if (pointer !== undefined) this.pointer = pointer;
        if (this.hovered === item) return;
        this.hovered = item;
        this.redraw();
    }
    beginRotate(item, timestamp = performance.now()) {
        this.draggingItem = item;
        this.setHover(null);
        const state = this.rotations.get(item) || { yaw: 0, pitch: 0, velocity: 0, pitchVelocity: 0 };
        state.dragging = true;
        state.velocity = 0;
        state.pitchVelocity = 0;
        state.samples = [{ time: timestamp, yaw: state.yaw, pitch: state.pitch }];
        this.rotations.set(item, state);
    }
    rotate(item, dx, dy = 0, timestamp = performance.now()) {
        const state = this.rotations.get(item) || { yaw: 0, pitch: 0, velocity: 0, pitchVelocity: 0, dragging: true };
        const yawDelta = dx * 0.008;
        const pitchDelta = dy * 0.006;
        state.yaw += yawDelta;
        state.pitch = THREE.MathUtils.clamp(state.pitch + pitchDelta, -Math.PI / 2, Math.PI / 2);
        state.samples ||= [];
        state.samples.push({ time: timestamp, yaw: state.yaw, pitch: state.pitch });
        while (state.samples.length > 2 && timestamp - state.samples[0].time > 90) state.samples.shift();
        this.rotations.set(item, state);
        this.redraw();
    }
    releaseRotate(item, timestamp = performance.now()) {
        const state = this.rotations.get(item);
        if (!state) return;
        const samples = state.samples || [];
        const last = samples.at(-1);
        const recent = samples.filter(sample => sample.time >= last.time - 50);
        const first = recent.length > 1 ? recent[0] : samples.at(-2) || last;
        const duration = Math.max(0.008, ((last?.time ?? timestamp) - (first?.time ?? timestamp)) / 1000);
        const idle = Math.max(0, timestamp - (last?.time ?? timestamp));
        const carry = Math.exp(-idle / 130);
        state.velocity = THREE.MathUtils.clamp(((last?.yaw ?? state.yaw) - (first?.yaw ?? state.yaw)) / duration * carry, -14, 14);
        state.pitchVelocity = THREE.MathUtils.clamp(((last?.pitch ?? state.pitch) - (first?.pitch ?? state.pitch)) / duration * carry, -10, 10);
        state.yaw = Math.atan2(Math.sin(state.yaw), Math.cos(state.yaw));
        state.dragging = false;
        this.draggingItem = null;
        if (!this.returnFrame) this.returnFrame = requestAnimationFrame(now => this.returnToPose(now));
        this.redraw();
    }
    returnToPose(now) {
        this.returnFrame = null;
        if (this.disposed) return;
        const dt = Math.min(0.032, (now - (this.lastReturnFrame ?? now - 16)) / 1000);
        this.lastReturnFrame = now;
        let pending = false, changed = false;
        for (const state of this.rotations.values()) {
            if (state.dragging) continue;
            const acceleration = -14 * state.yaw - 7.5 * state.velocity;
            state.velocity = THREE.MathUtils.clamp(state.velocity + acceleration * dt, -14, 14);
            state.yaw += state.velocity * dt;
            const pitchAcceleration = -14 * state.pitch - 7.5 * state.pitchVelocity;
            state.pitchVelocity = THREE.MathUtils.clamp(state.pitchVelocity + pitchAcceleration * dt, -10, 10);
            state.pitch = THREE.MathUtils.clamp(state.pitch + state.pitchVelocity * dt,
                -Math.PI / 2, Math.PI / 2);
            if (Math.abs(state.pitch) === Math.PI / 2 && Math.sign(state.pitchVelocity) === Math.sign(state.pitch))
                state.pitchVelocity = 0;
            if (Math.abs(state.yaw) < 0.001 && Math.abs(state.velocity) < 0.008) state.yaw = state.velocity = 0;
            if (Math.abs(state.pitch) < 0.001 && Math.abs(state.pitchVelocity) < 0.008)
                state.pitch = state.pitchVelocity = 0;
            if (state.yaw || state.velocity || state.pitch || state.pitchVelocity) pending = true;
            changed = true;
        }
        if (changed) this.redraw();
        if (pending) this.returnFrame = requestAnimationFrame(next => this.returnToPose(next));
        else this.lastReturnFrame = null;
    }
    begin(exponent = 0) {
        this.eyeY = 500 - (globalThis.ScaleJourney?.BASELINE ?? 405)
            + 130 * THREE.MathUtils.clamp((exponent + 1) / 7, 0, 1);
        for (const instance of this.instances.values()) if (instance) instance.visible = false;
    }
    draw(item, x, y, size) {
        const entry = this.entry(item);
        if (!entry || this.unavailable || this.disposed) return false;
        if (!this.instances.has(item)) {
            this.instances.set(item, null);
            load(entry).then(model => {
                if (this.disposed) return;
                if (model) {
                    const instance = clone(model);
                    instance.userData.pickPoints = sampledModelPoints(instance);
                    instance.userData.hoverOverlays = addHoverOverlay(instance);
                    const pose = entry.presentation || {};
                    instance.rotation.order = 'XYZ';
                    instance.rotation.set(THREE.MathUtils.degToRad(pose.pitch || 0),
                        THREE.MathUtils.degToRad(pose.yaw || 0), THREE.MathUtils.degToRad(pose.roll || 0));
                    instance.updateMatrixWorld(true);
                    const defaultBounds = new THREE.Box3().setFromObject(instance);
                    instance.userData.anchorMinY = defaultBounds.min.y;
                    instance.userData.anchorMaxZ = defaultBounds.max.z;
                    instance.userData.modelItem = item;
                    this.instances.set(item, instance);
                    this.scene.add(instance);
                }
                this.redraw();
            });
        }
        const instance = this.instances.get(item);
        if (!instance) return false;
        instance.visible = true;
        const pose = entry.presentation || {};
        const rotation = this.rotations.get(item) || { yaw: 0, pitch: 0 };
        instance.rotation.order = 'XYZ';
        instance.rotation.set(THREE.MathUtils.degToRad(pose.pitch || 0) + rotation.pitch,
            THREE.MathUtils.degToRad(pose.yaw || 0) + rotation.yaw,
            THREE.MathUtils.degToRad(pose.roll || 0));
        instance.scale.setScalar(size);
        instance.position.set(0, 0, 0);
        // The default pose establishes placement once. Drag rotation changes only
        // orientation, never the model's center or its camera-depth offset.
        const depth = Math.min(5000, Math.max(0, instance.userData.anchorMaxZ * size));
        const baseline = 500 - y;
        instance.position.set(x + (x - 500) * depth / this.camera.position.z,
            baseline + (baseline - this.eyeY) * depth / this.camera.position.z -
                instance.userData.anchorMinY * size, -depth);
        return true;
    }
    finish(exponent = 0) {
        if (!this.renderer || this.disposed) return;
        const box = this.ctx.stage.getBoundingClientRect();
        const w = Math.max(1, box.width), h = Math.max(1, box.height);
        this.renderer.setSize(w, h, false);
        // Off-axis frustum matches SVG at z=0. The eye is at baseline height,
        // so grounded meshes share the same horizon at every depth.
        const view = this.ctx.stage.viewBox.baseVal;
        const scale = Math.min(w / view.width, h / view.height);
        const cx = view.x + view.width / 2, cy = 500 - view.y - view.height / 2;
        const eyeY = this.eyeY;
        const near = this.camera.near, distance = this.camera.position.z;
        let far = distance + 1000;
        for (const instance of this.instances.values()) {
            if (!instance?.visible) continue;
            const bounds = new THREE.Box3().setFromObject(instance);
            far = Math.max(far, distance - bounds.min.z + 100);
        }
        // A fixed 0.1..1e7 frustum made nearly coplanar fly parts flicker.
        // Tighten depth precision around the models actually on screen.
        this.camera.far = far;
        this.camera.position.set(cx,eyeY,distance);
        this.camera.projectionMatrix.makePerspective(-w/scale/2*near/distance,w/scale/2*near/distance,
            (cy+h/scale/2-eyeY)*near/distance,(cy-h/scale/2-eyeY)*near/distance,near,far);
        this.camera.projectionMatrixInverse.copy(this.camera.projectionMatrix).invert();
        this.camera.updateMatrixWorld(true);
        this.camera.matrixWorldInverse.copy(this.camera.matrixWorld).invert();
        this.hulls.clear();
        for (const [item, instance] of this.instances) {
            if (!instance?.visible) continue;
            instance.updateMatrixWorld(true);
            const projected = [];
            for (const point of instance.userData.pickPoints || []) {
                const ndc = point.clone().applyMatrix4(instance.matrixWorld).project(this.camera);
                if (!Number.isFinite(ndc.x) || !Number.isFinite(ndc.y) || ndc.z < -1 || ndc.z > 1) continue;
                projected.push({ x: (ndc.x + 1) * w / 2, y: (1 - ndc.y) * h / 2 });
            }
            const polygon = convexHull(projected);
            if (polygon.length >= 3) this.hulls.set(item, { item, polygon, depth: instance.position.z });
        }
        this.hovered = this.pointer && !this.draggingItem
            ? this.pick(this.pointer.x, this.pointer.y) : null;
        this.ctx.stageFrame.classList.toggle('is-model-hovered', Boolean(this.hovered));
        for (const [item, instance] of this.instances)
            for (const overlay of instance?.userData.hoverOverlays || [])
                overlay.visible = item === this.hovered && instance.visible;
        this.renderer.render(this.scene, this.camera);
    }
    dispose() {
        this.disposed = true;
        cancelAnimationFrame(this.returnFrame);
        this.renderer?.dispose();
        this.renderer?.forceContextLoss();
        this.renderer?.domElement.remove();
        for (const instance of this.instances.values())
            for (const overlay of instance?.userData.hoverOverlays || []) overlay.material.dispose();
        this.instances.clear();
    }
}
window.ScaleModels = { ModelStage, convexHull, insideHull };
window.dispatchEvent(new Event('scale-models-ready'));
