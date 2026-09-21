// sw.js — My Music 的 Service Worker (scope /music):
//  - 曲目音频流: 已下载的从 Cache API 直接回 (拖进度条的 Range 请求切 206),
//    没下载的原样走网络;
//  - 封面图: 缓存优先 —— 后端虽已发长缓存头, iOS 的 HTTP 缓存容易被系统
//    整体清掉, 50k 曲库一刷列表就是几百张图全回源; Cache API 里存一份,
//    系统清不动 (配合 storage.persist), 只在没缓存过时才走网络;
//  - 列表数据 (/music/api/ 的 GET, search 除外): 网络优先, 顺路存档 ——
//    断网时回上次拉到的 (1.8.4 用户点名「断网播放列表都打不开」:
//    壳和封面本来就缓存, 数据也缓一份, 联网打开过的页离线都能翻;
//    401/403 = 换人了, 整档清掉免得串账号);
//  - 应用壳 (页面 + 静态资源): 网络优先, 顺路存进缓存 —— 断网时页面也打得开,
//    已下载的歌照播 (已下载栏读的是本机索引, 不走接口);
//  - activate 时清掉旧版壳/数据缓存 + 接管已打开的页面 (clients.claim,
//    不用等重载)。
// 下载动作本身是页面脚本直连 Cache API, 这里只管离线时把缓存喂给 <audio>。
// 注意: 只在安全上下文 (HTTPS / localhost) 能注册, 明文 HTTP 下不存在。
"use strict";

const DOWNLOAD_CACHE = "music-downloads-v1";
// 壳缓存 v56 (2026-09-21 1.8.46 十改三轮: 层根滚动器外铺接点条罩住收
// 拢簇 —— iOS 惯性里点按整个吞给滚动器, 页头监听/touch-action 全没
// 用, 滚动器外才有原生响应; 惯性里点 播放/… 一下就灵);
// v55: 二轮: 补发上提 document·双通道; v54: 一轮按视觉位置认键补发;
// v53: 补程只管页头收放中间; v52: 八改: 被吞点按补发; v51: 停稳自动
// 补程; v50: 六改: 键衬底 20px 软边; v49: 五改: 纱钉收拢簇左缘, 150);
// v48: 四改: 开 … 后五颗键等距 (首键让 8px); 飞行不掉帧 (GPU 层 +
// 起飞立即显形不吃 250ms 淡入);
// v47: 1.8.46 三改: 收拢的键错峰走弧线飞进 … —— 途中
// 两两不叠 (逐帧算过: 任意时刻轴距 ≥ 44px > 键宽 40); 遮罩罩满整个
// 按钮区域 —— 播放键整高衬底 + 额外键箱整高衬底, 开 … 时上下露边不
// 漏字; 修了飞行期额外键箱被最小内容宽撑开、纱跟着跑偏的根;
// v46: 1.8.46 二改: 收拢的键不再缩小 —— 全尺寸飞到 … 键上互相叠成一摞,
// 末段化进 … 里;
// v45: 1.8.46 收缩顶栏换岗改路径平移 —— 播放键从操作行一路平移进槽位,
// 其余四颗收拢进 … 键, 不再闪现; 遮罩拉宽越靠左越透;
// v44: 1.8.45 收缩顶栏改单行 —— 播放 + … 两颗在封面同行右靠, … 点开
// 随机/下载/分享/删除 顶替它, 挤到的标题用阴影渐隐;
// v43: 1.8.44 蓝牙车机封面实验 —— 锁屏封面先取成 blob 再重设元数据,
// 车机的 AVRCP 通道才有机会拿到图;
// v42: 1.8.43 视口体检红框弹窗撤了, 打点改静默回传;
// v41: 1.8.42 收缩顶栏的标题/副标题左对齐;
// v40: 1.8.41 双指缩放全禁 + 分享页列表行序号换歌曲封面 / 1.8.40 收缩顶栏
// 两行布局·副标题并进上行·短列表补行程·横向晃动修复 / 1.8.39 桌面键鼠
// 适配 —— 换版本号让 activate 清旧账)
const SHELL_CACHE = "music-shell-v56";
const ARTWORK_CACHE = "music-artwork-v1";
// 列表数据档 (1.8.4): /music/api/ 的 GET 全缓存 (search 除外 —— 词组合
// 无限多, 缓存不值), 网络优先断网回档
const DATA_CACHE = "music-data-v1";
const TRACK_URL_PATTERN = /\/music\/media\/stream\/\d+$/;
// 封面族: 专辑/艺人/单曲封面 + 播放列表自定义封面
// (URL 全带 ?v= 版本号, 换图即换址 —— 缓存键跟着换, 不会读到旧图)
const ARTWORK_PATTERN
  = /^\/music\/media\/(?:albums|artists|tracks)\/\d+\/artwork$|^\/music\/media\/playlists\/\d+\/cover$/;
const DATA_PATTERN = /^\/music\/api\/(?!search\b)/;
const SHELL_PATHS = new Set(["/music", "/music/", "/music/login", "/music/changelog"]);

function isShellPath(path) {
  return SHELL_PATHS.has(path) || path.startsWith("/music/static/");
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const path = new URL(request.url).pathname;
  if (TRACK_URL_PATTERN.test(path)) {
    event.respondWith(serveTrack(request));
  } else if (ARTWORK_PATTERN.test(path)) {
    event.respondWith(serveArtwork(request));
  } else if (DATA_PATTERN.test(path)) {
    event.respondWith(serveApiData(request));
  } else if (isShellPath(path)) {
    event.respondWith(serveShell(request));
  }
});

/** 壳资源: 在线用网络的 (顺手把成功的存缓存, 下次断网有得回), 断网回缓存。 */
async function serveShell(request) {
  const cache = await caches.open(SHELL_CACHE);
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch (_error) {
    const cached = await cache.match(request);
    if (cached) return cached;
    return new Response("离线且尚未缓存过此页面, 联网打开一次后可离线使用",
      { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } });
  }
}

/** 缓存里有就回缓存 (Range 切 206, iOS Safari 拖进度条需要), 没有走网络。 */
async function serveTrack(request) {
  const cache = await caches.open(DOWNLOAD_CACHE);
  const cached = await cache.match(request.url);
  if (!cached) return fetch(request);
  const rangeHeader = request.headers.get("range");
  if (!rangeHeader) return cached;
  const slice = rangeSlice(await cached.blob(), rangeHeader);
  if (!slice) return cached;              // 解析不出范围: 给全量兜底
  return new Response(slice.body, {
    status: 206,
    headers: {
      "Content-Type": cached.headers.get("Content-Type")
        || "application/octet-stream",
      "Content-Range": `bytes ${slice.start}-${slice.end}/${slice.total}`,
      "Content-Length": String(slice.end - slice.start + 1),
    },
  });
}

/** "bytes=start-end" → 全量 blob 的切片 (end 缺省 = 到尾; 越界钳到尾)。 */
function rangeSlice(blob, rangeHeader) {
  const match = /^bytes=(\d+)-(\d*)$/.exec(rangeHeader.trim());
  if (!match) return null;
  const start = Number(match[1]);
  if (start >= blob.size) return null;
  const end = match[2] ? Math.min(Number(match[2]), blob.size - 1)
    : blob.size - 1;
  return { start, end, total: blob.size, body: blob.slice(start, end + 1) };
}

/** 封面: 缓存优先 (URL 自带 ?v= 版本, 缓存里的内容永不换), 没缓存过才走
    网络并顺手存下。条数封顶防无限膨胀: 超了丢最早一批 (Cache API 没有
    LRU, keys() 顺序近似先来后到, 够用)。 */
async function serveArtwork(request) {
  const cache = await caches.open(ARTWORK_CACHE);
  const cached = await cache.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok) {
    await cache.put(request, response.clone());
    trimArtworkCache(cache);
  }
  return response;
}

async function trimArtworkCache(cache) {
  const keys = await cache.keys();
  if (keys.length <= 600) return;
  for (const key of keys.slice(0, keys.length - 400)) {
    await cache.delete(key);
  }
}

/** 列表数据: 网络优先 (在线永远拿新的), 断网回上次存档 —— 联网打开过的
    页 (播放列表/专辑/艺人/最近播放/统计…) 离线都能翻。401/403 = 登录态
    没了或换人了, 整档清掉免得串账号 (退出登录时页面也清一次)。 */
async function serveApiData(request) {
  const cache = await caches.open(DATA_CACHE);
  try {
    const response = await fetch(request);
    if (response.ok) {
      const type = response.headers.get("Content-Type") || "";
      if (type.includes("application/json")) {
        await cache.put(request, response.clone());
        trimDataCache(cache);
      }
    } else if (response.status === 401 || response.status === 403) {
      const keys = await cache.keys();
      for (const key of keys) await cache.delete(key);
    }
    return response;
  } catch (_error) {
    const cached = await cache.match(request);
    if (cached) return cached;
    return new Response(
      JSON.stringify({ detail: "离线中: 这个页面联网打开过一次就能离线看" }),
      { status: 503, headers: { "Content-Type": "application/json" } });
  }
}

/** 数据档条数封顶 (分页 URL 各占一条, 50k 曲库翻久了会攒出几十条):
    超了丢最早一批 (Cache API 没有 LRU, keys() 顺序近似先来后到)。 */
async function trimDataCache(cache) {
  const keys = await cache.keys();
  if (keys.length <= 120) return;
  for (const key of keys.slice(0, keys.length - 80)) {
    await cache.delete(key);
  }
}

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    // 壳/数据缓存换版本号时清旧账; 下载缓存 (DOWNLOAD_CACHE) 是用户数据, 不动
    const names = await caches.keys();
    for (const name of names) {
      if (name.startsWith("music-shell-") && name !== SHELL_CACHE) {
        await caches.delete(name);
      }
      if (name.startsWith("music-artwork-") && name !== ARTWORK_CACHE) {
        await caches.delete(name);
      }
      if (name.startsWith("music-data-") && name !== DATA_CACHE) {
        await caches.delete(name);
      }
    }
    await self.clients.claim();   // 不等刷新, 已开的页面立刻归我管
  })());
});
