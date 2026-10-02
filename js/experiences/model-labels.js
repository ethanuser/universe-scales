// Stable label placement for dense model annotations (e.g. planets). Each label
// sits at a fixed offset above its anchor, so it never jumps around while the
// camera zooms; where two labels would overlap, the lower-priority one is
// hidden rather than moved. Coordinates are SVG user units (labels are 12 px).
export function placeLabels(labels, viewport) {
    const accepted = [];
    const overlap = (a, b) => a.left < b.right + 4 && a.right + 4 > b.left && a.top < b.bottom + 2 && a.bottom + 2 > b.top;
    const ordered = labels.map((label, index) => ({ ...label, index }))
        .sort((a, b) => (a.priority ?? 99) - (b.priority ?? 99) || a.index - b.index);
    for (const label of ordered) {
        const width = label.text.length * 6.6 + 4, height = 13;
        const x = label.x + (label.callout?.x ?? 0);
        const y = label.y + (label.callout?.y ?? -(label.offset ?? 6));
        const box = { left: x - width / 2, right: x + width / 2, top: y - height, bottom: y + 2 };
        const inside = box.left >= viewport.left && box.right <= viewport.right &&
            box.top >= viewport.top && box.bottom <= viewport.bottom;
        label.labelX = x; label.labelY = y; label.box = box;
        label.visible = inside && !accepted.some(other => overlap(box, other.box));
        if (label.visible) accepted.push(label);
    }
    return ordered.sort((a, b) => a.index - b.index);
}

// Final screen-space pass, after item names and all model overlays are present.
// Keep anchors fixed as the camera moves; omit a lower-priority annotation
// instead of letting it collide with an item name or another annotation.
export function labelVisibility(boxes, gap = 5) {
    const accepted = [], visible = new Set();
    for (const box of boxes.slice().sort((a, b) => b.priority - a.priority || a.index - b.index)) {
        if (accepted.some(other => box.left < other.right + gap && box.right + gap > other.left &&
            box.top < other.bottom + gap && box.bottom + gap > other.top)) continue;
        accepted.push(box); visible.add(box.index);
    }
    return visible;
}

export function resolveLabelCollisions(stage) {
    const nodes = [...stage.querySelectorAll('.journey-object-label, .journey-model-label')];
    const boxes = nodes.map((node, index) => {
        const style = getComputedStyle(node);
        if (style.visibility === 'hidden' || style.display === 'none' || Number(style.opacity) < 0.05) return null;
        const rect = node.getBoundingClientRect();
        const priority = Number(node.dataset.labelPriority ?? (node.classList.contains('journey-object-label') ? 100 : 10));
        return { index, priority, left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom };
    }).filter(box => box && box.right > box.left && box.bottom > box.top);
    const visible = labelVisibility(boxes);
    nodes.forEach((node, index) => {
        if (visible.has(index)) return;
        (node.closest('[data-label-group]') || node).style.visibility = 'hidden';
    });
}
