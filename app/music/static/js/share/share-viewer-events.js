// share-viewer-events — My Music 分享页事件: 音频事件/曲目清单与队列点播/三态循环键/进度拖动 + 开局。
// 1.8.130 (用户点名「按钮跟普通播放界面保持一致」) 底排三键对齐应用:
// 循环键三态一键 (列表循环 → 单曲循环 → 随机循环, queueCyclePlayMode),
// 队列键翻开待播面板 (点行跳播); 播完推进与 app 同款 (单曲循环回开头,
// 其余 playerNext 强续); 进度条垫命中层 (music-player-slider, iOS 按轨道
// 也跳值); 3D 封面舞台在此接线 (initArtStage)。
"use strict";
/* global $, audio, boot, enhanceSliderTouch, fmtTime, initArtStage,
          loadShareTrack, openFullPlayer, playQueue, playerNext, queueCyclePlayMode,
          queueJump, queueViewOpen, renderQueueView, seeking: writable,
          syncLyricHighlight, toggleLyricsView, togglePlay,
          toggleQueueView, toast, updateIcons, updatePlayModeButton */

// ------------------------------------------------------------ 按键

// 1.8.6: 红色播键一按顺势掀开全屏播放页 (用户点名) —— 迷你条的播键不掀,
// 只有大红键这样; 后面掀不迟 (openFullPlayer 自带"开着就不重复"守卫)
$("#hero-play").addEventListener("click", () => {
  togglePlay();
  openFullPlayer();
});
$("#p-toggle").addEventListener("click", togglePlay);
$("#fp-lyrics-btn").addEventListener("click", toggleLyricsView);
// 三态循环一键 (app 1.8.89 同款): 列表循环 → 单曲循环 → 随机循环,
// 切一下报一下当前态; 队列开着顺带重铺 (随机换序看得见)
$("#fp-mode-btn").addEventListener("click", () => {
  if (!playQueue) return;
  const mode = queueCyclePlayMode(playQueue);
  updatePlayModeButton();
  if (queueViewOpen) renderQueueView();
  toast(mode === "all" ? "列表循环" : mode === "one" ? "单曲循环" : "随机循环");
});
$("#fp-queue-btn").addEventListener("click", toggleQueueView);

// 分享清单点播 (队列跳转, 与队列面板同一语义)
$("#share-list").addEventListener("click", (event) => {
  const row = event.target.closest(".row");
  if (!row || row.classList.contains("na")) return;
  const track = queueJump(playQueue, Number(row.dataset.trackId));
  if (track) loadShareTrack(track, true);
});

// 队列面板点行跳播 (只读队列: 没有换序/删除 —— 那要登录会话)
$("#queue-list").addEventListener("click", (event) => {
  const row = event.target.closest("[data-queue-track-id]");
  if (!row || !playQueue) return;
  const track = queueJump(playQueue, Number(row.dataset.queueTrackId));
  if (track) loadShareTrack(track, true);
});

// ------------------------------------------------------------ 音频事件

audio.addEventListener("play", updateIcons);
audio.addEventListener("pause", updateIcons);
audio.addEventListener("loadedmetadata", () => {
  $("#t-total").textContent = fmtTime(audio.duration);
  $("#fp-time-total").textContent = `-${fmtTime(audio.duration)}`;
});
audio.addEventListener("timeupdate", () => {
  const duration = Number.isFinite(audio.duration) ? audio.duration : 0;
  if (!seeking && duration > 0) {
    const value = String(Math.round(audio.currentTime / duration * 1000));
    $("#seek").value = value;
    $("#fp-scrub").value = value;
    setScrubFill($("#fp-scrub"));
  }
  $("#t-now").textContent = fmtTime(audio.currentTime);
  $("#fp-time-cur").textContent = `-${fmtTime(audio.currentTime)}`;
  $("#fp-time-total").textContent = `-${fmtTime(Math.max(0, duration - audio.currentTime))}`;
  syncLyricHighlight(false);
});
audio.addEventListener("ended", () => {
  if (playQueue && playQueue.repeat === "one") {   // 单曲循环: 回开头重播
    audio.currentTime = 0;
    audio.play().catch(() => {});
    return;
  }
  playerNext(true);                                // 自然播完强续 (app 同款)
});
audio.addEventListener("error", () => {
  $("#p-title").textContent = "播放失败";
  $("#p-artist").textContent = "";
});

// ------------------------------------------------------------ 进度拖动

// 拖进度 (迷你条/全屏页同一套): input 里只做标记 + 标签跟随, 真正 seek
// 落在 change (iOS 拖完才发); metadata 没到时 iOS 会拒 currentTime,
// try/catch 吞掉等 loadedmetadata。
// 全屏页是 app 同款细进度条 (填充与滑块同色), --fill 画已播段。
function setScrubFill(input) {
  input.style.setProperty("--fill", `${Number(input.value) / 10}%`);
}
function bindSeek(input) {
  input.addEventListener("input", () => {
    seeking = true;
    setScrubFill(input);
    if (Number.isFinite(audio.duration) && audio.duration > 0) {
      const at = Number(input.value) / 1000 * audio.duration;
      $("#t-now").textContent = fmtTime(at);
      $("#fp-time-cur").textContent = `-${fmtTime(at)}`;
    }
  });
  input.addEventListener("change", () => {
    if (Number.isFinite(audio.duration) && audio.duration > 0) {
      try {
        audio.currentTime = Number(input.value) / 1000 * audio.duration;
      } catch { /* iOS 换源瞬间还没 metadata */ }
    }
    seeking = false;
  });
}
bindSeek($("#seek"));
bindSeek($("#fp-scrub"));
setScrubFill($("#fp-scrub"));   // 开局归零 (有总时长前也画个起点)
enhanceSliderTouch($("#fp-scrub"));   // iOS 命中垫 (app 同款): 按轨道也跳值

// ------------------------------------------------------------ 舞台与收尾

// 3D 封面舞台 (app 1.8.60 同款): 两侧站上一首/下一首, 左右划跟手切歌
initArtStage();

// 双指缩放全禁 (1.8.41, 用户点名「整个app任何地方都不允许」): body 的
// touch-action: pan-y 挡得住安卓/桌面, iOS Safari 的捏合缩放不吃
// touch-action —— 非标准手势事件掐掉才是 iOS 上的真解 (app 主壳同款)
document.addEventListener("gesturestart", (event) => event.preventDefault());

boot();
