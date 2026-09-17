import * as THREE from 'three';
import { GLTFLoader } from '../vendor/three/addons/loaders/GLTFLoader.js';
import { clone } from '../vendor/three/addons/utils/SkeletonUtils.js';

const models = new Map();
const registry = fetch('content/visualizations/models.json').then(r => r.ok ? r.json() : { models: [] }).catch(() => ({ models: [] }));
const loader = new GLTFLoader();
async function load(entry) {
    if (!models.has(entry.src)) models.set(entry.src, loader.loadAsync(entry.src).then(gltf => {
        const scene = gltf.scene;
        scene.updateMatrixWorld(true);
        const bounds = new THREE.Box3().setFromObject(scene);
        const center = bounds.getCenter(new THREE.Vector3());
        const size = bounds.getSize(new THREE.Vector3());
        const group = new THREE.Group();
        scene.position.sub(center);
        group.add(scene);
        group.scale.setScalar(1 / Math.max(size.x, size.y, size.z));
        const normalized = new THREE.Group();
        normalized.add(group);
        normalized.userData.relativeHeight = size.y / Math.max(size.x, size.y, size.z);
        normalized.userData.relativeDepth = Math.hypot(size.x,size.z) / Math.max(size.x, size.y, size.z);
        return normalized;
    }).catch(() => null));
    return models.get(entry.src);
}
class ModelStage {
    constructor(ctx, redraw) {
        this.ctx = ctx; this.redraw = redraw; this.instances = new Map(); this.entries = [];
        try {
            this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
            this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
            this.renderer.domElement.className = 'experience-model-stage';
            this.renderer.domElement.setAttribute('aria-hidden', 'true');
            ctx.stageFrame.append(this.renderer.domElement);
            this.scene = new THREE.Scene();
            this.scene.add(new THREE.HemisphereLight(0xffffff, 0x667788, 2));
            const light = new THREE.DirectionalLight(0xffffff, 2.5);
            light.position.set(-500, 800, 1500); this.scene.add(light);
            this.camera = new THREE.PerspectiveCamera(35, 2, 0.1, 1e7);
            this.camera.position.z = 1200;
            registry.then(data => { if (!this.disposed) { this.entries = data.models || []; redraw(); } });
        } catch { this.unavailable = true; }
    }
    entry(item) { return this.entries.find(e => e.matches?.[this.ctx.dimension]?.includes(item.name)); }
    begin() { for (const instance of this.instances.values()) if (instance) instance.visible = false; }
    draw(item, x, y, size, yaw) {
        const entry = this.entry(item);
        if (!entry || this.unavailable || this.disposed) return false;
        if (!this.instances.has(item)) {
            this.instances.set(item, null);
            load(entry).then(model => {
                if (this.disposed) return;
                if (model) { const instance = clone(model); this.instances.set(item, instance); this.scene.add(instance); }
                this.redraw();
            });
        }
        const instance = this.instances.get(item);
        if (!instance) return false;
        instance.visible = true;
        // Keep the front of the model behind the reference plane; approaching it
        // changes perspective through its real depth, not an artificial yaw.
        const depth = size * instance.userData.relativeDepth / 2;
        instance.position.set(500 + (x-500)*(1+depth/this.camera.position.z),
            500 - y + size * instance.userData.relativeHeight / 2, -depth);
        instance.scale.setScalar(size);
        instance.rotation.y = yaw;
        return true;
    }
    finish() {
        if (!this.renderer || this.disposed) return;
        const box = this.ctx.stage.getBoundingClientRect();
        const w = Math.max(1, box.width), h = Math.max(1, box.height);
        this.renderer.setSize(w, h, false);
        // Off-axis frustum matches SVG at z=0. The eye is at baseline height,
        // so grounded meshes share the same horizon at every depth.
        const view = this.ctx.stage.viewBox.baseVal;
        const scale = Math.min(w / view.width, h / view.height);
        const cx = view.x + view.width / 2, cy = 500 - view.y - view.height / 2;
        const eyeY = 500 - (globalThis.ScaleJourney?.BASELINE ?? 340);
        const near = this.camera.near, distance = this.camera.position.z;
        this.camera.position.set(cx,eyeY,distance);
        this.camera.projectionMatrix.makePerspective(-w/scale/2*near/distance,w/scale/2*near/distance,
            (cy+h/scale/2-eyeY)*near/distance,(cy-h/scale/2-eyeY)*near/distance,near,this.camera.far);
        this.camera.projectionMatrixInverse.copy(this.camera.projectionMatrix).invert();
        this.renderer.render(this.scene, this.camera);
    }
    dispose() { this.disposed = true; this.renderer?.dispose(); this.renderer?.forceContextLoss(); this.renderer?.domElement.remove(); this.instances.clear(); }
}
window.ScaleModels = { ModelStage };
window.dispatchEvent(new Event('scale-models-ready'));
