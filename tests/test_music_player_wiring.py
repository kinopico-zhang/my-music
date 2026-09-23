"""My Music 播放交互接线测试: 搜索页/锁屏进度, 歌词动画,
点播从头, 音量 UI 撤除, 词标行平齐, 歌词行匹配纯逻辑。"""


from app.music.library_tags import extract_album_artwork
from tests.music_audio_seed import _write_audio
from tests.music_static_files import (
    MUSIC_STATIC, music_browser_js, music_page_shell, music_player_js,
)


def test_music_search_page_and_lockscreen_wiring():
    """1.4.1 后半批接线: 搜索页语种筛选撤掉 (2026-09-16 资料库也撤了) +
    页面不许横向溢出 (标题/右列文字收口, 长艺人名撑不宽) +
    锁屏进度随暂停/跳句/变速重报真实位置。"""
    html = music_page_shell()
    js = music_browser_js()
    player = music_player_js()
    # 语种筛选两处都撤净 (1.4.1 撤搜索页, 2026-09-16 再撤资料库):
    # chips 行/常量/接口参数全不该再出现
    assert "search-chips" not in js and "search-chips" not in html
    assert "lib-chips" not in js and "chipsHTML" not in js
    assert "&language=" not in js and "language:" not in js
    # 横向溢出: html 兜底禁横滑 + 行内标题包收缩层 + 右列可省略
    assert "overflow: hidden" in html   # 固定壳 (2026-09-16): 连 x 带 y 一起锁
    assert ".t-title-text" in html and "t-title-text" in js
    t_time_block = html.split(".t-time {", 1)[1].split("}", 1)[0]
    assert "min-width: 0" in t_time_block and "ellipsis" in t_time_block
    # 锁屏进度: 暂停 (速率报 0) / 跳句 / 变速 / timeupdate 都重报
    assert "function syncPositionState" in player
    assert '"play", "pause", "seeked", "ratechange"' in player
    assert "audio.paused ? 0 : audio.playbackRate" in player
    assert "setPositionState" in player
    assert "syncPositionState();" in player       # timeupdate 里也在报
    # 1.8.69 锁屏键位 (用户点名「应该是前一首, 后一首和暂停键」):
    # seekbackward/seekforward 一注册, iOS 键位就被 10 秒快退快进占了
    # —— 撤了, 只留切歌三键; 进度条拖动走 seekto, 不占键位
    assert '["play", "pause", "previoustrack", "nexttrack",' in player
    assert '"seekto"])' in player                  # 进度条拖动保留
    assert 'case "seekbackward"' not in player and 'case "seekforward"' not in player
    # 1.8.70 气泡直接播锁屏没切歌键 (用户实报「重启应用直接点气泡播放,
    # 锁屏没有上一首/下一首」): iOS 只认「出声那一刻」挂的键位, 开机恢复
    # 挂得早会被丢 —— 挂键位抽成可重挂函数, play/playing 起播都重挂
    assert "function rearmMediaSession" in player
    assert player.count("rearmMediaSession();") == 3   # 换曲 + play/playing 起播


def test_music_lyrics_animation_wiring():
    """歌词滚动动画接线: 当前行放大清晰/下一句清晰不放大/其余模糊退后
    (CSS 缓动) + rAF 逐帧缓动滚动, 手指一按就让位 (JS)。1.8.17 放大改
    transform: scale (字号/行宽恒定, 断行点物理上不可能再变 —— 两轮字号
    过渡法都治不干净的跳行断根)。"""
    html = music_page_shell()
    player = music_player_js()
    assert ".lyrics-line {" in html and "filter: blur(3px)" in html   # 其余模糊
    # 放大走视觉缩放: 字号恒 21px、行宽恒 80%, 当前行 transform: scale(1.24)
    # —— 布局盒尺寸不变, 断行点不会变 (1.8.17, 用户点名「放大别触发换行」)
    assert ".lyrics-line.active" in html and "transform: scale(1.24);" in html \
        and "blur(0)" in html                                          # 当前行放大清晰
    assert "font-size: 21px; font-weight: 700;" in html                # 字号从头到尾不动
    assert "will-change: filter, transform;" in html
    assert "transform-origin: left center;" in html    # 左缘对齐放大, 顶行不歪
    # 清晰度分工: 下一句清晰但不放大 (马上要唱, 给个预告)
    assert ".lyrics-line.upnext { color: rgba(255,255,255,.66); filter: blur(0); }" in html
    assert 'classList.toggle("upnext", position === index + 1)' in player
    lyrics_css = html[html.index(".lyrics-line {"):html.index(".lyrics-line.upnext")]
    assert "font-size: 26px" not in lyrics_css           # 旧字号过渡法退役
    assert "transition: filter .5s" in html                            # 状态切换也缓动
    for frag in ["function scrollLyricsTo", "function lyricsScrollFrame",
                 "function cancelLyricsScroll", "lyricsScrollRaf",
                 '"pointerdown", cancelLyricsScroll']:   # 手动滚动优先于动画
        assert frag in player, f"music-player.js 缺少 {frag}"


def test_music_click_play_starts_from_beginning():
    """点播一律从头 (用户报"有时点一首歌从一半播起, 怀疑存了每首的进度"):
    并没有按曲存进度 —— 冷启动恢复在 preload=none 的 audio 上写
    currentTime 是"待生效进度", Safari 会把它漏到之后点开的歌上。
    1.8.59 起恢复也走 loadTrack (startTime 参数带上存档进度, 且写在换源
    之后 —— 待生效进度只落在新源上, 不外漏; 点播照旧归零)。"""
    player = music_player_js()
    html = music_page_shell()
    load_track = player[player.index("function loadTrack"):
                        player.index("function prefetchNextTrack")]
    assert "audio.currentTime = startTime;" in load_track  # 换源后显式写 (0 = 点播归零)
    assert 'preload="none"' in html          # 恢复态不拉元数据 (待生效进度的温床)
    restore = player[player.index("function playerRestore"):
                     player.index("function renderPlayerChrome")]
    assert "loadTrack(track, false, saved.time || 0);" in restore  # 续听同一条路
    assert "audio.src = " not in restore     # 恢复不再自己赋源 (loadTrack 管)


def test_music_lockscreen_sw_bypass_wiring():
    """1.8.59 锁屏自停根修 (用户报「iOS 27 锁屏播着播着自己停了, 开 app
    又自动开始播放」): 每一轨音频流原本都经 SW 中转 (serveTrack 缓存回
    源/代取网络), iOS 锁屏会冻结 SW —— 管线要不到数据断粮自停, 开屏解冻
    挂起请求补上又自动续播。修法 = 播放全程绕开 SW: 流媒体带 ?direct 标记
    (SW 放行直连, 同步赋址保住手势内起播); 已下载的直读 Cache API 成 blob;
    预取同一条路; 下载模块加载晚于恢复现场, 就位后补刀换源。"""
    queue_js = (MUSIC_STATIC / "js" / "music-player-queue.js").read_text(
        encoding="utf-8")
    prefetch_js = (MUSIC_STATIC / "js" / "music-player-prefetch.js").read_text(
        encoding="utf-8")
    boot_js = (MUSIC_STATIC / "js" / "music-app-boot.js").read_text(
        encoding="utf-8")
    assert 'const blob = await downloads.cachedBlob(trackId);' in queue_js
    assert "`/music/media/stream/${trackId}?direct=1`" in queue_js
    assert "async function resolveTrackSource" in queue_js
    assert "typeof downloadsEnabled" in queue_js   # 恢复现场早于下载模块加载
    assert "playerUpgradeDownloadedSource" in queue_js   # 补刀换源 (blob 源)
    assert "let loadSequence = 0;" in queue_js     # 连切时旧的换源解析作废
    assert "resolveTrackSource(trackId)" in prefetch_js  # 预取同一条源解析路
    assert "function discardPrefetch" in prefetch_js
    assert "playerUpgradeDownloadedSource();" in boot_js  # 全模块就位后补刀
    downloads_js = (MUSIC_STATIC / "js" / "downloads.js").read_text(
        encoding="utf-8")
    # 下载取流同样直连 (?direct 标记); 缓存键仍光杆 (SW 旧壳兜底认得)
    assert 'streamURL(trackId) + "?direct=1"' in downloads_js
    assert "async function cachedBlob" in downloads_js   # 播放器直读缓存字节
    assert "cacheRead" in downloads_js


def test_music_volume_ui_removed():
    """音量条全平台撤除 (用户点名"音量条去掉吧"): iOS 的 audio.volume
    写了也白写, 1.5.0 的 WebAudio 增益又拖不动还脱开音量键 —— 桌面也
    不留了, 音量统一设备自己的键。回归: 旧的音量代码不许再爬回来。"""
    html = music_page_shell()
    player = music_player_js()
    for gone in ["AudioContext", "createGain", "createMediaElementSource",
                 "ensureVolumeRouting", "loadSavedVolume", "nativeVolumeWorks",
                 "applyVolume", "music-volume", "volume-off", "fp-volume"]:
        assert gone not in player, f"音量残留: {gone}"
        assert gone not in html, f"音量残留 (html): {gone}"


def test_music_lyrics_mark_row_badge():
    """词标 ❝: 行右侧图标簇的一员 (下载标前面), 17×17 与下载标同大、
    同 26px 高度框里垂直居中 —— 两个图标同一水平线, 不再像小上标;
    颜色同一档, 行右侧图标簇没有色差 (用户点名)。"""
    html = music_page_shell()
    js = music_browser_js()
    common = (MUSIC_STATIC / "js" / "music-common.js").read_text(encoding="utf-8")
    assert 'width="17" height="17"' in common              # 与下载标同大
    assert ".t-lyric" in html and "height: 26px" in html   # 与 .t-dl 同框高
    # 同色: 词标和下载标都是 ink-2 (下载完的勾加深到 ink-1 是另一态)
    lyric_block = html[html.index(".t-lyric {"):]
    assert "color: var(--ink-2)" in lyric_block[:lyric_block.index("}")]
    dl_block = html[html.index(".t-dl {"):]
    assert "color: var(--ink-2)" in dl_block[:dl_block.index("}")]
    # 挪出 .t-title: 行级元素, 排在下载标前面 (❝ 在前, 下载标在它后面)
    assert '${track.lyrics_available ? `<i class="t-lyric">' in js
    t_title_pos = js.index('<span class="t-title">')
    lyric_pos = js.index('<i class="t-lyric">${ICON_LYRICS}')
    dl_pos = js.index('<span class="t-dl${downloads.isDownloaded')
    assert t_title_pos < lyric_pos < dl_pos, "词标应排在标题之后、下载标之前"


def test_matching_lyric_line_pure():
    """歌词命中行: 剥时间轴/大小写不敏感; 全文没命中返回空串。"""
    from app.music.library_queries import _matching_lyric_line  # noqa: SLF001
    lyrics = "[00:01.00]Hello World\n[00:02.00]再见"
    assert _matching_lyric_line(lyrics, "hello") == "Hello World"
    assert _matching_lyric_line(lyrics, "再见") == "再见"
    assert _matching_lyric_line(lyrics, "不存在") == ""


def test_music_1853_lyrics_resume_residue_gone():
    """1.8.53 修「打开播放页偶尔在封面页上见着 回到当前句」: 关页途中
    歌词的惯性滚动还会补发几拍 scroll, 把浏览态 (含「回到当前句」键) 又
    点亮, 残留到下次开页。闸门两道: scroll 监听只在播放页开着且歌词视图
    在屏时才认; 开页先按下「回到当前句」兜底。"""
    events_js = (MUSIC_STATIC / "js" / "music-player-events.js").read_text(
        encoding="utf-8")
    fullpage_js = (MUSIC_STATIC / "js" / "music-player-fullpage.js").read_text(
        encoding="utf-8")
    assert "if (!playerOpen || !lyricsViewOpen) return;" in events_js
    assert ("lyricsViewOpen, openFullPlayer, playQueue, playerNext, playerOpen,"
            in events_js)                            # 全局声明补齐 (eslint 把着)
    assert '$("#lyrics-resume").hidden = true;' in fullpage_js   # 开页兜底


def test_extract_artwork_empty_picture(tmp_path):
    """FLAC 带空 PICTURE 块 (data 为空) → 没有可用封面。"""
    path = _write_audio(tmp_path, "A/a.flac", picture=b"")
    assert extract_album_artwork(path) is None
