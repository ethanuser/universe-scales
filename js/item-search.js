// Item search shared by the explorer's item picker and the chart: forgiving matching on names
// (word starts, initials such as "ISS", plurals, punctuation-insensitive), a short list of
// everyday synonyms, and then the item's own description text as a fallback.
(function (root) {
    const SYNONYMS = {
        'trex': ['tyrannosaurus'], 't rex': ['tyrannosaurus'], 'dinosaur': ['tyrannosaurus', 'titanosaur'],
        'covid': ['sars cov 2'], 'coronavirus': ['sars cov 2'], 'germ': ['bacteria', 'virus'], 'microbe': ['bacteria', 'virus', 'mycoplasma'],
        'person': ['human'], 'people': ['human'], 'man': ['human'], 'woman': ['human'], 'body': ['human'],
        'building': ['burj khalifa', 'eiffel tower', 'statue of liberty'], 'skyscraper': ['burj khalifa'], 'tower': ['eiffel tower', 'burj khalifa'],
        'plane': ['boeing'], 'airplane': ['boeing'], 'aircraft': ['boeing', 'hindenburg'], 'airship': ['hindenburg'], 'blimp': ['hindenburg'],
        'ship': ['titanic', 'ever given', 'prelude'], 'boat': ['titanic', 'ever given'],
        'space station': ['international space station'], 'telescope': ['hubble', 'webb', 'arecibo', 'fast radio', 'very large telescope'],
        'black hole': ['event horizon', 'm87', 'sagittarius a', 'ton 618'], 'mountain': ['everest', 'kilimanjaro', 'mauna kea', 'thor'],
        'volcano': ['mauna kea', 'hunga tonga', 'olympus'], 'ocean': ['mariana trench', 'pacific'], 'trench': ['mariana trench'],
        'star': ['sun', 'sirius', 'proxima', 'betelgeuse', 'vega', 'neutron star'], 'planet': ['earth', 'jupiter', 'mars', 'venus', 'mercury', 'saturn', 'uranus', 'neptune'],
        'milky way': ['galaxy diameter', 'milky way'], 'universe': ['observable universe'], 'cosmos': ['observable universe'],
        'light': ['visible light', 'light year'], 'color': ['visible light'], 'colour': ['visible light'],
        'dna': ['dna helix'], 'gene': ['dna'], 'virus': ['virus', 'bacteriophage', 'mimivirus', 'sars', 'influenza', 'tobacco mosaic'],
        'cat': ['cat'], 'dog': ['dog'], 'whale': ['blue whale', 'sperm whale'], 'bird': ['albatross', 'hummingbird'], 'insect': ['ant', 'fly', 'beetle', 'flea', 'bee'],
        'bug': ['ant', 'fly', 'beetle', 'flea', 'mite'], 'tree': ['hyperion'], 'redwood': ['hyperion'], 'flower': ['rafflesia'],
        'car': ['car'], 'phone': ['smartphone'], 'paper': ['a4 paper'], 'ball': ['basketball', 'tennis ball', 'table tennis', 'football'],
        'soccer': ['football field'], 'stadium': ['football field'], 'canal': ['panama canal', 'suez canal'], 'river': ['amazon river'],
        'wall': ['great wall'], 'pyramid': ['great pyramid'], 'egypt': ['great pyramid'], 'atom': ['atom', 'hydrogen', 'carbon'],
        'nucleus': ['nucleus', 'helium nucleus', 'atomic nucleus'], 'proton': ['proton'], 'electron': ['electron'], 'quark': ['quark']
    };
    const normalize = text => String(text || '').normalize('NFKD').replace(/[̀-ͯ]/g, '')
        .toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
    const singular = word => word.length > 4 && word.endsWith('ies') ? `${word.slice(0, -3)}y`
        : word.length > 3 && word.endsWith('s') && !word.endsWith('ss') && !word.endsWith('us') ? word.slice(0, -1) : word;
    const initials = name => {
        const words = normalize(name).split(' ').filter(Boolean);
        return words.length > 1 ? words.map(word => word[0]).join('') : '';
    };
    const cache = new WeakMap();
    function fields(item, describe) {
        if (cache.has(item)) return cache.get(item);
        const name = normalize(item.name);
        const entry = { name, words: ` ${name.split(' ').map(singular).join(' ')} `, initials: initials(item.name),
            text: ` ${normalize(describe ? describe(item) : [item.summary_short, item.hook, item.description].join(' '))
                .split(' ').map(singular).join(' ')} ` };
        cache.set(item, entry);
        return entry;
    }
    function score(item, query, describe) {
        const q = normalize(query);
        if (!q) return 1;
        const f = fields(item, describe);
        const expansions = [q, ...(SYNONYMS[q] || [])];
        let best = 0;
        for (const phrase of expansions) {
            const term = phrase.split(' ').map(singular).join(' ');
            if (f.name === phrase) best = Math.max(best, 100);
            else if (f.name.startsWith(phrase)) best = Math.max(best, 90);
            else if (f.initials && phrase.length >= 2 && !phrase.includes(' ') && f.initials.startsWith(phrase))
                best = Math.max(best, f.initials === phrase ? 88 : 84);
            else if (f.words.includes(` ${term}`)) best = Math.max(best, phrase === q ? 80 : 75);
            else if (f.name.includes(phrase)) best = Math.max(best, 70);
            const tokens = term.split(' ');
            if (best < 60 && tokens.every(token => f.words.includes(` ${token}`))) best = Math.max(best, phrase === q ? 60 : 55);
        }
        if (best) return best;
        const tokens = q.split(' ').map(singular);
        return tokens.every(token => f.text.includes(` ${token}`)) ? 30 : 0;
    }
    // Matches for a query, best first; ties keep the original order. Description-only matches
    // (score 30) appear only when nothing matches by name, so each letter typed narrows the list.
    function rank(items, query, describe) {
        const results = items.map((item, index) => ({ item, index, score: score(item, query, describe) }))
            .filter(result => result.score > 0);
        const named = results.filter(result => result.score > 30);
        return (named.length ? named : results).sort((a, b) => b.score - a.score || a.index - b.index);
    }
    // Scale bands for grouping item lists. Length, area and volume share named bands over the
    // equivalent length (sqrt of an area, cube root of a volume); other dimensions group by
    // powers of a thousand (thousands, millions, ...).
    const LENGTH_BANDS = [
        [-Infinity, 'Subnuclear'], [-15, 'Nuclear and subatomic'], [-10, 'Atoms and molecules'],
        [-7, 'Microscopic'], [-4, 'Small things'], [-1, 'Human scale'], [2, 'Buildings and landscapes'],
        [5, 'Planetary'], [8, 'Stars and solar systems'], [13, 'Interstellar'], [17, 'Galactic'], [22, 'Cosmic']
    ];
    const LENGTH_ORDER = { length: 1, area: 2, volume: 3 };
    const MAGNITUDES = { '-12': 'Trillionths', '-9': 'Billionths', '-6': 'Millionths', '-3': 'Thousandths',
        0: 'Ones to hundreds', 3: 'Thousands', 6: 'Millions', 9: 'Billions', 12: 'Trillions' };
    const SUPERSCRIPT = { '-': '⁻', 0: '⁰', 1: '¹', 2: '²', 3: '³', 4: '⁴', 5: '⁵', 6: '⁶', 7: '⁷', 8: '⁸', 9: '⁹' };
    const power = exponent => exponent === 0 ? '1' : `10${String(exponent).replace(/[-0-9]/g, c => SUPERSCRIPT[c])}`;
    function band(value, dimension) {
        if (!(value > 0) || !Number.isFinite(value)) return { key: 'other', label: 'No value yet', range: '' };
        const order = LENGTH_ORDER[dimension];
        if (order) {
            const exponent = Math.log10(value) / order;
            let index = 0;
            while (index + 1 < LENGTH_BANDS.length && exponent >= LENGTH_BANDS[index + 1][0] - 1e-9) index++;
            const low = LENGTH_BANDS[index][0], high = LENGTH_BANDS[index + 1]?.[0];
            const range = low === -Infinity ? `under ${power(high)} m` : high == null ? `over ${power(low)} m` : `${power(low)} to ${power(high)} m`;
            return { key: `length:${index}`, label: LENGTH_BANDS[index][1], range: order === 1 ? range : `${range} across` };
        }
        const exponent = Math.floor(Math.log10(value) / 3 + 1e-9) * 3;
        const range = `${power(exponent)} to ${power(exponent + 3)}`;
        return MAGNITUDES[exponent] ? { key: `e${exponent}`, label: MAGNITUDES[exponent], range }
            : { key: `e${exponent}`, label: range, range: '' };
    }
    // Items in their given order, split into consecutive runs that share a band.
    function groups(items, dimension, value = item => item.value) {
        const runs = [];
        items.forEach((item, index) => {
            const found = band(value(item), dimension);
            const last = runs.at(-1);
            if (last && last.key === found.key) last.indices.push(index);
            else runs.push({ ...found, indices: [index] });
        });
        return runs;
    }
    // Writes text into an element with real <sup> elements for the exponents above, because
    // Unicode superscript digits are uneven in most fonts.
    const PLAIN = Object.fromEntries(Object.entries(SUPERSCRIPT).map(([digit, mark]) => [mark, digit === '-' ? '−' : digit]));
    function writePowers(element, text) {
        element.replaceChildren(...String(text).split(/([⁻⁰¹²³⁴⁵⁶⁷⁸⁹]+)/).map((part, index) => {
            if (index % 2 === 0) return document.createTextNode(part);
            const sup = document.createElement('sup');
            sup.textContent = [...part].map(mark => PLAIN[mark]).join('');
            return sup;
        }));
    }
    // Hides each band header whose items are all hidden, so a filtered list keeps its dividers.
    function syncHeaders(list, headerClass) {
        let header = null, shown = 0;
        const close = () => { if (header) header.hidden = shown === 0; };
        for (const node of list.children) {
            if (node.classList.contains(headerClass)) { close(); header = node; shown = 0; }
            else if (!node.hidden) shown++;
        }
        close();
    }
    root.ScaleSearch = { rank, score, normalize, band, groups, power, writePowers, syncHeaders };
    if (typeof module !== 'undefined') module.exports = root.ScaleSearch;
})(globalThis);
