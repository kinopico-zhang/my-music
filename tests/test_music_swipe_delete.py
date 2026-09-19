"""My Music 左滑删除接线测试: iOS 同款红色删除钮 —— 静态文本断言,
不碰数据库。拆自 test_music_wiring_library.py (1.8.23 改款批次它长到
超 200 行上限, 按域再分家); 改款后的样式断言在
test_music_playlist_rename_reorder, 下载页选择态压住左滑在
test_music_page_wiring。"""

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
    # 删不得 (queueRemove 拒, 提示一句); 开着的行把手藏掉 (删除钮盖着,
    # 抓不得); 旧 .queue-row.dragging 那套撤了 (拖拽单位上移到 wrap)
    queue = (MUSIC_STATIC / "js" / "player-queue.js").read_text(encoding="utf-8")
    assert "function queueRemove" in queue \
        and "queueUpcoming, queueReorder, queueRemove };" in queue
    assert "queueRemove(playQueue, Number(wrap.dataset.queuePos))" in player
    assert 'aria-label="从队列移除"' in player
    assert ".queue-row.dragging" not in html \
        and "#queue-list .swipe-wrap.revealed .q-grip" in html
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
