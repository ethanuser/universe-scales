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
            this.fullscreenState = null;
            this.fullscreenRequest = 0;
            this.onFullscreenChange = () => this.handleFullscreenChange();
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
            this.exitFullscreen();
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
            this.exitFullscreen();
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
            const toolbarMain = dom('div', 'experience-toolbar__main');
            const toolbarActions = dom('div', 'experience-toolbar__actions');
            toolbar.append(toolbarMain, toolbarActions);
            const picker = dom('div', 'experience-picker');
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
            this.pickerToggle.setAttribute('aria-keyshortcuts', 'Control+k Meta+k');
            this.pickerToggle.title = 'Search items (Ctrl/Cmd+K)';
            this.pickerToggle.setAttribute('aria-controls', 'experience-picker-panel');
            this.pickerCurrent = dom('span', '', this.item.name);
            this.pickerCurrent.setAttribute('aria-live', 'polite');
            this.pickerToggle.setAttribute('aria-label', `Choose item, currently ${this.item.name}`);
            this.pickerToggle.append(this.pickerCurrent, dom('span', 'dimension-browser-toggle__chevron', '▾'));
            this.previous = this.createNavigationButton('previous', 'Previous item', 'M15 5 8 12l7 7');
            this.next = this.createNavigationButton('next', 'Next item', 'M9 5l7 7-7 7');
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
            picker.append(this.pickerToggle, this.previous, this.next, this.select, this.pickerPanel);
            toolbarMain.append(picker);
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
            this.fullscreenButton = dom('button', 'experience-fullscreen-button');
            this.fullscreenButton.type = 'button';
            this.fullscreenButton.title = 'Enter fullscreen';
            this.fullscreenButton.setAttribute('aria-label', 'Enter fullscreen');
            this.fullscreenButton.setAttribute('aria-pressed', 'false');
            this.fullscreenButton.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" /></svg>';
            this.fullscreenButton.addEventListener('click', () => this.toggleFullscreen());
            this.reset = button(toolbarActions, 'Frame item', () =>
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
            toolbarMain.append(info, this.fullscreenButton);
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
            const keydown = (event) => {
                if (this.active && (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k'
                    && !event.altKey && !event.shiftKey) {
                    event.preventDefault();
                    openPicker();
                    return;
                }
                if (this.handleNavigationKey(event)) return;
                if (event.key !== 'Escape') return;
                if (this.fullscreenState?.fallback) {
                    this.exitFullscreen();
                    return;
                }
                closePicker();
                info.classList.remove('is-open');
                infoButton.setAttribute('aria-expanded', 'false');
                this.pickerToggle.focus();
            };
            document.addEventListener('pointerdown', outside);
            document.addEventListener('keydown', keydown);
            this.toolbarCleanup = () => {
                document.removeEventListener('pointerdown', outside);
                document.removeEventListener('keydown', keydown);
                this.fullscreenButton = null;
            };
            this.clock.reset();
            this.renderer = ScaleRenderers[this.config[1]](this);
            this.focus(this.index);
        }
        toggleFullscreen() {
            if (this.fullscreenState) this.exitFullscreen();
            else this.enterFullscreen();
        }
        handleFullscreenChange() {
            if (document.fullscreenElement === this.host) {
                if (this.fullscreenState) {
                    this.fullscreenState.native = true;
                    this.updateFullscreenButton(true);
                }
            } else if (this.fullscreenState?.native) {
                this.restoreFullscreen();
            }
        }
        enterFullscreen() {
            if (this.fullscreenState || !this.active || !this.host) return;
            const request = ++this.fullscreenRequest;
            this.fullscreenState = {
                fallback: false,
                native: false,
                scrollX: window.scrollX,
                scrollY: window.scrollY,
                htmlOverflow: document.documentElement.style.overflow,
                bodyOverflow: document.body.style.overflow
            };
            document.addEventListener('fullscreenchange', this.onFullscreenChange);
            document.documentElement.style.overflow = 'hidden';
            document.body.style.overflow = 'hidden';
            const fallback = () => {
                if (request !== this.fullscreenRequest || !this.fullscreenState) return;
                this.fullscreenState.fallback = true;
                this.host.classList.add('experience-fullscreen-fallback');
                document.body.classList.add('experience-fullscreen-active');
                this.updateFullscreenButton(true);
                this.renderer?.render(this.clock.time);
            };
            if (typeof this.host.requestFullscreen !== 'function') {
                fallback();
                return;
            }
            try {
                Promise.resolve(this.host.requestFullscreen()).then(() => {
                    if (request !== this.fullscreenRequest) {
                        if (document.fullscreenElement === this.host && typeof document.exitFullscreen === 'function') {
                            try { Promise.resolve(document.exitFullscreen()).catch(() => {}); } catch {}
                        }
                        return;
                    }
                    if (document.fullscreenElement === this.host) {
                        this.fullscreenState.native = true;
                        this.updateFullscreenButton(true);
                        this.renderer?.render(this.clock.time);
                    } else fallback();
                }).catch(fallback);
            } catch {
                fallback();
            }
        }
        exitFullscreen() {
            if (!this.fullscreenState) return;
            const native = this.fullscreenState.native || document.fullscreenElement === this.host;
            if (native && typeof document.exitFullscreen === 'function') {
                try {
                    Promise.resolve(document.exitFullscreen()).catch(() => {});
                } catch {}
            }
            this.restoreFullscreen();
        }
        restoreFullscreen() {
            const state = this.fullscreenState;
            if (!state) return;
            this.fullscreenRequest++;
            this.fullscreenState = null;
            document.removeEventListener('fullscreenchange', this.onFullscreenChange);
            this.host?.classList.remove('experience-fullscreen-fallback');
            document.body.classList.remove('experience-fullscreen-active');
            document.documentElement.style.overflow = state.htmlOverflow;
            document.body.style.overflow = state.bodyOverflow;
            this.updateFullscreenButton(false);
            window.scrollTo(state.scrollX, state.scrollY);
            if (this.active) this.renderer?.render(this.clock.time);
        }
        updateFullscreenButton(active) {
            if (!this.fullscreenButton) return;
            const label = active ? 'Exit fullscreen' : 'Enter fullscreen';
            this.fullscreenButton.title = label;
            this.fullscreenButton.setAttribute('aria-label', label);
            this.fullscreenButton.setAttribute('aria-pressed', String(active));
            this.fullscreenButton.innerHTML = active
                ? '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M9 4v5H4M20 9h-5V4M15 20v-5h5M4 15h5v5" /></svg>'
                : '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" /></svg>';
        }
        createNavigationButton(direction, label, path) {
            const control = dom('button', `experience-nav-button experience-nav-button--${direction}`);
            control.type = 'button';
            control.title = label;
            control.setAttribute('aria-label', label);
            control.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="${path}" /></svg>`;
            control.addEventListener('click', () =>
                this.focus(this.index + (direction === 'next' ? 1 : -1))
            );
            return control;
        }
        handleNavigationKey(event) {
            if (!this.active || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return false;
            if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return false;
            if (event.target?.closest?.('input, select, textarea, [contenteditable]:not([contenteditable="false"]), [role="textbox"]')) return false;
            event.preventDefault();
            const nextIndex = this.index + (event.key === 'ArrowRight' ? 1 : -1);
            if (nextIndex >= 0 && nextIndex < this.items.length && nextIndex !== this.index)
                this.focus(nextIndex);
            return true;
        }
        focus(index, frame = true) {
            // frame = true is an explicit choice (click, arrows, search, link); false is the
            // explorer following the camera, which never marks an item as selected.
            this.explicitSelection = Boolean(frame);
            this.noFocus = false;
            this.index = clamp(index, 0, this.items.length - 1);
            this.select.value = this.index;
            if (this.pickerCurrent) this.pickerCurrent.textContent = this.item.name;
            this.pickerToggle?.setAttribute('aria-label', `Choose item, currently ${this.item.name}`);
            this.pickerButtons?.forEach((option, optionIndex) => {
                option.classList.toggle('is-active', optionIndex === this.index);
                option.setAttribute('aria-current', optionIndex === this.index ? 'true' : 'false');
            });
            this.previous.disabled = this.index === 0;
            this.next.disabled = this.index === this.items.length - 1;
            this.clock.reset();
            // While the camera sweeps through scales the selection changes many times a
            // second; rebuild the side panel once it settles instead of on every change.
            clearTimeout(this.detailTimer);
            if (frame) this.updateDetail();
            else this.detailTimer = setTimeout(() => { if (this.active) this.updateDetail(); }, 160);
            this.updateComparison();
            this.renderer?.focus?.(frame);
            this.renderer?.render(0);
        }
        // Nothing is in view at the camera's scale (for example the empty decades between
        // the Planck length and quarks): show no object description until something is.
        clearFocus() {
            if (this.noFocus) return;
            this.noFocus = true;
            this.explicitSelection = false;
            if (this.pickerCurrent) this.pickerCurrent.textContent = 'Search items';
            this.pickerToggle?.setAttribute('aria-label', 'Choose item, none in view');
            clearTimeout(this.detailTimer);
            this.detailTimer = setTimeout(() => { if (this.active && this.noFocus) this.showEmptyDetail(); }, 160);
        }
        showEmptyDetail() {
            this.detailImage = null;
            const empty = dom('div', 'experience-detail-empty');
            empty.append(dom('h2', '', 'No objects at this scale'),
                dom('p', '', 'Zoom in or out to find the next object, or search for one by name.'));
            this.detail.replaceChildren(empty);
        }
        updateDetail() {
            clearTimeout(this.detailTimer);
            if (this.noFocus) { this.showEmptyDetail(); return; }
            const item = this.item;
            const model = this.modelEntry?.(item);
            const title = dom('h2', '', model?.display_label || item.name);
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
            if (modelNote) modelNote.append(dom('h3', '', model.note_heading || 'What this 3D model shows'),
                dom('p', '', model.note));
            this.detail.replaceChildren(title, value, ...(modelNote ? [modelNote] : []), prose);
            // The panel is rebuilt when the registry arrives or units change: reuse the
            // same image element so it does not reload and push the text down again.
            if (this.detailImage?.item !== item) this.detailImage = this.detailThumbnail(item);
            if (!this.detailImage.missing) this.detail.prepend(this.detailImage.button);
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
            if (model?.basis_url && model.basis_url !== modelSource && model.basis_url !== item.source)
                addSource('Model basis', model.basis_url);
            for (const source of model?.additional_sources || [])
                addSource(source.label || 'Model source', source.url);
            if (sources.childNodes.length) this.detail.append(sources);
            this.detail.scrollTop = 0;
        }
        detailThumbnail(item) {
            // The button reserves its full height before the image arrives; the image
            // fades in, so nothing below it moves. Only a missing image collapses it.
            const state = { item, missing: this.images.get(item) === '' };
            const button = state.button = dom('button', 'experience-detail-image-button is-loading');
            button.type = 'button';
            button.setAttribute('aria-label', `Open full image of ${item.name}`);
            const thumbnail = dom('img', 'experience-detail-image');
            thumbnail.alt = `${item.name} (illustrative image)`;
            thumbnail.decoding = 'async';
            button.append(thumbnail);
            const collapse = () => { state.missing = true; button.remove(); };
            this.resolveImage(item).then((info) => {
                if (this.detailImage !== state) return;
                const src = typeof info === 'string' ? info : info?.path;
                if (!src) return collapse();
                const fullPath = typeof info === 'string' ? info : info.fullPath || info.path;
                button.onclick = () => this.app.openImageModal(fullPath, item.name);
                thumbnail.onload = () => button.classList.remove('is-loading');
                thumbnail.onerror = collapse;
                thumbnail.src = src;
            });
            return state;
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
