export class ModelCache {
    constructor({ maxEntries = 32, maxBytes = 128 * 1024 * 1024, measure = () => 0, dispose = () => {} } = {}) {
        this.maxEntries = maxEntries;
        this.maxBytes = maxBytes;
        this.measure = measure;
        this.dispose = dispose;
        this.records = new Map();
        this.bytes = 0;
        this.clock = 0;
    }

    acquire(key, loader) {
        let record = this.records.get(key);
        if (!record) {
            record = { key, pins: 0, value: undefined, bytes: 0, pending: true, used: ++this.clock };
            this.records.set(key, record);
            let loaded;
            try { loaded = Promise.resolve(loader()); }
            catch (error) { loaded = Promise.reject(error); }
            record.promise = loaded.then(value => {
                if (this.records.get(key) !== record) return value;
                record.pending = false;
                if (value == null) {
                    this.records.delete(key);
                    this.trim();
                    return value;
                }
                record.value = value;
                try { record.bytes = Math.max(0, Number(this.measure(value)) || 0); }
                catch { record.bytes = 0; }
                this.bytes += record.bytes;
                this.trim();
                return value;
            }, error => {
                if (this.records.get(key) === record) this.records.delete(key);
                this.trim();
                throw error;
            });
            // The lease promise preserves rejection for consumers; this observer
            // prevents an ignored/released lease from becoming an unhandled rejection.
            record.promise.catch(() => {});
        }
        record.pins++;
        record.used = ++this.clock;
        let released = false;
        return {
            promise: record.promise,
            release: () => {
                if (released) return;
                released = true;
                record.pins = Math.max(0, record.pins - 1);
                this.trim();
            },
            touch: () => {
                if (this.records.get(key) === record) record.used = ++this.clock;
            }
        };
    }

    setLimits({ maxEntries = this.maxEntries, maxBytes = this.maxBytes } = {}) {
        this.maxEntries = maxEntries;
        this.maxBytes = maxBytes;
        this.trim();
    }

    stats() {
        let pinned = 0, pending = 0;
        for (const record of this.records.values()) {
            pinned += record.pins;
            if (record.pending) pending++;
        }
        return { entries: this.records.size, bytes: this.bytes, pinned, pending, maxEntries: this.maxEntries, maxBytes: this.maxBytes };
    }

    trim() {
        while (this.records.size > this.maxEntries || this.bytes > this.maxBytes) {
            let candidate;
            for (const record of this.records.values()) {
                if (record.pending || record.pins) continue;
                if (!candidate || record.used < candidate.used) candidate = record;
            }
            if (!candidate) break;
            this.records.delete(candidate.key);
            this.bytes -= candidate.bytes;
            try { this.dispose(candidate.value); } catch { /* Disposal must not break cache bookkeeping. */ }
        }
    }
}
