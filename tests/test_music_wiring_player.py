"""My Music 播放器接线测试: 控制钮样式, 队列封面视图, 返回手势收起,
单 URL 导航 —— 静态文本断言, 不碰数据库。拆自 test_music_wiring.py
(结构化重构); 1.8.31 队列拖拽长出自己的历史, 分家去 test_music_queue_drag。"""

from tests.music_static_files import (MUSIC_STATIC, music_browser_js,
                                      music_page_shell, music_player_js)


def test_music_controls_apple_style_wiring():
    """传输区最终形 (用户两连点名): 三键站在进度条**正上方**居中成一行,
    不是挤在进度条旁边; 三键一般大 (44×44, 播放键不再大一号);
    进度条 range 住在 flex 行里要 flex:1+min-width:0 才肯让位收缩。
    迷你气泡 1.8.0 起只留播放/暂停 (上下曲撤了, 全屏页里都有,
    气泡收窄让位给歌名跑马灯)。图标包围盒中心对准按键中心的
    不变量在 player-icons.test.mjs。"""
    html = music_page_shell()
    common = (MUSIC_STATIC / "js" / "music-common.js").read_text(encoding="utf-8")
    # 键行在进度行**上面** (markup 顺序即视觉顺序)
    assert html.index('<div class="fp-controls">') < html.index('<div class="fp-transport">')
    controls = html[html.index(".fp-controls {"):html.index(".fp-transport {")]
    assert "justify-content: center" in controls and "gap: 32px" in controls
    assert "width: 44px; height: 44px; color: #fff; padding: 0" in controls  # 三键一般大
    assert "#fp-play { width" not in html          # 播放键不再有大一号的覆盖
    transport = html[html.index(".fp-transport {"):html.index(".fp-actions {")]
    assert ".fp-scrub { flex: 1; min-width: 0; }" in transport  # range 让位收缩
    assert 'id="fp-time-cur"' in html and 'id="fp-time-total"' in html  # 时间标签还在
    assert 'width="30" height="30"' in html                       # 上下曲字形
    assert 'width="32" height="32"' in common                     # 播放/暂停只略大
    assert ".fp-times" not in html                                # 旧三行布局撤了
    assert ".fp-controls > button:active { transform: scale(.86)" in html  # 按压反馈
    assert "#fp-grab" in html                                 # 收起抓手
    # 迷你气泡: 播放/暂停 + 上下曲 (1.8.0 撤过, 1.8.87 用户点名加回);
    # 歌名/作者改跑马灯
    assert 'id="mini-play"' in html and 'id="mini-prev"' in html \
        and 'id="mini-next"' in html
    assert 'class="mq-line"' in html and 'class="mq-run"' in html
    # 音量条整个撤了 (1.5.1, 用户点名): 音量交给设备音量键/系统音量
    assert "#fp-volume" not in html and ".fp-volume" not in html
    # 气泡磨砂玻璃 (用户点名): 七成底色配 blur(20), 底下划过的内容糊成
    # 影子透上来 —— 不是一块实心灰板; 1.8.3 调实一档后 1.8.5 调回半透明
    # (八成看着偏实心板, 磨砂感回来)
    mini_css = html[html.index("#mini-player {"):html.index("#mini-progress")]
    assert "rgba(44,44,46,.7);" in mini_css
    assert "backdrop-filter: blur(20px) saturate(180%);" in mini_css
    # 气泡播放/暂停键大一号 (用户点名 "比上一首下一首还小"): 三角/双杠是
    # 紧凑实心形, 跟宽箭头同尺寸显得小 —— 28 对 24 才齐平; 撤掉旧补偿边距
    assert 'width="28" height="28"' in common
    assert "margin: 0 2px" not in html
    # 整个应用不画滚动条 (用户点名 "整个页面都不要"): 星规则管 Firefox,
    # 伪元素管 Chrome/Safari; iOS 本来就不画 —— 能滚, 只是不显示
    star_css = html[html.index("* {"):html.index("[hidden]")]
    assert "scrollbar-width: none;" in star_css
    assert "::-webkit-scrollbar { display: none; }" in html


def test_music_queue_cover_view_wiring():
    """播放队列 = 封面原地翻开的视图 (用户点名"不要弹队列, 用封面区域显示
    播放列表"): 头部一行 (继续播放 + N 首歌曲), 下面 upcoming 列表; 与歌词
    视图同住封面区互斥; 全屏页收起时跟着收。旧底部弹层全撤。
    1.8.5 头部改「继续播放」+ 随机/循环两枚图标钮; 1.8.89 (用户点名「待播放
    列表就不需要播放控制了」) 两枚键撤了 —— 循环控制归播放页底行三态一键,
    iconfont 循环标 (单曲带 1, 列表去 1) + 交叉箭头随机形照用, JS 按态换。"""
    html = music_page_shell()
    player = music_player_js()
    for frag in ['<div id="fp-queue" hidden>', 'class="fq-head"',
                 'class="fq-head-txt"', 'id="fq-count"',
                 'id="queue-list"', "#full-player.queue .fp-bg img"]:
        assert frag in html, f"队列视图缺 {frag}"
    # 1.8.89 (用户点名「待播放列表就不需要播放控制了」): 头部两枚控制键死透
    for gone in ["fq-head-btns", "fp-shuffle", "fp-repeat"]:
        assert gone not in html, f"{gone} 该撤没撤"
    assert "<b>继续播放</b>" in html and ">待播放<" not in html
    # 1.8.89 循环控制归播放页底行三态一键 (加列表键让位, 加列表仍在 ⋯ 菜单):
    # 列表/单曲/随机三态各一枚图标, JS 按态换 innerHTML; 切一下气泡报当前态
    assert 'id="fp-mode-btn" aria-label="循环模式"' in html
    assert "$(\"#fp-mode-btn\").innerHTML = shuffle ? ICON_SHUFFLE" in player
    assert "queueCyclePlayMode(playQueue)" in player
    assert 'toast(mode === "all" ? "列表循环" : mode === "one" ? "单曲循环" : "随机循环")' \
        in player
    common = (MUSIC_STATIC / "js" / "music-common.js").read_text(encoding="utf-8")
    for icon in ["ICON_REPEAT = ", "ICON_REPEAT_ONE = ", "ICON_SHUFFLE = "]:
        assert icon in common, f"music-common.js 缺少 {icon}"
    # 1.8.91 (用户点名「放在标题上, 整体居中」): 播放页开着时气泡上标题行
    # —— JS 现量 .fp-now 行位钉 top, CSS 收 bottom 让位
    assert '$("#full-player.open .fp-now")' in common
    assert 'classList.toggle("on-title"' in common
    assert "#toast.on-title" in html and "#toast.on-title.show" in html
    assert "#fp-repeat.one" not in html          # 旧「1」角标那套撤了
    assert "fq-modes" not in html                    # 旧顶排胶囊撤了
    assert "queue-sheet" not in html and "queue-mask" not in html \
        and "queue-close" not in html              # 旧弹层死透
    assert "queue-sheet" not in player and "queue-mask" not in player
    for frag in ["function toggleQueueView", "function closeQueueView",
                 "function renderQueueView", "let queueViewOpen = false;",
                 '$("#fp-queue-btn").addEventListener("click", toggleQueueView);',
                 "$(\"#queue-list\").innerHTML = upcoming.map",
                 '$("#fq-count").textContent = `${upcoming.length} 首歌曲`']:
        assert frag in player, f"music-player.js 缺 {frag}"
    # 行样式: 1.8.38 改歌单同款行 (用户点名「去序号, 显封面, 跟歌单里的
    # 歌曲风格一致」) —— 序号 (.q-num) 退役, 左 44px 封面 + 歌名/作者两行
    for frag in [".queue-row {", ".q-lead {", ".q-main {", ".q-title {",
                 ".q-artist {", "touch-action: pan-y;"]:
        assert frag in html, f"队列行样式缺 {frag}"
    assert ".q-num" not in html                       # 序号那套撤净
    # 行内容: 封面走 trackArtHTML (无图退 ♪ 块), 当前曲封面盖半透纱+白动条
    assert '${on ? ICON_BARS : ""}${trackArtHTML(track)}' in player
    assert ".queue-row.on .bars {" in html
    assert ".queue-row.on .bars i { background: #fff;" in html
    # 1.8.58 动条扶正 (用户点名「正在播放的动态」): 纱罩动条自 1.8.38 起
    # 一直没亮 —— .bars 基类 display:none, 开它的 .playing 类没给到队列行。
    # 现在真播着才亮 (渲染带类 + 暂停/续播 updatePlayButtons 同拍收放),
    # 暂停只留白粗歌名认当前曲 (与列表行同一语言)
    assert '${on && playerIsPlaying() ? " playing" : ""}' in player
    assert ".queue-row.playing .bars { display: flex; }" in html
    assert 'document.querySelectorAll(".queue-row")' in player
    assert "row.dataset.queueTrackId) === playerCurrentTrackId() && playing" in player
    # 互斥: 开队列先收歌词, 开歌词先收队列; 收起播放页两个都收
    assert "if (lyricsViewOpen) toggleLyricsView();" in player
    assert "if (!lyricsViewOpen && queueViewOpen) closeQueueView();" in player
    # 1.8.20 改回原样 (用户点名「歌词页不要封面缩略图」): 歌词页罩满封面
    # 区, 封面整块藏掉; .lyrics 类只留背景压暗用 (缩略图那套 CSS 撤净)
    assert '$("#fp-art-wrap").hidden = lyricsViewOpen;' in player
    assert "#full-player.lyrics .fp-body {" not in html


def test_music_player_dismiss_wiring():
    """播放页的收起路径 (1.7.0 单地址批): 下拉/Esc 向下收, 抓手条横拖右甩
    向右收 —— 全是纯视图开关, 不再挂历史条目 (一个地址批后浏览器里没有
    可退的条目, 播放页也跟着撤了 pushState/popstate 那套)。
    电脑上的"返回"是 Esc: 先收播放页, 没开就收顶层二级页。"""
    html = music_page_shell()
    player = music_player_js()
    js = music_browser_js()
    assert "#full-player.dismiss-right { transform: translateX(100%); }" in html
    # 历史耦合撤净: 播放页开关不再碰 pushState/back/popstate
    assert "pushState" not in player and "history.back" not in player
    assert "popstate" not in player and "poppingPlayerEntry" not in player
    assert 'closeFullPlayer("right")' in player    # 抓手横拖的甩出收起
    assert 'if (direction === "right") fullPlayer.classList.add("dismiss-right")' \
        in player
    # 抓手条横拖收起: bindDismissDrag 第二参数开启, 拖整页不是拖封面
    assert "horizontalClose = false" in player
    assert 'player.style.transform = dx > 0 ? `translateX(${dx * 0.92}px)` : "";' \
        in player
    assert 'bindDismissDrag($("#fp-grab"), true);' in player
    # 1.8.60 封面只剩下拉收起, 左右划交给 3D 封面舞台 (art-stage 模块)
    assert 'bindDismissDrag($("#fp-art-wrap"));' in player
    assert "initArtStage();" in player
    # 1.8.2 整页下拉收起 (用户点名「任何一点都能拖」): .fp-sheet/.fp-bg 也绑
    # 一份, 第三参数让路自带手势/滚动/按钮的起手点 (歌词/队列要滚,
    # 抓手/封面自带拖动, 按钮滑杆各有语义)
    assert 'bindDismissDrag($(".fp-sheet"), false, true);' in player
    assert 'bindDismissDrag($(".fp-bg"), false, true);' in player
    # 1.8.5 修「切到待播放后全局下拉退出小了」: 歌词/待播放不再是免死金牌
    # —— 自己滚在半路才让路 (滚到顶时下拉归收起); 让路名单里其余照旧
    assert '"#fp-grab, #fp-art-wrap, .fp-scrub,"' in player
    assert 'event.target.closest("#fp-lyrics, #queue-list");' in player
    # Esc = 电脑上的返回: 先收播放页 (1.8.63 水滴收回), 没开收顶层二级页
    esc_handler = js[js.index('event.key !== "Escape"'):
                     js.index("// 键盘避让")]
    assert 'if (playerOpen) closeFullPlayer("morph");' in esc_handler
    assert "closePushStack(pushStack.length - 1)" in esc_handler


def test_music_single_url_navigation_wiring():
    """单地址导航 (用户点名: 列表和主页就是一个页面, 进播放列表只是内容
    变化, 不存在网页切换): 导航目标只活在内存里 (根视图 + 层栈), 全程
    不碰 location.hash / pushState / history.back —— 浏览器返回/前进和
    iOS 系统侧滑在应用里没有条目可退, 整页截图滑走 (气泡跟着跑) 绝迹。
    旧深链开局消化一次, URL 随即洗成光杆 /music。"""
    js = music_browser_js()
    player = music_player_js()
    # 不写 hash、不挂 hashchange、不加/弹历史条目 (认调用形式 —— 文件头
    # 注释里提到这些词是说明, 不算数)
    assert "location.hash =" not in js
    assert "hashchange" not in js
    assert "pushState(" not in js and "history.back(" not in js
    assert "pushState(" not in player and "history.back(" not in player
    # 目标从状态派生: 有层看顶层, 没层看根视图 (1.8.0: 主页独占根层,
    # 播放列表/专辑/艺人/最近播放/播放排行/已下载/搜索/设置/统计/更新日志
    # 全是推入层)
    assert "function parseRoute" in js and "function currentRoute" in js
    assert ('const PANE_VIEWS = ["playlists", "albums", "albums-recent", '
            '"artists", "recent",') in js
    assert '"top", "downloads", "search", "settings", "stats", "changelog"];' in js
    assert "PANE_VIEWS.includes(name)" in js
    assert 'const pushed = view !== "home";' in js
    assert "function routeRoot" in js and "function routePushed" in js
    # 开局: 旧深链消化一次 → replaceState 洗 URL (不加条目) → 状态开局
    # (1.8.8 起整条轨迹逐层重放, 详见搜索接线测试)
    assert 'const legacyHash = location.hash.replace(/^#\\/?/, "");' in js
    assert 'history.replaceState(null, "", location.pathname + location.search);' \
        in js
    assert "journey.forEach(navigate);" in js
    # 层收尽 (按钮收/右划收) 回到根视图 = 主页; 页签点亮同步那套随页签栏撤了
    assert "syncViewTabs" not in js
