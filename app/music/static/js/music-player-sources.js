// music-player-sources — My Music 曲目音频源解析与失败兜底: 本地字节
// (手动下载 > 自动缓存) 优先, 流媒体直连兜底; 播放挂了先试缓存救回,
// 不行跳下一首。
// 拆自 music-player-queue (1.8.76: 换源/兜底与队列驱动分家, queue 顶到
// 200 行帽按逻辑再切一刀 —— loadTrack 管"播什么", 这儿管"声音从哪来")。
// 1.8.76 锁屏/后台连播三刀的源侧两刀: 已下载/已自动缓存的歌在 loadTrack
// 里先按流占位 (同步赋址不断流), 这儿补刀换 blob (还没出声才换); 流挂了
// localBlobFor 救回原位置接着放, 没有就 playerNext 强续 —— 连挂 3 首封顶
// 停住 (playFailStreak), 边界流一挂不再死在半路。
// 1.8.78 打断后自动续播排程搬来本模块 (跟失败兜底作伴 —— 都是"声音没了
// 怎么救"): iOS 打断把 Safari 音频会话整个收走, 锁屏控件跟着没影, 页面
// 不出声就拿不回控件; 小步重试探着续播, 一放行出声, 锁屏控件自己回来。
"use strict";
/* global audioElement, autoCache, autoCacheEnabled, currentTrack, downloads,
          downloadsEnabled, noteAudioSourceChanged, playerNext, startAudio,
          toast */
/* exported directStreamURL, loadSequence, notePlaybackFailed,
            notePlaybackSucceeded, playerUpgradeDownloadedSource,
            playingObjectURL, resolveTrackSource, scheduleInterruptResume,
            cancelInterruptResume, trackLocalCached */

let playingObjectURL = "";   // audio 正在用的 blob 源; 换曲时 revoke (一首几十 MB, 攒着会撑爆手机内存)
let loadSequence = 0;        // 换源解析的过站号: 快速连切, 旧的解析回来直接作废
let playFailStreak = 0;      // 连挂计数: 出声即清零, 连挂 3 首停 (无限跳歌封顶)

/** 下载能力在线且这首歌已手动下载? (调用可能早于下载模块加载 —— boot
    顺序, typeof 兜住还没影子的全局, 不至于 ReferenceError。) */
function trackDownloaded(trackId) {
  return typeof downloadsEnabled !== "undefined" && downloadsEnabled
    && downloads && downloads.isDownloaded(trackId);
}

/** 自动缓存里有这首? (同上一道 typeof 兜底: 集成模块加载更晚)。 */
function autoCached(trackId) {
  return typeof autoCacheEnabled !== "undefined" && autoCacheEnabled
    && autoCache && autoCache.has(trackId);
}

/** 本地 (手动下载或自动缓存) 有这份音? 同步答, 只看索引不碰字节。 */
function trackLocalCached(trackId) {
  return trackDownloaded(trackId) || autoCached(trackId);
}

/** 流媒体直连地址: SW 见 ?direct 标记放行, 浏览器媒体栈自己连网络。 */
function directStreamURL(trackId) {
  return `/music/media/stream/${trackId}?direct=1`;
}

/** 本地音字节: 手动下载优先 (用户亲手下的不许被 LRU 清), 自动缓存次之。 */
async function localBlobFor(trackId) {
  if (trackDownloaded(trackId)) {
    const blob = await downloads.cachedBlob(trackId);
    if (blob) return blob;
  }
  if (autoCached(trackId)) return autoCache.blob(trackId);
  return null;
}

/** 曲目音频源: 本地有直读成 blob, 其余流媒体直连。 */
async function resolveTrackSource(trackId) {
  const blob = await localBlobFor(trackId);
  if (blob) return URL.createObjectURL(blob);
  return directStreamURL(trackId);
}

/** 补刀换缓存源 (1.8.59 恢复现场引入, 1.8.76 扩到常规切歌): 已下载/已
    自动缓存的歌在 loadTrack 里先按流占位 (同步赋址, iOS 在「没有出声的
    音频」那一瞬能把整页挂起, 不能等异步读), 这儿本地字节一就位就换
    blob —— 锁屏 SW 冻结掐不断, 断网也照播。onlyIfNotAudible: 流上已经
    出声的就按流听完, 不来回折腾。 */
async function playerUpgradeDownloadedSource(onlyIfNotAudible) {
  const track = currentTrack;
  const audio = audioElement();
  if (!track || !trackLocalCached(track.track_id)) return;
  if (!audio.src || audio.src.startsWith("blob:")) return;   // 已是缓存源
  const token = ++loadSequence;
  const blob = await localBlobFor(track.track_id);
  if (!blob || token !== loadSequence || currentTrack !== track) return;
  if (onlyIfNotAudible && !audio.paused && audio.readyState >= 2) return;
  const wasPaused = audio.paused;
  const at = audio.currentTime;          // 恢复态的待生效进度别丢
  const source = URL.createObjectURL(blob);
  if (playingObjectURL) URL.revokeObjectURL(playingObjectURL);
  playingObjectURL = source;
  audio.src = source;
  noteAudioSourceChanged();   // 不然 startAudio 会把新源再白重挂一次
  audio.currentTime = at;
  if (!wasPaused) startAudio().catch(() => {});
}

/** 出声了: 连挂计数清零 (playing 事件里调)。 */
function notePlaybackSucceeded() {
  playFailStreak = 0;
}

/** 播放挂了 (audio error 事件): 先试本地缓存救回当前曲, 没有就跳下一首
    强续; 连挂 3 首就停 —— 不封顶的话断网时连播会无限跳歌烧流量。 */
function notePlaybackFailed() {
  if (!currentTrack) return;
  playFailStreak += 1;
  if (playFailStreak >= 3) {
    playFailStreak = 0;    // 停下报一次; 下次点播放重新计
    toast("连着几首都播不了, 先停了");
    return;
  }
  recoverFailedPlayback();
}

/** 失败兜底 (1.8.76 第三刀): 当前曲先问本地字节 (流挂了, 缓存里可能有
    整曲), 有就原位置接着放; 没有就 playerNext(true) 强续 —— 这之前
    error 只弹一句「这首播放失败了」就地停住, 锁屏连播死在半路的帮凶。 */
async function recoverFailedPlayback() {
  const track = currentTrack;
  if (!track) return;
  const at = audioElement().currentTime;   // 挂掉时的位置, 缓存救回接着放
  const token = ++loadSequence;
  const blob = await localBlobFor(track.track_id);
  if (token !== loadSequence || currentTrack !== track) return;   // 已经切走了
  if (!blob) {
    playerNext(true);
    return;
  }
  const audio = audioElement();
  const source = URL.createObjectURL(blob);
  if (playingObjectURL) URL.revokeObjectURL(playingObjectURL);
  playingObjectURL = source;
  audio.src = source;
  noteAudioSourceChanged();
  if (at > 0 && track.duration_seconds) {
    audio.currentTime = Math.min(at, track.duration_seconds - 1);   // blob 是整曲, 旧位置接得上
  }
  startAudio().catch(() => {});
}

// ------------------------------------------------ 打断后自动续播 (1.8.78)

const INTERRUPT_RESUME_DELAYS = [2000, 5000, 10000, 20000];   // 之后每 30 秒一次

let interruptResumeTimer = 0;
let interruptResumeGeneration = 0;   // 换一代 = 旧的排程全作废 (作废了的重试自己会退场)

/** 系统打断后的小步续播重试 (audio-events 的 pause 认出打断时调)。
    iOS 打断 (来电/微信语音/Siri) 会把 Safari 的音频会话整个收走 —— 锁屏
    媒体控件跟着没影, 而页面不出声就拿不回控件 (网页没法凭空重挂),
    用户只能开 app 点播放。原生音乐 App 的惯例是打断一结束就接着播:
    这儿小步重试探 —— 打断还没结束 play() 会被拒, 一放行就续上, 出声
    那一刻锁屏控件自己回来 (1.8.70 rearmMediaSession 现成机制)。
    长打断时页面多半会被 iOS 挂起 (定时器冻着), 解锁/唤醒后到点的
    重试照常补一枪 —— 挂起期间页面冻死是救不了的, 醒得来就续得上。 */
function scheduleInterruptResume() {
  const generation = ++interruptResumeGeneration;
  // 打断那一刻的位置存一份: 重挂多次后元素时长可能一直是 NaN, 1.8.73
  // 的 seek 闸会误拦, 起播带着这份存档走 (startAudio 的 preferredAt)
  const at = audioElement().currentTime;
  const attempt = (tries) => {
    if (generation !== interruptResumeGeneration) return;   // 已作废
    startAudio(at).catch(() => {
      // 还在被打断 (或音频路由没回来): 稍后再试。2/5/10/20 秒小步快走
      // (微信语音/Siri 这类短打断), 之后每 30 秒一次 (来电), 约六分钟放弃
      if (generation !== interruptResumeGeneration || tries >= 15) return;
      const delay = tries < INTERRUPT_RESUME_DELAYS.length
        ? INTERRUPT_RESUME_DELAYS[tries] : 30000;
      interruptResumeTimer = setTimeout(() => attempt(tries + 1), delay);
    });
  };
  interruptResumeTimer = setTimeout(() => attempt(0), INTERRUPT_RESUME_DELAYS[0]);
}

/** 作废续播排程: 用户自己按了暂停 (明确要停) / 换曲 (别让重试把暂停切的
    歌放出来) / 已出声 (续上了)。 */
function cancelInterruptResume() {
  interruptResumeGeneration += 1;
  if (interruptResumeTimer) {
    clearTimeout(interruptResumeTimer);
    interruptResumeTimer = 0;
  }
}
