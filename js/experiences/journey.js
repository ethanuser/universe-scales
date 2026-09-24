// Logarithmic camera coordinate; image sizes remain linear physical ratios.
(function (root) {
    const BASELINE = 405;
    const BASE_SIZE = 370;
    const CENTER_X = 500;
    // Exact critically damped spring: stable at different refresh rates, no overshoot.
    class Camera {
        constructor(value, min, max) { this.value = this.target = value; this.velocity = 0; this.min = min; this.max = max; }
        aim(value) { this.target = Math.max(this.min, Math.min(this.max, value)); }
        snap(value) { this.aim(value); this.value = this.target; this.velocity = 0; }
        step(dt) {
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
    function layout(items, exponent, order = 1, options = {}) {
        const logs = items.map(item => Math.log10(item.value) / order);
        const lengths = logs.map(value => 10 ** value);
        const factors = items.map(item => options.widthFactor?.(item) ?? 1);
        const left = options.left ?? 0, right = left + (options.width ?? 1000);
        const overscan = Math.max(0, options.overscan ?? 0);
        const world = [0];
        for (let index = 1; index < items.length; index++) {
            const footprint = Math.min(1, factors[index - 1], factors[index]);
            const gapFactor = 0.10 + (WORLD_GAP_FACTOR - 0.10) * footprint * footprint;
            world[index] = world[index - 1] +
                (factors[index - 1] * lengths[index - 1] + factors[index] * lengths[index]) / 2 +
                gapFactor * lengths[index];
            const ratio = lengths[index] / lengths[index - 1];
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
        if (Number.isInteger(options.focusIndex) && world[options.focusIndex] != null) {
            const focused = options.focusIndex;
            const focusExponent = options.focusExponent ?? logs[focused];
            const distance = Math.min(1, Math.abs(exponent - focusExponent) /
                (options.focusWindow ?? 0.3));
            const blend = (1 - distance * distance) ** 2;
            cameraWorld += (world[focused] - cameraAt(10 ** focusExponent)) * blend;
        }
        const pixelsPerUnit = BASE_SIZE / cameraLength;
        return items.map((item, index) => {
            const delta = logs[index] - exponent;
            const size = BASE_SIZE * 10 ** Math.max(-300, Math.min(296, delta));
            const width = size * factors[index];
            const x = CENTER_X + (world[index] - cameraWorld) * pixelsPerUnit;
            const leftEdge = x - width / 2;
            const rightEdge = leftEdge + width;
            return {item,index,size,width,x,leftEdge,rightEdge,y:BASELINE,worldX:world[index],pixelsPerUnit,
                visible:rightEdge >= left - overscan && leftEdge <= right + overscan};
        });
    }
    function frameExponent(items, index, order = 1, options = {}) {
        return Math.log10(items[index].value) / order;
    }
    root.ScaleJourney = { layout, frameExponent, Camera, BASELINE, BASE_SIZE, TRAVEL_PER_DECADE };
    if (typeof module !== 'undefined') module.exports = root.ScaleJourney;
})(globalThis);
