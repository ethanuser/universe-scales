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
            f: () => experiences()?.active && experiences().toggleFullscreen(),
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
            if (event.ctrlKey || event.metaKey || event.altKey || typing(event.target)) return;
            if (!help.hidden || !about.hidden) return;
            const action = shortcuts[event.key.length === 1 ? event.key.toLowerCase() : ''] ?? shortcuts[event.key];
            if (!action) return;
            event.preventDefault();
            action();
        }, true);

        // --- One-time controls hint ----------------------------------------------------
        // First visit only: a short strip over the explorer naming the three gestures and
        // where to find the rest. Any interaction with the explorer dismisses it for good.
        const showHint = () => {
            const frame = document.querySelector('#dimension-experience .experience-stage-frame');
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
