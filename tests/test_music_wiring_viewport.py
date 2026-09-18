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
    """1.8.9 起「键盘没收起就右划关掉搜索, 底部一条黑带」的诊治线;
    1.8.10 埋的回传在手机上实锤了病根, 1.8.11 按数据治:
    iOS 18 独立模式键盘弹起时 innerHeight 跟着缩 (812→415), 收起后冻在
    771 (差的 41 正是黑带) 一分多钟不回来 —— WebKit 上游老病 (cordova
    #1575 同族), scrollTo/探针 focus→blur/换 100% 高度链都是社区验过没用
    的路 (1.8.10 的定时器探针在回传里零 resize, 印证)。现三层对策:
    ① 右划起手 (横向坐实) 就摘焦点, 键盘从拖动第一下就开始收;
    ② 早治: focusout 后 140/450ms 就对满高元素做 display 翻面夹同步
       reflow (cederhook/dev.to 验方), 磨砂罩遮闪帧, 黑带来不及露头;
    ③ 冻矮 0.7s 实锤 (闩住只喊一次) → 修复阶梯 (翻面→身体翻面→[手势]
       键盘往返→meta 踢), 体检窗挪出刘海地带且整窗可点。误诊修正:
       判据看焦点在不在输入框 (1.8.10 拿 vv 与 inner 互比恒真, 键盘还
       开着就喊病发, 还抢用户焦点)。流水全程回传
       data/viewport-doctor.jsonl (见 test_music_viewport_log.py)。"""
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
    assert ('music-viewport-hud.js?v=2' in html
            and 'music-viewport-heal.js?v=1' in html
            and 'music-viewport-doctor.js?v=2' in html)
    # 只医独立模式 iPhone: 浏览器 Safari 工具栏自己收放 (满高基准立不住),
    # 安卓 interactive-widget 布局自己缩 (是正常不是病)
    assert 'window.matchMedia("(display-mode: standalone)").matches' in doctor
    assert "/iP(hone|ad|od)/.test(navigator.userAgent)" in doctor
    # 满高基准: 开局读档跨重启 + 长高刷新 + 转屏按新方向重立
    assert '"music.fullInner"' in doctor
    assert 'matchMedia("(orientation: landscape)").matches' in doctor
    assert "return window.innerHeight >= full - 12;" in doctor  # 收稳 = 回满
    # 键盘开着的判据 (1.8.11 修正): 焦点在输入框 —— iOS 18 独立模式里
    # vv 与 inner 永远相等, 1.8.10 拿它们互比是空转 (误诊还抢了用户焦点)
    assert 'el.tagName === "INPUT" || el.tagName === "TEXTAREA"' in doctor
    # 冻矮判定: 比满高矮 12px 以上 + 值定住 0.7s 才实锤; 闩住只喊一次
    # (1.8.10 心跳每 1.5s 重复喊了一分多钟, 白刷回传发件箱)
    assert "full - window.innerHeight > 12" in doctor
    assert "}, 700);" in doctor
    assert "declared = true;" in doctor
    # 早治 (验方的时机): 收键盘动画里就翻面, 黑带来不及露头; 干净收起
    # 回满高 sick() 拦住罩子都不亮; 探针自己的收起不掺和 (那是往返在干活)
    assert 'event.target.id !== "kb-repair"' in doctor
    assert 'ViewportHeal.flip(document.getElementById("main"), "收尾");' in doctor
    assert "}, 140);" in doctor
    # 翻面手法 (heal 模块, 验方原样): display none→'' 夹同步 reflow,
    # 滚位存还, 磨砂罩先罩严 (淡入 .22s) 再动手、缓缓掀开
    assert "el.style.display = \"none\";" in heal
    assert "void el.offsetHeight;" in heal
    assert "el.style.display = keep;" in heal
    assert "#kb-veil{" in heal
    assert "backdrop-filter:blur(26px)" in heal
    # 修复阶梯 (间隔够日志看清每一步成效): 自动档上限 2 次, 手势档 3 次,
    # 点体检窗 = force 不计次只防连击
    assert "gRepairs >= 3 : aRepairs >= 2" in doctor
    assert "ViewportHeal.flip(document.getElementById(\"main\"), tag);" in doctor
    assert "ViewportHeal.flip(document.body, `${tag}②`);" in doctor
    assert "ViewportHeal.roundtrip(probe, `${tag}③`);" in doctor
    assert "ViewportHeal.metaKick(`${tag}④`);" in doctor
    # 键盘往返: 手势上下文才唤得动键盘 (定时器唤不动, 1.8.10 回传实锤),
    # 真弹起来 (矮过 100px) 稳一拍再收, 唤不动 1.5s 认了; 探针还是那个
    # 常驻隐形输入框 (样式在 music-base.css), 只在往返里干活
    assert ('probe.id = "kb-repair";' in doctor
            and "document.body.appendChild(probe);" in doctor)
    assert "start - window.innerHeight > 100" in heal
    assert "键盘唤不动" in heal
    # meta 踢: 视口 meta 摘 80ms 再戴回去 (压箱底的大锤)
    assert 'meta[name="viewport"]' in heal
    # 借用户下一次触屏补一趟手势修复 (定时器没手势未必唤得动键盘)
    assert '"pointerdown", () => {' in doctor
    assert "{ once: true });" in doctor
    # 体检窗 (HUD 管「说」): 挪出刘海/状态栏的模糊地带 (1.8.10 弹在
    # top:8px 用户点不到), 整窗可点 = 立即修复, 亮着期间每秒刷数字
    assert '"#doctor-hud{' in hud
    assert "top:calc(env(safe-area-inset-top) + 8px)" in hud
    assert "repair({ gesture: true, force: true })" in hud
    assert '"#doctor-probe{' in hud
    assert '"立即修复"' in hud
    assert "hudTick = setInterval" in hud
    assert 'ViewportHUD.wire({ stat, repair, full: () => full });' in doctor
    assert '"My Music 1.8.11 视口体检' in doctor
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
