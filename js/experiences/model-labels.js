// Resolve dense labels in screen coordinates without moving their 3D anchors.
export function layoutModelLabels(labels, viewport) {
    const occupied = [];
    const overlap = (a, b) => a.left < b.right + 5 && a.right + 5 > b.left &&
        a.top < b.bottom + 4 && a.bottom + 4 > b.top;
    return labels.map(label => {
        const width = Math.max(18, label.text.length * 7), height = 16;
        let chosen;
        for (let ring = 0; ring < 14 && !chosen; ring++) {
            const distance = 12 + ring * 16;
            for (const [dx, dy] of [[0, -distance], [distance, -distance], [-distance, -distance],
                [distance, distance], [-distance, distance], [0, distance]]) {
                const x = Math.max(viewport.left + width / 2 + 4,
                    Math.min(viewport.right - width / 2 - 4, label.x + dx));
                const y = Math.max(viewport.top + height + 4, Math.min(viewport.bottom - 5, label.y + dy));
                const box = { left: x - width / 2, right: x + width / 2, top: y - height, bottom: y + 3 };
                if (!occupied.some(other => overlap(box, other))) {
                    chosen = { ...label, labelX: x, labelY: y, box };
                    break;
                }
            }
        }
        chosen ||= { ...label, labelX: label.x, labelY: label.y - 12,
            box: { left: label.x - width / 2, right: label.x + width / 2, top: label.y - 28, bottom: label.y - 9 } };
        occupied.push(chosen.box);
        return chosen;
    });
}
