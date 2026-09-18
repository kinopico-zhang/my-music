// music-player-lyrics-toggle — My Music 歌词视图开关: 打开条件, 歌词键亮灰, 后台探词, 开合切换。
// 拆自 music-player.js (结构化重构: 代码逐字节未动, 按 music.html 里的顺序加载, 跨模块引用走全局)。
"use strict";
/* global $, cancelLyricsScroll, closeQueueView, currentTrack, fetchJSON, loadLyrics,
          lyricsActiveIndex: writable, lyricsCache, lyricsFollowPaused: writable,
          lyricsViewOpen: writable, parseLyrics, queueViewOpen */
/* exported lyricsActiveIndex, lyricsFollowPaused, openLyricsView, prefetchLyrics,
            syncLyricsButton, toggleLyricsView */

function openLyricsView() {
  if (!lyricsViewOpen && !$("#fp-lyrics-btn").disabled) toggleLyricsView();
}

/** 歌词键状态: 探明没歌词的置灰禁点 —— 视图关着时开不了; 视图开着
    (1.8.17 换曲不再强关回封面, 空态「这首歌没有歌词」垫着) 键保持
    可点, 好点回封面 (切歌后视图跟上一首保持一致, 用户点名)。 */
function syncLyricsButton() {
  const noLyrics = currentTrack && lyricsCache.has(currentTrack.track_id)
    && lyricsCache.get(currentTrack.track_id) === null;
  $("#fp-lyrics-btn").disabled = !!noLyrics && !lyricsViewOpen;
}

/** 换曲后台探一遍歌词: 结果进缓存, 歌词键跟着亮/灰 (探不到先不灰)。 */
function prefetchLyrics(track) {
  if (!track) return;
  fetchJSON(`/music/api/tracks/${track.track_id}/lyrics`)
    .then((response) => {
      lyricsCache.set(track.track_id,
        response.lyrics ? parseLyrics(response.lyrics) : null);
    })
    .catch(() => { /* 探不到就当还没探: 键保持可点, 开视图再试 */ })
    .finally(() => {
      if (currentTrack && currentTrack.track_id === track.track_id) {
        syncLyricsButton();
      }
    });
}

function toggleLyricsView() {
  if (!lyricsViewOpen && queueViewOpen) closeQueueView();   // 同住封面区, 二选一
  lyricsViewOpen = !lyricsViewOpen;
  $("#fp-art-wrap").hidden = lyricsViewOpen;
  $("#fp-lyrics").hidden = !lyricsViewOpen;
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

