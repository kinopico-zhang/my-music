"""My Music 播放器批次接线测试: 1.8.2 交互批 + 1.8.5 打磨批 + 1.8.6
修复批 —— 静态文本断言, 不碰数据库。拆自 test_music_wiring_player.py
(文件超 200 行按域再拆)。"""

from tests.music_static_files import (MUSIC_STATIC, music_browser_js,
                                      music_page_shell, music_player_js)


def test_music_182_player_interaction_batch():
    """1.8.2 播放页交互批 (用户点名): 专辑名并进艺人行 (来源行只留作词
    标签, 没有整行收掉; 1.8.17 作曲也撤了); 弹出菜单加「进入专辑主页」;
    修「进艺人主页点了没反应」—— 页面其实开了, 但 z90 的全屏播放页
    盖着 z44 的推入层, 开了也看不见: 跳转前先把播放页收起来。"""
    html = music_page_shell()
    player = music_player_js()
    js = music_browser_js()
    # 专辑名并到艺人后 (| 隔开), 底下那一行省出来
    assert "[track.artist, track.album_title]" in player
    assert '.filter(Boolean).join(" | ");' in player
    assert "function renderSourceLine" in player     # 来源行只留 作词 标签
    assert 'id="fp-source" hidden' in html           # 没标签时整行收掉
    # 1.8.17 撤作曲 (用户点名「播放页下面的作曲去掉」): 只认作词,
    # credits 接口照旧返回作曲 —— 展示层不读它
    assert "data.lyricist" in player
    assert "data.composer" not in player
    # 菜单新条目: 进入专辑主页 (这首歌有专辑才亮)
    assert 'data-track-action="album" id="track-menu-album"' in html
    assert '进入专辑主页' in html
    assert '$("#track-menu-album").hidden = !track.album_id;' in js
    # 修: 跳艺人/专辑前先收播放页 (盖在底下 = 看着没反应)
    assert "if (playerOpen) closeFullPlayer();" in js
    assert "`album/${track.album_id}`" in js


def test_music_185_player_polish_batch():
    """1.8.5 播放页打磨批 (用户点名): 待播放界面列表顶时整页下拉也收得掉;
    刚开歌打开字幕停在第一句 (换曲残留的 scrollTop 归零); 歌词平时行宽
    只给 80%, 放大后不触发重新换行。"""
    html = music_page_shell()
    player = music_player_js()
    # 队列/歌词视图各自的滚动器: 列表顶时下拉归收起, 滚到中间先归滚动
    assert 'event.target.closest("#fp-lyrics, #queue-list");' in player
    assert "if (scroller && scroller.scrollTop > 0) return;" in player
    # 换曲重铺歌词从第一句起 (残留 scrollTop 归零)
    lyrics_js = (MUSIC_STATIC / "js" / "music-player-lyrics.js").read_text(
        encoding="utf-8")
    assert "container.scrollTop = 0;" in lyrics_js
    # 行宽预留: 平时 80%; 1.8.17 放大改 transform: scale(1.24) —— 字号/行宽
    # 从头到尾恒定, 断行点物理上不可能再变 (1.8.5/1.8.6 行宽跟着长的过渡法
    # 只留 ~1% 余量, 中途取整仍小概率跳行, 退役); 80%×1.24 = 99.2% 装得下,
    # 溢出的 ~3.5px 落在 12px 行距里
    lyrics_css = html[html.index(".lyrics-line {"):html.index(".lyrics-line.upnext")]
    assert "max-width: 80%;" in lyrics_css
    assert "font-size: 21px; font-weight: 700;" in lyrics_css     # 字号从头到尾不动
    assert "max-width .5s" not in lyrics_css                      # 行宽不再参与动画
    assert "transition: filter .5s cubic-bezier(.22,.61,.36,1)," in lyrics_css
    active_css = html[html.index(".lyrics-line.active"):html.index("#fp-lyrics.browsing")]
    assert "transform: scale(1.24);" in active_css                # 放大走视觉缩放
    assert "max-width" not in active_css                          # 布局盒尺寸不变
    # 清晰度分工: 下一句清晰不放大 (马上要唱, 给个预告)
    assert ".lyrics-line.upnext { color: rgba(255,255,255,.66); filter: blur(0); }" in html


def test_music_186_player_batch():
    """1.8.6 播放页批 (用户点名): 继续播放列表顶上的「继续播放」标题和
    两枚图标钮不再发糊 —— 渐隐蒙版原来上下两头都罩, 把钉在顶上的头部
    也泡进渐隐带 (看着像一层涂层), 改成只在底边渐隐 (列表尾滚出用)。"""
    html = music_page_shell()
    queue_css = html[html.index("#fp-queue {"):html.index(".fq-head {")]
    assert "linear-gradient(#000 94%, transparent);" in queue_css  # 只底边渐隐
    assert "transparent, #000 18%" not in queue_css                # 顶边渐隐撤了


def test_music_1817_lyrics_view_survives_track_change():
    """1.8.17 (用户点名「切歌后歌词/封面视图跟上一首保持一致」): 歌词页
    开着切到一首没词的 (连播或手动), 不再强关回封面 —— 空态「这首歌没有
    歌词」垫着, 歌词键保持可点 (点一下才回封面); 视图关着时没词的键
    照旧灰掉开不了。看着封面的切歌也照旧封面 (无事发生, 无断言可立)。"""
    player = music_player_js()
    # 旧强关路径撤了: syncLyricsButton 不再顺手把开着的歌词视图 toggle 掉
    assert "if (noLyrics && lyricsViewOpen) toggleLyricsView();" not in player
    # 键的灰亮: 视图关着且没词才灰; 开着保持可点好关回封面
    assert '$("#fp-lyrics-btn").disabled = !!noLyrics && !lyricsViewOpen;' in player
    # 收视图时顺手重算键态: 关了且这首没词 → 灰回去 (再开开不了)
    assert "syncLyricsButton();    // 视图关了且这首没词: 键灰回去 (再开开不了)" \
        in player
    # 空态文案在 (loadLyrics 铺给没词的曲子)
    assert "这首歌没有歌词" in player
