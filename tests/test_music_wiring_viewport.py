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
    1.8.10 埋的回传 + 1.8.11 一整轮实测把话说死了: iOS 18 独立模式键盘
    收起那一下, WebKit 把还原高度记坏 (812→771, 差的 41 就是黑带), 之后
    页面里什么都掰不动 —— 翻面/meta 踢十一连发原地不动, 连真实开合键盘
    三轮也只回落到 771 (社区验方在这台机器上无效); 而开局是干净的 812:
    换新文档就复位。1.8.12 对策: ① 右划起手 (横向坐实) 就摘焦点, 键盘
    从拖动第一下就开始收; ② 冻矮 0.7s 实锤 (闩住只喊一次) → 体检窗亮
    「深度修复 · 刷新复位」(播放现场本来有 5 秒一存的档, 回来原曲原秒);
    ③ 开局/深修归来都报数回传, 灵不灵日志有账。误诊修正 (1.8.11): 判据
    看焦点在不在输入框, 不拿 vv 与 inner 互比 (iOS 18 独立模式里恒相等)。
    流水全程回传 data/viewport-doctor.jsonl (见 test_music_viewport_log.py)。"""
    html = music_page_shell()
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
    assert ('music-viewport-hud.js?v=3' in html
            and 'music-viewport-heal.js?v=2' in html
            and 'music-viewport-doctor.js?v=3' in html)
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
    # 深修 (heal 模块, 唯一被两轮回传证明有效的手法): 存标记 → 当场送流水
    # → 刷新换新文档 (播放现场有档: 5 秒一存 + pagehide, 回来原曲原秒)
    assert ('localStorage.setItem("music.deepRepairAt"' in heal
            and "ViewportHUD.send();" in heal
            and "location.reload();" in heal)
    # 医生调度: 实锤只亮窗 (深修按钮在窗上, 刷不刷新用户点头) —— 不自动
    # 五连招了 (翻面/唤键盘/meta 踢全在 1.8.11 回传里证明无效, 撤干净)
    assert "ViewportHUD.show();" in doctor
    assert "ViewportHeal.reloadDeep();" in doctor
    for dead in ("ViewportHeal.flip", "metaKick", "roundtrip", "kb-veil",
                 "kb-repair"):
        assert dead not in doctor and dead not in heal, dead
    assert "kb-repair" not in html        # 探针 (1.8.9) 连样式一起退役
    # 开局报数; 深修归来 (15 秒内带标记) 复位成没成当场回传, 再清标记
    assert "开局 i${window.innerHeight} 满高${full}" in doctor
    assert ('localStorage.getItem("music.deepRepairAt"' in doctor
            and "Date.now() - at < 15000" in doctor
            and "深修归来" in doctor and "复位成功" in doctor
            and 'localStorage.removeItem("music.deepRepairAt");' in doctor)
    # 体检窗 (HUD 管「说」): 挪出刘海/状态栏的模糊地带 (1.8.10 弹在
    # top:8px 用户点不到); 刷新是有分量的动作, 只认按钮那一下 (别误触)
    assert '"#doctor-hud{' in hud
    assert "top:calc(env(safe-area-inset-top) + 8px)" in hud
    assert '"深度修复 · 刷新复位"' in hud
    assert 'fix.addEventListener("click", deepRepair);' in hud
    assert '"#doctor-hud button{' in hud
    assert "hudTick = setInterval" in hud
    assert 'ViewportHUD.wire({ stat, deepRepair });' in doctor
    assert '"My Music 1.8.12 视口体检' in doctor
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
