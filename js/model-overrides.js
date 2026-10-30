// Per-item 3D model adjustments made in the data editor, kept in this browser only.
// Size and rotation live in localStorage; uploaded GLB files live in IndexedDB and are served to
// the model stage as object URLs. Changes fire a `scale-model-override` event on window.
(function (root) {
    const STORE_KEY = 'scale-model-overrides';
    const DB_NAME = 'universe-scales', DB_STORE = 'models';
    const keyFor = (dimension, name) => `${dimension}::${name}`;
    let records = {};
    try { records = JSON.parse(localStorage.getItem(STORE_KEY) || '{}') || {}; } catch { records = {}; }
    const urls = new Map();
    const save = () => { try { localStorage.setItem(STORE_KEY, JSON.stringify(records)); } catch {} };
    const notify = (key, reload = false) => root.dispatchEvent(new CustomEvent('scale-model-override', { detail: { key, reload } }));
    const database = () => new Promise((resolve, reject) => {
        if (!root.indexedDB) { reject(new Error('IndexedDB unavailable')); return; }
        const request = indexedDB.open(DB_NAME, 1);
        request.onupgradeneeded = () => request.result.createObjectStore(DB_STORE);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
    const transact = (mode, work) => database().then(db => new Promise((resolve, reject) => {
        const store = db.transaction(DB_STORE, mode).objectStore(DB_STORE);
        const request = work(store);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    }));
    // Restore object URLs for uploads saved in earlier visits.
    const ready = Promise.all(Object.entries(records).filter(([, record]) => record.file).map(([key]) =>
        transact('readonly', store => store.get(key)).then(blob => {
            if (blob) { urls.set(key, URL.createObjectURL(blob)); notify(key, true); }
        }).catch(() => {})));

    root.ModelOverrides = {
        ready,
        key: keyFor,
        // The merged override for an item, or null: { presentation, src, fileName, version }.
        get(dimension, name) {
            const key = keyFor(dimension, name), record = records[key];
            if (!record) return null;
            return { key, presentation: record.presentation || null, src: urls.get(key) || null,
                fileName: record.file?.name || null, version: record.file?.version || 0 };
        },
        setPresentation(dimension, name, patch) {
            const key = keyFor(dimension, name);
            const record = records[key] ||= {};
            record.presentation = { ...(record.presentation || {}), ...patch };
            for (const [field, value] of Object.entries(record.presentation)) if (value == null) delete record.presentation[field];
            save();
            notify(key);
        },
        async setFile(dimension, name, file) {
            const key = keyFor(dimension, name);
            await transact('readwrite', store => store.put(file, key));
            if (urls.has(key)) URL.revokeObjectURL(urls.get(key));
            urls.set(key, URL.createObjectURL(file));
            const record = records[key] ||= {};
            record.file = { name: file.name, size: file.size, version: Date.now() };
            save();
            notify(key, true);
        },
        async clear(dimension, name) {
            const key = keyFor(dimension, name), hadFile = Boolean(records[key]?.file);
            delete records[key];
            save();
            if (urls.has(key)) { URL.revokeObjectURL(urls.get(key)); urls.delete(key); }
            if (hadFile) await transact('readwrite', store => store.delete(key)).catch(() => {});
            notify(key, hadFile);
        }
    };
})(globalThis);
