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
    """接线: 列表名点按 prompt 改名 (PATCH); 曲目行右缘把手上下拖换序
    (队列拖拽同款: 指针捕获/让位平移/尾随 click 吞掉), 松手 PUT 全量
    顺序, 没存上整页重拉对齐服务端。"""
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
    # 拖拽: 只认把手起手 (行照常点播/滚动), 松手按落点落定
    assert 'class="pl-grip"' in view_js
    assert "function bindPlaylistDrag" in drag_js
    assert 'grip.setPointerCapture(event.pointerId);' in drag_js
    assert "playlistDragSwallowClick" in drag_js   # 落定尾随 click 吞掉 (不开播)
    assert 'bindPlaylistDrag(target.querySelector("#playlist-tracks")' in view_js
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
    # 左滑露出删除钮时行尾内容全藏 (1.8.18 用户点名: 时长/下载标/词标/
    # 箭头让开, 只留歌名)
    assert ".swipe-wrap > button.revealed > :not(.t-lead, .t-main)" \
        " { visibility: hidden; }" in html
