"""My Music 视口上边界接线测试: 1.8.19 立的全局规矩 --top-clear (固定控件
都钉在系统磨砂带之下)。拆自 test_music_wiring_viewport.py (1.8.32 批:
视口文件加冷开自愈用例后超 200 行硬上限, 按域分家)。"""
from tests.music_static_files import MUSIC_STATIC, music_page_shell


def test_music_top_clear_boundary():
    """1.8.19 立的全局上边界 (用户令「固定的控件都不要超过这个边界」):
    顶部系统磨砂带糊控件这事此前各修各的 (1.8.10 体检窗、1.8.17 页顶条、
    1.8.19 搜索框都各自躲过一回), 这版归成一条规矩 —— 变量 --top-clear
    定义在 music-base.css, 两条地界取深: 浏览器 env+36 (.pane-title 那条
    1.8.17 实测干净)、独立模式 96px (--top-floor 老地界, iOS 26 磨砂带
    env() 谎报 0)。固定控件全数钉在它之下: 搜索页顶条 / 播放页抓手
    (app+share) / 体检窗 / 长按菜单 (拿隐形量尺 #top-clear-probe 的
    offsetTop 读回边界值 —— CSS 变量进 JS 不用 getComputedStyle)。分享页
    自包含, 自家 :root 同名 (没有独立模式地界, env+36 即可)。"""
    html = music_page_shell()
    css = {name: (MUSIC_STATIC / "css" / f"{name}.css").read_text(
        encoding="utf-8") for name in
        ("music-base", "music-search", "music-player", "music-menus",
         "share-viewer-page", "share-viewer-player")}
    js = {name: (MUSIC_STATIC / "js" / f"{name}.js").read_text(
        encoding="utf-8") for name in ("music-viewport-hud",
                                       "music-track-menus")}
    # 变量本体: 两条地界取深 (浏览器 env+36 / 独立模式 --top-floor 96px)
    assert ("--top-clear: max(calc(env(safe-area-inset-top, 0px) + 36px),"
            in css["music-base"])
    assert "var(--top-floor));" in css["music-base"]
    # 固定控件挨个验钉
    assert "padding: var(--top-clear) 16px 0;" in css["music-search"]
    assert "margin-top: var(--top-clear);" in css["music-player"]
    # 分享页全屏播放页 1.8.130 起样式直引 music-player.css (上一行那钉
    # 连分享页一起管), share-viewer-player.css 不再有播放页规则 —— 抓手
    # 的验钉挪去 test_music_share_player_wiring (钉 css 引用)
    # 视口体检红框 1.8.43 撤了 (用户点名), HUD 不再是钉顶控件 —— 它在
    # --top-clear 之下的样式挂靠一并消失, 这里不再有它的验钉
    # 长按菜单的竖向下限: 隐形量尺钉在边界上, JS 读 offsetTop 当下限
    assert '<i id="top-clear-probe" aria-hidden="true">' in html
    assert "#top-clear-probe {" in css["music-menus"]
    assert 'const probe = $("#top-clear-probe");' in js["music-track-menus"]
    assert "probe.offsetTop" in js["music-track-menus"]
    assert ("menu.style.top = `${Math.max(minY, Math.round(y))}px`;"
            in js["music-track-menus"])
    # 分享页自包含: 自家 :root 同名变量 (没有独立模式地界, env+36 即可)
    assert ("--top-clear: calc(env(safe-area-inset-top, 0px) + 36px);"
            in css["share-viewer-page"])
