(function (root) {
    const A = [1.340264, -0.081106, 0.000893, 0.003796];
    const M = Math.sqrt(3) / 2;
    function forward(lon, lat) {
        const t = Math.asin(M * Math.sin(lat)), t2 = t * t, t6 = t2 ** 3;
        const derivative = A[0] + 3 * A[1] * t2 + t6 * (7 * A[2] + 9 * A[3] * t2);
        return [lon * Math.cos(t) / (M * derivative), t * (A[0] + A[1] * t2 + t6 * (A[2] + A[3] * t2))];
    }
    function inverse(x, y) {
        let t = y;
        for (let i = 0; i < 12; i++) {
            const t2 = t * t, t6 = t2 ** 3;
            const derivative = A[0] + 3 * A[1] * t2 + t6 * (7 * A[2] + 9 * A[3] * t2);
            t -= (t * (A[0] + A[1] * t2 + t6 * (A[2] + A[3] * t2)) - y) / derivative;
        }
        const t2 = t * t, t6 = t2 ** 3;
        return [M * x * (A[0] + 3 * A[1] * t2 + t6 * (7 * A[2] + 9 * A[3] * t2)) / Math.cos(t),
            Math.asin(Math.max(-1, Math.min(1, Math.sin(t) / M)))];
    }
    const sphereBounds = [forward(Math.PI, 0)[0], forward(0, Math.PI / 2)[1]];
    const sphereDimensions = sphereBounds.map(v => 2 * v / Math.sqrt(4 * Math.PI));

    // This is cartographic reprojection, not inferred 3D terrain. Shapes retain holes/islands.
    function projectGeometry(geometry, longitude = 0) {
        const data = JSON.parse(JSON.stringify(geometry));
        function orient(feature) {
            if (feature.type === 'FeatureCollection') return feature.features.forEach(orient);
            if (feature.type === 'Feature') return orient(feature.geometry);
            if (feature.type === 'GeometryCollection') return feature.geometries.forEach(orient);
            const polygons = feature.type === 'Polygon' ? [feature.coordinates] : feature.coordinates;
            if (!['Polygon', 'MultiPolygon'].includes(feature.type)) throw new Error('Area outlines must be polygons');
            for (const polygon of polygons) {
                // GeoJSON uses exterior CCW winding; D3 spherical polygons use CW.
                if (d3.geoArea({ type: 'Polygon', coordinates: polygon }) > 2 * Math.PI)
                    polygon.forEach(ring => ring.reverse());
            }
        }
        orient(data);
        // A spherical rotation preserves area and avoids flattening polar regions
        // merely because they were cut from a global equatorial map.
        const latitude = d3.geoCentroid(data)[1];
        const projection = d3.geoEqualEarth().rotate([-longitude, -latitude]).scale(1).translate([0, 0]).precision(0.00001);
        const path = d3.geoPath(projection);
        const area = path.area(data);
        if (!(area > 0)) throw new Error('Empty projected area');
        projection.scale(1 / Math.sqrt(area));
        const bounds = path.bounds(data), width = bounds[1][0] - bounds[0][0], height = bounds[1][1] - bounds[0][1];
        projection.translate([-(bounds[0][0] + bounds[1][0]) / 2, -bounds[1][1]]);
        return { path: path.digits(6)(data), width, height, area: path.area(data), centralLatitude: latitude };
    }
    class Catalog {
        constructor(onReady) {
            this.entries = new Map();
            this.ready = this.load().then(() => onReady?.()).catch(error => {
                console.warn('Area map catalog unavailable:', error);
                onReady?.();
            });
        }
        async load() {
            const response = await fetch('content/visualizations/area-maps.json');
            if (!response.ok) throw new Error(`Area catalog: ${response.status}`);
            const manifest = await response.json();
            await Promise.all(manifest.entries.map(async source => {
                try {
                    const entry = { ...source, note_heading: 'What this area view shows', link_label: 'Map source' };
                    if (entry.geojson) {
                        const response = await fetch(entry.geojson);
                        if (!response.ok) throw new Error(`${entry.geojson}: ${response.status}`);
                        Object.assign(entry, projectGeometry(await response.json(), entry.central_longitude || 0));
                        entry.note += ' The Equal Earth view is centered on this region, reducing polar shape distortion while preserving area. Its full filled outline is uniformly calibrated to the listed area.';
                    } else [entry.width, entry.height] = sphereDimensions;
                    entry.presentation = { focus_scale_factor: Math.max(1, entry.height, entry.width / 1.5) };
                    this.entries.set(entry.name, entry);
                } catch (error) { console.warn('Area map unavailable:', source.name, error); }
            }));
        }
        entry(item) { return this.entries.get(item.name); }
        draw(group, item, x, y, size) {
            const entry = this.entry(item);
            if (!entry) return false;
            group.dataset.areaMap = entry.id;
            group.dataset.normalizedArea = '1';
            const { svg } = ScaleControls;
            if (entry.path) group.append(svg('path', { d: entry.path, transform: `translate(${x} ${y}) scale(${size})`,
                fill: entry.fill || '#6f9c93', stroke: '#314f49', 'stroke-width': 0.8, 'vector-effect': 'non-scaling-stroke' }));
            else group.append(svg('image', { href: entry.src, x: x - size * entry.width / 2, y: y - size * entry.height,
                width: size * entry.width, height: size * entry.height, preserveAspectRatio: 'none' }));
            return true;
        }
    }
    const api = { forward, inverse, sphereBounds, sphereDimensions, projectGeometry, Catalog };
    root.ScaleAreaMaps = api;
    if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
