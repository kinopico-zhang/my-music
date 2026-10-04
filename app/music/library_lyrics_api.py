"""联网补歌词: 内嵌标签和同名 .lrc 都没有时, 上网求一遍 (1.8.57 起多家厂商)。

厂商: LRCLIB (国际; 兼容接口可换地址) / 网易云 / QQ 音乐 —— 设「自动」
(默认) 就按 网易云 → QQ → LRCLIB 依次试, 头一家求到为止: 中文歌网易云
和 QQ 全得多, 国际歌兜底靠 LRCLIB。求到就写回索引 (tracks.lyrics) ——
之后离线也能看, 搜索歌词也搜得到; 求不到 (没有这首 / 断网 / 超时) 保持
空, 前端照旧显示「没有歌词」。
"""
import base64
import html
import json
from collections.abc import Callable
from typing import Final
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_TIMEOUT_SECONDS = 4.0
_MAX_LYRICS_BYTES = 20000      # 与扫描入库同一截断 (库里 lyrics 就存这么长)


def _http_json(url: str, data: bytes | None = None,
               referer: str = "") -> object:
    """一发请求回解析好的 JSON; 任何失败回 None (不抛, 不挡听歌)。"""
    headers = {"User-Agent": "Mozilla/5.0"}
    if referer:
        headers["Referer"] = referer
    try:
        with urlopen(Request(url, data=data, headers=headers),
                     timeout=_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                return None
            return json.loads(response.read().decode("utf-8", "replace"))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return None            # 404 / 断网 / 超时 / 坏 JSON: 都当求不到


def _search_query(title: str, artist: str) -> str:
    """搜索词: 歌名 + 艺人 (哪家搜索都这么喂)。"""
    return " ".join(part for part in (title, artist) if part)


def _pick_song(songs: list[tuple[str, str, list[str]]], title: str,
               artist: str) -> str | None:
    """搜索结果里挑最像的那首: 名字相等且艺人对得上 > 只名字相等 > 头一个。

    网易云搜「晴天」头一条常是翻唱 —— 拿歌名和艺人双对, 才不会把别人
    的词配到这首歌上。"""
    if not songs:
        return None
    titled = [song for song in songs if song[1] == title]
    for song in titled:
        names = " ".join(song[2])
        if artist and (artist in names
                       or any(name and name in artist for name in song[2])):
            return song[0]
    return (titled or songs)[0][0]


def _lrclib(api_base: str, title: str, artist: str, album_title: str) -> str:
    """LRCLIB 及其兼容接口 (地址可在设置里换)。"""
    query = urlencode({"artist_name": artist, "track_name": title,
                       "album_name": album_title})
    payload = _http_json(f"{api_base.rstrip('/')}/get?{query}")
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("syncedLyrics") or payload.get("plainLyrics") or "")


def _netease_lyric_by_id(song_id: str) -> str:
    """按歌曲 id 取网易云 lrc (带时间轴的原文歌词)。"""
    payload = _http_json(
        "https://music.163.com/api/song/lyric?"
        + urlencode({"id": song_id, "lv": 1, "kv": 1, "tv": -1}),
        referer="https://music.163.com")
    lrc = payload.get("lrc") if isinstance(payload, dict) else None
    return str(lrc.get("lyric") or "") if isinstance(lrc, dict) else ""


def _netease(_api_base: str, title: str, artist: str,
             _album_title: str) -> str:
    """网易云: 搜歌拿 id, 再取 lrc (带时间轴的原文歌词)。"""
    search = _http_json(
        "https://music.163.com/api/search/get?"
        + urlencode({"type": 1, "limit": 5}),
        data=urlencode({"s": _search_query(title, artist)}).encode(),
        referer="https://music.163.com")
    result = search.get("result") if isinstance(search, dict) else None
    listing = result.get("songs") if isinstance(result, dict) else None
    songs = ([(str(song.get("id", "")), str(song.get("name", "")),
               [str(art.get("name", "")) for art in song.get("artists", [])])
              for song in listing if isinstance(song, dict)]
             if listing else [])
    song_id = _pick_song(songs, title, artist)
    if not song_id:
        return ""
    return _netease_lyric_by_id(song_id)


def _qq_lyric_by_mid(songmid: str) -> str:
    """按 songmid 取 QQ 音乐歌词: 应答里是 base64(utf-8) 的 lrc。"""
    lyric = _http_json(
        "https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg?"
        + urlencode({"songmid": songmid, "format": "json", "g_tk": 5381}),
        referer="https://y.qq.com/")
    encoded = lyric.get("lyric") if isinstance(lyric, dict) else None
    try:
        return html.unescape(
            base64.b64decode(str(encoded or "")).decode("utf-8", "replace"))
    except (ValueError, TypeError):     # 坏 base64: 当求不到
        return ""


def _qq(_api_base: str, title: str, artist: str, _album_title: str) -> str:
    """QQ 音乐: 搜歌拿 songmid, 歌词是 base64 (utf-8) 的 lrc。"""
    payload = _http_json(
        "https://c.y.qq.com/soso/fcgi-bin/client_search_cp?"
        + urlencode({"w": _search_query(title, artist),
                     "format": "json", "p": 1, "n": 5}),
        referer="https://y.qq.com/")
    songs = []
    if isinstance(payload, dict):
        data = payload.get("data")
        song = data.get("song") if isinstance(data, dict) else None
        listing = song.get("list") if isinstance(song, dict) else None
        songs = ([(str(item.get("songmid", "")), str(item.get("songname", "")),
                   [str(art.get("name", "")) for art in item.get("singer", [])])
                  for item in listing if isinstance(item, dict)]
                 if listing else [])
    songmid = _pick_song(songs, title, artist)
    if not songmid:
        return ""
    return _qq_lyric_by_mid(songmid)


# 厂商注册表: 设置页的选择键 → 取词函数 (自定义地址只 LRCLIB 用得上)
LYRICS_PROVIDERS: Final[dict[str, Callable[..., str]]] = {
    "lrclib": _lrclib, "netease": _netease, "qq": _qq}
# 「自动」(设置存空串) 的试次序: 中文歌多的网易云/QQ 在前, 国际歌兜底 LRCLIB
_AUTO_ORDER: Final[tuple[str, ...]] = ("netease", "qq", "lrclib")


def fetch_lyrics(provider: str, api_base: str, title: str, artist: str,
                 album_title: str) -> str:
    """求一首的歌词 (优先带时间轴的); 任何失败都返回空串 (不抛, 不挡听歌)。

    provider 空串 = 自动, 按 _AUTO_ORDER 依次试到求到为止; 指定厂商只试
    那一家。"""
    keys = _AUTO_ORDER if provider.strip() in ("", "auto") else (provider,)
    for key in keys:
        fetcher = LYRICS_PROVIDERS.get(key)
        if fetcher is None:
            continue
        lyrics = fetcher(api_base, title, artist, album_title)
        if lyrics:
            return lyrics[:_MAX_LYRICS_BYTES]
    return ""
