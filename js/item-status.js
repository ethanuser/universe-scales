// Editorial completeness, shown as a four-step meter on dimensions and items. Levels are computed
// from what an entry has; "Reviewed" is the only one that takes a person, through
// `owner_reviewed: true` on an item, and no item has it yet. This is not `review_status` in the
// data, which only records that the build pipeline accepted an item.
(function (root) {
    const ITEM_LEVELS = [
        { label: 'Stub', note: 'Listed with a value, but its description is short or unsourced.' },
        { label: 'Draft', note: 'Has a full description and a source. Not yet checked by hand.' },
        { label: 'Developed', note: 'A draft with its own 3D model. Not yet checked by hand.' },
        { label: 'Reviewed', note: 'Checked by hand against its sources.' }
    ];
    const DIMENSION_LEVELS = [
        { label: 'Stub', note: 'Most items here are stubs.' },
        { label: 'In progress', note: 'Most items have a full description.' },
        { label: 'Complete', note: 'A broad set of items with full descriptions. Not yet checked by hand.' },
        { label: 'Reviewed', note: 'Every item checked by hand.' }
    ];
    const FULL_DESCRIPTION = 200, BROAD_SET = 100;
    const hasSource = item => /^https?:/.test(item.source || '') ||
        (item.sources || []).some(source => /^https?:/.test(source.url || ''));
    function itemLevel(item, hasModel = false) {
        if (item.owner_reviewed === true) return 3;
        if (String(item.description || '').trim().length < FULL_DESCRIPTION || !hasSource(item)) return 0;
        return hasModel ? 2 : 1;
    }
    // counts: { items, drafted, reviewed } (drafted: items past Stub).
    function dimensionLevel({ items, drafted, reviewed }) {
        if (items > 0 && reviewed === items) return 3;
        if (drafted < items * 0.5) return 0;
        return items >= BROAD_SET && drafted >= items * 0.9 ? 2 : 1;
    }
    function summarize(items) {
        const levels = items.map(item => itemLevel(item));
        return { items: items.length, drafted: levels.filter(level => level > 0).length,
            reviewed: levels.filter(level => level === 3).length };
    }
    const forItem = (item, dimension) => itemLevel(item, Boolean(root.ScaleModels?.hasModel?.(dimension, item.name)));
    // The meter: four bars, filled up to the level. `title` becomes the app's styled tooltip.
    function meter(level, levels = ITEM_LEVELS) {
        const span = root.document.createElement('span');
        span.className = 'status-meter';
        span.dataset.level = level;
        span.setAttribute('role', 'img');
        span.setAttribute('aria-label', levels[level].label);
        span.title = `${levels[level].label}: ${levels[level].note}`;
        for (let bar = 0; bar < levels.length; bar++) span.append(root.document.createElement('i'));
        return span;
    }
    root.ScaleStatus = { ITEM_LEVELS, DIMENSION_LEVELS, FULL_DESCRIPTION, itemLevel, dimensionLevel, summarize, forItem, meter };
    if (typeof module !== 'undefined') module.exports = root.ScaleStatus;
})(globalThis);
