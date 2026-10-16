// Logarithmic camera coordinate; image sizes remain linear physical ratios.
(function (root) {
    const BASELINE = 405;
    const BASE_SIZE = 370;
    const CENTER_X = 500;
    const smoothstep = u => u * u * u * (u * (6 * u - 15) + 10);
    // Interpolate complete camera poses, not zoom-dependent focus corrections.
    // The latter can pull the camera past a neighbor and then back again.
    class FocusTransition {
        constructor() { this.targets = []; this.moving = false; this.path = this.anchor = null; }
        set(index, exponent, window = 0.3) {
            this.targets = [{ focusIndex: index, focusExponent: exponent, focusWindow: window, weight: 1 }];
            this.path = this.anchor = null;
            this.moving = false;
        }
        glide(index, exponent, window, seconds, pose) {
            this.to = { focusIndex: index, focusExponent: exponent, focusWindow: window, weight: 1 };
            this.path = { from: pose, to: this.to, progress: 0 };
            this.elapsed = 0; this.seconds = seconds; this.moving = true;
        }
        stop(pose) {
            if (this.path) {
                this.anchor = { ...pose, window: this.to.focusWindow };
                this.targets = [];
                this.path = null;
            }
            this.moving = false;
        }
        step(dt) {
            if (!this.moving) return false;
            this.elapsed += dt;
            const u = Math.min(1, this.elapsed / this.seconds);
            this.path.progress = smoothstep(u);
            if (u === 1) { this.targets = [this.to]; this.path = this.anchor = null; this.moving = false; }
            return this.moving;
        }
        options() { return { focusTargets: this.targets, cameraAnchor: this.anchor, cameraPath: this.path }; }
    }
    // Two motions share one camera. Wheel and drag use an exact critically
    // damped spring (stable at any refresh rate, no overshoot). Item-to-item
    // hops use `glide`: a fixed-duration smootherstep, because between items of
    // similar size the exponent barely changes while the scene slides a whole
    // object width, and a spring would finish that slide almost instantly.
    class Camera {
        constructor(value, min, max) { this.value = this.target = value; this.velocity = 0; this.min = min; this.max = max; this.glideTime = null; }
        aim(value) { this.glideTime = null; this.target = Math.max(this.min, Math.min(this.max, value)); }
        snap(value) { this.aim(value); this.value = this.target; this.velocity = 0; }
        glide(value, seconds) {
            this.aim(value);
            if (this.target === this.value) return;
            this.glideFrom = this.value; this.glideTime = 0; this.glideSeconds = Math.max(0.05, seconds);
            this.velocity = 0;
        }
        step(dt) {
            if (this.glideTime != null) {
                this.glideTime += dt;
                const u = Math.min(1, this.glideTime / this.glideSeconds);
                this.value = this.glideFrom + (this.target - this.glideFrom) * smoothstep(u);
                if (u >= 1) { this.glideTime = null; this.value = this.target; }
                return this.glideTime != null;
            }
            const omega = 18, delta = this.value - this.target;
            const c = this.velocity + omega * delta, decay = Math.exp(-omega * dt);
            this.value = this.target + (delta + c * dt) * decay;
            this.velocity = (this.velocity - omega * c * dt) * decay;
            if (Math.abs(this.value - this.target) < 1e-6 && Math.abs(this.velocity) < 1e-5) this.snap(this.target);
            return this.value !== this.target || this.velocity !== 0;
        }
    }
    const TRAVEL_PER_DECADE = 195;
    const WORLD_GAP_FACTOR = 0.67;
    // Similar-sized neighbors keep this clearance (in units of the larger object) so
    // overhanging parts of one model, such as an arrow or label, do not touch the next.
    const MIN_GAP_FACTOR = 0.2;
    function layout(items, exponent, order = 1, options = {}) {
        const logs = items.map(item => Math.log10(item.value) / order);
        const lengths = logs.map(value => 10 ** value);
        const factors = items.map(item => options.widthFactor?.(item) ?? 1);
        const left = options.left ?? 0, right = left + (options.width ?? 1000);
        const overscan = Math.max(0, options.overscan ?? 0);
        const world = [0];
        for (let index = 1; index < items.length; index++) {
            const footprint = Math.min(1, factors[index - 1], factors[index]);
            const ratio = lengths[index] / lengths[index - 1];
            const separation = Math.max(0, Math.min(1, Math.log10(ratio / 2) / Math.log10(5)));
            const gapFactor = MIN_GAP_FACTOR + (WORLD_GAP_FACTOR - MIN_GAP_FACTOR) * separation * footprint * footprint;
            world[index] = world[index - 1] +
                (factors[index - 1] * lengths[index - 1] + factors[index] * lengths[index]) / 2 +
                gapFactor * lengths[index];
            if (ratio > 1) {
                // Only objects readable beside the previous anchor constrain
                // its next camera segment. Microscopic, long-gone objects do not.
                let firstVisible = index - 1;
                for (let candidate = 0; candidate < index; candidate++) {
                    const scale = BASE_SIZE / lengths[index];
                    const width = factors[candidate] * lengths[candidate] * scale;
                    if (width >= 40) {
                        firstVisible = candidate;
                        break;
                    }
                }
                const visibleWorld = world[firstVisible];
                world[index] = Math.max(world[index], visibleWorld +
                    (world[index - 1] - visibleWorld) * ratio);
            }
        }
        const cameraLength = 10 ** exponent;
        const anchors = [];
        for (let first = 0; first < items.length;) {
            let last = first;
            while (last + 1 < items.length && lengths[last + 1] === lengths[first]) last++;
            anchors.push({ length: lengths[first], position: (world[first] + world[last]) / 2 });
            first = last + 1;
        }
        const cameraAt = length => {
            let segment = 0;
            while (segment < anchors.length - 2 && anchors[segment + 1].length < length) segment++;
            const span = anchors[segment + 1]?.length - anchors[segment]?.length;
            const fraction = span > 0 ? (length - anchors[segment].length) / span : 0;
            return anchors[segment].position +
                (anchors[segment + 1]?.position - anchors[segment].position || 0) * fraction;
        };
        let cameraWorld = cameraAt(cameraLength);
        for (const target of options.focusTargets ?? [options]) {
            if (!Number.isInteger(target.focusIndex) || world[target.focusIndex] == null) continue;
            const focused = target.focusIndex;
            const focusExponent = target.focusExponent ?? logs[focused];
            const distance = Math.min(1, Math.abs(exponent - focusExponent) /
                (target.focusWindow ?? 0.3));
            const blend = (1 - distance * distance) ** 2;
            cameraWorld += (world[focused] - cameraAt(10 ** focusExponent)) * blend * (target.weight ?? 1);
        }
        if (options.cameraAnchor) {
            const anchor = options.cameraAnchor;
            const distance = Math.min(1, Math.abs(exponent - anchor.exponent) / anchor.window);
            if (distance === 0) cameraWorld = anchor.worldX;
            else cameraWorld += (anchor.worldX - cameraAt(10 ** anchor.exponent)) * (1 - distance * distance) ** 2;
        }
        if (options.cameraPath) {
            const { from, to, progress } = options.cameraPath;
            const delta = to.focusExponent - from.exponent;
            // Linear interpolation of the projected transforms makes every
            // silhouette move monotonically between its endpoint positions.
            // expm1 keeps nearly identical sizes numerically well-conditioned.
            const fraction = delta === 0 ? progress : Math.max(0, Math.min(1,
                Math.expm1(-(exponent - from.exponent) * Math.LN10) / Math.expm1(-delta * Math.LN10)));
            cameraWorld = (1 - fraction) * from.worldX * 10 ** (exponent - from.exponent) +
                fraction * world[to.focusIndex] * 10 ** (exponent - to.focusExponent);
        }
        const pixelsPerUnit = BASE_SIZE / cameraLength;
        return items.map((item, index) => {
            const delta = logs[index] - exponent;
            const size = BASE_SIZE * 10 ** Math.max(-300, Math.min(296, delta));
            const width = size * factors[index];
            const x = CENTER_X + (world[index] - cameraWorld) * pixelsPerUnit;
            const leftEdge = x - width / 2;
            const rightEdge = leftEdge + width;
            return {item,index,size,width,x,leftEdge,rightEdge,y:BASELINE,worldX:world[index],cameraWorld,pixelsPerUnit,
                visible:rightEdge >= left - overscan && leftEdge <= right + overscan};
        });
    }
    function frameExponent(items, index, order = 1, options = {}) {
        return Math.log10(items[index].value) / order;
    }

    // Radial layout (as in Scale of the Universe): each object sits at a fixed world
    // position whose distance from the center is proportional to its own size, so at
    // any zoom the objects near the camera's scale form a ring, smaller ones converge
    // toward the center and larger ones wait offscreen. Only the zoom changes.
    const RADIAL_SIZE = 150;               // px drawn for an object as large as the camera length
    const RADIAL_CENTER_Y = 250;
    const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));
    const LABEL_EM = 0.07;                 // label font size, in units of the drawn extent
    const radialCache = new Map();
    // Half-extents of an object and its label below it, in units of its size.
    function radialBox(item, factor, extent) {
        const label = LABEL_EM * extent;
        const halfWidth = 0.5 * Math.max(factor * extent, 0.56 * label * String(item.name).length);
        return { halfWidth, top: 0.5 * extent, bottom: 0.5 * extent + 2.9 * label };
    }
    function radialPlacement(items, order, options) {
        const aspect = (options.width ?? 1000) < 800 ? 'narrow' : 'wide';
        const factors = items.map(item => options.widthFactor?.(item) ?? 1);
        const extents = items.map(item => options.extentFactor?.(item) ?? 1);
        const key = `${aspect}|${order}|${items.map((item, i) => `${item.name}:${item.value}:${factors[i]}:${extents[i]}`).join('|')}`;
        if (radialCache.has(key)) return radialCache.get(key);
        const [stretchX, stretchY] = aspect === 'wide' ? [1.55, 0.78] : [1.0, 0.92];
        const sizes = items.map(item => 10 ** (Math.log10(item.value) / order));
        const sorted = items.map((_, index) => index).sort((a, b) => sizes[a] - sizes[b] ||
            String(items[a].name).localeCompare(String(items[b].name)));
        const placed = [];
        const offsets = new Array(items.length);
        sorted.forEach((index, rank) => {
            const size = sizes[index];
            const box = radialBox(items[index], factors[index], extents[index]);
            // Keep the center clear for the smaller objects converging there.
            const reach = Math.hypot(box.halfWidth / stretchX, Math.max(box.top, box.bottom) / stretchY);
            const base = Math.max(1.05, reach + 0.3);
            const start = rank * GOLDEN_ANGLE;
            const neighbors = placed.filter(other => other.size >= size / 60);
            let chosen = null;
            for (let ring = 0; ring < 28 && !chosen; ring++) {
                const radius = base * 1.07 ** ring;
                for (let step = 0; step < 24 && !chosen; step++) {
                    const turn = (step % 2 ? 1 : -1) * Math.ceil(step / 2) * (Math.PI / 12);
                    const angle = start + turn;
                    const x = size * radius * stretchX * Math.cos(angle);
                    const y = size * radius * stretchY * Math.sin(angle);
                    const gap = 0.06 * size;
                    const clear = neighbors.every(other =>
                        Math.abs(x - other.x) >= size * box.halfWidth + other.size * other.box.halfWidth + gap ||
                        y + size * box.top + gap <= other.y - other.size * other.box.bottom ||
                        other.y + other.size * other.box.top + gap <= y - size * box.bottom);
                    if (clear) chosen = { x, y };
                }
            }
            chosen ||= { x: size * base * 4 * stretchX * Math.cos(start), y: size * base * 4 * stretchY * Math.sin(start) };
            placed.push({ ...chosen, size, box });
            offsets[index] = { u: chosen.x / size, v: chosen.y / size };
        });
        radialCache.set(key, offsets);
        if (radialCache.size > 8) radialCache.delete(radialCache.keys().next().value);
        return offsets;
    }
    function radialLayout(items, exponent, order = 1, options = {}) {
        const offsets = radialPlacement(items, order, options);
        const left = options.left ?? 0, right = left + (options.width ?? 1000);
        const overscan = Math.max(0, options.overscan ?? 0);
        const pixelsPerUnit = RADIAL_SIZE / 10 ** exponent;
        return items.map((item, index) => {
            const length = 10 ** (Math.log10(item.value) / order);
            const size = RADIAL_SIZE * 10 ** Math.max(-300, Math.min(296, Math.log10(item.value) / order - exponent));
            const factor = options.widthFactor?.(item) ?? 1;
            const extent = options.extentFactor?.(item) ?? 1;
            const box = radialBox(item, factor, extent);
            const x = CENTER_X + offsets[index].u * length * pixelsPerUnit;
            const center = RADIAL_CENTER_Y - offsets[index].v * length * pixelsPerUnit;
            const width = size * 2 * box.halfWidth;
            const leftEdge = x - width / 2, rightEdge = x + width / 2;
            const top = center - size * box.top, bottom = center + size * box.bottom;
            return { item, index, size, width, x, y: center + size * extent / 2, center, leftEdge, rightEdge,
                pixelsPerUnit, visible: rightEdge >= left - overscan && leftEdge <= right + overscan &&
                    bottom >= -overscan && top <= 500 + overscan };
        });
    }
    // The item at the camera's scale: drawn closest to RADIAL_SIZE * ratio.
    function radialFocus(items, exponent, order = 1, ratio = 0.85) {
        let best = 0, bestDistance = Infinity;
        items.forEach((item, index) => {
            const distance = Math.abs(Math.log10(item.value) / order - exponent - Math.log10(ratio));
            if (distance < bestDistance) { best = index; bestDistance = distance; }
        });
        return best;
    }
    root.ScaleJourney = { layout, frameExponent, radialLayout, radialFocus, radialPlacement, Camera, FocusTransition,
        BASELINE, BASE_SIZE, RADIAL_SIZE, RADIAL_CENTER_Y, LABEL_EM, TRAVEL_PER_DECADE };
    if (typeof module !== 'undefined') module.exports = root.ScaleJourney;
})(globalThis);
