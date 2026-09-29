"""My Music 单艺人重扫测试 (1.8.75 艺人页「刷新元数据」按钮): 扫描器层
强制重读/名字跟新标签走/只清这棵子树, 接口层口径, 前端按钮与海报版本号。
"""
import shutil

from sqlalchemy import func, select, update

from app.music import service
from app.music.library_database import Album, Artist, Track, session_factory
from tests.music_audio_seed import PICTURE_BYTES, _write_audio
from tests.music_library_helpers import (_make_library, _scanner_for,
                                         _wait_scan_done)
from tests.music_static_files import MUSIC_STATIC, music_page_shell


def test_scanner_artist_refresh_forces_and_follows_tags(tmp_path):
    """单艺人重扫: 签名没变也强制重读 (写脏的行医好), 改过的名字/标题跟
    新标签走 (整库扫描只在空时填, 不抹的话新名字永远进不来), 海报认目录
    里现在的文件; 隔壁艺人一行不碰。"""
    root = tmp_path / "music-library"
    _make_library(root)
    scanner = _scanner_for(root)
    scanner.scan()

    # 索引行写脏 (文件没动, 签名一致 —— 整库增量扫会跳过): 强制重读医好
    with session_factory()() as session:
        session.execute(update(Track).where(
            Track.file_path == "AI机组/2019 甲 [aaaa1111]/01 曲A.flac"
        ).values(title="脏数据"))
        session.commit()
    (root / "AI机组/poster.jpeg").unlink()          # 海报换成 png
    (root / "AI机组/poster.png").write_bytes(PICTURE_BYTES)
    scanner.scan_artist("AI机组")
    with session_factory()() as session:
        healed = session.execute(select(Track).where(
            Track.file_path == "AI机组/2019 甲 [aaaa1111]/01 曲A.flac"
        )).scalar_one()
        assert healed.title == "曲A"
        artist = session.execute(select(Artist).where(
            Artist.directory == "AI机组")).scalar_one()
        assert artist.poster_file == "poster.png"
        other = session.execute(select(Artist).where(
            Artist.directory == "老歌手")).scalar_one()
        assert other.name == "老歌手" and other.poster_file == ""
        assert session.execute(select(func.count()).select_from(Track).where(
            Track.file_path.startswith("老歌手/"))).scalar() == 2

    # 改标签 (mtime 保持 2000 不动): 艺人名/专辑名跟新标签走
    _write_audio(root, "AI机组/2019 甲 [aaaa1111]/01 曲A.flac",
                 {"TITLE": "曲A新", "ARTIST": "新机组", "ALBUMARTIST": "新机组",
                  "ALBUM": "甲新版", "DATE": "2019", "SCRIPT": "Jpan"},
                 mtime=2000.0)
    scanner.scan_artist("AI机组")
    with session_factory()() as session:
        artist = session.execute(select(Artist).where(
            Artist.directory == "AI机组")).scalar_one()
        assert artist.name == "新机组"
        album = session.execute(select(Album).where(
            Album.directory == "AI机组/2019 甲 [aaaa1111]")).scalar_one()
        assert album.title == "甲新版" and album.track_count == 1
        track = session.execute(select(Track).where(
            Track.file_path == "AI机组/2019 甲 [aaaa1111]/01 曲A.flac"
        )).scalar_one()
        assert track.title == "曲A新"


def test_scanner_artist_refresh_prunes_only_subtree(tmp_path):
    """只清这棵子树: 删掉的曲目行消失、专辑汇总跟着降; 艺人目录整个没了
    连空专辑带艺人行一起清 —— 隔壁艺人原封不动。"""
    root = tmp_path / "music-library"
    _make_library(root)
    scanner = _scanner_for(root)
    scanner.scan()

    (root / "老歌手/2001 丙 [cccc3333]/02 曲D.flac").unlink()
    scanner.scan_artist("老歌手")
    with session_factory()() as session:
        album = session.execute(select(Album).where(
            Album.directory == "老歌手/2001 丙 [cccc3333]")).scalar_one()
        assert album.track_count == 1              # 汇总跟着降
        assert session.execute(select(func.count()).select_from(Track).where(
            Track.file_path.startswith("AI机组/"))).scalar() == 2  # 隔壁没动

    shutil.rmtree(root / "AI机组")
    scanner.scan_artist("AI机组")
    with session_factory()() as session:
        assert session.execute(select(Artist).where(
            Artist.directory == "AI机组")).scalars().all() == []
        assert session.execute(select(func.count()).select_from(Track).where(
            Track.file_path.startswith("AI机组/"))).scalar() == 0
        assert session.execute(select(Artist).where(
            Artist.directory == "老歌手")).scalar_one().name == "老歌手"


def test_music_artist_refresh_endpoint(auth, tmp_path):
    """艺人页按钮接口: 脏行医好 + 名字跟新标签走 + 海报换新址 (poster_version
    跟着新海报的 mtime 变, 前端换图即换址), 404/409 口径。"""
    root = tmp_path / "music-library"
    _make_library(root)
    assert auth.post("/music/api/rescan").json() == {"started": True}
    _wait_scan_done(auth)
    assert auth.post("/music/api/artists/99999/refresh").status_code == 404

    artists = auth.get("/music/api/artists").json()["artists"]
    ai = next(a for a in artists if a["has_poster"])
    assert ai["poster_version"] > 0              # 海报版本号 = 文件 mtime

    # 改一首的标签 + 另一首行写脏 + 海报换 png
    _write_audio(root, "AI机组/2019 甲 [aaaa1111]/01 曲A.flac",
                 {"TITLE": "曲A新", "ARTIST": "新机组", "ALBUMARTIST": "新机组",
                  "ALBUM": "甲", "DATE": "2019", "SCRIPT": "Jpan"}, mtime=2000.0)
    with session_factory()() as session:
        session.execute(update(Track).where(
            Track.file_path == "AI机组/2020 乙 [bbbb2222]/01 曲B.flac"
        ).values(title="脏数据"))
        session.commit()
    (root / "AI机组/poster.jpeg").unlink()
    (root / "AI机组/poster.png").write_bytes(PICTURE_BYTES)

    assert auth.post(
        f"/music/api/artists/{ai['artist_id']}/refresh").json() == {"ok": True}
    page = auth.get(f"/music/api/artists/{ai['artist_id']}").json()
    assert page["artist"]["name"] == "新机组"
    assert page["artist"]["poster_version"] != ai["poster_version"]
    titles = {track["title"] for track
              in auth.get("/music/api/tracks").json()["tracks"]}
    assert titles == {"曲A新", "曲B", "曲C", "曲D"}     # 脏行已医好

    # 全库扫描占着锁 (两个写者共用一把): 409
    current = service.scanner()
    assert current._scan_lock.acquire(  # noqa: SLF001 pylint: disable=consider-using-with
        blocking=False)
    try:
        response = auth.post(f"/music/api/artists/{ai['artist_id']}/refresh")
        assert response.status_code == 409
        assert "扫描正在进行中" in response.json()["detail"]
    finally:
        current._scan_lock.release()                   # noqa: SLF001


def test_music_artist_refresh_wiring():
    """前端接线: 艺人页操作行多一颗「刷新元数据」, 点击 POST 单艺人重扫,
    完了整页重拉; 艺人海报 URL 带 mtime 版本号 (?v=) —— SW 封面缓存按
    URL 存, 没有版本号换了海报永远读旧头像 (这正是换头像不见新的根)。"""
    views_js = (MUSIC_STATIC / "js" / "music-album-artist-views.js"
                ).read_text(encoding="utf-8")
    common_js = (MUSIC_STATIC / "js" / "music-common.js").read_text(
        encoding="utf-8")
    for frag in ['id="artist-refresh"', 'title="刷新元数据"',
                 "${ICON_ACTION_REFRESH}",
                 "`/music/api/artists/${artistId}/refresh`",
                 "{ method: \"POST\" }",
                 "await renderArtistView(artistId, target);",
                 'button.disabled = true;',
                 'toast("正在刷新元数据…");', 'toast("元数据已刷新");',
                 'toast(`刷新失败: ${error.message}`);']:
        assert frag in views_js, f"艺人页缺 {frag}"
    # 海报 URL 版本号 (换图即换址) + 图标本体 + 供跨模块引用的导出名
    assert "artwork?v=${artist.poster_version || 0}" in common_js
    assert "const ICON_ACTION_REFRESH" in common_js
    assert "ICON_ACTION_REFRESH" in common_js[:common_js.index("*/")]
    routes_py = (MUSIC_STATIC.parent / "webapp" / "library_routes.py"
                 ).read_text(encoding="utf-8")
    assert '@router.post("/artists/{artist_id}/refresh"' in routes_py
    assert "scan_artist(artist.directory)" in routes_py
    assert "HTTPException(409, str(exc))" in routes_py
    queries_py = (MUSIC_STATIC.parent / "library_queries" / "browse_queries.py"
                  ).read_text(encoding="utf-8")
    assert queries_py.count("poster_version=_poster_version(artist)") == 2
    html = music_page_shell()
    assert "js/music-common.js?v=21" in html
    assert "js/music-album-artist-views.js?v=10" in html
