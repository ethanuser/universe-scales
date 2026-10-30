(function (root) {
    const R = (root.ScaleRenderers = root.ScaleRenderers || {});
    const { svg, dom, Slider, number, button } = ScaleControls;
    const { log, power, clamp, countCluster } = ScaleMath;
    const line = (x1, y1, x2, y2) => svg('line', { x1, y1, x2, y2, stroke: 'currentColor', 'stroke-width': 2 });
    const MIN_DRAWN_PX = 0.5;
    const MIN_MODEL_PX = 4;
    const IN_VIEW_PX = 14;
    // A selected object is framed to about 55% of the stage's smaller side (in decades above
    // the ring size), so it and its in-model labels read clearly on any window shape.
    function frameZoom(ctx) {
        const box = stageSize(ctx.stage);
        const viewWidth = box.width < 600 ? 560 : 1000;
        const scale = Math.min(box.width / viewWidth, box.height / 500) || 1;
        const wanted = 0.55 * Math.min(box.width, box.height) / (ScaleJourney.RADIAL_SIZE * scale);
        return Math.log10(clamp(wanted || 1.8, 1.2, 4));
    }      // an object this large on screen counts as "in view"
    function createSpatialInput(element, { interaction = {}, onStart, onPan, onPinch, onEnd }) {
        const previousTouchAction = element.style.touchAction;
        const previousUserSelect = element.style.userSelect;
        // pinch: two touch points; their spread ratio zooms (onPinch) until either lifts.
        let active = null, dragged = 0, pinch = null;
        const spread = () => Math.hypot(pinch.points[0].x - pinch.points[1].x, pinch.points[0].y - pinch.points[1].y);
        const controls = 'button,input,select,textarea,option,a,[contenteditable="true"],[role="button"],.experience-camera-slider';
        element.style.touchAction = 'none';
        element.style.userSelect = 'none';
        const isControl = target => Boolean(target.closest?.(controls));
        const hover = event => {
            if (event?.pointerType === 'touch') return;
            const item = event && !isControl(event.target)
                ? interaction.pick?.(event.clientX, event.clientY) || null : null;
            interaction.hover?.(item, event && !isControl(event.target)
                ? { x: event.clientX, y: event.clientY } : null);
            element.classList.toggle('is-model-hovered', Boolean(item));
        };
        const pointerdown = event => {
            if (active && !pinch && onPinch && event.pointerType === 'touch' && active.pointerType === 'touch') {
                if (active.rotating) interaction.releaseRotate?.(active.rotating, event.timeStamp);
                active.rotating = null;
                try { element.setPointerCapture(event.pointerId); } catch {}
                pinch = { points: [{ id: active.id, x: active.x, y: active.y }, { id: event.pointerId, x: event.clientX, y: event.clientY }] };
                pinch.distance = spread();
                dragged = Math.max(dragged, 10);
                event.preventDefault();
                return;
            }
            if (active || event.button > 2 || isControl(event.target)) return;
            onStart?.(event);
            let captured = false;
            try {
                element.setPointerCapture(event.pointerId);
                captured = true;
            } catch { /* Pointer may already have become inactive. */ }
            // Shift-drag or a middle-button drag always pans, even over an object.
            const panOnly = event.shiftKey || event.button === 1 || event.button === 2;
            const rotating = panOnly ? null : interaction.pick?.(event.clientX, event.clientY) || null;
            if (rotating) interaction.beginRotate?.(rotating, event.timeStamp);
            interaction.hover?.(null, null);
            active = {
                id: event.pointerId, x: event.clientX, y: event.clientY,
                movedAt: event.timeStamp, velocity: 0, captured,
                rotating, pointerType: event.pointerType
            };
            dragged = 0;
            event.preventDefault();
            element.classList.remove('is-model-hovered');
            element.classList.add('is-dragging');
        };
        const pointermove = event => {
            if (pinch) {
                const point = pinch.points.find(p => p.id === event.pointerId);
                if (!point) return;
                point.x = event.clientX; point.y = event.clientY;
                const distance = spread();
                if (distance > 0 && pinch.distance > 0) onPinch(distance / pinch.distance);
                pinch.distance = distance;
                event.preventDefault();
                return;
            }
            if (!active) { hover(event); return; }
            if (event.pointerId !== active.id) return;
            const dx = event.clientX - active.x;
            const dy = event.clientY - active.y;
            active.x = event.clientX;
            active.y = event.clientY;
            if (!dx && !dy) return;
            dragged += Math.hypot(dx, dy);
            const dt = Math.max(8, event.timeStamp - active.movedAt) / 1000;
            active.movedAt = event.timeStamp;
            if (active.rotating) {
                interaction.hover?.(null, { x: event.clientX, y: event.clientY });
                interaction.rotate?.(active.rotating, dx, dy, event.timeStamp);
            } else {
                active.velocity = 0.65 * active.velocity + 0.35 * -dx * 0.0012 / dt;
                onPan?.(dx, dy, event);
            }
            event.preventDefault();
        };
        const finish = (event, canceled = false) => {
            if (pinch) {
                if (!pinch.points.some(p => p.id === event.pointerId)) return;
                // Lifting either finger ends the gesture; nothing pans or flings afterwards.
                for (const point of pinch.points)
                    if (element.hasPointerCapture?.(point.id)) try { element.releasePointerCapture(point.id); } catch {}
                pinch = null; active = null;
                element.classList.remove('is-dragging');
                return;
            }
            if (!active || (event.pointerId != null && event.pointerId !== active.id)) return;
            const gesture = active;
            active = null;
            if (gesture.rotating) interaction.releaseRotate?.(gesture.rotating, event.timeStamp);
            onEnd?.(!canceled && !gesture.rotating && dragged > 5 && event.type === 'pointerup' &&
                event.timeStamp - gesture.movedAt < 100 ? gesture.velocity : 0, event, canceled);
            element.classList.remove('is-dragging');
            if (gesture.captured && event.type !== 'lostpointercapture' &&
                element.hasPointerCapture?.(gesture.id)) {
                try { element.releasePointerCapture(gesture.id); } catch { /* Already released. */ }
            }
            hover(event.type === 'pointerup' && gesture.pointerType !== 'touch' ? event : null);
        };
        const pointerup = event => finish(event);
        const pointercancel = event => finish(event, true);
        const lostpointercapture = event => finish(event, true);
        const pointerleave = () => { if (!active) hover(null); };
        const dragstart = event => event.preventDefault();
        const contextmenu = event => event.preventDefault();  // right-drag pans
        const listeners = { pointerdown, pointermove, pointerup, pointercancel, lostpointercapture, pointerleave, dragstart, contextmenu };
        for (const [name, listener] of Object.entries(listeners)) element.addEventListener(name, listener);
        return {
            isControlTarget: isControl,
            consumeDraggedClick() {
                const wasDragged = dragged > 5;
                dragged = 0;
                return wasDragged;
            },
            dispose() {
                for (const [name, listener] of Object.entries(listeners)) element.removeEventListener(name, listener);
                if (active) finish({ type: 'pointercancel', pointerId: active.id, timeStamp: active.movedAt }, true);
                element.style.touchAction = previousTouchAction;
                element.style.userSelect = previousUserSelect;
                element.classList.remove('is-dragging', 'is-model-hovered');
            }
        };
    }
    R.createSpatialInput = createSpatialInput;
    // The stage's size, kept current by a ResizeObserver. Reading layout every frame,
    // right after the SVG is rebuilt, forced a synchronous layout on each frame.
    function stageSize(stage) {
        if (!stage._sizeObserver && typeof ResizeObserver !== 'undefined') {
            stage._size = stage.getBoundingClientRect();
            stage._sizeObserver = new ResizeObserver(([entry]) => {
                const box = entry.borderBoxSize?.[0];
                const size = box ? { width: box.inlineSize, height: box.blockSize } : entry.target.getBoundingClientRect();
                if (size.width === stage._size?.width && size.height === stage._size?.height) return;
                stage._size = size;
                stage._onResize?.();
            });
            stage._sizeObserver.observe(stage);
        }
        return stage._size || stage.getBoundingClientRect();
    }
    R.stageSize = stageSize;
    function viewport(ctx) {
        const box = stageSize(ctx.stage);
        const width = box.width < 600 ? 560 : 1000;
        const left = (1000 - width) / 2;
        ctx.stage.setAttribute('viewBox', `${left} 0 ${width} 500`);
        return { left, width, scale: Math.min(box.width / width, box.height / 500) || 1 };
    }
    const mix = (a, b, amount) => a.map((value, index) =>
        Math.round(value + (b[index] - value) * clamp(amount, 0, 1))
    );
    function ramp(value, stops) {
        if (value <= stops[0][0]) return stops[0][1];
        for (let index = 1; index < stops.length; index++) {
            if (value <= stops[index][0]) {
                const [startAt, startColor] = stops[index - 1];
                const [endAt, endColor] = stops[index];
                return mix(startColor, endColor, (value - startAt) / (endAt - startAt));
            }
        }
        return stops.at(-1)[1];
    }
    function navigation(ctx, order, zoom, render, layoutOptions = () => ({}), interaction = {}) {
        ctx.comparison.hidden = true;
        ctx.updateComparison = () => {};
        const camera = new ScaleJourney.Camera(zoom.value, Number(zoom.input.min), Number(zoom.input.max));
        const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
        let frame, previousTime, disposed = false, pinnedFocus = null, pinnedExponent = null, observed = [];
        // lockActive: the selected item also holds the view (centered, zoom-in limit). Panning
        // ends the lock but keeps the item selected.
        let lockActive = false;
        const focusTransition = new ScaleJourney.FocusTransition();
        // Radial view: a selected object is centered by panning to it. A selection glide is
        // one zoom about the fixed point shared by the start and end views, so every object
        // moves along a straight line. Inward zoom then returns to the shared origin;
        // only interrupting a glide freezes a new reference, not every wheel event.
        let anchor = null, panGlide = null;
        const panAt = exponent => {
            if (panGlide) {
                const { from, to, start, end, startTime, seconds } = panGlide;
                const zooming = Math.abs(end - start) >= 0.05;
                const elapsed = (performance.now() - startTime) / 1000;
                if (zooming ? camera.glideTime == null : elapsed >= seconds) {
                    anchor = { index: panGlide.index, exponent: end };
                    panGlide = null;
                } else if (zooming) {
                    // Counts zoom their camera at twice the layout's rate (exponentFactor).
                    const f = layoutOptions().exponentFactor ?? 1;
                    const q = 10 ** ((start - end) * f), grow = 10 ** ((exponent - start) * f);
                    const fixed = axis => (from[axis] - to[axis] * q) / (1 - q);
                    return { x: fixed('x') - (fixed('x') - from.x) * grow, y: fixed('y') - (fixed('y') - from.y) * grow };
                } else {
                    const u = clamp(elapsed / seconds, 0, 1), eased = u * u * (3 - 2 * u);
                    return { x: from.x + (to.x - from.x) * eased, y: from.y + (to.y - from.y) * eased };
                }
            }
            if (!anchor) return { x: 0, y: 0 };
            // A settled selection follows its item (the layout may still be refining);
            // a frozen manual pan keeps its world point.
            const point = anchor.index != null ? layoutOptions().radialWorld?.(anchor.index) : anchor;
            if (!point) return { x: 0, y: 0 };
            const f = layoutOptions().exponentFactor ?? 1;
            // A selected object stays centered while zooming into it. Zooming out from it eases
            // the view back to the shared center over half a decade, by which point the lock
            // releases, so coming back toward its size never re-centers on it.
            if (anchor.index != null && anchor.index === pinnedFocus && lockActive) {
                const out = pinnedExponent == null ? 0 : (exponent - pinnedExponent) * f;
                const u = clamp(out / 0.5, 0, 1), weight = 1 - u * u * (3 - 2 * u);
                return { x: point.x * weight, y: point.y * weight };
            }
            // A frozen view (after a drag, or a released selection) eases back to the shared
            // center as you keep zooming in either direction, so it never snaps back onto the
            // item it was centered on.
            if (anchor.manual && exponent > anchor.exponent) {
                const u = clamp((exponent - anchor.exponent) * f / 1.5, 0, 1), weight = 1 - u * u * (3 - 2 * u);
                return { x: point.x * weight, y: point.y * weight };
            }
            return ScaleJourney.radialReturnPan(point, exponent * f, anchor.exponent * f, anchor.manual ? 2 : 1);
        };
        const freezePan = () => {
            if (!layoutOptions().radial || !panGlide) return;
            anchor = { ...panAt(camera.value), exponent: camera.value };
            panGlide = null;
        };
        const glidePan = (index, exponent, seconds) => {
            const to = layoutOptions().radialWorld?.(index);
            const from = panAt(camera.value);
            if (to && seconds > 0)
                panGlide = { index, from, to, start: camera.value, end: exponent, startTime: performance.now(), seconds };
            else { anchor = { index, exponent }; panGlide = null; }
        };
        const currentPose = () => {
            const options = layoutOptions(), exponent = camera.value * (options.exponentFactor ?? 1);
            if (options.radial) return { exponent, worldX: 0 };
            const entries = ScaleJourney.layout(ctx.items, exponent, options.order ?? order,
                { ...options, ...focusTransition.options() });
            return { exponent, worldX: entries[0].cameraWorld };
        };
        const apply = () => {
            zoom.set(camera.value);
            const options = layoutOptions();
            if (options.radial) {
                if (camera.glideTime == null) {
                    // An explicit selection holds while its object stays near the size it was
                    // framed at; zooming further away deselects it.
                    const delta = pinnedExponent == null ? 0 : (camera.value - pinnedExponent) * (options.exponentFactor ?? 1);
                    if (pinnedFocus != null && delta > 0.5) {
                        // A locked view has already eased back to the center (see panAt); a
                        // panned view keeps its frozen point.
                        if (lockActive) anchor = null;
                        pinnedFocus = pinnedExponent = null;
                        lockActive = false;
                    }
                    if (pinnedFocus == null) {
                        // Otherwise describe the on-screen object nearest the camera's scale,
                        // or nothing when no object is in view.
                        const best = observed.reduce((a, b) => (!a || b.distance < a.distance ? b : a), null);
                        if (!best || best.distance > 1) ctx.clearFocus();
                        else if (best.index !== ctx.index || ctx.noFocus || ctx.explicitSelection) ctx.focus(best.index, false);
                    }
                }
                render();
                return;
            }
            const entries = ScaleJourney.layout(ctx.items,camera.value*(options.exponentFactor??1),options.order??order,
                {...options, ...focusTransition.options()});
            const focusEntries = options.maxFocusSize
                ? entries.filter(entry => entry.visible && entry.size <= options.maxFocusSize)
                : entries;
            const focusPool = focusEntries.length ? focusEntries : entries;
            const focused = focusPool.reduce((best,entry) =>
                Math.abs(entry.x-500) < Math.abs(best.x-500) ? entry : best
            , focusPool[0]);
            const index = focused.index;
            if (!focusTransition.moving && camera.glideTime == null && index !== ctx.index) ctx.focus(index, false);
            render();
        };
        const animate = now => {
            if (disposed) return;
            const dt = Math.max(0, (now - (previousTime ?? now - 16)) / 1000);
            const moving = camera.step(camera.glideTime != null ? dt : Math.min(0.05, dt));
            const focusing = focusTransition.step(dt);
            previousTime = now;
            apply();
            frame = moving || focusing || panGlide ? requestAnimationFrame(animate) : null;
            if (!frame) previousTime = null;
        };
        // While a selection is locked, zooming in stops LOCK_ZOOM_IN decades past its framing.
        const LOCK_ZOOM_IN = 1;
        const lockLimit = value => lockActive && pinnedFocus != null && pinnedExponent != null && layoutOptions().radial
            ? Math.max(value, pinnedExponent - LOCK_ZOOM_IN / (layoutOptions().exponentFactor ?? 1)) : value;
        const aim = (value, focusIndex, focusWindow = 0.3) => {
            freezePan();
            if (focusIndex == null) value = lockLimit(value);
            // Radial views keep an explicit selection through small manual zooms (see apply).
            if (focusIndex != null || !layoutOptions().radial) {
                pinnedFocus = focusIndex ?? null;
                pinnedExponent = focusIndex == null ? null : value;
                lockActive = focusIndex != null;
            }
            focusTransition.stop(currentPose());
            if (focusIndex != null) focusTransition.set(focusIndex, value * (layoutOptions().exponentFactor ?? 1), focusWindow);
            camera.aim(value);
            if (reduceMotion.matches) { camera.snap(value); apply(); }
            else if (!frame) frame = requestAnimationFrame(animate);
        };
        // Item hops glide for a fixed time that grows with how far the scene
        // must slide (in pixels at the current zoom), so a hop between two
        // near-identical sizes still reads as a deliberate camera move.
        const hop = (value, focusIndex, focusWindow = 0.3) => {
            // A manual selection must survive equal/near-equal size neighbors.
            // Only direct scale input resumes automatic nearest-size selection.
            pinnedFocus = focusIndex ?? null;
            value = clamp(value, camera.min, camera.max);
            pinnedExponent = focusIndex == null ? null : value;
            lockActive = focusIndex != null;
            if (reduceMotion.matches || focusIndex == null) {
                aim(value, focusIndex, focusWindow);
                if (focusIndex != null && layoutOptions().radial) { glidePan(focusIndex, value, 0); render(); }
                return;
            }
            const options = layoutOptions();
            if (options.radial) {
                const seconds = clamp(0.4 + 0.16 * Math.abs(value - camera.value), 0.4, 1.1);
                glidePan(focusIndex, value, seconds);
                camera.glide(value, seconds);
                if (!frame) frame = requestAnimationFrame(animate);
                return;
            }
            const entries = ScaleJourney.layout(ctx.items, camera.value * (options.exponentFactor ?? 1),
                options.order ?? order, { ...options, ...focusTransition.options() });
            const slide = Math.abs((entries[focusIndex]?.x ?? 500) - 500);
            const seconds = clamp(0.375 + 0.11 * Math.log2(1 + slide / 300), 0.375, 0.85);
            focusTransition.glide(focusIndex, value * (options.exponentFactor ?? 1), focusWindow, seconds, currentPose());
            camera.glide(value, seconds);
            if (!frame) frame = requestAnimationFrame(animate);
        };
        const move = amount => aim(camera.target + amount);
        const sliderInput = e => {
            e.stopImmediatePropagation();
            aim(Number(zoom.input.value));
        };
        const wheel = e => {
            e.preventDefault();
            const pixels = (Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY) * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 400 : 1);
            // Trackpad pinches arrive as Ctrl + wheel with small deltas; scale them up.
            move(-clamp(pixels * (e.ctrlKey ? 0.006 : 0.00045), -0.16, 0.16));
        };
        zoom.input.addEventListener('input', sliderInput, true);
        ctx.stageFrame.addEventListener('wheel', wheel, { passive: false });
        const input = createSpatialInput(ctx.stageFrame, {
            interaction,
            onStart: () => {
                freezePan();
                if (frame) cancelAnimationFrame(frame);
                frame = null; previousTime = null;
                focusTransition.stop(currentPose());
                camera.snap(camera.value);
            },
            onPan: (dx, dy) => {
                if (frame) cancelAnimationFrame(frame);
                frame = null; previousTime = null;
                if (!layoutOptions().radial) {
                    // Linear layouts keep drag-to-zoom.
                    pinnedFocus = null;
                    camera.snap(camera.value - dx * 0.0012);
                    apply();
                    return;
                }
                // Radial layouts pan: drag moves the view; the selection stays selected but
                // the view is no longer locked onto it.
                const box = ScaleRenderers.stageSize(ctx.stage);
                const viewWidth = box.width < 600 ? 560 : 1000;
                const scale = Math.min(box.width / viewWidth, box.height / 500) || 1;
                const f = layoutOptions().exponentFactor ?? 1;
                const unitsPerPixel = 10 ** (camera.value * f) / ScaleJourney.RADIAL_SIZE / scale;
                const current = panAt(camera.value);
                anchor = { x: current.x - dx * unitsPerPixel, y: current.y + dy * unitsPerPixel, exponent: camera.value, manual: true };
                // Panning away ends the lock on a selected item: no zoom limit, no recentering.
                lockActive = false;
                panGlide = null;
                apply();
            },
            onPinch: ratio => {
                if (frame) cancelAnimationFrame(frame);
                frame = null; previousTime = null;
                const f = layoutOptions().exponentFactor ?? 1;
                camera.snap(lockLimit(clamp(camera.value - Math.log10(ratio) / f, camera.min, camera.max)));
                apply();
            },
            onEnd: () => {}
        });
        const click = e => {
            if (input.isControlTarget(e.target)) { input.consumeDraggedClick(); return; }
            if (input.consumeDraggedClick()) { e.preventDefault(); e.stopPropagation(); return; }
            const picked = interaction.pick?.(e.clientX, e.clientY);
            if (picked) { e.preventDefault(); e.stopPropagation(); ctx.focus(ctx.items.indexOf(picked)); }
        };
        ctx.stageFrame.addEventListener('click', click, true);
        ctx.stageFrame.tabIndex = 0;
        ctx.stageFrame.setAttribute('aria-label', 'Scale journey. Scroll or pinch to zoom, drag to pan, drag a 3D object to rotate, or use the left and right arrow keys to select items.');
        // Zoom buttons beside the camera slider, and the hook keyboard shortcuts use.
        // Positive amounts zoom out (toward larger scales).
        const zoomButtons = dom('div', 'experience-zoom-buttons');
        for (const [label, amount, path] of [['Zoom in (+)', -0.25, 'M6 12h12M12 6v12'], ['Zoom out (\u2212)', 0.25, 'M6 12h12']]) {
            const control = dom('button', 'experience-zoom-button');
            control.type = 'button';
            control.title = label;
            control.setAttribute('aria-label', label.replace(/ \(.*\)$/, ''));
            control.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="${path}" /></svg>`;
            control.addEventListener('click', () => move(amount));
            zoomButtons.append(control);
        }
        zoom.element.append(zoomButtons);
        return { update: () => { ctx.updateComparison(); }, frameTo: hop, radialPan: panAt, zoomBy: move,
            // The renderer reports which objects it actually drew on screen, and how far each
            // is (in decades) from the camera's ring size; apply() chooses among them.
            observe: list => { observed = list; },
            focusOptions: () => focusTransition.options(),
            dispose: () => {
                disposed = true;
                cancelAnimationFrame(frame);
                input.dispose();
                zoom.input.removeEventListener('input', sliderInput, true);
                ctx.stageFrame.removeEventListener('wheel', wheel);
                ctx.stageFrame.removeEventListener('click', click, true);
                delete ctx.updateComparison;
            } };
    }
    R.spatial = ctx => {
        const order = { length: 1, area: 2, volume: 3 }[ctx.dimension];
        const zoom = ctx.zoomControl(order, 'Travel through scale');
        zoom.input.min = ScaleJourney.frameExponent(ctx.items, 0, order);
        zoom.input.max = ScaleJourney.frameExponent(ctx.items, ctx.items.length - 1, order);
        zoom.set(clamp(zoom.value, Number(zoom.input.min), Number(zoom.input.max)));
        zoom.input.setAttribute('aria-label', 'Scale camera');
        let areaMaps, modelStage, disposed = false, rulerHTML, attributedModel = null;
        let placement, placementWidth, placementReady;
        const widthFactor = item => {
            const map = areaMaps?.entry(item);
            if (map) return map.width;
            if (order === 2 && /cross-section|surface area|disk|boundary/i.test(item.name)) return 2 / Math.sqrt(Math.PI);
            const model = modelStage?.entry(item);
            if (!model) return 1;
            return (model.presentation?.layout_width_factor ?? 1) *
                (order === 3 && model.geometry === 'sphere' ? Math.cbrt(6 / Math.PI) : 1);
        };
        // Every spatial dimension uses the radial (Scale of the Universe) arrangement.
        const radial = true;
        const extentFactor = item => {
            const map = areaMaps?.entry(item);
            if (map) return map.height;
            if (order === 2 && /cross-section|surface area|disk|boundary/i.test(item.name)) return 2 / Math.sqrt(Math.PI);
            return modelStage?.entry(item)?.presentation?.display_extent_factor ?? 1;
        };
        // An item's world position in the radial layout (units of its own length).
        const radialWorld = index => placement?.[index] &&
            { x: placement[index].u * placement[index].length, y: placement[index].v * placement[index].length };
        const navigationControl = navigation(ctx, order, zoom, render, () => ({ widthFactor, radial, radialWorld }), {
            pick: (x, y) => modelStage?.pick(x, y),
            hover: (item, pointer) => modelStage?.setHover(item, pointer),
            beginRotate: (item, timestamp) => modelStage?.beginRotate(item, timestamp),
            rotate: (item, dx, dy, timestamp) => modelStage?.rotate(item, dx, dy, timestamp),
            releaseRotate: (item, timestamp) => modelStage?.releaseRotate(item, timestamp)
        });
        ctx.host.classList.add('experience--spatial');
        ctx.live.hidden = true;
        const ruler = dom('div', 'experience-corner-ruler');
        const rulerLine = dom('span');
        const rulerLabel = dom('span', 'experience-corner-ruler__label');
        ruler.title = order === 3 ? 'Side length of a cube enclosing the shown volume.'
            : order === 2 ? 'Side length of a square with the shown area.' : 'Length of the scale bar.';
        ruler.append(rulerLine, rulerLabel);
        zoom.element.classList.add('experience-camera-slider');
        zoom.output.hidden = true;
        ctx.stageFrame.append(ruler, zoom.element);
        ctx.caption.textContent = order === 1
            ? 'All objects share one camera that only zooms. Each sits at a distance from the center proportional to its own size, so objects at the current scale ring the center and smaller ones gather toward it; the arrangement is for reading, not physical distance. The ruler uses the listed length; photo framing is approximate. Distances, radii and object diameters retain their dataset definitions. Models are hidden when too small to read or still loading, rather than replaced with photos.'
            : order === 2
            ? 'Equal Earth maps preserve relative area: each full colored footprint, not its rectangular frame, equals the listed area. Planet maps unfold the whole globe under the listed spherical convention. Geographic outlines retain their source shapes, uniformly calibrated to the catalog area. Other disks/squares show equivalent area; their photos only identify the subject. Source and boundary conventions appear in each map note.'
            : 'Spherical models use diameter = (6V/pi)^(1/3). Explicitly volume-calibrated closed meshes enclose the listed representative volume; see each model note. Other models and photos use an equivalent-volume span V^(1/3), not a measured outline or mesh volume. Container capacity is not the volume of its material. Spacing is editorial.';
        ctx.modelEntry = item => order === 2 ? areaMaps?.entry(item) : modelStage?.entry(item);
        const attachModels = () => {
            if (disposed || order === 2 || modelStage || !root.ScaleModels) return;
            modelStage = new ScaleModels.ModelStage(ctx, render, () => {
                const factor = modelStage?.entry(ctx.item)?.presentation?.focus_scale_factor;
                const exponent = ScaleJourney.frameExponent(ctx.items, ctx.index, order) - frameZoom(ctx);
                if (factor && Math.abs(zoom.value - exponent) < 0.05)
                    navigationControl.frameTo(exponent + Math.log10(factor), ctx.index, 1);
            });
            ctx.updateDetail();
            render();
        };
        window.addEventListener('scale-models-ready', attachModels);
        attachModels();
        if (order === 2) areaMaps = new ScaleAreaMaps.Catalog(() => {
            if (!disposed) {
                ctx.updateDetail();
                const exponent = ScaleJourney.frameExponent(ctx.items, ctx.index, order) - frameZoom(ctx);
                const factor = areaMaps.entry(ctx.item)?.presentation.focus_scale_factor || 1;
                if (Math.abs(zoom.value - exponent) < 0.05)
                    navigationControl.frameTo(exponent + Math.log10(factor), ctx.index, 1);
                render();
            }
        });
        // Load models about a decade before they are big enough to draw, nearest the
        // current scale first, a couple at a time, so zooming reveals finished meshes
        // instead of empty slots that fill in. Larger, still-offscreen items load too:
        // zooming out brings them in from the edges.
        function prefetchModels(entries, view) {
            if (order === 2 || !modelStage?.registryReady || modelStage.unavailable) return;
            const wanted = [];
            for (const { item, size } of entries) {
                const entry = modelStage.entry(item);
                if (!entry || modelStage.usedItems.has(item)) continue;
                const drawn = size * (entry.presentation?.display_extent_factor ?? 1) * view.scale;
                if (drawn < MIN_MODEL_PX / 8 || drawn > 12 * view.width * view.scale) continue;
                wanted.push({ item, distance: Math.abs(Math.log10(drawn / (ScaleJourney.RADIAL_SIZE * view.scale))) });
            }
            wanted.sort((a, b) => a.distance - b.distance);
            // Speculation must fit alongside visible models. Remember measured
            // costs after eviction so an oversized neighbor cannot churn forever.
            let slots = modelStage.cacheLimits.maxEntries - modelStage.usedItems.size;
            let bytes = modelStage.cacheLimits.maxBytes;
            for (const item of modelStage.usedItems) bytes -= modelStage.estimatedCost(item);
            for (const { item } of wanted) {
                if (modelStage.pending >= 3 || slots <= 0) break;
                const cost = modelStage.estimatedCost(item);
                if (cost > bytes) continue;
                slots--; bytes -= cost;
                modelStage.prefetch(item);
            }
        }
        ctx.stage._onResize = () => render();
        function render() {
            if (disposed) return;
            ctx.stage.replaceChildren(); modelStage?.begin(zoom.value, radial ? 500 - ScaleJourney.RADIAL_CENTER_Y : undefined);
            const view = viewport(ctx);
            const sky = ramp(zoom.value, [
                [-4, [255, 255, 255]],
                [1.2, [250, 253, 255]],
                [2.2, [171, 220, 248]],
                [6.6, [74, 154, 218]],
                [7.25, [31, 79, 134]],
                [8.5, [8, 23, 47]],
                [10.5, [2, 6, 16]]
            ]);
            const fg = ramp(zoom.value, [
                [-4, [22, 29, 36]],
                [5.9, [22, 29, 36]],
                [6.35, [255, 220, 24]],
                [7.15, [255, 239, 116]],
                [7.75, [248, 250, 255]]
            ]);
            const edgeSky = zoom.value <= -3 ? sky : sky.map(value => Math.max(0, value - 8));
            ctx.stageFrame.style.background = `radial-gradient(ellipse at 35% 35%,rgb(${sky.join(',')}),rgb(${edgeSky.join(',')}))`;
            ctx.stage.style.color = `rgb(${fg.join(',')})`;
            ctx.stageFrame.style.setProperty('--journey-ink', ctx.stage.style.color);
            ctx.stage.style.setProperty('--journey-label-halo', `rgb(${sky.join(',')})`);
            ruler.style.color = ctx.stage.style.color;
            // Keep nearby offscreen objects mounted so the SVG viewport, rather than
            // JavaScript culling, controls the exact moment they cross an edge.
            const ready = order === 2 ? areaMaps?.entries.size : modelStage?.registryReady;
            if (radial && (!placement || placementWidth !== view.width || placementReady !== ready)) {
                placement = ScaleJourney.radialPlacement(ctx.items, order, { ...view, widthFactor, extentFactor });
                placementWidth = view.width;
                placementReady = ready;
            }
            const entries = radial
                ? ScaleJourney.radialLayout(ctx.items, zoom.value, order,
                    { ...view, placement, overscan: 40, pan: navigationControl.radialPan(zoom.value) })
                : ScaleJourney.layout(ctx.items, zoom.value, order, {
                    ...view,
                    widthFactor,
                    ...navigationControl.focusOptions(),
                    overscan: view.width * 0.75
                });
            const labels = [], onScreen = [];
            const ringPx = ScaleJourney.RADIAL_SIZE * 0.85 * view.scale;
            entries.filter(entry => entry.visible).forEach(({item, index, x, y, size, center}) => {
                const entry = ctx.modelEntry(item);
                // A sphere's diameter differs from the cube root of its volume.
                const visualSize = order === 3 && entry?.geometry === 'sphere' ? size * Math.cbrt(6 / Math.PI) : size;
                const modelExtent = entry?.presentation?.display_extent_factor ?? 1;
                const extent = areaMaps?.entry(item) ? size * Math.max(entry.width, entry.height)
                    : order === 2 && /cross-section|surface area|disk|boundary/i.test(item.name)
                    ? size * 2/Math.sqrt(Math.PI) : visualSize * modelExtent;
                // Sub-pixel objects would still fetch their GLB or photo; they load when they grow.
                if (extent * view.scale < MIN_DRAWN_PX) return;
                // Do not flash a photo while the model registry/mesh loads, or
                // substitute one when a distant model crosses its draw threshold.
                const useModel = order !== 2 && entry && !modelStage?.unavailable;
                if (order !== 2 && !modelStage?.registryReady && !modelStage?.unavailable) return;
                if (radial && useModel && extent * view.scale < MIN_MODEL_PX) return;
                if (x >= view.left && x <= view.left + view.width && center >= 0 && center <= 500 &&
                    extent * view.scale >= IN_VIEW_PX)
                    onScreen.push({ index, distance: Math.abs(Math.log10(extent * view.scale / ringPx)) });
                const g = ctx.object(ctx.stage, item, x, y, extent, extent, { image: false });
                if (useModel) {
                    g.dataset.modelIndex = ctx.items.indexOf(item);
                    g.style.pointerEvents = 'none';
                }
                if (useModel) g.dataset.modelState = modelStage.draw(item, x, y, visualSize) ? 'ready' : 'loading';
                else if (!areaMaps?.draw(g, item, x, y, size)) {
                    const src = ctx.image(item);
                    if (order === 2) {
                        const circular = /cross-section|surface area|disk|boundary/i.test(item.name);
                        if (circular) g.append(svg('circle', { cx:x, cy:y-size/Math.sqrt(Math.PI), r:size/Math.sqrt(Math.PI), class:'shape' }));
                        else g.append(svg('rect', { x:x-size/2,y:y-size,width:size,height:size,class:'shape',rx:2 }));
                    } else if (!src) {
                        g.append(svg('circle', { cx:x,cy:y-size/2,r:size/2,class:'shape' }));
                    }
                    if (src) g.append(svg('image', { href:src, x:x-size/2,y:y-size,width:size,height:size,
                        preserveAspectRatio:'xMidYMax meet' }));
                }
                // Radial view: labels scale with their object (a tenth of its drawn size) between
                // 9 and 40 px, and only fade out once the object is nearly too small to draw.
                const drawnPx = extent * view.scale;
                const fontSize = radial
                    ? Math.min(Math.max(ScaleJourney.LABEL_EM * extent, 9 / view.scale), 40 / view.scale)
                    : 19 * extent / ScaleJourney.BASE_SIZE;
                const labelOpacity = radial ? clamp((drawnPx - 12) / 16, 0, 1) : clamp((fontSize * view.scale - 7) / 5, 0, 1);
                const selected = item === ctx.item && ctx.explicitSelection;
                if (labelOpacity > 0) {
                    const name = entry?.display_label || item.name;
                    const labelY = radial ? y + fontSize * 1.25 : y + fontSize * 1.8;
                    const text = svg('text',{x,y:labelY,'text-anchor':'middle',class:'journey-object-label',style:`font-size:${fontSize}px${selected ? ';font-weight:700' : ''}`,opacity:labelOpacity},name);
                    text.dataset.labelPriority = selected ? '200' : '100';
                    labels.push({ text, x, y: labelY, fontSize, width: 0.56 * fontSize * name.length,
                        rank: (selected ? 1e9 : 0) + drawnPx });
                }
            });
            navigationControl.observe(onScreen);
            prefetchModels(entries, view);
            // Keep the selected item's label, then larger objects' labels; drop any that collide.
            const kept = [];
            for (const label of labels.sort((a, b) => b.rank - a.rank)) {
                const box = { left: label.x - label.width / 2, right: label.x + label.width / 2,
                    top: label.y - label.fontSize, bottom: label.y + 0.25 * label.fontSize };
                if (radial && kept.some(other => box.left < other.right && box.right > other.left &&
                    box.top < other.bottom && box.bottom > other.top)) continue;
                kept.push(box);
                ctx.stage.append(label.text);
            }
            modelStage?.finish(zoom.value);
            const rulerWidth = 112;
            const rulerValue = power(zoom.value) * rulerWidth / ((radial ? ScaleJourney.RADIAL_SIZE : ScaleJourney.BASE_SIZE) * view.scale);
            rulerLine.style.width = `${rulerWidth}px`;
            const formattedRuler = ctx.app.formatTooltipValueHTML(
                ctx.app.formatValueForCurrentUnit(rulerValue ** order, 2, true),
                ctx.app.getCurrentUnitDefinition()?.symbol || 'm');
            const nextRulerHTML = order === 1 ? formattedRuler
                : `${order === 3 ? '&#8731;' : '&radic;'}(${formattedRuler})`;
            if (nextRulerHTML !== rulerHTML) rulerLabel.innerHTML = rulerHTML = nextRulerHTML;
            navigationControl.update();
            const current = ctx.modelEntry(ctx.item);
            if (current === attributedModel) return;
            attributedModel = current;
            ctx.attribution.replaceChildren();
            if (current?.procedural) {
                ctx.attribution.append(document.createTextNode('Procedural 3D illustration'));
                if (current.basis_url) {
                    const basis = dom('a', '', current.basis_label || 'Orbital basis: MIT OpenCourseWare');
                    basis.href = current.basis_url;
                    basis.target = '_blank';
                    basis.rel = 'noopener noreferrer';
                    ctx.attribution.append(basis);
                }
            } else if (current) {
                const source = dom('a', '', `${order === 2 ? 'Map' : '3D model'}: ${current.author}`);
                source.href = current.source;
                source.target = '_blank';
                source.rel = 'noopener noreferrer';
                const license = dom('a', '', current.license);
                license.href = current.license_url;
                license.target = '_blank';
                license.rel = 'noopener noreferrer';
                ctx.attribution.append(source, license);
                if (current.sketchfab_uid) ctx.attribution.append(dom('span', '', 'adapted for web'));
            }
        }
        return { render, zoomBy: amount => navigationControl.zoomBy(amount), frameOffset: () => frameZoom(ctx), get modelStage() { return modelStage; }, get areaMaps() { return areaMaps; }, focus: frame => {
            if (frame) {
                const presentation = ctx.modelEntry(ctx.item)?.presentation || {};
                const exponent = ScaleJourney.frameExponent(ctx.items,ctx.index,order,{widthFactor}) - frameZoom(ctx) +
                    Math.log10(presentation.focus_scale_factor || 1);
                navigationControl.frameTo(exponent, ctx.index, presentation.focus_scale_factor ? 1 : 0.3);
            }
        },
            dispose: () => { disposed=true; delete ctx.modelEntry; ctx.host.classList.remove('experience--spatial'); modelStage?.dispose(); window.removeEventListener('scale-models-ready',attachModels); navigationControl.dispose(); } };
    };
    function board(parent, x, y, width, seed) {
        const cell=width/20;
        parent.append(svg('rect',{x,y,width,height:width,fill:'#dcb779',stroke:'#735329'}));
        for(let i=1;i<=19;i++) { parent.append(line(x+cell,y+i*cell,x+width-cell,y+i*cell));parent.append(line(x+i*cell,y+cell,x+i*cell,y+width-cell)); }
        for(let r=2;r<19;r+=2) for(let c=2;c<19;c+=2) {
            seed=(1664525*seed+1013904223)>>>0;
            if(seed%3)parent.append(svg('circle',{cx:x+c*cell,cy:y+r*cell,r:cell*.43,fill:seed%2?'#202020':'#fafafa'}));
        }
    }
    R.counts = ctx => {
        const zoom=ctx.zoomControl(1,'Count window');
        let examples=0,disposed=false,placement,placementWidth;
        // Counts use the same radial arrangement as the spatial explorers: each total is a
        // square of tiles whose side grows with the square root of the count.
        const radialWorld = index => placement?.[index] &&
            { x: placement[index].u * placement[index].length, y: placement[index].v * placement[index].length };
        const nav=navigation(ctx,1,zoom,render,()=>({order:2,exponentFactor:.5,radial:true,radialWorld}));
        const variants=button(ctx.settings,'Different Go examples',()=>{examples++;render();});
        // Same full-height stage and overlay camera slider as the spatial explorers.
        ctx.host.classList.add('experience--spatial');
        zoom.element.classList.add('experience-camera-slider');
        zoom.output.hidden=true;
        ctx.stageFrame.append(zoom.element);
        ctx.stage._onResize=()=>render();
        function render(){
            if(disposed)return;
            ctx.stage.replaceChildren();
            const view=viewport(ctx);
            const each=power(Math.max(0,Math.ceil(zoom.value-3.5)));
            if(!placement||placementWidth!==view.width){
                placement=ScaleJourney.radialPlacement(ctx.items,2,{...view});
                placementWidth=view.width;
            }
            const rows=ScaleJourney.radialLayout(ctx.items,zoom.value/2,2,{...view,placement,overscan:40,pan:nav.radialPan(zoom.value)});
            const defs=svg('defs'); ctx.stage.append(defs);
            let totalShown=0, imagesShown=false, clipped=false;
            const onScreen=[], labels=[], ringPx=ScaleJourney.RADIAL_SIZE*0.85*view.scale;
            variants.hidden=!/Legal Go positions/i.test(ctx.item.name);
            for(const {item,index,x,y,size,center} of rows.filter(p=>p.visible&&p.size*view.scale>=1&&p.size<=5000)){
                if(x>=view.left&&x<=view.left+view.width&&center>=0&&center<=500&&size*view.scale>=IN_VIEW_PX)
                    onScreen.push({index,distance:Math.abs(Math.log10(size*view.scale/ringPx))});
                const g=ctx.object(ctx.stage,item,x,y,size,size,{image:false});
                const go=/Legal Go positions/i.test(item.name);
                if(go) {
                    const w=Math.min(800,size)/2;
                    for(let i=0;i<4;i++)board(g,x-w+(i%2)*w,y-2*w+Math.floor(i/2)*w,w-4,examples*7+i+1);
                }else{
                    const represented=item.value/each, visible=Math.min(12000,Math.floor(represented));
                    totalShown+=visible;
                    clipped ||= represented > 12000;
                    const columns=Math.max(1,Math.ceil(Math.sqrt(visible)));
                    const extent=Math.min(800,size), cell=extent/columns;
                    const src=ctx.image(item);
                    const id=`count-tile-${index}`;
                    const pattern=svg('pattern',{id,patternUnits:'userSpaceOnUse',x:x-extent/2,y:y-extent,width:cell,height:cell});
                    if(src) {
                        pattern.append(svg('image',{href:src,x:cell*.07,y:cell*.07,width:cell*.86,height:cell*.86,preserveAspectRatio:'xMidYMid meet'}));
                        imagesShown=true;
                    } else pattern.append(svg('circle',{cx:cell/2,cy:cell/2,r:cell*.34,fill:'var(--accent-color)'}));
                    defs.append(pattern);
                    // A tiled image pattern draws thousands of replicas without thousands of DOM nodes.
                    const fullRows=Math.floor(visible/columns), remainder=visible%columns;
                    if(fullRows)g.append(svg('rect',{x:x-extent/2,y:y-extent,width:extent,height:fullRows*cell,fill:`url(#${id})`,'data-replicas':fullRows*columns}));
                    if(remainder)g.append(svg('rect',{x:x-extent/2,y:y-extent+fullRows*cell,width:remainder*cell,height:cell,fill:`url(#${id})`,'data-replicas':remainder}));
                    if(represented<1)g.append(svg('circle',{cx:x,cy:y-size/2,r:size/2,fill:'var(--accent-color)'}));
                }
                const drawnPx=size*view.scale, opacity=clamp((drawnPx-12)/16,0,1);
                if(opacity>0){
                    const fontSize=Math.min(Math.max(ScaleJourney.LABEL_EM*size,9/view.scale),40/view.scale);
                    const selected=item===ctx.item&&ctx.explicitSelection;
                    const text=svg('text',{x,y:y+fontSize*1.25,'text-anchor':'middle',class:'journey-object-label',
                        style:`font-size:${fontSize}px${selected?';font-weight:700':''}`,opacity},item.name);
                    labels.push({text,x,y:y+fontSize*1.25,fontSize,width:.56*fontSize*item.name.length,rank:(selected?1e9:0)+drawnPx});
                }
            }
            const kept=[];
            for(const label of labels.sort((a,b)=>b.rank-a.rank)){
                const box={left:label.x-label.width/2,right:label.x+label.width/2,top:label.y-label.fontSize,bottom:label.y+.25*label.fontSize};
                if(kept.some(o=>box.left<o.right&&box.right>o.left&&box.top<o.bottom&&box.bottom>o.top))continue;
                kept.push(box); ctx.stage.append(label.text);
            }
            nav.observe(onScreen);
            ctx.stage.append(svg('text',{x:view.left+14,y:470,class:'counts-multiplier',style:`font-size:${13/view.scale}px`},`1 ${imagesShown?'tile':'dot'} = ${number(each)} counted units`));
            ctx.live.textContent=`${/Legal Go positions/i.test(ctx.item.name)?'Four legal examples, not an enumeration':`${totalShown.toLocaleString()} replicas drawn${clipped?'; larger totals truncated at 12,000':''}`}`;
            ctx.caption.textContent='Each total is a square of image tiles whose side grows with the square root of the count, arranged so totals near the current scale ring the center and smaller ones gather toward it. The tiles identify what is counted, using illustrative photographs rather than measured outlines. A tile represents one object only when its multiplier is 1; otherwise it represents the explicit cluster size shown. All items share that multiplier. Totals below one cluster shrink in dot area; large totals are truncated at 12,000 tiles. Count alternatives (such as Go positions) are not physically coexisting objects. The four Go boards are valid illustrative positions, not a uniform random sample.';
            nav.update();
        }
        return {render,zoomBy:amount=>nav.zoomBy(amount*2),focus:frame=>{if(frame)nav.frameTo(2*(ScaleJourney.frameExponent(ctx.items,ctx.index,2)-frameZoom(ctx)),ctx.index);},dispose:()=>{disposed=true;ctx.host.classList.remove('experience--spatial');nav.dispose();}};
    };
})(globalThis);
