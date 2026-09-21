// share-viewer-playback — My Music 分享页播放: 队列开播/暂停/上下曲/播键态/锁屏控制中心。
// 拆自 share.html 的内联 <script> (结构化重构: 代码逐字节未动, 按 share.html 里的顺序加载, 跨模块引用走全局)。
// 1.8.37 (用户点名) 中排键的播放语义: 随机 = 下一首在队列里随机挑 (当前
// 曲除外); 循环三态 关 → 列表循环 (播完回绕) → 单曲循环 (播完重播本首)。
"use strict";
/* global $, BARS_SVG, ICON_PAUSE_BIG, ICON_PLAY_BIG, artURL, audio, loadLyrics, queue,
          queuePos: writable, setArt, token */
/* exported cycleRepeat, nextTrack, playQueue, prevTrack, syncStepButtons,
            togglePlay, toggleShuffle, updateIcons */

let shuffleOn = false;      // 随机: 下一首随机挑 (上一首仍按队列走)
let repeatMode = 0;         // 循环: 0 关 / 1 列表循环 / 2 单曲循环

function playQueue(pos) {
  if (pos < 0 || pos >= queue.length) return;
  const prevPos = queuePos;    // 切歌方向 = 新旧下标比 (滑/按键/点行通吃)
  queuePos = pos;
  const track = queue[pos];
  audio.src = `/music/share/${token}/stream/${track.track_id}`;
  for (const input of [$("#seek"), $("#fp-scrub")]) input.value = "0";
  $("#t-now").textContent = "0:00";
  $("#t-total").textContent = "-:--";
  $("#fp-time-cur").textContent = "-0:00";
  $("#fp-time-total").textContent = "-0:00";
  $("#player").hidden = false;
  $("#p-title").textContent = track.title;
  $("#p-artist").textContent = track.artist;
  setArt($("#p-art"), artURL(track));
  // 全屏页: 曲名/作者·专辑/封面/毛玻璃底 一起跟上 (1.8.5 作者行并上
  // 专辑名, app 同款「下面是标题和作者专辑名称」)
  $("#fp-title").textContent = track.title;
  $("#fp-artist").textContent =
    [track.artist, track.album_title].filter(Boolean).join(" | ");
  // 1.8.17 标题行的歌手照片 (用户点名「在歌名和艺人旁边加歌手照片」):
  // 走公开艺人海报路由 (门禁按这份分享里的艺人放行), 没传过海报的 404
  // —— onerror 藏图, 布局不塌
  const artistArt = $("#fp-artist-art");
  if (track.artist_id) {
    artistArt.onerror = () => { artistArt.hidden = true; };
    artistArt.src = `/music/share/${token}/artwork/artist/${track.artist_id}`;
    artistArt.hidden = false;
  } else {
    artistArt.hidden = true;
  }
  // 1.8.6 修「全屏页看不到封面」: #fp-art 本尊是 <img> (app 同款), 直接挂
  // src; 此前错用了给容器 div 用的 setArt —— 往 <img> 里塞子 <img> 永远
  // 不渲染, 封面就一直空着 (迷你条的 #p-art 是 div, setArt 没问题)
  $("#fp-art").src = artURL(track);
  // 1.8.19 切歌封面方向滑入 (用户点名「滑动封面切歌怎么没有动画」):
  // 下一首从右进 (左滑的方向), 上一首从左进; 重播本首不动。摘类→强制
  // 回流→挂类, 连着切才重得起来
  const artWrap = $("#fp-art-wrap");
  artWrap.classList.remove("art-in-next", "art-in-prev");
  if (pos !== prevPos) {
    void artWrap.offsetWidth;
    artWrap.classList.add(pos > prevPos ? "art-in-next" : "art-in-prev");
  }
  const bgImg = $("#fp-bg-img");
  bgImg.onerror = () => { $("#fp-bg").classList.add("ph"); bgImg.removeAttribute("src"); };
  if (bgImg.getAttribute("src") !== artURL(track)) {
    $("#fp-bg").classList.remove("ph");
    bgImg.src = artURL(track);
  }
  $("#fp-prev").disabled = repeatMode === 0 && queuePos <= 0;
  $("#fp-next").disabled = repeatMode === 0 && !shuffleOn
    && queuePos >= queue.length - 1;
  document.title = `${track.title} · My Music`;
  loadLyrics(track);
  updateMediaSession(track);
  updateIcons();     // 自动播放被浏览器拦住时 play 事件不来, 键态先就位
  // 1.8.41 行首是封面不是序号: 封面永远留着, 播放行的跳条蒙在封面上
  // (半透黑纱 + 白条, app 播放队列 1.8.38 同款), 不再抹掉行首回填
  document.querySelectorAll(".row").forEach((row) => {
    const on = Number(row.dataset.trackId) === track.track_id;
    row.classList.toggle("on", on);
    const lead = row.querySelector(".lead");
    const bars = lead.querySelector(".bars");
    if (on && !bars) lead.insertAdjacentHTML("beforeend", BARS_SVG);
    if (!on && bars) bars.remove();
  });
  audio.play().catch(() => {});
}

function togglePlay() {
  if (audio.paused) {
    if (!audio.src) return playQueue(0);
    audio.play().catch(() => {});
  } else {
    audio.pause();
  }
}

function prevTrack() {
  if (queuePos > 0) playQueue(queuePos - 1);
  else if (repeatMode !== 0 && queue.length > 1) playQueue(queue.length - 1);
}

function nextTrack() {
  // 随机: 队列里随机挑 (当前曲除外); 顺序: 下一首, 队尾在循环开着时回绕
  if (shuffleOn && queue.length > 1) {
    let pick = queuePos;
    while (pick === queuePos) pick = Math.floor(Math.random() * queue.length);
    playQueue(pick);
    return;
  }
  if (queuePos + 1 < queue.length) playQueue(queuePos + 1);
  else if (repeatMode !== 0 && queue.length > 0) playQueue(0);
}

/** 上下曲键的可用态 (随机/循环开着时队列两头也能走: 随机永远有下一首,
    循环队尾回绕队首)。 */
function syncStepButtons() {
  $("#fp-prev").disabled = repeatMode === 0 && queuePos <= 0;
  $("#fp-next").disabled = repeatMode === 0 && !shuffleOn
    && queuePos >= queue.length - 1;
}

/** 1.8.37 随机键: 开关随机下一首, 点亮键面。 */
function toggleShuffle() {
  shuffleOn = !shuffleOn;
  $("#fp-shuffle").classList.toggle("on", shuffleOn);
  syncStepButtons();
}

/** 1.8.37 循环键: 三态轮换 关 → 列表循环 → 单曲循环 (图标带 "1")。 */
function cycleRepeat() {
  repeatMode = (repeatMode + 1) % 3;
  $("#fp-repeat").classList.toggle("on", repeatMode !== 0);
  $("#fp-repeat").classList.toggle("one", repeatMode === 2);
  syncStepButtons();
}

function updateIcons() {
  const playing = !audio.paused;
  $("#ic-play").hidden = playing;
  $("#ic-pause").hidden = !playing;
  const toggleSvg = $("#p-toggle svg");
  toggleSvg.querySelector(".use-play").style.display = playing ? "none" : "";
  toggleSvg.querySelector(".use-pause").style.display = playing ? "" : "none";
  $("#fp-play").innerHTML = playing ? ICON_PAUSE_BIG : ICON_PLAY_BIG;
  const bars = document.querySelector(".row .bars");
  if (bars) bars.classList.toggle("paused", audio.paused);
}

// 锁屏/控制中心 (支持的浏览器才有; 微信内建浏览器没有也不碍事)
function updateMediaSession(track) {
  if (!("mediaSession" in navigator) || typeof MediaMetadata === "undefined") return;
  try {
    navigator.mediaSession.metadata = new MediaMetadata({
      title: track.title, artist: track.artist, album: "My Music",
      artwork: [{ src: new URL(artURL(track), location.href).href,
                  sizes: "512x512", type: "image/jpeg" }],
    });
    navigator.mediaSession.setActionHandler("play", () => audio.play().catch(() => {}));
    navigator.mediaSession.setActionHandler("pause", () => audio.pause());
    if (queue.length > 1) {
      navigator.mediaSession.setActionHandler("previoustrack", prevTrack);
      navigator.mediaSession.setActionHandler("nexttrack", nextTrack);
    }
  } catch { /* 老浏览器 setActionHandler 会抛, 不值得为它炸页面 */ }
}

