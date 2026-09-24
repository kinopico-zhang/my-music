"""My Music 播放器 audio 接线测试: 起播/暂停统一入口与打断解锁, 切歌不改
播放状态, 进度显示基准 (1.8.74), 锁屏/后台连播三刀 (1.8.76)。拆自
test_music_player_wiring.py (超 200 行按域分家); 1.8.78 的打断后自动
续播 1.8.83 撤了 (见末尾撤除断言)。"""

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
    assert "function startAudio() {" in audio_js   # 起播入口 (1.8.83 起无参: 位置参数随自动续播撤了)
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


def test_music_interrupt_auto_resume_removed():
    """1.8.83 撤「打断后自动续播」(用户实报: 切到别的 app 看视频, 这边
    自动恢复的音乐会把视频的声音抢走)。1.8.78 的整套小步重试排程
    (INTERRUPT_RESUME_DELAYS / scheduleInterruptResume / cancelInterruptResume)
    全数退场 —— 打断后想接着播自己点 (锁屏键/回 app 点播放)。1.8.71 的
    同源重挂解锁原样保留: 认出打断只立旗 (playInterrupted), 下次手动起播
    仍先 load() 重挂、进度过闸放回 (1.8.73 的 seek 闸还在)。"""
    audio_js = (MUSIC_STATIC / "js" / "music-player-audio-events.js"
                ).read_text(encoding="utf-8")
    sources_js = (MUSIC_STATIC / "js" / "music-player-sources.js"
                  ).read_text(encoding="utf-8")
    queue_js = (MUSIC_STATIC / "js" / "music-player-queue.js").read_text(
        encoding="utf-8")
    # 排程本体全撤: 三个模块里都不许再出现
    for js in (audio_js, sources_js, queue_js):
        assert "scheduleInterruptResume" not in js
        assert "cancelInterruptResume" not in js
        assert "INTERRUPT_RESUME_DELAYS" not in js
        assert "interruptResumeGeneration" not in js
    # 认出打断只立旗, 不排任何自动恢复 (1.8.71 的解锁态还在)
    assert "playInterrupted = true;" in audio_js
    assert "audio.load();" in audio_js              # 解锁: 同源重挂保留
    assert "const resumable = at > 0" in audio_js   # 进度过闸放回保留 (1.8.73)
    # startAudio 无参 (存档位置参数是给排程重试用的, 一起退场)
    assert "startAudio(at)" not in audio_js
    assert "startAudio(preferredAt)" not in audio_js


def test_music_rejected_play_retry_wiring():
    """1.8.84 修「看完别的 app 的视频, 锁屏点播放没反应」(用户实报): 会话
    被夺时掐我们的 pause 事件可能没跑到 JS (页面冻结/键位被丢), 打断旗没
    立上、元素却进了拒播态 —— 锁屏 play 落进来只是一次裸 play(), 被拒后
    被媒体的 catch(() => {}) 静默吞掉, 再没下文 (服务日志实锤: 锁屏点播放
    后连重挂会发的重新拉流请求都没有)。对策: startAudio 被拒 (AbortError
    除外 —— 换源/暂停的正常接力) 就当被打断, 重挂 (unlockPlay, 1.8.71
    机制抽成本体) 再试一把; 打断一落地就重申锁屏键位/元数据 (iOS 交出
    会话后可能丢 action handlers, 不重挂点不进来)。只兜明确起播请求,
    不自己开声 —— 1.8.83 撤自动续播的规矩不破。"""
    audio_js = (MUSIC_STATIC / "js" / "music-player-audio-events.js"
                ).read_text(encoding="utf-8")
    # 起播被拒 → 当打断 → 重挂再试; 旗在 (pause 认出打断 / 上次被拒) 直走重挂
    assert "function unlockPlay()" in audio_js
    assert 'if (error && error.name === "AbortError") throw error;' in audio_js
    assert audio_js.count("return unlockPlay();") == 2
    # 认出打断即重申锁屏键位/元数据
    assert "playInterrupted = true;\n  // 打断一落地就重申锁屏键位" in audio_js
    assert "updateMediaSession();" in audio_js


def test_music_ghost_playback_detection_wiring():
    """1.8.85 修「控制中心点暂停再点播放, 进度走却没声」(用户实报第二轮):
    会话被夺时元素可能根本没收 pause —— paused 一直 false、声音没了、
    timeupdate 停更 (控制中心还显示正在播放, 进度还是外推的假走)。用户
    第一次点「暂停键」其实是纠正幽灵态, 但旧代码记成自发暂停 → 第二次
    点播放只是一次裸 play(), 元素照旧幽灵播放 (服务日志实锤: 两次点击
    连重挂会发的重新拉流请求都没有)。对策: timeupdate 打时刻戳, 暂停键
    来时停更超 5 秒 (页面冻结/时钟停走都算) 即判幽灵 —— 直接记打断, 下
    次点播放走重挂解锁 (1.8.71 验证过的路子)。"""
    audio_js = (MUSIC_STATIC / "js" / "music-player-audio-events.js"
                ).read_text(encoding="utf-8")
    # 探针: timeupdate 里打时刻戳
    assert "let lastTimeupdateAt = 0;" in audio_js
    assert "lastTimeupdateAt = Date.now();" in audio_js
    # 暂停分流: 停更超 5 秒 = 幽灵 (记打断, 不记自发); 正常暂停照旧
    assert "if (Date.now() - lastTimeupdateAt > 5000) playInterrupted = true;" \
        in audio_js
    assert "else pauseByApp = true;" in audio_js
