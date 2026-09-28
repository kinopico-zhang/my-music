// autocache — My Music 自动缓存状态机 (1.8.77): 播放预取下一曲的整曲字节
// 顺手落盘, 下回切到这首歌缓存直读, 不再走网络。LRU 封顶 (默认 2GB):
// 满了清最久没听的, 读一次续一次命 (常听的留得住)。手动下载 (downloads.js)
// 是另一套仓, 互不清对方的字节。
// 网络与 Cache API 都是适配器注入 (node --test 直测 + tsc + c8); 浏览器
// 接线在 music-autocache-integration.js。
/**
 * 一条自动缓存索引 (localStorage "music-autocache"): 只记账, 不存展示
 * 信息 —— 这层是播放器的私仓, 不进任何列表页。
 * @typedef {Object} AutoCacheEntry
 * @property {number} track_id
 * @property {number} bytes
 * @property {number} cached_at    epoch 秒 (LRU 的命根: 最近用过的留得住)
 */

/**
 * 适配器 (浏览器实现在 music-autocache-integration.js, 测试用桩)。
 * @typedef {Object} AutoCacheAdapters
 * @property {Function} readIndex   () => Array<AutoCacheEntry>
 * @property {Function} writeIndex  (entries: Array<AutoCacheEntry>) => void
 * @property {Function} cachePut    (url, body, contentType) => Promise
 * @property {Function} cacheRead   (url) => Promise<Blob|null>
 * @property {Function} cacheDelete (url) => Promise
 * @property {Function} now         () => number   epoch 秒 (测试可注入)
 */

/**
 * 自动缓存管理器。
 * @typedef {Object} AutoCacheManager
 * @property {Function} has    (trackId: number) => boolean            只看索引, 同步
 * @property {Function} blob   (trackId: number) => Promise<Blob|null> 命中即续命;
 *                             索引说有、字节没了 (被系统清) 自愈出索引
 * @property {Function} put    (trackId: number, blob: Blob) => Promise<boolean>
 *                             幂等重写; 一首超预算不硬塞; 挤位只清旧的
 * @property {Function} remove (trackId: number) => Promise
 * @property {Function} clear  () => Promise                            整仓清空
 * @property {Function} usage  () => {count: number, totalBytes: number} 索引口径
 * @property {Function} reconcile (presentIds: Set<number>) => number
 *                             对账: 字节真在场的曲目号集合之外的索引条目
 *                             出账 (系统清了字节, 索引还当都在 = 谎报 +
 *                             播到那首整首走流量重下); 返回出掉几条
 * @property {Function} setBudget (bytes: number) => Promise
 *                             收紧预算, 超了的当场清最旧 (系统实际给的
 *                             存储比默认小时收着用, 留着也是被先清)
 */

/**
 * 建自动缓存管理器 (状态在实例里; 同一页面只建一个)。
 * @param {AutoCacheAdapters} adapters
 * @param {{maxBytes?: number}} [options] 缓存预算 (字节, 默认 2GB)
 * @returns {AutoCacheManager}
 */
function createAutoCache(adapters, options) {
  let maxBytes = (options && options.maxBytes) || 2 * 1024 * 1024 * 1024;

  // 缓存键 = 音频流光杆地址 (与手动下载同款键形, 但住各自的缓存仓)
  const streamURL = (trackId) => `/music/media/stream/${trackId}`;

  /** 索引读出来先洗一遍 (坏行丢弃), 不排序 —— LRU 自己按时刻排。 */
  function indexEntries() {
    const entries = adapters.readIndex();
    return (Array.isArray(entries) ? entries : [])
      .filter((entry) => entry && Number.isFinite(entry.track_id)
        && Number.isFinite(entry.bytes));
  }

  function totalBytes(entries) {
    return entries.reduce((sum, entry) => sum + entry.bytes, 0);
  }

  function has(trackId) {
    return indexEntries().some((entry) => entry.track_id === trackId);
  }

  async function blob(trackId) {
    if (!has(trackId)) return null;
    const cached = await adapters.cacheRead(streamURL(trackId));
    if (!cached) {   // 索引说有、字节没了 (系统清存储): 自愈出索引
      adapters.writeIndex(indexEntries().filter(
        (entry) => entry.track_id !== trackId));
      return null;
    }
    // 读即续命 (LRU): 命中一次, 这首往后排
    adapters.writeIndex(indexEntries().map((entry) => entry.track_id === trackId
      ? { ...entry, cached_at: adapters.now() } : entry));
    return cached;
  }

  /** 存一首: 幂等 (重存 = 重写时刻), 挤位只清最久没听的, 新存的不许被自己挤掉。 */
  async function put(trackId, blobBody) {
    if (!Number.isFinite(trackId) || !blobBody || !(blobBody.size > 0)) return false;
    if (blobBody.size > maxBytes) return false;   // 一首就超预算: 不硬塞 (塞了 = 清光别人)
    const entries = indexEntries().filter((entry) => entry.track_id !== trackId);
    entries.push({ track_id: trackId, bytes: blobBody.size,
                   cached_at: adapters.now() });
    entries.sort((left, right) => (left.cached_at || 0) - (right.cached_at || 0));
    while (totalBytes(entries) > maxBytes && entries.length > 1) {
      const evicted = entries.shift();   // 最旧的让位
      await adapters.cacheDelete(streamURL(evicted.track_id));
    }
    await adapters.cachePut(streamURL(trackId), blobBody,
      blobBody.type || "application/octet-stream");
    adapters.writeIndex(entries);
    return true;
  }

  async function remove(trackId) {
    await adapters.cacheDelete(streamURL(trackId));
    adapters.writeIndex(indexEntries().filter((entry) => entry.track_id !== trackId));
  }

  async function clear() {
    for (const entry of indexEntries()) {
      await adapters.cacheDelete(streamURL(entry.track_id));
    }
    adapters.writeIndex([]);
  }

  function usage() {
    const entries = indexEntries();
    return { count: entries.length, totalBytes: totalBytes(entries) };
  }

  /** 对账 (1.8.101): presentIds = keys() 现场里字节真在的曲目号。索引里
      不在场的 = 系统已清掉字节的影子账 —— 出账后 usage 不再谎报容量,
      播放/预取也不会先信索引、到换源那步才发现没了 (整首走流量重下)。
      只动索引不删字节 (能被对掉的条目本就没有字节; 对账途中新落盘的
      字节也不误伤)。 */
  function reconcile(presentIds) {
    const entries = indexEntries();
    const kept = entries.filter((entry) => presentIds.has(entry.track_id));
    if (kept.length !== entries.length) adapters.writeIndex(kept);
    return entries.length - kept.length;
  }

  /** 预算收紧 (1.8.101): 系统实际给的存储小了就收着用, 超新预算的当场
      清最旧 —— 与其压着等系统清 (它清完索引还不知道, 白走流量重下),
      不如自己按 LRU 让位, 留下的都真在。 */
  async function setBudget(bytes) {
    maxBytes = Math.max(0, Number(bytes) || 0);
    const entries = indexEntries();
    while (totalBytes(entries) > maxBytes && entries.length > 0) {
      await adapters.cacheDelete(streamURL(entries.shift().track_id));
    }
    adapters.writeIndex(entries);
  }

  return { has, blob, put, remove, clear, usage, reconcile, setBudget };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { createAutoCache };
}
