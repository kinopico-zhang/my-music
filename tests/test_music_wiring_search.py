"""My Music 搜索页接线测试 (1.8.3 重排 + 1.8.17 上顶): 输入框钉搜索页最顶
(键盘盖不住) + 回车落定查询词升作页标题 + 结果四子页左右滑切换 + 打开 app
回上次停的页 —— 静态文本断言, 不碰数据库。拆自 test_music_page_wiring.py
(文件超 200 行按域再拆)。"""

from tests.music_static_files import music_browser_js, music_page_shell


def test_music_183_search_restore_batch():
    """1.8.3 批 (用户点名): 打开 app 自动回上次停的页 (默认主页播放列表,
    退出登录清档); 搜索页重排 + 1.8.17 换思路 (用户点名「键盘弹出时搜索
    框在屏幕最上方」): 页顶一条 sticky —— 编辑态放搜索框, 落定后放查询词
    标题, 页签垫在下面; 结果分 歌曲/艺人/专辑/歌词 四子页左右滑切换
    (scroll-snap + 页签指示互相同步), 歌曲行带封面; 气泡/圆键透明度
    调实一档 (太透时底下内容忽明忽暗)。"""
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
    # 搜索页: 页顶一条 (搜索框/查询词标题 + 页签), 页壳照旧是滚动器
    # (1.8.15 结构 + 1.8.16 文档解锁留着, 黑带别再回来)
    assert '<div class="search-head">' in js and 'id="search-tabs"' in js
    assert ".search-shell {" in html           # 页壳抵掉层衬
    assert "interactive-widget=resizes-content" in html   # 安卓键盘自己缩布局
    assert "visualViewport" in js and '"--kb-full"' in js    # iOS 键盘让位 → 撑高页壳内滚
    # 回车落定 (1.8.17 用户点名): 撤防抖立刻搜 + 收键盘, 查询词升作页标题
    assert 'if (event.key !== "Enter") return;' in js
    assert "clearTimeout(debounceTimer);" in js
    assert "runSearch(target);\n    input.blur();" in js
    # 四子页: 横向 snap 容器 + 各自竖滚的页, 页签指示跟手滑同步
    assert 'data-search-page="tracks"' in js and 'data-search-page="lyrics"' in js
    assert "scroll-snap-type: x mandatory;" in html
    assert ".search-shell.paged .search-tabs { display: flex; }" in html
    assert "function bindSearchTabs(target)" in js
    assert 'body.scrollTo({ left: index * body.clientWidth, behavior: "smooth" });' in js
    # 两条横手势分家: 起手在四子页里的横拖归切页, 不归推入层右划返回;
    # 1.8.5 松一格 —— 歌曲页在最左 (scrollLeft 0) 没得再往左滚, 右划归返回;
    # 1.8.17 设置页也拆四滑页, 同一条守卫认两家的分页容器;
    # touch-action 是链式约束, .push-pane 放行 pan-x 后容器才滑得动
    assert 'const pager = event.target.closest("#search-body.paged, #settings-body");' in js
    assert "if (pager && pager.scrollLeft > 0) return;" in js
    assert "touch-action: pan-x pan-y;" in html
    # 1.8.18 最左页右划退出整层 (用户点名「跟其他界面右划退出一样」):
    # 原生平移把横拖整个抢走 (pointercancel), 右划返回死在半路 —— 触摸
    # 看门在最左页右向坐实 (6px, 抢在浏览器自家 slop 之前) 的那一下
    # preventDefault 掐掉原生平移, 手势让回右划返回; 左向切页/竖向滚页/
    # 不在最左页照旧全交原生
    assert 'pane.addEventListener("touchstart"' in js
    assert "guardRight = dx > 0 && Math.abs(dx) > Math.abs(dy);" in js
    assert "if (guardRight) event.preventDefault();" in js
    # 搜索歌曲行带封面 (与播放列表行同款 trackArtHTML)
    search_render = js[js.index("function renderSearchResults"):]
    assert 'trackRowHTML(track, trackArtHTML(track), "art")' in search_render
    # 透明度调回半透明: 三件套七成底, 动画期等效实底跟着重算 (1.8.5)
    assert "rgba(44,44,46,.7);" in html
    assert "background: rgb(31,31,32);" in html


def test_music_185_search_top_pin():
    """1.8.5 曾让搜索层到顶时三件套让位给页底搜索框; 1.8.17 换思路 (用户
    点名「键盘弹出时搜索输入框在屏幕最上方, 不要进入模糊区域; 点击搜索
    或回车, 搜索内容变成页面标题」): 搜索框上移钉到页顶 (系统磨砂带
    底下, 键盘再高也盖不住顶端), 回车落定后查询词升作页标题
    「搜索：xxx」, 点标题回来改; 船坞位空出来, 三件套常驻 —— 让位开关
    (syncSearchDock/body.search-top) 整组撤掉, 回归守卫不许回来。"""
    html = music_page_shell()
    js = music_browser_js()
    # 让位开关撤净: JS 开关函数没了, CSS 让位规则没了
    assert "syncSearchDock" not in js
    assert "body.search-top .dock-row" not in html
    # 搜索框形制照旧 (三件套同款磨砂外轮廓), 只是住进了页顶的 .search-head
    assert "height: var(--dock-h);" in html
    assert "border-radius: 23px; padding: 0 14px;" in html
    assert "max-width: 860px;" in html            # 与 .dock-row 同宽
    # 页顶钉位: sticky 钉页壳顶 (= 屏幕顶), 自家 padding 顶开系统磨砂带
    # (输入框不进模糊区域); 结果的尾衬铺到三件套上头
    assert ".search-head {" in html
    assert "position: sticky; top: 0;" in html
    assert "padding: calc(env(safe-area-inset-top) + 14px) 16px 0;" in html
    assert "padding: 8px 16px calc(var(--dock-clear) + 12px);" in html
    # 编辑/落定两态 (JS 按焦点切 .editing): 焦点在框里 = 编辑 (框钉页首);
    # 失焦 = 落定 (查询词升作页标题); 点标题回来改 —— 原词全选直接打字即替换
    assert 'shell.classList.add("editing")' in js
    assert 'shell.classList.remove("editing")' in js
    assert ".search-shell:not(.editing) .search-box { display: none; }" in html
    assert ".search-shell.editing .search-title { display: none; }" in html
    assert '`搜索：${pageState.searchQuery}`' in js
    assert "input.focus(); input.select();" in js
    # 让位滚过页壳的话落定时归位, 标题底下别压着结果
    assert "shell.scrollTo(0, 0);" in js
    # 1.8.18 修「点放大镜进来没有输入框」(用户报): 框默认藏着
    # (:not(.editing) display:none), 藏着的框恰恰聚不上焦 —— 焦点进不去,
    # .editing 就永远等不来。空查询开局先亮框; 点标题回来改 / 船坞键
    # 聚焦前也都先亮框再 focus
    assert 'if (!pageState.searchQuery) shell.classList.add("editing");' in js
    assert "shell.classList.add(\"editing\");   // 框先亮出来才聚焦得上" in js
    assert 'input.closest(".search-shell").classList.add("editing");' in js


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
