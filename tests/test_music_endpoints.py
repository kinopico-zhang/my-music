"""My Music 接口测试: 登录门槛, 浏览/搜索端点, 统计, 音质参数, Service
Worker, webapp 兜底。播放流水/排行 (1.8.31) 分家去
test_music_play_events。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

import app.main as m
from app import config
from app.music import library_queries
from app.music.library_database import Track, session_factory
from tests.music_library_helpers import _make_library, _seed_library, \
    _wait_scan_done


# ---------------------------------------------------------------- 接口

def _login(client):
    response = client.post(
        "/api/login",
        json={"user": config.AUTH_USER, "password": config.AUTH_PASS})
    assert response.status_code == 200


def test_music_page_requires_login(auth):
    """页面未登录 302 登录页, 接口未登录 401; 登录后页面 200。"""
    anonymous = TestClient(m.app)      # auth 会登录共享的 client, 这里另开
    assert anonymous.get("/music",
                         follow_redirects=False).status_code == 302
    assert anonymous.get("/music/api/status").status_code == 401
    assert anonymous.get("/music/api/stats").status_code == 401
    assert anonymous.get("/music/api/albums").status_code == 401
    assert auth.get("/music").status_code == 200   # 307 /music/ 跟一步到页面


def test_music_browse_and_search_endpoints(auth):
    """空库: 各接口空结果 + 404 + 参数校验 422。"""
    assert auth.get("/music/api/status").json()["track_count"] == 0
    assert auth.get("/music/api/stats").json() == {
        "artist_count": 0, "album_count": 0, "track_count": 0,
        "total_duration_seconds": 0.0, "formats": []}
    assert auth.get("/music/api/albums").json() == {
        "albums": [], "total_count": 0, "offset": 0, "limit": 60}
    assert auth.get("/music/api/artists").json()["artists"] == []
    assert auth.get("/music/api/tracks").json()["tracks"] == []
    assert auth.get("/music/api/search", params={"q": "x"}).json() == {
        "query": "x", "language": "全部", "tracks": [], "albums": [],
        "artists": [], "lyric_hits": [],
        "track_total": 0, "album_total": 0, "artist_total": 0, "lyric_total": 0}
    assert auth.get("/music/api/albums/1").status_code == 404
    assert auth.get("/music/api/artists/1").status_code == 404
    assert auth.get("/music/api/tracks/1/lyrics").status_code == 404
    assert auth.get("/music/api/albums/1/artwork").status_code == 404
    assert auth.get(
        "/music/api/albums", params={"language": "乱写"}).status_code == 422
    assert auth.get(
        "/music/api/albums", params={"sort": "乱写"}).status_code == 422
    assert auth.get(
        "/music/api/tracks", params={"limit": 0}).status_code == 422


def test_music_stats_endpoint(auth):
    """统计页: 库规模 + 总时长 + 格式分布 (多的在前, 同数按名, 播不了标记)。"""
    _seed_library()
    data = auth.get("/music/api/stats").json()
    assert data["artist_count"] == 2 and data["album_count"] == 3
    assert data["track_count"] == 5
    assert data["total_duration_seconds"] == 10.0      # 五曲各 2 秒
    assert data["formats"] == [
        {"format": "flac", "count": 3, "playable": True},
        {"format": "mp3", "count": 1, "playable": True},
        {"format": "tak", "count": 1, "playable": False}]


def test_music_track_quality_endpoint(auth, tmp_path):
    """音质参数 (1.8.127): 扫描顺手入库 (44.1kHz/16bit/立体声 + 大小算码率);
    老行 (列全 0, 1.8.127 前扫的) 首问现读文件回填; 文件没了读不出保持 0
    不炸; 没这曲 404。"""
    _make_library(tmp_path / "music-library")
    assert auth.post("/music/api/rescan").json() == {"started": True}
    _wait_scan_done(auth)
    with session_factory()() as session:
        track_id = session.execute(select(Track.id).where(
            Track.file_path.endswith("01 曲A.flac"))).scalar_one()
    data = auth.get(f"/music/api/tracks/{track_id}/quality").json()
    assert data["file_format"] == "flac"
    assert (data["sample_rate"], data["bit_depth"], data["channels"]) \
        == (44100, 16, 2)
    assert data["bitrate"] > 0
    # 老库行: 列清零再问 —— 现读文件回填, 第二问直接走库
    with session_factory()() as session:
        session.execute(update(Track).values(
            sample_rate=0, bit_depth=0, channels=0))
        session.commit()
    assert auth.get(
        f"/music/api/tracks/{track_id}/quality").json()["sample_rate"] == 44100
    # 文件没了 + 列是 0: 探测返回 None 保持 0, 整行藏
    (tmp_path / "music-library" / "AI机组" / "2019 甲 [aaaa1111]"
     / "01 曲A.flac").unlink()
    with session_factory()() as session:
        session.execute(update(Track).values(
            sample_rate=0, bit_depth=0, channels=0))
        session.commit()
    data = auth.get(f"/music/api/tracks/{track_id}/quality").json()
    assert data["sample_rate"] == 0 and data["bit_depth"] == 0
    assert auth.get("/music/api/tracks/99999/quality").status_code == 404


def test_music_share_quality_endpoint(auth, tmp_path):
    """分享页取质口 (1.8.130): 应用的 /api/tracks/{id}/quality 要登录,
    访客没有会话 —— /share/{token}/quality/{id} 免登录走同一条取数通道
    (走库/现读回填), 只放行这份分享里确实有的; 死链 410。"""
    _make_library(tmp_path / "music-library")
    assert auth.post("/music/api/rescan").json() == {"started": True}
    _wait_scan_done(auth)
    with session_factory()() as session:
        track_id = session.execute(select(Track.id).where(
            Track.file_path.endswith("01 曲A.flac"))).scalar_one()
        other_id = session.execute(select(Track.id).where(
            Track.id != track_id).order_by(Track.id)).scalars().first()
    made = auth.post("/music/api/shares",
                     json={"kind": "track", "id": track_id}).json()

    anon = TestClient(m.app)          # 不带 cookie: 分享面免登录
    data = anon.get(f"/music/share/{made['token']}/quality/{track_id}").json()
    assert data["file_format"] == "flac"
    assert (data["sample_rate"], data["bit_depth"], data["channels"]) \
        == (44100, 16, 2)
    assert data["bitrate"] > 0
    # 库里另一首不在这份分享里 / 死链 / 匿名问应用的口 (所以才有这条公开口)
    assert anon.get(
        f"/music/share/{made['token']}/quality/{other_id}").status_code == 404
    assert anon.get(
        f"/music/share/{'0' * 32}/quality/{track_id}").status_code == 410
    assert anon.get(
        f"/music/api/tracks/{track_id}/quality").status_code == 401


def test_music_service_worker_endpoint(client):
    """SW 脚本: 无需登录 200 (SW 更新检查不带 cookie), JS 类型, 可缓存校验。"""
    response = client.get("/music/sw.js")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/javascript")
    assert "music-downloads-v1" in response.text
    assert response.headers["cache-control"] == "no-cache"


def test_music_webapp_fallbacks(auth):
    """webapp 兜底: 登出 / 数据库异常 503 / 会话失效 401 / 资源不存在 404。"""
    from sqlalchemy.exc import SQLAlchemyError
    patched_queries = library_queries
    with pytest.MonkeyPatch.context() as patcher:   # 只撤自己的补丁
        patcher.setattr(patched_queries, "list_albums",
                        lambda *a, **k: (_ for _ in ()).throw(
                            SQLAlchemyError("boom")))
        assert auth.get("/music/api/albums").status_code == 503
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr("app.account_store.user_for_cookie",
                        lambda *a, **k: None)
        assert auth.get("/music/api/status").status_code == 401
    assert auth.get("/music/api/artists/99999").status_code == 404
    assert auth.get("/music/api/tracks/99999/lyrics").status_code == 404
    assert auth.get("/music/api/tracks/99999/credits").status_code == 404
    response = auth.post("/music/api/logout")     # 登出清 cookie, 放最后
    assert response.status_code == 200 and response.json() == {"ok": True}
