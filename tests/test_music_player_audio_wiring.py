"""My Music 播放器 audio 接线测试: 起播/暂停统一入口与打断解锁, 切歌不改
播放状态, 进度显示基准 (1.8.74)。拆自 test_music_player_wiring.py
(超 200 行按域分家)。"""

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
    assert "function startAudio()" in audio_js          # 起播入口搬来 audio-events
    assert "audio.load();" in audio_js                  # 打断解锁: 同源重挂
    assert "function pauseAudio()" in audio_js
    assert "noteAudioPaused();" in audio_js             # pause 事件里认打断
    assert "function noteAudioSourceChanged" in audio_js
    assert queue_js.count("noteAudioSourceChanged();") == 2   # 换源即重置解锁态
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
    # true 会冻住进度显示 —— 窗口级再接一次 (垫子上已释放过就空跑)
    assert 'window.addEventListener("pointerup", release);' in audio_js
    assert 'window.addEventListener("pointercancel", release);' in audio_js
