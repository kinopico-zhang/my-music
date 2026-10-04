"""调整歌词测试 (1.8.133): 播放页 ⋯ 菜单的后端三口 —— 关键词搜候选 /
套用选中 (写库换时间轴清微调) / 对齐微调 (±30 秒钳制); 取数走
library_lyrics_search (三家并搜, 按选中取词)。"""
import json

from fastapi.testclient import TestClient

import app.main as m
from app.music import library_lyrics_search
from app.music.schemas import LyricsCandidate
from app.music.webapp import lyrics_edit_routes
from tests.music_audio_seed import _write_plain_track
from tests.music_library_helpers import _wait_scan_done


def _seeded_track(auth, tmp_path):
    """种一首并扫进库, 回 (track_id, 客户端) —— 三口都对着这一首。"""
    root = tmp_path / "music-library"
    _write_plain_track(root, "A乐队/2001 甲 [aaaa1111]/01 曲A.flac", "曲A")
    assert auth.post("/music/api/rescan").json() == {"started": True}
    _wait_scan_done(auth)
    return next(track["track_id"]
                for track in auth.get("/music/api/tracks").json()["tracks"]
                if track["title"] == "曲A")


def test_lyrics_offset_endpoint(auth, tmp_path):
    """对齐微调: 落库 (GET /lyrics 带回) + ±30 秒钳制 + 404/401 两道门。"""
    track_id = _seeded_track(auth, tmp_path)
    url = f"/music/api/tracks/{track_id}/lyrics/offset"
    body = auth.post(url, json={"offset_ms": 1500}).json()
    assert body["lyrics_offset_ms"] == 1500 and body["track_id"] == track_id
    assert auth.get(f"/music/api/tracks/{track_id}/lyrics"
                    ).json()["lyrics_offset_ms"] == 1500
    # 钳制: 正负各 30 秒封顶 (再大该换一套词, 不是微调的事了)
    assert auth.post(url, json={"offset_ms": 999999}
                     ).json()["lyrics_offset_ms"] == 30000
    assert auth.post(url, json={"offset_ms": -999999}
                     ).json()["lyrics_offset_ms"] == -30000
    assert auth.post("/music/api/tracks/999999/lyrics/offset",
                     json={"offset_ms": 0}).status_code == 404
    anonymous = TestClient(m.app)   # auth 登的是共享 client, 另开干净的
    assert anonymous.post(url, json={"offset_ms": 0}).status_code == 401


def test_lyrics_candidates_endpoint(auth, tmp_path, monkeypatch):
    """搜候选: 原样转交 (哪家/哪首/带不带轴), 关键词直通; 门与曲校验。"""
    track_id = _seeded_track(auth, tmp_path)
    seen = []

    def fake_search(query, api_base):
        seen.append((query, api_base))
        return [LyricsCandidate(source="netease", ref="7", title="曲A",
                                artist="A乐队"),
                LyricsCandidate(source="lrclib", ref="9", title="曲A",
                                artist="路人", synced=False)]

    monkeypatch.setattr(lyrics_edit_routes, "search_candidates", fake_search)
    url = f"/music/api/tracks/{track_id}/lyrics/candidates"
    r = auth.get(url, params={"q": "曲A A乐队"})
    assert r.status_code == 200
    assert r.json()["candidates"] == [
        {"source": "netease", "ref": "7", "title": "曲A",
         "artist": "A乐队", "synced": None},
        {"source": "lrclib", "ref": "9", "title": "曲A",
         "artist": "路人", "synced": False}]
    assert seen == [("曲A A乐队",
                     "https://lrclib.net/api")]   # api_base 走设置默认
    anonymous = TestClient(m.app)   # auth 登的是共享 client, 另开干净的
    assert anonymous.get(url, params={"q": "x"}).status_code == 401
    assert auth.get("/music/api/tracks/999999/lyrics/candidates",
                    params={"q": "x"}).status_code == 404


def test_lyrics_apply_endpoint(auth, tmp_path, monkeypatch):
    """套用选中: 取词写库 (换词清微调), 取不到 502, 门与曲校验。"""
    track_id = _seeded_track(auth, tmp_path)
    offset_url = f"/music/api/tracks/{track_id}/lyrics/offset"
    auth.post(offset_url, json={"offset_ms": 800})    # 先有一笔旧微调
    monkeypatch.setattr(
        lyrics_edit_routes, "candidate_lyrics",
        lambda source, ref, api_base:
            "[00:05.00]选中这份" if ref == "7" else "")
    url = f"/music/api/tracks/{track_id}/lyrics/apply"
    body = auth.post(url, json={"source": "netease", "ref": "7"}).json()
    assert body == {"track_id": track_id, "lyrics": "[00:05.00]选中这份",
                    "lyrics_synced": True, "lyrics_offset_ms": 0}
    assert auth.post(url, json={"source": "netease", "ref": "bad"}
                     ).status_code == 502
    assert auth.post("/music/api/tracks/999999/lyrics/apply",
                     json={"source": "netease", "ref": "7"}
                     ).status_code == 404
    anonymous = TestClient(m.app)   # auth 登的是共享 client, 另开干净的
    assert anonymous.post(url, json={"source": "netease", "ref": "7"}
                          ).status_code == 401


def test_lyrics_search_module(monkeypatch):
    """搜索模块本身: 三家并搜各解析各的形状 (伴奏剔除, 轴标记只有
    LRCLIB 当场知道); 取词按 ref 走对应厂商的路。"""
    calls = []   # 每家的 (url, POST 体, referer) 都记下顺带断言传参

    def fake_http(url, data=None, referer=""):
        calls.append((url, data, referer))
        if "music.163.com" in url:
            return {"result": {"songs": [{"id": 11, "name": "曲A",
                                          "artists": [{"name": "A乐队"}]}]}}
        if "c.y.qq.com" in url:
            return {"data": {"song": {"list": [
                {"songmid": "mid1", "songname": "曲A",
                 "singer": [{"name": "A乐队"}]}]}}}
        assert "/search?" in url and "track_name=" in url
        return [{"id": 5, "trackName": "曲A", "artistName": "路人",
                 "syncedLyrics": "[00:01.00]x", "instrumental": False},
                {"id": 6, "trackName": "曲A (伴奏)", "artistName": "路人",
                 "syncedLyrics": None, "instrumental": True}]

    monkeypatch.setattr(library_lyrics_search, "_http_json", fake_http)
    got = library_lyrics_search.search_candidates(" 曲A ",
                                                  "https://example.com/api")
    assert [(c.source, c.ref, c.synced) for c in got] \
        == [("netease", "11", None), ("qq", "mid1", None),
            ("lrclib", "5", True)]          # 伴奏剔除, 不占候选位
    # 网易的搜索词走 POST 体 + 挂 referer (与 library_lyrics_api 同一口径)
    netease_call = next(c for c in calls if "music.163.com" in c[0])
    assert b"%E6%9B%B2A" in netease_call[1] and netease_call[2] \
        == "https://music.163.com"
    assert library_lyrics_search.source_label("qq") == "QQ 音乐"
    # 取词: 网易/QQ 转交 library_lyrics_api 的按 id/mid 取词 (那边自家的
    # 行为 test_music_lyrics 有盖, 这里钉转交对口); LRCLIB 本地按歌 id 取;
    # 不认识的厂商空串
    monkeypatch.setattr(library_lyrics_search, "_netease_lyric_by_id",
                        lambda song_id: f"[00:0{song_id}.00]网易词")
    monkeypatch.setattr(library_lyrics_search, "_qq_lyric_by_mid",
                        lambda songmid: f"[00:0{songmid}.00]QQ词")
    monkeypatch.setattr(library_lyrics_search, "_http_json",
                        lambda url, data=None, referer="":
                        json.loads('{"syncedLyrics": "[00:01.00]x"}')
                        if url.endswith("/get/5") else None)
    assert library_lyrics_search.candidate_lyrics(
        "netease", "7", "base") == "[00:07.00]网易词"
    assert library_lyrics_search.candidate_lyrics(
        "qq", "mid1", "base") == "[00:0mid1.00]QQ词"
    assert library_lyrics_search.candidate_lyrics(
        "lrclib", "5", "https://example.com/api") == "[00:01.00]x"
    assert library_lyrics_search.candidate_lyrics(
        "spotify", "5", "https://example.com/api") == ""
    # 空关键词直接空手 (不打外网)
    monkeypatch.setattr(library_lyrics_search, "_http_json",
                        lambda *a, **k: (_ for _ in ()).throw(
                            AssertionError("空词不该联网")))
    assert library_lyrics_search.search_candidates("  ", "base") == []
