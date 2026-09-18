// share-viewer-lyrics — My Music 分享页歌词: 取词铺词/当前句高亮/手动滚词暂停跟唱。
// 拆自 share.html 的内联 <script> (结构化重构)。1.8.5 起 app 同款浮层;
// 1.8.17 改版 (用户点名): 歌词只走标题行的歌词键 (toggleLyricsView),
// 封面点按/滑动都不再切歌词 (封面的滑动手势让给了切歌); 没词的曲子
// 键灰掉; 切歌后歌词/封面视图跟上一首保持一致 (开着词不因没词强关,
// 空态「这首歌没有歌词」垫着)。
"use strict";
/* global $, activeLyricIndex, audio, esc, lyricIndex: writable, lyrics: writable,
          lyricsAutoUntil: writable, lyricsCache, lyricsFollowPaused: writable,
          lyricsLastScrollAt: writable, parseLyrics, queue, queuePos, token */
/* exported loadLyrics, setLyricsView, syncLyricHighlight, toggleLyricsView */

// ------------------------------------------------------------ 歌词

let lyricsViewOpen = false;   // 歌词键掀开的歌词视图 (换曲不自动关, app 同款)
let lyricsSettled = false;    // 取词落定 (false = 还在取, 别急着说「没有歌词」)

/** 歌词键点按开合 (1.8.17 用户点名「用歌词按钮切换」)。 */
function toggleLyricsView() {
  setLyricsView(!lyricsViewOpen);
}

/** 开合歌词视图; 视图关着且没词想开也开不了 (视图开着时空态垫着,
    点一下就回封面)。 */
function setLyricsView(open) {
  if (open && !lyrics && !lyricsViewOpen) return;
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
    lyricsSettled = true;
    renderLyricsView();
    return;
  }
  let parsed = null;
  try {
    const resp = await fetch(`/music/share/${token}/lyrics/${track.track_id}`,
                             {cache: "no-store"});
    if (resp.ok) parsed = parseLyrics((await resp.json()).lyrics);
  } catch { /* 网络挂了当没词 */ }
  lyricsCache.set(track.track_id, parsed);
  const current = queue[queuePos];
  if (!current || current.track_id !== track.track_id) return;   // 已经换曲了
  lyrics = parsed;
  lyricsSettled = true;
  renderLyricsView();
}

function renderLyricsView() {
  const box = $("#fp-lyrics");
  const open = lyricsViewOpen;                 // 开合只听用户/换曲前那首的态,
  box.classList.toggle("static", !lyrics || !lyrics.synced);   // 不随有没有词翻面
  box.hidden = !open;
  // 歌词页罩满封面区 (1.8.20 改回原样, 用户点名「不要封面缩略图」):
  // 封面整块藏掉, 歌词独占 (app 同款)
  $("#fp-art-wrap").hidden = open;
  // 歌词键 (1.8.17): 视图关着时没词灰掉 (开不了); 开着保持可点好关回封面
  const lyricsButton = $("#fp-meta-lyrics");
  lyricsButton.disabled = !lyrics && !lyricsViewOpen;
  lyricsButton.classList.toggle("on", open);
  if (!open) return;
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
  box.scrollTop = 0;                              // 换曲/重铺从头 (1.8.5)
  syncLyricHighlight(true);
}

/** 高亮跟到当前句 (清晰度分工 1.8.17: 当前句清晰放大, 下一句清晰不放大,
    其余模糊), 顺带把当前句滚到视线中央。 */
function syncLyricHighlight(force) {
  if (!lyrics || !lyrics.synced) return;
  const index = activeLyricIndex(lyrics.lines, audio.currentTime);
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

// 手动滚词: 暂停跟唱, 静置 4 秒自动回去 (应用同款节奏)
$("#fp-lyrics").addEventListener("scroll", () => {
  if (Date.now() < lyricsAutoUntil) return;
  lyricsFollowPaused = true;
  lyricsLastScrollAt = Date.now();
});
setInterval(() => {
  if (lyricsFollowPaused && Date.now() - lyricsLastScrollAt > 4000) {
    lyricsFollowPaused = false;
    syncLyricHighlight(true);
  }
}, 600);

// 点句定位 (1.8.6, 用户点名「通过歌词快速定位歌曲进度」, app 同款):
// 点一句跳到那句的时间; 跳播后退出手动滚词的"暂停跟唱", 紧跟的
// timeupdate 把新当前句高亮并滚回视线中央。纯文本词没时间轴, 点不动。
$("#fp-lyrics").addEventListener("click", (event) => {
  const line = event.target.closest(".lyrics-line");
  if (!line || !lyrics || !lyrics.synced) return;
  const time = Number(line.dataset.time);
  if (time >= 0) audio.currentTime = time;
  lyricsFollowPaused = false;
  syncLyricHighlight(true);
});

