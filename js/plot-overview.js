// Overview rail for the logarithmic chart: every item as a dot (left to right by value, top to
// bottom as in the chart) with a frame for the part currently on screen, both the scrolled rows
// and the zoomed value range. Click or drag the rail to jump; it keeps a sense of place while
// scrolling a long list or zooming into a few decades.
class PlotOverview {
    constructor(app) {
        this.app = app;
        this.rail = document.createElement('div');
        this.rail.className = 'plot-overview';
        this.rail.setAttribute('role', 'scrollbar');
        this.rail.setAttribute('aria-label', 'Chart overview: drag to move through items');
        this.rail.setAttribute('aria-orientation', 'vertical');
        this.rail.tabIndex = -1;
        this.canvas = document.createElement('canvas');
        this.frame = document.createElement('div');
        this.frame.className = 'plot-overview__frame';
        this.rail.append(this.canvas, this.frame);
        (document.querySelector('.app') || document.body).append(this.rail);
        this.scroller = document.querySelector('.app-main');
        this.scroller?.addEventListener('scroll', () => this.updateFrame(), { passive: true });
        window.addEventListener('resize', () => this.update());
        const seek = event => {
            const rect = this.rail.getBoundingClientRect();
            this.scrollToFraction((event.clientY - rect.top) / rect.height);
        };
        this.rail.addEventListener('pointerdown', event => {
            event.preventDefault();
            this.rail.setPointerCapture(event.pointerId);
            seek(event);
            const move = moveEvent => seek(moveEvent);
            const up = () => { this.rail.removeEventListener('pointermove', move); this.rail.removeEventListener('pointerup', up); };
            this.rail.addEventListener('pointermove', move);
            this.rail.addEventListener('pointerup', up);
        });
    }
    // Vertical bounds of the item rows inside the scroller's content.
    rows() {
        const plot = this.app.plot, svg = plot?.svg?.node();
        if (!svg || !this.scroller) return null;
        const top = svg.getBoundingClientRect().top - this.scroller.getBoundingClientRect().top + this.scroller.scrollTop;
        return { top: top + plot.margin.top, height: plot.height };
    }
    scrollToFraction(fraction) {
        const rows = this.rows();
        if (!rows) return;
        const target = rows.top + Math.min(1, Math.max(0, fraction)) * rows.height - this.scroller.clientHeight / 2;
        this.scroller.scrollTo({ top: Math.max(0, target) });
    }
    visible() {
        const view = this.app.experiences;
        return Boolean(this.app.plot?.lastPositioned?.length) && !this.app.plotContainer?.hidden && !view?.active;
    }
    update() {
        this.rail.hidden = !this.visible();
        if (this.rail.hidden) return;
        const items = this.app.plot.lastPositioned;
        const width = this.rail.clientWidth, height = this.rail.clientHeight;
        const ratio = Math.min(window.devicePixelRatio || 1, 2);
        this.canvas.width = Math.round(width * ratio);
        this.canvas.height = Math.round(height * ratio);
        const context = this.canvas.getContext('2d');
        context.setTransform(ratio, 0, 0, ratio, 0, 0);
        context.clearRect(0, 0, width, height);
        const domain = this.app.plot.originalXDomain || d3.extent(items, item => item.convertedValue);
        const linear = this.app.plot.isLinearScale?.();
        const position = value => linear ? value : Math.log10(Math.max(value, Number.MIN_VALUE));
        const [lo, hi] = domain.map(position);
        const maxRow = Math.max(...items.map(item => item.yPosition)) || 1;
        context.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--accent-color') || '#0d6efd';
        for (const item of items) {
            const x = 3 + (position(item.convertedValue) - lo) / (hi - lo || 1) * (width - 6);
            const y = 2 + (1 - item.yPosition / maxRow) * (height - 4);
            context.fillRect(x - 1, y - 1, 2.5, 2.5);
        }
        this.updateFrame();
    }
    updateFrame() {
        if (this.rail.hidden || !this.visible()) return;
        const rows = this.rows();
        if (!rows || rows.height <= 0) return;
        const height = this.rail.clientHeight, width = this.rail.clientWidth;
        const start = (this.scroller.scrollTop - rows.top) / rows.height;
        const end = (this.scroller.scrollTop + this.scroller.clientHeight - rows.top) / rows.height;
        const clamp01 = value => Math.min(1, Math.max(0, value));
        // Horizontal extent of the zoomed value range, relative to the full range.
        const plot = this.app.plot, linear = plot.isLinearScale?.();
        const position = value => linear ? value : Math.log10(Math.max(value, Number.MIN_VALUE));
        const [lo, hi] = (plot.originalXDomain || plot.xScale.domain()).map(position);
        const [a, b] = plot.xScale.domain().map(position);
        const left = clamp01((a - lo) / (hi - lo || 1)), right = clamp01((b - lo) / (hi - lo || 1));
        Object.assign(this.frame.style, {
            top: `${clamp01(start) * height}px`,
            height: `${Math.max(6, (clamp01(end) - clamp01(start)) * height)}px`,
            left: `${left * width}px`,
            width: `${Math.max(6, (right - left) * width)}px`
        });
    }
}
window.PlotOverview = PlotOverview;
