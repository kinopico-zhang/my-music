/* autocache.js 的 node --test 单元测试: LRU 挤位/读即续命/自愈/幂等/
   超大拒绝/整仓清空/坏索引容错 (1.8.77 播放时自动缓存下一曲)。 */
import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const dir = path.join(path.dirname(fileURLToPath(import.meta.url)),
                      "../../app/music/static/js");
const { createAutoCache } = require(path.join(dir, "autocache.js"));

/** 桩适配器: 索引在内存里, 缓存是 Map (键 = 流地址), now 可注入可变。 */
function stubAdapters({ now = 1000 } = {}) {
  const calls = { puts: [], deletes: [] };
  let index = [];
  const cache = new Map();
  const nowValue = () => (typeof now === "function" ? now() : now);
  return {
    adapters: {
      readIndex() { return index; },
      writeIndex(entries) { index = entries; },
      async cachePut(url, body, contentType) {
        calls.puts.push({ url, size: body.size, contentType });
        cache.set(url, body);
      },
      async cacheRead(url) { return cache.get(url) || null; },
      async cacheDelete(url) { calls.deletes.push(url); cache.delete(url); },
      now: nowValue,
    },
    calls,
    index: () => index,
  };
}

const blobOf = (size, type = "audio/flac") =>
  new Blob([new Uint8Array(size)], { type });

test("put: 字节进缓存 + 索引落库, has/usage 同步答 (只看索引不碰字节)", async () => {
  const { adapters, index, calls } = stubAdapters();
  const cache = createAutoCache(adapters, { maxBytes: 100 });
  assert.equal(await cache.put(7, blobOf(30)), true);
  assert.equal(cache.has(7), true);
  assert.equal(cache.has(8), false);
  assert.deepEqual(cache.usage(), { count: 1, totalBytes: 30 });
  assert.equal(index().length, 1);
  assert.equal(index()[0].track_id, 7);
  assert.equal(index()[0].bytes, 30);
  assert.deepEqual(calls.puts,
    [{ url: "/music/media/stream/7", size: 30, contentType: "audio/flac" }]);
});

test("blob: 命中读回整曲字节, 读一次续一次命 (LRU 往后排)", async () => {
  let now = 1000;
  const { adapters, index } = stubAdapters({ now: () => now });
  const cache = createAutoCache(adapters, { maxBytes: 100 });
  await cache.put(7, blobOf(30));
  now = 2000;
  const blob = await cache.blob(7);
  assert.equal(blob.size, 30);
  assert.equal(index()[0].cached_at, 2000);   // 续命了
});

test("blob 自愈: 索引说有、字节没了 (系统清存储), 移出索引给 null", async () => {
  const { adapters } = stubAdapters();
  const cache = createAutoCache(adapters, { maxBytes: 100 });
  await cache.put(7, blobOf(30));
  await adapters.cacheDelete("/music/media/stream/7");   // 字节被系统清了
  assert.equal(await cache.blob(7), null);
  assert.equal(cache.has(7), false);   // 索引自愈掉了
});

test("blob: 索引里压根没有这首, 直接 null (不碰缓存)", async () => {
  const { adapters } = stubAdapters();
  const cache = createAutoCache(adapters, { maxBytes: 100 });
  assert.equal(await cache.blob(42), null);
  assert.deepEqual(adapters.readIndex(), []);   // 索引没被动过
});

test("put 幂等: 重存同一首只留一条, 时刻与字节重写", async () => {
  const { adapters } = stubAdapters();
  const cache = createAutoCache(adapters, { maxBytes: 100 });
  await cache.put(7, blobOf(30));
  assert.equal(await cache.put(7, blobOf(40)), true);
  assert.deepEqual(cache.usage(), { count: 1, totalBytes: 40 });
});

test("LRU 挤位: 满了清最久没听的, 新存的不许被自己挤掉; 续命过的留得住", async () => {
  let now = 1000;
  const { adapters, calls } = stubAdapters({ now: () => now });
  const cache = createAutoCache(adapters, { maxBytes: 100 });
  await cache.put(1, blobOf(40));          // 1000
  now = 1100;
  await cache.put(2, blobOf(40));          // 1100
  now = 1200;
  await cache.put(3, blobOf(40));          // 1200 → 超了: 清 1 (最旧)
  assert.equal(cache.has(1), false);
  assert.equal(cache.has(2), true);
  assert.equal(cache.has(3), true);
  assert.deepEqual(calls.deletes, ["/music/media/stream/1"]);
  now = 1300;
  await cache.blob(2);                     // 2 续命 → 1300
  now = 1400;
  await cache.put(4, blobOf(40));          // 3 (1200) 最旧 → 清 3 不清 2
  assert.equal(cache.has(2), true);
  assert.equal(cache.has(3), false);
  assert.equal(cache.has(4), true);
});

test("put 超预算: 一首就比预算大不硬塞 (塞了 = 清光别人), 索引缓存都不动", async () => {
  const { adapters, calls } = stubAdapters();
  const cache = createAutoCache(adapters, { maxBytes: 50 });
  assert.equal(await cache.put(7, blobOf(60)), false);
  assert.equal(cache.has(7), false);
  assert.deepEqual(calls.puts, []);
});

test("remove/clear: 缓存与索引一起清", async () => {
  const { adapters, calls } = stubAdapters();
  const cache = createAutoCache(adapters, { maxBytes: 100 });
  await cache.put(1, blobOf(30));
  await cache.put(2, blobOf(30));
  await cache.remove(1);
  assert.equal(cache.has(1), false);
  assert.deepEqual(cache.usage(), { count: 1, totalBytes: 30 });
  await cache.clear();
  assert.deepEqual(cache.usage(), { count: 0, totalBytes: 0 });
  assert.deepEqual(calls.deletes, ["/music/media/stream/1",   // remove
                                   "/music/media/stream/2"]);   // clear 扫剩下的
});

test("索引脏数据: 整体不是数组当空, 坏行丢弃好行保留", async () => {
  const { adapters } = stubAdapters();
  adapters.writeIndex("手改坏的");
  const cache = createAutoCache(adapters, { maxBytes: 100 });
  assert.equal(cache.has(7), false);
  assert.deepEqual(cache.usage(), { count: 0, totalBytes: 0 });
  adapters.writeIndex([{ track_id: 1, bytes: 10, cached_at: 5 },
                       null,
                       { track_id: "x", bytes: 10, cached_at: 5 },
                       { track_id: 2, cached_at: 5 }]);
  assert.equal(cache.has(1), true);
  assert.equal(cache.has(2), false);   // 缺 bytes 的坏行不算数
});

test("默认预算 2GB + 缓存内容类型兜底 (blob 无 type 时)", async () => {
  const { adapters, calls } = stubAdapters();
  const cache = createAutoCache(adapters);   // 不传 options
  assert.equal(await cache.put(7, new Blob(["x"])), true);
  assert.equal(calls.puts[0].contentType, "application/octet-stream");
});

test("坏入参: 非数 id / 空 blob 拒收", async () => {
  const { adapters } = stubAdapters();
  const cache = createAutoCache(adapters, { maxBytes: 100 });
  assert.equal(await cache.put(Number.NaN, blobOf(10)), false);
  assert.equal(await cache.put(7, new Blob([])), false);
  assert.equal(cache.has(7), false);
});

test("reconcile 对账 (1.8.101): 字节没了的影子账出清, 在场的保留; 没影子可出索引不动", async () => {
  const { adapters } = stubAdapters();
  const cache = createAutoCache(adapters, { maxBytes: 100 });
  await cache.put(1, blobOf(30));
  await cache.put(2, blobOf(30));
  await cache.put(3, blobOf(30));
  assert.equal(cache.reconcile(new Set([2, 3])), 1);   // 1 的字节被系统清了
  assert.equal(cache.has(1), false);
  assert.equal(cache.has(2), true);
  assert.deepEqual(cache.usage(), { count: 2, totalBytes: 60 });  // 不再谎报
  assert.equal(cache.reconcile(new Set([2, 3])), 0);   // 全在场: 索引不动
});

test("setBudget 收紧 (1.8.101): 超新预算的清最旧, 字节与索引一起走", async () => {
  let now = 1000;
  const { adapters, calls } = stubAdapters({ now: () => now });
  const cache = createAutoCache(adapters, { maxBytes: 100 });
  await cache.put(1, blobOf(40));          // 1000
  now = 1100;
  await cache.put(2, blobOf(40));          // 1100
  await cache.setBudget(50);               // 只留得住一首: 清 1 (最旧)
  assert.equal(cache.has(1), false);
  assert.equal(cache.has(2), true);
  assert.deepEqual(calls.deletes, ["/music/media/stream/1"]);
  assert.deepEqual(cache.usage(), { count: 1, totalBytes: 40 });
});
