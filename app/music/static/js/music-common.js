// music-common.js — My Music 页面公共小件 (DOM 查询/转义/请求/提示/资源 URL)。
// 纯逻辑在 lyrics-parser.js / player-queue.js;
// 浏览与播放两个页面脚本共用这里。
"use strict";
/* exported escapeHTML, fetchJSON, toast, albumArtworkURL, artistArtworkURL,
   trackArtworkURL, playlistCoverURL, PLACEHOLDER_ARTWORK,
   describeDuration,
   ICON_PLAY, ICON_PAUSE, ICON_BARS, ICON_DOWNLOAD, ICON_LYRICS,
   ICON_PLAY_BIG, ICON_PAUSE_BIG, ICON_CANCEL,
   ICON_ACTION_PLAY, ICON_ACTION_SHUFFLE, ICON_ACTION_TRASH,
   ICON_ACTION_IMAGE, ICON_ACTION_SHARE, ICON_ACTION_MORE, ICON_REPEAT,
   ICON_ACTION_REFRESH, ICON_REPEAT_ONE, ICON_SHUFFLE */   // 供 music-player.js / music.js 引用

function $(selector) {
  return document.querySelector(selector);
}

function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g,
    (char) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;",
                '"': "&quot;", "'": "&#39;"}[char]));
}

/** fetch JSON; 非 2xx 抛错 (调用方 catch 后 toast)。 */
async function fetchJSON(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      detail = (await response.json()).detail || detail;
    } catch (_error) { /* 保持 HTTP 状态文案 */ }
    // 挂上状态码: 有的调用方要按码分叉 (如加歌 409 = 已在列表里, 不算失败)
    throw Object.assign(new Error(detail), { status: response.status });
  }
  return response.json();
}

let toastTimer = 0;
/** 浮层提示 (2.4s 自动消失; 连续调用只保最后一条)。1.8.92 (用户点名
    「放在标题和封面之间」): 播放页开着时气泡吊在封面底边与标题行顶边的
    接缝上 —— 1.8.91 钉在标题行正中会盖住歌名; 这里现量两边取中点,
    播放页没开照旧沉底 (底部船坞上方)。 */
function toast(message) {
  const element = $("#toast");
  const player = $("#full-player.open");
  let seam = null;
  if (player) {
    const art = player.querySelector("#fp-art-wrap");
    const meta = player.querySelector(".fp-meta");
    seam = (art.getBoundingClientRect().bottom
            + meta.getBoundingClientRect().top) / 2;
  }
  element.classList.toggle("in-player", seam !== null);
  element.style.top = seam === null ? "" : `${seam}px`;
  element.textContent = message;
  element.hidden = false;
  element.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    element.classList.remove("show");
    setTimeout(() => { element.hidden = true; }, 300);
  }, 2400);
}

/** 专辑封面 URL (?v= 版本号跟文件内容走: 换过文件重扫后地址就变,
    手机缓存的旧封面才会跟着换; added_at 是入库时刻, 原地换文件不动)。 */
function albumArtworkURL(album) {
  const version = album.artwork_version || album.added_at || 0;
  return `/music/media/albums/${album.album_id}/artwork?v=${version}`;
}

/** 艺人海报 URL (曲库 poster.* 透传; ?v= 是海报文件 mtime —— 换过海报
    重扫后地址跟着变, 长缓存/离线封面缓存才读得到新头像, 不会永远是旧的)。 */
function artistArtworkURL(artist) {
  return `/music/media/artists/${artist.artist_id}/artwork?v=${artist.poster_version || 0}`;
}

/** 单曲自己的内嵌封面 URL (播放列表里每行用各首歌的; ?v= 是文件 mtime,
    改过标签重扫后自动换图)。 */
function trackArtworkURL(track) {
  return `/music/media/tracks/${track.track_id}/artwork?v=${track.mtime || 0}`;
}

/** 播放列表自定义封面 URL (0 = 没传过, 返回空串); ?v= 是版本号,
    换图即换址, 配合 immutable 长缓存。 */
function playlistCoverURL(playlist) {
  return playlist.cover_version
    ? `/music/media/playlists/${playlist.playlist_id}/cover?v=${playlist.cover_version}`
    : "";
}

/** 占位封面 (无封面/加载失败时的纯色音符, 免 404 图标闪)。 */
const PLACEHOLDER_ARTWORK =
  'data:image/svg+xml;utf8,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    + '<rect width="64" height="64" rx="8" fill="#2c2c2e"/>'
    + '<path d="M40 14v24.5a7.5 7.5 0 1 1-3-6V22l-12 3v17.5a7.5 7.5 0 1 1-3-6V19z"'
    + ' fill="#5a5a5e"/></svg>');

/** 专辑总时长文案: "48 分钟" / "1.2 小时" / "3 首 · 12 分钟"。 */
function describeDuration(totalSeconds, trackCount) {
  const minutes = Math.round(totalSeconds / 60);
  const durationText = minutes >= 60
    ? `${(minutes / 60).toFixed(1)} 小时` : `${minutes} 分钟`;
  return trackCount ? `${trackCount} 首 · ${durationText}` : durationText;
}

// ---------- 图标 (播放器与列表共用) ----------
// 三角一律包围盒中心对准 24 格的正中 (x=12): 图标光心 = 按键中心,
// 播放↔暂停切换不左右跳位 (2026-09-14 前的三角右偏 2 格, 一切换肉眼可见地歪)。
const ICON_PLAY = '<svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true"><path d="M6.583 17.075L6.583 6.925Q6.583 5.5 7.805 6.233L16.176 11.256Q17.416 12 16.176 12.744L7.805 17.767Q6.583 18.5 6.583 17.075z" fill="currentColor"/></svg>';
const ICON_PAUSE = '<svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true"><path d="M14.857 5.571q0.887 0 1.515 0.628t0.628 1.515l0 8.571q0 0.887-0.628 1.515t-1.515 0.628t-1.515-0.628t-0.628-1.515l0-8.571q0-0.887 0.628-1.515t1.515-0.628zM9.143 5.571q0.887 0 1.515 0.628t0.628 1.515l0 8.571q0 0.887-0.628 1.515t-1.515 0.628t-1.515-0.628t-0.628-1.515l0-8.571q0-0.887 0.628-1.515t1.515-0.628z" fill="currentColor"/></svg>';
// 全屏播放页的播放/暂停: 裸白字形站在传输键上 (三键一般大, 播放键
// 不再大一号 —— 用户嫌中间的播放键过于巨大; 字形 36→32 只略大于上下曲)
const ICON_PLAY_BIG = '<svg viewBox="0 0 24 24" width="32" height="32" aria-hidden="true"><path d="M5.029 3.127L19 10.889Q21 12 19 13.111L5.029 20.873Q3 22 3 19.679L3 4.321Q3 2 5.029 3.127z" fill="currentColor"/></svg>';
const ICON_PAUSE_BIG = '<svg viewBox="0 0 24 24" width="32" height="32" aria-hidden="true"><path d="M4 4.5q0-2.5 2.5-2.5t2.5 2.5v15q0 2.5-2.5 2.5t-2.5-2.5v-15zM15 4.5q0-2.5 2.5-2.5t2.5 2.5v15q0 2.5-2.5 2.5t-2.5-2.5v-15z" fill="currentColor"/></svg>';
const ICON_BARS = '<span class="bars" aria-hidden="true"><i></i><i></i><i></i></span>';

// ❝ 引号 glyph (与全屏页歌词键同款): 曲目行「有词」的标记。
// 17×17 与下载标同大, 行内同一高度 (小了看着像上标)。
const ICON_LYRICS = '<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true"><path d="M11.049 7.801L11.049 13.662Q11.406 15.378 10.242 16.689Q9.078 18 7.332 17.848Q7.244 17.9 7.146 17.87Q7.049 17.84 7.005 17.748Q6.9 17.71 6.858 17.608Q6.815 17.505 6.863 17.404L6.863 15.73Q6.83 15.576 6.931 15.454Q7.032 15.333 7.189 15.336Q7.857 15.352 8.276 14.832Q8.695 14.311 8.537 13.662L8.537 12.825L6.026 12.825Q5.286 12.952 4.755 12.421Q4.224 11.89 4.351 11.15L4.351 7.801Q4.224 7.062 4.755 6.531Q5.286 6 6.026 6.127L9.375 6.127Q10.114 6 10.645 6.531Q11.176 7.062 11.049 7.801L11.049 7.801M17.747 6.127L14.398 6.127Q13.658 6 13.127 6.531Q12.597 7.062 12.723 7.801L12.723 11.15Q12.597 11.89 13.127 12.421Q13.658 12.952 14.398 12.825L16.91 12.825L16.91 13.662Q17.068 14.311 16.649 14.832Q16.23 15.352 15.562 15.336Q15.399 15.335 15.298 15.462Q15.197 15.589 15.235 15.747L15.235 17.421Q15.194 17.517 15.236 17.611Q15.279 17.706 15.377 17.739Q15.421 17.832 15.518 17.862Q15.616 17.892 15.704 17.84Q17.448 17.992 18.612 16.684Q19.776 15.376 19.421 13.662L19.421 7.801Q19.548 7.062 19.017 6.531Q18.487 6 17.747 6.127L17.747 6.127" fill="currentColor"/></svg>';
// 下载 (曲目行右侧; 已下载时 music.js 换成勾; 正在下时换 ICON_CANCEL)
const ICON_CANCEL = '<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true"><path d="M6.5 6.5 17.5 17.5M17.5 6.5 6.5 17.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>';
const ICON_DOWNLOAD = '<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true"><path d="M12 3v11M7.5 9.5 12 14l4.5-4.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M5 17.5v1.5a1.5 1.5 0 0 0 1.5 1.5h11a1.5 1.5 0 0 0 1.5-1.5v-1.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
const ICON_ACTION_PLAY = '<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path d="M6.583 17.075L6.583 6.925Q6.583 5.5 7.805 6.233L16.176 11.256Q17.416 12 16.176 12.744L7.805 17.767Q6.583 18.5 6.583 17.075z" fill="currentColor"/></svg>';
// 随机播放 (1.8.111 换 iconfont 交叉双箭头, 用户点名): 实底填充画法, 与分享
// 图标同一家法; 大半径浅弧 (r=1116) 预换成 q 二次曲线 —— icons 测试对浅弧按
// 整椭圆做虚标记会把包围盒撑大一倍, 换 q 后测试与渲染口径一致
const ICON_ACTION_SHUFFLE = '<svg viewBox="-2.65 -18.28 1036.5 1036.5" width="15" height="15" aria-hidden="true"><path d="M779.48 608.12a24.27 24.27 0 0 1 14.32 4.66l152.33 111.27a24.27 24.27 0 0 1 -0.12 39.32l-152.36 109.69a24.27 24.27 0 0 1 -38.47 -19.71v-60.85c-94.27 -0.9 -151.78 -28.33 -203.33 -92.26c19.13 -27.53 37.09 -58.06 54.39 -91.65c41 63.96 78.38 86.12 148.94 86.8V632.39a24.27 24.27 0 0 1 24.27 -24.27zM779.24 122.28a24.27 24.27 0 0 1 14.18 4.56l152.53 109.57a24.27 24.27 0 0 1 0.17 39.32l-152.55 111.53a24.27 24.27 0 0 1 -38.59 -19.61v-62.91c-98.52 0.9 -135.15 43.04 -199.54 183.6c-7.23 15.85 -11.09 24.27 -14.68 32.04c-86.41 186.78 -174.81 269.21 -368.12 272.19H75.09v-97.58h96.8c146.95 -2.26 207.97 -59.15 280.35 -215.59c3.5 -7.57 7.23 -15.78 14.52 -31.7c78.67 -171.7 139.81 -239.16 288.24 -240.54V146.55a24.27 24.27 0 0 1 24.27 -24.27zM172.67 207.16c116.56 1.8 194.98 32.48 257.82 97.53q-26.34 45.59 -48.28 93.45c-50.85 -65.37 -110.93 -91.87 -210.3 -93.43H75.09v-97.58h97.55z" fill="currentColor"/></svg>';
const ICON_ACTION_TRASH = '<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path d="M4 7h16M9.5 7V4.5h5V7M6.5 7l.7 12.5h9.6l.7-12.5M10 10.5v6M14 10.5v6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
// 更多操作 … (1.8.45 收缩顶栏的动作条): 三点横排, 点开收着的额外键
const ICON_ACTION_MORE = '<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><g fill="currentColor"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></g></svg>';
const ICON_ACTION_IMAGE = '<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path d="M4.5 5.5h15v13h-15zM4.5 15l4.5-4 4 3.5 3-2.5 4 3.5M9 9.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
// 刷新 (艺人页「刷新元数据」): 环形箭头, 与下载标同一套描边画法
const ICON_ACTION_REFRESH = '<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true"><path d="M23 4v6h-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
// 分享图标 (1.8.25 换 iconfont「分享」搜索第 8 个, 用户点名): 三节点互连的
// 共享网络画法 (iconfont id 809967, fill 填充), 曲目菜单那颗同款
// (music.html 内联 18px)。1.8.23 的 iOS 共享样式 (方框 + 顶边缺口箭头) 随之退役
const ICON_ACTION_SHARE = '<svg viewBox="0 0 1024 1024" width="15" height="15" aria-hidden="true"><path d="M769.714 589.547c-51.754 0-97.702 24.851-126.571 63.269L394.479 528.059c3.93-13.798 6.034-28.364 6.034-43.424 0-16.496-2.527-32.399-7.211-47.35l247.724-124.288c28.71 40.052 75.647 66.151 128.687 66.151 87.388 0 158.229-70.84 158.229-158.229 0-87.388-70.841-158.229-158.229-158.229-87.389 0-158.229 70.841-158.229 158.229 0 6.046 0.352 12.009 1.011 17.88L351.22 369.884c-28.371-26.943-66.723-43.479-108.938-43.479-87.388 0-158.229 70.84-158.229 158.229s70.84 158.229 158.229 158.229c43.752 0 83.354-17.758 111.997-46.459l258.676 129.779c-0.964 7.062-1.474 14.266-1.474 21.592 0 87.389 70.84 158.229 158.229 158.229s158.229-70.84 158.229-158.229C927.938 660.388 857.103 589.547 769.714 589.547L769.714 589.547z" fill="currentColor"/></svg>';
// 循环三态 (1.8.111 换 iconfont 实底新画法, 用户点名): 列表/单曲共用同一枚
// 双环和同一视框 (用户给的两张循环图环体各是各的画法, 两态切换会跳形)。
// 1.8.115 徽章挪 logo 右上角 (用户点名): 圆片 (908,193) r193 整个盖住右上
// 折角箭头旗, 顶杆端顺势流入圆片 (iOS 角标款); 旗墨由一枚反向旗子副本
// 抵消, 圆片与环同绕向补实底, 「1」反向镂空见底色。环 d 逐字节不动。
// 1.8.117 整枚徽章按用户参照 logo (iconfont repeat-one) 等比重定尺寸
// (1.8.116 只放数字不放圆片, 用户点名「还是很小」—— 症结在圆片本身小):
// 圆片 Ø 放大 65% 到占图宽 47.8%, 顶/右沿与环的极值齐平, 「1」高占圆片一半
const ICON_REPEAT = '<svg viewBox="-96.72 -154.37 1329.4 1329.4" width="24" height="24" aria-hidden="true"><path d="M73.44 667.21a44.45 44.45 0 0 1 -12.12 1.64c-20.72 0 -38.18 -13.89 -43.62 -32.86c-9.37 -32.57 -14.71 -69.64 -14.71 -107.94v-0.42c0 -107.44 41.81 -208.46 117.8 -284.45C193.18 170.41 293.39 125.38 404.12 125.38h423.25V44.7c0 -25.71 17.68 -35.37 39.37 -21.36l194.36 125.48c21.64 14.01 21.41 36.56 -0.51 50.11L867.2 318.72c-21.92 13.61 -39.9 3.68 -39.9 -22.15V216.23h-422.04c-172.1 0.19 -311.55 139.75 -311.55 311.87c0 29.62 4.13 58.28 11.84 85.43c0.51 1.43 1.11 5.6 1.11 9.91a45.38 45.38 0 0 1 -32.91 43.63l-0.32 0.14zm1044.89 -282.16q14.66 52.96 14.63 107.91c0 107.4 -41.81 208.42 -117.8 284.42c-72.4 72.77 -172.6 117.8 -283.33 117.8H308.59v80.79c0 25.71 -17.68 35.37 -39.38 21.42l-194.3 -125.55c-21.64 -14.01 -21.47 -36.56 0.45 -50.11l193.45 -119.78c21.87 -13.62 39.83 -3.68 39.83 22.14v80.34h422.05c172.09 -0.18 311.54 -139.75 311.54 -311.87c0 -29.62 -4.12 -58.28 -11.84 -85.42c-0.36 -1.17 -0.88 -5.04 -0.88 -9.03a45.37 45.37 0 0 1 88.73 -13.38l0.09 0.32z" fill="currentColor"/></svg>';
const ICON_REPEAT_ONE = '<svg viewBox="-96.72 -154.37 1329.4 1329.4" width="24" height="24" aria-hidden="true"><path d="M73.44 667.21a44.45 44.45 0 0 1 -12.12 1.64c-20.72 0 -38.18 -13.89 -43.62 -32.86c-9.37 -32.57 -14.71 -69.64 -14.71 -107.94v-0.42c0 -107.44 41.81 -208.46 117.8 -284.45C193.18 170.41 293.39 125.38 404.12 125.38h423.25V44.7c0 -25.71 17.68 -35.37 39.37 -21.36l194.36 125.48c21.64 14.01 21.41 36.56 -0.51 50.11L867.2 318.72c-21.92 13.61 -39.9 3.68 -39.9 -22.15V216.23h-422.04c-172.1 0.19 -311.55 139.75 -311.55 311.87c0 29.62 4.13 58.28 11.84 85.43c0.51 1.43 1.11 5.6 1.11 9.91a45.38 45.38 0 0 1 -32.91 43.63l-0.32 0.14zm1044.89 -282.16q14.66 52.96 14.63 107.91c0 107.4 -41.81 208.42 -117.8 284.42c-72.4 72.77 -172.6 117.8 -283.33 117.8H308.59v80.79c0 25.71 -17.68 35.37 -39.38 21.42l-194.3 -125.55c-21.64 -14.01 -21.47 -36.56 0.45 -50.11l193.45 -119.78c21.87 -13.62 39.83 -3.68 39.83 22.14v80.34h422.05c172.09 -0.18 311.54 -139.75 311.54 -311.87c0 -29.62 -4.12 -58.28 -11.84 -85.42c-0.36 -1.17 -0.88 -5.04 -0.88 -9.03a45.37 45.37 0 0 1 88.73 -13.38l0.09 0.32zM827.3 216.23L827.3 296.57C827.3 322.4 845.28 332.33 867.2 318.72L1060.59 198.93C1082.51 185.38 1082.74 162.83 1061.1 148.82L866.74 23.34C845.05 9.33 827.37 18.99 827.37 44.7L827.37 125.38zM815.09 15.45C991.36 15.45 1132.96 157.05 1132.96 333.32C1132.96 509.59 991.36 651.19 815.09 651.19C638.82 651.19 497.22 509.59 497.22 333.32C497.22 157.05 638.82 15.45 815.09 15.45zM872.86 503.82L872.86 185.95L826.63 185.95C815.07 200.41 797.73 211.96 780.39 223.53C763.05 235.08 745.72 243.74 728.38 246.63L728.38 310.2C763.05 298.64 789.07 284.2 812.18 263.97L812.18 503.82L872.86 503.82z" fill="currentColor"/></svg>';
// 随机循环态与随机播放键同一枚交叉箭头 (1.8.111 同批换装保持一致)
const ICON_SHUFFLE = '<svg viewBox="-2.65 -18.28 1036.5 1036.5" width="24" height="24" aria-hidden="true"><path d="M779.48 608.12a24.27 24.27 0 0 1 14.32 4.66l152.33 111.27a24.27 24.27 0 0 1 -0.12 39.32l-152.36 109.69a24.27 24.27 0 0 1 -38.47 -19.71v-60.85c-94.27 -0.9 -151.78 -28.33 -203.33 -92.26c19.13 -27.53 37.09 -58.06 54.39 -91.65c41 63.96 78.38 86.12 148.94 86.8V632.39a24.27 24.27 0 0 1 24.27 -24.27zM779.24 122.28a24.27 24.27 0 0 1 14.18 4.56l152.53 109.57a24.27 24.27 0 0 1 0.17 39.32l-152.55 111.53a24.27 24.27 0 0 1 -38.59 -19.61v-62.91c-98.52 0.9 -135.15 43.04 -199.54 183.6c-7.23 15.85 -11.09 24.27 -14.68 32.04c-86.41 186.78 -174.81 269.21 -368.12 272.19H75.09v-97.58h96.8c146.95 -2.26 207.97 -59.15 280.35 -215.59c3.5 -7.57 7.23 -15.78 14.52 -31.7c78.67 -171.7 139.81 -239.16 288.24 -240.54V146.55a24.27 24.27 0 0 1 24.27 -24.27zM172.67 207.16c116.56 1.8 194.98 32.48 257.82 97.53q-26.34 45.59 -48.28 93.45c-50.85 -65.37 -110.93 -91.87 -210.3 -93.43H75.09v-97.58h97.55z" fill="currentColor"/></svg>';
