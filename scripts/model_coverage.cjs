// Inventory is separate from visual approval: a source link alone is not a quality score.
function coverageReport(catalog, minimumGap = 1) {
    const items = catalog.filter(item => Number.isFinite(item.value) && item.value > 0)
        .slice().sort((a, b) => a.value - b.value || a.name.localeCompare(b.name));
    const gaps = [];
    for (let index = 1; index < items.length; index++) {
        const lower = items[index - 1], upper = items[index];
        const decades = Math.log10(upper.value) - Math.log10(lower.value);
        if (decades >= minimumGap) gaps.push({ lower: lower.name, upper: upper.name,
            lowerMeters: lower.value, upperMeters: upper.value,
            decades: +decades.toFixed(3), midpointMeters: Math.sqrt(lower.value) * Math.sqrt(upper.value) });
    }
    gaps.sort((a, b) => b.decades - a.decades);
    const modeled = items.filter(item => item.model);
    return { dimension: 'length', total: items.length, modeled: modeled.length,
        photoOnly: items.filter(item => !item.model).map(item => item.name),
        missingModelNotes: modeled.filter(item => !item.note?.trim()).map(item => item.name),
        missingModelReferences: modeled.filter(item => !item.source && !item.basis).map(item => item.name),
        unclassifiedRepresentations: modeled.filter(item => !item.representation).map(item => item.name),
        oversizedAssets: modeled.filter(item => item.bytes > 1.5 * 1024 ** 2).map(item => ({ name: item.name, bytes: item.bytes })),
        gaps, items };
}
module.exports = { coverageReport };
