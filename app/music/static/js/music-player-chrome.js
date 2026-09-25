// music-player-chrome — My Music 播放器界面渲染: 迷你条 (含跑马灯)/全屏页文案, 播放键同步。
// 拆自 music-player.js (结构化重构), 1.8.0 气泡变窄: 上下曲撤走,
// 歌名/作者太长改跑马灯来回滚 (用户点名), 不再截断省略号。
// 1.8.72 来源行整行撤了 (用户点名) —— credits 接口还在, 前端没人读了。
"use strict";
/* global $, ICON_PAUSE, ICON_PAUSE_BIG, ICON_PLAY, ICON_PLAY_BIG, ICON_REPEAT,
          ICON_REPEAT_ONE, ICON_SHUFFLE, PLACEHOLDER_ARTWORK,
          currentTrack, playQueue, playerCurrentTrackId, playerIsPlaying */
/* exported renderPlayerChrome, updatePlayButtons, updatePlayModeButton */

// ------------------------------------------------------------ 界面渲染

function renderPlayerChrome() {
  const track = currentTrack;
  $("#mini-player").hidden = !track;   // 先显形再量跑马灯 (display:none 量不出宽)
  if (!track) return;
  $("#mini-art").src = PLACEHOLDER_ARTWORK;
  setMarqueeLine($("#mini-title"), track.title);
  setMarqueeLine($("#mini-artist"), track.artist);
  $("#fp-title").textContent = track.title;
  // 1.8.2 专辑名并进艺人行 (用户点名「用一个 | 隔开」)
  $("#fp-artist").textContent = [track.artist, track.album_title]
    .filter(Boolean).join(" | ");
  const artwork = track.album_id
    ? `/music/media/albums/${track.album_id}/artwork` : PLACEHOLDER_ARTWORK;
  $("#mini-art").src = artwork;
  $("#fp-art").src = artwork;
  $("#fp-bg-img").src = artwork;
  updatePlayButtons();
  updatePlayModeButton();
}

/** 迷你条一行文字: 放得下静止, 放不下挂 .marquee 来回滚
    (距离/时长写 CSS 变量, 两端各停一拍 —— 见 music-bottom-bar.css)。 */
function setMarqueeLine(line, text) {
  const run = line.querySelector(".mq-run");
  run.textContent = text;
  run.classList.remove("marquee");
  if (!text) return;
  const overflow = run.scrollWidth - line.clientWidth;
  if (overflow <= 2) return;               // 放得下: 不滚
  run.style.setProperty("--mq-dx", `${-overflow}px`);
  run.style.setProperty("--mq-dur", `${Math.max(8, overflow / 18)}s`);
  run.classList.add("marquee");
}

// 转屏/改窗口后行宽变了, 静止/滚动的判定要重量一遍 (防抖一下, 别跟每帧 resize 跑)
let marqueeResizeTimer = 0;
addEventListener("resize", () => {
  clearTimeout(marqueeResizeTimer);
  marqueeResizeTimer = setTimeout(() => {
    if (!currentTrack) return;
    setMarqueeLine($("#mini-title"), currentTrack.title);
    setMarqueeLine($("#mini-artist"), currentTrack.artist);
  }, 200);
});

function updatePlayButtons() {
  const playing = playerIsPlaying();
  $("#mini-play").innerHTML = playing ? ICON_PAUSE : ICON_PLAY;
  $("#fp-play").innerHTML = playing ? ICON_PAUSE_BIG : ICON_PLAY_BIG;
  for (const element of document.querySelectorAll("[data-track-row]")) {
    element.classList.toggle("playing",
      Number(element.dataset.trackRow) === playerCurrentTrackId() && playing);
  }
  // 队列行同拍 (1.8.58): 开着队列暂停/续播, 动条当场收/放 (列表行同款)
  for (const row of document.querySelectorAll(".queue-row")) {
    row.classList.toggle("playing",
      Number(row.dataset.queueTrackId) === playerCurrentTrackId() && playing);
  }
}

/** 三态循环键 (1.8.89 用户点名): 列表/单曲/随机各有各的图标, 队列没起时
    回落列表循环形 (页面内联默认形与之逐字节同款, 首拍刷新不跳位)。 */
function updatePlayModeButton() {
  if (!playQueue) return;
  const shuffle = playQueue.shuffle;
  const one = !shuffle && playQueue.repeat === "one";
  $("#fp-mode-btn").innerHTML = shuffle ? ICON_SHUFFLE
    : one ? ICON_REPEAT_ONE : ICON_REPEAT;
}

// 收起后等滑出动画 (300ms) 再 display:none。这期间两层都要放行点击到下层列表
// (用户看见列表露出来了, 点了就该有反应); 重开必须撤掉挂着的隐藏定时器,
// 不然「刚关又马上开」时旧定时器会把正开着的播放页藏掉, 之后所有点击
// 全落到下层列表上 (表现为按键没反应、点了别的歌)。
