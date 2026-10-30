// App shell: Options drawer, About and Help dialogs, the dimension info popover, keyboard
// shortcuts and a one-time controls hint. Everything inside keeps its original ids, so
// script.js and editor.js wire their controls exactly as before.
(function () {
    const typing = target => target?.closest?.('input, select, textarea, [contenteditable]:not([contenteditable="false"]), [role="textbox"]');
    const storage = {
        get(key) { try { return localStorage.getItem(key); } catch { return null; } },
        set(key, value) { try { localStorage.setItem(key, value); } catch {} }
    };

    document.addEventListener('DOMContentLoaded', () => {
        const $ = id => document.getElementById(id);
        const drawer = $('options-drawer'), backdrop = $('options-backdrop'), optionsToggle = $('options-toggle');
        const about = $('about-dialog'), help = $('help-dialog');
        const infoToggle = $('dimension-info-toggle'), info = $('dimension-info');
        if (!drawer || !optionsToggle) return;
        const app = () => window.app;
        const experiences = () => window.app?.experiences;
        let returnFocus = null;

        // --- Drawer and dialogs -------------------------------------------------------
        const setDrawer = open => {
            drawer.hidden = !open;
            backdrop.hidden = !open;
            optionsToggle.setAttribute('aria-expanded', String(open));
            if (open) drawer.querySelector('button, a, input, select, textarea')?.focus();
            else optionsToggle.focus({ preventScroll: true });
        };
        const setDialog = (dialog, open) => {
            if (open) {
                closeTransient();
                returnFocus = document.activeElement;
                dialog.hidden = false;
                dialog.querySelector('button')?.focus();
            } else {
                dialog.hidden = true;
                returnFocus?.focus?.({ preventScroll: true });
            }
        };
        const setInfo = open => {
            info.hidden = !open;
            infoToggle.setAttribute('aria-expanded', String(open));
        };
        // Menus that should close when another opens or on Escape.
        const closeTransient = () => {
            if (!drawer.hidden) setDrawer(false);
            if (!info.hidden) setInfo(false);
            if (app()?.isDimensionBrowserOpen) app().toggleDimensionBrowser(false);
        };

        optionsToggle.addEventListener('click', () => setDrawer(drawer.hidden));
        $('fullscreen-toggle')?.addEventListener('click', () => experiences()?.toggleFullscreen());

        // Chart controls: the same stroke symbols as the rest of the toolbar.
        const chartIcons = {
            'pan-left': ['Pan left', '<path d="M15 5 8 12l7 7"/>'],
            'pan-right': ['Pan right', '<path d="M9 5l7 7-7 7"/>'],
            'zoom-out': ['Zoom out (Ctrl + scroll)', '<path d="M6 12h12"/>'],
            'zoom-in': ['Zoom in (Ctrl + scroll)', '<path d="M6 12h12M12 6v12"/>'],
            reset: ['Reset view', '<path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 9.5V20h13V9.5"/><path d="M10 20v-5h4v5"/>']
        };
        document.querySelectorAll('.zoom-btn[data-action]').forEach(button => {
            const [label, path] = chartIcons[button.dataset.action] || [];
            if (!label) return;
            button.title = label;
            button.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">${path}</svg>`;
        });
        $('options-close')?.addEventListener('click', () => setDrawer(false));
        backdrop.addEventListener('click', () => setDrawer(false));
        $('about-open')?.addEventListener('click', () => { setDrawer(false); setDialog(about, true); });
        $('about-close')?.addEventListener('click', () => setDialog(about, false));
        $('help-toggle')?.addEventListener('click', () => setDialog(help, true));
        document.querySelectorAll('[data-open-help]').forEach(button =>
            button.addEventListener('click', () => { setDrawer(false); setDialog(help, true); }));
        for (const dialog of [about, help]) {
            dialog.addEventListener('click', event => {
                if (event.target === dialog || event.target.closest('[data-close-dialog]')) setDialog(dialog, false);
            });
        }
        infoToggle?.addEventListener('click', event => { event.stopPropagation(); setInfo(info.hidden); });
        document.addEventListener('pointerdown', event => {
            if (!info.hidden && !info.contains(event.target) && !infoToggle.contains(event.target)) setInfo(false);
        });

        // --- Keyboard shortcuts -------------------------------------------------------
        const press = id => $(id)?.click();
        const shortcuts = {
            '?': () => setDialog(help, help.hidden),
            '/': () => experiences()?.openItemSearch?.(),
            d: () => press('dimension-browser-toggle'),
            u: () => press('unit-browser-toggle'),
            o: () => setDrawer(drawer.hidden),
            t: () => press('dark-mode-toggle'),
            n: () => press('notation-toggle'),
            m: () => press('music-toggle'),
            l: () => {
                const view = experiences();
                if (!view?.interactiveButton) return;
                (view.active ? view.logButton : view.interactiveButton)?.click();
            },
            p: () => experiences()?.active && experiences().togglePanel(),
            f: () => experiences()?.toggleFullscreen(),
            c: () => { const view = experiences(); if (view?.active && !view.noFocus) view.focus(view.index); },
            '+': () => experiences()?.renderer?.zoomBy?.(-0.25),
            '=': () => experiences()?.renderer?.zoomBy?.(-0.25),
            '-': () => experiences()?.renderer?.zoomBy?.(0.25),
            _: () => experiences()?.renderer?.zoomBy?.(0.25)
        };
        document.addEventListener('keydown', event => {
            if (event.key === 'Escape') {
                for (const dialog of [help, about]) if (!dialog.hidden) {
                    setDialog(dialog, false); event.stopPropagation(); return;
                }
                if (!drawer.hidden || !info.hidden) { closeTransient(); event.stopPropagation(); }
                return;
            }
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k' && document.body.dataset.experience === 'log') {
                event.preventDefault();
                shortcuts['/']();
                return;
            }
            if (event.ctrlKey || event.metaKey || event.altKey || typing(event.target)) return;
            if (!help.hidden || !about.hidden) return;
            const action = shortcuts[event.key.length === 1 ? event.key.toLowerCase() : ''] ?? shortcuts[event.key];
            if (!action) return;
            event.preventDefault();
            action();
        }, true);

        // --- Chart item picker --------------------------------------------------------------
        // The chart gets the same item picker as the explorer (dropdown list with thumbnails and
        // search, previous/next arrows). Choosing an item zooms the chart to it and its neighbors.
        const chartSearch = (() => {
            const chevron = '<span class="dimension-browser-toggle__chevron" aria-hidden="true"></span>';
            const arrow = path => `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="${path}" /></svg>`;
            const wrap = document.createElement('div');
            wrap.className = 'experience-toolbar chart-toolbar';
            wrap.innerHTML = `<div class="experience-toolbar__main"><div class="experience-picker">
                <button type="button" class="experience-picker-toggle" aria-expanded="false" title="Search items (/)"><span>Choose an item</span>${chevron}</button>
                <button type="button" class="experience-nav-button" data-step="-1" title="Previous item (←)">${arrow('M15 5 8 12l7 7')}</button>
                <button type="button" class="experience-nav-button" data-step="1" title="Next item (→)">${arrow('M9 5l7 7-7 7')}</button>
                <div class="experience-picker-panel" hidden>
                    <input class="experience-picker-search" type="search" placeholder="Search by name, initials or keyword" aria-label="Search items" autocomplete="off" spellcheck="false">
                    <div class="experience-picker-options"></div>
                    <p class="experience-picker-empty" hidden>No items match that search.</p>
                </div></div></div>`;
            const toggle = wrap.querySelector('.experience-picker-toggle'), label = toggle.querySelector('span');
            const panel = wrap.querySelector('.experience-picker-panel'), input = panel.querySelector('input');
            const list = panel.querySelector('.experience-picker-options'), empty = panel.querySelector('.experience-picker-empty');
            let options = [], highlighted = -1;
            const items = () => app()?.chartItemsInOrder?.() || [];
            const current = () => app()?.chartCurrent;
            const choose = item => { close(); app().focusChartItem(item); };
            const build = () => {
                options = items().map(item => {
                    const option = document.createElement('button');
                    option.type = 'button';
                    option.className = 'experience-picker-option';
                    const thumb = document.createElement('img');
                    thumb.className = 'experience-picker-thumb';
                    Object.assign(thumb, { alt: '', loading: 'lazy', decoding: 'async' });
                    const path = app().getImagePath?.(item.name);
                    if (path && !path.startsWith('data:')) thumb.src = `${path.replace(/^images\//, 'images/thumbs/')}.jpg`;
                    thumb.onerror = () => thumb.classList.add('is-missing');
                    option.append(thumb, Object.assign(document.createElement('span'), { textContent: item.name }));
                    option.classList.toggle('is-active', item.name === current()?.name);
                    option.addEventListener('click', () => choose(item));
                    option.item = item;
                    return option;
                });
                list.replaceChildren(...options);
            };
            const visible = () => options.filter(option => !option.hidden);
            const highlight = index => {
                const shown = visible();
                highlighted = shown.length ? (index + shown.length) % shown.length : -1;
                shown.forEach((option, i) => option.classList.toggle('is-highlighted', i === highlighted));
                shown[highlighted]?.scrollIntoView({ block: 'nearest' });
            };
            const filter = () => {
                const query = input.value.trim();
                const ranked = query ? ScaleSearch.rank(options.map(option => option.item), query) : null;
                const shown = ranked ? new Set(ranked.map(result => result.index)) : null;
                options.forEach((option, index) => { option.hidden = Boolean(shown) && !shown.has(index); });
                list.append(...(ranked ? ranked.map(result => options[result.index]) : options));
                empty.hidden = !ranked || ranked.length > 0;
                highlight(query ? 0 : -1);
            };
            const open = () => {
                build();
                input.value = '';
                filter();
                panel.hidden = false;
                toggle.classList.add('is-open');
                toggle.setAttribute('aria-expanded', 'true');
                input.focus();
                options.find(option => option.classList.contains('is-active'))?.scrollIntoView({ block: 'center' });
            };
            const close = () => {
                panel.hidden = true;
                toggle.classList.remove('is-open');
                toggle.setAttribute('aria-expanded', 'false');
            };
            toggle.addEventListener('click', () => panel.hidden ? open() : close());
            input.addEventListener('input', filter);
            input.addEventListener('keydown', event => {
                if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                    event.preventDefault();
                    highlight(highlighted + (event.key === 'ArrowDown' ? 1 : -1));
                } else if (event.key === 'Enter') {
                    event.preventDefault();
                    visible()[Math.max(0, highlighted)]?.click();
                } else if (event.key === 'Escape') { close(); toggle.focus(); }
            });
            const step = delta => {
                const ordered = items();
                if (!ordered.length) return;
                const index = ordered.findIndex(item => item.name === current()?.name);
                const next = index < 0 ? (delta > 0 ? 0 : ordered.length - 1) : Math.max(0, Math.min(ordered.length - 1, index + delta));
                app().focusChartItem(ordered[next]);
            };
            wrap.querySelectorAll('[data-step]').forEach(button => button.addEventListener('click', () => step(Number(button.dataset.step))));
            document.addEventListener('pointerdown', event => { if (!panel.hidden && !wrap.contains(event.target)) close(); });
            document.addEventListener('chart-selection', event => { label.textContent = event.detail?.name || 'Choose an item'; });
            document.addEventListener('keydown', event => {
                if (document.body.dataset.experience !== 'log' || typing(event.target) || event.altKey || event.ctrlKey || event.metaKey) return;
                if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') { event.preventDefault(); step(event.key === 'ArrowRight' ? 1 : -1); }
            });
            return { element: wrap, focus: open };
        })();
        const slot = $('app-item-slot');
        const syncChartSearch = () => {
            const chart = document.body.dataset.experience === 'log';
            if (chart && slot && !slot.contains(chartSearch.element) && !slot.children.length) slot.append(chartSearch.element);
            else if (!chart && chartSearch.element.isConnected) chartSearch.element.remove();
        };
        new MutationObserver(syncChartSearch).observe(document.body, { attributes: true, attributeFilter: ['data-experience'] });
        if (slot) new MutationObserver(syncChartSearch).observe(slot, { childList: true });
        syncChartSearch();
        shortcuts['/'] = () => document.body.dataset.experience === 'log' ? chartSearch.focus() : experiences()?.openItemSearch?.();

        // --- Tooltips ---------------------------------------------------------------------
        // Styled tooltips replace the browser's: a short label, with the keyboard shortcut (the
        // trailing "(X)" in a title) shown as a key cap. After one shows, neighbors show at once.
        const tip = document.createElement('div');
        tip.className = 'app-tooltip';
        tip.setAttribute('role', 'tooltip');
        tip.hidden = true;
        (document.querySelector('.app') || document.body).append(tip);
        let tipTarget = null, tipTimer = 0, warmUntil = 0;
        const hideTip = () => {
            clearTimeout(tipTimer);
            if (!tip.hidden) warmUntil = performance.now() + 600;
            tip.hidden = true;
            tipTarget = null;
        };
        const showTip = target => {
            const text = target.dataset.tip;
            if (!text || !target.isConnected) return;
            const match = text.match(/^(.*?)\s*\(([^()]{1,24})\)$/);
            tip.replaceChildren(document.createTextNode(match ? match[1] : text));
            if (match) tip.append(Object.assign(document.createElement('kbd'), { textContent: match[2] }));
            // Measure at the left edge so the box keeps its natural width, then place it.
            Object.assign(tip.style, { left: '0px', top: '0px' });
            tip.hidden = false;
            const rect = target.getBoundingClientRect(), box = tip.getBoundingClientRect();
            let top = rect.bottom + 8;
            if (top + box.height > innerHeight - 4) top = rect.top - box.height - 8;
            const left = Math.max(4, Math.min(innerWidth - box.width - 4, rect.left + rect.width / 2 - box.width / 2));
            tip.style.left = `${left}px`;
            tip.style.top = `${top}px`;
        };
        document.addEventListener('pointerover', event => {
            if (event.pointerType === 'touch') return;
            const target = event.target.closest?.('[title], [data-tip]');
            if (!target || target === tipTarget || target.closest('svg') && !target.matches('svg')) return;
            if (target.hasAttribute('title')) {
                target.dataset.tip = target.getAttribute('title');
                if (!target.hasAttribute('aria-label')) target.setAttribute('aria-label', target.dataset.tip);
                target.removeAttribute('title');
            }
            hideTip();
            tipTarget = target;
            tipTimer = setTimeout(() => showTip(target), performance.now() < warmUntil ? 0 : 450);
        });
        document.addEventListener('pointerout', event => {
            if (tipTarget && !tipTarget.contains(event.relatedTarget)) hideTip();
        });
        for (const type of ['pointerdown', 'keydown', 'wheel']) document.addEventListener(type, hideTip, { capture: true, passive: true });

        // --- One-time controls hint ----------------------------------------------------
        // First visit only: a short strip over the explorer naming the three gestures and
        // where to find the rest. Any interaction with the explorer dismisses it for good.
        const showHint = () => {
            // Only the size explorers use these gestures.
            const frame = document.querySelector('#dimension-experience.experience--spatial .experience-stage-frame');
            if (storage.get('scale-hint-seen') || !frame || frame.querySelector('.app-hint')) return;
            const hint = document.createElement('div');
            hint.className = 'app-hint';
            hint.setAttribute('role', 'note');
            const touch = matchMedia('(pointer: coarse)').matches;
            hint.innerHTML = (touch
                ? '<span><b>Pinch</b> to zoom</span><span><b>Drag</b> to pan</span><span><b>Tap</b> to select</span>'
                : '<span><b>Scroll</b> to zoom</span><span><b>Drag</b> to pan</span><span><b>Click</b> to select</span><span><kbd>?</kbd> shortcuts</span>') +
                '<button type="button" aria-label="Dismiss" title="Dismiss"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" /></svg></button>';
            const dismiss = () => {
                storage.set('scale-hint-seen', '1');
                hint.remove();
                frame.removeEventListener('pointerdown', dismiss);
                frame.removeEventListener('wheel', dismiss);
            };
            hint.querySelector('button').addEventListener('click', dismiss);
            frame.addEventListener('pointerdown', dismiss, { once: true });
            frame.addEventListener('wheel', dismiss, { once: true, passive: true });
            frame.append(hint);
        };
        const experience = $('dimension-experience');
        if (experience) new MutationObserver(showHint).observe(experience, { childList: true });
    });
})();
