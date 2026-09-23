"""My Music 左滑删除接线测试: iOS 同款红色删除钮 —— 静态文本断言,
不碰数据库。拆自 test_music_wiring_library.py (1.8.23 改款批次它长到
超 200 行上限, 按域再分家); 改款后的样式断言在
test_music_playlist_rename_reorder, 已下载页多选删除 (含选择态压住
左滑) 在本文件 test_music_downloads_select_wiring (1.8.59 挪来)。"""

from tests.music_static_files import (MUSIC_STATIC, music_browser_js,
                                      music_page_shell, music_player_js)


def test_music_swipe_delete_wiring():
    """左滑删除 (用户点名两处: 列表内曲目移出 + 主页列表整列删): iOS 同款
    红色删除钮。与长按菜单共存 (阈值分家), 滚动让位 (touch-action pan-y +
    捕获 scroll 即收), 尾随 click 吞掉, 同一时间只开一行。1.8.23 改款起
    行原地不动 —— 删除钮自己从右缘滑上来 (样式在 music-swipe-delete.css,
    根层橡皮筋也让开开着的行, 见 test_music_wiring_chrome)。"""
    html = music_page_shell()
    js = music_browser_js()
    for frag in [".swipe-wrap {", ".swipe-del {", "touch-action: pan-y;"]:
        assert frag in html, f"左滑样式缺 {frag}"
    assert "#e5484d" in html                          # 删除钮红底
    for frag in ["const SWIPE_REVEAL = 72;",
                 "function closeSwipeRow", "function bindSwipeDelete",
                 'document.addEventListener("scroll", closeSwipeRow, true)',
                 'data-swipe-track=', 'data-swipe-playlist=',
                 "swipeSuppressClick",
                 '`/music/api/playlists/${playlistId}/tracks/${trackId}`']:
        assert frag in js, f"music.js 缺 {frag}"
    # 两处挂载: 列表详情的曲目行 + 播放列表页的列表行 (1.8.28 主页段改
    # 网格卡, 主页那处撤了 —— 卡片不滑, 删整列走播放列表页)
    assert 'bindSwipeDelete(target.querySelector("#playlist-tracks")' in js
    assert "bindSwipeDelete(list, async (wrap) => {" in js
    # 1.8.27 队列也挂上 (用户点名「所有列表的删除按钮都这样」—— 队列是
    # 最后一个没壳的列表): 队列视图住全屏播放页, 挂载在播放器模块。
    # 1.8.29 修加载序 (真机「播放不了」那单): bindSwipeDelete 住在浏览模块
    # (music.html 里排在播放器组后面), bindPlayerEvents 开局跑它必
    # ReferenceError —— 同函数里排在后面的接线 (整组 audio 事件) 和 boot
    # 里紧跟的 playerRestore 全被掐死。改成队列视图第一次打开才绑。
    player = music_player_js()
    events = (MUSIC_STATIC / "js" / "music-player-events.js").read_text(
        encoding="utf-8")
    assert 'bindSwipeDelete($("#queue-list")' in player
    assert "function bindQueueSwipeDelete" in player
    assert "queueSwipeBound" in player           # 开视图只绑一次
    assert "bindQueueSwipeDelete" not in events  # 开局不再碰它 (1.8.29)
    # 删的是壳记的 order 绝对位 (视图下标 0 = order[position]); 当前曲
    # 删不得 (queueRemove 拒, 提示一句); 1.8.31 把手退役 (整行拖) ——
    # 开着的行不再是「把手藏掉」, 整行归删除钮; 旧 .queue-row.dragging
    # 那套也撤了 (拖拽单位上移到 wrap), 预备亮 (.drag-armed) 顶上
    queue = (MUSIC_STATIC / "js" / "player-queue.js").read_text(encoding="utf-8")
    assert "function queueRemove" in queue \
        and "queueUpcoming, queueReorder, queueRemove };" in queue
    assert "queueRemove(playQueue, Number(wrap.dataset.queuePos))" in player
    assert 'aria-label="从队列移除"' in player
    assert ".queue-row.dragging" not in html \
        and ".q-grip" not in html
    assert "#queue-list .swipe-wrap.drag-armed {" in html
    # 手势地盘分家 (1.7.0 后遗症修): 左滑只认左移 (右移归推入层返回手势,
    # 抢了会被 pointercancel 掐弹回); 左缘 24px 让给 iOS 系统边缘返回
    assert "swipeDrag.horizontal = dx < 0 && Math.abs(dx) > Math.abs(dy);" in js
    # 左缘返回的归属 (用户点名两轮 preventDefault 拦截, iPhone Safari 实测
    # 都掐不住系统手势, 终版撤净): 苹果把屏幕最边一条握在系统手里, 网页
    # 收不到那片触摸 (Navigation API 的 traverse 取消也未实现) —— 应用
    # 自己的右滑从页面任意位置起手; 别再往 document 挂 touchstart 拦截,
    # 那只剩左缘一小条不能起手滚动的副作用
    assert "standaloneLaunch" not in js
    assert "EDGE_STRIP_PX" not in js
    assert 'document.addEventListener("touchstart"' not in js
    assert 'document.addEventListener("touchend"' not in js
    # 拖动跟手 (1.8.23 改行不动款): wrap 上挂 .swiping 撤掉删除钮/纱的
    # 过渡, 松手回位/定住才交给过渡 (不撤的话每帧都在重定 250ms 补间,
    # 手指拖着钮像皮筋 —— 队列拖拽同款)
    assert 'swipeDrag.wrap.classList.add("swiping")' in js
    assert ".swipe-wrap.swiping .swipe-del," in html
    assert ".swipe-wrap.swiping::after { transition: none; }" in html
    # 删除钮的点击走捕获层 (}, true); 行自己的冒泡 click 处理器看不到它
    assert 'container.addEventListener("click", async (event) => {' in js
    assert "}, true);" in js


def test_music_downloads_select_wiring():
    """已下载页的多选删除 (1.8.59 从 test_music_page_wiring 挪来 —— 那文件
    顶到 200 行上限): 1.8.6 「多选」选择模式 (capture 截下点行改勾选);
    1.8.17 选择态压住左滑 (两套手势不打架); 1.8.18 封面即复选框 +
    垃圾桶/多选并成右上一对椭圆键。"""
    html = music_page_shell()
    js = music_browser_js()
    # 1.8.6 多选删除 (用户点名): 「多选」进选择模式, capture 阶段截下点行
    # 改勾选 (不再开播), 删完/「完成」退出; 状态住模块, 整页重铺后
    # syncDownloadsSelect 按 state 补勾
    assert "music-downloads-select.css?v=" in html        # 选择态样式
    select_js = (MUSIC_STATIC / "js" / "music-downloads-select.js").read_text(
        encoding="utf-8")
    for frag in ["function bindDownloadsSelect", "function syncDownloadsSelect",
                 "function deleteSelected", "const dlSelected = new Set();",
                 "event.stopPropagation();",          # capture 截下: 不走开播
                 "删除选中的 ${dlSelected.size} 首?",
                 "await downloads.removeDownload(trackId);"]:
        assert frag in select_js, f"多选删除缺 {frag}"
    assert "bindDownloadsSelect(target);" in js          # 挂 pane 层 (重铺不丢)
    assert 'id="dl-select-toggle"' in js and 'id="dl-select-delete"' in js
    # 1.8.18 改版 (用户点名「封面即复选框」): 不再左移出行画选择圈 —— 勾
    # 画在封面上 (蒙暗 + 白勾, .dl-art 裹层挂伪元素), 行布局一毫米不动
    assert '#dl-pane-body.selecting .dl-row.sel .dl-art::after' in html
    assert "#dl-pane-body.selecting .dl-row.sel .dl-art::before" in html
    assert '<span class="dl-art">' in js                 # 封面裹层 (模板带出)
    assert "padding-left: 32px" not in html              # 左移出行那套撤了
    # 1.8.17: 勾中出垃圾桶; 多选模式压住左滑 (删除钮和延伸纱一起藏),
    # 两套手势不打架
    assert 'aria-label="删除选中"' in js
    assert "#dl-pane-body.selecting .swipe-del { display: none; }" in html \
        and "#dl-pane-body.selecting .swipe-wrap::after { display: none; }" in html
    # 1.8.18 垃圾桶/多选并成右上一对黑白灰椭圆键 (原先 space-between
    # 隔在两头, 用户点名「距离太远了」)
    assert '<span class="dl-actions">' in js
    assert ".dl-actions { display: flex; align-items: center; gap: 8px;" in html
    assert "border-radius: 999px;" in html and "min-height: 32px;" in html
