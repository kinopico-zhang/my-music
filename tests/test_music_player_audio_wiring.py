"""My Music 播放器 audio 接线测试: 起播/暂停统一入口, 切歌不改播放状态,
进度显示基准 (1.8.74), 锁屏/后台连播三刀 (1.8.76)。拆自
test_music_player_wiring.py (超 200 行按域分家); 打断/幽灵一域 (1.8.83
撤自动续播起) 1.8.86 拆去 test_music_player_interrupt_wiring.py。"""

from pathlib import Path

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
    ② error 不再只弹一句就停: 先试本地缓存救回原位置接着放, 不行就地
    挂起等信号重试 —— 跳不跳下一首用户定 (1.8.96 撤强续与连挂封顶);
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
    # ② error 兜底: 救回/挂起都在 sources, 出声 (playing) 销挂起
    assert "if (currentTrack) notePlaybackFailed();" in audio_js
    assert "notePlaybackSucceeded();" in audio_js
    assert "recoverFailedPlayback();" in sources_js
    assert "playerNext(" not in sources_js          # 1.8.96 救不回不跳歌: 挂起重试
    assert "playFailStreak" not in sources_js       # 连挂计数/强续封顶退役
    assert "Math.min(at, track.duration_seconds - 1)" in sources_js  # 原位置接上
    # ③ 源同步落定: loadTrack 不再 await, 本地有货补刀换 blob
    # (1.8.87 ① 补刀带上起播意图 —— 见 test_music_offline_transition_wiring)
    assert "await resolveTrackSource" not in queue_js
    assert "const source = prefetchedURL || directStreamURL(track.track_id);" \
        in queue_js
    assert "playerUpgradeDownloadedSource(true, autoplay);" in queue_js
    assert "onlyIfNotAudible && !audio.paused && audio.readyState >= 2" \
        in sources_js       # 流上已出声就按流听完, 不来回折腾
    # 连切作废闸: 补刀换源/失败救回各自带过站号, 切走的曲目解析回来直接丢
    assert sources_js.count("const token = ++loadSequence;") == 2
    assert "currentTrack !== track" in sources_js


def test_music_offline_transition_wiring():
    """1.8.87 修「开车时一首放完, 下一首就停在暂停态」(用户实报: 歌都缓存
    在本地, 服务日志实锤整个车程零请求 —— 缓存歌全靠本地 blob 在播, 断点
    全在切歌那一拍)。两刀接线: ① 换源竞态死锁 —— 预取没接上的缓存歌先按
    流占位, startAudio 的 play() 在流上挂着 (断网永远等不到数据), 几毫秒
    后补刀换 blob 会把挂起的 play() 掐成 AbortError 吞掉, 而 wasPaused 读
    到的还是假 true (play 挂起≠在播) 不再重启 —— 歌对了源对了却永远暂
    停, 连 error 都没有 (元素好好的, 只是没人再喊播)。起播意图带进补刀,
    换完源自己重启。② error 恢复 (用户点名「服务不稳定也要有恢复措施」,
    1.8.96 再点名「网络不好也别直接跳过, 跳过是用户才能定的」): 本地有
    整曲立刻救回, 没有就地挂起等信号 (计时一次 + 回前台即刻重试; 页面
    不在前台绝不自己开声, 1.8.83 撤自动续播的规矩不破) —— 出错一律不
    自动跳歌 (WebKit 网络失败常报 code 4, 信号差与文件烂分不清, 分家收摊)。"""
    queue_js = (MUSIC_STATIC / "js" / "music-player-queue.js").read_text(
        encoding="utf-8")
    sources_js = (MUSIC_STATIC / "js" / "music-player-sources.js"
                  ).read_text(encoding="utf-8")
    # ① 起播意图带进补刀换源; 换完自己重启 (wasPaused 单独说了不算)
    assert "playerUpgradeDownloadedSource(true, autoplay);" in queue_js
    assert "if (!wasPaused || resumeAfterSwap) startAudio().catch(() => {});" \
        in sources_js
    # ② 出错不跳歌 (1.8.96): 缓存有立刻救回, 没有挂起等信号; 错码分家撤了
    assert "audioElement().error" not in sources_js
    assert "recoverFailedPlayback();" in sources_js
    assert "armNetworkRetry();" in sources_js
    assert 'toast("信号断了, 回来会自动接着放")' in sources_js
    # 挂起重试: 计时一次 + 回前台即刻; 隐着不开声; 重试先缓存后流, 绝不跳歌
    assert "function retryAfterNetworkDrop" in sources_js
    assert "if (!pendingNetworkRetry || document.hidden) return;" in sources_js
    assert 'document.addEventListener("visibilitychange"' in sources_js
    # 重试先问缓存 (有就换缓存源), 没有同一首再拉流 —— 全文件不跳歌
    assert "playerNext(" not in sources_js
    # 出声/换曲: 挂起作废 (playing 事件与 loadTrack 两头销)
    assert "networkRetryToasted = false;" in sources_js
    assert "discardNetworkRetry();" in queue_js
    # 1.8.96 连挂封顶退役后的防转圈: 缓存救回出手打点, 刚救回又挂转挂起
    assert "let lastRecoverAt = 0;" in sources_js
    assert "Date.now() - lastRecoverAt < 3000" in sources_js


def test_music_background_handoff_wiring():
    """1.8.100 修「后台连播第二首没声音, 进度条还在走, 过一阵锁屏卡片
    也没了」(用户实报, 全程零服务端请求 = playing 从未落地, 锁屏进度是
    浏览器自估的): iOS 在「上一曲停了、下一曲还没出声」的空窗里能把
    整页挂起 —— 1.8.76 把 ended→play() 做成同步也躲不开, 出声在 WebKit
    内部异步落地, 偶发先被冻住。改趁还剩零点几秒、声音还在响时先切
    (会话活着换源即接上, 与补刀换 blob 同机理): 裁决拆纯模块 handoff.js
    (node 直测), 驱动住 queue, timeupdate 每拍问一嘴; 前台不切 (自然
    播完零裁切), ended 路保底 (时长不准没触发走老路)。"""
    handoff_js = (MUSIC_STATIC / "js" / "handoff.js").read_text(encoding="utf-8")
    queue_js = (MUSIC_STATIC / "js" / "music-player-queue.js").read_text(
        encoding="utf-8")
    audio_js = (MUSIC_STATIC / "js" / "music-player-audio-events.js").read_text(
        encoding="utf-8")
    # 裁决本体 (纯逻辑): 窗口 0.45s / 复位线 1s, 状态机一处收口
    assert "const HANDOFF_WINDOW_S = 0.45;" in handoff_js
    assert "const HANDOFF_RESET_S = 1;" in handoff_js
    assert "function shouldHandoffEarly" in handoff_js
    assert "module.exports" in handoff_js
    # 驱动: 元素时长优先 (它知道自己何时完), 库时长兜底; 还在响 = 强续
    assert "function maybeHandoffEarly" in queue_js
    assert "isFinite(audio.duration) && audio.duration > 0" in queue_js
    assert "hidden: document.hidden," in queue_js
    assert "repeatOne: !!(playQueue && playQueue.repeat === \"one\")" in queue_js
    assert "if (verdict.handoff) playerNext(true);" in queue_js
    # 接线: timeupdate 每拍问一嘴 (停更 = 页面冻结, 问不着, ended 保底)
    assert "maybeHandoffEarly();" in audio_js
    # 门禁收编: tsc 类型检查 + c8 覆盖率都认这个纯模块
    root = Path(__file__).resolve().parent.parent
    assert "app/music/static/js/handoff.js" in (root / "tsconfig.json"
                                                ).read_text(encoding="utf-8")
    assert "app/music/static/js/handoff.js" in (root / "run_tests.sh"
                                                ).read_text(encoding="utf-8")
