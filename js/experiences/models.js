import * as THREE from 'three';
import { GLTFLoader } from '../vendor/three/addons/loaders/GLTFLoader.js';
import { clone } from '../vendor/three/addons/utils/SkeletonUtils.js';

const models = new Map();
const registry = fetch('content/visualizations/models.json', { cache: 'no-store' })
    .then(r => r.ok ? r.json() : { models: [] }).catch(() => ({ models: [] }));
const loader = new GLTFLoader();
const proceduralLength = {
    'Hydrogen Atom': { id: 'hydrogen-1s', procedural: 'hydrogen-1s', geometry: 'mesh',
        presentation: { reference_size: 1, layout_width_factor: 6.8,
            focus_scale_factor: 6.6, display_extent_factor: 6.6 },
        basis_url: 'https://ocw.mit.edu/courses/5-111-principles-of-chemical-science-fall-2008/8a0da0346f1d611fbbd5c31a54865c2d_lecnotes06.pdf',
        note: 'Sampled 1s orbital. The listed Bohr radius is the most probable electron distance, not a hard edge.' },
    'Human Hair': { id: 'hair-fiber', procedural: 'hair-fiber', geometry: 'mesh',
        presentation: { measure_axis: 'x', layout_width_factor: 1.1 },
        basis_url: 'https://wellcomecollection.org/works/wxgqyf66',
        basis_label: 'Cuticle reference: Wellcome Collection',
        note: 'An illustrative scalp-hair fiber with overlapping cuticle ridges. Only its horizontal diameter is calibrated to the listed 100 micrometers; the cropped shaft length is not.' }
};

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
        for (let index = 0; index < 10500; index++) {
            const radius = -Math.log(random() * random() * random()) / 2;
            if (radius > 3.3) continue;
            const z = 2 * random() - 1, angle = 2 * Math.PI * random();
            const circle = Math.sqrt(1 - z * z);
            positions.push(radius * circle * Math.cos(angle), radius * circle * Math.sin(angle), radius * z);
        }
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        scene.add(new THREE.Points(geometry, new THREE.PointsMaterial({
            color: 0x2675ae, size: 2.2, sizeAttenuation: false,
            transparent: true, opacity: 0.32, depthWrite: false
        })));
    }
    return scene;
}

async function load(entry) {
    const key = entry.src || entry.id;
    if (!models.has(key)) models.set(key, (entry.procedural
        ? Promise.resolve({ scene: proceduralScene(entry.procedural) })
        : loader.loadAsync(entry.src)).then(gltf => {
        const scene = gltf.scene;
        for (const name of entry.presentation?.remove_nodes || []) scene.getObjectByName(name)?.removeFromParent();
        const preRotation = entry.presentation?.pre_rotation;
        if (preRotation) scene.rotation.set(
            THREE.MathUtils.degToRad(preRotation.x || 0),
            THREE.MathUtils.degToRad(preRotation.y || 0),
            THREE.MathUtils.degToRad(preRotation.z || 0)
        );
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
        if (entry.presentation && ['tint', 'color_gain', 'roughness', 'metalness', 'opaque', 'emissive']
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
        return normalized;
    }).catch(() => null));
    return models.get(key);
}
class ModelStage {
    constructor(ctx, redraw) {
        this.ctx = ctx; this.redraw = redraw; this.instances = new Map(); this.entries = [];
        this.rotations = new Map();
        try {
            this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
            this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
            this.renderer.domElement.className = 'experience-model-stage';
            this.renderer.domElement.setAttribute('aria-hidden', 'true');
            ctx.stageFrame.insertBefore(this.renderer.domElement, ctx.stage);
            this.scene = new THREE.Scene();
            this.raycaster = new THREE.Raycaster();
            this.scene.add(new THREE.HemisphereLight(0xffffff, 0x667788, 2));
            const light = new THREE.DirectionalLight(0xffffff, 2.5);
            light.position.set(-500, 800, 1500); this.scene.add(light);
            this.camera = new THREE.PerspectiveCamera(35, 2, 20, 1e8);
            this.camera.position.z = 8000;
            registry.then(data => { if (!this.disposed) { this.entries = data.models || []; redraw(); } });
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
        const point = new THREE.Vector2(2 * (clientX - rect.left) / rect.width - 1,
            1 - 2 * (clientY - rect.top) / rect.height);
        this.raycaster.setFromCamera(point, this.camera);
        const roots = [...this.instances.values()].filter(instance => instance?.visible);
        for (const hit of this.raycaster.intersectObjects(roots, true)) {
            let object = hit.object;
            while (object && !object.userData.modelItem) object = object.parent;
            if (object?.userData.modelItem) return object.userData.modelItem;
        }
        return null;
    }
    beginRotate(item) {
        const state = this.rotations.get(item) || { yaw: 0, pitch: 0, velocity: 0, pitchVelocity: 0 };
        state.dragging = true;
        state.velocity = 0;
        state.pitchVelocity = 0;
        this.rotations.set(item, state);
    }
    rotate(item, dx, dy = 0) {
        const state = this.rotations.get(item) || { yaw: 0, pitch: 0, velocity: 0, pitchVelocity: 0, dragging: true };
        state.yaw += dx * 0.008;
        state.pitch = THREE.MathUtils.clamp(state.pitch + dy * 0.006, -0.65, 0.65);
        this.rotations.set(item, state);
        this.redraw();
    }
    releaseRotate(item) {
        const state = this.rotations.get(item);
        if (!state) return;
        state.yaw = Math.atan2(Math.sin(state.yaw), Math.cos(state.yaw));
        state.dragging = false;
        state.releasedAt = performance.now();
        if (!this.returnFrame) this.returnFrame = requestAnimationFrame(now => this.returnToPose(now));
    }
    returnToPose(now) {
        this.returnFrame = null;
        if (this.disposed) return;
        const dt = Math.min(0.032, (now - (this.lastReturnFrame ?? now - 16)) / 1000);
        this.lastReturnFrame = now;
        let pending = false, changed = false;
        for (const state of this.rotations.values()) {
            if (state.dragging) continue;
            if (now - state.releasedAt < 180) { pending = true; continue; }
            const acceleration = -20 * state.yaw - 8.5 * state.velocity;
            state.velocity = THREE.MathUtils.clamp(state.velocity + acceleration * dt, -2.4, 2.4);
            state.yaw += state.velocity * dt;
            const pitchAcceleration = -20 * state.pitch - 8.5 * state.pitchVelocity;
            state.pitchVelocity = THREE.MathUtils.clamp(state.pitchVelocity + pitchAcceleration * dt, -2.4, 2.4);
            state.pitch += state.pitchVelocity * dt;
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
        this.renderer.render(this.scene, this.camera);
    }
    dispose() { this.disposed = true; cancelAnimationFrame(this.returnFrame); this.renderer?.dispose(); this.renderer?.forceContextLoss(); this.renderer?.domElement.remove(); this.instances.clear(); }
}
window.ScaleModels = { ModelStage };
window.dispatchEvent(new Event('scale-models-ready'));
