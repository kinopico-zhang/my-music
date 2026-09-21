"""My Music 专辑分享测试 (1.8.33, 用户点名「共享专辑, 跟共享播放列表
差不多」): 整张专辑的临时链接 —— 公开面 (数据/流/封面) 只放行这张专辑
里的东西, 微信卡片取专辑封面。拆自 test_music_shares.py (该文件行数
到顶, 专辑这条线按域另立)。"""
from fastapi.testclient import TestClient

import app.main as m
from app.music.library_database import music_directory
from tests.music_audio_seed import PICTURE_BYTES, _write_audio
from tests.music_library_helpers import _seed_library


def _seed_with_files() -> None:
    """索引行 + 对应的真实音频文件 (流/封面接口要读盘): 曲A 带内嵌封面。"""
    _seed_library()
    _write_audio(music_directory(), "AI机组/甲/01.flac",
                 {"TITLE": "曲A"}, PICTURE_BYTES)
    _write_audio(music_directory(), "AI机组/甲/02.flac", {"TITLE": "曲B"})


def _share_album(client, album_id):
    response = client.post("/music/api/shares",
                           json={"kind": "album", "id": album_id})
    assert response.status_code == 200, response.text
    return response.json()


def test_share_album_public_flow(auth):
    """专辑分享全流程: 开链接 → 匿名访客拉到数据 (整张按碟号/音轨号排,
    副题带艺人), 播得到专辑里的流、取得到专辑封面; 别张专辑的歌一概
    404 —— token 只认"这份分享里确实有的东西"。"""
    _seed_with_files()
    made = _share_album(auth, 1)                     # 专辑「甲」(AI机组)
    assert len(made["token"]) == 32

    anon = TestClient(m.app)                         # 不带 cookie: 分享面免登录
    data = anon.get(f"/music/share/{made['token']}/api").json()
    assert data["kind"] == "album"
    assert data["title"] == "甲"
    assert data["subtitle"] == "AI机组 · 2 首 · 0 分钟"
    assert [t["title"] for t in data["tracks"]] == ["曲A", "曲B"]
    assert data["album_id"] == 1 and data["playlist"] is None

    # 专辑里的: 流/封面放行 (曲B 是 tak, 浏览器播不了但仍在清单里)
    assert anon.get(f"/music/share/{made['token']}/stream/1").status_code == 200
    assert anon.get(
        f"/music/share/{made['token']}/artwork/album/1").status_code == 200
    assert anon.get(
        f"/music/share/{made['token']}/artwork/track/1").status_code == 200
    # 别张专辑的 (Hello 在专辑「乙」): 一概 404
    assert anon.get(f"/music/share/{made['token']}/stream/3").status_code == 404
    assert anon.get(
        f"/music/share/{made['token']}/artwork/album/2").status_code == 404


def test_share_album_og_card(auth):
    """专辑分享的微信卡片 (og: 三件套): 标题 = 专辑名, 摘要带艺人,
    缩略图 = 专辑封面 (绝对地址)。"""
    _seed_with_files()
    made = _share_album(auth, 1)
    page = TestClient(m.app).get(f"/music/share/{made['token']}")
    assert page.status_code == 200
    assert '<meta property="og:title" content="甲">' in page.text
    assert ('<meta property="og:description" content="AI机组 · 2 首'
            ' · 0 分钟 · My Music">') in page.text
    assert (f'<meta property="og:image" content="http://testserver'
            f'/music/share/{made["token"]}/artwork/album/1">') in page.text
