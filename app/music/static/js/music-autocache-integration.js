// music-autocache-integration — My Music 自动缓存接线 (1.8.77): 浏览器适配器
// + 实例 + 预取落盘入口。门与手动下载同一道 (downloadsEnabled: HTTPS +
// Cache API) —— 明文环境整个功能收起。预取字节顺手进这仓 (autoCacheStash),
// 播放换源优先本地直读 (music-player-sources 的 localBlobFor), 不再走网络。
// 1.8.98 换代清仓: 服务端修过的歌 (音频文件换了新字节), 手机里这仓的旧
// 字节会一直压着不放 (没有逐首清除的口) —— 仓一代一跳, 旧代整仓清掉,
// 索引自愈 (autocache.blob 字节没了自动出账), 听过自动回填; 手动下载仓
// (music-downloads-v1) 不受牵连。
// 1.8.101 存储保卫 (实报「放着已缓存的歌, 蜂窝流量爆走」): 手机系统存储
// 吃紧会悄悄清 Cache API (没申请 persist 的源随便清, 一个小时内就能清掉
// 刚听过的歌), 索引还在 → 播到那首整首重新走流量。三道防线: ① 申请
// persist; ② 打开/回到应用就对账 (两仓索引里在、字节没了的影子账当场
// 出清 —— 统计行不再谎报「都缓存好了」); ③ 预算跟系统实际给的存储走。
// 2026-09-29 v2→v3 再换代: 服务器重修了 Angels & Demons 整专辑 (下载源
// 头顶包的 14-bit 噪声流, 九曲已原位换正版 FLAC) —— v2 仓里听过旧噪声
// 字节的手机照 1.8.98 的路子清仓换血; 手动下载仓仍旧不牵连 (那首若是
// 手动下载的, 得在 UI 里删了重下)。
// 1.8.122 缓存真查 (用户点名「Safari 会随机清空缓存, 要检查缓存里到底
// 有没有这首歌」): 对账触发面从「开局/回前台」两口扩到 bfcache 恢复
// (pageshow —— Safari 切标签回来常走这条, 未必过 visibilitychange) 和
// 路由重铺 (reconcileLocalAudioStoresSoon, 15s 节流 —— Safari 清仓不
// 一定挑后台, 正翻着列表也能被清); 顺手把写死的仓名换 DOWNLOAD_CACHE
// 常量。播放入口的谎报出账在 music-player-sources 的 localBlobFor。
"use strict";
/* global createAutoCache, downloads, downloadsEnabled, DOWNLOAD_CACHE */
/* exported autoCache, autoCacheEnabled, autoCachePersisted, autoCacheStash,
            reconcileLocalAudioStoresSoon */

// 同一道门: 没有下载能力 (明文 HTTP / 无 Cache API) 就没有自动缓存
const autoCacheEnabled = downloadsEnabled;

const AUTO_CACHE = "music-autocache-v3";
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

// ------------------------------------------------------------ 1.8.101 存储保卫

let autoCachePersisted = false;   // persist 批没批 (没批 = 系统可能随时清)

/** 申请固定存储 (整个源生效, 手动下载也受益): 没批过的源随使用时长/
    加桌面有机会翻盘, 每次回到应用再试一把。 */
function requestPersist() {
  if (navigator.storage && navigator.storage.persist) {
    navigator.storage.persist().then((granted) => {
      autoCachePersisted = granted;
    }).catch(() => {});
  }
}

/** 一个仓里字节真在场的曲目号 (keys() 只翻目录不读字节, 便宜)。 */
async function presentTrackIds(storeName) {
  const present = new Set();
  const cache = await caches.open(storeName);
  for (const key of await cache.keys()) {
    const match = /\/music\/media\/stream\/(\d+)$/.exec(
      new URL(key.url).pathname);
    if (match) present.add(Number(match[1]));
  }
  return present;
}

/** 两仓对账: 自动缓存走 reconcile, 手动下载走 removeDownload (同款键形,
    同款病 —— 字节没了账还在, 已下载页谎报 + 播到那首整首走流量重下)。
    下载中的 (有 state) 不碰: 字节还没落完。 */
let lastReconcileAt = 0;   // 对账节流表: 路由重铺也来敲, 连续导航不白翻目录

async function reconcileLocalAudioStores() {
  lastReconcileAt = Date.now();
  try {
    autoCache.reconcile(await presentTrackIds(AUTO_CACHE));
    if (typeof downloads !== "undefined" && downloads) {
      const present = await presentTrackIds(DOWNLOAD_CACHE);
      for (const entry of downloads.entries()) {
        if (!entry.state && !present.has(entry.track_id)) {
          await downloads.removeDownload(entry.track_id);
        }
      }
    }
  } catch (_error) { /* 这趟对不上就先不对: 播放路径自己会自愈 */ }
}

/** 路由重铺触发的节流对账 (1.8.122): Safari 清仓不一定挑后台, 正翻着
    列表也能被清 —— 每次重铺顺手验一遍真缓存, 已下载标记当场翻正;
    keys() 只翻目录不读字节, 但连续导航不该白翻, 15 秒内只敲一次
    (开局/回前台/bfcache 恢复另走直达)。 */
function reconcileLocalAudioStoresSoon() {
  if (Date.now() - lastReconcileAt < 15000) return;
  reconcileLocalAudioStores();
}

/** 预算跟系统实际给的存储走: quota 减半给自动缓存 (另一半留给手动下载/
    壳/封面), 最低 128MB; 估不出维持默认 2GB。收紧时超预算的清最旧
    (setBudget 自己收), 不压着等系统清 —— 它清完索引还不知道。 */
function clampBudgetToQuota() {
  if (!(navigator.storage && navigator.storage.estimate)) return;
  navigator.storage.estimate().then((estimate) => {
    if (estimate && estimate.quota) {
      autoCache.setBudget(Math.max(128 * 1024 * 1024,
        Math.min(AUTO_CACHE_MAX_BYTES, Math.floor(estimate.quota / 2))));
    }
  }).catch(() => {});
}

if (autoCacheEnabled && autoCache && window.caches) {
  requestPersist();
  reconcileLocalAudioStores();   // 异步对账, 不挡起播
  clampBudgetToQuota();
  // 回到应用再对一遍 (清场多发生在后台/锁屏期间), 顺手重试 persist
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      requestPersist();
      reconcileLocalAudioStores();
      clampBudgetToQuota();
    }
  });
  // bfcache 恢复 (1.8.122): Safari 切标签/回 app 常走 pageshow, 未必过
  // 上面的 visibilitychange —— 两口都守; 首次加载那下 (persisted=false)
  // 开局已对过, 不重复
  window.addEventListener("pageshow", (event) => {
    if (!event.persisted) return;
    requestPersist();
    reconcileLocalAudioStores();
    clampBudgetToQuota();
  });
}
