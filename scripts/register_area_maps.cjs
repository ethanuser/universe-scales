const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const planets = JSON.parse(fs.readFileSync(path.join(root,'content/visualizations/area-maps/manifest.json')));
const entries = [...planets.entries];
const geographyPath = path.join(root,'handoff/area-gis/entries.json');
if (!process.argv.includes('--planets-only') && fs.existsSync(geographyPath)) {
    for (const entry of JSON.parse(fs.readFileSync(geographyPath))) {
        if (!entry.id || !entry.name || !/^https:\/\//.test(entry.source) || !entry.license ||
            !entry.license_url || !entry.author || !entry.note || !entry.geojson)
            throw Error('Incomplete map provenance: ' + entry.name);
        entries.push(entry);
    }
}
if (new Set(entries.map(e=>e.name)).size !== entries.length) throw Error('Duplicate map names');
const output = JSON.stringify({schema_version:1,entries},null,2)+'\n';
const file = path.join(root,'content/visualizations/area-maps.json');
if (process.argv.includes('--check')) {
    if (fs.readFileSync(file,'utf8') !== output) throw Error('Area map catalog is stale');
} else fs.writeFileSync(file,output);
console.log(entries.length+' sourced area maps');
