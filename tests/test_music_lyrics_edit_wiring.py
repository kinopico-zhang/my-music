"""My Music 调整歌词接线测试 (1.8.133, 用户点名「播放页 … 里加一个选项,
可以搜索歌词, 也可以调整歌词的 offset, 界面和正在播放的界面差不多,
要能实时看到效果」): ⋯ 菜单项 → 底部弹层盖在歌词视图上, 搜词换词 +
±0.5 秒对齐微调即点即生效。后端三口的行为在 test_music_lyrics_edit,
这里只钉静态接线 (选择器×html 交叉, 防撤元素后 JS 孤儿接线)。"""
from tests.music_static_files import (MUSIC_STATIC, music_page_shell,
                                      share_page_shell)


def test_music_lyrics_edit_menu_wiring():
    """⋯ 菜单的「调整歌词」: 标记/派发/显隐三处接线齐。"""
    html = music_page_shell()
    for frag in ['data-track-action="lyrics" id="track-menu-lyrics" hidden',
                 'id="lyr-edit-mask"', 'id="lyr-edit-sheet"',
                 'id="lyr-edit-close"', 'id="lyr-edit-query"',
                 'id="lyr-edit-search"', 'id="lyr-edit-status"',
                 'id="lyr-edit-list"', 'id="lyr-edit-earlier"',
                 'id="lyr-edit-later"', 'id="lyr-edit-reset"',
                 'id="lyr-edit-offset-val"', 'id="lyr-edit-offset-hint"',
                 'css/music-lyrics-edit.css?v=1',
                 'js/music-lyrics-edit.js?v=1',
                 'js/music-player-state.js?v=4',      # lyricsOffsets 缓存
                 'js/music-player-lyrics-toggle.js?v=6',   # 预取记 offset
                 'js/music-player-lyrics.js?v=5',      # 高亮减 offset
                 'js/music-track-menus.js?v=10',       # ⋯ 变体亮出该项
                 'js/music-menu-gestures.js?v=8']:     # 派发分支
        assert frag in html, f"页面缺 {frag}"
    gest = (MUSIC_STATIC / "js" / "music-menu-gestures.js").read_text(
        encoding="utf-8")
    assert ('else if (action.dataset.trackAction === "lyrics")'
            in gest and "openLyricsEditSheet" in gest)
    menus = (MUSIC_STATIC / "js" / "music-track-menus.js").read_text(
        encoding="utf-8")
    # ⋯ 变体亮出 / 行长按变体藏掉 (面板只对着正在播的那首)
    assert '$("#track-menu-lyrics").hidden = false;' in menus
    assert '$("#track-menu-lyrics").hidden = true;' in menus


def test_music_lyrics_edit_module_wiring():
    """面板模块: 开面板落座歌词页 (预览即正在播的那页), 搜索/套用/微调
    三动作的取数口与守门都在。"""
    js = (MUSIC_STATIC / "js" / "music-lyrics-edit.js").read_text(
        encoding="utf-8")
    for frag in [
        "function openLyricsEditSheet(track)",
        "openLyricsView();",                       # 界面就是正在播的歌词页
        '$("#lyr-edit-query").value = `${track.title} ${track.artist}`.trim();',
        "const OFFSET_STEP_MS = 500;",             # 一步半秒
        "const OFFSET_LIMIT_MS = 30000;",          # 与服务端同一钳制
        "Math.max(-OFFSET_LIMIT_MS, Math.min(OFFSET_LIMIT_MS, next))",
        "highlightActiveLyric();",                 # 微调就地重算, 当场见效
        "offsetSaveTimer = setTimeout(saveOffsetNow, 700);",   # 防抖落库
        "`/music/api/tracks/${trackId}/lyrics/offset`",
        "offset_ms: lyricsOffsets.get(trackId) || 0",
        "`/music/api/tracks/${trackId}/lyrics/candidates`",
        "`/music/api/tracks/${trackId}/lyrics/apply`",
        "if (seq !== searchSeq || trackId !== lyricsEditTrackId) return;",
        "if (trackId !== lyricsEditTrackId) return;   // 面板已收/已换曲",
        "lyricsCache.set(trackId,",                # 套用后缓存换新
        "lyricsOffsets.set(trackId, response.lyrics_offset_ms || 0);",
        "await loadLyrics();",                     # 重铺 + 高亮即时跟上
        "escapeHTML(candidate.title)",             # 候选行文案过 HTML 转义
        "onTrackChange(() => {",                   # 换曲收面板
    ]:
        assert frag in js, f"面板模块缺 {frag}"
    # 歌词高亮对轴: 拿 播放进度 − offset (正 = 词延后)
    lyrics_js = (MUSIC_STATIC / "js" / "music-player-lyrics.js").read_text(
        encoding="utf-8")
    assert "lyricsOffsets.set(track.track_id, response.lyrics_offset_ms || 0);" \
        in lyrics_js
    assert ("const offsetSeconds = (lyricsOffsets.get(currentTrack.track_id)"
            " || 0) / 1000;") in lyrics_js
    assert "audioElement().currentTime - offsetSeconds" in lyrics_js
    # 预取也把 offset 记进缓存 (歌词键亮灰同一条应答)
    toggle = (MUSIC_STATIC / "js" / "music-player-lyrics-toggle.js").read_text(
        encoding="utf-8")
    assert "lyricsOffsets.set(track.track_id, response.lyrics_offset_ms || 0);" \
        in toggle
    # 微调缓存住在共享状态里 (别处声明, 面板/高亮都读写它)
    state = (MUSIC_STATIC / "js" / "music-player-state.js").read_text(
        encoding="utf-8")
    assert "let lyricsOffsets = new Map();" in state
    # 样式: 弹层盖满 (z 在全屏页之上), 微调灰钮有视觉
    css = (MUSIC_STATIC / "css" / "music-lyrics-edit.css").read_text(
        encoding="utf-8")
    for frag in ["#lyr-edit-mask { position: fixed; inset: 0; z-index: 99;",
                 "#lyr-edit-sheet {",
                 "position: fixed; left: 0; right: 0; bottom: 0; z-index: 100;",
                 ".lyr-edit-offset button:disabled { opacity: .4; }",
                 "#lyr-edit-offset-hint:empty { display: none; }"]:
        assert frag in css, f"面板样式缺 {frag}"


def test_music_lyrics_edit_share_follows():
    """分享页跟调: 主人调好的对齐跟着分享走 —— 高亮/点句定位同一式。"""
    share = share_page_shell()
    assert "js/share/share-viewer-lyrics.js?v=11" in share
    js = (MUSIC_STATIC / "js" / "share" / "share-viewer-lyrics.js").read_text(
        encoding="utf-8")
    assert "const shareLyricsOffsets = new Map();" in js
    assert "shareLyricsOffsets.set(track.track_id, body.lyrics_offset_ms || 0);" \
        in js
    assert "audio.currentTime - lyricsOffsetMs / 1000" in js   # 高亮对轴
    assert "audio.currentTime = time + lyricsOffsetMs / 1000" in js  # 点句定位
    sw = (MUSIC_STATIC / "sw.js").read_text(encoding="utf-8")
    assert "music-shell-v124" in sw
