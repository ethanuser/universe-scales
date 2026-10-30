import * as THREE from 'three';
import { GLTFLoader } from '../vendor/three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from '../vendor/three/addons/utils/BufferGeometryUtils.js';
import { clone } from '../vendor/three/addons/utils/SkeletonUtils.js';
import { RoomEnvironment } from '../vendor/three/addons/environments/RoomEnvironment.js';
import { placeLabels, resolveLabelCollisions } from './model-labels.js?v=fb897a2b3a';
import { SCREEN_LINE_PX, addDistanceBracket, moleculeScene, proceduralLength, proceduralScene } from './procedural-models.js?v=de09502a31';
import { waveAnimation } from './wave-models.js?v=d9360c0030';
import './neuron-animation.js?v=a744312505';
import { prepareModelPoints } from './model-points.js?v=c77d6e1266';
import { angularEntry, angularScene } from './angular-models.js?v=d1fdf1228b';
import { orbitalAssets, orbitalEntry } from './angular-orbits.js?v=b50491e0cc';
import { createAngularRig, angularSweepBounds } from './angular-rig.js?v=8f269aade6';
import { ModelCache } from './model-cache.js?v=1f3b449d69';
import { modelBytes, retainModelResources, releaseModelResources } from './model-resources.js?v=75ad13d002';

const MIB = 1024 * 1024;
const models = new ModelCache({ maxEntries: 64, maxBytes: 192 * MIB,
    measure: modelBytes, dispose: releaseModelResources });
const sourceQueue = [];
let sourceLoads = 0;
function queueSource(key, create) {
    const pump = () => {
        while (sourceLoads < 4 && sourceQueue.length) {
            const task = sourceQueue.shift();
            if (!models.records.get(task.key)?.pins) { task.resolve(null); continue; }
            sourceLoads++;
            Promise.resolve().then(task.create).then(task.resolve, task.reject).finally(() => {
                sourceLoads--; pump();
            });
        }
    };
    return new Promise((resolve, reject) => {
        sourceQueue.push({ key, create, resolve, reject });
        // acquire() installs the lease pin before a queued load can start.
        Promise.resolve().then(pump);
    });
}
const registry = fetch('content/visualizations/models.json', { cache: 'no-cache' })
    .then(r => r.ok ? r.json() : { models: [] }).catch(() => ({ models: [] }));
const moleculeData = fetch('content/visualizations/molecules.json', { cache: 'no-cache' })
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
        if (child.isMesh || child.isPoints || child.isLine) {
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
        if ((child.isMesh || child.isPoints) && !child.userData.screenLine
            && child.userData.hoverOverlay !== false) originals.push(child);
    });
    return originals.map(child => {
        const overlay = child.clone(false);
        // Keep point-size animation, but not labels, outlines or picking metadata.
        overlay.userData = child.isPoints && child.userData.pointSize
            ? { pointSize: { ...child.userData.pointSize } } : {};
        overlay.material = child.isPoints
            ? new THREE.PointsMaterial({ color: 0xffffff, size: child.material.size,
                sizeAttenuation: child.material.sizeAttenuation, transparent: true,
                opacity: 0.16, depthWrite: false, map: child.material.map,
                alphaTest: child.material.alphaTest })
            : new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true,
                opacity: 0.16, depthWrite: false, polygonOffset: true,
                polygonOffsetFactor: -1, polygonOffsetUnits: -1 });
        overlay.visible = false;
        overlay.renderOrder = child.renderOrder + 1;
        child.parent.add(overlay);
        return overlay;
    });
}
// Quantized (KHR_mesh_quantization) attributes are normalized integers; baking
// a node transform into them clamps every coordinate to +/-1. Merge in floats.
function dequantized(geometry) {
    for (const [name, attribute] of Object.entries(geometry.attributes)) {
        if (!attribute.normalized && attribute.array instanceof Float32Array && !attribute.isInterleavedBufferAttribute) continue;
        const values = new Float32Array(attribute.count * attribute.itemSize);
        for (let index = 0; index < attribute.count; index++)
            for (let component = 0; component < attribute.itemSize; component++)
                values[index * attribute.itemSize + component] = attribute.getComponent(index, component);
        geometry.setAttribute(name, new THREE.BufferAttribute(values, attribute.itemSize));
    }
    return geometry;
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
        const geometry = dequantized(child.geometry.clone());
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
function acquireModel(entry) {
    // Entries may share a GLB but differ in presentation (e.g. a recolored Sun).
    const key = entry.id || entry.src;
    return models.acquire(key, () => queueSource(key, () => (entry.procedural === 'molecule'
        ? moleculeData.then(data => data?.models?.[entry.molecule]
            ? { scene: moleculeScene(data.models[entry.molecule]) } : null)
        : entry.procedural ? Promise.resolve({ scene: entry.procedural === 'angular-machine'
            ? angularScene(entry.angular_kind) : proceduralScene(entry.procedural, entry) })
            // The content hash busts browser caches whenever a model file changes.
            : loader.loadAsync(entry.sha256 ? `${entry.src}?v=${entry.sha256.slice(0, 12)}` : entry.src)).then(gltf => {
        if (!gltf) return null;
        let scene = gltf.scene;
        const original = retainModelResources(scene);
        try {
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
            prepareModelPoints(scene);
            if (entry.presentation?.distance_bracket) addDistanceBracket(scene, entry.presentation.distance_bracket);
            scene.updateMatrixWorld(true);
            // Precise (per-vertex) bounds: box-of-rotated-box estimates inflate
            // calibration for rotated nodes and would mis-size the model.
            const bounds = new THREE.Box3().setFromObject(scene, true);
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
            if (entry.presentation && ['tint', 'color_gain', 'roughness', 'metalness', 'opaque', 'double_sided', 'emissive', 'environment']
                .some(key => key in entry.presentation)) {
                normalized.traverse(child => {
                    // Glowing meshes carry a shader hook that Material.clone() would drop.
                    if (!child.isMesh || child.userData.additive) return;
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
                        // Metals need something to reflect; ModelStage attaches its room map.
                        if (entry.presentation.environment) material.userData.environment = entry.presentation.environment;
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
            return retainModelResources(normalized);
        } finally { releaseModelResources(original); }
    }).catch(() => null)));
}

export class ModelStage {
    constructor(ctx, redraw, onRegistryReady) {
        this.ctx = ctx; this.redraw = redraw; this.instances = new Map(); this.entries = [];
        this.registryReady = false;
        this.entryCache = new WeakMap();
        this.rotations = new Map(); this.hulls = new Map();
        this.activeLeases = new Map(); this.prefetchLeases = new Map(); this.usedItems = new Set();
        this.loadingSources = new Set();
        this.sourceLeases = new WeakMap(); this.instanceMaterials = new WeakMap();
        this.modelCosts = new WeakMap(); this.failedUntil = new WeakMap();
        this.warmAbort = new AbortController();
        this.coarsePointer = window.matchMedia('(pointer: coarse)').matches;
        this.cacheLimits = { maxEntries: this.coarsePointer ? 20 : 32, maxBytes: (this.coarsePointer ? 48 : 96) * MIB };
        this.instanceCache = new ModelCache({ ...this.cacheLimits,
            measure: instance => this.modelCosts.get(instance.userData.modelItem) || 0,
            dispose: instance => this.disposeInstance(instance) });
        if (this.coarsePointer) models.setLimits({ maxEntries: 40, maxBytes: 96 * MIB });
        this.waveStart = performance.now();
        try {
            this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
            // Checking compile logs forces every new shader to finish compiling synchronously,
            // which was most of the stall when models appear. Without it, warm (below)
            // compiles in parallel. Add ?shaderchecks to the URL to debug shaders.
            this.renderer.debug.checkShaderErrors = /[?&]shaderchecks\b/.test(location.search);
            if (ctx.dimension === 'angular-velocity') {
                this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
                this.renderer.toneMappingExposure = 0.85;
            }
            this.maxPixelRatio = Math.min(devicePixelRatio, this.coarsePointer ? 1.5 : 2);
            this.pixelRatio = this.maxPixelRatio;
            this.frameIntervals = [];
            this.renderer.setPixelRatio(this.pixelRatio);
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
                this.entryCache = new WeakMap();
                this.registryReady = true;
                this.ctx.updateDetail();
                onRegistryReady?.();
                redraw();
            });
        } catch { this.unavailable = true; }
    }
    environment() {
        if (!this.environmentMap) {
            const generator = new THREE.PMREMGenerator(this.renderer);
            const room = new RoomEnvironment();
            this.environmentMap = generator.fromScene(room, 0.04).texture;
            room.dispose();
            generator.dispose();
        }
        return this.environmentMap;
    }
    entry(item) {
        // Wait for sourced entries before caching a procedural fallback. An
        // early fallback otherwise survives after the registry has arrived.
        if (this.ctx.dimension === 'angular-velocity' && !this.registryReady) return null;
        if (this.orbitEntries?.has(item)) return this.orbitEntries.get(item);
        if (this.entryCache.has(item)) return this.entryCache.get(item);
        const entry = this.ctx.dimension === 'angular-velocity'
            ? orbitalEntry(item, this.entries) || angularEntry(item, this.entries)
            : (this.ctx.dimension === 'length' && proceduralLength[item.name]) ||
                this.entries.find(e => e.matches?.[this.ctx.dimension]?.includes(item.name));
        // Layout asks for each item's presentation several times per frame.
        // Do not cache misses until the asynchronous registry has arrived.
        if (this.registryReady) this.entryCache.set(item, entry);
        return entry;
    }
    queueLoadRedraw() {
        if (this.loadFrame || this.disposed) return;
        this.loadFrame = requestAnimationFrame(() => {
            this.loadFrame = null;
            if (!this.disposed) this.redraw();
        });
    }
    orbitalBodies(item) {
        if (this.ctx.dimension !== 'angular-velocity') return null;
        this.orbitItems ||= new Map();
        this.orbitEntries ||= new Map();
        if (!this.orbitItems.has(item)) {
            const assets = orbitalAssets(item, this.entries);
            if (!assets) return null;
            const body = { name: item.name }, center = { name: assets.centerName };
            // Distinct identities prevent two comparison lanes from moving the
            // same instance. Geometry loading still shares the source asset.
            this.orbitEntries.set(body, { ...assets.body, angular_motion: undefined });
            this.orbitEntries.set(center, { ...assets.center, angular_motion: undefined });
            this.orbitItems.set(item, { body, center });
        }
        return this.orbitItems.get(item);
    }
    drawOrbit(item, x, y, bodyX, bodyY) {
        const bodies = this.orbitalBodies(item);
        if (!bodies) return { center: false, body: false };
        return {
            center: this.draw(bodies.center, x, y, 62, undefined, true),
            body: this.draw(bodies.body, bodyX, bodyY, item.name === 'ISS orbit' ? 68 : 48, undefined, true)
        };
    }
    pick(clientX, clientY) {
        if (!this.renderer || this.disposed) return null;
        const rect = this.renderer.domElement.getBoundingClientRect();
        if (!rect.width || !rect.height || clientX < rect.left || clientX > rect.right ||
            clientY < rect.top || clientY > rect.bottom) return null;
        const point = { x: clientX - rect.left, y: clientY - rect.top };
        return [...this.hulls.values()]
            .filter(hull => (!hull.circle || Math.hypot(point.x - hull.circle.x, point.y - hull.circle.y) <= hull.circle.r) &&
                hull.polygon.length >= 3 && insideHull(point, hull.polygon))
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
        // Pointer events can arrive faster than display frames. Keep every motion
        // sample for release momentum, but only draw the latest pose once per frame.
        if (!this.inputFrame) this.inputFrame = requestAnimationFrame(() => {
            this.inputFrame = null;
            if (!this.disposed) this.redraw();
        });
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
        cancelAnimationFrame(this.inputFrame);
        this.inputFrame = null;
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
    begin(exponent = 0, eyeY) {
        // A camera/input frame already includes any models that just loaded.
        cancelAnimationFrame(this.loadFrame);
        this.loadFrame = null;
        this.usedItems.clear();
        // Radial layouts pass the screen center: objects sit above and below it.
        this.eyeY = eyeY ?? 500 - (globalThis.ScaleJourney?.BASELINE ?? 405)
            + 130 * THREE.MathUtils.clamp((exponent + 1) / 7, 0, 1);
        for (const instance of this.instances.values()) if (instance) instance.visible = false;
    }
    // Start loading an item's model without drawing it, so it is parsed, on the GPU and
    // ready by the time it scrolls or zooms into view. Returns true once it is ready.
    prefetch(item) {
        const entry = this.entry(item);
        if (!entry || this.unavailable || this.disposed) return false;
        this.ensure(item, entry, false);
        return !!this.instances.get(item);
    }
    // Models currently fetching or parsing; callers throttle prefetching with it.
    get pending() { return this.pendingLoads || 0; }
    estimatedCost(item) {
        return this.modelCosts.get(item) ?? Math.max(MIB, (this.entry(item)?.bytes || 0) * 8);
    }
    cacheStats() {
        return { instances: this.instanceCache.stats(), sources: models.stats(),
            gpu: { ...this.renderer?.info.memory } };
    }
    setCacheLimits({ instances, sources } = {}) {
        if (instances) {
            Object.assign(this.cacheLimits, instances);
            this.instanceCache.setLimits(this.cacheLimits);
        }
        if (sources) models.setLimits(sources);
    }
    ensure(item, entry, active = true) {
        if (this.disposed || (this.failedUntil.get(item) || 0) > Date.now()) return;
        const leases = active ? this.activeLeases : this.prefetchLeases;
        if (leases.has(item)) { leases.get(item).touch(); return; }
        const lease = this.instanceCache.acquire(item, () => this.loadInstance(item, entry));
        leases.set(item, lease);
        if (!active) {
            const release = () => {
                if (leases.get(item) === lease) leases.delete(item);
                lease.release();
            };
            lease.promise.then(release, release);
        }
    }
    async loadInstance(item, entry) {
        this.pendingLoads = (this.pendingLoads || 0) + 1;
        this.instances.set(item, null);
        const source = acquireModel(entry);
        this.loadingSources.add(source);
        let instance;
        try {
            const model = await source.promise;
            if (!model || this.disposed) {
                if (!model) this.failedUntil.set(item, Date.now() + 30000);
                source.release(); return null;
            }
            instance = clone(model);
            this.sourceLeases.set(instance, source);
            this.modelCosts.set(item, modelBytes(model));
            instance.userData.waveRoots = waveAnimation.animationRoots(instance);
            instance.userData.pickPoints = sampledModelPoints(instance);
            instance.userData.hoverOverlays = addHoverOverlay(instance);
            if (entry.angular_motion) {
                instance.userData.angularRig = createAngularRig(instance, entry.angular_motion);
            }
            const pose = entry.presentation || {};
            instance.rotation.order = 'XYZ';
            instance.rotation.set(THREE.MathUtils.degToRad(pose.pitch || 0),
                THREE.MathUtils.degToRad(pose.yaw || 0), THREE.MathUtils.degToRad(pose.roll || 0));
            if (instance.userData.angularRig)
                instance.userData.axialPose = instance.userData.angularRig.faceCamera(entry.angular_motion.view_side, entry.angular_motion.view_tilt);
            instance.updateMatrixWorld(true);
            // Precise bounds so rotated poses sit on the ground instead of floating.
            const defaultBounds = instance.userData.angularRig
                ? angularSweepBounds(instance, instance.userData.angularRig)
                : new THREE.Box3().setFromObject(instance, true);
            instance.userData.restExtent = defaultBounds.getSize(new THREE.Vector3());
            // Radius (model units) of a sphere around the origin that contains the
            // model in any orientation. Clip planes use it: per-frame boxes can be
            // stale for skinned meshes, letting a turned model cross the near plane.
            instance.userData.boundRadius = Math.max(...[0, 1].flatMap(i => [0, 1].flatMap(j => [0, 1].map(k =>
                new THREE.Vector3(i ? defaultBounds.max.x : defaultBounds.min.x, j ? defaultBounds.max.y : defaultBounds.min.y,
                    k ? defaultBounds.max.z : defaultBounds.min.z).length()))));
            instance.userData.anchorMinY = defaultBounds.min.y;
            instance.userData.anchorMaxZ = defaultBounds.max.z;
            // Environment maps belong to this renderer, not the cached source.
            const localMaterials = new Map();
            instance.traverse(child => {
                if (!child.material) return;
                const local = material => {
                    if (!material?.userData.environment) return material;
                    if (!localMaterials.has(material)) {
                        const made = material.clone();
                        made.envMap = this.environment();
                        made.envMapIntensity = material.userData.environment;
                        localMaterials.set(material, made);
                    }
                    return localMaterials.get(material);
                };
                child.material = Array.isArray(child.material) ? child.material.map(local) : local(child.material);
            });
            this.instanceMaterials.set(instance, [...localMaterials.values()]);
            instance.userData.modelItem = item;
            instance.userData.modelEntryId = entry.id;
            Object.assign(instance.userData, { screenLines: [], overlays: [], clouds: [] });
            instance.traverse(child => {
                if (child.userData.screenLine) instance.userData.screenLines.push(child);
                if (child.userData.label || child.userData.outline) instance.userData.overlays.push(child);
                if (child.userData.pointSize) instance.userData.clouds.push(child);
            });
            instance.visible = false;
            this.scene.add(instance);
            await this.warm(instance);
            if (!this.disposed) this.instances.set(item, instance);
            return instance;
        } catch (error) {
            console.warn(`Cannot load ${entry.id}: ${error.message}`);
            this.failedUntil.set(item, Date.now() + 30000);
            if (instance) this.disposeInstance(instance);
            else source.release();
            return null;
        } finally {
            this.loadingSources.delete(source);
            this.pendingLoads--;
            this.queueLoadRedraw();
        }
    }
    // Dynamic resolution: while frames arrive back to back (zooming, rotating), watch
    // their spacing. Below ~40 fps drop the pixel ratio a step (never under 1); once
    // frames keep up again, restore it. Idle redraws are ignored.
    adaptResolution() {
        const now = performance.now();
        const gap = now - (this.lastFrameAt ?? -Infinity);
        this.lastFrameAt = now;
        if (gap > 250) return;
        this.frameIntervals.push(gap);
        if (this.frameIntervals.length < 12) return;
        const sorted = [...this.frameIntervals].sort((a, b) => a - b);
        const median = sorted[sorted.length >> 1];
        this.frameIntervals = [];
        let next = this.pixelRatio;
        if (median > 25 && next > 1) next = Math.max(1, next - 0.25);
        else if (median < 18 && next < this.maxPixelRatio) next = Math.min(this.maxPixelRatio, next + 0.25);
        if (next === this.pixelRatio) return;
        this.pixelRatio = next;
        this.renderer.setPixelRatio(next);
        this.renderer.setSize(this.viewportWidth, this.viewportHeight, false);
    }
    // Upload textures and compile shaders while the instance is still hidden; doing it on
    // the first visible frame stalls that frame and makes the model visibly pop in.
    async warm(instance) {
        try {
            instance.traverse(child => {
                for (const material of [child.material].flat()) {
                    if (!material) continue;
                    for (const value of Object.values(material))
                        if (value?.isTexture) this.renderer.initTexture(value);
                }
            });
            instance.visible = true;
            const materials = this.renderer.compile(instance, this.camera, this.scene);
            instance.visible = false;
            // The vendored compileAsync polls disposed material properties after a
            // mode switch. Use the same readiness check with cancellable polling.
            await new Promise(resolve => {
                const signal = this.warmAbort.signal;
                let timeout;
                const started = performance.now();
                const done = () => { clearTimeout(timeout); signal.removeEventListener('abort', done); resolve(); };
                const poll = () => {
                    if (signal.aborted || performance.now() - started > 5000) { done(); return; }
                    for (const material of materials) {
                        const program = this.renderer.properties.get(material).currentProgram;
                        if (!program || program.isReady()) materials.delete(material);
                    }
                    if (materials.size) timeout = setTimeout(poll, 10);
                    else done();
                };
                signal.addEventListener('abort', done, { once: true });
                poll();
            });
        } catch { instance.visible = false; }
    }
    draw(item, x, y, size, phase, centered = false) {
        const entry = this.entry(item);
        if (!entry || this.unavailable || this.disposed) return false;
        this.usedItems.add(item);
        this.ensure(item, entry);
        const instance = this.instances.get(item);
        if (!instance) return false;
        if (phase != null) instance.userData.angularRig?.setPhase(phase);
        instance.visible = true;
        if (entry.angular_motion) {
            const extent = instance.userData.restExtent;
            size = Math.min(size, 240 / extent.y, 310 / extent.x);
        }
        if (centered) {
            const extent = instance.userData.restExtent;
            size /= Math.max(extent.x, extent.y);
            y += extent.y * size / 2;
        }
        const pose = entry.presentation || {};
        const rotation = this.rotations.get(item) || { yaw: 0, pitch: 0 };
        instance.rotation.order = 'XYZ';
        instance.rotation.set(THREE.MathUtils.degToRad(pose.pitch || 0) + rotation.pitch,
            THREE.MathUtils.degToRad(pose.yaw || 0) + rotation.yaw,
            THREE.MathUtils.degToRad(pose.roll || 0));
        if (instance.userData.axialPose) instance.quaternion.copy(instance.userData.axialPose);
        instance.scale.setScalar(size);
        instance.userData.drawSize = size;
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
        const box = this.ctx.stage._size || this.ctx.stage.getBoundingClientRect();
        const w = Math.max(1, box.width), h = Math.max(1, box.height);
        if (this.viewportWidth !== w || this.viewportHeight !== h) {
            this.renderer.setSize(w, h, false);
            this.viewportWidth = w; this.viewportHeight = h;
        }
        // Off-axis frustum matches SVG at z=0. The eye is at baseline height,
        // so grounded meshes share the same horizon at every depth.
        const view = this.ctx.stage.viewBox.baseVal;
        const scale = Math.min(w / view.width, h / view.height);
        const cx = view.x + view.width / 2, cy = 500 - view.y - view.height / 2;
        const eyeY = this.eyeY;
        const distance = this.camera.position.z;
        let far = distance + 1000, nearest = Infinity;
        for (const instance of this.instances.values()) {
            if (!instance?.visible) continue;
            const radius = (instance.userData.boundRadius ?? 1) * instance.scale.x * 1.02;
            far = Math.max(far, distance - (instance.position.z - radius) + 100);
            nearest = Math.min(nearest, distance - (instance.position.z + radius));
        }
        // A fixed 0.1..1e7 frustum made nearly coplanar parts flicker (fly wings,
        // painted lines on a field). The eye sits thousands of units back, so the
        // near plane can sit just in front of the closest model: depth precision
        // grows about with near, which removes z-fighting on thin decals.
        const near = Math.max(20, Math.min(nearest - 20, far / 4));
        this.camera.near = near;
        this.camera.far = far;
        this.camera.position.set(cx,eyeY,distance);
        this.camera.projectionMatrix.makePerspective(-w/scale/2*near/distance,w/scale/2*near/distance,
            (cy+h/scale/2-eyeY)*near/distance,(cy-h/scale/2-eyeY)*near/distance,near,far);
        this.camera.projectionMatrixInverse.copy(this.camera.projectionMatrix).invert();
        this.camera.updateMatrixWorld(true);
        this.camera.matrixWorldInverse.copy(this.camera.matrixWorld).invert();
        const viewProjection = new THREE.Matrix4().multiplyMatrices(this.camera.projectionMatrix, this.camera.matrixWorldInverse);
        this.hulls.clear();
        let visibleWave = false;
        const animateWaves = !document.hidden && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        // Screen-space size of one world unit at a given camera depth.
        const pixelsPerUnit = depth => this.camera.projectionMatrix.elements[5] * h / 2 / depth;
        for (const [item, instance] of this.instances) {
            if (!instance?.visible) continue;
            if (instance.userData.waveRoots.length) {
                visibleWave = true;
                const elapsed = this.animationTime ?? (performance.now() - this.waveStart) / 1000;
                if (animateWaves || this.animationTime != null)
                    for (const root of instance.userData.waveRoots) waveAnimation.update(root, elapsed);
            }
            instance.updateMatrixWorld(true);
            if (instance.userData.screenLines.length) {
                const perPixel = 1 / pixelsPerUnit(distance - instance.position.z);
                for (const line of instance.userData.screenLines) {
                    const thickness = (line.userData.screenLine.width ?? SCREEN_LINE_PX) * perPixel / line.parent.matrixWorld.getMaxScaleOnAxis();
                    const { axis, length } = line.userData.screenLine;
                    line.scale.set(axis === 'x' ? length : thickness, axis === 'y' ? length : thickness,
                        axis === 'z' ? length : thickness);
                }
                instance.updateMatrixWorld(true);
            }
            // Point clouds shrink with the model instead of staying a fixed-size smudge.
            const drawnPixels = instance.userData.drawSize * scale;
            for (const cloud of instance.userData.clouds) {
                const { max, perPixel, conserve } = cloud.userData.pointSize;
                const wanted = drawnPixels * perPixel;
                cloud.material.size = THREE.MathUtils.clamp(wanted, 0.35, max);
                const count = cloud.geometry.attributes.position.count;
                let drawn = count;
                if (cloud.userData.pointLOD) {
                    const { fullPixels, minimum, mobileMaximum = Infinity } = cloud.userData.pointLOD;
                    drawn = Math.min(count, this.coarsePointer ? mobileMaximum : Infinity, Math.max(minimum,
                        Math.ceil(count * Math.min(1, drawnPixels / fullPixels))));
                    cloud.geometry.setDrawRange(0, drawn);
                }
                // Glowing gas (extras pointSize.conserve) keeps its calibrated brightness
                // when sprites hit their size cap or the LOD draws fewer of them.
                if (conserve) {
                    cloud.userData.baseOpacity ??= cloud.material.opacity;
                    const gain = Math.max(1, wanted / cloud.material.size) ** 2 * count / drawn;
                    cloud.material.opacity = cloud.userData.baseOpacity * Math.min(gain, 8);
                }
            }
            this.overlay(instance, w, h, scale, cx, view);
            // Pick outlines are projected lazily: only when the pointer is inside a model's
            // bounding circle. Reprojecting every model on every zoom frame was the costliest
            // script work while zooming.
            const matrix = new THREE.Matrix4().multiplyMatrices(viewProjection, instance.matrixWorld);
            const center = new THREE.Vector3().setFromMatrixPosition(instance.matrixWorld).applyMatrix4(viewProjection);
            const radius = (instance.userData.boundRadius ?? 1) * instance.scale.x * 1.05 *
                pixelsPerUnit(Math.max(1, distance - instance.position.z - (instance.userData.boundRadius ?? 1) * instance.scale.x));
            this.hulls.set(item, {
                item, depth: instance.position.z,
                circle: { x: (center.x + 1) * w / 2, y: (1 - center.y) * h / 2, r: radius },
                get polygon() {
                    let cache = instance.userData.projectedHull;
                    if (!cache || cache.width !== w || cache.height !== h || !cache.matrix.equals(matrix)) {
                        const projected = [], ndc = new THREE.Vector3();
                        for (const point of instance.userData.pickPoints || []) {
                            ndc.copy(point).applyMatrix4(matrix);
                            if (!Number.isFinite(ndc.x) || !Number.isFinite(ndc.y) || ndc.z < -1 || ndc.z > 1) continue;
                            projected.push({ x: (ndc.x + 1) * w / 2, y: (1 - ndc.y) * h / 2 });
                        }
                        cache = { width: w, height: h, matrix, polygon: convexHull(projected) };
                        instance.userData.projectedHull = cache;
                    }
                    return cache.polygon;
                }
            });
        }
        this.hovered = this.pointer && !this.draggingItem
            ? this.pick(this.pointer.x, this.pointer.y) : null;
        this.ctx.stageFrame.classList.toggle('is-model-hovered', Boolean(this.hovered));
        for (const [item, instance] of this.instances)
            for (const overlay of instance?.userData.hoverOverlays || [])
                overlay.visible = item === this.hovered && instance.visible;
        resolveLabelCollisions(this.ctx.stage);
        this.adaptResolution();
        this.renderer.render(this.scene, this.camera);
        for (const [item, lease] of this.activeLeases) {
            if (this.usedItems.has(item)) continue;
            this.activeLeases.delete(item);
            lease.release();
        }
        if (visibleWave && animateWaves && this.animationTime == null && !this.waveFrame)
            this.waveFrame = requestAnimationFrame(() => {
                this.waveFrame = null;
                if (!this.disposed) this.redraw();
            });
        else if ((!visibleWave || !animateWaves || this.animationTime != null) && this.waveFrame) {
            cancelAnimationFrame(this.waveFrame);
            this.waveFrame = null;
        }
    }
    // Labels and outlines are SVG drawn at projected node positions, so text
    // stays upright and lines stay thin while the model rotates underneath.
    overlay(instance, w, h, scale, cx, view) {
        if (!instance.userData.overlays.length) return;
        // Annotations fade out well before their model does, so zooming away
        // leaves clean objects (many share the radial view): fully visible above
        // 320 px, gone below 180 px.
        const drawnPixels = instance.userData.drawSize * scale;
        const opacity = THREE.MathUtils.clamp((drawnPixels - 180) / 140, 0, 1);
        if (!opacity && !instance.userData.overlays.some(node => node.userData.labelRole === 'dimension')) return;
        const toScreen = point => {
            const ndc = point.project(this.camera);
            return { x: cx + (ndc.x * w / 2) / scale, y: view.y + view.height / 2 - (ndc.y * h / 2) / scale };
        };
        const svgNode = (name, attributes) => {
            const node = document.createElementNS('http://www.w3.org/2000/svg', name);
            for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
            this.ctx.stage.append(node);
            return node;
        };
        const stableLabels = [];
        for (const node of instance.userData.overlays) {
            const dimension = node.userData.labelRole === 'dimension';
            const fontPixels = Math.min(13, drawnPixels * 0.032);
            const labelOpacity = dimension ? THREE.MathUtils.clamp((fontPixels - 2) / 3, 0, 1) : opacity;
            if (!labelOpacity) continue;
            const center = node.getWorldPosition(new THREE.Vector3());
            const at = toScreen(center.clone());
            let radius = 0;
            if (node.userData.sphere) {
                const top = toScreen(center.add(new THREE.Vector3(0, node.matrixWorld.getMaxScaleOnAxis(), 0)));
                radius = Math.abs(at.y - top.y);
            }
            if (node.userData.outline) {
                radius = Math.max(radius + (node.userData.markerPadding ?? 1.5) / scale,
                    (node.userData.markerRadius ?? 3.5) / scale);
                svgNode('circle', { cx: at.x, cy: at.y, r: radius, class: 'journey-model-outline', opacity });
            }
            if (node.userData.label) {
                // A depth annotation is useful side-on, but unreadable end-on.
                const labelAxis = node.userData.labelAxis;
                if (labelAxis) {
                    const end = new THREE.Vector3();
                    end[labelAxis.axis] = labelAxis.length;
                    const projected = toScreen(end.applyMatrix4(node.matrixWorld));
                    if (Math.hypot(projected.x - at.x, projected.y - at.y) * scale
                        < (labelAxis.minPixelLength ?? 10)) continue;
                }
                if (node.userData.labelLayout === 'orbit') {
                    stableLabels.push({ x: at.x, y: at.y, text: node.userData.label,
                        priority: node.userData.labelPriority, offset: radius + 4 / scale,
                        callout: node.userData.labelOffset && { x: node.userData.labelOffset.x / scale,
                            y: node.userData.labelOffset.y / scale } });
                    continue;
                }
                const offset = node.userData.labelOffset || { x: 0, y: 0 };
                const label = svgNode('text', { x: at.x + offset.x / scale,
                    y: at.y - radius + (offset.y - (radius ? 6 : 0)) / scale,
                    class: `journey-model-label ${node.userData.labelClass || ''}`, 'text-anchor': 'middle', opacity: labelOpacity });
                if (dimension) {
                    label.style.fontSize = `${fontPixels / scale}px`;
                    label.dataset.labelPriority = '80';
                }
                label.textContent = node.userData.label;
                if (node.userData.labelVector) {
                    const group = svgNode('g', { 'data-label-group': '' });
                    group.append(label);
                    // Vector hat: a short right-pointing arrow centered over the text.
                    const x = at.x, y = at.y - radius - (radius ? 6 : 0) / scale - 12;
                    group.append(svgNode('path', { d: `M${x - 5.5} ${y}H${x + 5.5}M${x + 2.5} ${y - 3}L${x + 5.5} ${y}L${x + 2.5} ${y + 3}`,
                        class: `journey-model-vector ${node.userData.labelClass || ''}`, opacity }));
                }
            }
        }
        for (const label of placeLabels(stableLabels, {
            left: view.x + 4, right: view.x + view.width - 4, top: view.y + 4, bottom: view.y + view.height - 4
        })) {
            if (!label.visible) continue;
            const group = svgNode('g', { 'data-label-group': '' });
            if (label.callout)
                group.append(svgNode('line', { x1: label.x, y1: label.y, x2: label.labelX,
                    y2: label.labelY + 3, class: 'journey-model-leader', opacity: opacity * 0.55 }));
            const text = svgNode('text', { x: label.labelX, y: label.labelY,
                class: 'journey-model-label', 'text-anchor': 'middle', opacity });
            text.textContent = label.text;
            group.append(text);
        }
    }
    disposeInstance(instance) {
        const item = instance.userData.modelItem;
        instance.removeFromParent();
        if (this.instances.get(item) === instance) this.instances.delete(item);
        this.hulls.delete(item);
        this.rotations.delete(item);
        for (const overlay of instance.userData.hoverOverlays || []) overlay.material.dispose();
        for (const material of this.instanceMaterials.get(instance) || []) material.dispose();
        instance.traverse(node => { if (node.isSkinnedMesh) node.skeleton?.dispose(); });
        this.sourceLeases.get(instance)?.release();
        this.sourceLeases.delete(instance);
    }
    dispose() {
        this.disposed = true;
        cancelAnimationFrame(this.returnFrame);
        cancelAnimationFrame(this.waveFrame);
        cancelAnimationFrame(this.inputFrame);
        cancelAnimationFrame(this.loadFrame);
        this.warmAbort.abort();
        for (const lease of this.loadingSources) lease.release();
        this.loadingSources.clear();
        for (const lease of [...this.activeLeases.values(), ...this.prefetchLeases.values()]) lease.release();
        this.activeLeases.clear(); this.prefetchLeases.clear();
        this.instanceCache.setLimits({ maxEntries: 0, maxBytes: 0 });
        this.environmentMap?.dispose();
        this.renderer?.dispose();
        this.renderer?.forceContextLoss();
        this.renderer?.domElement.remove();
        this.instances.clear();
        this.orbitItems?.clear();
        this.orbitEntries?.clear();
    }
}
window.ScaleModels = { ModelStage, convexHull, insideHull };
window.dispatchEvent(new Event('scale-models-ready'));
