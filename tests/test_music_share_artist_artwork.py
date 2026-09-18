"""My Music 分享页歌手海报测试 (1.8.17 用户点名「在歌名和艺人旁边加歌手
照片」): 海报走公开艺人路由, 门禁还是分享的老规矩 —— 每个 token 只放行
"这份分享里确实有的艺人"的图, 拿着 A 的链接看不到 B 的海报。"""
from fastapi.testclient import TestClient

import app.main as m
from app.music.library_database import Artist, music_directory, session_factory
from tests.music_library_helpers import _seed_library

# JPEG 魔数 + 内容 (路由透传文件字节, 不解析图)
POSTER_BYTES = b"\xff\xd8\xff\xe0poster-for-share"


def test_share_artist_artwork_scoped(auth):
    """曲A 的分享只认 AI机组 (艺人 1) 的海报: 老歌手 (艺人 2) 也传了
    海报, 但不在这份分享里, 一样 404 —— 门禁 (scope) 在前, 有没有海报
    在后; 没这个艺人 404, 链接不存在 410。"""
    _seed_library()
    with session_factory()() as session:
        for artist_id, directory in ((1, "AI机组"), (2, "老歌手")):
            artist = session.get(Artist, artist_id)
            assert artist is not None
            artist.poster_file = "poster.jpeg"
            folder = music_directory() / directory
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "poster.jpeg").write_bytes(POSTER_BYTES)
        session.commit()
    made = auth.post("/music/api/shares", json={"kind": "track", "id": 1}).json()
    anon = TestClient(m.app)                      # 不带 cookie: 分享面免登录
    base = f"/music/share/{made['token']}/artwork/artist"
    mine = anon.get(f"{base}/1")
    assert mine.status_code == 200 and mine.content == POSTER_BYTES
    assert mine.headers["content-type"].startswith("image/jpeg")
    assert anon.get(f"{base}/2").status_code == 404   # 有海报, 不在范围
    assert anon.get(f"{base}/999").status_code == 404
    assert anon.get(
        f"/music/share/{'0' * 32}/artwork/artist/1").status_code == 410
