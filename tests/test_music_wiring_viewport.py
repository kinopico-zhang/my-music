"""My Music 视口健康接线测试: 键盘往返后 iOS 赖账的三味病 (滚位/偏移/高度
冻矮) 与各版本的对策 —— 静态文本断言, 不碰数据库。拆自
test_music_wiring_search.py (黑带这条线的守卫按域归拢到这里)。"""
from tests.music_static_files import MUSIC_STATIC, music_page_shell


def test_music_187_keyboard_scroll_repair():
    """1.8.7 修「搜索页开关几回, 回主页底部一块黑、页面没充满屏」(用户
    追了两个版本, 重启 app 都不消): iOS 键盘收走后赖账有两味 —— ① 键盘
    避让把文档滚了 (overflow:hidden 拦不住, window.scrollY 赖非零而视口
    偏移是 0; 1.8.5 只查偏移, 漏的正是这味); ② 视口停在偏移上 (1.8.5
    修过)。收尾还经常一声事件不响, 脏滚位会被 iOS 会话恢复原样带回重启
    后。对策在全局事件层: 复位条件补查文档滚位; 焦点一走迟两拍补跑;
    滚动恢复关掉; 开局/pageshow/回前台各清一次账。"""
    ge = (MUSIC_STATIC / "js" / "music-global-events.js").read_text(
        encoding="utf-8")
    # 复位条件: 文档滚位 + 视口偏移两味都查; 焦点在输入框里不复位
    # (别跟键盘避让的让位滚动打架)
    assert "!typing && (window.scrollX || window.scrollY" in ge
    assert "|| visualViewport.offsetLeft" in ge
    assert "window.scrollTo(0, 0);" in ge
    # 收尾没事件也兜得住: 焦点一离开输入框迟两拍各补一次
    # (层滑出/移除的 420ms 罩在这个窗口里)
    assert 'document.addEventListener("focusout", () => {' in ge
    assert "setTimeout(lift, 350);" in ge
    assert "setTimeout(lift, 900);" in ge
    assert "setTimeout(lift, 1800);" in ge   # 1.8.8 加长一拍 (100% 复现兜底)
    # iOS 会话恢复别把脏滚位带回来 (重启 app 黑区还在的元凶):
    # 滚动恢复关掉 + 页面一亮出来就清账 (开局/pageshow/回前台)
    assert 'if ("scrollRestoration" in history) history.scrollRestoration = "manual";' in ge
    assert "addEventListener(\"pageshow\", lift);" in ge
    assert "if (!document.hidden) lift();" in ge
    assert "    lift();\n    addEventListener(\"pageshow\", lift);" in ge


def test_music_189_viewport_freeze_repair():
    """1.8.9 起「键盘没收起就右划关掉搜索, 底部一条黑带」的诊治线。
    三轮回传把病根的数学都对上了 (1.8.13): iOS 18 独立模式键盘收起那一下,
    WebKit 把「还原高度」记成 键盘弹起时 innerHeight + 收起起手时视口偏移
    (两回都是 415+356 → 冻在 771/776), 正确答案 812 = 415+397 (键盘整个
    高度)。对策: ① 右划起手 (横向坐实) 就摘焦点; ② focusout 一到 (键盘还
    开着) 就把视口偏移「按住」在键盘整个高度上, 一帧一帧跟系统的回滚抢,
    innerHeight 回满 (账记对了) 或 1 秒上限才松手归位; ③ lift() 在按住期间
    避让 (别把钉住的偏移抹了); ④ 冻矮 0.7s 实锤 → 体检窗给真话 (划掉重开
    秒复原 —— 刷新实测无效, 坏值跟着 webview 走)。误诊修正 (1.8.11): 判据
    看焦点在不在输入框, 不拿 vv 与 inner 互比 (恒相等)。流水全程回传
    data/viewport-doctor.jsonl (见 test_music_viewport_log.py)。"""
    html = music_page_shell()
    ge = (MUSIC_STATIC / "js" / "music-global-events.js").read_text(
        encoding="utf-8")
    panes = (MUSIC_STATIC / "js" / "music-push-panes.js").read_text(
        encoding="utf-8")
    swipe = (MUSIC_STATIC / "js" / "music-pane-swipe.js").read_text(
        encoding="utf-8")
    doctor = (MUSIC_STATIC / "js" / "music-viewport-doctor.js").read_text(
        encoding="utf-8")
    heal = (MUSIC_STATIC / "js" / "music-viewport-heal.js").read_text(
        encoding="utf-8")
    hud = (MUSIC_STATIC / "js" / "music-viewport-hud.js").read_text(
        encoding="utf-8")
    # ① 起手摘焦点 (横向坐实即 blur, 键盘从拖动第一下就开始收)
    assert ("if (pane.contains(document.activeElement))"
            " document.activeElement.blur();") in swipe
    # ② 收稳才移除: 两处收层共用同一个等待函数, 判据交医生, 上限 1.2s
    assert "function removePaneWhenSettled(pane)" in panes
    assert "removePaneWhenSettled(item.pane);" in panes    # closePushStack
    assert "removePaneWhenSettled(pane);" in swipe         # 手势收层
    assert "ViewportDoctor.settled()" in panes
    assert "Date.now() - start > 1200" in panes   # 键盘赖着: 最多再等 1.2s
    # 装载顺序: HUD 先载 (医生 wire 时在场), 再治疗手法, 再医生
    assert ('music-viewport-hud.js?v=4' in html
            and 'music-viewport-heal.js?v=3' in html
            and 'music-viewport-doctor.js?v=4' in html)
    # 只医独立模式 iPhone: 浏览器 Safari 工具栏自己收放 (满高基准立不住),
    # 安卓 interactive-widget 布局自己缩 (是正常不是病)
    assert 'window.matchMedia("(display-mode: standalone)").matches' in doctor
    assert "/iP(hone|ad|od)/.test(navigator.userAgent)" in doctor
    # 满高基准: 开局读档跨重启 + 长高刷新 + 转屏按新方向重立
    assert '"music.fullInner"' in doctor
    assert 'matchMedia("(orientation: landscape)").matches' in doctor
    assert "return window.innerHeight >= full - 12;" in doctor  # 收稳 = 回满
    # 键盘开着的判据 (1.8.11 修正): 焦点在输入框 —— iOS 18 独立模式里
    # vv 与 inner 永远相等, 互比是空转 (1.8.10 误诊过还抢了用户焦点)
    assert 'el.tagName === "INPUT" || el.tagName === "TEXTAREA"' in doctor
    # 冻矮判定: 比满高矮 12px 以上 + 值定住 0.7s 才实锤; 闩住只喊一次
    assert "full - window.innerHeight > 12" in doctor
    assert "}, 700);" in doctor
    assert "declared = true;" in doctor
    # 按住手法 (heal, 1.8.13 验方): focusout 同步把偏移钉到键盘整个高度
    # (抢在收起动画起手前 —— 记账在起手那一下), rAF 一帧一帧跟系统回滚抢,
    # 回满或 1 秒才松手归位; 焦点回来了 (键盘没走) 就撤手别搅局
    assert ('window.scrollTo(0, overlap);' in heal
            and "requestAnimationFrame(hold);" in heal
            and 'holding: () => holding' in heal
            and "撤手 (焦点回来了)" in heal)
    assert ('松手 i${window.innerHeight} y${y}' in heal
            and '" 回满"' in heal)      # 松手报数: i812=按住了, i771=没按住
    # 医生调度: focusout 一到 (键盘还开着) 就按住; 修不好时窗口给真话
    assert ('ViewportHeal.holdDuringDismissal('
            'full - window.innerHeight, full, "收键");' in doctor)
    assert '"治不了就划掉重开应用 (秒复原)"' in doctor
    assert 'ViewportHUD.wire({ stat });' in doctor
    assert '"My Music 1.8.13 视口体检' in doctor
    # lift() 避让: 按住期间归零复位 = 拆台 (松手时按住自己会归位)
    assert "ViewportHeal.holding()" in ge
    # 换新文档的路 1.8.12 试过死了 (归来还是矮的, 坏值跟着 webview 走):
    # 刷新/深修那条线撤干净, 只留开局报数 (带这趟文档怎么来的, 拆连开谜团)
    for dead in ("reloadDeep", "deepRepair", "deepRepairAt", "kb-repair"):
        assert dead not in doctor and dead not in heal and dead not in hud, dead
    assert ("performance.getEntriesByType(\"navigation\")" in doctor
            and "开局 i${window.innerHeight} 满高${full} ${nav}" in doctor)
    # 体检窗 (HUD 管「说」): 挪出刘海/状态栏的模糊地带 (1.8.10 弹在
    # top:8px 用户点不到); 没按钮了 —— 能治的自动治, 治不了的直说
    assert '"#doctor-hud{' in hud
    assert "top:calc(env(safe-area-inset-top) + 8px)" in hud
    assert 'createElement("button")' not in hud
    assert "hudTick = setInterval" in hud
    # 回传通道: 每行流水排进发件箱, 攒 3 秒一批 POST /music/api/viewport-log
    # (keepalive 兜最后一趟, 失败退回箱里), 切后台/离开页面就送
    assert 'fetch("/music/api/viewport-log"' in hud
    assert "keepalive: true," in hud
    assert "setTimeout(send, 3000);" in hud
    assert "if (document.hidden) send();" in hud
    assert 'addEventListener("pagehide", send);' in hud
    # 快照字段与后端 ViewportEvent 对齐 (inner/vv/top/left/scrollY + 时间戳)
    assert "function snapshot(line)" in hud
    assert "inner: window.innerHeight," in hud
