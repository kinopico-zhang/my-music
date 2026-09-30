"""My Music 播放列表改名 + 曲序重排测试 (1.8.17 用户点名「允许编辑播放
列表的标题, 允许调整列表歌曲的顺序」): 查询层校验 + 页面接线静态断言。
拆自 test_music_playlists.py (文件超 200 行按域再拆)。"""

import time

import pytest

from app.music.library_database import session_factory
from app.music import library_playlists, library_queries
from tests.music_static_files import MUSIC_STATIC, music_page_shell
from tests.music_library_helpers import _seed_library


def test_playlist_rename_reorder_query(tmp_path):
    """查询层: 改名 (收边/撞别人的名/空名报错, 撞自己不算) + 整表重排
    (全量曲目 id 的新顺序重写 position, 缺/重/混外人报错); 每次编辑都
    记 updated_at —— 选择单按它排, 最近动过的在最前。"""
    _seed_library()
    with session_factory()() as session:
        first = library_playlists.create_playlist(session, "第一")
        other = library_playlists.create_playlist(session, "第二")
        assert first.updated_at > 0 and other.updated_at > 0
        time.sleep(0.01)              # updated_at 是 epoch 秒, 隔开两笔编辑
        renamed = library_playlists.rename_playlist(
            session, first.playlist_id, " 改名 ")
        assert renamed.name == "改名"                  # 名字收边
        assert renamed.updated_at > first.updated_at   # 改名也算一次编辑
        with pytest.raises(ValueError):    # 撞别人的名 (撞自己那次成功了)
            library_playlists.rename_playlist(session, other.playlist_id, "改名")
        with pytest.raises(ValueError):    # 空名
            library_playlists.rename_playlist(session, first.playlist_id, "  ")
        with pytest.raises(KeyError):      # 列表不在库
            library_playlists.rename_playlist(session, 99999, "没有")
        # 拖拽落定: 全量 id 新顺序 → position 1..N 重写; [5,1,3] 无题曲领队
        for track_id in (1, 3, 5):
            library_playlists.add_track_to_playlist(session, first.playlist_id,
                                                    track_id)
        time.sleep(0.01)
        reordered = library_playlists.reorder_playlist_tracks(
            session, first.playlist_id, [5, 1, 3])
        page = library_queries.playlist_page(session, first.playlist_id)
        assert page is not None
        assert [t.title for t in page.tracks] == ["无题曲", "曲A", "Hello"]
        assert reordered.updated_at > renamed.updated_at
        # 顺序对不上就 409 (客户端列表过期): 缺一首 / 重复 / 混进非成员
        for bad_ids in ([5, 1], [1, 1, 3], [1, 3, 5, 4]):
            with pytest.raises(ValueError, match="列表内容对不上"):
                library_playlists.reorder_playlist_tracks(
                    session, first.playlist_id, bad_ids)
        with pytest.raises(KeyError):
            library_playlists.reorder_playlist_tracks(session, 99999, [])
        # 重排顺手把 position 的洞补平: 抽掉中间一首, 顺序连号不受影响
        library_playlists.remove_track_from_playlist(session, first.playlist_id, 1)
        page = library_queries.playlist_page(session, first.playlist_id)
        assert page is not None
        assert [t.title for t in page.tracks] == ["无题曲", "Hello"]


def test_music_playlist_rename_reorder_wiring():
    """接线: 列表名点按 prompt 改名 (PATCH); 1.8.31 起曲目行整行按住一小会儿
    上下拖换序 (队列拖拽同款: 预备/让位平移/尾随 click 吞掉, 把手退役),
    松手 PUT 全量顺序, 没存上整页重拉对齐服务端; 1.8.108 键鼠端鼠标按下
    即拖 (不用按住等预备)。"""
    html = music_page_shell()
    view_js = (MUSIC_STATIC / "js" / "music-playlist-view.js").read_text(
        encoding="utf-8")
    drag_js = (MUSIC_STATIC / "js" / "music-playlist-drag.js").read_text(
        encoding="utf-8")
    # 改名: 标题本身就是按钮 (✎ 角标暗示), prompt 落定, 取消不算失败
    assert '<h2 class="pl-name"' in view_js
    assert 'window.prompt("新的列表名"' in view_js
    assert 'method: "PATCH",' in view_js
    assert ".pl-name::after" in html and 'content: "✎"' in html
    # 1.8.123 修「改名后收层回去列表页还是旧名」(用户实报): 底下的层收层
    # 回去不重铺 (1.8.80/1.8.99 同款坑) —— 改名当场把列表页行/主页卡的名字
    # 就地换新 (refreshPlaylistName, 换封面 1.8.99 同款套路)
    rendering_js = (MUSIC_STATIC / "js" / "music-list-rendering.js").read_text(
        encoding="utf-8")
    assert "function refreshPlaylistName" in rendering_js
    assert '.playlist-row[data-playlist-id="${playlist.playlist_id}"] .a-main b' \
           in rendering_js
    assert '.playlist-card[data-playlist-id="${playlist.playlist_id}"] > b' \
           in rendering_js
    assert "refreshPlaylistName(updated);" in view_js
    # 拖拽 (1.8.31 整行拖, 用户点名「不需要显示三个横杠, 默认都是直接
    # 拖动调整顺序, 长按是右键菜单」): 行上按住 ~200ms 进预备再拖 (预备期
    # 滑走交还滚动/左滑删除, 长按菜单开了也撤), 松手按落点落定
    assert 'class="pl-grip"' not in view_js and "ICON_GRIP" not in view_js
    assert "function bindPlaylistDrag" in drag_js
    assert "const PLAYLIST_ARM_MS = 200;" in drag_js
    assert "try { arm.row.setPointerCapture(pointerId); }" in drag_js
    assert "playlistDragSwallowClick" in drag_js   # 拖动过/落定过的尾随 click 吞掉 (不开播)
    # 1.8.126 修「列表里点不动」(用户实报 Yashima 行): 触摸按住 200–500ms 的
    # 慢点按不再被拖拽预备吞掉 —— 预备 (held) 只亮行板, 吞点旗只在真拖动
    # (位移>8px) 和落定换序两处置真, 按住没动抬手照旧开播 (与键鼠端同规矩;
    # 老代码预备时就置旗, 点得慢一点整列表像死了一样 —— 触摸端专属)
    assert 'if (held) {\n      arm.wrap.classList.add("drag-armed");\n    }' \
        in drag_js
    assert drag_js.count("playlistDragSwallowClick = true") == 2
    assert "按住过的抬手不算点击" not in drag_js
    assert 'js/music-playlist-drag.js?v=7"' in html   # 1.8.126 慢点按改版
    assert 'bindPlaylistDrag(target.querySelector("#playlist-tracks")' in view_js
    # 1.8.108 鼠标拖拽 (用户点名「播放列表要支持鼠标拖拽调整顺序」): 键鼠
    # 端按下即起拖 (没动过不吞 click, 点了照旧开播), 触摸端照旧等 200ms;
    # 行首封面 <img> 的原生拖拽会抢走指针流 —— 预备/拖拽中掐 dragstart;
    # 右键 (菜单)/中键 (自动滚动) 不是拖拽意图
    assert 'if (event.pointerType === "mouse" && isKeyMouseInput()) {' \
        in drag_js
    assert "armDrag(event.pointerId, false);" in drag_js
    assert "if (arm && arm.armed) event.preventDefault();" in drag_js
    assert "if (event.pointerType === \"mouse\" && event.button !== 0) return;" \
        in drag_js
    # 动够 8px 才算拖拽意图 (横向仍交还左滑删除), 那一下起尾随 click 吞掉
    assert "if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;\n" \
           "      playlistDragSwallowClick = true;" in drag_js
    desktop_css = (MUSIC_STATIC / "css" / "music-desktop.css").read_text(
        encoding="utf-8")
    assert "html[data-input=\"keymouse\"] #playlist-tracks .track-row " \
        "{ cursor: grab; }" in desktop_css
    # 持久化: 就地先挪 DOM, 再 PUT 全量新顺序; 失败整页重拉
    assert '`/music/api/playlists/${playlistId}/order`' in view_js
    assert 'method: "PUT"' in view_js
    assert "renderPlaylistView(playlistId);" in view_js
    # 1.8.18 修让位 (用户报「拖到哪其他歌该让个位置, 现在没有」): 目标位只认
    # 拖动距离 —— offsetTop 相对整个 offsetParent (头图/操作排的全高混进
    # 来), 一起手目标位就整体偏飞; 让位平移的过渡在 wrap 上 (左滑那套
    # 过渡在行 button 上, wrap 自己没有就是瞬跳)
    assert "drag.from + Math.round(dy / drag.rowH)" in drag_js
    assert "offsetTop" not in drag_js
    assert "#playlist-tracks .swipe-wrap { transition: transform .18s ease; }" \
        in html
    # 1.8.19 修「被拖行被黑色空位遮挡住」(用户报): wrap overflow:hidden
    # (左滑删除的裁切), 行在 wrap 里竖移出界被自家裁掉, z-index 挂在行上
    # 也翻不出裁切 —— 位移/抬层/影子全落 wrap 一级, 行只管提亮
    assert 'wrap.classList.add("dragging");' in drag_js
    assert "drag.row.style.transform" not in drag_js
    assert "#playlist-tracks .swipe-wrap.dragging {" in html
    assert "transition: none; z-index: 3; box-shadow: 0 8px 22px rgba(0,0,0,.5);" \
        in html
    # 1.8.23 改款 (用户报「左滑时左边的信息不见了」): 行不动了 —— 原先
    # 行整体左移、封面从左缘被裁掉; 现在删除钮从右缘滑上来 (z3 压过行),
    # 钮左侧延伸半透纱 (wrap::after, 浓度 --veil 跟手), 行尾内容只是
    # 罩暗不藏 —— 1.8.18 的行尾整藏 (visibility:hidden) 随之退役。
    # 1.8.25 纱换色 (用户点名「遮罩不是红色的, 跟 item 一样」): 行背景色
    # 渐隐替掉红纱, 红只剩删除钮自己
    swipe_css = (MUSIC_STATIC / "css" / "music-swipe-delete.css").read_text(
        encoding="utf-8")
    assert ".swipe-wrap > button:first-child {" in swipe_css
    assert "transition: transform .25s" not in swipe_css[
        swipe_css.index(".swipe-wrap > button:first-child {"):
        swipe_css.index(".swipe-del {")]           # 行不再带过渡 (行不动了)
    assert "transform: translateX(100%);" in swipe_css   # 钮原位藏在右缘外
    assert "z-index: 3;" in swipe_css              # 钮压在行上 (不再垫底)
    assert "opacity: var(--veil, 0);" in swipe_css  # 纱的浓度跟手
    # 纱与行同色 (var(--bg) 掺半透明做渐隐), 红纱退役
    assert "color-mix(in srgb, var(--bg) 50%, transparent)" in swipe_css
    assert "rgba(229, 72, 77" not in swipe_css
    # 1.8.27 方向转回 (用户报「你搞反了」): 近钮一头最浓 (50%)、往左渐至
    # 几乎透明 —— 1.8.26 掉头掉错方向 (近钮全透) 退役
    assert "color-mix(in srgb, var(--bg) 50%, transparent), transparent" \
        in swipe_css
    assert "transparent, color-mix(in srgb, var(--bg) 50%, transparent))" \
        not in swipe_css
    # 1.8.27 修点击死区 (用户报「点行进不去」): 纱是装饰, 伪元素命中算到
    # wrap 头上 —— closest 找行落空, 纱底 84px 成死区; 点击全放行
    assert "pointer-events: none;" in swipe_css[
        swipe_css.index(".swipe-wrap::after {"):
        swipe_css.index(".swipe-wrap::after {") + 400]
    assert "visibility: hidden;" not in swipe_css   # 行尾整藏退役
    assert "wrap.classList.toggle(\"revealed\"" in (
        MUSIC_STATIC / "js" / "music-swipe-delete.js").read_text(encoding="utf-8")
    # 1.8.31 把手退役 (整行拖, 用户点名): 预备亮顶上, 右缘让位的衬法撤了
    assert ".pl-grip" not in html
    assert "#playlist-tracks .swipe-wrap.drag-armed > button {" in html
