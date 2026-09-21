// music-player-media-session — My Music 锁屏/控制中心: MediaSession 元数据与进度上报。
// 拆自 music-player.js (结构化重构: 代码逐字节未动, 按 music.html 里的顺序加载, 跨模块引用走全局)。
// 1.8.44 蓝牙车机封面 (用户车上实报「锁屏有封面、车机没有」): 特斯拉 v10
// 起支持蓝牙封面, iOS 13 起会把 now-playing 里的图塞进蓝牙的 AVRCP 通道
// (BIP 传 200 缩略图) —— 但网页给的远程 URL 封面, WebKit 是后台异步去取
// 的, 图进没进 now-playing 不保证, 车机上常只剩文字。对策: 封面先取成
// blob 再重设一次元数据 —— 图是本地现成数据, now-playing 收得完整 (锁屏
// 照旧有图, 赌的是蓝牙通道也跟着亮)。
"use strict";
/* global audioElement, currentTrack, playerNext, playerPrevious, startAudio */
/* exported syncPositionState, updateMediaSession */

// ------------------------------------------------------------ 锁屏/控制中心

let artBlobURL = "";    // 当前曲封面的 blob 址 (换曲回收, 别泄)
let artForTrack = -1;   // blob 属于哪首: 慢一拍的回包别盖到新歌头上

function updateMediaSession() {
  if (!("mediaSession" in navigator) || !currentTrack) return;
  const artwork = `/music/media/albums/${currentTrack.album_id}/artwork`;
  setMediaMetadata(artwork);     // 先给远程 URL: 锁屏立即可用, 取图失败也兜底
  fetch(artwork).then((resp) => (resp.ok ? resp.blob() : null)).then((blob) => {
    if (!blob || !currentTrack || artForTrack === currentTrack.track_id) return;
    artForTrack = currentTrack.track_id;
    if (artBlobURL) URL.revokeObjectURL(artBlobURL);
    artBlobURL = URL.createObjectURL(blob);
    setMediaMetadata(artBlobURL, blob.type);   // 本地图重设一次, 车机才有得拿
  }).catch(() => { /* 取不到图: 远程 URL 那份还在, 行为不退步 */ });
  for (const action of ["play", "pause", "previoustrack", "nexttrack",
                        "seekto", "seekbackward", "seekforward"]) {
    try {
      navigator.mediaSession.setActionHandler(action, mediaSessionAction(action));
    } catch (_error) { /* 老浏览器不认识某些动作 */ }
  }
}

function setMediaMetadata(artSrc, artType) {
  navigator.mediaSession.metadata = new MediaMetadata({
    title: currentTrack.title,
    artist: currentTrack.artist,
    album: currentTrack.album_title || "",
    artwork: [{ src: artSrc, sizes: "512x512",
                type: artType || "image/jpeg" }],
  });
}

/** 锁屏/控制中心的进度快照: 暂停时速率报 0 (不然外推器以为还在播),
    位置钳在 [0, 时长] 里; 时长没就绪就不报 (浏览器会拒)。 */
function syncPositionState() {
  if (!("mediaSession" in navigator) || !currentTrack) return;
  const audio = audioElement();
  if (!isFinite(audio.duration) || audio.duration <= 0) return;
  try {
    navigator.mediaSession.setPositionState({
      duration: audio.duration,
      playbackRate: audio.paused ? 0 : audio.playbackRate,
      position: Math.min(Math.max(audio.currentTime, 0), audio.duration),
    });
  } catch (_error) { /* 个别浏览器挑参数, 不挡播放 */ }
}

function mediaSessionAction(action) {
  const audio = audioElement();
  switch (action) {
    case "play": return () => startAudio().catch(() => {});
    case "pause": return () => audio.pause();
    case "previoustrack": return () => playerPrevious();
    case "nexttrack": return () => playerNext();
    case "seekto":
      return (details) => {
        if (details && typeof details.seekTime === "number") {
          audio.currentTime = details.seekTime;
        }
      };
    case "seekbackward": return () => { audio.currentTime = Math.max(0, audio.currentTime - 10); };
    default: return () => { audio.currentTime = Math.min(
      audio.duration || 0, audio.currentTime + 10); };
  }
}
