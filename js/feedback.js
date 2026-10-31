// Interaction feedback shared across the app: toasts for the result of an action, a progress line
// for loading, confirmation on a button, a sliding highlight for segmented controls, and a ripple
// where something was picked. Each one reports something that happened; none is decoration.
(function (root) {
    const reduced = () => root.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    const ICONS = {
        success: '<path d="M5 12.5l4.5 4.5L19 7.5" />',
        error: '<circle cx="12" cy="12" r="9" /><path d="M12 7.5v5.5M12 16.5v.01" />',
        warning: '<path d="M12 4 2.5 20h19ZM12 10v4.5M12 17.5v.01" />',
        info: '<circle cx="12" cy="12" r="9" /><path d="M12 11v5.5M12 7.5v.01" />'
    };
    const icon = kind => `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">${ICONS[kind]}</svg>`;
    let stack = null;
    function toast(message, kind = 'info') {
        if (!stack) {
            stack = Object.assign(document.createElement('div'), { className: 'app-toasts' });
            stack.setAttribute('role', 'status');
            stack.setAttribute('aria-live', 'polite');
            (document.querySelector('.app') || document.body).append(stack);
        }
        // Dialogs sit above the app, so the stack moves to the top of whatever is open.
        const open = [...document.querySelectorAll('.app-dialog:not([hidden])')].at(-1);
        (open || document.querySelector('.app') || document.body).append(stack);
        const note = Object.assign(document.createElement('div'), { className: `app-toast app-toast--${kind}` });
        note.innerHTML = icon(kind);
        note.append(Object.assign(document.createElement('span'), { textContent: message }));
        stack.append(note);
        while (stack.children.length > 3) stack.firstChild.remove();
        const close = () => {
            note.classList.add('is-leaving');
            setTimeout(() => note.remove(), reduced() ? 0 : 160);
        };
        setTimeout(close, kind === 'error' ? 6000 : 2600);
        note.addEventListener('click', close);
    }
    // A thin line under the top bar. It waits briefly, so fast loads show nothing.
    let bar = null, barTimer = 0, loads = 0;
    function progress(active) {
        loads = Math.max(0, loads + (active ? 1 : -1));
        bar ||= document.body.appendChild(Object.assign(document.createElement('div'), { className: 'app-progress' }));
        clearTimeout(barTimer);
        if (loads) barTimer = setTimeout(() => bar.classList.add('is-active'), 140);
        else bar.classList.remove('is-active');
    }
    // Shows a result on the button that caused it, then restores the label.
    function confirm(button, text = 'Done') {
        if (!button) return;
        clearTimeout(button._confirmTimer);
        button._confirmLabel ??= button.innerHTML;
        button.classList.add('is-confirmed');
        button.innerHTML = `${icon('success')}<span>${text}</span>`;
        button._confirmTimer = setTimeout(() => {
            button.classList.remove('is-confirmed');
            button.innerHTML = button._confirmLabel;
            button._confirmLabel = null;
        }, 1600);
    }
    function busy(button, active) {
        button?.classList.toggle('is-busy', active);
        button?.setAttribute('aria-busy', String(active));
    }
    // A highlight that slides to the chosen segment, so the eye follows the change. `attribute`
    // is the one that marks the chosen child (aria-pressed, aria-selected or aria-checked).
    function segmented(container, attribute) {
        if (!container) return;
        const thumb = Object.assign(document.createElement('span'), { className: 'segment-thumb' });
        thumb.setAttribute('aria-hidden', 'true');
        container.classList.add('has-thumb');
        const place = animate => {
            if (!thumb.isConnected) container.prepend(thumb);
            const on = container.querySelector(`[${attribute}="true"]`);
            thumb.hidden = !on || !on.offsetWidth;
            if (thumb.hidden) return;
            thumb.classList.toggle('is-instant', !animate);
            thumb.style.width = `${on.offsetWidth}px`;
            thumb.style.height = `${on.offsetHeight}px`;
            thumb.style.transform = `translate(${on.offsetLeft}px, ${on.offsetTop}px)`;
        };
        new MutationObserver(() => place(thumb.offsetWidth > 0)).observe(container,
            { subtree: true, childList: true, attributes: true, attributeFilter: [attribute] });
        new ResizeObserver(() => place(false)).observe(container);
        place(false);
    }
    // A ring that opens at the point where an object was picked.
    function ripple(parent, clientX, clientY) {
        if (reduced()) return;
        const box = parent.getBoundingClientRect();
        const ring = Object.assign(document.createElement('span'), { className: 'app-ripple' });
        ring.style.left = `${clientX - box.left}px`;
        ring.style.top = `${clientY - box.top}px`;
        parent.append(ring);
        ring.addEventListener('animationend', () => ring.remove());
    }
    // Restarts a one-shot CSS animation class.
    function replay(element, className) {
        element?.classList.remove(className);
        void element?.offsetWidth;
        element?.classList.add(className);
    }
    // Crossfades a change of view. `scope` 'main' fades the content under the top bar, which keeps
    // updating live; 'root' fades the whole page, for a change of theme.
    function crossfade(change, scope = 'main') {
        if (!document.startViewTransition || reduced()) { change(); return; }
        const html = document.documentElement;
        html.classList.add(`fade-${scope}`);
        const fade = document.startViewTransition(change);
        // A skipped transition (a second change, a hidden tab) still applies the change.
        fade.ready.catch(() => {});
        fade.finished.catch(() => {}).finally(() => html.classList.remove(`fade-${scope}`));
    }
    root.AppFeedback = { toast, progress, confirm, busy, segmented, ripple, replay, crossfade };
})(globalThis);
