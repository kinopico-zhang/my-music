"""My Music 主页接线测试 (1.8.24 用户点名改版): 三段 —— 最近播放列表/
最近播放音乐/最近添加专辑, 各 10 个, 段头 › 查看全部 (1.8.30 用户点名
调序 + 补专辑卡跳转)。拆自
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
    每段 10 个, 段头整条可点 (› 查看全部 → 最近播放页/最近添加专辑页/播放列表页);
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
    # 每个都显示 10 个元素, 标题加一个 > 查看全部」); 1.8.30 用户点名调序
    # (列表段最前, 专辑段垫底) + 「最新添加专辑」改名「最近添加专辑」
    assert "const HOME_SECTION_COUNT = 10;" in home_js
    heads = [f'sectionHeadHTML("{title}", "{target}")'
             for title, target in [("最近播放列表", "playlists"),
                                   ("最近播放音乐", "recent"),
                                   ("最近添加专辑", "albums-recent")]]
    for head in heads:
        assert head in home_js
    # 1.8.81 用户点名「从最新添加专辑进去, 应该按照添加的时间倒排, 而不是
    # 按照字母顺序」: 段头改走 albums-recent 层 (标题「最近添加」, 按添加
    # 时间倒排), 菜单「所有专辑」照旧字母序 —— 两种进法两个段名, 缓存分开住
    views_js = (MUSIC_STATIC / "js" / "music-library-views.js").read_text(
        encoding="utf-8")
    pagination = (MUSIC_STATIC / "js" / "music-library-pagination.js").read_text(
        encoding="utf-8")
    assert 'recent ? "最近添加" : "所有专辑"' in views_js
    assert 'recent ? "albums-recent" : "albums"' in views_js
    assert 'renderAlbumsPane(target, "recent")' in js
    assert 'if (segment === "albums") parameters.set("sort", "title");' \
        in pagination
    assert 'else if (segment === "albums-recent") parameters.set("sort", "added");' \
        in pagination
    # 三段在 renderHomeView 里按 用户点的顺序铺 (列表 → 音乐 → 专辑)
    assert home_js.index(heads[0]) < home_js.index(heads[1]) \
        < home_js.index(heads[2])
    assert '"最新添加专辑"' not in home_js                # 旧名已退场
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
    # 1.8.30 专辑卡跳转补上 (你报的「点专辑进不去」): 与列表段/艺人页同款,
    # 绑容器 (内容异步重铺不累加), data-album-id 卡片 → album/<id>
    assert '$("#home-albums").addEventListener' in home_js
    assert 'navigate(`album/${card.dataset.albumId}`)' in home_js
    rendering = (MUSIC_STATIC / "js" / "music-list-rendering.js").read_text(
        encoding="utf-8")
    assert 'class="album-card playlist-card"' in rendering
    assert ".playlist-card .pl-icon { width: 100%; height: 100%;" in html
    # 播放列表详情路由
    assert 'if (name === "playlist" && argument)' in js
    assert "function renderPlaylistView(" in js
    # 播放列表独立成层 (原主页列表段上头的入口, 1.8.0 进上弹菜单)
    assert "function renderPlaylistsPane(" in js
    # 最近播放独立成层 (1.8.1): LRU 整页 (词标/下载标照旧)
    assert "function renderRecentPane(" in js
    assert '"top", "downloads", "search",' in js  # PANE_VIEWS 收录 (1.8.31 +top)
    assert 'else if (view === "recent") renderRecentPane(target);' in js
    assert '"/music/api/plays/recent?limit=100"' in js    # 全量页 100 首
    assert "pageState.recentPane" in js                   # 点行开播的队列语境
    recent_js = (MUSIC_STATIC / "js" / "music-recent-pane.js").read_text(
        encoding="utf-8")
    # 1.8.31 用户点名「最近播放不用显示播放次数」: 右缘回到时长
    # (trailingHTML 不传 = 默认时长); 次数只在播放排行页出
    assert "play_count" not in recent_js
    # 默认进主页 (单地址批: 旧深链开局消化一次, URL 洗成光杆 /music);
    # 1.8.8 起档案记整条轨迹, 开局逐层重放 (详见搜索接线测试)
    assert 'history.replaceState(null, "", location.pathname + location.search);' in js
    assert "journey.forEach(navigate);" in js


def test_music_top_plays_page_wiring():
    """播放排行页接线 (1.8.31 用户点名): 菜单「播放排行」推入层, 本周/本月/
    今年三榜左右滑切换 (设置页同款壳法: 大标题 + 页签钉住, 正文横向 snap
    三页各自竖滚); 行上只显区间内的播放次数 —— 时长/下载标都不出, 引导位
    是歌曲封面 (1.8.54 用户点名, 原来标名次)。数据来自播放流水 (老库没
    流水, 榜从这版起算, 接口测试在 test_music_endpoints)。"""
    html = music_page_shell()
    js = music_browser_js()
    top_js = (MUSIC_STATIC / "js" / "music-top-pane.js").read_text(
        encoding="utf-8")
    rendering = (MUSIC_STATIC / "js" / "music-list-rendering.js").read_text(
        encoding="utf-8")
    # 菜单入口 + 资源: css/js 各带版本参数
    assert 'data-pop-nav="top"' in html and "播放排行</button>" in html
    assert "css/music-top.css?v=" in html
    assert "js/music-top-pane.js?v=" in html
    # 路由收录 + 推入层分发
    assert '"top", "downloads", "search",' in js
    assert 'else if (view === "top") renderTopPane(target);' in js
    assert "pageState.topPanes" in js                     # 三榜各记队列语境
    # 三榜页签 (数组序即页序) + 左右滑 snap 容器 (页签点击/手滑互切)
    for frag in ['const TOP_PERIODS = [', '{ key: "week", label: "本周"',
                 '{ key: "month", label: "本月"',
                 '{ key: "year", label: "今年"',
                 'data-top-period="${period.key}"',
                 'data-top-page="${period.key}"',
                 '`/music/api/plays/top?period=${period.key}`',
                 'body.scrollTo({ left: index * body.clientWidth, behavior: "smooth" });',
                 "Math.round(body.scrollLeft / (body.clientWidth || 1))",
                 "bindTrackLists(element, () => pageState.topPanes[period.key]"]:
        assert frag in top_js, f"播放排行页缺 {frag}"
    # 行: 封面占引导位 (播放列表同款 .art 槽), 右缘 = 区间内播放次数
    # (trailingHTML 顶掉时长位), plain 连下载标一起收走 (用户点名)
    assert "trackArtHTML, trackRowHTML */" in top_js
    assert 'track, trackArtHTML(track), "art",' in top_js
    assert '`×${track.play_count}`, true)' in top_js
    assert "trackArtHTML" in rendering                    # 封面引导位是现成件
    assert "top-rank" not in top_js and "top-rank" not in html   # 名次位退役
    assert "${!plain && downloadsEnabled ?" in rendering  # plain 选项收下载标
    # 样式: 设置页同款壳法 (层衬清零自己管布局) + snap 容器
    for frag in ['.push-pane[data-view="top"] .pane-scroll {',
                 ".top-tabs button.on {", "#top-body {",
                 "scroll-snap-type: x mandatory; overscroll-behavior-x: contain;",
                 ".top-page {", "scroll-snap-align: start;"]:
        assert frag in html, f"播放排行样式缺 {frag}"
    # 最左页右划让回右划返回 (分页容器看门, 搜索/设置同款)
    assert '"#search-body.paged, #settings-body, #top-body"' in js


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
