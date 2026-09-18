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
    四轮回传把病根的数学都对上了: 独立模式键盘收起那一下, WebKit 把
    「还原高度」记成 键盘弹起时 innerHeight + 收起起手时视口偏移
    (两回都是 415+356 → 冻在 771/776), 正确答案 812 = 415+397 (键盘整个
    高度)。收手抢账三连败 (翻面/meta 踢/键盘往返 1.8.11; 收键按住 1.8.13
    —— 钉住的 397 在回传里看得见, 账还是记 356, 记账读的是系统自家的
    数, 页面钉什么它不看), 1.8.14 预抬也败 (输入框抬到屏幕上部, 让位
    照滚原值 —— 让位根本不看输入框在哪), 1.8.15 换血也败 (页壳变滚动
    器 + ge 撑高咬合, 让位连层内新滚动器都不看, 照滚文档原值 —— 「最近
    滚动祖先」理论死), 1.8.16 定案并实测病愈: 病根在文档本身锁死
    (固定壳), 让位滚成幽灵滚、收键把幽灵滚位记进还原高度; 键盘期解锁
    文档 + 给真高度, 高度回满回锁 (健康对照 my-tesla/my-money 的文档
    天生可滚, 让位是合法滚动)。冻矮 0.7s 实锤 → 体检窗给真话 (再进搜索点
    键盘收起键再返回当场复原 —— 回传实测; 划掉重开只有三成灵)。流水
    全程回传 data/viewport-doctor.jsonl (见 test_music_viewport_log.py)。"""
    html = music_page_shell()
    ge = (MUSIC_STATIC / "js" / "music-global-events.js").read_text(
        encoding="utf-8")
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
    # 装载顺序: HUD 先载 (医生 wire 时在场), 再医生 —— 1.8.15 起治法在
    # 搜索页结构 + ge, heal 模块退役, 装载少一件
    assert ('music-viewport-hud.js?v=7' in html
            and 'music-viewport-doctor.js?v=7' in html
            and "music-viewport-heal" not in html)
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
    # ③ 定案 (1.8.16): 1.8.15 换血那轮回传实锤也败 —— 撑高咬合, 让位连
    # 层内新滚动器都不看, 照滚文档原值 (315/356), 「最近滚动祖先」理论
    # 死; 病根在文档本身: 锁死的固定壳 (html/body overflow:hidden) 让让
    # 位滚成幽灵滚, 收键把幽灵滚位记进还原高度。健康对照 (my-tesla 费用
    # 弹窗 / my-money 记账弹层, 同机实测无恙) 的文档天生可滚, 让位是合法
    # 滚动。治法 = 键盘期解锁文档 + 给真高度 (可见物全 fixed, 肉眼无感),
    # 高度回满再锁回固定壳 (搜索页 1.8.15 的层内滚动结构留着没坏处)
    assert 'document.addEventListener("focusin", (event) => {' in ge
    assert 'document.documentElement.style.setProperty("--kb-full"' in ge
    assert "if (kbFull) return;" in ge            # 键盘已开着 (焦点换框) 不重立
    assert "window.innerHeight >= kbFull - 40" in ge   # 回满屏高 = 键盘走了, 撤撑
    assert 'document.documentElement.style.removeProperty("--kb-full")' in ge
    assert "}, 650);" in ge                       # 650ms 没见矮 (实体键盘): 撤撑
    # 解锁: 拆文档锁 + 给文档真高度 (让位那一滚落在合法可滚的文档上)
    assert 'root.style.overflow = "auto";' in ge
    assert 'root.style.height = "auto";' in ge
    assert "document.body.style.minHeight = `${kbFull}px`;" in ge
    assert "ViewportHUD.say(`解锁${kbFull}`);" in ge
    # 回锁: 高度回满或焦点离开超 2.5s 死线才锁 (抢在收键半路会重新毒化
    # 还原 —— 右划返回时焦点先走键盘后收, 还原必须全程发生在可滚文档上)
    assert 'document.documentElement.style.removeProperty("overflow");' in ge
    assert "!typing && Date.now() - blurredAt > 2500" in ge
    assert 'ViewportHUD.say("回锁");' in ge
    # CSS 侧的结构换血: 层标记 data-view=search 清底衬 (页底条住进流里,
    # 船坞让位那截不要了), 页壳变滚动器 (my-money 弹层同款), 页底条
    # sticky 钉底 (键盘缩矮布局时自动贴键盘上沿, 不用 JS 量高度)
    assert "pane.dataset.view = view;" in panes
    assert '.push-pane[data-view="search"] .pane-scroll { padding-bottom: 0; }' \
        in html
    assert "position: sticky; bottom: calc(4px + env(safe-area-inset-bottom));" \
        in html
    assert "min-height: var(--kb-full, 0);" in html
    assert "overscroll-behavior-y: contain;" in html
    # 撑高也只医独立模式 iPhone (桌面/安卓的账不这么记)
    assert 'if (!window.matchMedia("(display-mode: standalone)").matches' in ge
    # 体检窗给实测真话 (回传数据: 键盘收起键那条路当场复原, 重启只有三成)
    assert ('"治不了就再进搜索, 点键盘收起键收掉再返回 (重启不保证灵)"'
            in doctor)
    assert 'ViewportHUD.wire({ stat });' in doctor
    assert '"My Music 1.8.16 视口体检' in doctor
    # 走过的死路撤干净: 换新文档 (1.8.12: 归来还是矮的, 坏值跟着 webview
    # 走) + 收键按住 (1.8.13: 记账不读页面实际滚动) + 预抬 (1.8.14: 让位
    # 不看输入框位置, 抬了照滚) —— heal 模块删了, 标识一个不留; 只留
    # 开局报数 (带这趟文档怎么来的, 拆连开谜团)
    for dead in ("reloadDeep", "deepRepair", "deepRepairAt", "kb-repair",
                 "holdDuringDismissal", "ViewportHeal", "focusInner",
                 "keyboardUp", "--kb-h", "60vh"):
        assert dead not in doctor and dead not in ge and dead not in hud, dead
    assert "--kb-h" not in html and "60vh" not in html   # CSS 侧的 --kb-h 也退役
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
