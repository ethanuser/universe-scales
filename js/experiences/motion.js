(function () {
    const { svg, dom, Slider, number, button } = ScaleControls;
    const { log, clamp, power, motionOrder } = ScaleMath;
    const {
        isLinear,
        kinematics,
        duration,
        timeBounds,
        cycleState,
        visualKind
    } = ScaleMotionMath;
    let imageRegistry;
    function loadImages() {
        imageRegistry ||= fetch('content/visualizations/motion-images.json')
            .then((response) => response.ok ? response.json() : {})
            .catch(() => ({}));
        return imageRegistry;
    }

    ScaleRenderers.motion = (ctx) => {
        const dim = ctx.dimension;
        const translating = isLinear(dim);
        const angular = dim === 'angular-velocity';
        const order = motionOrder(dim);
        let distance = 100;
        let bounds;
        let modelStage, disposed = false;
        let images = {};
        const failedImages = new Set();

        const text = (x, y, content, attrs = {}) => {
            const node = svg(
                'text',
                { x, y, 'text-anchor': 'middle', ...attrs },
                content
            );
            ctx.stage.append(node);
            return node;
        };
        function referencePhoto(item, x, y) {
            const entry = images[item.name];
            const curated = entry?.src && !failedImages.has(entry.src);
            const src = curated ? entry.src : ctx.image(item);
            const group = ctx.object(ctx.stage, item, x, y + 70, 140, 140, { image: false });
            group.setAttribute('class', 'experience-object motion-reference-photo');
            if (src && !failedImages.has(src)) {
                const photo = svg('image', {
                    href: src, x: x - 70, y: y - 70, width: 140, height: 140,
                    preserveAspectRatio: 'xMidYMid meet'
                });
                photo.addEventListener('error', () => {
                    if (disposed) return;
                    failedImages.add(src);
                    render(ctx.clock.time);
                });
                group.append(photo);
            } else {
                group.append(svg('text', { x, y, 'text-anchor': 'middle', 'font-size': 14 }, 'Photo unavailable'));
            }
            // An unsegmented photo is an identifier, not a rotating rigid body.
            text(x, y + 130, 'Photo reference; marker shows phase', { 'font-size': 14 });
            if (curated) {
                group.append(svg('title', {}, entry.note));
                for (const [href, label, offset, anchor] of [
                    [entry.source, `Photo: ${entry.author || 'source'}`, -5, 'end'],
                    [entry.license_url || entry.source, entry.license, 5, 'start']
                ]) {
                    const link = svg('a', { href, target: '_blank', rel: 'noopener noreferrer' });
                    link.append(svg('text', { x: x + offset, y: y + 148, 'text-anchor': anchor, 'font-size': 11 }, label));
                    ctx.stage.append(link);
                }
            }
        }
        function updateBounds() {
            bounds = timeBounds(dim, ctx.item.value, distance);
            Object.assign(ctx.timeSlider.input, {
                min: bounds.min,
                max: bounds.max
            });
            ctx.timeSlider.set(
                clamp(ctx.timeSlider.value, bounds.min, bounds.max)
            );
            ctx.clock.rate = power(ctx.timeSlider.value);
        }
        function setTime(exponent) {
            ctx.timeSlider.set(clamp(exponent, bounds.min, bounds.max));
            ctx.clock.rate = power(ctx.timeSlider.value);
            ctx.clock.reset();
            render(0);
        }

        if (translating) {
            const reference = new Slider(ctx.settings, {
                label: 'Track length',
                min: -6,
                max: 12,
                value: 2,
                format: (x) => `${number(power(x))} m`,
                onChange: (x) => setDistance(power(x))
            });
            function setDistance(value) {
                distance = value;
                reference.set(log(value));
                updateBounds();
                ctx.clock.reset();
                render(0);
            }
            const anchors = dom('div', 'experience-calibration');
            button(anchors, 'Human height (1.7 m)', () => setDistance(1.7));
            button(anchors, 'Football field (100 m)', () => setDistance(100));
            ctx.settings.append(anchors);
        }
        ctx.timeControls(0);
        ctx.timeSlider.format = (exponent) =>
            exponent === 0
                ? '1x (real time)'
                : `${number(power(exponent))}x real time`;
        updateBounds();
        button(ctx.settings, 'Real time (1x)', () => setTime(0));
        button(ctx.settings, 'Fit time to item', () => setTime(bounds.fit));

        const notes = {
            speed: 'Speed is distance traveled per second. With constant positive speed, $v$ stays fixed and $x=vt$; $a=0$ and $j=0$.',
            acceleration:
                'Acceleration is the change in velocity per second, not a rotation rate. Holding $a$ constant and starting at rest gives $v=at$ and $x=\\tfrac12 at^2$; $j=0$. Equal time intervals add equal amounts of velocity, so the distance between the dots grows.',
            jerk: 'Jerk is the change in acceleration per second, not speed or angular acceleration. Holding $j$ constant and starting with $a_0=v_0=0$ gives $a=jt$, then $v=\\tfrac12 jt^2$, then $x=\\tfrac16 jt^3$. Equal time intervals add equal amounts of acceleration; velocity grows quadratically and distance cubically.'
        };
        ctx.app.setRichText(
            ctx.caption,
            translating
                ? `${notes[dim]} Both lanes start at $x=0$ and share the same distance and simulated time. Dots mark four equal time intervals, not equal distances. Each trial restarts both lanes when the selected item reaches the end; that reset is not a physical reversal or sudden braking. Images are identifiers, not scaled lengths. This is a hypothetical straight-line, constant-value model, not a reconstruction of impacts, gravity fields, or centripetal motion. A linear acceleration alone cannot determine a rotation rate without a radius and a motion model. Classical equations cease to apply near relativistic speeds. Above two trials per real second, the view shows a labeled static timing diagram instead of misleading sampled motion.`
                : angular
                  ? 'Angular velocity measures angle per second: $\\theta=\\omega t$. One turn is $2\\pi$ radians, so $f=\\omega/(2\\pi)$ and the period is $T=2\\pi/\\omega$. Orbital examples move around a center; spinning examples rotate about their own center. The marker shows phase, with counterclockwise chosen for illustration, not a measured direction. Where no suitable model is available, reference photos stay fixed so fixtures and backgrounds do not rotate; only the phase marker moves. Photos retain their proportions but are not measured geometries or recordings at the listed rate. Time controls change simulated time, not the recorded rate. Above eight turns per real second the diagram is static to avoid misleading aliasing.'
                  : `${dim === 'sound-frequency' ? 'Sound frequency counts pressure cycles per second, not the movement of a pictured animal or instrument. The marker and sine wave are schematic timing guides, not a measured waveform, sound level, or wavelength. This visualization does not play sound.' : 'Frequency counts cycles per second. Explicit orbital examples revolve, rotation examples spin, and heartbeat or breathing examples pulse. Other examples use a schematic oscillator; its displacement and shape are illustrative, not measurements.'} The period is $T=1/f$ and the phase is $\\phi=2\\pi ft$. One complete orbit, pulse, or back-and-forth represents one cycle. Time controls change simulated time, not the recorded frequency. Above eight cycles per real second the diagram is static to avoid misleading aliasing.`
        );

        function renderLinear(time) {
            const span = duration(dim, ctx.item.value, distance);
            const unresolved = ctx.clock.rate / span > 2;
            const segment = time % span;
            // A frozen view must not imply the object is physically motionless.
            const shownTime = unresolved ? span / 2 : segment;
            text(
                500,
                26,
                unresolved
                    ? 'Static timing diagram: use Fit time to item to see motion'
                    : `Trial time: ${number(segment)} / ${number(span)} s`
            );
            ctx.pair.forEach((item, lane) => {
                const y = ctx.pair.length === 1 ? 240 : 130 + lane * 200;
                const state = kinematics(dim, item.value, shownTime);
                const ratio = item.value / ctx.item.value;
                const position = clamp(
                    ratio * (shownTime / span) ** order,
                    0,
                    1
                );
                ctx.stage.append(
                    svg('line', {
                        x1: 70,
                        y1: y,
                        x2: 930,
                        y2: y,
                        stroke: 'var(--border-color)',
                        'stroke-width': 3
                    })
                );
                for (let i = 0; i <= 10; i++) {
                    ctx.stage.append(
                        svg('line', {
                            x1: 70 + i * 86,
                            y1: y + 5,
                            x2: 70 + i * 86,
                            y2: y + 13,
                            stroke: 'currentColor'
                        })
                    );
                }
                for (let i = 0; i <= 4; i++) {
                    ctx.stage.append(
                        svg('circle', {
                            cx:
                                70 +
                                860 * clamp(ratio * (i / 4) ** order, 0, 1),
                            cy: y,
                            r: 4,
                            fill: 'var(--accent-color)',
                            opacity: 0.55,
                            class: 'motion-time-sample'
                        })
                    );
                }
                const x = 70 + position * 860;
                ctx.object(ctx.stage, item, x, y - 8, 64, 64);
                ctx.stage.append(
                    svg('line', {
                        x1: x,
                        y1: y - 5,
                        x2: x,
                        y2: y + 10,
                        stroke: 'var(--accent-color)',
                        'stroke-width': 3
                    })
                );
                text(70, y + 30, '0 m', { 'text-anchor': 'start' });
                text(930, y + 30, `${number(distance)} m`, {
                    'text-anchor': 'end'
                });
                ctx.label(item, 500, y + 57);
                text(
                    500,
                    y + 115,
                    unresolved
                        ? `Crossing time: ${number(duration(dim, item.value, distance))} s`
                        : `x ${number(state.position)} m  |  v ${number(state.velocity)} m/s  |  a ${number(state.acceleration)} m/s^2`
                );
            });
            text(
                500,
                485,
                `Dots: every ${number(span / 4)} simulated s${unresolved ? '; marker shown halfway through a trial' : ''}`
            );
            if (unresolved) {
                ctx.live.textContent = `${number(distance)} m takes ${number(span)} s. Too fast at ${number(ctx.clock.rate)}x; fit time to see the motion.`;
            } else {
                const state = kinematics(dim, ctx.item.value, segment);
                const change =
                    dim === 'jerk'
                        ? `a ${number(state.acceleration)} m/s^2; +${number(ctx.item.value)} m/s^2 each simulated second.`
                        : dim === 'acceleration'
                          ? `+${number(ctx.item.value)} m/s each simulated second.`
                          : 'Constant speed.';
                ctx.live.textContent = `t ${number(segment)} s: ${number(state.position)} m traveled; v ${number(state.velocity)} m/s. ${change}`;
            }
        }

        function renderCycle(item, lane, time) {
            const x = ctx.pair.length === 1 ? 500 : lane ? 750 : 250;
            const y = 220;
            const state = cycleState(dim, item.value, time, ctx.clock.rate);
            const { phase, unresolved } = state;
            const kind = visualKind(dim, item.name);
            if (kind === 'orbit' || kind === 'spin') {
                ctx.stage.append(
                    svg('circle', {
                        cx: x,
                        cy: y,
                        r: 110,
                        fill: 'none',
                        stroke: 'var(--border-color)',
                        'stroke-width': 2
                    })
                );
                const spoke = svg('line', {
                    x1: x + (kind === 'spin' ? 100 * Math.cos(phase) : 0),
                    y1: y - (kind === 'spin' ? 100 * Math.sin(phase) : 0),
                    x2: x + 110 * Math.cos(phase),
                    y2: y - 110 * Math.sin(phase),
                    stroke: 'var(--accent-color)',
                    'stroke-width': 3,
                    class: 'motion-phase-guide'
                });
                if (kind === 'orbit') {
                    ctx.stage.append(
                        spoke,
                        svg('circle', { cx: x, cy: y, r: 9, class: 'shape' })
                    );
                    ctx.object(
                        ctx.stage,
                        item,
                        x + 110 * Math.cos(phase),
                        y - 110 * Math.sin(phase) + 25,
                        50,
                        50
                    );
                } else {
                    if (!modelStage?.draw(item, x, y + 70, 140, phase)) {
                        referencePhoto(item, x, y);
                    }
                    ctx.stage.append(spoke);
                }
            } else if (kind === 'pulse') {
                // Uniform scaling preserves the image's original aspect ratio.
                const size = unresolved ? 120 : 120 + 16 * Math.sin(phase);
                ctx.object(ctx.stage, item, x, y + size / 2, size, size);
            } else {
                ctx.stage.append(
                    svg('line', {
                        x1: x - 110,
                        y1: y,
                        x2: x + 110,
                        y2: y,
                        stroke: 'var(--border-color)'
                    })
                );
                ctx.object(
                    ctx.stage,
                    item,
                    x + (unresolved ? 0 : 55 * Math.sin(phase)),
                    y + 45,
                    90,
                    90
                );
                const points = Array.from(
                    { length: 121 },
                    (_, i) =>
                        `${x - 150 + i * 2.5},${y + 95 - 25 * Math.sin((i / 120) * 4 * Math.PI - phase)}`
                ).join(' ');
                ctx.stage.append(
                    svg('polyline', {
                        points,
                        fill: 'none',
                        stroke: 'var(--accent-color)',
                        'stroke-width': 2
                    })
                );
            }
            text(
                x,
                40,
                angular
                    ? `${number(item.value)} rad/s`
                    : `${number(state.hz)} Hz`
            );
            text(
                x,
                70,
                `One ${kind === 'spin' || kind === 'orbit' ? 'turn' : 'cycle'}: ${number(state.period)} s`
            );
            ctx.label(item, x, 390);
            text(
                x,
                470,
                unresolved
                    ? 'Too fast to resolve: static diagram'
                    : `${number(state.visibleHz)} cycles / real s`
            );
            return state;
        }

        function render(time = 0) {
            if (disposed) return;
            ctx.stage.replaceChildren();
            modelStage?.begin();
            if (translating) {
                renderLinear(time);
                return;
            }
            const states = ctx.pair.map((item, lane) =>
                renderCycle(item, lane, time)
            );
            const selected = states.at(-1);
            modelStage?.finish();
            ctx.live.textContent = `Period ${number(selected.period)} s; ${number(selected.visibleHz)} ${angular ? 'turns' : 'cycles'} / real s at ${number(ctx.clock.rate)}x.${states.some((state) => state.unresolved) ? ' Fit time to see individual cycles.' : ` Elapsed ${number(time)} s.`}`;
        }
        const attachModels = () => {
            if (disposed || !angular || modelStage || !globalThis.ScaleModels) return;
            modelStage = new ScaleModels.ModelStage(ctx, () => render(ctx.clock.time));
        };
        globalThis.addEventListener?.('scale-models-ready', attachModels);
        attachModels();
        if (angular) loadImages().then((registry) => {
            if (disposed) return;
            images = registry.images?.[dim] || {};
            render(ctx.clock.time);
        });
        return {
            render,
            dispose: () => {
                disposed = true; modelStage?.dispose();
                globalThis.removeEventListener?.('scale-models-ready', attachModels);
            },
            focus: (frame) => {
                updateBounds();
                if (frame) setTime(0);
            }
        };
    };
})();
