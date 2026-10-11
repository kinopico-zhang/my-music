// music-player-media-session — My Music 锁屏/控制中心: MediaSession 元数据与进度上报。
// 拆自 music-player.js (结构化重构: 代码逐字节未动, 按 music.html 里的顺序加载, 跨模块引用走全局)。
// 1.8.44 蓝牙车机封面 (用户车上实报「锁屏有封面、车机没有」): 特斯拉 v10
// 起支持蓝牙封面, iOS 13 起会把 now-playing 里的图塞进蓝牙的 AVRCP 通道
// (BIP 传 200 缩略图) —— 但网页给的远程 URL 封面, WebKit 是后台异步去取
// 的, 图进没进 now-playing 不保证, 车机上常只剩文字。对策: 封面取回本地
// 再重设一次元数据 —— 图是本地现成数据, now-playing 收得完整 (锁屏照旧
// 有图, 赌的是蓝牙通道也跟着亮)。
// 1.8.140 车机媒体卡封面 (特斯拉浏览器实报「媒体控制界面只有浏览器图标,
// 没有歌的封面」): 1.8.44 的 blob: 址只有本进程认得, 车机把媒体信息递给
// 系统侧的通道一出进程就取不动 blob: (相对址同理拼不出请求, 认 cookie 的
// 通道还会被登录拦)。本地数据改走 data URI —— 字节自带在址里, 谁都拿得
// 动; 顺手归一成 ≤512 方 JPEG (原图动辄千像素, 塞进元数据前先压身量)。
// 远程绝对址垫在 data URI 后面当第二路 (浏览器自己取图仍走它, 最快)。
// 1.8.69 锁屏键位 (用户点名「应该是前一首, 后一首和暂停键」): iOS 锁屏
// 键位有限, seekbackward/seekforward 一注册就被 10 秒快退快进占了 —— 撤了,
// 只留切歌三键; 进度条拖动走 seekto, 不占键位。
// 1.8.70 气泡起播没键位 (用户实报「重启应用直接点气泡播放, 锁屏没有上一
// 首/下一首」): iOS 只认「真正出声那一刻」挂的键位, 出声前挂的 handlers
// 会被它丢掉 —— 开机恢复现场挂得早, 点气泡出声时早过点了。挂键位抽成
// rearmMediaSession, 起播事件 (play/playing) 里都重挂一遍 (幂等)。
"use strict";
/* global audioElement, currentTrack, pauseAudio, playbackDuration, playerNext,
          playerPrevious, startAudio */
/* exported rearmMediaSession, syncPositionState, updateMediaSession */

// ------------------------------------------------------------ 锁屏/控制中心

let artForTrack = -1;   // data URI 属于哪首: 慢一拍的回包别盖到新歌头上

function updateMediaSession() {
  if (!("mediaSession" in navigator) || !currentTrack) return;
  // 绝对地址 (1.8.140): 出进程的取图通道拿「/music/...」拼不出请求
  const artwork = `${location.origin}/music/media/albums/${currentTrack.album_id}/artwork`;
  const remoteEntry = { src: artwork, sizes: "512x512", type: "image/jpeg" };
  setMediaMetadata([remoteEntry]);   // 先给远程址: 锁屏立即可用, 取图失败也兜底
  fetch(artwork).then((resp) => (resp.ok ? resp.blob() : null)).then(async (blob) => {
    if (!blob || !currentTrack || artForTrack === currentTrack.track_id) return;
    let localEntry;
    try {
      localEntry = await artworkEntry(blob);   // 归一成 ≤512 方 JPEG 的 data URI
    } catch (_error) {
      return;    // 归一失败: 远程址那份还在, 行为不退步
    }
    if (!currentTrack || artForTrack === currentTrack.track_id) return;
    artForTrack = currentTrack.track_id;
    // data URI 打头 (字节自带, 车机系统侧的通道也拿得动), 远程址垫后兜底
    setMediaMetadata([localEntry, remoteEntry]);
  }).catch(() => { /* 取不到图: 远程址那份还在, 行为不退步 */ });
  rearmMediaSession();
}

/** 封面 blob → 元数据条目: 大图/非 JPEG 归一成 512 方 JPEG (铺满裁方, 与
    页面封面的呈现同款), 小 JPEG 原样进 data URI (不白压一道)。位图路走
    不通就把原图字节直接 base64 (sizes 声明是提示性的, 兜底 512 方)。 */
async function artworkEntry(blob) {
  let source = blob;
  let sizes = "512x512";
  try {
    const bitmap = await createImageBitmap(blob);
    const { width, height } = bitmap;
    if (width > 512 || height > 512 || blob.type !== "image/jpeg") {
      const canvas = document.createElement("canvas");
      canvas.width = 512; canvas.height = 512;
      const ctx = canvas.getContext("2d");
      const scale = Math.max(512 / width, 512 / height);
      ctx.drawImage(bitmap, (512 - width * scale) / 2, (512 - height * scale) / 2,
                    width * scale, height * scale);
      source = await new Promise((resolve) =>
        canvas.toBlob((out) => resolve(out || blob), "image/jpeg", 0.85));
    } else {
      sizes = `${width}x${height}`;
    }
    bitmap.close();
  } catch (_error) { /* 老解码器不认的格式: 原图字节直接走 */ }
  const dataURI = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(source);
  });
  return { src: dataURI, sizes, type: source.type || "image/jpeg" };
}

/** 重挂锁屏/控制中心动作键 (幂等)。iOS 只认「出声那一刻」挂的键位:
    出声前挂的 (开机恢复现场) 会被丢, 所以起播事件里都重挂一遍。 */
function rearmMediaSession() {
  if (!("mediaSession" in navigator)) return;
  for (const action of ["play", "pause", "previoustrack", "nexttrack",
                        "seekto"]) {
    try {
      navigator.mediaSession.setActionHandler(action, mediaSessionAction(action));
    } catch (_error) { /* 老浏览器不认识某些动作 */ }
  }
}

function setMediaMetadata(artwork) {
  navigator.mediaSession.metadata = new MediaMetadata({
    title: currentTrack.title,
    artist: currentTrack.artist,
    album: currentTrack.album_title || "",
    artwork,
  });
}

/** 锁屏/控制中心的进度快照: 暂停时速率报 0 (不然外推器以为还在播),
    位置钳在 [0, 时长] 里; 时长没就绪就不报 (浏览器会拒)。时长走
    playbackDuration (库时长, 1.8.74) —— iOS 流上 seek 后元素时长会翻脸,
    信它锁屏进度也会提前见底。 */
function syncPositionState() {
  if (!("mediaSession" in navigator) || !currentTrack) return;
  const audio = audioElement();
  const duration = playbackDuration();
  if (duration <= 0) return;
  try {
    navigator.mediaSession.setPositionState({
      duration,
      playbackRate: audio.paused ? 0 : audio.playbackRate,
      position: Math.min(Math.max(audio.currentTime, 0), duration),
    });
  } catch (_error) { /* 个别浏览器挑参数, 不挡播放 */ }
}

function mediaSessionAction(action) {
  const audio = audioElement();
  switch (action) {
    case "play": return () => startAudio().catch(() => {});
    case "pause": return () => pauseAudio();   // 1.8.71 走统一入口 (好认出自发暂停)
    case "previoustrack": return () => playerPrevious();
    case "nexttrack": return () => playerNext();
    default:                              // seekto: 锁屏进度条拖动
      return (details) => {
        if (details && typeof details.seekTime === "number") {
          audio.currentTime = details.seekTime;
        }
      };
  }
}
