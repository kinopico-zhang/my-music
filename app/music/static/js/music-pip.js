// music-pip — 画中画迷你播放窗 (1.8.105 上桌; 1.8.106 改失焦自动开/回焦收;
// 1.8.107 修用户实报「来回切换页面, 画中画就没了」: Chrome 只许赶在最近的
// 用户手势 (~5 秒) 里 requestWindow, 回焦即关的小窗再想弹开时手势早过期,
// 被 NotAllowedError 拦下 —— 小窗改长驻: 失焦时 (还没开过) 自动弹, 回到
// 播放页不收, 用户亲手 ✕ 过的这页会话不再自动弹): Chrome 的 Document
// Picture-in-Picture API 开一枚总在最前的小窗, 里面封面/歌名/进度线/
// 上一首·播停·下一首 —— 音频照旧留在主页的 #audio 里播 (PiP 窗只是遥控器
// +显示器, 主页最小化、切去别的应用都不断音), 控制键回连主页的播放函数
// (监听器闭包在 opener 一侧, 主页的全局都拿得到)。探测不到这 API 的浏览器
// (Firefox/Safari) 整个模块歇着。窗内文档不吃主页样式, 自带 music-pip.css。
"use strict";
/* global $, ICON_PAUSE, ICON_PLAY, PLACEHOLDER_ARTWORK, currentTrack,
          playerIsPlaying, playerNext, playerPrevious, playerToggle */

let pipWindow = null;       // 开着的画中画窗 (null = 没开, pagehide 时清)
let pipOpenTimer = 0;       // 失焦后的 300ms 观望计时 (回焦了就不弹)
let pipDismissed = false;   // 用户亲手 ✕ 过小窗: 这一页会话不再自动弹
let pipClosingByApp = false;   // 代关标记 (主页收页时我们调的 close, 不算嫌弃)

// 上一首/下一首键的图标 (全屏播放页同款三角, 缩到 24)
const PIP_PREV = '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M21.981 6.098L14.6 10.949Q13 12 14.6 13.051L21.981 17.902Q23.5 18.9 23.5 17.082L23.5 6.918Q23.5 5.1 21.981 6.098M9.481 6.098L2.1 10.949Q0.5 12 2.1 13.051L9.481 17.902Q11 18.9 11 17.082L11 6.918Q11 5.1 9.481 6.098" fill="currentColor"/></svg>';
const PIP_NEXT = '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M2.019 6.098L9.4 10.949Q11 12 9.4 13.051L2.019 17.902Q0.5 18.9 0.5 17.082L0.5 6.918Q0.5 5.1 2.019 6.098zM14.519 6.098L21.9 10.949Q23.5 12 21.9 13.051L14.519 17.902Q13 18.9 13 17.082L13 6.918Q13 5.1 14.519 6.098z" fill="currentColor"/></svg>';

/** 当前曲的封面地址 (专辑封面, 没专辑给占位图 —— 与播放页同一口径)。 */
function pipArtwork(track) {
  return track && track.album_id
    ? `/music/media/albums/${track.album_id}/artwork` : PLACEHOLDER_ARTWORK;
}

/** 小窗文案/封面/播停键刷一拍 (开窗、换曲、起播时)。 */
function updatePipChrome() {
  if (!pipWindow) return;
  const doc = pipWindow.document;
  const track = currentTrack;
  doc.getElementById("pip-title").textContent = track ? track.title : "My Music";
  doc.getElementById("pip-artist").textContent = track
    ? [track.artist, track.album_title].filter(Boolean).join(" · ") : "没在播";
  doc.getElementById("pip-art").src = pipArtwork(track);
  updatePipPlayButton();
}

/** 播停键随主播放器走 (play/pause 事件各喊一拍)。 */
function updatePipPlayButton() {
  const button = pipWindow && pipWindow.document.getElementById("pip-play");
  if (button) button.innerHTML = playerIsPlaying() ? ICON_PAUSE : ICON_PLAY;
}

/** 进度线随主 #audio 走 (timeupdate ≈4Hz, 只写宽度, 没开着窗早退)。 */
function updatePipProgress() {
  const bar = pipWindow && pipWindow.document.getElementById("pip-progress");
  if (!bar) return;
  const audio = $("#audio");
  const total = Number.isFinite(audio.duration) ? audio.duration : 0;
  bar.style.width = total > 0 ? `${(audio.currentTime / total) * 100}%` : "0%";
}

/** 开画中画窗 (已在开着就不动); 没赶上用户手势会被浏览器拒 —— 调用方兜。 */
async function openPipWindow() {
  if (pipWindow && !pipWindow.closed) return;
  pipWindow = await documentPictureInPicture.requestWindow(
    { width: 400, height: 112 });
  const doc = pipWindow.document;
  doc.title = "My Music";
  const link = doc.createElement("link");
  link.rel = "stylesheet";
  link.href = "/music/static/css/music-pip.css?v=1";
  doc.head.appendChild(link);
  doc.body.innerHTML = `
    <img id="pip-art" alt="">
    <div class="pip-info">
      <b id="pip-title"></b>
      <small id="pip-artist"></small>
      <div class="pip-track"><i id="pip-progress"></i></div>
    </div>
    <div class="pip-keys">
      <button type="button" id="pip-prev" aria-label="上一首"></button>
      <button type="button" id="pip-play" aria-label="播放/暂停"></button>
      <button type="button" id="pip-next" aria-label="下一首"></button>
    </div>`;
  doc.getElementById("pip-prev").innerHTML = PIP_PREV;
  doc.getElementById("pip-next").innerHTML = PIP_NEXT;
  // 控制键回连主页播放函数 (监听器挂在 opener 侧闭包里)。playerNext 必须
  // 包一层箭头函数 —— 裸挂会把 click 事件对象当 forceAutoplay 传进去
  doc.getElementById("pip-prev").addEventListener("click", playerPrevious);
  doc.getElementById("pip-play").addEventListener("click", playerToggle);
  doc.getElementById("pip-next").addEventListener("click", () => playerNext());
  // 窗关了收尾; pagehide 比 unload 可靠。谁关的要分清: 我们代关的 (主页
  // 收页) 不算嫌弃, 用户自己 ✕ 的记下 —— 这一页会话别再自动弹回来烦人
  pipWindow.addEventListener("pagehide", () => {
    pipWindow = null;
    if (!pipClosingByApp) pipDismissed = true;
    pipClosingByApp = false;
  });
  updatePipChrome();
  updatePipProgress();
}

/** 关画中画窗 (主页收页时, 别留孤儿窗); pagehide 会跟着清引用。 */
function closePipWindow() {
  if (pipWindow && !pipWindow.closed) {
    pipClosingByApp = true;
    pipWindow.close();
  }
}

/** 失焦自动开 (1.8.106); 小窗长驻 (1.8.107): 回焦不收 —— Chrome 只许赶在
    最近用户手势里开窗, 收了这小窗就再也弹不回来了, 别关它。 */
function bindPip() {
  if (!("documentPictureInPicture" in window)) return;   // Firefox/Safari 歇着
  window.addEventListener("blur", () => {
    // 失焦先观望 300ms (一闪而过的失焦不弹窗), 到点还不在焦点、还正在播、
    // 用户没亲手 ✕ 过、手上还没开着, 才开 —— 没声的遥控器没意义
    clearTimeout(pipOpenTimer);
    pipOpenTimer = setTimeout(async () => {
      if (document.hasFocus() || !playerIsPlaying() || pipDismissed) return;
      try {
        await openPipWindow();
      } catch (_error) {
        // Chrome 要求 requestWindow 赶在最近的用户手势里 (约 5 秒):
        // 听了半天再切走的场景会被 NotAllowedError 拦下, 静默作罢
      }
    }, 300);
  });
  window.addEventListener("focus", () => {
    clearTimeout(pipOpenTimer);   // 还没弹就回来了: 不弹 (小窗不收, 长驻)
  });
  // 主页整个收掉 (关标签/跳走): 小窗别成孤儿
  window.addEventListener("pagehide", closePipWindow);
  // 主页播放器的动静带进小窗: 起播刷文案+键, 暂停刷键, 换曲 (loadedmetadata)
  // 刷整套, timeupdate 刷进度 —— 全从主 #audio 的原生事件取, 窗没开时早退
  const audio = $("#audio");
  audio.addEventListener("play", updatePipChrome);
  audio.addEventListener("pause", updatePipPlayButton);
  audio.addEventListener("loadedmetadata", updatePipChrome);
  audio.addEventListener("timeupdate", updatePipProgress);
}

bindPip();
