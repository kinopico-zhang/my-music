"""My Music 播放器打断/幽灵播放接线测试: 会话被别的 app (来电/视频) 夺走
后的各副面孔 —— 拒播态 (play 被拒)、没收 pause (幽灵播放)、页面冻结。
拆自 test_music_player_audio_wiring.py (超 200 行按域分家)。"""

from tests.music_static_files import MUSIC_STATIC


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


def test_music_ghost_probe_at_start_and_thaw_wiring():
    """1.8.86 修「1.8.85 还是没啥用」(用户实报第三轮): 服务日志实锤 —— 看
    长视频期间 iOS 把页面整个冻结 (viewport 医生攒批只有 3 秒, 事件却迟到
    8 分钟), 控制中心按键落进来时根本没有 JS 在跑, 光修按键处理路白修。
    转向两刀: ① 幽灵探针挪进起播入口本体 —— 元素自称在播但 timeupdate
    停更超 5 秒即判幽灵直接重挂 (1.8.85 只在暂停键路上设伏, 用户直接点
    播放就绕过去了); ② 页面解冻回前台自愈 —— visibilitychange 时幽灵
    (停更超 30 秒, 门槛抬高防后台网络卡顿误伤) 归位成诚实暂停 (pauseAudio
    幽灵分支立旗, pause 事件链重申锁屏键位)。冻结中的页面救不了 (平台限
    制), 回到应用点一下播放即真声。"""
    audio_js = (MUSIC_STATIC / "js" / "music-player-audio-events.js"
                ).read_text(encoding="utf-8")
    # ① 起播入口本体探幽灵: 自称在播 + 停更超 5 秒 = 直接重挂
    assert "if (playInterrupted ||" in audio_js
    assert "(!audioElement().paused && Date.now() - lastTimeupdateAt > 5000))" \
        in audio_js
    # ② 解冻自愈: 回前台 + 幽灵 (30 秒门槛) → pauseAudio 归位
    assert 'document.addEventListener("visibilitychange"' in audio_js
    assert 'document.visibilityState === "visible"' in audio_js
    assert "Date.now() - lastTimeupdateAt > 30000) pauseAudio();" in audio_js
