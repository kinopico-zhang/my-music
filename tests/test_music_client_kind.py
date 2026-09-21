"""My Music 客户端识别测试 (1.8.35, 用户点名「前端要判断用户的客户端,
以后移动端和 PC 端设计不一样」): 主指针粗细判移动/桌面, UA 兜底, ?ui=
覆写预览另一端; <html data-client> 是唯一事实源, 桌面分叉规则全收在
music-desktop.css 且一律 html[data-client="desktop"] 作用域 (移动端 =
无前缀基线不动)。分类真值表在 tests/js/music-client.test.mjs (node 直测)。"""
from tests.music_static_files import MUSIC_STATIC, music_page_shell


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
    键盘快捷键 (空格播停/左右切歌//直达搜索) 收在 music-desktop-keys.js,
    只在桌面端挂, 焦点在控件上或菜单弹着时让路; 鼠标手感 (手型光标/悬停
    亮一档/图标钮提示/键盘焦点环/行悬停播放符) 收在 music-desktop.css;
    左滑删除在桌面端改成悬停亮钮 —— 前提是 JS 收起时清行内样式, 藏态交回
    CSS 基线, :hover 才拿得回接管权 (行内样式永远压着样式表)。"""
    html = music_page_shell()
    keys = (MUSIC_STATIC / "js" / "music-desktop-keys.js").read_text(
        encoding="utf-8")
    css = (MUSIC_STATIC / "css" / "music-desktop.css").read_text(
        encoding="utf-8")
    swipe = (MUSIC_STATIC / "js" / "music-swipe-delete.js").read_text(
        encoding="utf-8")
    assert 'src="/music/static/js/music-desktop-keys.js?v=' in html
    # 键盘层只在桌面端挂; 让路规矩写在代码里
    assert "function bindDesktopKeys()" in keys
    assert "if (!isDesktopClient()) return;" in keys   # 移动端不挂
    assert 'el.closest("input, textarea, select, button, a, [contenteditable]")' \
        in keys                                         # 焦点在控件: 键归控件
    assert "$(\"#pop-menu\").hidden || !$(\"#track-menu\").hidden" in keys
    assert "playerToggle();" in keys and "playerPrevious();" in keys \
        and "playerNext();" in keys                     # 空格/左/右箭头
    assert 'if (event.key === "/") {' in keys
    assert '$("#dock-search").click();' in keys         # / 直达搜索 (复用船坞)
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
