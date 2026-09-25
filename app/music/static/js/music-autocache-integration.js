// music-autocache-integration — My Music 自动缓存接线 (1.8.77): 浏览器适配器
// + 实例 + 预取落盘入口。门与手动下载同一道 (downloadsEnabled: HTTPS +
// Cache API) —— 明文环境整个功能收起。预取字节顺手进这仓 (autoCacheStash),
// 播放换源优先本地直读 (music-player-sources 的 localBlobFor), 不再走网络。
// 1.8.98 换代清仓: 服务端修过的歌 (音频文件换了新字节), 手机里这仓的旧
// 字节会一直压着不放 (没有逐首清除的口) —— 仓一代一跳, 旧代整仓清掉,
// 索引自愈 (autocache.blob 字节没了自动出账), 听过自动回填; 手动下载仓
// (music-downloads-v1) 不受牵连。
"use strict";
/* global createAutoCache, downloadsEnabled */
/* exported autoCache, autoCacheEnabled, autoCacheStash */

// 同一道门: 没有下载能力 (明文 HTTP / 无 Cache API) 就没有自动缓存
const autoCacheEnabled = downloadsEnabled;

const AUTO_CACHE = "music-autocache-v2";
const AUTO_INDEX_KEY = "music-autocache";
const AUTO_CACHE_MAX_BYTES = 2 * 1024 * 1024 * 1024;   // 2GB 封顶, LRU 自动让位

// 旧代整仓清掉 (一次性的活: 清完 caches.keys() 里再无旧名, 空转无害)
if (window.caches) {
  caches.keys().then((names) => {
    for (const name of names) {
      if (name.startsWith("music-autocache-") && name !== AUTO_CACHE) {
        caches.delete(name);
      }
    }
  }).catch(() => {});
}

function browserAutoCacheAdapters() {
  return {
    readIndex() {
      try {
        return JSON.parse(localStorage.getItem(AUTO_INDEX_KEY) || "[]");
      } catch (_error) { return []; }
    },
    writeIndex(entries) {
      try {
        localStorage.setItem(AUTO_INDEX_KEY, JSON.stringify(entries));
      } catch (_error) { /* 存满了: 索引丢了这套缓存就当不存在 */ }
    },
    async cachePut(url, body, contentType) {
      const cache = await caches.open(AUTO_CACHE);
      await cache.put(url, new Response(body, {
        headers: { "Content-Type": contentType },
      }));
    },
    async cacheRead(url) {              // 换源直读: 不经 SW (同 1.8.59 手动下载)
      const cache = await caches.open(AUTO_CACHE);
      const response = await cache.match(url);
      return response ? await response.blob() : null;
    },
    async cacheDelete(url) {
      const cache = await caches.open(AUTO_CACHE);
      await cache.delete(url);
    },
    now() { return Date.now() / 1000; },
  };
}

const autoCache = autoCacheEnabled
  ? createAutoCache(browserAutoCacheAdapters(),
      { maxBytes: AUTO_CACHE_MAX_BYTES })
  : null;

/** 预取字节顺手落盘 (fire-and-forget): 失败/没实例都不挡预取主路。 */
function autoCacheStash(trackId, blob) {
  if (!autoCache) return;
  autoCache.put(trackId, blob).catch(() => {});
}
