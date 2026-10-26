import assert from 'node:assert/strict';
import test from 'node:test';
import { ModelCache } from '../js/experiences/model-cache.js';

const deferred = () => {
    let resolve, reject;
    const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
    return { promise, resolve, reject };
};

test('deduplicates concurrent loads and releases each shared lease once', async () => {
    const gate = deferred();
    let calls = 0;
    const cache = new ModelCache();
    const a = cache.acquire('x', () => { calls++; return gate.promise; });
    const b = cache.acquire('x', () => { calls++; });
    assert.equal(calls, 1);
    assert.deepEqual(cache.stats(), { entries: 1, bytes: 0, pinned: 2, pending: 1, maxEntries: 32, maxBytes: 128 * 1024 * 1024 });
    const value = {};
    gate.resolve(value);
    assert.equal(await a.promise, value);
    assert.equal(await b.promise, value);
    a.release(); a.release();
    assert.equal(cache.stats().pinned, 1);
    b.release();
    assert.equal(cache.stats().pinned, 0);
});

test('touch updates LRU order and count and byte budgets evict oldest settled entries', async () => {
    const disposed = [];
    const cache = new ModelCache({ maxEntries: 2, maxBytes: 5, measure: value => value.size, dispose: value => disposed.push(value.id) });
    const add = async (key, size) => { const lease = cache.acquire(key, async () => ({ id: key, size })); await lease.promise; lease.release(); };
    await add('a', 2); await add('b', 2);
    const a = cache.acquire('a', () => { throw Error('must hit cache'); }); a.touch(); a.release();
    await add('c', 2);
    assert.deepEqual(disposed, ['b']);
    await add('d', 4);
    assert.deepEqual(disposed, ['b', 'a', 'c']);
    assert.equal(cache.stats().bytes, 4);
    assert.equal(cache.stats().entries, 1);
});

test('oversized pinned and pending entries exceed limits until safe to evict', async () => {
    const disposed = [];
    const cache = new ModelCache({ maxEntries: 0, maxBytes: 1, measure: v => v.size, dispose: v => disposed.push(v) });
    const gate = deferred();
    const lease = cache.acquire('large', () => gate.promise);
    lease.release();
    assert.equal(cache.stats().entries, 1, 'pending entries cannot be evicted');
    const value = { size: 10 };
    gate.resolve(value);
    await lease.promise;
    assert.equal(cache.stats().entries, 0);
    assert.deepEqual(disposed, [value]);
});

test('failed and null loads are removed so a later acquire retries', async () => {
    const cache = new ModelCache();
    const failed = cache.acquire('x', () => { throw new Error('no'); });
    await assert.rejects(failed.promise, /no/);
    failed.release();
    assert.equal(cache.stats().entries, 0);
    const empty = cache.acquire('x', async () => null);
    assert.equal(await empty.promise, null);
    empty.release();
    assert.equal(cache.stats().entries, 0);
    const retry = cache.acquire('x', async () => 42);
    assert.equal(await retry.promise, 42);
    retry.release();
});

test('setLimits trims immediately and disposer exceptions do not break bookkeeping', async () => {
    const cache = new ModelCache({ maxEntries: 4, dispose: () => { throw Error('dispose'); } });
    for (const key of ['a', 'b', 'c']) {
        const lease = cache.acquire(key, async () => key);
        await lease.promise;
        lease.release();
    }
    cache.setLimits({ maxEntries: 1, maxBytes: 0 });
    assert.equal(cache.stats().entries, 1);
    assert.equal(cache.stats().maxEntries, 1);
    assert.equal(cache.stats().maxBytes, 0);
});
