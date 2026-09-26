(function (root) {
    const { dom, svg, Slider, Clock, button, number } = ScaleControls;
    const { log, nearest, clamp } = ScaleMath;
    const registry = {
        length: ['Size explorer', 'spatial'],
        area: ['Area explorer', 'spatial'],
        volume: ['Volume explorer', 'spatial'],
        counts: ['Count explorer', 'counts'],
        brightness: ['Light explorer', 'brightness'],
        speed: ['Motion explorer', 'motion'],
        acceleration: ['Motion explorer', 'motion'],
        jerk: ['Motion explorer', 'motion'],
        frequency: ['Cycle explorer', 'motion'],
        'sound-frequency': ['Cycle explorer', 'motion'],
        'angular-velocity': ['Spin explorer', 'motion'],
        angle: ['Viewing angle', 'angle'],
        'visual-angle': ['Viewing angle', 'angle']
    };
    class DimensionExperiences {
        constructor(app) {
            this.app = app;
            this.active = false;
            this.host = document.getElementById('dimension-experience');
            this.switcher = document.getElementById('view-switch');
            this.assets = {};
            this.images = new Map();
            this.clock = new Clock((time) => this.renderer?.render(time));
            this.resize = new ResizeObserver(() =>
                this.renderer?.render(this.clock.time)
            );
            this.resize.observe(this.host);
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    this.pause();
                    this.audio?.stop();
                }
            });
            window.addEventListener('pagehide', () => {
                this.pause();
                this.audio?.stop();
            });
            fetch('content/visualizations/assets.json')
                .then((r) => (r.ok ? r.json() : {}))
                .then((assets) => {
                    this.assets = assets;
                    if (this.active) this.renderer?.render(this.clock.time);
                })
                .catch(() => {});
            fetch('content/visualizations/brightness-images.json')
                .then(r => r.ok ? r.json() : {})
                .then(registry => {
                    this.explorerImages = {...this.explorerImages,...registry.images};
                    if (this.active) { this.updateDetail(); this.renderer?.render(this.clock.time); }
                }).catch(() => {});
            fetch('content/visualizations/motion-images.json')
                .then(r => r.ok ? r.json() : {})
                .then(registry => {
                    this.explorerImages = {...this.explorerImages,...registry.images};
                    if (this.active) { this.updateDetail(); this.renderer?.render(this.clock.time); }
                }).catch(() => {});
            this.audio = new ScaleAudio(app);
        }
        get dimension() {
            return this.app.currentDimension;
        }
        get item() {
            return this.items[this.index];
        }
        get config() {
            return registry[this.dimension];
        }
        readItems() {
            return this.app
                .getAllItems()
                .filter(
                    (item) =>
                        Number.isFinite(Number(item.value)) &&
                        Number(item.value) > 0
                )
                .map((item) => ({ ...item, value: Number(item.value) }))
                .sort((a, b) => a.value - b.value);
        }
        fingerprint(items) {
            return JSON.stringify(
                items.map(
                    ({ id, name, value, description, source, imageData }) => [
                        id,
                        name,
                        value,
                        description,
                        source,
                        imageData
                    ]
                )
            );
        }
        get pair() {
            return [this.items[Math.max(0, this.index - 1)], this.item].filter(
                (x, i, a) => a.indexOf(x) === i
            );
        }
        preference() {
            try {
                return localStorage.getItem(`scale-view:${this.dimension}`);
            } catch {
                return null;
            }
        }
        onDimension() {
            this.renderer?.dispose?.();
            this.pause();
            this.audio.stop();
            this.active = false;
            this.items = this.readItems();
            this.itemsFingerprint = this.fingerprint(this.items);
            const initialExponent = ['angle', 'visual-angle'].includes(this.dimension) ? -1 : 0;
            // ?item=Exact%20Name deep-links to an item (first load only).
            const linked = this.linkedItem !== undefined ? null
                : new URLSearchParams(location.search).get('item');
            this.linkedItem ??= linked;
            const linkedIndex = linked ? this.items.findIndex(item => item.name === linked) : -1;
            this.index = linkedIndex >= 0 ? linkedIndex : this.items.length
                ? this.items.indexOf(nearest(this.items, initialExponent))
                : 0;
            this.switcher.replaceChildren();
            this.switcher.hidden = !this.config || !this.items.length;
            if (this.config && this.items.length) {
                this.interactiveButton = button(
                    this.switcher,
                    this.config[0],
                    () => this.setMode('interactive')
                );
                this.logButton = button(
                    this.switcher,
                    this.app.isLinearScale() ? 'Scale plot' : 'Logarithmic',
                    () => this.setMode('log')
                );
            }
            this.setMode(
                this.config && this.items.length && this.preference() !== 'log'
                    ? 'interactive'
                    : 'log',
                false
            );
        }
        setMode(mode, save = true) {
            const wasActive = this.active;
            this.renderer?.dispose?.();
            this.pause();
            this.audio.stop();
            this.app.hideTooltip();
            this.active =
                mode === 'interactive' &&
                Boolean(this.config) &&
                this.items.length > 0;
            if (save) {
                try {
                    localStorage.setItem(
                        `scale-view:${this.dimension}`,
                        this.active ? 'interactive' : 'log'
                    );
                } catch {}
            }
            document.body.dataset.experience = this.active
                ? 'interactive'
                : 'log';
            document.body.dataset.experienceDimension = this.active ? this.dimension : '';
            this.app.plotContainer.hidden = this.active;
            this.host.hidden = !this.active;
            this.interactiveButton?.setAttribute(
                'aria-pressed',
                String(this.active)
            );
            this.logButton?.setAttribute('aria-pressed', String(!this.active));
            if (this.active) this.mount();
            else {
                this.toolbarCleanup?.();
                this.toolbarCleanup = null;
                this.renderer = null;
                if (wasActive) this.app.resizePlot();
            }
        }
        mount() {
            this.toolbarCleanup?.();
            this.host.replaceChildren();
            this.images.clear();
            const toolbar = dom('div', 'experience-toolbar');
            const picker = dom('div', 'experience-picker');
            const pickerLabel = dom('span', 'experience-picker__label', 'Explore');
            this.select = dom('select', 'experience-select sr-only');
            this.select.tabIndex = -1;
            this.select.setAttribute('aria-hidden', 'true');
            this.items.forEach((item, index) => {
                const option = dom('option', '', item.name);
                option.value = index;
                this.select.append(option);
            });
            this.select.value = this.index;
            this.pickerToggle = dom('button', 'experience-picker-toggle');
            this.pickerToggle.type = 'button';
            this.pickerToggle.setAttribute('aria-expanded', 'false');
            this.pickerToggle.setAttribute('aria-controls', 'experience-picker-panel');
            this.pickerCurrent = dom('span', '', this.item.name);
            this.pickerToggle.append(this.pickerCurrent, dom('span', 'dimension-browser-toggle__chevron', '▾'));
            this.pickerPanel = dom('div', 'experience-picker-panel');
            this.pickerPanel.id = 'experience-picker-panel';
            this.pickerPanel.hidden = true;
            const search = dom('input', 'experience-picker-search');
            Object.assign(search, { type: 'search', placeholder: 'Search items', autocomplete: 'off', spellcheck: false });
            search.setAttribute('aria-label', 'Search items');
            const options = dom('div', 'experience-picker-options');
            this.pickerButtons = this.items.map((item, index) => {
                const option = dom('button', 'experience-picker-option', item.name);
                option.type = 'button';
                option.dataset.search = item.name.toLocaleLowerCase();
                option.addEventListener('click', () => {
                    this.focus(index);
                    closePicker();
                });
                options.append(option);
                return option;
            });
            this.pickerEmpty = dom('p', 'experience-picker-empty', 'No items match that search.');
            this.pickerEmpty.hidden = true;
            this.pickerPanel.append(search, options, this.pickerEmpty);
            picker.append(pickerLabel, this.pickerToggle, this.select, this.pickerPanel);
            toolbar.append(picker);
            const closePicker = () => {
                this.pickerPanel.hidden = true;
                this.pickerToggle.classList.remove('is-open');
                this.pickerToggle.setAttribute('aria-expanded', 'false');
                search.value = '';
                this.pickerButtons.forEach(option => option.hidden = false);
                this.pickerEmpty.hidden = true;
            };
            const openPicker = () => {
                this.pickerPanel.hidden = false;
                this.pickerToggle.classList.add('is-open');
                this.pickerToggle.setAttribute('aria-expanded', 'true');
                search.focus();
            };
            this.pickerToggle.addEventListener('click', () => this.pickerPanel.hidden ? openPicker() : closePicker());
            search.addEventListener('input', () => {
                const query = search.value.trim().toLocaleLowerCase();
                let matches = 0;
                this.pickerButtons.forEach(option => {
                    option.hidden = Boolean(query) && !option.dataset.search.includes(query);
                    if (!option.hidden) matches++;
                });
                this.pickerEmpty.hidden = matches !== 0;
            });
            const info = dom('div', 'experience-info');
            const infoButton = dom('button', 'experience-info__button', 'i');
            infoButton.type = 'button';
            infoButton.setAttribute('aria-label', 'How this visualization works');
            infoButton.setAttribute('aria-expanded', 'false');
            const infoPanel = dom('div', 'experience-info__panel');
            infoPanel.setAttribute('role', 'tooltip');
            infoButton.addEventListener('click', () => {
                const open = info.classList.toggle('is-open');
                infoButton.setAttribute('aria-expanded', String(open));
            });
            info.append(infoButton, infoPanel);
            this.previous = button(toolbar, 'Previous', () =>
                this.focus(this.index - 1)
            );
            this.next = button(toolbar, 'Next', () =>
                this.focus(this.index + 1)
            );
            this.reset = button(toolbar, 'Frame item', () =>
                this.focus(this.index)
            );
            const body = dom('div', 'experience-body');
            const visual = dom('div', 'experience-visual');
            this.stage = svg('svg', {
                viewBox: '0 0 1000 500',
                class: 'experience-stage',
                role: 'group',
                'aria-label': this.config[0]
            });
            this.caption = dom('p', 'experience-caption');
            this.comparison = dom('div', 'experience-comparison');
            this.live = dom('p', 'experience-live');
            this.settings = dom('div', 'experience-settings');
            this.attribution = dom('div', 'experience-attribution');
            infoPanel.append(this.caption, this.attribution);
            toolbar.append(info);
            this.stageFrame = dom('div', 'experience-stage-frame');
            this.stageFrame.append(this.stage);
            visual.append(
                this.stageFrame,
                this.comparison,
                this.live,
                this.settings
            );
            this.detail = dom('article', 'experience-detail');
            this.detail.setAttribute('aria-label', 'Selected item description');
            body.append(visual, this.detail);
            this.host.append(toolbar, body);
            const outside = (event) => {
                if (!picker.contains(event.target)) closePicker();
                if (!info.contains(event.target)) {
                    info.classList.remove('is-open');
                    infoButton.setAttribute('aria-expanded', 'false');
                }
            };
            const escape = (event) => {
                if (event.key !== 'Escape') return;
                closePicker();
                info.classList.remove('is-open');
                infoButton.setAttribute('aria-expanded', 'false');
                this.pickerToggle.focus();
            };
            document.addEventListener('pointerdown', outside);
            document.addEventListener('keydown', escape);
            this.toolbarCleanup = () => {
                document.removeEventListener('pointerdown', outside);
                document.removeEventListener('keydown', escape);
            };
            this.clock.reset();
            this.renderer = ScaleRenderers[this.config[1]](this);
            this.focus(this.index);
        }
        focus(index, frame = true) {
            this.index = clamp(index, 0, this.items.length - 1);
            this.select.value = this.index;
            if (this.pickerCurrent) this.pickerCurrent.textContent = this.item.name;
            this.pickerButtons?.forEach((option, optionIndex) => {
                option.classList.toggle('is-active', optionIndex === this.index);
                option.setAttribute('aria-current', optionIndex === this.index ? 'true' : 'false');
            });
            this.previous.disabled = this.index === 0;
            this.next.disabled = this.index === this.items.length - 1;
            this.clock.reset();
            this.updateDetail();
            this.updateComparison();
            this.renderer?.focus?.(frame);
            this.renderer?.render(0);
        }
        updateDetail() {
            const item = this.item;
            const model = this.modelEntry?.(item);
            const title = dom('h2', '', this.item.name);
            const value = dom('div', 'experience-value');
            const photometry = this.dimension === 'brightness' && root.ScaleRenderers.photometry?.(this.item);
            value.innerHTML = this.app.formatTooltipValueHTML(
                photometry && photometry.kind !== 'luminance' ? number(this.item.value) : this.app.formatValueForCurrentUnit(this.item.value, 2, true),
                photometry && photometry.kind !== 'luminance' ? photometry.unit : this.app.getCurrentUnitDefinition()?.symbol || ''
            );
            if (!photometry || photometry.kind === 'luminance')
                this.app.enableUnitConversions(value, this.item.value);
            this.app.typesetMathIfReady(value);
            const prose = dom('div');
            this.app.setRichText(
                prose,
                this.app.buildTooltipDescriptionMarkdown(
                    this.item,
                    this.item.description ||
                        this.item.description_long ||
                        this.item.description_medium ||
                        ''
                )
            );
            const modelNote = model?.note ? dom('section', 'experience-model-note') : null;
            if (modelNote) modelNote.append(dom('h3', '', 'What this 3D model shows'),
                dom('p', '', model.note));
            this.detail.replaceChildren(title, value, ...(modelNote ? [modelNote] : []), prose);
            const thumbnailButton = dom('button', 'experience-detail-image-button');
            thumbnailButton.type = 'button';
            thumbnailButton.hidden = true;
            thumbnailButton.setAttribute('aria-label', `Open full image of ${item.name}`);
            const thumbnail = dom('img', 'experience-detail-image');
            thumbnail.alt = `${item.name} (illustrative image)`;
            thumbnailButton.append(thumbnail);
            this.detail.prepend(thumbnailButton);
            this.resolveImage(item)
                .then((info) => {
                    if (!thumbnail.isConnected || this.item !== item) return;
                    const src = typeof info === 'string' ? info : info?.path;
                    if (!src) return;
                    const fullPath = typeof info === 'string' ? info : info.fullPath || info.path;
                    thumbnailButton.onclick = () => this.app.openImageModal(fullPath, item.name);
                    thumbnail.onload = () => {
                        thumbnailButton.hidden = false;
                    };
                    thumbnail.onerror = () => {
                        thumbnailButton.hidden = true;
                    };
                    thumbnail.src = src;
                });
            const sources = dom('div', 'experience-detail-sources');
            const addSource = (label, href) => {
                if (!/^https?:\/\//.test(href || '')) return;
                if (sources.childNodes.length) sources.append(document.createTextNode(' · '));
                const link = dom('a', '', label);
                Object.assign(link, { href, target: '_blank', rel: 'noopener noreferrer' });
                sources.append(link);
            };
            addSource('Source', item.source);
            const modelSource = model?.source || model?.basis_url;
            if (modelSource !== item.source)
                addSource(model?.link_label || (model?.procedural ? 'Model basis' : '3D model'), modelSource);
            if (sources.childNodes.length) this.detail.append(sources);
            this.detail.scrollTop = 0;
        }
        updateComparison() {
            this.comparison.replaceChildren();
            const items = ['angle', 'visual-angle'].includes(this.dimension)
                ? [this.item]
                : this.pair;
            for (const item of items)
                button(this.comparison, item.name, () =>
                    this.focus(this.items.indexOf(item))
                );
        }
        refresh() {
            if (!this.active) return;
            const items = this.readItems();
            if (this.fingerprint(items) !== this.itemsFingerprint) {
                const id = this.item.id,
                    name = this.item.name;
                this.onDimension();
                if (this.active)
                    this.focus(
                        Math.max(
                            0,
                            this.items.findIndex((i) =>
                                id ? i.id === id : i.name === name
                            )
                        )
                    );
                return;
            }
            this.updateDetail();
            this.updateComparison();
            this.renderer?.render(this.clock.time);
        }
        pause() {
            this.clock.stop();
            if (this.playButton) this.playButton.textContent = 'Play';
        }
        timeControls(defaultExponent) {
            this.playButton = button(this.settings, 'Play', () => {
                if (this.clock.playing) this.pause();
                else {
                    this.clock.start();
                    this.playButton.textContent = 'Pause';
                }
            });
            button(this.settings, 'Restart time', () => {
                this.clock.reset();
                this.renderer.render(0);
            });
            this.timeSlider = new Slider(this.settings, {
                label: 'Time scale',
                min: -3,
                max: 3,
                value: defaultExponent,
                format: (x) =>
                    `${number(10 ** x)} simulated seconds / real second`,
                onChange: (x) => {
                    this.clock.rate = 10 ** x;
                    this.renderer?.render(this.clock.time);
                }
            });
            this.clock.rate = 10 ** defaultExponent;
        }
        zoomControl(order = 1, label = 'Zoom: reference span') {
            return new Slider(this.settings, {
                label,
                step: 'any',
                min: log(this.items[0].value) / order - 1,
                max: log(this.items.at(-1).value) / order + 1,
                value: log(this.item.value) / order,
                format: (x) =>
                    `${number(10 ** x)} ${order === 1 && this.dimension === 'counts' ? 'count' : 'm'}`,
                onChange: (x) => {
                    const index = this.items.indexOf(
                        nearest(this.items, x, order)
                    );
                    if (index !== this.index) this.focus(index, false);
                    this.renderer.render(this.clock.time);
                }
            });
        }
        object(group, item, x, y, width, height, { image = true } = {}) {
            const w = clamp(width, 0, 4000),
                h = clamp(height, 0, 4000);
            const g = svg('g', {
                class: 'experience-object',
                role: 'button',
                tabindex: '0',
                'aria-label': `Focus ${item.name}`
            });
            g.append(
                svg('rect', {
                    x: x - Math.max(44, w) / 2,
                    y: y - h,
                    width: Math.max(44, w),
                    height: Math.max(44, h),
                    fill: 'transparent'
                })
            );
            const focus = () => this.focus(this.items.indexOf(item));
            g.addEventListener('click', focus);
            g.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    focus();
                }
            });
            if (image && w >= 1 && h >= 1) {
                const src = this.image(item);
                if (src)
                    g.append(
                        svg('image', {
                            href: src,
                            x: x - w / 2,
                            y: y - h,
                            width: w,
                            height: h,
                            preserveAspectRatio: 'xMidYMid meet'
                        })
                    );
                else
                    g.append(
                        svg('rect', {
                            x: x - w / 2,
                            y: y - h,
                            width: w,
                            height: h,
                            class: 'shape'
                        })
                    );
            }
            group.append(g);
            return g;
        }
        image(item) {
            const override = this.explorerImages?.[this.dimension]?.[item.name] || this.assets.images?.[this.dimension]?.[item.name];
            if (override?.src) return override.src;
            if (!this.images.has(item)) {
                this.images.set(item, null);
                const dimension = this.dimension;
                this.resolveImage(item)
                    .then((info) => {
                        if (dimension !== this.dimension || !this.active)
                            return;
                        this.images.set(
                            item,
                            typeof info === 'string' ? info : info?.path || ''
                        );
                        this.renderer?.render(this.clock.time);
                    });
            }
            return this.images.get(item);
        }
        async resolveImage(item) {
            const override = this.explorerImages?.[this.dimension]?.[item.name] || this.assets.images?.[this.dimension]?.[item.name];
            if (override?.src) return override.src;
            const path = this.app.getImagePath(item.name);
            return path ? this.app.checkImageExists(path, true) : null;
        }
        label(item, x, y) {
            const text = svg('text', {
                x,
                y,
                'text-anchor': 'middle',
                class: 'object-label'
            });
            // Two short lines keep the two object lanes from overlapping.
            const words = item.name.split(' ');
            let line = '',
                lines = [];
            for (const word of words) {
                if ((line + word).length > 28 && line) {
                    lines.push(line);
                    line = '';
                }
                line += `${word} `;
            }
            lines.push(line.trim());
            lines
                .slice(0, 3)
                .forEach((part, i) =>
                    text.append(svg('tspan', { x, dy: i ? 20 : 0 }, part))
                );
            this.stage.append(text);
        }
        addTooltip(item, parent) {
            parent.querySelector('.experience-tooltip-extra')?.remove();
            const extra = dom('div', 'experience-tooltip-extra');
            if (['angle', 'visual-angle'].includes(this.dimension))
                ScaleRenderers.angleDiagram(extra, Number(item.value));
            if (this.dimension === 'sound-intensity')
                this.audio.controls(extra, item);
            parent.append(extra);
        }
    }
    root.DimensionExperiences = DimensionExperiences;
})(globalThis);
