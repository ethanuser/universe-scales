// Reuse credited local assets in the existing mean-angular-speed orbit view.
// These are visual identifiers, not a new mesh, ephemeris, or physical size scale.
const bodies = {
    'Pluto orbit around the Sun': ['nasa-pluto', 'nasa-sun', 'Sun'],
    'Mars orbit around the Sun': ['nasa-mars-length', 'nasa-sun', 'Sun'],
    'Earth orbit around the Sun': ['nasa-earth', 'nasa-sun', 'Sun'],
    'Venus orbit around the Sun': ['nasa-venus', 'nasa-sun', 'Sun'],
    'Mercury orbit around the Sun': ['nasa-mercury', 'nasa-sun', 'Sun'],
    'Moon orbit': ['nasa-moon', 'nasa-earth', 'Earth'],
    'Moon orbit around Earth': ['nasa-moon', 'nasa-earth', 'Earth'],
    'ISS orbit': ['nasa-iss-length', 'nasa-earth', 'Earth']
};

export function orbitalAssets(item, entries) {
    const specification = bodies[item.name];
    if (!specification) return null;
    const [bodyId, centerId, centerName] = specification;
    const body = entries.find(entry => entry.id === bodyId);
    const center = entries.find(entry => entry.id === centerId);
    if (!body || !center) return null;
    return { body, center, centerName };
}

export function orbitalEntry(item, entries) {
    const assets = orbitalAssets(item, entries);
    if (!assets) return null;
    return { ...assets.body, angular_motion: undefined,
        additional_sources: [{label: `${assets.centerName} model`, url: assets.center.source}],
        note: `${assets.body.note || ''} In this angular-velocity view the model follows the existing circular, constant-mean-speed guide. Body sizes and orbital distance are enlarged independently for visibility, not to scale. Surface attitude is held fixed: axial spin, synchronous lunar attitude, ISS attitude control, eccentricity and current orbital positions are not simulated.` };
}
