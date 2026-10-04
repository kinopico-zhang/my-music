// share-viewer-lyrics — My Music 分享页歌词: 取词铺词/当前句高亮/手动滚词暂停跟唱。
// 1.8.17 改版 (用户点名): 歌词只走歌词键 (toggleLyricsView), 封面点按/
// 滑动都不再切歌词; 没词的曲子键灰掉; 切歌后歌词/封面视图跟上一首保持
// 一致 (开着词不因没词强关, 空态「这首歌没有歌词」垫着)。
// 1.8.130 对齐应用: 手动滚词出「回到当前句」+ 浏览期间整页清晰
// (.browsing), 静置 4 秒/点行跳播后回跟唱; 氛围底压暗 (#full-player.lyrics);
// 与待播队列互斥 (同住封面区, 二选一)。
"use strict";
/* global $, activeLyricIndex, audio, currentTrack, esc, lyricIndex: writable,
          lyrics: writable, lyricsAutoUntil: writable, lyricsCache,
          lyricsFollowPaused: writable, lyricsLastScrollAt: writable, parseLyrics,
          playerOpen, queueViewOpen, closeQueueView, token */
/* exported loadLyrics, resumeLyricsFollow, setLyricsView, syncLyricHighlight,
            toggleLyricsView */

// ------------------------------------------------------------ 歌词

let lyricsViewOpen = false;   // 歌词键掀开的歌词视图 (换曲不自动关, app 同款)
let lyricsSettled = false;    // 取词落定 (false = 还在取, 别急着说「没有歌词」)
// 对齐微调 (1.8.133, 跟 app 同一口径): 正 = 词整体延后, 高亮拿 播放进度
// − offset 对轴; 分享访客改不了, 但主人调好的对齐跟着这份分享走
let lyricsOffsetMs = 0;
const shareLyricsOffsets = new Map();   // track_id → 毫秒 (与取词同缓存)

/** 歌词键点按开合。 */
function toggleLyricsView() {
  setLyricsView(!lyricsViewOpen);
}

/** 开合歌词视图; 视图关着且没词想开也开不了 (视图开着时空态垫着,
    点一下就回封面)。 */
function setLyricsView(open) {
  if (open && !lyrics && !lyricsViewOpen) return;
  if (open && queueViewOpen) closeQueueView();   // 同住封面区, 二选一 (app 同款)
  lyricsViewOpen = open;
  renderLyricsView();
}

/** 换曲铺词: 先空态, 取回来 (404 = 没词) 再铺; 换得快就听最后那首的。 */
async function loadLyrics(track) {
  lyrics = null;
  lyricsSettled = false;
  lyricIndex = -1;
  lyricsFollowPaused = false;
  renderLyricsView();
  if (lyricsCache.has(track.track_id)) {
    lyrics = lyricsCache.get(track.track_id);
    lyricsOffsetMs = shareLyricsOffsets.get(track.track_id) || 0;
    lyricsSettled = true;
    renderLyricsView();
    return;
  }
  let parsed = null;
  try {
    const resp = await fetch(`/music/share/${token}/lyrics/${track.track_id}`,
                             {cache: "no-store"});
    if (resp.ok) {
      const body = await resp.json();
      parsed = parseLyrics(body.lyrics);
      shareLyricsOffsets.set(track.track_id, body.lyrics_offset_ms || 0);
    }
  } catch { /* 网络挂了当没词 */ }
  lyricsCache.set(track.track_id, parsed);
  if (!currentTrack || currentTrack.track_id !== track.track_id) return;   // 换曲了
  lyrics = parsed;
  lyricsOffsetMs = shareLyricsOffsets.get(track.track_id) || 0;
  lyricsSettled = true;
  renderLyricsView();
}

function renderLyricsView() {
  const box = $("#fp-lyrics");
  const open = lyricsViewOpen;                 // 开合只听用户/换曲前那首的态,
  box.classList.toggle("static", !lyrics || !lyrics.synced);   // 不随有没有词翻面
  box.hidden = !open;
  // 歌词页罩满封面区 (1.8.20 用户点名「不要封面缩略图」): 封面整块藏掉,
  // 歌词独占; 氛围底跟着压暗 (app 同款)
  $("#fp-art-wrap").hidden = open;
  $("#full-player").classList.toggle("lyrics", open);
  // 歌词键: 视图关着时没词灰掉 (开不了); 开着保持可点好关回封面
  const lyricsButton = $("#fp-lyrics-btn");
  lyricsButton.disabled = !lyrics && !lyricsViewOpen;
  lyricsButton.classList.toggle("on", open);
  if (!open) {
    $("#lyrics-resume").hidden = true;        // 浏览残留收干净
    box.classList.remove("browsing");
    return;
  }
  if (!lyrics) {
    // 还在取词: 先空着 (别闪「没有歌词」的错话); 落定没词: 空态明说
    box.innerHTML = lyricsSettled
      ? '<div class="lyrics-empty">这首歌没有歌词</div>' : "";
    box.scrollTop = 0;
    return;
  }
  box.innerHTML = lyrics.lines.map(
    (line) => `<p class="lyrics-line" data-time="${line.timeSeconds}">`
      + `${esc(line.text)}</p>`).join("");
  lyricsAutoUntil = Date.now() + 900;   // 重铺归顶的程序滚动不算手动
  box.scrollTop = 0;                    // 换曲/重铺从头 (1.8.5)
  syncLyricHighlight(true);
}

/** 高亮跟到当前句 (清晰度分工: 当前句清晰放大, 下一句清晰不放大,
    其余模糊), 顺带把当前句滚到视线中央。 */
function syncLyricHighlight(force) {
  if (!lyrics || !lyrics.synced) return;
  // 微调对轴: 正 = 词延后 (app 高亮同一式)
  const index = activeLyricIndex(lyrics.lines,
                                 audio.currentTime - lyricsOffsetMs / 1000);
  if (index === lyricIndex && !force) return;
  lyricIndex = index;
  const lines = $("#fp-lyrics").querySelectorAll(".lyrics-line");
  lines.forEach((line, i) => {
    line.classList.toggle("active", i === index);
    line.classList.toggle("upnext", i === index + 1);
  });
  if (index >= 0 && lines[index] && !lyricsFollowPaused) {
    scrollLyricsTo(lines[index]);
  }
}

function scrollLyricsTo(line) {
  const box = $("#fp-lyrics");
  lyricsAutoUntil = Date.now() + 900;   // smooth 滚动期间的 scroll 不算手动
  box.scrollTo({ top: line.offsetTop - box.clientHeight / 2
                         + line.offsetHeight / 2,
                 behavior: "smooth" });
}

/** 回到跟唱: 收浏览态 (整页距离模糊回来), 滚回当前句。 */
function resumeLyricsFollow(scrollToActive = true) {
  lyricsFollowPaused = false;
  $("#lyrics-resume").hidden = true;
  $("#fp-lyrics").classList.remove("browsing");   // 浏览态结束, 距离模糊回来
  if (scrollToActive && lyricIndex >= 0) {
    const lines = $("#fp-lyrics").querySelectorAll(".lyrics-line");
    if (lines[lyricIndex]) scrollLyricsTo(lines[lyricIndex]);
  }
}

// 手动滑歌词 (smooth 定位引发的 scroll 不算) → 暂停跟唱 + 出「回到当前句」;
// 浏览期间整页取消模糊 (.browsing), 静置 4 秒自动回跟唱 (app 同款节奏)。
// 关页/关视图途中歌词的惯性滚动还会补发几拍 scroll, 这时点亮浏览态会
// 残留到下次开页 —— 没开就不算。
$("#fp-lyrics").addEventListener("scroll", () => {
  if (Date.now() < lyricsAutoUntil) return;
  if (!playerOpen || !lyricsViewOpen) return;
  if (!$("#fp-lyrics").classList.contains("static")) {   // 无时间轴: 没跟唱可暂停
    lyricsFollowPaused = true;
    $("#fp-lyrics").classList.add("browsing");
    $("#lyrics-resume").hidden = false;
  }
  lyricsLastScrollAt = Date.now();
});
setInterval(() => {
  if (lyricsFollowPaused && Date.now() - lyricsLastScrollAt > 4000) {
    resumeLyricsFollow();
  }
}, 600);

// 点句定位 (1.8.6 用户点名「通过歌词快速定位歌曲进度」): 点一句跳到那句
// 的时间, 就地落座跟唱 (紧跟的 timeupdate 把新当前句高亮并滚回视线中央)。
// 纯文本词没时间轴, 点不动。
$("#fp-lyrics").addEventListener("click", (event) => {
  const line = event.target.closest(".lyrics-line");
  if (!line || !lyrics || !lyrics.synced) return;
  const time = Number(line.dataset.time);
  if (time >= 0) audio.currentTime = time + lyricsOffsetMs / 1000;   // 微调对轴
  resumeLyricsFollow(false);
  syncLyricHighlight(true);
});

$("#lyrics-resume").addEventListener("click", () => resumeLyricsFollow());
