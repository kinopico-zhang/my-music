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
    """1.8.9 修「键盘没收起就右划关掉搜索, 底部一条黑带」的真病根 (用户
    录屏逐帧量出来的): 键盘收起动画走到半路时移除聚焦过的层, iOS 把
    布局视口整个冻在没收满的矮个上 —— 顶部纹丝不动 (不是 1.8.5/1.8.7
    修的偏移/滚位那两味, scrollTo 够不着), fixed 船坞和 100dvh 一起
    垫高, 屏底露出纯黑。三层对策: ① 右划起手 (横向坐实) 就摘焦点, 键盘
    从拖动第一下就开始收 (同原生返回手势); ② 收层移除 DOM 等键盘收稳;
    ③ 冻矮自愈 (满高基准 + 隐形探针 focus→blur 逼系统重算)。
    1.8.10 用户复测仍复现, 病根补全: ② 的收稳判据 (vv.height ≥
    innerHeight) 在 innerHeight 跟着键盘一起动的场合恒真, 等了等于没等
    —— 判据移交新立的视口医生模块 (等 innerHeight 回到满高), ③ 的自愈
    与体检窗 (冻矮 0.7s 自动亮相, 现场数字 + 立即修复按钮) 也归医生。
    体检窗还会把流水回传服务器 (POST /api/viewport-log →
    data/viewport-doctor.jsonl, 见 test_music_viewport_log.py) —— 手机上
    复现完直接读档分析, 不用等截图。"""
    html = music_page_shell()
    panes = (MUSIC_STATIC / "js" / "music-push-panes.js").read_text(
        encoding="utf-8")
    swipe = (MUSIC_STATIC / "js" / "music-pane-swipe.js").read_text(
        encoding="utf-8")
    doctor = (MUSIC_STATIC / "js" / "music-viewport-doctor.js").read_text(
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
    # 医生上工: HUD 先载 (医生装载时 wire), 再医生, 都在 global-events 前
    assert 'music-viewport-hud.js?v=1' in html
    assert 'music-viewport-doctor.js?v=1' in html
    # 只医独立模式 iPhone: 浏览器 Safari 工具栏自己收放 (满高基准立不住),
    # 安卓 interactive-widget 布局自己缩 (是正常不是病)
    assert 'window.matchMedia("(display-mode: standalone)").matches' in doctor
    assert "/iP(hone|ad|od)/.test(navigator.userAgent)" in doctor
    # 满高基准: 开局读档跨重启 + 长高刷新 + 转屏按新方向重立
    assert '"music.fullInner"' in doctor
    assert 'matchMedia("(orientation: landscape)").matches' in doctor
    assert "return window.innerHeight >= full - 12;" in doctor  # 收稳 = 回满
    # 自愈探针: 常驻隐形输入框走一趟 focus→blur; 一回赖账最多三次; 定时器
    # 没手势未必唤得动键盘, 埋一手借用户下次触屏补一趟
    assert 'probe.id = "kb-repair";' in doctor
    assert "document.body.appendChild(probe);" in doctor
    assert "setTimeout(() => probe.blur(), 150);" in doctor
    assert "if (repairs >= 3) return;" in doctor
    assert '"pointerdown", () => {' in doctor
    assert "{ once: true });" in doctor
    # 冻矮判定: 键盘收走却比满高矮 12px 以上, 值定住 0.7s 才实锤
    assert "full - window.innerHeight > 12" in doctor
    assert "}, 700);" in doctor
    # 体检窗 (HUD 模块管「说」): 冻矮亮相 + 立即修复按钮 + 屏底红杠画布探针
    # (画得进黑带说明 CSS 还有救); 医生 wire 注入现场数字/修复/满高
    assert '"#doctor-hud{' in hud
    assert '"#doctor-probe{' in hud
    assert '"立即修复"' in hud
    assert 'ViewportHUD.wire({ stat, repair, full: () => full });' in doctor
    assert '"My Music 1.8.10 视口体检' in doctor
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
    # 探针样式 (隐形输入框): 1px 见方全透明钉在视口内
    assert "#kb-repair {" in html
    assert "opacity: 0; pointer-events: none;" in html
