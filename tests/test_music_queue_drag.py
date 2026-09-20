"""My Music 队列拖拽换序接线测试 (1.8.20 起; 1.8.31 改整行拖, 用户点名
「不需要显示三个横杠, 直接拖整个条」): 静态文本断言, 不碰数据库。
拆自 test_music_wiring_player.py (文件超 200 行按域再拆); 左滑删行
断言在 test_music_swipe_delete。"""

from tests.music_static_files import (MUSIC_STATIC, music_page_shell,
                                      music_player_js)


def test_music_queue_drag_wiring():
    """队列内拖拽换序 (用户点名"列表里的歌单可以被拖拽更换顺序"): 位置数学
    在 player-queue.js 的 queueReorder (node 直测), 这里只验接线 —— 行上
    按住 ~200ms 进预备 (armed, 行板微亮), 再动就是拖: 行跟手位移让位,
    松手按落点改 order 并存档; 预备期滑走交还原生 (竖滑滚列表), 横向让给
    左滑删除; armed 起 touchmove 全掐 (防原生滚动半路接管), 按住过的尾随
    click 吞掉 (不跳播)。换过的顺序和随机/循环开关存进 localStorage,
    恢复前先验 order 是完整排列 (缺/重/越界的旧档弃用, 随机旗只在顺序
    真恢复时才点亮)。
    1.8.27 行套 .swipe-wrap (左滑删除同构): 拖拽单位上移到 wrap 一级,
    落点位只认拖动距离。"""
    html = music_page_shell()
    player = music_player_js()
    common = (MUSIC_STATIC / "js" / "music-common.js").read_text(encoding="utf-8")
    queue = (MUSIC_STATIC / "js" / "player-queue.js").read_text(encoding="utf-8")
    # 拖动中的行浮起来 (阴影 + 免过渡) —— 1.8.27 被拖的是 wrap, 过渡也在 wrap;
    # 1.8.31 预备亮 (drag-armed) 比拖拽中弱一档, 提示「可以拖了」
    assert "#queue-list .swipe-wrap.dragging {" in html
    assert "#queue-list .swipe-wrap.drag-armed {" in html
    assert "#queue-list .swipe-wrap { transition: transform .18s ease; }" in html
    # 1.8.31 把手图标退役 (整行拖), 队列行板改透明跟播放页一张底
    assert "ICON_GRIP" not in common and "q-grip" not in player
    assert "--bg: transparent;" in html
    assert "#queue-list .swipe-wrap::after {" in html   # 左滑纱换近黑渐隐
    assert "module.exports = {" in queue and "queueReorder," in queue
    for frag in ["function bindQueueDrag", "function finishQueueDrag",
                 "queueReorder(playQueue, base + drag.fromView, base + drag.target)",
                 "const QUEUE_ARM_MS = 200;",
                 'queueDragSwallowClick = true',
                 'wrap.classList.add("drag-armed")',
                 "try { row.setPointerCapture(event.pointerId); }",
                 "Math.abs(dx) > Math.abs(dy)",
                 "drag.fromView + Math.round(dy / drag.rowH)"]:
        assert frag in player, f"music-player.js 缺 {frag}"
    # armed 起 touchmove 全掐 (非被动): 原生滚动半路接管 = pointercancel
    assert 'if ((arm && arm.armed) || (queueDrag && queueDrag.moved)) {' in player
    assert '{ passive: false });' in player
    assert "bindQueueDrag();" in player                 # 挂进事件绑定
    # 存档: order (截 500) + position 一起进 player state
    assert "order: playQueue.order.slice(0, 500)," in player
    assert "saved.order" in player and "orderRestored" in player
    assert "new Set(saved.order).size === saved.tracks.length" in player  # 排列校验
