import * as THREE from 'three';
import { GLTFLoader } from '../vendor/three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from '../vendor/three/addons/utils/BufferGeometryUtils.js';
import { clone } from '../vendor/three/addons/utils/SkeletonUtils.js';
import { RoomEnvironment } from '../vendor/three/addons/environments/RoomEnvironment.js';
import { SCREEN_LINE_PX, addDistanceBracket, moleculeScene, proceduralLength, proceduralScene } from './procedural-models.js?v=2';

const models = new Map();
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
        if ((child.isMesh || child.isPoints) && !child.userData.screenLine) originals.push(child);
    });
    return originals.map(child => {
        const overlay = child.clone(false);
        overlay.userData = {}; // not a labeled or outlined node itself
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
async function load(entry) {
    // Entries may share a GLB but differ in presentation (e.g. a recolored Sun).
    const key = entry.id || entry.src;
    if (!models.has(key)) models.set(key, (entry.procedural === 'molecule'
        ? moleculeData.then(data => data?.models?.[entry.molecule]
            ? { scene: moleculeScene(data.models[entry.molecule]) } : null)
        : entry.procedural ? Promise.resolve({ scene: proceduralScene(entry.procedural) })
            // The content hash busts browser caches whenever a model file changes.
            : loader.loadAsync(entry.sha256 ? `${entry.src}?v=${entry.sha256.slice(0, 12)}` : entry.src)).then(gltf => {
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
        if (entry.presentation?.distance_bracket) addDistanceBracket(scene, entry.presentation.distance_bracket);
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
        if (entry.presentation && ['tint', 'color_gain', 'roughness', 'metalness', 'opaque', 'double_sided', 'emissive', 'environment']
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
                    instance.traverse(child => {
                        for (const material of [child.material].flat())
                            if (material?.userData.environment) {
                                material.envMap = this.environment();
                                material.envMapIntensity = material.userData.environment;
                            }
                    });
                    instance.userData.modelItem = item;
                    Object.assign(instance.userData, { screenLines: [], overlays: [], clouds: [] });
                    instance.traverse(child => {
                        if (child.userData.screenLine) instance.userData.screenLines.push(child);
                        if (child.userData.label || child.userData.outline) instance.userData.overlays.push(child);
                        if (child.userData.pointSize) instance.userData.clouds.push(child);
                    });
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
        // Screen-space size of one world unit at a given camera depth.
        const pixelsPerUnit = depth => this.camera.projectionMatrix.elements[5] * h / 2 / depth;
        for (const [item, instance] of this.instances) {
            if (!instance?.visible) continue;
            instance.updateMatrixWorld(true);
            if (instance.userData.screenLines.length) {
                const perPixel = 1 / pixelsPerUnit(distance - instance.position.z);
                for (const line of instance.userData.screenLines) {
                    const thickness = SCREEN_LINE_PX * perPixel / line.parent.matrixWorld.getMaxScaleOnAxis();
                    const { axis, length } = line.userData.screenLine;
                    line.scale.set(axis === 'x' ? length : thickness, axis === 'y' ? length : thickness,
                        axis === 'z' ? length : thickness);
                }
                instance.updateMatrixWorld(true);
            }
            // Point clouds shrink with the model instead of staying a fixed-size smudge.
            const drawnPixels = instance.userData.drawSize * scale;
            for (const cloud of instance.userData.clouds) {
                const { max, perPixel } = cloud.userData.pointSize;
                cloud.material.size = THREE.MathUtils.clamp(drawnPixels * perPixel, 0.35, max);
            }
            this.overlay(instance, w, h, scale, cx, view);
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
    // Labels and outlines are SVG drawn at projected node positions, so text
    // stays upright and lines stay thin while the model rotates underneath.
    overlay(instance, w, h, scale, cx, view) {
        if (!instance.userData.overlays.length) return;
        const opacity = THREE.MathUtils.clamp(instance.userData.drawSize / 80, 0, 1);
        if (!opacity) return;
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
        for (const node of instance.userData.overlays) {
            const center = node.getWorldPosition(new THREE.Vector3());
            const at = toScreen(center.clone());
            let radius = 0;
            if (node.userData.sphere) {
                const top = toScreen(center.add(new THREE.Vector3(0, node.matrixWorld.getMaxScaleOnAxis(), 0)));
                radius = Math.abs(at.y - top.y);
            }
            if (node.userData.outline) {
                radius = Math.max(radius + 1.5 / scale, 3.5 / scale);
                svgNode('circle', { cx: at.x, cy: at.y, r: radius, class: 'journey-model-outline', opacity });
            }
            if (node.userData.label) {
                const label = svgNode('text', { x: at.x, y: at.y - radius - (radius ? 6 : 0) / scale,
                    class: `journey-model-label ${node.userData.labelClass || ''}`, 'text-anchor': 'middle', opacity });
                label.textContent = node.userData.label;
            }
        }
    }
    dispose() {
        this.disposed = true;
        cancelAnimationFrame(this.returnFrame);
        this.environmentMap?.dispose();
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
