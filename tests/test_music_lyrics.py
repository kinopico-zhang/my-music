"""歌词测试: 联网拉取与持久化, fetch_lyrics 路径分支 (1.8.57 起多厂商:
LRCLIB / 网易云 / QQ, 「自动」依次试)。拆自原 test_music_settings.py。"""
import base64
import json
from email.message import Message
from urllib.error import HTTPError
from urllib.parse import urlencode

import pytest

from app.music import library_lyrics_api, library_queries, library_settings
from tests.music_audio_seed import _write_plain_track
from tests.music_library_helpers import _wait_scan_done

def test_lyrics_fetched_from_api_and_persisted(auth, tmp_path):
    """歌词联网补齐: 求到写回索引 (之后离线也有), 求不到保持空; 关了 API 不联网。"""
    root = tmp_path / "music-library"
    _write_plain_track(root, "A乐队/2001 甲 [aaaa1111]/01 曲A.flac", "曲A")
    _write_plain_track(root, "A乐队/2001 甲 [aaaa1111]/02 曲B.flac", "曲B")
    assert auth.post("/music/api/rescan").json() == {"started": True}
    _wait_scan_done(auth)
    tracks = {track["title"]: track["track_id"]
              for track in auth.get("/music/api/tracks").json()["tracks"]}

    # 求到带时间轴的 → 写回索引, synced 标记跟走 (默认厂商空串 = 自动)
    calls = []

    def fake_fetch(provider, api_base, title, artist, album_title):
        calls.append((provider, api_base, title, artist, album_title))
        return "[00:10.00]从API求来的"

    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(library_queries.lyrics_queries, "fetch_lyrics", fake_fetch)
        lyrics = auth.get(f"/music/api/tracks/{tracks['曲A']}/lyrics").json()
    assert lyrics == {"track_id": tracks["曲A"],
                      "lyrics": "[00:10.00]从API求来的",
                      "lyrics_synced": True,
                      "lyrics_offset_ms": 0}   # 1.8.133 起应答带对齐微调
    assert calls == [("", library_settings.LYRICS_API_DEFAULT,
                      "曲A", "A乐队", "曲A的专辑")]

    # 写回了索引: 再问不再联网 (替身这次一被调就炸)
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(library_queries.lyrics_queries, "fetch_lyrics",
                        lambda *a: (_ for _ in ()).throw(
                            AssertionError("不该再联网")))
        again = auth.get(f"/music/api/tracks/{tracks['曲A']}/lyrics").json()
    assert again["lyrics"] == "[00:10.00]从API求来的"

    # 求不到 (空串): 保持没歌词
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(library_queries.lyrics_queries, "fetch_lyrics", lambda *a: "")
        empty = auth.get(f"/music/api/tracks/{tracks['曲B']}/lyrics").json()
    assert empty == {"track_id": tracks["曲B"], "lyrics": "",
                     "lyrics_synced": False, "lyrics_offset_ms": 0}

    # 设置里关掉歌词 API: 连求都不求
    assert auth.post("/music/api/settings",
                     json={"lyrics_api_enabled": False}
                     ).json()["lyrics_api_enabled"] is False
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(library_queries.lyrics_queries, "fetch_lyrics",
                        lambda *a: (_ for _ in ()).throw(
                            AssertionError("关了 API 不该联网")))
        empty = auth.get(f"/music/api/tracks/{tracks['曲B']}/lyrics").json()
    assert empty["lyrics"] == ""


class _FakeResponse:
    """urlopen 的替身应答 (够 fetch_lyrics 用: status + read + 上下文)。"""

    def __init__(self, payload: bytes, status: int = 200):
        """带状态码的定身响应。"""
        self._payload = payload
        self.status = status

    def read(self) -> bytes:
        """一次性吐出全部响应体。"""
        return self._payload

    def __enter__(self):
        """with 块进入 (urlopen 是上下文管理器)。"""
        return self

    def __exit__(self, *exc):
        """交还异常 (有异常照常往外抛)。"""
        return False


def test_fetch_lyrics_paths(monkeypatch):
    """联网求词的分支 (LRCLIB 一家时): 优先带时间轴的 / 截断 / 各种失败一律
    空串不抛。"""
    requested = {}

    def fake_urlopen(request, timeout):
        requested["url"] = request.full_url
        requested["timeout"] = timeout
        return _FakeResponse(json.dumps(
            {"syncedLyrics": "[00:01.00]synced",
             "plainLyrics": "plain"}).encode())

    monkeypatch.setattr(library_lyrics_api, "urlopen", fake_urlopen)
    assert library_lyrics_api.fetch_lyrics(
        "lrclib", "https://example.com/api/", "曲", "艺人", "专辑") == "[00:01.00]synced"
    assert requested["url"].startswith("https://example.com/api/get?")
    assert "track_name=" in requested["url"]
    assert requested["timeout"] == library_lyrics_api._TIMEOUT_SECONDS  # noqa: SLF001

    # 只剩纯文本: 用 plainLyrics; 空地址 (相对 URL) 当失败
    monkeypatch.setattr(library_lyrics_api, "urlopen", lambda req, timeout:
                        _FakeResponse(b'{"plainLyrics": "plain text"}'))
    assert library_lyrics_api.fetch_lyrics(
        "lrclib", "https://example.com/api", "t", "a", "b") == "plain text"
    assert library_lyrics_api.fetch_lyrics("lrclib", "", "t", "a", "b") == ""

    # 超长截断 (与库里的歌词列同一上限)
    monkeypatch.setattr(library_lyrics_api, "urlopen", lambda req, timeout:
                        _FakeResponse(b'{"plainLyrics": "' + b"x" * 30000
                                      + b'"}'))
    assert len(library_lyrics_api.fetch_lyrics(
        "lrclib", "https://example.com/api", "t", "a", "b")) \
        == library_lyrics_api._MAX_LYRICS_BYTES                    # noqa: SLF001

    # 失败分支: 404 / 坏 JSON / 非对象 / 非 200 —— 都当求不到
    monkeypatch.setattr(library_lyrics_api, "urlopen", lambda req, timeout:
                        (_ for _ in ()).throw(
                            HTTPError(req.full_url, 404, "Not Found",
                                      Message(), None)))
    assert library_lyrics_api.fetch_lyrics(
        "lrclib", "https://example.com/api", "t", "a", "b") == ""
    monkeypatch.setattr(library_lyrics_api, "urlopen", lambda req, timeout:
                        _FakeResponse(b"not json"))
    assert library_lyrics_api.fetch_lyrics(
        "lrclib", "https://example.com/api", "t", "a", "b") == ""
    monkeypatch.setattr(library_lyrics_api, "urlopen", lambda req, timeout:
                        _FakeResponse(b"[1, 2]"))
    assert library_lyrics_api.fetch_lyrics(
        "lrclib", "https://example.com/api", "t", "a", "b") == ""
    monkeypatch.setattr(library_lyrics_api, "urlopen", lambda req, timeout:
                        _FakeResponse(b"{}", status=503))
    assert library_lyrics_api.fetch_lyrics(
        "lrclib", "https://example.com/api", "t", "a", "b") == ""


def test_fetch_lyrics_providers(monkeypatch):
    """1.8.57 多厂商 (用户点名「歌词接口多提供几个厂商」): 网易云/QQ 各自
    搜索+取词两步; 搜索结果按 歌名+艺人 挑 (翻唱不抢正主的词);「自动」
    (空串) 依次试到求到为止, 头一家求到就不往下走。"""
    def netease_fake(request, timeout):
        if "search/get" in request.full_url:       # 搜索: POST 表单带歌名+艺人
            assert request.data == urlencode({"s": "曲A A乐队"}).encode()
            return _FakeResponse(json.dumps({"result": {"songs": [
                {"id": 1, "name": "曲A", "artists": [{"name": "翻唱乐队"}]},
                {"id": 2, "name": "曲A", "artists": [{"name": "A乐队"}]}]}}).encode())
        assert "song/lyric" in request.full_url
        assert "id=2" in request.full_url          # 挑中的不是头一条翻唱
        return _FakeResponse(json.dumps(
            {"lrc": {"lyric": "[00:01.00]网易词"}}).encode())

    monkeypatch.setattr(library_lyrics_api, "urlopen", netease_fake)
    assert library_lyrics_api.fetch_lyrics(
        "netease", "https://example.com/api", "曲A", "A乐队", "专辑") \
        == "[00:01.00]网易词"

    def qq_fake(request, timeout):                 # QQ: songmid + base64 歌词
        if "client_search_cp" in request.full_url:
            return _FakeResponse(json.dumps({"data": {"song": {"list": [
                {"songmid": "mid1", "songname": "曲A",
                 "singer": [{"name": "A乐队"}]}]}}}).encode())
        assert "songmid=mid1" in request.full_url
        return _FakeResponse(json.dumps({"retcode": 0, "lyric": base64.b64encode(
            "[00:02.00]QQ词".encode()).decode()}).encode())

    monkeypatch.setattr(library_lyrics_api, "urlopen", qq_fake)
    assert library_lyrics_api.fetch_lyrics(
        "qq", "https://example.com/api", "曲A", "A乐队", "专辑") == "[00:02.00]QQ词"

    # 自动: 网易云空手 → 顺到 QQ 求到 → 不再试 LRCLIB (自定义地址没人碰)
    seq = []

    def chain_fake(request, timeout):
        seq.append(request.full_url)
        if "music.163.com" in request.full_url:
            return _FakeResponse(b'{"result": {"songCount": 0}}')
        if "client_search_cp" in request.full_url:
            return _FakeResponse(json.dumps({"data": {"song": {"list": [
                {"songmid": "m", "songname": "曲A",
                 "singer": [{"name": "A乐队"}]}]}}}).encode())
        return _FakeResponse(json.dumps({"retcode": 0, "lyric": base64.b64encode(
            "[00:03.00]顺到的词".encode()).decode()}).encode())

    monkeypatch.setattr(library_lyrics_api, "urlopen", chain_fake)
    assert library_lyrics_api.fetch_lyrics(
        "", "https://example.com/api", "曲A", "A乐队", "专辑") == "[00:03.00]顺到的词"
    assert any("music.163.com" in url for url in seq)     # 从网易云起试
    assert not any("example.com" in url for url in seq)    # 求到就收手
