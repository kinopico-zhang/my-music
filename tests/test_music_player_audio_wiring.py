"""My Music 播放器 audio 接线测试: 起播/暂停统一入口与打断解锁, 切歌不改
播放状态, 进度显示基准 (1.8.74), 锁屏/后台连播三刀 (1.8.76), 打断后自动
续播 (1.8.78)。拆自 test_music_player_wiring.py (超 200 行按域分家)。"""

from tests.music_static_files import MUSIC_STATIC


def test_music_switch_keeps_playback_state():
    """1.8.66 切歌不改播放状态 (用户点名): 上下曲/锁屏/键盘/划封面切歌都
    带着原状态走, 只有自然播完 (ended) 传 true 强续, 点播照旧直接开播。
    1.8.68 修「播放被浏览器拦了」误报: 缓冲中 (readyState<3) 的多余点按
    直接无视不掐起播, 拒绝里只有真正的 NotAllowedError 才提示。"""
    queue_js = (MUSIC_STATIC / "js" / "music-player-queue.js").read_text(
        encoding="utf-8")
    events_js = (MUSIC_STATIC / "js" / "music-player-events.js").read_text(
        encoding="utf-8")
    audio_js = (MUSIC_STATIC / "js" / "music-player-audio-events.js").read_text(
        encoding="utf-8")
    assert "function playerNext(forceAutoplay) {" in queue_js
    assert "forceAutoplay === true || !audioElement().paused" in queue_js
    assert "loadTrack(track, !audio.paused);" in queue_js
    assert "playerNext(true);" in audio_js           # 自然播完强续, 其余保持原状态
    assert '$("#fp-next").addEventListener("click", playerNext);' in events_js
    assert queue_js.count("loadTrack(track, true);") == 2   # 点播/跳不可播照旧开播
    # 1.8.68 缓冲中的连点不掐起播 + 拒绝按类型分流 (AbortError 不再误报)
    assert "if (audio.readyState < 3) return;" in queue_js
    assert 'if (e && e.name === "NotAllowedError")' in queue_js
    assert 'toast("播放被浏览器拦了, 再点一次")' in queue_js   # 真拦截才提示
    # 1.8.71 被别的 App 打断后锁屏点播放没反应 (用户实报): iOS 把 audio 掐
    # 进「拒播」态, 直接 play() 不走 —— 非自发 pause 记成打断, 下次起播同源
    # load() 重挂解锁、进度放回; 自发暂停统一走 pauseAudio (好销旗)
    assert "let playInterrupted = false;" in audio_js
    assert "function startAudio(preferredAt)" in audio_js   # 起播入口搬来 audio-events (1.8.78 带存档位置参数)
    assert "audio.load();" in audio_js                  # 打断解锁: 同源重挂
    assert "function pauseAudio()" in audio_js
    assert "noteAudioPaused();" in audio_js             # pause 事件里认打断
    assert "function noteAudioSourceChanged" in audio_js
    # 换源即重置解锁态: loadTrack 一次; 1.8.76 源解析拆去 sources,
    # 补刀换源/失败救回各再来一次 (那儿两处)
    assert queue_js.count("noteAudioSourceChanged();") == 1
    sources_js = (MUSIC_STATIC / "js" / "music-player-sources.js").read_text(
        encoding="utf-8")
    assert sources_js.count("noteAudioSourceChanged();") == 2
    # 1.8.73 打断解锁补两道闸 (用户实报「在线的放不了, 下载过的能播」):
    # 换源自带的补刀 pause 不算打断; 解锁 seek 只在位置对得上当前源
    # 时长时放行 —— 陈值进度 seek 进不存在的位置 = 流媒体无声卡死
    assert "audioElement().readyState < 2) return;" in audio_js
    assert "isFinite(audio.duration)" in audio_js


def test_music_scrub_display_uses_library_duration():
    """1.8.74 修「拖完进度条剩余时间是 0, 还在继续播放」(用户实报): iOS 在
    流媒体上 seek 后 audio.duration 会翻脸 —— NaN 一阵, 或按 seek 那段
    206 响应估出个偏短的, 剩余时间提前见 0、进度条乱跳, 声音却照播。
    显示基准换成 playbackDuration(): 先信库里扫描器读文件得出的
    duration_seconds, 元素时长只在库里没有时兜底。"""
    state_js = (MUSIC_STATIC / "js" / "music-player-state.js").read_text(
        encoding="utf-8")
    audio_js = (MUSIC_STATIC / "js" / "music-player-audio-events.js").read_text(
        encoding="utf-8")
    session_js = (MUSIC_STATIC / "js" / "music-player-media-session.js"
                  ).read_text(encoding="utf-8")
    # 基准本体: 库时长优先, 元素时长兜底 (NaN/非正数不算数)
    assert "function playbackDuration" in state_js
    assert "currentTrack.duration_seconds" in state_js
    # 拖动预览/落定 seek/timeupdate 三处 + loadedmetadata 一处, 全走基准
    assert audio_js.count("const total = playbackDuration();") == 3
    assert "renderTimes(audio.currentTime, playbackDuration());" in audio_js
    assert "audio.duration || 0" not in audio_js   # 旧的直接信元素时长, 不许回来
    # 进度钳在 [0,1]: 库时长万一比实际音频长也不撑破进度条
    assert "Math.min(1, Math.max(0, audio.currentTime / total))" in audio_js
    # 锁屏进度同基准 (元素时长翻脸别把锁屏也带偏)
    assert "const duration = playbackDuration();" in session_js
    # 释放兜底: 指针捕获失灵时 pointerup 落不到垫子上, scrubbing 卡在
    # true 会冻住进度显示 —— 窗口级再接一次 (垫子上已释放过就空跑)。
    # 1.8.76 滑杆命中区增强拆去 music-player-slider (代码逐字节未动)
    slider_js = (MUSIC_STATIC / "js" / "music-player-slider.js").read_text(
        encoding="utf-8")
    assert 'window.addEventListener("pointerup", release);' in slider_js
    assert 'window.addEventListener("pointercancel", release);' in slider_js
    assert 'enhanceSliderTouch($("#fp-scrub"));' in audio_js   # 拆了还接着调


def test_music_autoplay_recovery_wiring():
    """1.8.76 修锁屏/后台不自动连播 (用户实报) 三刀接线:
    ① playerNext 跳过播不了的格式 —— tak/dsf/ape 夹在歌单里, 连播到那
    首就 error 就地停住 (预取早就跳, 队列推进一直没跳);
    ② error 不再只弹一句就停: 先试本地缓存救回原位置接着放, 不行跳下
    一首强续, 连挂 3 首封顶 (断网不会无限跳歌烧流量);
    ③ loadTrack 源同步落定 —— ended 到下一曲 play() 之间原本隔着一步
    Cache API 异步读, iOS 恰在「没有出声的音频」那一瞬能把整页挂起,
    微任务从此不回来 = 连播死在半路 (锁屏/后台尤甚); 已下载/已自动缓存
    的先按流占位, 缓存直读一就位就补刀换 blob (还没出声才换)。"""
    queue_js = (MUSIC_STATIC / "js" / "music-player-queue.js").read_text(
        encoding="utf-8")
    sources_js = (MUSIC_STATIC / "js" / "music-player-sources.js").read_text(
        encoding="utf-8")
    audio_js = (MUSIC_STATIC / "js" / "music-player-audio-events.js").read_text(
        encoding="utf-8")
    # ① 连播跳过播不了的 (与 playerStart 的 advanceToPlayable 同款循环)
    assert "while (track && !track.playable) track = queueAdvance(playQueue);" \
        in queue_js
    # ② error 兜底: 计数与救回都在 sources, 出声 (playing) 清零
    assert "if (currentTrack) notePlaybackFailed();" in audio_js
    assert "notePlaybackSucceeded();" in audio_js
    assert "let playFailStreak = 0;" in sources_js
    assert 'toast("连着几首都播不了, 先停了")' in sources_js
    assert "recoverFailedPlayback();" in sources_js
    assert "playerNext(true);" in sources_js        # 救不回: 强续下一首
    assert "Math.min(at, track.duration_seconds - 1)" in sources_js  # 原位置接上
    # ③ 源同步落定: loadTrack 不再 await, 本地有货补刀换 blob
    assert "await resolveTrackSource" not in queue_js
    assert "const source = prefetchedURL || directStreamURL(track.track_id);" \
        in queue_js
    assert "playerUpgradeDownloadedSource(true);" in queue_js
    assert "onlyIfNotAudible && !audio.paused && audio.readyState >= 2" \
        in sources_js       # 流上已出声就按流听完, 不来回折腾
    # 连切作废闸: 补刀换源/失败救回各自带过站号, 切走的曲目解析回来直接丢
    assert sources_js.count("const token = ++loadSequence;") == 2
    assert "currentTrack !== track" in sources_js


def test_music_interrupt_auto_resume_wiring():
    """1.8.78 修「后台播放被打断, 锁屏控制不了, 甚至不出现在锁屏」(用户
    实报): iOS 打断 (来电/微信语音) 会把 Safari 的音频会话整个收走 ——
    锁屏媒体控件跟着没影, 而页面不出声就拿不回控件 (网页没法凭空重挂),
    只能开 app 点播放。对策照原生音乐 App 的惯例: 打断一结束就接着播。
    pause 认出打断时排一串小步重试 (play 被拒 = 还在被打断, 一放行就续
    上, 出声那一刻 rearmMediaSession 把锁屏控件带回来); 手动暂停/换曲/
    已出声都作废排程。重挂多次后元素时长可能一直 NaN, 1.8.73 的 seek 闸
    会误拦 —— 起播带排程时记下的存档位置 (startAudio 的 preferredAt),
    打断旗也改成出声才销 (被拒的尝试下次仍走同源重挂解锁)。"""
    audio_js = (MUSIC_STATIC / "js" / "music-player-audio-events.js"
                ).read_text(encoding="utf-8")
    sources_js = (MUSIC_STATIC / "js" / "music-player-sources.js"
                  ).read_text(encoding="utf-8")
    queue_js = (MUSIC_STATIC / "js" / "music-player-queue.js").read_text(
        encoding="utf-8")
    # 排程本体在 sources (跟失败兜底作伴): 代际号作废 + 小步延时表
    assert "function scheduleInterruptResume" in sources_js
    assert "function cancelInterruptResume" in sources_js
    assert "const INTERRUPT_RESUME_DELAYS" in sources_js
    assert "generation !== interruptResumeGeneration" in sources_js
    assert "startAudio(at).catch" in sources_js   # 被拒 = 还在被打断, 再试
    # 接线三处: 认出打断就排程; 手动暂停作废 (要停就停); 出声作废 (续上了)
    assert "playInterrupted = true;\n  scheduleInterruptResume();" in audio_js
    assert "cancelInterruptResume();\n  pauseByApp = true;" in audio_js
    assert audio_js.count("cancelInterruptResume();") == 2   # pauseAudio + playing
    # 换曲作废: 在途重试别把暂停切的歌自己放出来 (重试带的是旧曲位置)
    assert "cancelInterruptResume();" in queue_js
    # 打断旗出声才销 (被拒不销, 下次重试仍走重挂解锁); 存档位置信得过
    assert "playInterrupted = false;   // 出声在望, 打断态正式销" in audio_js
    assert "const at = preferredAt != null ? preferredAt : audio.currentTime;" \
        in audio_js
    assert "(preferredAt != null\n      || (isFinite(audio.duration)" in audio_js
