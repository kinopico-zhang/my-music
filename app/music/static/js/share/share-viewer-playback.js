// share-viewer-playback — My Music 分享页播放: 换曲/暂停/上下曲/三态循环键/播键态/锁屏控制中心。
// 1.8.130 (用户点名「按钮跟普通播放界面保持一致」) 语义整用应用的
// player-queue.js + music-player-queue.js 同款: 循环三态一键
// 列表循环 → 单曲循环 → 随机循环 (queueCyclePlayMode), 上一首播过 3 秒
// 先回本曲开头, 队尾列表循环回绕, 自然播完强续播 / 手动切歌保持播放状态。
"use strict";
/* global $, BARS_SVG, ICON_PAUSE_BIG, ICON_PLAY_BIG, ICON_REPEAT, ICON_REPEAT_ONE,
          ICON_SHUFFLE, PLACEHOLDER_ARTWORK, artURL, audio, currentTrack: writable,
          fillStageQuality, loadLyrics, playQueue, queueAdvance, queueCurrent,
          queueGoBack, renderQueueView, setArt, token, toast,
          trackChangeListeners, queueViewOpen */
/* exported loadShareTrack, onTrackChange, playerNext, playerPrevious,
            startShareQueue, togglePlay, updateIcons, updateMediaSession,
            updatePlayModeButton */

/** 红键/空播键兜底: 队列当前位那首开播 (还没点过 = 队首)。 */
function startShareQueue() {
  const track = playQueue ? queueCurrent(playQueue) : null;
  if (track) loadShareTrack(track, true);
}

/** 载入曲目 (应用 loadTrack 的分享版): 音频源 + 迷你条/全屏页文案 + 歌词 +
 *  锁屏元数据 + 行高亮, 最后广播 trackChange —— 3D 舞台在那班车上重铺
 *  三张卡 (中卡本尊在这里挂 src, 两侧邻卡归舞台的 stageCardSrc)。 */
function loadShareTrack(track, autoplay) {
  currentTrack = track;
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
  // 全屏页: 曲名/作者·专辑 一起跟上 (1.8.5 作者行并上专辑名, app 同款)
  $("#fp-title").textContent = track.title;
  $("#fp-artist").textContent =
    [track.artist, track.album_title].filter(Boolean).join(" | ");
  // 1.8.6 修「全屏页看不到封面」: #fp-art 本尊是 <img>, 直接挂 src
  // (舞台只管两侧邻卡); 裂图退占位 (app 同款兜底)
  const art = $("#fp-art");
  art.onerror = () => { art.onerror = null; art.src = PLACEHOLDER_ARTWORK; };
  art.src = artURL(track);
  const bgImg = $("#fp-bg-img");
  bgImg.onerror = () => { $("#fp-bg").classList.add("ph"); bgImg.removeAttribute("src"); };
  if (bgImg.getAttribute("src") !== artURL(track)) {
    $("#fp-bg").classList.remove("ph");
    bgImg.src = artURL(track);
  }
  document.title = `${track.title} · My Music`;
  loadLyrics(track);
  updateMediaSession(track);
  updateIcons();     // 自动播放被浏览器拦住时 play 事件不来, 键态先就位
  // 1.8.41 行首是封面不是序号: 播放行的跳条蒙在封面上 (半透黑纱 + 白条,
  // app 播放队列同款), 不再抹掉行首回填
  document.querySelectorAll(".row").forEach((row) => {
    const on = Number(row.dataset.trackId) === track.track_id;
    row.classList.toggle("on", on);
    const lead = row.querySelector(".lead");
    const bars = lead.querySelector(".bars");
    if (on && !bars) lead.insertAdjacentHTML("beforeend", BARS_SVG);
    if (!on && bars) bars.remove();
  });
  if (queueViewOpen) renderQueueView();   // 队列开着: 播放行就地挪
  for (const listener of trackChangeListeners) listener(track);   // 3D 舞台重铺
  void fillStageQuality();   // 音质三条跟上新场 (app renderPlayerChrome 同款)
  if (autoplay) audio.play().catch(() => {});
}

function togglePlay() {
  if (audio.paused) {
    if (!currentTrack) return startShareQueue();
    audio.play().catch(() => {});
  } else {
    audio.pause();
  }
}

/** 下一首 (应用 playerNext 同款): 自然播完 forceAutoplay 强续, 手动/滑切
 *  保持播放状态; 三态键没有「关」—— 单曲/随机下队尾走不下去就到头播完了。 */
function playerNext(forceAutoplay) {
  if (!playQueue) return;
  const track = queueAdvance(playQueue);
  if (!track) { toast("播完了"); return; }
  loadShareTrack(track, forceAutoplay === true || !audio.paused);
}

/** 上一首 (应用 playerPrevious 同款): 播过 3 秒先回本曲开头 (苹果同款),
 *  队首再按一次回本曲开头 (queueGoBack 原地), 队中退一首。 */
function playerPrevious() {
  if (!playQueue) return;
  if (audio.currentTime > 3) {
    audio.currentTime = 0;
    return;
  }
  const track = queueGoBack(playQueue);
  if (track) loadShareTrack(track, !audio.paused);
}

/** 换曲回调挂号 (舞台在这挂重铺; 撤不掉也不碍事, 页面就一个舞台)。 */
function onTrackChange(listener) {
  trackChangeListeners.push(listener);
}

/** 三态循环键 (应用 updatePlayModeButton 同款): 列表/单曲/随机各有图标。 */
function updatePlayModeButton() {
  if (!playQueue) return;
  const shuffle = playQueue.shuffle;
  const one = !shuffle && playQueue.repeat === "one";
  $("#fp-mode-btn").innerHTML = shuffle ? ICON_SHUFFLE
    : one ? ICON_REPEAT_ONE : ICON_REPEAT;
}

function updateIcons() {
  const playing = !audio.paused;
  $("#ic-play").hidden = playing;
  $("#ic-pause").hidden = !playing;
  const toggleSvg = $("#p-toggle svg");
  toggleSvg.querySelector(".use-play").style.display = playing ? "none" : "";
  toggleSvg.querySelector(".use-pause").style.display = playing ? "" : "none";
  $("#fp-play").innerHTML = playing ? ICON_PAUSE_BIG : ICON_PLAY_BIG;
  const id = currentTrack ? currentTrack.track_id : 0;
  for (const bars of document.querySelectorAll(".bars")) {
    bars.classList.toggle("paused", !playing);   // 清单行 + 队列行的动条一起
  }
  for (const row of document.querySelectorAll(".queue-row")) {
    row.classList.toggle("playing", Number(row.dataset.queueTrackId) === id
                                  && playing);
  }
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
    if (playQueue && playQueue.tracks.length > 1) {
      navigator.mediaSession.setActionHandler("previoustrack", playerPrevious);
      navigator.mediaSession.setActionHandler("nexttrack", playerNext);
    }
  } catch { /* 老浏览器 setActionHandler 会抛, 不值得为它炸页面 */ }
}
