"""My Music 流体胶囊形变测试 (1.8.63, 用户点名「播放气泡被点击要实现流体
胶囊形变, 像水滴一样平滑流动延展成新的面板」+ AI 描述词「实现胶囊按钮向
弹窗面板的流体形态变换, 尺寸与圆角采用高阻尼流体曲线无缝过渡」;
1.8.64 用户回评「展开动画再慢一点, 细节多一些」)。"""


from tests.music_static_files import MUSIC_STATIC, music_page_shell


def test_music_fluid_morph_wiring():
    """点播放气泡, 播放页从气泡的胶囊轮廓原位延展成整页 (水滴铺开):
    几何五件套加皮肤 (胶囊的影子/底色) 走同一条高阻尼流体曲线 (与滑入
    同款, 无过冲), 底色从胶囊的半透明灰渐成播放页纯黑; 长成过半内容
    分层进场。收起分两路: 程序化收起 (抓手点按/Esc/跳艺人专辑页) 水滴
    收回胶囊 (快一拍 —— 进场可以慢, 出场要干脆), 落位后交还气泡; 拖拽
    收起 (下拉/右甩) 照旧滑出。形变可被打断: 序号闸作废旧收尾, 退路都
    先清行内回样式表世界。"""
    html = music_page_shell()
    fluid_js = (MUSIC_STATIC / "js" / "music-player-fluid-morph.js").read_text(
        encoding="utf-8")
    fullpage_js = (MUSIC_STATIC / "js" / "music-player-fullpage.js").read_text(
        encoding="utf-8")
    events_js = (MUSIC_STATIC / "js" / "music-player-events.js").read_text(
        encoding="utf-8")
    # 模块挂载: 在 fullpage (开合逻辑) 之前
    assert '<script src="/music/static/js/music-player-fluid-morph.js?v=2">' \
        in html
    # 高阻尼流体曲线 + 时长: 铺开放缓 (1.8.64), 收回快一拍
    assert "const FLUID_MS = 640;" in fluid_js
    assert "const FLUID_CLOSE_MS = 480;" in fluid_js
    assert 'const FLUID_CURVE = "cubic-bezier(.32,.72,0,1)";' in fluid_js
    for frag in ["function fluidBubble", "function fluidPose",
                 "function fluidClear", "function fluidGo",
                 "function fluidExpand", "function fluidCollapse",
                 "function fluidReset"]:
        assert frag in fluid_js, f"fluid-morph 缺 {frag}"
    # 气泡是形变的原点: 没在播 (气泡 hidden) 就退回滑入; 皮肤读计算样式
    assert 'if (!bubble || bubble.hidden) return null;' in fluid_js
    assert "parseFloat(style.borderTopLeftRadius)" in fluid_js
    assert "style.boxShadow" in fluid_js
    assert "style.backgroundColor" in fluid_js
    # 气泡由形变中的面板接管 (防双影), 清场时交还
    assert '$("#mini-player").style.visibility = "hidden";' in fluid_js
    assert '$("#mini-player").style.visibility = "";' in fluid_js
    # 开场: 几何 + 皮肤从胶囊位铺到全屏位 (落位皮肤 = 播放页本色)
    assert "const endSkin = { radius: 0, shadow: \"none\"," \
        " bg: computed.backgroundColor };" in fluid_js
    assert "fluidPose(player, 0, 0, target.width, target.height, endSkin);" \
        in fluid_js
    # 收尾带序号闸 (中途改戏作废); 长成过半内容先分层回场
    assert "if (seq !== fluidSeq) return;" in fluid_js
    assert "player.classList.add(\"revealed\");" in fluid_js
    # 开合接线: 开优先流体 (没气泡退回滑入), 程序化收起收拢回胶囊
    assert "if (fluidExpand(fullPlayer)) {" in fullpage_js
    assert 'direction === "morph" && fluidCollapse(fullPlayer)' in fullpage_js
    assert "}, FLUID_CLOSE_MS);" in fullpage_js
    # 退路都先清形变残留: 滑入起点 / 滑出路径 / 拖拽跟手
    assert fullpage_js.count("fluidReset(") == 4
    # 抓手点按也是水滴收回
    assert 'closeFullPlayer("morph");' in events_js


def test_music_fluid_morph_css_states():
    """形变态内容的状态机 (music-fluid-morph.css, 1.8.64 从
    music-player.css 拆出): .morphing = 内容整体退场 (visibility 延迟到
    淡出后 —— 不吃逐帧重排也不吃命中), 各层沉到自己的进场位 (收拢时
    反向走一遍); .revealed = 分层回场 —— 抓手先落, 封面带升起, 文字控件
    一排排跟上 (错峰 70-245ms), 氛围底慢一拍铺满; 圆角裁切开着。"""
    css = (MUSIC_STATIC / "css" / "music-fluid-morph.css").read_text(
        encoding="utf-8")
    # 基态带进场过渡 (撤 .morphing 那拍淡入回场); 退场快一拍
    assert ".fp-bg, .fp-sheet > * {" in css
    assert "transition: opacity .34s cubic-bezier(.22,.61,.36,1)," in css
    assert "#full-player.morphing { overflow: hidden; }" in css
    for frag in ["#full-player.morphing .fp-bg,",
                 "#full-player.morphing .fp-sheet > * {",
                 "opacity: 0; visibility: hidden; transform: translateY(14px);",
                 "visibility 0s .22s;",
                 "#full-player.morphing .fp-sheet > .fp-body"
                 " { transform: translateY(20px) scale(.97); }",
                 "#full-player.morphing.revealed .fp-sheet > * {",
                 "#full-player.morphing.revealed .fp-bg {"]:
        assert frag in css, f"形变样式缺 {frag}"
    # 分层错峰: 封面 70ms → 文字 130 → 控件 175 → 进度 215 → 底排 245,
    # 氛围底慢拍铺满 (.55s)
    for frag in [".fp-sheet > .fp-body {",
                 ".fp-sheet > .fp-meta {",
                 ".fp-sheet > .fp-controls {",
                 ".fp-sheet > .fp-transport {",
                 ".fp-sheet > .fp-actions {",
                 "cubic-bezier(.22,.61,.36,1) 70ms,",
                 "cubic-bezier(.22,.61,.36,1) 130ms,",
                 "cubic-bezier(.22,.61,.36,1) 175ms,",
                 "cubic-bezier(.22,.61,.36,1) 215ms,",
                 "cubic-bezier(.22,.61,.36,1) 245ms,",
                 "transition: opacity .55s ease 110ms, visibility 0s 0s;"]:
        assert frag in css, f"分层进场缺 {frag}"


def test_music_fluid_morph_programmatic_closes():
    """程序化收起三处都走水滴收回: 抓手点按 / Esc (电脑返回) / 菜单跳
    艺人专辑 (层滑入与收拢同场); 拖拽收起不走形变 (滑出才是惯性连续)。"""
    esc_js = (MUSIC_STATIC / "js" / "music-global-events.js").read_text(
        encoding="utf-8")
    menu_js = (MUSIC_STATIC / "js" / "music-menu-gestures.js").read_text(
        encoding="utf-8")
    assert 'else if (playerOpen) closeFullPlayer("morph");' in esc_js
    assert 'if (playerOpen) closeFullPlayer("morph");' in menu_js
    # 拖拽收起保持滑出: 下拉松手不带参, 右甩 "right" (fullpage 里)
    fullpage_js = (MUSIC_STATIC / "js" / "music-player-fullpage.js").read_text(
        encoding="utf-8")
    assert "if (lastY - startY > 90 || velocity > 0.55) closeFullPlayer();" \
        in fullpage_js
    assert 'closeFullPlayer("right");' in fullpage_js
