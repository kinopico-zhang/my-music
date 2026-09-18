"""My Music 搜索页接线测试 (1.8.3 重排, 用户点名): 输入框钉页底船坞上方 +
回车收起键盘 + 结果四子页左右滑切换 + 打开 app 回上次停的页 —— 静态文本
断言, 不碰数据库。拆自 test_music_page_wiring.py (文件超 200 行按域再拆)。"""

from tests.music_static_files import MUSIC_STATIC, music_browser_js, music_page_shell


def test_music_183_search_restore_batch():
    """1.8.3 批 (用户点名): 打开 app 自动回上次停的页 (默认主页播放列表,
    退出登录清档); 搜索页重排 —— 输入框钉页底船坞上方 (顶端不再有钉死的
    内容) + 回车收起 iOS 键盘; 结果分 歌曲/艺人/专辑/歌词 四子页左右滑
    切换 (scroll-snap + 页签指示互相同步), 歌曲行带封面; 气泡/圆键
    透明度调实一档 (太透时底下内容忽明忽暗)。"""
    html = music_page_shell()
    js = music_browser_js()
    # 回跳: 导航/收层/手势收层各存一次档, 开局读档 (旧深链优先, 没记过
    # 回主页); localStorage 抛异常 (隐私模式) 存读全兜住
    assert 'const LAST_ROUTE_KEY = "music.lastRoute";' in js
    for frag in ["function routeKey(", "function saveLastRoute(",
                 "function readLastRoute(", "function clearLastRoute("]:
        assert frag in js, f"回跳缺 {frag}"
    assert js.count("saveLastRoute();") == 3       # 导航/收层/手势收层
    assert "// 手势收层也记停在哪页 (开局回跳)" in js
    # 1.8.8 整栈回跳: 档案记整条轨迹 (根领头 + 各层依序), 开局逐层重放;
    # 旧格式单键档案/旧深链当一层处理, 前面垫上主页再走
    assert "function stackKey(item)" in js
    assert 'const journey = [pageState.rootView || "home",' in js
    assert "...pushStack.map(stackKey)].join(\",\");" in js
    assert "journey.forEach(navigate);" in js
    assert 'if (!journey.length || journey[0] !== "home") journey = ["home", ...journey];' in js
    # 层底下永远先铺根 (不变量): 谁在根没渲染时推层, 收层就露出「加载中」
    # 死页 —— 返回逻辑等于失效 (用户点名)
    assert 'if (!pageState.rootView) renderRootView("home");' in js
    assert "clearLastRoute();         // 上次停的页清档" in js   # 退出登录清档
    # 搜索页: 页底一条 (页签 + 输入框), 顶端全给滚动内容
    assert '<div class="search-foot">' in js and 'id="search-tabs"' in js
    assert ".search-shell {" in html           # 页壳抵掉层衬
    assert "interactive-widget=resizes-content" in html   # 安卓键盘自己缩布局
    assert "visualViewport" in js and '"--kb-h"' in js    # iOS 键盘高度 → 抬输入框
    assert "bottom: calc(4px + env(safe-area-inset-bottom) + var(--kb-h, 0));" in html
    # 回车收起 iOS 键盘 (搜索是边打边搜的, 回车没有别的活)
    assert 'if (event.key === "Enter") { event.preventDefault(); input.blur(); }' in js
    # 四子页: 横向 snap 容器 + 各自竖滚的页, 页签指示跟手滑同步
    assert 'data-search-page="tracks"' in js and 'data-search-page="lyrics"' in js
    assert "scroll-snap-type: x mandatory;" in html
    assert "#search-body.paged + .search-foot .search-tabs { display: flex; }" in html
    assert "function bindSearchTabs(target)" in js
    assert 'body.scrollTo({ left: index * body.clientWidth, behavior: "smooth" });' in js
    # 两条横手势分家: 起手在四子页里的横拖归切页, 不归推入层右划返回;
    # 1.8.5 松一格 —— 歌曲页在最左 (scrollLeft 0) 没得再往左滚, 右划归返回;
    # touch-action 是链式约束, .push-pane 放行 pan-x 后容器才滑得动
    assert 'const searchBody = event.target.closest("#search-body.paged");' in js
    assert "if (searchBody && searchBody.scrollLeft > 0) return;" in js
    assert "touch-action: pan-x pan-y;" in html
    # 搜索歌曲行带封面 (与播放列表行同款 trackArtHTML)
    search_render = js[js.index("function renderSearchResults"):]
    assert 'trackRowHTML(track, trackArtHTML(track), "art")' in search_render
    # 透明度调回半透明: 三件套七成底, 动画期等效实底跟着重算 (1.8.5)
    assert "rgba(44,44,46,.7);" in html
    assert "background: rgb(31,31,32);" in html


def test_music_185_search_dock_swap():
    """1.8.5 (用户点名): 搜索层到顶时三件套消失, 搜索框顶上 —— 高度/圆角/
    底色与三件套同款磨砂, 宽度铺满整条船坞行; 歌曲子页 (最左) 右划退出
    搜索层回原页。"""
    html = music_page_shell()
    js = music_browser_js()
    # JS 开关: 开层/收层/手势收层都重排谁站船坞位
    assert "function syncSearchDock()" in js
    assert 'document.body.classList.toggle("search-top"' in js
    assert js.count("syncSearchDock();") == 3   # 开层/收层/手势收层
    # 三件套让位 (扫描进度条不在 .dock-row 里, 照常)
    assert "body.search-top .dock-row > * { visibility: hidden; }" in html
    # 搜索框 = 三件套外轮廓: 船坞行的宽, 船坞件的高/圆角/磨砂底
    assert "height: var(--dock-h);" in html
    assert "border-radius: 23px; padding: 0 14px;" in html
    assert "max-width: 860px;" in html            # 与 .dock-row 同宽
    # 钉在船坞的位置: 随层滑入滑出 (层的 will-change 是 containing block)
    assert "position: fixed; left: 0; right: 0;" in html


def test_music_186_search_batch():
    """1.8.6 批 (用户点名): 各板块数量报真实命中总数 —— 页签/板块头不再
    拿截断长度当命中数 (艺人页 64 张专辑、搜索页只写 20 的口径打架),
    截断时列表尾注明「共 N, 已显示前 M」; 搜索层重进输入框失灵修好 ——
    旧层滑出的 420ms 里 $() 全局查找会绑到旧层元素, 现在查找全圈定在
    本层 target, 收层顺手摘掉层内焦点。"""
    html = music_page_shell()
    js = music_browser_js()
    # 数量口径: 板块头挂 *_total (后端同条件不截断的 COUNT), 尾注如实
    search_render = js[js.index("function renderSearchResults"):]
    for frag in ["歌曲 · ${results.track_total}", "艺人 · ${results.artist_total}",
                 "专辑 · ${results.album_total}", "歌词 · ${results.lyric_total}"]:
        assert frag in search_render, f"板块头缺真实总数: {frag}"
    assert "共 ${total} ${unit}, 已显示前 ${shown} ${unit}" in search_render
    assert ".list-note {" in html                       # 尾注样式
    # 页签计数也挂总数 (四页签依序对应四个 *_total)
    assert "const counts = [results.track_total, results.artist_total," in search_render
    # 输入框失灵: 查找圈定本层 (renderSearchView/bindSearchTabs 吃 target,
    # 输入框/结果体从 target 取), 结果晚到时层已收走就丢弃
    assert "function renderSearchView(target)" in js
    assert 'const input = target.querySelector("#search-input");' in js
    assert "if (controller.signal.aborted || !body.isConnected) return;" in js
    # 收层摘焦点: 收层循环/手势收层/右划起手三处都 blur 层内焦点 (键盘/
    # 视口状态不再被将删的输入框搅乱; 起手那处是 1.8.9 加的, 见 189 测试)
    assert js.count("contains(document.activeElement)) document.activeElement.blur();") == 3
    # 搜索圆键聚焦收窄到栈顶层: 旧层那枚不许碰
    assert 'const input = top && top.pane.querySelector("#search-input");' in js


def test_music_187_keyboard_scroll_repair():
    """1.8.7 修「搜索页开关几回, 回主页底部一块黑、页面没充满屏」(用户
    追了两个版本, 重启 app 都不消): iOS 键盘收走后赖账有两味 —— ① 键盘
    避让把文档滚了 (overflow:hidden 拦不住, window.scrollY 赖非零而视口
    偏移是 0; 1.8.5 只查偏移, 漏的正是这味); ② 视口停在偏移上 (1.8.5
    修过)。收尾还经常一声事件不响, 脏滚位会被 iOS 会话恢复原样带回重启
    后。对策全在全局事件层: 复位条件补查文档滚位; 焦点一走迟两拍补跑;
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
    """1.8.9 修「键盘没收起就右划关搜索, 底部一条黑带」的真病根 (用户
    录屏逐帧量出来的): 键盘收起动画走到半路时移除聚焦过的层, iOS 把
    布局视口整个冻在没收满的矮个上 —— 顶部纹丝不动 (不是 1.8.5/1.8.7
    修的偏移/滚位那两味, scrollTo 够不着), fixed 船坞和 100dvh 一起
    垫高, 屏底露出纯黑。三层对策: ① 右划起手 (横向坐实) 就摘焦点,
    键盘从拖动第一下就开始收 (同原生返回手势); ② 收层移除 DOM 不再
    赌 420ms 够用 —— 等视口高度回到 innerHeight 附近 (键盘彻底收走)
    才动手, 键盘赖着最多再等 1.2s; ③ 真被冻矮了应用自己修: 记着见过
    的满高 (存档跨重启, 转屏按新方向重立), 没键盘却矮一截就拿常驻的
    隐形输入框走一趟 focus→blur 逼视口重算 (定时器没手势未必唤得动
    iOS 键盘, 再埋一手借用户下次触屏补一趟; 一回赖账最多修三次)。"""
    html = music_page_shell()
    js = music_browser_js()
    ge = (MUSIC_STATIC / "js" / "music-global-events.js").read_text(
        encoding="utf-8")
    panes = (MUSIC_STATIC / "js" / "music-push-panes.js").read_text(
        encoding="utf-8")
    swipe = (MUSIC_STATIC / "js" / "music-pane-swipe.js").read_text(
        encoding="utf-8")
    # ① 起手摘焦点 + ② 收稳才移除: 两处收层共用同一个等待函数
    assert "function removePaneWhenSettled(pane)" in panes
    assert "removePaneWhenSettled(item.pane);" in panes    # closePushStack
    assert "removePaneWhenSettled(pane);" in swipe         # 手势收层
    assert "vv.height >= window.innerHeight - 12" in panes  # 键盘收走判据
    assert "Date.now() - start > 1200" in panes            # 键盘赖着: 最多再等 1.2s
    # ③ 视口冻矮的察觉与自修 (全局事件层): 满高基准 (开局读档 + 长高刷新 +
    # 转屏重立) / 探针走一趟 focus→blur / 手势补一趟 / 三次封顶
    assert '"music.fullInner"' in ge                       # 满高存档 (跨重启)
    assert 'matchMedia("(orientation: landscape)").matches' in ge
    assert "setTimeout(() => probe.blur(), 150);" in ge    # 键盘往返一趟
    assert "if (fullInner - window.innerHeight > 12) repairViewport();" in ge
    assert '"pointerdown", () => {' in ge                  # 借下次触屏补一趟
    assert "{ once: true });" in ge
    assert "repairs >= 3" in ge                            # 别闪个没完
    # 触发条件: 没键盘 (视口回到 innerHeight 附近) + iOS 独有 (安卓布局
    # 自己缩, innerHeight 天生会动, 不修)
    assert "visualViewport.height >= window.innerHeight - 12" in ge
    assert "/iP(hone|ad|od)/.test(navigator.userAgent)" in ge
    # 探针本体: JS 建的常驻隐形输入框 (markup 不占行, 样式在 base.css)
    assert 'probe.id = "kb-repair";' in ge
    assert "document.body.appendChild(probe);" in ge
    assert "#kb-repair {" in html                          # 隐形样式 (1px 全透明)
    assert "opacity: 0; pointer-events: none;" in html
