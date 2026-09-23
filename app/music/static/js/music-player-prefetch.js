// music-player-prefetch — My Music 下一曲预取: 后台拉下一曲的完整音频进 blob, 切歌秒换源。
// 拆自 music-player-queue (1.8.59); 预取同一条源解析路 (已下载的缓存直读,
// 流媒体直连) —— 预取也不再经 SW (iOS 锁屏冻结 SW 会掐断音频)。
"use strict";
/* global playQueue, playerCurrentTrackId, prefetched: writable,
          prefetchSequence: writable, queueUpcoming, resolveTrackSource */
/* exported discardPrefetch, prefetchNextTrack */

/** 后台拉下一曲的完整音频进 blob; 单槽: 只留即将播的那首, 旧的 revoke。
    下一曲的封面也顺手焐热 —— 冷门专辑的封面服务端要现抽 (NAS 盘一忙
    就是好几秒), 藏在整首歌的播放时间里预取, 切歌时即取即有。 */
function prefetchNextTrack() {
  if (!playQueue || playQueue.repeat === "one") return;   // 单曲循环没有"下一曲"
  const next = nextUpcomingTrack();
  if (!next || !next.playable || next.track_id === playerCurrentTrackId()) return;
  if (next.album_id) {
    const warmCover = new Image();
    warmCover.src = `/music/media/albums/${next.album_id}/artwork`;
  }
  if (prefetched && prefetched.trackId === next.track_id) return;   // 已就位
  discardPrefetch();
  const trackId = next.track_id;
  const token = prefetchSequence;
  resolveTrackSource(trackId)
    .then((source) => {
      const stale = token !== prefetchSequence
        || playerCurrentTrackId() === trackId     // 已经切到这首了
        || nextUpcomingTrack() !== next;          // 不再是下一曲
      if (stale) {
        // 缓存直读的 blob 没人接了: 当场回收 (流媒体地址没占什么, 直接丢)
        if (source.startsWith("blob:")) URL.revokeObjectURL(source);
        return;
      }
      if (source.startsWith("blob:")) {           // 已下载: 缓存直读的现成 blob
        prefetched = { trackId, objectURL: source };
        return;
      }
      return fetch(source)                        // 流媒体: 直连拉整曲
        .then((response) => (response.ok ? response.blob()
          : Promise.reject(new Error(`HTTP ${response.status}`))))
        .then((blob) => {
          if (token !== prefetchSequence) return;             // 目标已经变了
          if (playerCurrentTrackId() === trackId) return;     // 已经切到这首了
          if (nextUpcomingTrack() !== next) return;           // 不再是下一曲
          prefetched = { trackId, objectURL: URL.createObjectURL(blob) };
        });
    })
    .catch(() => { /* 预取失败: 到时候正常走网络 */ });
}

/** 下一曲 (不含当前; 队列快播完且不循环时没有)。 */
function nextUpcomingTrack() {
  const upcoming = queueUpcoming(playQueue);
  return upcoming.length > 1 ? upcoming[1] : null;
}

function discardPrefetch() {
  prefetchSequence++;              // 在途的旧请求回来也认作过期
  if (prefetched) {
    URL.revokeObjectURL(prefetched.objectURL);
    prefetched = null;
  }
}
