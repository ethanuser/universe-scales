// App shell: the Options drawer and the About dialog. Everything inside them keeps its
// original ids, so script.js and editor.js wire their controls exactly as before.
(function () {
    document.addEventListener('DOMContentLoaded', () => {
        const toggle = document.getElementById('options-toggle');
        const drawer = document.getElementById('options-drawer');
        const backdrop = document.getElementById('options-backdrop');
        const about = document.getElementById('about-dialog');
        if (!toggle || !drawer) return;
        let returnFocus = null;

        const setDrawer = open => {
            drawer.hidden = !open;
            backdrop.hidden = !open;
            toggle.setAttribute('aria-expanded', String(open));
            document.body.classList.toggle('is-options-open', open);
            if (open) drawer.querySelector('button, a, input, select, textarea')?.focus();
            else toggle.focus({ preventScroll: true });
        };
        const setAbout = open => {
            about.hidden = !open;
            if (open) {
                returnFocus = document.activeElement;
                about.querySelector('button')?.focus();
            } else returnFocus?.focus?.({ preventScroll: true });
        };

        toggle.addEventListener('click', () => setDrawer(drawer.hidden));
        document.getElementById('options-close')?.addEventListener('click', () => setDrawer(false));
        backdrop.addEventListener('click', () => setDrawer(false));
        document.getElementById('about-open')?.addEventListener('click', () => setAbout(true));
        document.getElementById('about-close')?.addEventListener('click', () => setAbout(false));
        about.addEventListener('click', event => { if (event.target === about) setAbout(false); });
        document.addEventListener('keydown', event => {
            if (event.key !== 'Escape') return;
            if (!about.hidden) { setAbout(false); event.stopPropagation(); }
            else if (!drawer.hidden) { setDrawer(false); event.stopPropagation(); }
        }, true);
    });
})();
