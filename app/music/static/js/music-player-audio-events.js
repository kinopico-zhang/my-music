// music-player-audio-events — My Music 播放器 audio 元素事件 (出声计数/进度/播完切歌/兜底存档)。
// 拆自 music-player.js (结构化重构: 按逻辑再切一刀, 前半按钮事件留在 music-player-events)。
// 1.8.70 起播即重挂锁屏键位: iOS 只认「出声那一刻」挂的键位 (见
// music-player-media-session 的 1.8.70 注释), play/playing 各挂一遍。
// 1.8.71 起播/暂停统一入口搬来本模块: iOS 被别的 App 打断 (来电/微信语音)
// 会把 audio 掐进「拒播」态, 直接 play() 不走 —— 非自发的 pause 记成打断,
// 下次起播先同源 load() 重挂解锁, 进度放回原位。
// 1.8.73 解锁补两道闸: 换源补刀的 pause 不算打断; 解锁 seek 只在位置对得上
// 当前源时长时放行 (陈值 seek 卡死流媒体)。
// 1.8.74 进度显示不再信 audio.duration (流上 seek 后会翻脸): 换 playbackDuration() 库时长。
// 1.8.76 播放挂了不再只弹一句就停: error 兜底交给 notePlaybackFailed
// (缓存救回/跳下一首/连挂 3 首封顶); 滑杆命中区增强拆去 music-player-slider。
// 1.8.78 加过「打断后自动续播」, 1.8.83 撤了 (自动恢复抢别的 app 声音)。
// 1.8.84/85/86 会话被别的 app 夺走后的三副面孔, 都修: ① 裸 play() 被拒
// (AbortError 除外) 就当被打断重挂再试; ② 元素没收 pause —— paused 一直
// false、声音没了、timeupdate 停更: 停更超 5 秒即判幽灵记打断; ③ 幽灵
// 不止暂停键一条路 — 起播入口直接探, 解冻回前台也自愈 (1.8.86)。
"use strict";
/* global $, audioElement, currentTrack,
          enhanceSliderTouch, formatPlaybackTime, highlightActiveLyric,
          maybeHandoffEarly, notePlaybackFailed, notePlaybackSucceeded,
          playbackDuration,
          playQueue, playRecorded: writable, playerIsPlaying, playerNext,
          rearmMediaSession, savePlayerState, updateMediaSession,
          scrubbing: writable, syncPositionState, updatePlayButtons */
/* exported bindPlayerAudioEvents, noteAudioSourceChanged, pauseAudio,
            startAudio */

// ------------------------------------------------ 起播/暂停 (audio 元素的主人)

let pauseByApp = false;       // 我们自己掐的 pause (按钮/锁屏/换源) —— pause 事件好认出系统打断
let playInterrupted = false;  // 系统掐的暂停 (别的 App 抢声音): 下次起播先同源重挂解锁
let lastTimeupdateAt = 0;     // 元素最近一次报 timeupdate 的时刻 (幽灵播放探针, 会话被夺/页面冻结后停更)

function startAudio() {
  // 1.8.86 幽灵探针在起播入口本体: 自称在播但 timeupdate 停更超 5 秒 =
  // 会话早被夺走/页面冻过, 裸 play() 只会假成功没声 —— 直接重挂, 全入口盖住。
  if (playInterrupted ||
      (!audioElement().paused && Date.now() - lastTimeupdateAt > 5000)) {
    return unlockPlay();
  }
  // 1.8.84 裸 play() 被拒 (AbortError 除外 —— 换源/暂停的正常接力): 元素
  // 被掐进拒播态而打断旗没立上 —— 当被打断重挂再试一把, 再拒照实抛。
  // 只在明确起播请求后兜, 绝不自己开声 (1.8.83 撤自动续播的规矩不破)。
  return audioElement().play().catch((error) => {
    if (error && error.name === "AbortError") throw error;
    playInterrupted = true;
    return unlockPlay();
  });
}

/** 打断解锁 (1.8.71 机制本体): 被打断后 iOS 把 audio 掐进「拒播」态, 直接
    play() 要么被拒要么挂着不出声 —— 同源 load() 重挂才肯走。进度放回要过
    闸: 位置在当前源时长内 (时长要在 load() 前读, load 一跑就归零)。 */
function unlockPlay() {
  const audio = audioElement();
  const at = audio.currentTime;
  const resumable = at > 0 && isFinite(audio.duration) && at < audio.duration - 1;
  audio.load();
  if (resumable) audio.currentTime = at;
  return audio.play().then((result) => {
    playInterrupted = false;   // 出声在望, 打断态正式销
    return result;
  });
}

/** 自己发起的暂停 (按钮/锁屏暂停键): 记一笔, pause 事件来时才能认出
    「不是我们掐的 = 系统打断」。已在暂停态就不动。幽灵播放例外 (1.8.85):
    会话被夺时元素可能没收 pause —— paused 一直 false、timeupdate 停更,
    这时来的暂停键是用户在纠正幽灵态, 记成打断 (下次点播放走重挂)。 */
function pauseAudio() {
  const audio = audioElement();
  if (audio.paused) return;
  if (Date.now() - lastTimeupdateAt > 5000) playInterrupted = true;
  else pauseByApp = true;
  audio.pause();
}

/** pause 事件到了: 自发的销旗; 系统掐的 (来电/别的 App) 记成打断, 下次起
    播走同源重挂解锁 (1.8.71)。只立旗不自动恢复 (1.8.83 撤)。播着切歌时
    Safari 给旧源补发的 pause 不算 —— 新源未装载 (readyState 没到元数据)。 */
function noteAudioPaused() {
  if (pauseByApp) {
    pauseByApp = false;
    return;
  }
  if (audioElement().readyState < 2) return;   // 新源未装载的 pause = 换源补刀
  playInterrupted = true;
  // 打断一落地就重申锁屏键位/元数据: iOS 交出会话后可能丢 action handlers
  updateMediaSession();
}

/** 换了音频源 (loadTrack 换曲/缓存直读升级): 打断解锁态作废, 不然
    startAudio 会把刚挂好的源再白重挂一次。 */
function noteAudioSourceChanged() {
  playInterrupted = false;
}

function bindPlayerAudioEvents(audio) {
  // 滑杆命中区增强 (进度条轨道 7px 手指按不准, 外面垫 28px 拖拽面):
  // 1.8.76 拆去 music-player-slider, 代码逐字节未动
  enhanceSliderTouch($("#fp-scrub"));

  const scrubber = $("#fp-scrub");
  // 时间文案照参考图: 左 = −已播, 右 = −剩余 (倒数式, 两边都带负号)
  const renderTimes = (current, total) => {
    $("#fp-time-cur").textContent = `-${formatPlaybackTime(current)}`;
    $("#fp-time-total").textContent =
      `-${formatPlaybackTime(Math.max(0, (total || 0) - current))}`;
  };
  scrubber.addEventListener("input", () => {
    scrubbing = true;
    const total = playbackDuration();
    const time = total * Number(scrubber.value) / 1000;
    renderTimes(time, total);
    scrubber.style.setProperty("--fill", `${scrubber.value / 10}%`);
  });
  const applyScrub = () => {
    if (!scrubbing) return;
    scrubbing = false;
    const total = playbackDuration();
    audio.currentTime = total * Number(scrubber.value) / 1000;
  };
  scrubber.addEventListener("change", applyScrub);
  scrubber.addEventListener("touchend", applyScrub);

  // 解冻自愈 (1.8.86, 实报第三轮): 看长视频期间 iOS 冻结整个页面, 控制中
  // 心按键没人接 (viewport 医生事件迟到 8 分钟为证) —— 冻结的页面救不了,
  // 回前台这刻把幽灵播放归位成诚实暂停, 点播放即真声。30 秒门槛防误伤。
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" &&
        !audio.paused && Date.now() - lastTimeupdateAt > 30000) pauseAudio();
  });

  audio.addEventListener("playing", () => {
    rearmMediaSession();   // 1.8.70 iOS 认出声那刻的键位, 重挂 (幂等)
    notePlaybackSucceeded();   // 1.8.76 出声了: 连挂计数清零
    // 真正出声了才算"听过" (恢复现场直接暂停的不算); 暂停续播不重复报
    if (playRecorded || !currentTrack) return;
    playRecorded = true;
    fetch("/music/api/plays", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ track_id: currentTrack.track_id }),
    }).catch(() => { /* 记不上不挡听歌 */ });
  });
  audio.addEventListener("play", () => {
    updatePlayButtons();
    rearmMediaSession();   // 1.8.70 play 一落地就重挂, 缓冲久也不怕 (playing 再兜一次)
  });
  audio.addEventListener("pause", () => {
    updatePlayButtons();
    savePlayerState();
    noteAudioPaused();   // 1.8.71 区分自发暂停与系统打断 (打断 → 起播先解锁)
  });
  audio.addEventListener("loadedmetadata", () => {
    renderTimes(audio.currentTime, playbackDuration());
    syncPositionState();
  });
  // 锁屏/控制中心的进度是浏览器拿「位置 + 流逝时间 × 速率」估的: 暂停、
  // 跳句、拖动、变速后不重报, iPhone 锁屏进度条就会自顾自走。有动静都重报。
  for (const eventName of ["play", "pause", "seeked", "ratechange"]) {
    audio.addEventListener(eventName, syncPositionState);
  }
  audio.addEventListener("timeupdate", () => {
    lastTimeupdateAt = Date.now();   // 幽灵播放探针 (1.8.85): 还在出声推进
    maybeHandoffEarly();             // 后台连播提前接力 (1.8.100): 趁还响着切
    // 显示基准走 playbackDuration (库时长): 元素时长在 iOS 流上 seek 后
    // 会翻脸 (NaN / 偏短), 信它就是「剩余 -0:00 歌照播」; 进度钳在 [0,1],
    // 库里时长万一比实际音频长也不撑破进度条
    const total = playbackDuration();
    const progress = total > 0
      ? Math.min(1, Math.max(0, audio.currentTime / total)) : 0;
    $("#mini-progress").style.width = `${Math.round(progress * 100)}%`;
    if (!scrubbing) {
      const scrubber = $("#fp-scrub");
      scrubber.value = String(Math.round(progress * 1000));
      scrubber.style.setProperty("--fill", `${Math.round(progress * 100)}%`);
      renderTimes(audio.currentTime, total);
    }
    syncPositionState();
    highlightActiveLyric();
  });
  audio.addEventListener("ended", () => {
    if (playQueue && playQueue.repeat === "one") {   // 单曲循环: 回开头重播
      audio.currentTime = 0;
      startAudio().catch(() => {});
      return;
    }
    playerNext(true);   // 1.8.66 自然播完强续播 (其余切歌都保持原播放状态)
  });
  audio.addEventListener("error", () => {
    // 兜底在 music-player-sources (notePlaybackFailed): 1.8.96 起出错一律
    // 不跳歌 —— 缓存救回或挂起重试, 跳过是用户才能定的
    if (currentTrack) notePlaybackFailed();
  });

  window.addEventListener("pagehide", savePlayerState);
  setInterval(() => { if (playerIsPlaying()) savePlayerState(); }, 5000);
}
