"""My Music 客户端识别双轴测试 (1.8.103, 用户点名「按屏幕尺寸分手机小/
PC 大, 尺寸只影响布局; 按操作逻辑分键鼠/触摸」): 1.8.35 的 mobile/desktop
单轴拆成两条正交轴 —— 布局轴 data-size (视口宽 ≥700px 跟窗口换, 样式收在
music-large.css, 一律 html[data-size="large"] 作用域) 与操作轴 data-input
(主指针粗细 + UA 兜底跟插拔鼠标换, 样式收在 music-desktop.css, 一律
html[data-input="keymouse"] 作用域); 小屏+触摸是无前缀基线一个字节不动,
两轴独立翻转 (iPad = 大屏+触摸, PC 拖窄窗口 = 小屏+键鼠)。分类真值表在
tests/js/music-client.test.mjs (node 直测)。"""
from tests.music_static_files import (MUSIC_STATIC, music_page_shell,
                                      music_player_js)


def test_music_18103_client_axes_wiring():
    """识别模块先于 boot 加载 (boot 渲染前两条轴就位); 启动即写
    html[data-size / data-input], 窗口宽度和主指针粗细各跟各的信号换
    (拖宽窗口只翻布局轴, 插拔鼠标只翻操作轴); JS 分叉入口
    isKeyMouseInput()/isLargeSize(); 旧 ?ui=mobile/desktop 照认。"""
    html = music_page_shell()
    client_js = (MUSIC_STATIC / "js" / "music-client.js").read_text(
        encoding="utf-8")
    assert html.index("music-client.js") < html.index("music-app-boot.js")
    for frag in ["function classifySize(",
                 "function classifyInput(",
                 'matchMedia("(min-width: 700px)")',
                 'matchMedia("(pointer: coarse)")',
                 "root.dataset.size = classifySize(",
                 "root.dataset.input = classifyInput(",
                 "function isKeyMouseInput()",
                 "function isLargeSize()",
                 'if (raw === "mobile") return "phone";',  # 旧 ?ui= 照认
                 'if (raw === "desktop") return "pc";']:
        assert frag in client_js, f"music-client.js 缺 {frag}"


def test_music_18103_axes_css_scoping():
    """双轴的样式规矩: 布局规则一律 html[data-size="large"] 作用域收在
    music-large.css (只动布局, 不碰操作手感), 操作规则一律
    html[data-input="keymouse"] 作用域收在 music-desktop.css; 反向档
    (small/touch) = 无前缀基线不写; 旧单轴 data-client 选择器全站清零。"""
    html = music_page_shell()
    desktop_css = (MUSIC_STATIC / "css" / "music-desktop.css").read_text(
        encoding="utf-8")
    large_css = (MUSIC_STATIC / "css" / "music-large.css").read_text(
        encoding="utf-8")
    assert "music-desktop.css?v=" in html
    assert "music-large.css?v=" in html         # 1.8.103 布局轴分家
    assert 'html[data-size="large"]' in large_css
    assert 'html[data-size="small"]' not in large_css
    assert "cursor: pointer;" not in large_css  # 布局轴不碰操作手感
    assert 'html[data-input="keymouse"]' in desktop_css
    assert 'html[data-input="touch"]' not in desktop_css
    assert "scrollbar-width: thin;" in desktop_css
    assert "max-width: 1040px" in large_css     # 大屏加宽的版心
    # 旧单轴选择器全站不许再出现 (注释里讲历史不算)
    assert 'html[data-client=' not in html


def test_music_18103_dock_volume_bubble():
    """船坞音量气泡 (1.8.103, 用户点名「非移动端底下除了菜单/播放气泡/
    搜索, 再加一个音量调节气泡, 点击后可以调节音量」): 键鼠端专属 ——
    挂操作轴 (勿用尺寸轴, iPad 大屏也是触摸), 触摸端基线整个不显示
    (音量归系统硬件键, iOS 的 audio.volume 只读); 落地走
    setDesktopVolume 全应用唯一事实源 (播放页音量条/船坞气泡/↑↓ 键
    三处同源); Esc 收层进 music-global-events.js 链头 (最小的层最先收)。"""
    html = music_page_shell()
    keys = (MUSIC_STATIC / "js" / "music-desktop-keys.js").read_text(
        encoding="utf-8")
    dock_js = (MUSIC_STATIC / "js" / "music-dock-volume.js").read_text(
        encoding="utf-8")
    events_js = (MUSIC_STATIC / "js" / "music-global-events.js").read_text(
        encoding="utf-8")
    assert 'id="dock-volume"' in html            # 船坞第四键 (键鼠端)
    assert 'id="volume-pop"' in html and 'id="dock-volume-range"' in html
    assert 'src="/music/static/js/music-dock-volume.js?v=' in html
    # 键鼠端放行上桌 / 触摸端基线整个不显示 (操作轴, 不是尺寸轴)
    assert 'html[data-input="keymouse"] #dock-volume { display: flex; }' \
        in html
    assert "#dock-volume { display: none; }" in html
    assert 'html[data-size="large"] #dock-volume' not in html
    # 拖条与键鼠层同一个事实源: 两根音量条 (播放页/船坞) + 记档同步
    assert "setDesktopVolume" in dock_js
    assert 'for (const id of ["fp-volume", "dock-volume-range"])' in keys
    assert "$(\"#volume-pop\")" in events_js     # Esc 链头先收气泡


def test_music_1839_desktop_input_batch():
    """1.8.39 桌面键鼠适配 (用户点名「优化一下桌面ui, 适配键鼠操作」):
    键盘快捷键收在 music-desktop-keys.js, 运行时判操作轴 (翻轴即时生效),
    焦点在控件上或菜单弹着时让路; 鼠标手感收在 music-desktop.css;
    左滑删除在键鼠端改成悬停亮钮 —— 前提是 JS 收起时清行内样式, 藏态交回
    CSS 基线, :hover 才拿得回接管权 (行内样式永远压着样式表)。
    1.8.102 键位补全 (用户实报「PC Chrome 打开并没有适配键鼠」): ① 让路
    规矩收紧 —— 点过的按钮/链接不再吞键 (Windows Chrome 点按即聚焦, 焦点
    停在钮上时空格/箭头全哑); ② 箭头按桌面惯例改快退/快进 (钳在曲目时长
    内), 切歌让给 Shift+左右; ③ 音量 —— 播放页底行加音量条 (触摸端基线
    藏, 键鼠端放行), ↑/↓ 键与条同源, 记档下回接着用。"""
    html = music_page_shell()
    keys = (MUSIC_STATIC / "js" / "music-desktop-keys.js").read_text(
        encoding="utf-8")
    css = (MUSIC_STATIC / "css" / "music-desktop.css").read_text(
        encoding="utf-8")
    player_css = (MUSIC_STATIC / "css" / "music-player.css").read_text(
        encoding="utf-8")
    swipe = (MUSIC_STATIC / "js" / "music-swipe-delete.js").read_text(
        encoding="utf-8")
    assert 'src="/music/static/js/music-desktop-keys.js?v=' in html
    # 键盘层运行时判操作轴 (1.8.103 翻轴即时生效); 让路规矩写在代码里
    # (button/a 出队 —— 点按即聚焦的平台上, 焦点停在钮上会把键盘层哑掉)
    assert "function bindDesktopKeys()" in keys
    assert "if (!isKeyMouseInput()) return;" in keys   # 触摸端不接管
    assert 'el.closest("input, textarea, select, [contenteditable]")' \
        in keys                                         # 真输入控件: 键归控件
    assert "button, a" not in keys
    assert "$(\"#pop-menu\").hidden || !$(\"#track-menu\").hidden" in keys
    assert "playerToggle();" in keys                    # 空格播停
    assert 'if (event.key === "/") {' in keys
    assert '$("#dock-search").click();' in keys         # / 直达搜索 (复用船坞)
    # ② 箭头: 快退/快进 (电脑惯例是走进度); 切歌 Shift+左右
    assert "DESKTOP_SEEK_S" in keys
    assert "playbackDuration();" in keys                # 钳在曲目时长内
    assert "audio.currentTime = clampNumber(audio.currentTime + step" in keys
    assert "if (event.shiftKey) {" in keys              # Shift+左右才切歌
    assert "playerPrevious();" in keys and "playerNext();" in keys
    # ③ 音量: 键 + 记档 (条的分轴断言在船坞气泡测里)
    assert "DESKTOP_VOLUME_STEP" in keys
    assert 'function setDesktopVolume(' in keys
    assert 'localStorage.setItem("music-volume"' in keys  # 下回打开接着用
    assert "$(\"#fp-volume\")" in keys
    assert 'id="fp-volume"' in html                     # 播放页底行最左一根
    assert "#fp-volume { display: none; }" in player_css  # 触摸端音量归硬件键
    assert 'html[data-input="keymouse"] #fp-volume {' in css  # 键鼠端放行
    # 鼠标手感的关键几条 (作用域规矩由上一测守)
    for frag in ['html[data-input="keymouse"] button { cursor: pointer; }',
                 "content: attr(aria-label);",       # 图标钮提示复用 aria-label
                 'html[data-input="keymouse"] .swipe-wrap:hover { --veil: 1; }',
                 'html[data-input="keymouse"] :focus-visible {']:
        assert frag in css, f"desktop.css 缺 {frag}"
    # 行距密度 (1.8.103): 触摸基线 8px 行衬是手指的尺寸, 键鼠收紧一档
    assert 'html[data-input="keymouse"] .track-row,' in css
    # 悬停亮删除钮的前提: 收起清行内样式 (不是写 0)
    assert 'del.style.transform = x ? `translateX(${SWIPE_REVEAL + x}px)` : "";' \
        in swipe
    assert 'wrap.style.removeProperty("--veil")' in swipe


def test_music_volume_ui_axes_split():
    """音量控制的分端规矩 (1.5.1 用户点名「音量条去掉吧」全平台撤除 →
    1.8.102 键鼠端回归): 触摸端音量归设备硬件键, 基线一根不剩 —— iOS 的
    audio.volume 写了也白写, 1.5.0 的 WebAudio 增益又拖不动还脱开音量键,
    那套机器不许再爬回来; 电脑没有硬件音量键可按, 键鼠端在播放页底行和
    船坞气泡各放一处 (1.8.103 双轴: 放行只许走操作轴
    html[data-input="keymouse"], 勿用尺寸轴 —— iPad 大屏也是触摸)。
    回归: WebAudio 音量路由全套禁词 + 播放器模块不碰音量 + 基线藏。"""
    html = music_page_shell()
    player = music_player_js()
    keys = (MUSIC_STATIC / "js" / "music-desktop-keys.js").read_text(
        encoding="utf-8")
    for gone in ["AudioContext", "createGain", "createMediaElementSource",
                 "ensureVolumeRouting", "loadSavedVolume", "nativeVolumeWorks",
                 "applyVolume", "volume-off"]:
        assert gone not in player, f"音量残留: {gone}"
        assert gone not in html, f"音量残留 (html): {gone}"
        assert gone not in keys, f"音量残留 (keys): {gone}"
    # 播放器模块一根音量线都没有 —— 全应用唯一写 audio.volume 的地方是
    # 键鼠层 (运行时判轴, 触摸端不写 —— Android 写了会真生效而条又藏着)
    assert ".volume" not in player
    assert "audio.volume" in keys
    # 基线藏 (触摸端), 只有键鼠端放行 —— 两句都在拼进 html 的 css 里
    assert "#fp-volume { display: none; }" in html
    assert 'html[data-input="keymouse"] #fp-volume {' in html
