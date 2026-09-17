// Logarithmic camera coordinate; image sizes remain linear physical ratios.
(function (root) {
    const BASELINE = 340;
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
    const PAN_PER_DECADE = 400;
    function layout(items, exponent, order = 1, options = {}) {
        const logs = items.map(item => Math.log10(item.value) / order);
        let occupied = 0;
        const left = options.left ?? 0, right = left + (options.width ?? 1000);
        return items.map((item, index) => {
            const size = 200 * 10 ** Math.max(-300, Math.min(300, logs[index] - exponent));
            const width = size * (options.widthFactor?.(item) ?? 1);
            // Continuous pan plus dolly. No nearest-item anchors or width caps.
            // Reserve each previous footprint and a scale-relative breathing space.
            const x = 400 + PAN_PER_DECADE * (logs[index] - exponent) + occupied + width / 2;
            occupied += width * 1.15;
            return {item,index,size,width,x,y:BASELINE,
                visible:x + width/2 >= left && x - width/2 <= right};
        });
    }
    function frameExponent(items, index, order = 1, options = {}) {
        let low = Math.log10(items[index].value) / order - 2;
        let high = Math.log10(items[index].value) / order + 6;
        for (let i=0;i<48;i++) {
            const mid = (low+high)/2;
            if (layout(items,mid,order,options)[index].x > 500) low=mid; else high=mid;
        }
        return (low+high)/2;
    }
    root.ScaleJourney = { layout, frameExponent, Camera, BASELINE };
    if (typeof module !== 'undefined') module.exports = root.ScaleJourney;
})(globalThis);
