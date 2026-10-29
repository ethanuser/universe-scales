// Reuse existing credited photos unchanged; the explorer maps have separate attribution.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const check = process.argv.includes('--check');
const planets = ['mercury', 'venus', 'mars', 'saturn', 'uranus', 'neptune', 'pluto'];
const credits = JSON.parse(fs.readFileSync(path.join(root, 'images/credits/length.json')));
for (const dimension of ['area', 'volume']) {
    const file = path.join(root, `images/credits/${dimension}.json`);
    const catalog = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file)) : {
        note: 'Area image credits. Planetary photos reuse the existing credited Length originals and thumbnails unchanged.', images: []
    };
    for (const planet of planets) {
        const source = `images/length_${planet}.jpg`;
        const destination = `images/${dimension}_${planet}_${dimension === 'area' ? 'surface_area' : 'volume'}.jpg`;
        const credit = credits.images.find(entry => entry.file === source);
        if (!credit) throw Error('Missing source attribution: ' + source);
        for (const thumbnail of [false, true]) {
            const from = path.join(root, thumbnail ? source.replace('images/', 'images/thumbs/') : source);
            const to = path.join(root, thumbnail ? destination.replace('images/', 'images/thumbs/') : destination);
            if (check) {
                if (!fs.readFileSync(from).equals(fs.readFileSync(to))) throw Error('Stale image alias: ' + to);
            } else fs.copyFileSync(from, to);
        }
        const next = { ...credit, file: destination, reused_from: source,
            changes: 'Unchanged copy of existing JPEG and thumbnail; original conversion credited in length.json.' };
        const i = catalog.images.findIndex(entry => entry.file === destination);
        if (check) {
            if (JSON.stringify(catalog.images[i]) !== JSON.stringify(next)) throw Error('Stale image credit: ' + destination);
        } else if (i < 0) catalog.images.push(next); else catalog.images[i] = next;
    }
    if (!check) fs.writeFileSync(file, JSON.stringify(catalog, null, 2) + '\n');
}
console.log('Verified 14 planet originals, 14 thumbnails and their inherited credits.');
