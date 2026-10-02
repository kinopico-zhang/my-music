"""My Music 分享页播放器接线测试 (1.8.130 增, 用户点名「优化分享播放页面,
样式和普通播放页面一样, 3d切换封面, 按钮也跟普通播放界面保持一致」):
分享页全屏播放器整块对齐应用 —— 容器/控件栈/三键图标与 music.html 的
#full-player 同构, 样式直接引应用的 music-player.css/music-queue.css,
3D 舞台与队列模型整用应用的件, 分享侧只覆盖封面取址 (走 token 公开
路由) 和只读的队列视图。静态文本断言 (页面接线); 队列纯逻辑在
test_music_queue_rules, 舞台本体在 test_music_art_stage, 应用侧同款
接线在 test_music_wiring_player。"""

from tests.music_static_files import (MUSIC_STATIC, share_page_js,
                                      share_page_shell)


def test_music_share_player_wiring():
    """播放页同款: 三卡 3D 舞台 + 传输三键站进度条上方 + 底排三态循环/
    歌词/队列 + 待播队列面板 + 回到当前句。"""
    share = share_page_shell()               # markup + css
    # 容器换 #full-player (app 同名同款), 三卡舞台: 中卡 + 两侧邻卡,
    # 卡下各跟一条音质行 (1.8.130 起, 与 music.html 同排布)
    for frag in ['<div id="full-player" hidden>', 'id="fp-bg-img"',
                 'id="fp-art-prev" class="art-card"',
                 'id="fp-art-next" class="art-card"',
                 'id="fp-art" class="art-card"',
                 'id="fp-quality-prev" class="art-quality"',
                 'id="fp-quality-next" class="art-quality"',
                 'id="fp-quality" class="art-quality"',
                 'id="fp-grab"', 'id="fp-play"', 'id="fp-prev"', 'id="fp-next"',
                 'id="fp-scrub"', 'id="fp-mode-btn"', 'id="fp-lyrics-btn"',
                 'id="fp-queue-btn"', 'id="fp-queue"', 'id="queue-list"',
                 'id="fq-count"', 'id="lyrics-resume"', 'id="toast"']:
        assert frag in share, f"share.html 缺 {frag}"
    # 样式直接引应用那份 (不再自己 fork 一整份), 分享侧补丁收在
    # share-viewer-player.css; 借的应用脚本六枚纯件挂了号 (wiring_library)
    for frag in ['css/music-player.css?v=26', 'css/music-queue.css?v=6',
                 'css/music-player-quality.css?v=1',
                 'css/share-viewer-player.css?v=11',
                 "js/music-player-art-stage.js?v=9", "js/player-queue.js?v=4",
                 "js/music-common.js?v=23", "js/music-player-quality.js?v=2",
                 "js/music-player-slider.js?v=1",
                 "js/share/share-viewer-stage.js?v=2",
                 "js/share/share-viewer-queue.js?v=1"]:
        assert frag in share, f"share.html 缺引用 {frag}"
    # 控件栈次序与 app 一致: 传输三键 (.fp-controls) 在进度行
    # (.fp-transport) 上方, 底排三键 (.fp-actions) 在下
    assert share.index('<div class="fp-controls">') \
        < share.index('<div class="fp-transport">') \
        < share.index('<div class="fp-actions">')
    # 1.8.37 旧布局退役: 中排键/键行/歌手照/随机循环各一颗 都撤了
    for gone in ['id="fp-mid"', 'id="fp-shuffle"', 'id="fp-repeat"',
                 'id="fp-artist-art"', 'class="fp-scrub-row"', 'class="fp-keys"']:
        assert gone not in share, f"旧布局 {gone} 该撤了"
    # 三态循环/歌词/队列 三键图标与 music.html 同款 (mode 是 1.8.121 的
    # 共窗环, 逐字节同 path; 歌词/队列键 36/28px 同款)
    mode_path = "M73.44 667.21a44.45 44.45 0 0 1 -12.12 1.64"
    assert share.count(mode_path) == 1      # 循环键用迭代过的环 (JS 换图标)
    assert 'viewBox="-1.72 -154.37 1329.4 1329.4" width="24"' in share


def test_music_share_player_stage_wiring():
    """3D 封面舞台 (用户点名「3d切换封面」): 整用应用的
    music-player-art-stage, 分享侧只覆盖封面/音质两处取址。"""
    share_all = share_page_shell() + share_page_js()
    stage = (MUSIC_STATIC / "js" / "share" / "share-viewer-stage.js"
             ).read_text(encoding="utf-8")
    # 封面取址覆盖: 全局函数属性改写, 走分享 token 的公开路由 + 裂图退占位
    for frag in ["stageCardSrc = (img, track) => {",
                 "img.src = track ? artURL(track) : PLACEHOLDER_ARTWORK;"]:
        assert frag in stage, f"share 舞台覆盖缺 {frag}"
    # 音质取址同法覆盖 (应用口要会话): 后端 /share/{token}/quality 公开口;
    # 空转钩子撤了 —— 三条跟卡飞/按曲缓存整用 music-player-quality
    assert ("qualityURL = (track) => "
            "`/music/share/${token}/quality/${track.track_id}`;") in stage
    assert "function poseQualityStrips() {}" not in stage
    assert "function fillStageQuality" in share_all
    assert "void fillStageQuality();" in share_all   # 换曲铺场 (playback)
    # 舞台接线: events 里 initArtStage; 切歌走 playerNext/playerPrevious
    assert "initArtStage();" in share_all
    # 中卡本尊在换曲时直接挂 src (app 同款: 舞台只管两侧邻卡)
    assert 'const art = $("#fp-art");' in share_all
    assert "art.src = artURL(track);" in share_all
    assert "art.src = PLACEHOLDER_ARTWORK;" in share_all
    # 旧 1.8.19 平面滑切退役: 切歌动画归舞台 (起跳/交班)
    for gone in ["bindCoverSwipe", "art-in-next", "art-in-prev"]:
        assert gone not in share_all, f"{gone} 该撤了 (3D 舞台接管)"


def test_music_share_player_queue_wiring():
    """队列模型换应用的 player-queue.js: 三态循环一键 + 待播队列面板
    点行跳播; 上下曲/播完推进与 app 同款语义。"""
    share_all = share_page_shell() + share_page_js()
    # 开局建队列 (只收可播的), 默认列表循环 (app playerStart 同款)
    assert "playQueue = createPlayQueue(data.tracks.filter((t) => t.playable));" \
        in share_all
    assert 'playQueue.repeat = "all";' in share_all
    # 三态循环一键: 切一下报一下态, 图标跟着换 (app 1.8.89 同款)
    for frag in ["const mode = queueCyclePlayMode(playQueue);",
                 'toast(mode === "all" ? "列表循环" : mode === "one" ? "单曲循环" : "随机循环");',
                 '$("#fp-mode-btn").innerHTML = shuffle ? ICON_SHUFFLE',
                 ": one ? ICON_REPEAT_ONE : ICON_REPEAT;"]:
        assert frag in share_all, f"三态循环缺 {frag}"
    # 上一首播过 3 秒先回本曲开头; 队尾列表循环回绕, 走不下去报播完了
    for frag in ["function playerPrevious", "if (audio.currentTime > 3) {",
                 "function playerNext",
                 'toast("播完了");',
                 "loadShareTrack(track, forceAutoplay === true || !audio.paused);"]:
        assert frag in share_all, f"上下曲语义缺 {frag}"
    # 播完推进: 单曲循环回开头重播, 其余强续 (app audio-events 同款)
    assert 'if (playQueue && playQueue.repeat === "one") {' in share_all
    assert "playerNext(true);" in share_all
    # 单曲分享: 没有上一首/下一首可言, 传输区收成一颗播放键
    assert "if (playQueue.tracks.length < 2) {" in share_all
    # 待播队列: 从当前曲往后排, 点行跳播 (只读, 没有换序/删除)
    for frag in ["function renderQueueView", "queueUpcoming(playQueue)",
                 'data-queue-track-id="${track.track_id}"',
                 "继续播放", "队列是空的",
                 "const track = queueJump(playQueue, Number(row.dataset.queueTrackId));"]:
        assert frag in share_all, f"待播队列缺 {frag}"
    # 队列行封面走分享路由, 裂图退 ♪ (与 app 的 .t-art 同类名同语言)
    assert 'class="t-art" loading="lazy"' in share_all
    assert ".t-art {" in share_all
    # 旧 数组+下标 队列退役
    for gone in ["repeatMode", "shuffleOn", "syncStepButtons",
                 "$(\"#fp-prev\").disabled"]:
        assert gone not in share_all, f"旧队列态 {gone} 该撤了"


def test_music_share_player_views_wiring():
    """歌词/队列两视图同住封面区互斥; 手动滚词出「回到当前句」+ 浏览期间
    整页清晰; 下拉/横划收起整用应用 bindDismissDrag 同款。"""
    share = share_page_shell()
    share_all = share + share_page_js()
    # 互斥: 开歌词收队列, 开队列收歌词 (app 同款)
    assert "if (open && queueViewOpen) closeQueueView();" in share_all
    assert "if (lyricsViewOpen) toggleLyricsView();\n  if (queueViewOpen) closeQueueView();" \
        in share_all
    # 氛围底跟着视图压暗 (app 同款 #full-player.lyrics/.queue)
    assert "$(\"#full-player\").classList.toggle(\"lyrics\", open);" in share_all
    assert "$(\"#full-player\").classList.add(\"queue\");" in share_all
    # 手动滚词: 浏览态整页清晰 + 回到当前句, 静置 4 秒自动回跟唱
    for frag in ['$("#fp-lyrics").classList.add("browsing");',
                 "$(\"#lyrics-resume\").hidden = false;",
                 "function resumeLyricsFollow",
                 "$(\"#lyrics-resume\").addEventListener(\"click\", () => resumeLyricsFollow());"]:
        assert frag in share_all, f"浏览歌词缺 {frag}"
    assert "回到当前句" in share
    # 收起手势: 应用 bindDismissDrag 同款 (抓手横拖右甩/封面下拉/
    # 整页让路清单 + 词队列滚在半路先归滚)
    for frag in ["function bindDismissDrag",
                 'closeFullPlayer("right");',
                 '"#fp-grab, #fp-art-wrap, .fp-scrub,"',
                 'event.target.closest("#fp-lyrics, #queue-list")',
                 "bindDismissDrag($(\".fp-sheet\"), false, true);",
                 "bindDismissDrag($(\".fp-bg\"), false, true);"]:
        assert frag in share_all, f"收起手势缺 {frag}"
    # 进度条命中垫 (app 同款): iOS 按轨道也跳值
    assert 'enhanceSliderTouch($("#fp-scrub"));' in share_all
    # 开页压「回到当前句」, 关页顺手收两视图 (app 同款)
    assert '$("#lyrics-resume").hidden = true;' in share_all
    # 歌词视图开关的旧语义照旧: 没词键灰, 开着封面让位
    assert '$("#fp-art-wrap").hidden = open;' in share_all
    assert 'lyricsButton.disabled = !lyrics && !lyricsViewOpen;' in share_all
