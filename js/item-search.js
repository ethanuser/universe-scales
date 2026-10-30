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
    // Matches for a query, best first; ties keep the original order.
    function rank(items, query, describe) {
        return items.map((item, index) => ({ item, index, score: score(item, query, describe) }))
            .filter(result => result.score > 0)
            .sort((a, b) => b.score - a.score || a.index - b.index);
    }
    root.ScaleSearch = { rank, score, normalize };
    if (typeof module !== 'undefined') module.exports = root.ScaleSearch;
})(globalThis);
