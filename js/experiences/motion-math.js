// Constant-value, one-dimensional models; all inputs use SI units.
(function (root) {
    const orders = { speed: 1, acceleration: 2, jerk: 3 };
    const factorial = [1, 1, 2, 6];
    const isLinear = (dimension) => Object.hasOwn(orders, dimension);
    function kinematics(dimension, value, time) {
        const order = orders[dimension];
        if (
            !order ||
            !Number.isFinite(value) ||
            value < 0 ||
            !Number.isFinite(time) ||
            time < 0
        )
            throw new RangeError(
                'Expected a linear motion dimension and nonnegative finite inputs'
            );
        const derivative = (n) => {
            const exponent = order - n;
            if (exponent < 0 || value === 0) return 0;
            if (exponent === 0) return value;
            if (time === 0) return 0;
            // Log products avoid overflow in t^3 before multiplication by a tiny jerk.
            return (
                10 **
                (Math.log10(value) +
                    exponent * Math.log10(time) -
                    Math.log10(factorial[exponent]))
            );
        };
        return {
            position: derivative(0),
            velocity: derivative(1),
            acceleration: derivative(2),
            jerk: derivative(3)
        };
    }
    function duration(dimension, value, distance = 100) {
        if (
            !(value > 0) ||
            !Number.isFinite(value) ||
            !(distance > 0) ||
            !Number.isFinite(distance)
        )
            throw new RangeError(
                'Expected a positive finite value and distance'
            );
        if (isLinear(dimension)) {
            const order = orders[dimension];
            return (
                10 **
                ((Math.log10(distance) +
                    Math.log10(factorial[order]) -
                    Math.log10(value)) /
                    order)
            );
        }
        return dimension === 'angular-velocity'
            ? (2 * Math.PI) / value
            : 1 / value;
    }
    function timeBounds(dimension, value, distance = 100) {
        const seconds = duration(dimension, value, distance);
        const fit =
            Math.log10(seconds) - Math.log10(isLinear(dimension) ? 5 : 4);
        const bounded = (x) => Math.max(-300, Math.min(300, x));
        // Include real time and a decade around a legible crossing / period.
        // Integer endpoints also make exactly 1x reachable with a 0.01 step.
        return {
            min: bounded(Math.floor(Math.min(-1, fit - 1))),
            max: bounded(Math.ceil(Math.max(0, fit + 1))),
            fit: bounded(fit)
        };
    }
    function cycleState(dimension, value, time, rate = 1) {
        const period = duration(dimension, value);
        const hz =
            dimension === 'angular-velocity' ? value / (2 * Math.PI) : value;
        const visibleHz = hz * rate;
        const unresolved = visibleHz > 8;
        return {
            hz,
            period,
            visibleHz,
            unresolved,
            // Reduce time before multiplying, including for very high frequencies.
            phase: unresolved ? 0 : ((time % period) / period) * 2 * Math.PI
        };
    }
    function visualKind(dimension, name = '') {
        if (isLinear(dimension)) return 'linear';
        // A named sound source is not necessarily moving at its acoustic frequency.
        if (dimension === 'sound-frequency') return 'oscillation';
        if (/\borbit(?:al)?\b|galactic year/i.test(name)) return 'orbit';
        if (
            dimension === 'angular-velocity' ||
            /\brotation\b|\brevolution\b|\bspin\b|\bceiling fan\b/i.test(name)
        )
            return 'spin';
        if (/\bheartbeat\b|\bbreathing\b/i.test(name)) return 'pulse';
        return 'oscillation';
    }
    const api = {
        isLinear,
        kinematics,
        duration,
        timeBounds,
        cycleState,
        visualKind
    };
    root.ScaleMotionMath = api;
    if (typeof module !== 'undefined') module.exports = api;
})(globalThis);
