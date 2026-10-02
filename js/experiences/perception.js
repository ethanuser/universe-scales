(function () {
    const { svg, dom, Slider, field, number, button } = ScaleControls;
    const { angularWidth, luminance, clamp } = ScaleMath;

    // Item qualifiers override the legacy base unit. Flux/intensity are not nits.
    const photometry = (item) => {
        const q = item.qualifiers || {};
        const keys = ['quantity', 'quantity_kind', 'photometric_quantity',
            'measurement_type', 'unit', 'units', 'unit_symbol', 'value_unit',
            'measurement_unit', 'original_unit', 'source_unit'];
        const metadata = JSON.stringify([q, ...keys.map((key) => item[key])])
            .toLowerCase().replace(/[_-]/g, ' ');
        if (/luminous\s+flux|\blumens?\b|\blm\b/.test(metadata))
            return { kind: 'flux', unit: 'lm', reason: 'Luminous flux is not surface luminance.' };
        if (/illuminance|\blux\b|\blx\b|foot[ -]?candles?|\bfc\b/.test(metadata))
            return { kind: 'illuminance', unit: /foot[ -]?candles?|\bfc\b/.test(metadata) ? 'fc' : 'lx', reason: 'Illuminance is not surface luminance.' };
        const unit = q.value_unit || q.unit_symbol || q.unit || q.units || q.measurement_unit ||
            item.value_unit || item.unit_symbol || item.unit || item.units || item.measurement_unit ||
            q.original_unit || item.original_unit || q.source_unit || item.source_unit;
        const normalized = typeof unit === 'string'
            ? unit.toLowerCase().replace(/[_\s^\u00b2]/g, (s) => s === '\u00b2' ? '2' : '')
            : '';
        if (/luminous\s+intensity/.test(metadata) || /^(cd|candela|candelas)$/.test(normalized))
            return { kind: 'intensity', unit: 'cd', reason: 'Luminous intensity is not surface luminance.' };
        const quantity = q.quantity || q.quantity_kind || q.photometric_quantity ||
            item.quantity || item.quantity_kind || item.photometric_quantity;
        if (quantity && !/^(luminance|surface[ _-]luminance|brightness)$/i.test(quantity))
            return { kind: 'unknown', unit: '', reason: 'Quantity metadata does not establish surface luminance.' };
        if (unit && !/^(nits?|cd\/m2|candelaspersquaremet(er|re)|candelapersquaremet(er|re))$/.test(normalized))
            return { kind: 'unknown', unit: '', reason: 'Unit metadata does not establish luminance in nits.' };
        return { kind: 'luminance', unit: 'cd/m\u00b2', reason: '' };
    };
    ScaleRenderers.photometry = photometry;
    const validValue = (item) => Number.isFinite(item.value) && item.value >= 0;
    const valueLabel = (item) => {
        const measurement = photometry(item);
        return validValue(item)
            ? `${number(item.value)}${measurement.unit ? ` ${measurement.unit}` : ' (unit unverified)'}`
            : 'Value unavailable';
    };
    const stageLayout = (ctx, kind, height) => {
        const box = ctx.stage.getBoundingClientRect();
        const width = box.width || 640;
        height = box.height || height;
        ctx.stage.classList.add('perception-stage', `perception-stage--${kind}`);
        ctx.settings.classList.add('perception-settings');
        ctx.stage.setAttribute('viewBox', `0 0 ${width} ${height}`);
        return { width, height };
    };
    const stageText = (parent, text, x, y, className = '') => {
        const node = svg('text', { x, y, 'text-anchor': 'middle', class: className }, text);
        parent.append(node);
        return node;
    };
    const itemSlider = (ctx, format) => new Slider(ctx.settings, {
        label: 'Explore the scale', min: 0, max: Math.max(0, ctx.items.length - 1),
        step: 1, value: ctx.index, format: (index) => format(ctx.items[index]),
        onChange: (index) => ctx.focus(index)
    });
    const illustration = (ctx, item, x, y, width, height, brightness = 1) => {
        const group = ctx.object(ctx.stage, item, x, y + height, width, height, { image: false });
        const src = ctx.image(item);
        const unavailable = () => stageText(group, 'Image unavailable', x, y + height / 2, 'perception-unavailable');
        if (!src) {
            unavailable();
            return group;
        }
        const photo = svg('image', {
            href: src, x: x - width / 2, y, width, height,
            preserveAspectRatio: 'xMidYMid meet', class: 'perception-photo',
            style: `filter: brightness(${brightness})`,
            role: 'img', 'aria-label': `${item.name}, illustrative photograph`
        });
        photo.addEventListener('error', () => {
            photo.remove();
            unavailable();
        }, { once: true });
        group.append(photo);
        return group;
    };

    ScaleRenderers.angleDiagram = (parent, angle) => {
        if (!Number.isFinite(angle) || angle < 0) return;
        const degrees = (angle / Math.PI) * 180;
        const diagram = svg('svg', {
            viewBox: '0 0 360 230', class: 'angle-diagram', role: 'img',
            'aria-label': `Two rays separated by ${number(degrees)} degrees`
        });
        const theta = angle % (2 * Math.PI), x = 180, y = 108, r = 78;
        diagram.append(svg('circle', { cx: x, cy: y, r, fill: 'none', stroke: 'currentColor', opacity: 0.15 }));
        for (const a of [0, theta]) diagram.append(svg('line', {
            x1: x, y1: y, x2: x + r * Math.cos(a), y2: y - r * Math.sin(a),
            stroke: 'currentColor', 'stroke-width': 2
        }));
        const points = Array.from({ length: 101 }, (_, i) => {
            const a = (Math.min(angle, 2 * Math.PI) * i) / 100;
            return `${x + 33 * Math.cos(a)},${y - 33 * Math.sin(a)}`;
        }).join(' ');
        diagram.append(svg('polyline', { points, fill: 'none', stroke: 'var(--accent-color)', 'stroke-width': 2 }));
        stageText(diagram, `${number(degrees)} degrees`, x, 204);
        const turns = Math.floor(angle / (2 * Math.PI));
        stageText(diagram, angle < 0.01 ? 'Rays nearly coincide at this scale' : turns ? `${number(turns)} full turn${turns === 1 ? '' : 's'}` : 'Angle between rays', x, 225);
        parent.append(diagram);
    };

    ScaleRenderers.angle = (ctx) => {
        let distance = 0.6, rulerCM = 2.65;
        const selection = itemSlider(ctx, (item) => `${number((item.value / Math.PI) * 180)} degrees`);
        new Slider(ctx.settings, {
            label: 'Viewing distance', min: 10, max: 300, value: 60, step: 1,
            format: (value) => `${number(value)} cm`,
            onChange: (value) => { distance = value / 100; render(); }
        });
        const calibration = dom('details', 'perception-calibration');
        calibration.append(dom('summary', '', 'Calibrate physical size'));
        const ruler = dom('div', 'experience-ruler');
        ruler.setAttribute('aria-label', 'Measure this line with a physical ruler');
        calibration.append(ruler);
        field(calibration, 'Measured line length (cm)', 2.65, 0.5, 20, (value) => {
            rulerCM = value;
            render();
        });
        ctx.settings.append(calibration);
        ctx.caption.textContent = 'The bracket spans w = 2d tan(theta/2), using your viewing distance d and angle theta. Measure the calibration line with a physical ruler and enter its length; the initial 2.65 cm is only an estimate. Sit facing the center at the chosen distance. Recalibrate after changing browser zoom or displays. No camera or device-size detection is used. Photographs preserve their proportions; the bracket, not the photographed object\'s edges, defines the angle. Subpixel angles and angles too wide for the screen use a diagram, not a magnified claim of physical size. For geometric angles this is an equivalent viewing angle, not the original geometry.';
        const render = () => {
            ctx.stage.replaceChildren();
            const { width, height } = stageLayout(ctx, 'angle', 330);
            selection.set(ctx.index);
            // A closed details element has no box; the styled ruler is 100 CSS px.
            const rulerPixels = ruler.getBoundingClientRect().width || 100;
            const physical = angularWidth(ctx.item.value, distance);
            const cssPixels = physical === null ? Infinity : physical * 100 * rulerPixels / rulerCM;
            const matrix = ctx.stage.getScreenCTM?.();
            const scale = matrix ? Math.hypot(matrix.a, matrix.b) : 1;
            const size = cssPixels / (scale || 1);
            if (physical !== null && Number.isFinite(cssPixels) && cssPixels >= 1 && size <= width - 40) {
                illustration(ctx, ctx.item, width / 2, 18, size, Math.max(1, height - 100));
                ctx.stage.append(svg('path', {
                    d: `M ${(width - size) / 2} ${height - 60} v 8 h ${size} v -8`,
                    class: 'perception-angle-span', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5
                }));
                ctx.live.textContent = `Span ${number(physical * 100)} cm at ${number(distance * 100)} cm viewing distance (using your calibration).`;
            } else {
                const diagram = svg('g');
                ScaleRenderers.angleDiagram(diagram, ctx.item.value);
                const nested = diagram.firstElementChild;
                if (nested) {
                    const diagramHeight = Math.max(1, Math.min(230, height - 44));
                    const diagramWidth = Math.min(width, diagramHeight * 360 / 230);
                    nested.setAttribute('x', (width - diagramWidth) / 2);
                    nested.setAttribute('y', 4);
                    nested.setAttribute('width', diagramWidth);
                    nested.setAttribute('height', diagramHeight);
                    nested.setAttribute('style', `width: ${diagramWidth}px; height: ${diagramHeight}px; margin: 0`);
                }
                ctx.stage.append(diagram);
                ctx.live.textContent = physical === null
                    ? '180 degrees or more cannot fit on a flat screen in front of you. Diagram only.'
                    : cssPixels < 1
                      ? 'Smaller than one CSS pixel at this distance. Diagram only.'
                      : `Required span ${number(physical * 100)} cm exceeds this view. Shorten the viewing distance. Diagram only.`;
            }
            stageText(ctx.stage, `${number((ctx.item.value / Math.PI) * 180)} degrees`, width / 2, height - 16);
        };
        return { render };
    };

    ScaleRenderers.brightness = (ctx) => {
        let white = 300, black = 0.3, exposure = 0;
        const selection = itemSlider(ctx, valueLabel);
        const exposureSlider = new Slider(ctx.settings, {
            label: 'Illustration exposure', min: -35, max: 15, value: 0,
            format: (value) => `${value > 0 ? '+' : ''}${number(value)} decades`,
            onChange: (value) => { exposure = value; render(); }
        });
        const calibration = dom('details', 'perception-calibration');
        calibration.append(dom('summary', '', 'Display settings (entered manually)'));
        const sourceLabel = dom('label', 'experience-field', 'Display values');
        const source = dom('select', 'experience-select');
        for (const [value, title] of [['estimate', 'Manual estimate'], ['measured', 'Measured at current screen setting']]) {
            const option = dom('option', '', title);
            option.value = value;
            source.append(option);
        }
        source.value = 'estimate';
        sourceLabel.append(source);
        calibration.append(sourceLabel);
        source.addEventListener('change', () => render());
        const fields = dom('div', 'experience-calibration');
        const whiteInput = field(fields, 'White level (nits)', white, 0.01, 10000, (value) => {
            if (value <= black) {
                whiteInput.value = white;
                validation.textContent = 'White level must be greater than black level.';
                return;
            }
            white = value;
            validation.textContent = '';
            render();
        });
        const blackInput = field(fields, 'Black level (nits)', black, 0, 9999, (value) => {
            if (value >= white) {
                blackInput.value = black;
                validation.textContent = 'Black level must be less than white level.';
                return;
            }
            black = value;
            validation.textContent = '';
            render();
        });
        const validation = dom('p', 'perception-validation');
        validation.setAttribute('role', 'status');
        calibration.append(fields, validation);
        ctx.settings.append(calibration);
        button(ctx.settings, 'Fit illustration exposure', () => { fitExposure(); render(); });
        ctx.caption.textContent = 'This is a relative photo illustration, not a reproduction of real-world light output or a radiometric measurement. Photo pixels and camera exposures are not calibrated. Exposure scales luminance values together before an approximate sRGB mapping to the entered black and white levels; changing the selected item fits that exposure. Clipping reports the model limits, not measured screen output. Browsers do not provide a standard API to read OS brightness or actual screen luminance; no device brightness is detected or changed here. Manual estimates are placeholders. For measured settings, enter meter readings of black and white at your current OS brightness, keep that setting fixed, and disable automatic brightness. HDR, color management, ambient reflections and local dimming remain unmeasured. Lumens (flux), candela (intensity) and lux (illuminance) are not nits: entries with those qualifiers remain unadjusted photos and are not compared as luminance. Entries without unit qualifiers use the dataset\'s declared cd/m2 base unit, not independently verified measurements. Viewing distance does not apply an inverse-square correction to surface luminance.';
        const fitExposure = () => {
            exposure = photometry(ctx.item).kind === 'luminance' && validValue(ctx.item) && ctx.item.value > 0
                ? clamp(Math.log10(white * 0.8) - Math.log10(ctx.item.value), -35, 15) : 0;
            exposureSlider.set(exposure);
        };
        const render = () => {
            ctx.stage.replaceChildren();
            const items = ctx.pair;
            const { width, height } = stageLayout(ctx, 'brightness', 350);
            selection.set(ctx.index);
            const messages = [];
            items.forEach((item, index) => {
                const measurement = photometry(item);
                const eligible = measurement.kind === 'luminance' && validValue(item);
                const light = eligible ? luminance(item.value, white, black, exposure) : null;
                const lane = width / items.length;
                const x = lane * (index + 0.5);
                const imageHeight = Math.max(1, height - 112);
                illustration(ctx, item, x, 12, Math.max(1, lane - 28), imageHeight, light ? light.gray / 255 : 1);
                const title = stageText(ctx.stage, '', x, imageHeight + 35, 'object-label');
                title.append(svg('title', {}, item.name));
                const limit = Math.max(8, Math.floor((lane - 24) / 8));
                const words = item.name.split(' ');
                const lines = [''];
                for (const word of words) {
                    if (lines.at(-1) && `${lines.at(-1)} ${word}`.length > limit) lines.push('');
                    lines[lines.length - 1] += `${lines.at(-1) ? ' ' : ''}${word}`;
                }
                lines.slice(0, 2).forEach((line, i) => {
                    const overflow = line.length > limit || (i === 1 && lines.length > 2);
                    title.append(svg('tspan', { x, dy: i ? 17 : 0 }, overflow ? `${line.slice(0, limit - 3)}...` : line));
                });
                stageText(ctx.stage, valueLabel(item), x, height - 34, 'perception-value');
                const status = !light ? 'Unadjusted photo'
                    : light.clipped === 'above' ? 'Above model range'
                      : light.clipped === 'below' ? 'Below model range'
                        : 'Relative illustration';
                stageText(ctx.stage, status, x, height - 13, 'perception-status');
                if (!eligible) messages.push(`${item.name}: ${validValue(item) ? measurement.reason : 'Invalid luminance value.'}`);
                else if (light.clipped) messages.push(`${item.name}: ${light.clipped} modeled range.`);
            });
            const sourceText = source.value === 'measured' ? 'Using your entered measurements.' : 'Using manual estimates, not detected display values.';
            ctx.live.textContent = `${messages.join(' ')} ${sourceText} Relative illustration only.`.trim();
        };
        fitExposure();
        return { render, focus: (frame = true) => { if (frame) fitExposure(); } };
    };
})();
