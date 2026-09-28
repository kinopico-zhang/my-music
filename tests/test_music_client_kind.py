"""My Music 客户端识别测试 (1.8.35, 用户点名「前端要判断用户的客户端,
以后移动端和 PC 端设计不一样」): 主指针粗细判移动/桌面, UA 兜底, ?ui=
覆写预览另一端; <html data-client> 是唯一事实源, 桌面分叉规则全收在
music-desktop.css 且一律 html[data-client="desktop"] 作用域 (移动端 =
无前缀基线不动)。分类真值表在 tests/js/music-client.test.mjs (node 直测)。"""
from tests.music_static_files import (MUSIC_STATIC, music_page_shell,
                                      music_player_js)


def test_music_1835_client_kind_wiring():
    """识别模块先于 boot 加载 (boot 渲染前 data-client 就位); 启动即写
    html[data-client], 主指针变了 (插拔鼠标/平板模式翻转) 跟着换;
    JS 分叉入口 clientKind()/isDesktopClient()。"""
    html = music_page_shell()
    client_js = (MUSIC_STATIC / "js" / "music-client.js").read_text(encoding="utf-8")
    assert html.index("music-client.js") < html.index("music-app-boot.js")
    for frag in ["function classifyClient(",
                 'window.matchMedia("(pointer: coarse)")',
                 'addEventListener("change", applyClientKind);',
                 "document.documentElement.dataset.client = classifyClient(",
                 "function isDesktopClient()"]:
        assert frag in client_js, f"music-client.js 缺 {frag}"


def test_music_1835_desktop_css_scoping():
    """桌面分叉的规矩: 桌面规则一律 html[data-client="desktop"] 作用域,
    不写 html[data-client="mobile"] (移动端 = 无前缀基线, 规则留在原文件);
    第一条分叉已落地 —— 电脑上恢复滚动条 (移动端仍整页不画)。"""
    html = music_page_shell()
    css = (MUSIC_STATIC / "css" / "music-desktop.css").read_text(encoding="utf-8")
    assert "music-desktop.css?v=" in html          # 页面挂上了分叉样式
    assert 'html[data-client="desktop"]' in css
    assert 'html[data-client="mobile"]' not in css
    assert "scrollbar-width: thin;" in css         # 第一条桌面分叉: 滚动条


def test_music_1839_desktop_input_batch():
    """1.8.39 桌面键鼠适配 (用户点名「优化一下桌面ui, 适配键鼠操作」):
    键盘快捷键 (空格播停//直达搜索) 收在 music-desktop-keys.js, 只在桌面端
    挂, 焦点在控件上或菜单弹着时让路; 鼠标手感 (手型光标/悬停亮一档/图标
    钮提示/键盘焦点环/行悬停播放符) 收在 music-desktop.css; 左滑删除在桌面
    端改成悬停亮钮 —— 前提是 JS 收起时清行内样式, 藏态交回 CSS 基线,
    :hover 才拿得回接管权 (行内样式永远压着样式表)。
    1.8.102 键位补全 (用户实报「PC Chrome 打开并没有适配键鼠」): ① 让路
    规矩收紧 —— 点过的按钮/链接不再吞键 (Windows Chrome 点按即聚焦, 焦点
    停在钮上时空格/箭头全哑, 整个键盘层形同虚设); ② 箭头按桌面惯例改
    快退/快进 (钳在曲目时长内), 切歌让给 Shift+左右; ③ 音量 —— 全应用原先
    一根音量控制都没有: 播放页底行加音量条 (移动端基线藏, 桌面端放行,
    iOS 的 audio.volume 只读), ↑/↓ 键与条同源, 记档下回接着用。"""
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
    # 键盘层只在桌面端挂; 让路规矩写在代码里 (1.8.102 收紧: button/a 出
    # 队 —— 点按即聚焦的平台上, 焦点停在钮上会把整个键盘层哑掉)
    assert "function bindDesktopKeys()" in keys
    assert "if (!isDesktopClient()) return;" in keys   # 移动端不挂
    assert 'el.closest("input, textarea, select, [contenteditable]")' \
        in keys                                         # 真输入控件: 键归控件
    assert "button, a" not in keys
    assert "$(\"#pop-menu\").hidden || !$(\"#track-menu\").hidden" in keys
    assert "playerToggle();" in keys                    # 空格播停
    assert 'if (event.key === "/") {' in keys
    assert '$("#dock-search").click();' in keys         # / 直达搜索 (复用船坞)
    # ② 箭头: 快退/快进 (1.8.39 原是切歌, 电脑惯例是走进度); 切歌 Shift+左右
    assert "DESKTOP_SEEK_S" in keys
    assert "playbackDuration();" in keys                # 钳在曲目时长内
    assert "audio.currentTime = clampNumber(audio.currentTime + step" in keys
    assert "if (event.shiftKey) {" in keys              # Shift+左右才切歌
    assert "playerPrevious();" in keys and "playerNext();" in keys
    # ③ 音量: 键 + 条 + 记档 (基线藏/桌面放行在下面 CSS 断言)
    assert "DESKTOP_VOLUME_STEP" in keys
    assert 'function setDesktopVolume(' in keys
    assert 'localStorage.setItem("music-volume"' in keys  # 下回打开接着用
    assert "$(\"#fp-volume\")" in keys
    assert 'id="fp-volume"' in html                     # 播放页底行最左一根
    assert "#fp-volume { display: none; }" in player_css   # 移动端音量归硬件键
    assert 'html[data-client="desktop"] #fp-volume {' in css  # 桌面端放行上桌
    # 鼠标手感的关键几条 (作用域规矩由上一测守)
    for frag in ['html[data-client="desktop"] button { cursor: pointer; }',
                 "content: attr(aria-label);",        # 图标钮提示复用 aria-label
                 'html[data-client="desktop"] .swipe-wrap:hover { --veil: 1; }',
                 'html[data-client="desktop"] :focus-visible {']:
        assert frag in css, f"desktop.css 缺 {frag}"
    # 悬停亮删除钮的前提: 收起清行内样式 (不是写 0)
    assert 'del.style.transform = x ? `translateX(${SWIPE_REVEAL + x}px)` : "";' \
        in swipe
    assert 'wrap.style.removeProperty("--veil")' in swipe


def test_music_volume_ui_desktop_only():
    """音量控制的分端规矩 (1.5.1 用户点名「音量条去掉吧」全平台撤除 →
    1.8.102 分端回归): 移动端音量归设备硬件键, 基线继续一根不剩 —— iOS
    的 audio.volume 写了也白写, 1.5.0 的 WebAudio 增益又拖不动还脱开音量
    键, 那套机器不许再爬回来; 电脑没有硬件音量键可按 (1.8.102 用户实报
    「PC Chrome 打开并没有适配键鼠」), 桌面端在播放页底行放一根
    (music-desktop.css 放行, 键盘 ↑/↓ 同源, 记档下回接着用)。
    回归: WebAudio 音量路由全套禁词 + 播放器模块不碰音量 + 基线藏 +
    放行只许走 html[data-client="desktop"] 作用域。"""
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
    # 桌面键鼠层 (这层移动端不挂, 移动端自然没有音量 UI)
    assert ".volume" not in player
    assert "audio.volume" in keys
    # 基线藏 (移动端), 只有桌面端放行 —— 两句都在拼进 html 的 css 里
    assert "#fp-volume { display: none; }" in html
    assert 'html[data-client="desktop"] #fp-volume {' in html
