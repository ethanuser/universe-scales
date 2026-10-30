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
        const about = $('about-dialog'), help = $('help-dialog'), dataEditor = $('data-editor-dialog');
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
                dialog.onClose?.();
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
        for (const dialog of [about, help, dataEditor].filter(Boolean)) {
            dialog.addEventListener('click', event => {
                if (event.target === dialog || event.target.closest('[data-close-dialog]')) setDialog(dialog, false);
            });
        }
        infoToggle?.addEventListener('click', event => { event.stopPropagation(); setInfo(info.hidden); });
        document.addEventListener('pointerdown', event => {
            if (!info.hidden && !info.contains(event.target) && !infoToggle.contains(event.target)) setInfo(false);
        });

        // --- Data editor ------------------------------------------------------------------
        // editor.js builds the editor inside #editor-content. It opens as a full page with
        // Dimension / Units / Items tabs. Items use a list and detail layout: the sidebar lists
        // every item, grouped by scale, and the selected item's card fills the page (its
        // details and image on the left, its 3D model with a live preview on the right).
        // Every card stays in the DOM, because editor.js saves by reading all of them.
        const editorContent = $('editor-content'), editorToggle = $('editor-toggle');
        if (dataEditor && editorContent && editorToggle) {
            const element = (tag, className, text) => Object.assign(document.createElement(tag), className ? { className } : {}, text != null ? { textContent: text } : {});
            const link = (label, href) => Object.assign(element('a', '', label), { href, target: '_blank', rel: 'noopener noreferrer' });
            const panel = dataEditor.querySelector('.data-editor');
            const body = dataEditor.querySelector('.data-editor__body');
            const filter = dataEditor.querySelector('.data-editor__filter');
            body.append(editorContent);
            // Global actions (share, import/export, undo, save) live in a footer bar.
            const footer = element('div', 'data-editor__footer');
            const actions = editorContent.querySelector('.editor-header');
            if (actions) footer.append(actions);
            panel.append(footer);
            const itemsSection = $('items-section'), itemsList = $('items-list'), unitsList = $('units-list');
            const detail = itemsSection?.querySelector('.section-content');
            // Sidebar: filter and Add, the item list, and Delete all at the bottom.
            const nav = element('aside', 'data-editor__nav');
            const navTools = element('div', 'data-editor__nav-tools');
            const navList = element('div', 'data-editor__nav-list');
            navList.setAttribute('role', 'listbox');
            navList.setAttribute('aria-label', 'Items');
            const navFooter = element('div', 'data-editor__nav-footer');
            const addItem = $('add-item-btn'), deleteAll = $('delete-all-items-btn');
            if (addItem) { addItem.textContent = 'Add item'; addItem.prepend(Object.assign(element('span', 'data-editor__plus'), { ariaHidden: 'true' })); }
            if (deleteAll) deleteAll.textContent = 'Delete all items';
            navTools.append(filter, addItem || '');
            navFooter.append(deleteAll || '');
            nav.append(navTools, navList, navFooter);
            itemsSection?.prepend(nav);
            dataEditor.querySelector('.data-editor__toolbar')?.remove();
            const empty = element('div', 'data-editor__empty');
            empty.append(element('h3', '', 'No item selected'), element('p', '', 'Choose an item from the list, or add a new one.'));
            detail?.prepend(empty);

            const showTab = tab => {
                panel.dataset.tab = tab;
                dataEditor.querySelectorAll('[role="tab"]').forEach(button =>
                    button.setAttribute('aria-selected', String(button.dataset.tab === tab)));
                $(`${tab}-section`)?.classList.remove('collapsed');
                body.scrollTop = 0;
            };
            dataEditor.querySelectorAll('[role="tab"]').forEach(button =>
                button.addEventListener('click', () => showTab(button.dataset.tab)));
            // editor.js's own toggle listener runs first and renders; this one opens the page.
            editorToggle.addEventListener('click', () => {
                if (editorContent.style.display === 'none') return;
                setDrawer(false);
                // Undo and Save sit apart from the sharing actions, at the right of the footer.
                if (actions && !actions.querySelector('.data-editor__commit')) {
                    const commit = element('div', 'data-editor__commit');
                    commit.append(...[$('editor-undo-all-btn'), $('editor-save-all-btn')].filter(Boolean));
                    actions.append(commit);
                }
                const title = dataEditor.querySelector('#data-editor-title');
                title.textContent = `Edit ${document.getElementById('dimension-browser-current')?.textContent || ''} data`;
                filter.value = '';
                selectedKey = null;
                showTab(panel.dataset.tab || 'items');
                setDialog(dataEditor, true);
                buildNav();
            });
            dataEditor.onClose = () => {
                if (editorContent.style.display !== 'none') window.app?.editor?.toggleEditor();
                preview?.dispose();
                preview = null;
                previewFor = null;
            };
            // Section headers keep their action buttons but no longer collapse the section.
            dataEditor.addEventListener('click', event => {
                const header = event.target.closest('.section-header');
                if (header && !event.target.closest('button, input, select, textarea, a')) {
                    event.stopPropagation();
                    event.preventDefault();
                }
            }, true);

            // --- Item list ---
            let selectedKey = null, wantNew = false, rows = new Map();
            const cardKey = card => card.dataset.isCustom === 'true' ? `custom:${card.dataset.customId}` : `item:${card.dataset.itemIndex}`;
            const cardName = card => card.querySelector('input[name="name"]')?.value.trim() || '';
            const cardValue = card => Number(card.querySelector('input[name="value"]')?.value);
            const superscript = text => text.replace(/[-0-9]/g, c => '⁻⁰¹²³⁴⁵⁶⁷⁸⁹'['-0123456789'.indexOf(c)]);
            const formatValue = value => {
                if (!Number.isFinite(value)) return '';
                if (value === 0 || (Math.abs(value) >= 0.01 && Math.abs(value) < 1e5)) return String(Number(value.toPrecision(3)));
                const exponent = Math.floor(Math.log10(Math.abs(value)));
                return `${Number((value / 10 ** exponent).toPrecision(3))} × 10${superscript(String(exponent))}`;
            };
            // Values are stored in the base unit (conversion factor 1).
            const unitSymbol = () => app()?.dimensionData?.units?.find(unit => Number(unit.conversion_factor) === 1)?.symbol || '';
            const fillRow = (row, card) => {
                row.querySelector('.data-editor__nav-name').textContent = cardName(card) || 'Unnamed item';
                const value = formatValue(cardValue(card));
                row.querySelector('.data-editor__nav-value').textContent = value ? `${value} ${unitSymbol()}`.trim() : '';
            };
            const makeRow = card => {
                const row = element('button', 'data-editor__nav-item');
                row.type = 'button';
                row.setAttribute('role', 'option');
                const thumb = element('img', 'data-editor__nav-thumb');
                Object.assign(thumb, { alt: '', loading: 'lazy', decoding: 'async' });
                const source = cardName(card) && card.querySelector('.image-preview')?.getAttribute('src');
                if (source) { thumb.src = source; thumb.onerror = () => thumb.classList.add('is-missing'); }
                else thumb.classList.add('is-missing');
                const text = element('span', 'data-editor__nav-text');
                text.append(element('span', 'data-editor__nav-name'), element('span', 'data-editor__nav-value'));
                row.append(thumb, text);
                fillRow(row, card);
                row.addEventListener('click', () => select(card));
                rows.set(card, row);
                return row;
            };
            function buildNav() {
                if (!itemsList || dataEditor.hidden) return;
                const cards = [...itemsList.querySelectorAll('.item-editor-card')];
                rows = new Map();
                const linear = app()?.isLinearScale?.() || !window.ScaleSearch?.groups;
                const groups = linear ? [{ label: '', indices: cards.map((card, index) => index) }]
                    : ScaleSearch.groups(cards, app()?.currentDimension, cardValue);
                navList.replaceChildren(...groups.flatMap(group => {
                    const nodes = group.indices.map(index => makeRow(cards[index]));
                    if (!group.label) return nodes;
                    const header = element('div', 'data-editor__nav-group');
                    header.append(element('span', '', group.label));
                    if (group.range) header.append(element('small', '', group.range));
                    return [header, ...nodes];
                }));
                applyFilter();
                // Keep the selection across re-renders; a new item is selected once added;
                // otherwise start on the item the explorer shows.
                const target = (wantNew && cards.find(card => !cardName(card))) ||
                    cards.find(card => cardKey(card) === selectedKey) ||
                    cards.find(card => cardName(card) === experiences()?.item?.name) || cards[0];
                wantNew = false;
                if (target) select(target, 'center');
                else { previewFor = null; empty.hidden = false; }
            }
            addItem?.addEventListener('click', () => { wantNew = true; filter.value = ''; });
            function select(card, scroll = 'nearest') {
                itemsList.querySelectorAll('.item-editor-card.is-selected').forEach(other => other.classList.remove('is-selected'));
                card.classList.add('is-selected');
                empty.hidden = true;
                selectedKey = cardKey(card);
                rows.forEach((row, other) => row.setAttribute('aria-selected', String(other === card)));
                rows.get(card)?.scrollIntoView({ block: scroll });
                if (detail) detail.scrollTop = 0;
                decorate(card);
                modelPanel(card);
            }
            // Headings for the card's groups, and live list updates while typing.
            function decorate(card) {
                if (card.dataset.decorated) return;
                card.dataset.decorated = 'true';
                card.querySelector('.item-editor-form-left')?.prepend(element('h5', 'data-editor__block-title', 'Details'));
                card.querySelector('.item-editor-form-right')?.prepend(element('h5', 'data-editor__block-title', 'Image'));
                const heading = card.querySelector('.item-editor-card-title-row h4');
                const number = heading?.textContent.match(/^\s*(\d+)\./)?.[1];
                const rename = () => {
                    if (heading) heading.textContent = cardName(card) || 'Unnamed item';
                    const row = rows.get(card);
                    if (row) fillRow(row, card);
                };
                if (heading && number) heading.dataset.number = number;
                // The value is in the dimension's base unit; say which.
                const valueLabel = card.querySelector('input[name="value"]')?.closest('.item-editor-form-group')?.querySelector('label');
                if (valueLabel && unitSymbol()) valueLabel.textContent = `Value (${unitSymbol()}) *`;
                rename();
                card.querySelector('input[name="name"]')?.addEventListener('input', rename);
                card.querySelector('input[name="value"]')?.addEventListener('input', rename);
            }
            const count = (selector, list) => {
                const node = dataEditor.querySelector(`[data-count="${selector}"]`);
                if (node && list) node.textContent = String(list.querySelectorAll(`.${selector === 'units' ? 'unit' : 'item'}-editor-card`).length);
            };
            const recount = () => { count('units', unitsList); count('items', itemsList); };
            if (unitsList) new MutationObserver(recount).observe(unitsList, { childList: true });
            if (itemsList) new MutationObserver(() => { recount(); buildNav(); }).observe(itemsList, { childList: true });
            function applyFilter() {
                const query = window.ScaleSearch ? ScaleSearch.normalize(filter.value) : filter.value.toLowerCase();
                let header = null, shown = 0;
                const closeGroup = () => { if (header) header.hidden = shown === 0; };
                for (const node of navList.children) {
                    if (node.classList.contains('data-editor__nav-group')) { closeGroup(); header = node; shown = 0; continue; }
                    const name = node.querySelector('.data-editor__nav-name')?.textContent || '';
                    const text = window.ScaleSearch ? ScaleSearch.normalize(name) : name.toLowerCase();
                    node.hidden = Boolean(query) && !text.includes(query);
                    if (!node.hidden) shown++;
                }
                closeGroup();
            }
            filter.addEventListener('input', applyFilter);
            // Arrow keys move through the list while it or the filter has focus.
            nav.addEventListener('keydown', event => {
                if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;
                const visible = [...rows.entries()].filter(([, row]) => !row.hidden);
                if (!visible.length) return;
                event.preventDefault();
                const index = visible.findIndex(([card]) => cardKey(card) === selectedKey);
                const next = visible[Math.max(0, Math.min(visible.length - 1, index + (event.key === 'ArrowDown' ? 1 : -1)))];
                select(next[0]);
                if (event.target !== filter) next[1].focus();
            });

            // --- 3D model panel ---
            // A live preview (drag to turn, scroll to zoom), size and rotation adjustments,
            // upload or download, and where the model comes from. Adjustments also preview in
            // the explorer and stay in this browser.
            let registry = null, preview = null, previewFor = null;
            const previewBox = element('div', 'model-preview');
            previewBox.title = 'Drag to turn, scroll to zoom, double-click to reset the view';
            const loadRegistry = () => registry ||= fetch('content/visualizations/models.json').then(r => r.json()).catch(() => ({ models: [] }));
            async function modelPanel(card) {
                const name = cardName(card);
                const dimension = app()?.currentDimension;
                const host = card.querySelector('.item-editor-form');
                if (!host) return;
                const data = await loadRegistry();
                if (!card.classList.contains('is-selected')) return;
                card.querySelector('.item-model-panel')?.remove();
                const view = experiences();
                const item = view?.items?.find(other => other.name === name);
                const sourced = name ? data.models.find(model => model.matches?.[dimension]?.includes(name)) : null;
                const live = item && view.modelEntry ? view.modelEntry(item) : null;
                const entry = sourced || live;
                const override = name ? window.ModelOverrides?.get(dimension, name) : null;
                const current = { ...(entry?.presentation || {}), ...(override?.presentation || {}) };
                const section = element('section', 'item-model-panel');
                const buttons = element('div', 'item-model-panel__actions');
                const reset = element('button', 'btn btn-danger', 'Reset model');
                reset.type = 'button';
                reset.addEventListener('click', async () => { await ModelOverrides.clear(dimension, name); modelPanel(card); });
                section.append(element('h5', 'data-editor__block-title', '3D model'), previewBox);
                if (window.ScaleModels?.ModelPreview && name) {
                    preview ||= new ScaleModels.ModelPreview(previewBox);
                    const key = `${dimension}::${name}`;
                    if (previewFor !== key) { previewFor = key; preview.show(dimension, name); }
                    else requestAnimationFrame(() => preview?.render());
                }
                previewBox.hidden = !name;
                if (name && (entry || override?.src)) {
                    const sliders = element('div', 'item-model-panel__sliders');
                    const slider = (label, field, min, max, step, toValue, fromValue, format) => {
                        const row = element('label', 'item-model-panel__slider');
                        const output = element('output');
                        const range = Object.assign(element('input'), { type: 'range', min, max, step });
                        range.value = fromValue(current[field]);
                        output.textContent = format(toValue(Number(range.value)));
                        range.addEventListener('input', () => {
                            const value = toValue(Number(range.value));
                            output.textContent = format(value);
                            ModelOverrides.setPresentation(dimension, name, { [field]: value });
                            if (!reset.isConnected) buttons.append(reset);
                        });
                        row.append(element('span', '', label), range, output);
                        sliders.append(row);
                    };
                    slider('Size', 'display_scale', -2, 2, 0.05, v => Math.round(2 ** v * 100) / 100,
                        v => Math.log2(v ?? 1), v => `${v.toFixed(2)}×`);
                    for (const [label, field] of [['Turn', 'yaw'], ['Tilt', 'pitch'], ['Roll', 'roll']])
                        slider(label, field, -180, 180, 1, v => v, v => v ?? 0, v => `${v}°`);
                    section.append(sliders);
                }
                if (sourced?.src && !override?.src) {
                    const download = link('Download GLB', sourced.src);
                    download.className = 'btn';
                    download.setAttribute('download', `${sourced.id}.glb`);
                    download.removeAttribute('target');
                    buttons.append(download);
                }
                if (name) {
                    const upload = element('label', 'btn', override?.src ? 'Replace upload' : 'Upload GLB');
                    const input = Object.assign(element('input'), { type: 'file', accept: '.glb,model/gltf-binary', hidden: true });
                    input.addEventListener('change', async () => {
                        const file = input.files?.[0];
                        if (!file) return;
                        await ModelOverrides.setFile(dimension, name, file);
                        modelPanel(card);
                    });
                    upload.append(input);
                    buttons.append(upload);
                }
                if (override) buttons.append(reset);
                section.append(buttons);
                const facts = element('dl', 'item-model-panel__facts');
                const fact = (label, value) => { if (!value) return; facts.append(element('dt', '', label)); const dd = element('dd'); dd.append(value); facts.append(dd); };
                if (!name) fact('Model', 'Name the item to attach a model');
                else if (override?.src) fact('Model', `Your upload: ${override.fileName}`);
                else if (sourced) {
                    fact('Model', sourced.id);
                    fact('Author', sourced.author || '');
                    if (sourced.license) fact('License', sourced.license_url ? link(sourced.license, sourced.license_url) : sourced.license);
                    if (sourced.source) fact('Source', link(sourced.source.replace(/^https?:\/\//, '').slice(0, 60), sourced.source));
                    if (sourced.basis_url && sourced.basis_url !== sourced.source) fact('Basis', link(sourced.basis_label || 'Model basis', sourced.basis_url));
                } else if (live?.procedural) fact('Model', 'Built in the app from measurements');
                else fact('Model', 'None. The explorer shows the photo.');
                if (item?.source) fact('Item source', link(item.source.replace(/^https?:\/\//, '').slice(0, 60), item.source));
                section.append(facts);
                const note = override?.src ? '' : sourced?.note || live?.note || '';
                if (note) section.append(element('p', 'item-model-panel__note', note));
                if (name && (entry || override)) section.append(element('p', 'item-model-panel__hint', 'Adjustments also show in the explorer, and are saved in this browser only.'));
                host.append(section);
            }
        }

        // --- Chart: no browser back/forward from horizontal swipes ----------------------------
        document.addEventListener('wheel', event => {
            if (document.body.dataset.experience === 'log' && Math.abs(event.deltaX) > Math.abs(event.deltaY) &&
                event.target.closest?.('.app-main')) event.preventDefault();
        }, { passive: false });

        // --- Scroll latching -----------------------------------------------------------------
        // A scroll gesture stays with the pane where it started: passing over an inner scrollable
        // field (a long description box) does not take over until the gesture pauses.
        {
            let latched = null, latchedAt = 0;
            const scrollableFrom = node => {
                for (; node && node !== document.documentElement; node = node.parentElement) {
                    const style = getComputedStyle(node);
                    if (/(auto|scroll)/.test(style.overflowY) && node.scrollHeight > node.clientHeight + 1) return node;
                }
                return null;
            };
            document.addEventListener('wheel', event => {
                if (Math.abs(event.deltaX) > Math.abs(event.deltaY)) return;
                const now = performance.now();
                if (latched?.isConnected && now - latchedAt < 400) {
                    latchedAt = now;
                    const inner = scrollableFrom(event.target);
                    if (inner && inner !== latched && latched.contains(inner)) {
                        event.preventDefault();
                        latched.scrollTop += event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? latched.clientHeight : 1);
                    }
                    return;
                }
                latched = scrollableFrom(event.target);
                latchedAt = now;
            }, { capture: true, passive: false });
        }

        // --- Keyboard shortcuts -------------------------------------------------------
        const press = id => $(id)?.click();
        const shortcuts = {
            '?': () => setDialog(help, help.hidden),
            '/': () => experiences()?.openItemSearch?.(),
            d: () => press('dimension-browser-toggle'),
            u: () => press('unit-browser-toggle'),
            o: () => setDrawer(drawer.hidden),
            t: () => window.app?.toggleDarkMode(),
            n: () => window.app?.toggleNotation(),
            m: () => window.app?.toggleMusic(),
            l: () => {
                const view = experiences();
                if (!view?.interactiveButton) return;
                (view.active ? view.logButton : view.interactiveButton)?.click();
            },
            p: () => experiences()?.active ? experiences().togglePanel() : chartPanelToggle?.(),
            f: () => experiences()?.toggleFullscreen(),
            c: () => { const view = experiences(); if (view?.active && !view.noFocus) view.focus(view.index); },
            '+': () => experiences()?.renderer?.zoomBy?.(-0.25),
            '=': () => experiences()?.renderer?.zoomBy?.(-0.25),
            '-': () => experiences()?.renderer?.zoomBy?.(0.25),
            _: () => experiences()?.renderer?.zoomBy?.(0.25)
        };
        document.addEventListener('keydown', event => {
            if (event.key === 'Escape') {
                for (const dialog of [help, about, dataEditor].filter(Boolean)) if (!dialog.hidden) {
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
        let chartPanelToggle = null;
        const chartSearch = (() => {
            const chevron = '<span class="dimension-browser-toggle__chevron" aria-hidden="true"></span>';
            const arrow = path => `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="${path}" /></svg>`;
            const wrap = document.createElement('div');
            wrap.className = 'experience-toolbar chart-toolbar';
            wrap.innerHTML = `<div class="experience-toolbar__main">
                <button type="button" class="experience-panel-button" title="Show or hide the description panel (P)" aria-label="Description panel" aria-pressed="true">
                    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="3" y="4" width="18" height="16" /><path d="M9 4v16" /></svg></button>
                <div class="experience-picker">
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
            let options = [], grouped = [], highlighted = -1;
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
                // Scale bands as headers (see ScaleSearch.groups); searches show ranked results.
                grouped = app().isLinearScale?.() ? options : ScaleSearch.groups(options.map(option => option.item), app().currentDimension)
                    .flatMap(group => {
                        const header = document.createElement('div');
                        header.className = 'experience-picker-group';
                        header.append(Object.assign(document.createElement('span'), { textContent: group.label }));
                        if (group.range) header.append(Object.assign(document.createElement('small'), { textContent: group.range }));
                        return [header, ...group.indices.map(index => options[index])];
                    });
                list.replaceChildren(...grouped);
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
                list.classList.toggle('is-searching', Boolean(ranked));
                list.append(...(ranked ? ranked.map(result => options[result.index]) : grouped));
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
            // The chart's details panel shows or hides with the same preference as the explorer's.
            const panelButton = wrap.querySelector('.experience-panel-button');
            const setPanel = hidden => {
                document.body.classList.toggle('chart-panel-hidden', hidden);
                panelButton.setAttribute('aria-pressed', String(!hidden));
                storage.set('scale-panel-hidden', String(hidden));
            };
            setPanel(storage.get('scale-panel-hidden') === 'true');
            panelButton.addEventListener('click', () => setPanel(!document.body.classList.contains('chart-panel-hidden')));
            chartPanelToggle = () => setPanel(!document.body.classList.contains('chart-panel-hidden'));
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
