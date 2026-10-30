// A symbol for every dimension (24x24 stroke icons, drawn in currentColor) and a color for each
// dimension group, used in the dimension picker, the dimension browser and the side panel.
(function (root) {
    const ICONS = {
        length: '<path d="M3 16 16 3l5 5L8 21Z"/><path d="M7 12l2 2M10 9l2 2M13 6l2 2"/>',
        duration: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/>',
        mass: '<path d="M6 9h12l2 11H4Z"/><circle cx="12" cy="6" r="2.5"/>',
        current: '<path d="M13 2 5 14h6l-1 8 8-12h-6Z"/>',
        temperature: '<path d="M10 4a2 2 0 0 1 4 0v10a4 4 0 1 1-4 0Z"/><path d="M12 9v7"/>',
        counts: '<path d="M5 5v14M9 5v14M13 5v14M17 5v14M3 16 19 8"/>',
        brightness: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
        area: '<rect x="4" y="4" width="16" height="16"/><path d="M4 12 12 4M4 20 20 4M12 20l8-8"/>',
        volume: '<path d="M12 3 20 7.5v9L12 21l-8-4.5v-9Z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/>',
        energy: '<path d="M12 3c1 4 6 6 6 11a6 6 0 0 1-12 0c0-3 2-4 3-7 1 2 2 3 3 3-1-3 0-5 0-7Z"/>',
        force: '<rect x="3" y="7" width="10" height="10"/><circle cx="8" cy="12" r="1"/><path d="M8 12h13M17.5 8.5 21 12l-3.5 3.5"/>',
        speed: '<path d="M4 17a8 8 0 1 1 16 0"/><path d="M12 17l5-6"/>',
        acceleration: '<path d="M4 6l6 6-6 6M12 6l6 6-6 6"/>',
        jerk: '<path d="M3 17l5-10 4 8 4-8 5 10"/>',
        torque: '<path d="M19 12a7 7 0 1 1-7-7"/><path d="M11 2l3 3-3 3"/><circle cx="12" cy="12" r="1.5"/>',
        'moment-of-inertia': '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="2"/><path d="M12 4v6M12 14v6M4 12h6M14 12h6"/>',
        angle: '<path d="M4 20h16M4 20 16 6"/><path d="M10 20a6 6 0 0 0-1.6-4.2"/>',
        'angular-velocity': '<path d="M20 12a8 8 0 1 1-3-6.2"/><path d="M17 2v4h4"/>',
        pressure: '<path d="M3 20h18"/><path d="M7 4v11M12 4v11M17 4v11M5 13l2 2 2-2M10 13l2 2 2-2M15 13l2 2 2-2"/>',
        'youngs-modulus': '<path d="M12 2v3l-5 2 10 3-10 3 10 3-5 2v4"/>',
        'yield-strength': '<path d="M3 12h7l2-4 2 8 2-4h5"/><path d="M3 8v8M21 8v8"/>',
        density: '<rect x="4" y="4" width="16" height="16"/><circle cx="8.5" cy="8.5" r="1.3"/><circle cx="15.5" cy="8.5" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="8.5" cy="15.5" r="1.3"/><circle cx="15.5" cy="15.5" r="1.3"/>',
        viscosity: '<path d="M12 3s6 7 6 11a6 6 0 0 1-12 0c0-4 6-11 6-11Z"/><path d="M9 15a3 3 0 0 0 3 3"/>',
        'flow-rate': '<path d="M3 9c3-3 6 3 9 0s6 3 9 0M3 15c3-3 6 3 9 0s6 3 9 0"/>',
        'surface-tension': '<path d="M3 19h18"/><path d="M6 19a6 6 0 0 1 12 0"/>',
        salinity: '<path d="M12 3 20 8v8l-8 5-8-5V8Z"/><path d="M12 3v18M4 8l16 8M20 8 4 16"/>',
        concentration: '<path d="M9 3h6M10 3v6l-5 10h14l-5-10V3"/><path d="M7 15h10"/>',
        hardness: '<path d="M6 4h12l3 5-9 11L3 9Z"/><path d="M3 9h18M9 4l-1 5 4 11 4-11-1-5"/>',
        strain: '<path d="M3 12h18M6 9l-3 3 3 3M18 9l3 3-3 3"/><path d="M9 7v10M15 7v10"/>',
        'thermal-conductivity': '<rect x="3" y="11" width="18" height="6"/><path d="M7 3c1.2 1.4-1.2 2.6 0 4M12 3c1.2 1.4-1.2 2.6 0 4M17 3c1.2 1.4-1.2 2.6 0 4"/>',
        'specific-heat': '<path d="M7 4a2 2 0 0 1 4 0v9a4 4 0 1 1-4 0Z"/><path d="M18 8c1 2 3 3 3 5a3 3 0 0 1-6 0c0-2 2-3 3-5Z"/>',
        frequency: '<path d="M2 12c2-6 3-6 5 0s3 6 5 0 3-6 5 0 3 6 5 0"/>',
        entropy: '<circle cx="6" cy="7" r="1.5"/><circle cx="16" cy="5" r="1.5"/><circle cx="11" cy="12" r="1.5"/><circle cx="19" cy="14" r="1.5"/><circle cx="5" cy="17" r="1.5"/><circle cx="14" cy="19" r="1.5"/>',
        charge: '<circle cx="7" cy="12" r="4.5"/><circle cx="17" cy="12" r="4.5"/><path d="M5 12h4M7 10v4M15 12h4"/>',
        'magnetic-field': '<path d="M5 4v8a7 7 0 0 0 14 0V4h-4v8a3 3 0 0 1-6 0V4Z"/><path d="M5 8h4M15 8h4"/>',
        'sound-intensity': '<path d="M4 9h4l5-4v14l-5-4H4Z"/><path d="M16.5 8.5a5 5 0 0 1 0 7M19 6a8.5 8.5 0 0 1 0 12"/>',
        intensity: '<circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4M5 5l3 3M16 16l3 3M5 19l3-3M16 8l3-3"/>',
        information: '<rect x="3" y="5" width="18" height="14"/><path d="M7 9v6M11 9h3v6h-3ZM18 9v6"/>',
        'information-rate': '<path d="M2 9a15 15 0 0 1 20 0M5 13a10 10 0 0 1 14 0M8.5 16.5a5 5 0 0 1 7 0"/><path d="M12 20v.5"/>',
        flops: '<rect x="6" y="6" width="12" height="12"/><rect x="9.5" y="9.5" width="5" height="5"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
        scoville: '<path d="M10 9c4-2 9 0 9 4 0 5-7 8-15 8 6-3 8-6 6-12Z"/><path d="M10 9c1-1.6 3.4-2.2 5.2-1.2"/><path d="M14.5 7.6c0-2 1-3.6 3-4.4"/>',
        'odor-concentration': '<path d="M7 21c0-3 3-4 3-7.5S7 9 7 5.5M12 21c0-3 3-4 3-7.5S12 9 12 5.5M17 21c0-3 3-4 3-7.5S17 9 17 5.5"/>',
        'sound-frequency': '<path d="M9 18V5l11-2v13"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',
        'visual-angle': '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
        roughness: '<path d="M3 16l3-4 2 3 3-6 2 4 3-5 2 3 3-2M3 20h18"/>',
        'friction-coefficient': '<path d="M3 20h18L3 8Z"/><path d="M7.99 11.33 13.40 14.93 15.95 11.11 10.54 7.50Z"/>',
        'population-density': '<circle cx="8" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M2 20c0-4 3-6 6-6s6 2 6 6M14 20c0-3 1.5-5 3-5s4 2 4 5"/>',
        'physiological-density': '<circle cx="8" cy="7" r="3"/><path d="M3 20c0-4 2-6 5-6s5 2 5 6"/><path d="M15 20c0-6 3-10 7-10-1 5-3 8-7 10Z"/>',
        'agricultural-density': '<path d="M12 21V7"/><path d="M12 8c-3 0-4-2-4-5 3 0 4 2 4 5ZM12 8c3 0 4-2 4-5-3 0-4 2-4 5ZM12 14c-3 0-4-2-4-5 3 0 4 2 4 5ZM12 14c3 0 4-2 4-5-3 0-4 2-4 5Z"/>',
        qalys: '<path d="M12 20s-8-5-8-11a4.5 4.5 0 0 1 8-2.5A4.5 4.5 0 0 1 20 9c0 6-8 11-8 11Z"/><path d="M7 11h3l1-2 2 4 1-2h3"/>',
        micromorts: '<path d="M12 3 22 20H2Z"/><path d="M12 9v5M12 17v.5"/>',
        'disease-rarity': '<circle cx="10" cy="10" r="6"/><path d="M14.5 14.5 21 21M10 7v6M7 10h6"/>',
        'cell-count': '<circle cx="8" cy="9" r="4"/><circle cx="16" cy="9" r="4"/><circle cx="12" cy="16" r="4"/>',
        'absorbed-dose': '<circle cx="12" cy="12" r="1.7"/><path d="M7.35 3.95A9.3 9.3 0 0 1 16.65 3.95L13.70 9.06A3.4 3.4 0 0 0 10.30 9.06ZM21.30 12.00A9.3 9.3 0 0 1 16.65 20.05L13.70 14.94A3.4 3.4 0 0 0 15.40 12.00ZM7.35 20.05A9.3 9.3 0 0 1 2.70 12.00L8.60 12.00A3.4 3.4 0 0 0 10.30 14.94Z"/>',
        costs: '<circle cx="12" cy="12" r="9"/><path d="M15 8.5c-1-1-5-1.5-5 1s5 1.5 5 4-4 2-5 1M12 6v12"/>',
        'historical-time': '<path d="M6 3h12M6 21h12M7 3c0 5 5 6 5 9s-5 4-5 9M17 3c0 5-5 6-5 9s5 4 5 9"/>',
        'event-rate': '<path d="M2 12h5l2-6 4 12 2-6h7"/>',
        probability: '<rect x="4" y="4" width="16" height="16"/><circle cx="8.5" cy="8.5" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="15.5" cy="15.5" r="1.3"/>',
        precision: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
        correlation: '<path d="M3 3v18h18"/><path d="M6 18 20 5"/><circle cx="8" cy="13" r="1"/><circle cx="11" cy="9" r="1"/><circle cx="15" cy="11" r="1"/><circle cx="17" cy="6" r="1"/>',
        'effect-size': '<path d="M3 21h18"/><rect x="5" y="12" width="5" height="9"/><rect x="14" y="5" width="5" height="16"/>',
        utility: '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9Z"/>',
        attention: '<path d="M12 4a6 6 0 0 0-6 6v4l-2 3h16l-2-3v-4a6 6 0 0 0-6-6Z"/><path d="M10 20a2 2 0 0 0 4 0"/>'
    };
    const FALLBACK = '<circle cx="12" cy="12" r="8"/><path d="M12 8v8M8 12h8"/>';
    // One hue per group; the darker theme gets lighter tints for contrast.
    const GROUP_COLORS = {
        'Fundamental Scales': ['#2563eb', '#7aa6ff'],
        'Geometry & Scale': ['#0f9488', '#4fd1c1'],
        'Motion & Mechanics': ['#d9690b', '#ffa45c'],
        'Materials & Matter': ['#8b6a3e', '#d2ad7a'],
        'Fields, Waves & Radiation': ['#7c4dd8', '#b49bff'],
        'Information & Computation': ['#15803d', '#5ed38c'],
        'Senses & Perception': ['#cc3d79', '#ff8ab8'],
        'Global & Geography': ['#0b84b6', '#5cc6f0'],
        'Health & Biology': ['#c93636', '#ff8a8a'],
        'Society, Economy & Abstract Quantities': ['#a7740a', '#e6b64a']
    };
    const icon = (slug, className = 'dimension-icon') =>
        `<svg class="${className}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${ICONS[slug] || FALLBACK}</svg>`;
    const color = (group, dark = document.documentElement.getAttribute('data-theme') === 'dark') =>
        (GROUP_COLORS[group] || ['#2563eb', '#7aa6ff'])[dark ? 1 : 0];
    root.DimensionIcons = { icon, color, has: slug => slug in ICONS, slugs: Object.keys(ICONS) };
})(globalThis);
