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
        const x = label.x, y = label.y - (label.offset ?? 6);
        const box = { left: x - width / 2, right: x + width / 2, top: y - height, bottom: y + 2 };
        const inside = box.left >= viewport.left && box.right <= viewport.right &&
            box.top >= viewport.top && box.bottom <= viewport.bottom;
        label.labelX = x; label.labelY = y; label.box = box;
        label.visible = inside && !accepted.some(other => overlap(box, other.box));
        if (label.visible) accepted.push(label);
    }
    return ordered.sort((a, b) => a.index - b.index);
}
