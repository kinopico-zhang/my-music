// share-viewer-data — My Music 分享页数据与状态: uuid 换数据/失效态/卡片与清单渲染, 工具与封面兜底。
// 拆自 share.html 的内联 <script> (结构化重构, 跨模块引用走全局)。
// 1.8.130 (用户点名「按钮跟普通播放界面保持一致」) 队列整用应用的
// player-queue.js: 播放状态从 数组+下标 换成真正的 PlayQueue
// (tracks/order/position/shuffle/repeat), 三态循环键/待播队列/舞台邻居
// 都从它取数。$ / ICON_*_BIG 常量改由应用的 music-common.js 提供
// (本页不再自己抄一份), 本文件只留分享专属的。
"use strict";
/* exported BARS_SVG, artURL, audio, boot, currentTrack, esc, fmtTime,
            lyricIndex, lyrics, lyricsAutoUntil, lyricsCache, lyricsFollowPaused,
            lyricsLastScrollAt, playQueue, queueViewOpen, seeking, setArt,
            token, trackChangeListeners */

// 分享页逻辑: 拿 uuid 换数据 → 渲染 → 流地址播放; 失效 (410) 走错误态。
// 迷你条点文字区掀全屏播放页 (1.8.5 与 app 同款: 封面/标题行字幕引号/
// 传输三键/细进度条); 歌词解析借应用公开的 lyrics-parser.js (纯模块,
// 不带会话)。一切状态以 <audio> 的 play/pause 事件为准, 按钮只改 audio。

/* global $, createPlayQueue, updatePlayModeButton */
const esc = (value) => String(value).replace(/[&<>"']/g, (ch) => (
  {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[ch]));

const PATH_PARTS = location.pathname.split("/");   // ["", "music", "share", token]
const token = PATH_PARTS.length > 3 ? PATH_PARTS[3] : "";

const audio = $("#audio");
let playQueue = null;       // 可播曲目的 PlayQueue (player-queue.js 建, 只含 playable)
let currentTrack = null;    // 正在播的曲目 (舞台/歌词/锁屏元数据都看它)
let queueViewOpen = false;  // 待播队列视图开着 (与歌词视图互斥, 同住封面区)
const trackChangeListeners = [];   // 换曲回调 (3D 舞台在车上重铺三张卡)
let seeking = false;
let lyrics = null;         // 当前曲的 {synced, lines} | null (没歌词)
let lyricsCache = new Map();     // track_id → 解析结果 (null = 没歌词)
let lyricIndex = -1;       // 正在唱的行
let lyricsFollowPaused = false;  // 手动滚过: 暂停跟唱
let lyricsLastScrollAt = 0;
let lyricsAutoUntil = 0;   // 程序滚动宽限期 (这期间的 scroll 不算手动)

const BARS_SVG = '<svg class="bars paused" viewBox="0 0 14 14" aria-hidden="true">'
  + '<rect x="1" y="2" width="2.6" height="10" rx="1.3"/>'
  + '<rect x="5.7" y="2" width="2.6" height="10" rx="1.3"/>'
  + '<rect x="10.4" y="2" width="2.6" height="10" rx="1.3"/></svg>';

function fmtTime(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return "-:--";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

function fmtDateTime(epochSeconds) {
  const d = new Date(epochSeconds * 1000);
  const two = (n) => String(n).padStart(2, "0");
  return `${d.getMonth() + 1}月${d.getDate()}日 `
    + `${two(d.getHours())}:${two(d.getMinutes())}`;
}

// 封面: 这一首自己的 → 它的专辑的 → 渐变占位 (onerror 兜底)
function artURL(track) {
  if (track.has_artwork) {
    return `/music/share/${token}/artwork/track/${track.track_id}?v=${track.mtime}`;
  }
  return `/music/share/${token}/artwork/album/${track.album_id}`;
}

function setArt(el, url) {
  el.classList.remove("ph");
  el.textContent = "";
  const img = document.createElement("img");
  img.alt = "";
  img.decoding = "async";
  img.onerror = () => {
    el.classList.add("ph");
    el.textContent = "♪";
    img.remove();
  };
  img.src = url;
  el.appendChild(img);
}

function setPlaceholder(el) {
  el.classList.add("ph");
  el.textContent = "♪";
}

async function boot() {
  if (!token) return showError();
  let data = null;
  try {
    const resp = await fetch(`/music/share/${token}/api`,
                             {cache: "no-store"});
    if (!resp.ok) return showError();          // 410 / 404 → 失效态
    data = await resp.json();
  } catch {
    return showError();
  }
  render(data);
}

function showError() {
  $("#share-error").hidden = false;
}

function render(data) {
  document.title = `${data.title} · My Music`;
  $("#share-title").textContent = data.title;
  $("#share-subtitle").textContent = data.subtitle;
  $("#share-expire").textContent = `链接有效期至 ${fmtDateTime(data.expires_at)}`;

  const heroArt = $("#hero-art");
  if (data.kind === "playlist" && data.playlist) {
    if (data.playlist.cover_version > 0) {
      setArt(heroArt, `/music/share/${token}/artwork/playlist/`
             + `${data.playlist.playlist_id}?v=${data.playlist.cover_version}`);
    } else {
      setPlaceholder(heroArt);
    }
  } else if (data.kind === "album" && data.album_id) {
    setArt(heroArt, `/music/share/${token}/artwork/album/${data.album_id}`);
  } else if (data.tracks.length > 0) {
    setArt(heroArt, artURL(data.tracks[0]));
  } else {
    setPlaceholder(heroArt);
  }

  // 待播队列 = 分享清单里能播的 (app playerStart 同款: 默认列表循环)
  playQueue = createPlayQueue(data.tracks.filter((t) => t.playable));
  playQueue.repeat = "all";
  updatePlayModeButton();          // 三态循环键图标跟上真实状态
  if (data.kind === "playlist" || data.kind === "album") {
    $("#list-head").hidden = false;
    $("#list-head").textContent = `${data.tracks.length} 首歌曲`;
    // 1.8.41 行首序号换歌曲封面 (用户点名, app 歌单同款): 裂图退 ♪ 占位
    $("#share-list").innerHTML = data.tracks.map((t) => (
      `<div class="row${t.playable ? "" : " na"}" data-track-id="${t.track_id}">`
      + `<span class="lead"><img alt="" loading="lazy" decoding="async"
         src="${artURL(t)}"
         onerror="this.onerror=null;this.closest('.lead').classList.add('ph');this.remove()"></span>`
      + `<span class="txt"><span class="t">${esc(t.title)}</span>`
      + `<span class="a">${esc(t.artist)}</span></span>`
      + `<span class="dur">${fmtTime(t.duration_seconds)}</span></div>`
    )).join("");
  }
  // 单曲分享没有上一首/下一首可言, 传输区收成一颗播放键 (循环键留着
  // —— 单曲循环一首歌也有意义)
  if (playQueue.tracks.length < 2) {
    $("#fp-prev").hidden = true;
    $("#fp-next").hidden = true;
  }
  if (playQueue.tracks.length === 0) $("#hero-play").classList.add("off");
  $("#share-card").hidden = false;
}
