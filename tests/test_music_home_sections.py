"""My Music 主页接线测试 (1.8.24 用户点名改版): 三段 —— 最近播放音乐/
最新添加专辑/最近播放列表, 各 10 个, 段头 › 查看全部。拆自
test_music_page_wiring.py (主页断言随改版长出一片, 按域分家);
「最近播放列表」的查询层/接口层测试也住这 (主页一段的口径)。"""
import time

from fastapi.testclient import TestClient

import app.main as m
from app.music import library_playlists, library_queries
from app.music.library_database import session_factory
from tests.music_library_helpers import _seed_library
from tests.music_static_files import (MUSIC_STATIC, music_browser_js,
                                      music_page_shell)


def test_music_home_page_wiring():
    """主页接线 (1.8.0: 主页是唯一根视图, 其余全是推入层; 1.8.24 改三段):
    每段 10 个, 段头整条可点 (› 查看全部 → 最近播放页/所有专辑/播放列表页);
    最近播放列表走新接口 (成员曲目最近被播过的在前, 没播过的按编辑时刻)。"""
    html = music_page_shell()
    js = music_browser_js()
    home_js = (MUSIC_STATIC / "js" / "music-home-view.js").read_text(
        encoding="utf-8")
    assert '<div id="dock">' in html                     # 船坞三件套在场
    assert 'data-pop-nav="playlists"' in html           # 菜单进播放列表
    assert 'data-pop-nav="recent"' in html              # 菜单进最近播放页
    assert 'id="dock-search"' in html                   # 搜索键直进搜索页
    assert 'id="search-btn"' not in html    # 放大镜按钮已撤
    assert 'id="sync-playlists"' not in html     # Plex 同步入口已撤
    assert "playlist-row" in html                  # 行样式在
    assert "function renderHomeView()" in js
    # 1.8.24 三段 (用户点名「分成最近播放音乐, 最新添加专辑, 最近播放列表,
    # 每个都显示 10 个元素, 标题加一个 > 查看全部」)
    assert "const HOME_SECTION_COUNT = 10;" in home_js
    for title, target in [("最近播放音乐", "recent"),
                          ("最新添加专辑", "albums"),
                          ("最近播放列表", "playlists")]:
        assert f'sectionHeadHTML("{title}", "{target}")' in home_js
    assert 'data-see-all="${target}"' in home_js   # 段头目标页
    assert '<span class="chev">›</span>' in home_js        # 段头右缘的 ›
    assert "navigate(head.dataset.seeAll)" in home_js     # 整条可点
    # 段头点击绑在 document: #root-view 常驻, 绑它身上主页重铺一次就多挂
    # 一份 (点一下进两层), 只有随 innerHTML 重造的子容器可以就地绑
    assert '$("#root-view").addEventListener' not in home_js
    assert "button.section-head" in html             # 按钮化的兜底重置
    # 各段数据: 曲目 10 首 / 专辑最新入库 10 张 / 列表最近播过优先 10 个
    assert "plays/recent?limit=${HOME_SECTION_COUNT}" in home_js
    assert "/music/api/albums?sort=added&limit=${HOME_SECTION_COUNT}" \
        in home_js
    assert "/music/api/playlists/recent?limit=${HOME_SECTION_COUNT}" \
        in home_js
    assert 'id="home-albums" class="album-grid"' in home_js  # 专辑段网格
    assert "albumCardHTML" in home_js                     # 专辑卡渲染
    # 1.8.28 播放列表段改专辑同款网格卡 (用户点名「排版和最近专辑一样」):
    # 复用 .album-card 排版 + .pl-icon 渐变兜底; 卡片不挂壳, 删整列走
    # 播放列表页 (列表行照旧带左滑删除)
    assert 'id="home-playlists" class="album-grid"' in home_js
    assert "playlistCardHTML" in home_js
    assert 'bindSwipeDelete($("#home-playlists")' not in home_js
    rendering = (MUSIC_STATIC / "js" / "music-list-rendering.js").read_text(
        encoding="utf-8")
    assert 'class="album-card playlist-card"' in rendering
    assert ".playlist-card .pl-icon { width: 100%; height: 100%;" in html
    # 播放列表详情路由
    assert 'if (name === "playlist" && argument)' in js
    assert "function renderPlaylistView(" in js
    # 播放列表独立成层 (原主页列表段上头的入口, 1.8.0 进上弹菜单)
    assert "function renderPlaylistsPane(" in js
    # 最近播放独立成层 (1.8.1): LRU 整页 + 次数替时长 (词标/下载标照旧)
    assert "function renderRecentPane(" in js
    assert '"recent", "downloads",' in js                 # PANE_VIEWS 收录
    assert 'else if (view === "recent") renderRecentPane(target);' in js
    assert '"/music/api/plays/recent?limit=100"' in js    # 全量页 100 首
    assert "pageState.recentPane" in js                   # 点行开播的队列语境
    assert "`×${track.play_count}`" in js                 # 行右缘 = 播过几次
    # 默认进主页 (单地址批: 旧深链开局消化一次, URL 洗成光杆 /music);
    # 1.8.8 起档案记整条轨迹, 开局逐层重放 (详见搜索接线测试)
    assert 'history.replaceState(null, "", location.pathname + location.search);' in js
    assert "journey.forEach(navigate);" in js


def test_recent_playlists_query():
    """查询层 (1.8.24): 「最近播放列表」按最近用过排 —— 播过旗下曲目看
    最近那次播放 (播放压过编辑: 播完再改名的列表不跳前), 没播过的看最后
    编辑时刻; 按人记, 别人播的不算数。"""
    _seed_library()
    with session_factory()() as session:
        often = library_playlists.create_playlist(session, "常听")
        older = library_playlists.create_playlist(session, "老列表")
        library_playlists.add_track_to_playlist(session, often.playlist_id, 1)
        library_playlists.add_track_to_playlist(session, older.playlist_id, 3)
        # 本人: 先播「老列表」里的 Hello, 再播「常听」里的曲A —— 常听顶前
        assert library_queries.record_play(session, "u-home", 3) is True
        time.sleep(0.01)                 # last_played_at 是 epoch 秒, 隔开
        assert library_queries.record_play(session, "u-home", 1) is True
        time.sleep(0.01)
        # 播完又改了「老列表」的名 —— 播放压过编辑, 排位不动
        library_playlists.rename_playlist(session, older.playlist_id, "改名了")
        names = [p.name for p
                 in library_queries.recent_playlists(session, "u-home")]
        assert names[:2] == ["常听", "改名了"]
        # limit 生效 (只取 1 个 = 最前的)
        assert [p.name for p in library_queries.recent_playlists(
            session, "u-home", 1)] == ["常听"]
        # 别人没播过: 全按编辑时刻, 刚改名的在最前
        others = [p.name for p
                  in library_queries.recent_playlists(session, "别人")]
        assert others[:2] == ["改名了", "常听"]
        # 行模型与全量清单同款 (封面/计数那套不用另算)
        brief = library_queries.recent_playlists(session, "u-home")[0]
        assert brief.track_count == 1 and brief.updated_at > 0


def test_recent_playlists_endpoint(auth):
    """接口层 (1.8.24): /api/playlists/recent 走登录门槛 + 参数校验,
    最近播过旗下曲目的列表在前。"""
    _seed_library()
    assert TestClient(m.app).get(
        "/music/api/playlists/recent").status_code == 401
    assert auth.get("/music/api/playlists/recent",
                    params={"limit": 0}).status_code == 422
    # 建两个列表, 只播其中一个的成员曲 —— 播过的在前, 没播的按编辑排后
    first = auth.post("/music/api/playlists",
                      json={"name": "常听"}).json()["playlist_id"]
    auth.post("/music/api/playlists", json={"name": "没听过"})
    auth.post(f"/music/api/playlists/{first}/tracks", json={"track_id": 1})
    auth.post("/music/api/plays", json={"track_id": 1})
    data = auth.get("/music/api/playlists/recent").json()
    assert [p["name"] for p in data["playlists"]] == ["常听", "没听过"]
    assert data["playlists"][0]["track_count"] == 1
