// Pure scale math, shared by renderers and the Node regression tests.
(function (root) {
    const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
    const log = (value) => Math.log10(Math.max(Number.MIN_VALUE, value));
    const power = (exponent) => 10 ** clamp(exponent, -300, 300);
    const nearest = (items, exponent, order = 1) =>
        items.reduce((best, item) =>
            Math.abs(log(item.value) / order - exponent) <
            Math.abs(log(best.value) / order - exponent)
                ? item
                : best
        );
    const sizeRatio = (value, reference, order = 1) =>
        power((log(value) - log(reference)) / order);
    const motionOrder = (dimension) =>
        ({ speed: 1, acceleration: 2, jerk: 3 })[dimension] || 1;
    const displacement = (dimension, value, time) =>
        (value * time ** motionOrder(dimension)) /
        ({ speed: 1, acceleration: 2, jerk: 6 }[dimension] || 1);
    const angularWidth = (angle, distance) =>
        angle >= 0 && angle < Math.PI
            ? 2 * distance * Math.tan(angle / 2)
            : null;
    const soundLevel = (intensity) => 10 * Math.log10(intensity / 1e-12);
    const countCluster = (count, exponent = log(count)) => {
        const each = power(Math.max(0, Math.ceil(exponent - 2)));
        const represented = count / each;
        return {
            each,
            represented,
            visible: Math.min(300, Math.floor(represented)),
            overflow: represented > 300,
            fraction: represented < 1 ? represented : represented % 1
        };
    };
    const linearToSRGB = (linear) =>
        linear <= 0.0031308
            ? 12.92 * linear
            : 1.055 * linear ** (1 / 2.4) - 0.055;
    const luminance = (value, white, black, exposure = 0) => {
        const target = value * power(exposure);
        return {
            gray: Math.round(
                255 *
                    linearToSRGB(
                        clamp((target - black) / (white - black), 0, 1)
                    )
            ),
            clipped: target > white ? 'above' : target < black ? 'below' : null,
            target
        };
    };
    function displayItems(items) {
        const chosen = new Map();
        const normalize = value => String(value).normalize('NFKC').trim().toLowerCase().replace(/\s+/g,' ');
        const score = item => (item.facts?.source_trace?.derivation_note ? 4 : 0)
            + (item.facts?.source_trace?.source_value_text ? 2 : 0) + (Number(item.source_count)||0)
            + (item.sources?.some(s=>s.source_class==='official_dataset') ? 10 : 0);
        for (const item of items) {
            const conditions = Object.entries(item.qualifiers||{}).filter(([key,value]) =>
                /condition|temperature|pressure|phase|regime|friction_type|snapshot_date/i.test(key)
                || (key==='measurement' && /static|kinetic|dynamic/i.test(String(value))))
                .map(([key,value])=>[normalize(key),normalize(value)]).sort();
            const key = JSON.stringify([normalize(item.name),conditions,item.snapshot_date||'']);
            const previous = chosen.get(key);
            if (!previous || score(item)>score(previous)) chosen.set(key,item);
        }
        return [...chosen.values()];
    }
    const api = {
        displayItems,
        clamp,
        log,
        power,
        nearest,
        sizeRatio,
        motionOrder,
        displacement,
        angularWidth,
        soundLevel,
        countCluster,
        luminance
    };
    root.ScaleMath = api;
    if (typeof module !== 'undefined') module.exports = api;
})(globalThis);
