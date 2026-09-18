// music-player-lyrics-toggle — My Music 歌词视图开关: 打开条件, 歌词键亮灰, 后台探词, 开合切换。
// 拆自 music-player.js (结构化重构: 代码逐字节未动, 按 music.html 里的顺序加载, 跨模块引用走全局)。
"use strict";
/* global $, cancelLyricsScroll, closeQueueView, currentTrack, fetchJSON, loadLyrics,
          lyricsActiveIndex: writable, lyricsCache, lyricsFollowPaused: writable,
          lyricsViewOpen: writable, parseLyrics, queueViewOpen */
/* exported lyricsActiveIndex, lyricsFollowPaused, openLyricsView, prefetchLyrics,
            syncLyricsButton, toggleLyricsView */

function openLyricsView() {
  // 1.8.20 歌词键默认灰 (没探明 = 当没词), 程序化开页不再看键 —— 唯一
  // 调用方是歌词搜索命中 (有词是搜索条件本身), 键还在灰着也得开
  if (!lyricsViewOpen) toggleLyricsView();
}

/** 歌词键状态 (1.8.20 反转默认, 用户点名「默认是没歌词的, 有歌词再亮」):
    没探明 = 灰着当没词, 探明确认有词才亮; 视图开着例外 —— 键是关回封面
    的路, 必须可点 (1.8.17 换曲不关视图, 空态「这首歌没有歌词」垫着)。 */
function syncLyricsButton() {
  const hasLyrics = currentTrack && lyricsCache.has(currentTrack.track_id)
    && lyricsCache.get(currentTrack.track_id) !== null;
  $("#fp-lyrics-btn").disabled = !lyricsViewOpen && !hasLyrics;
}

/** 换曲后台探一遍歌词: 结果进缓存, 歌词键跟着亮/灰 (1.8.20 默认灰着,
    探明有词才亮; 探不到也灰着 —— 下次换曲/开视图再探)。 */
function prefetchLyrics(track) {
  if (!track) return;
  fetchJSON(`/music/api/tracks/${track.track_id}/lyrics`)
    .then((response) => {
      lyricsCache.set(track.track_id,
        response.lyrics ? parseLyrics(response.lyrics) : null);
    })
    .catch(() => { /* 探不到: 默认灰着 (当没词), 开视图时 loadLyrics 再试 */ })
    .finally(() => {
      if (currentTrack && currentTrack.track_id === track.track_id) {
        syncLyricsButton();
      }
    });
}

function toggleLyricsView() {
  if (!lyricsViewOpen && queueViewOpen) closeQueueView();   // 同住封面区, 二选一
  lyricsViewOpen = !lyricsViewOpen;
  // 歌词页罩满封面区 (1.8.20 改回原样, 用户点名「不要封面缩略图」):
  // 封面整块藏掉, 歌词独占; .lyrics 类留着管背景压暗 (模糊底图再暗一档)
  $("#fp-lyrics").hidden = !lyricsViewOpen;
  $("#fp-art-wrap").hidden = lyricsViewOpen;
  $("#fp-lyrics-btn").classList.toggle("on", lyricsViewOpen);
  $("#full-player").classList.toggle("lyrics", lyricsViewOpen);
  lyricsFollowPaused = false;         // 开/关歌词都回到跟唱
  $("#lyrics-resume").hidden = true;
  $("#fp-lyrics").classList.remove("browsing");   // 距离模糊重新生效
  if (lyricsViewOpen) {
    loadLyrics();
  } else {
    cancelLyricsScroll();          // 关页时动画立刻停, scroll 事件别再误判
    lyricsActiveIndex = -1;
  }
  syncLyricsButton();    // 视图关了且这首没词: 键灰回去 (再开开不了)
}

