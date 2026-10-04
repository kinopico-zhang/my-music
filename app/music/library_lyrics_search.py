"""联网搜歌词候选 (1.8.133 调整歌词): 与 library_lyrics_api 同一批厂商,
但只列候选 (哪家 / 哪首 / 带不带时间轴), 选中哪首再按 ref 单独取词 ——
原先的 fetch_lyrics 搜索+挑最优一气呵成, 用户没得挑; 这里把挑的权交回。

搜索词是用户在调整歌词面板里敲的任意关键词 (默认预填 歌名+艺人); 三家
并搜各自截断, 顺序同 _AUTO_ORDER (网易 → QQ → LRCLIB)。设置里的厂商
选择只管自动补词的次序, 手动搜词不受限。"""
from urllib.parse import urlencode

from .schemas import LyricsCandidate
from .library_lyrics_api import _http_json, _netease_lyric_by_id, _qq_lyric_by_mid

_PER_SOURCE_LIMIT = 8      # 每家最多列几条 (三家并搜, 堆多了手机上翻不完)
_SOURCE_LABELS = {"netease": "网易云", "qq": "QQ 音乐", "lrclib": "LRCLIB"}


def source_label(source: str) -> str:
    """候选行的来源角标文案。"""
    return _SOURCE_LABELS.get(source, source)


def _netease_candidates(query: str) -> list[LyricsCandidate]:
    """网易云: 搜索接口同 _netease, 但整页候选都留下。"""
    search = _http_json(
        "https://music.163.com/api/search/get?"
        + urlencode({"type": 1, "limit": _PER_SOURCE_LIMIT}),
        data=urlencode({"s": query}).encode(),
        referer="https://music.163.com")
    result = search.get("result") if isinstance(search, dict) else None
    listing = result.get("songs") if isinstance(result, dict) else None
    return ([LyricsCandidate(source="netease", ref=str(song.get("id", "")),
                             title=str(song.get("name", "")),
                             artist="/".join(str(art.get("name", ""))
                                             for art in song.get("artists", [])))
             for song in listing if isinstance(song, dict)]
            if listing else [])


def _qq_candidates(query: str) -> list[LyricsCandidate]:
    """QQ 音乐: 搜索接口同 _qq, 但整页候选都留下。"""
    payload = _http_json(
        "https://c.y.qq.com/soso/fcgi-bin/client_search_cp?"
        + urlencode({"w": query, "format": "json", "p": 1,
                     "n": _PER_SOURCE_LIMIT}),
        referer="https://y.qq.com/")
    data = payload.get("data") if isinstance(payload, dict) else None
    song = data.get("song") if isinstance(data, dict) else None
    listing = song.get("list") if isinstance(song, dict) else None
    return [LyricsCandidate(source="qq", ref=str(item.get("songmid", "")),
                            title=str(item.get("songname", "")),
                            artist="/".join(str(art.get("name", ""))
                                            for art in item.get("singer", [])))
            for item in (listing or []) if isinstance(item, dict)]


def _lrclib_candidates(api_base: str, query: str) -> list[LyricsCandidate]:
    """LRCLIB: /search 关键词搜, 应答自带 syncedLyrics (带没带轴当场知道)。"""
    payload = _http_json(
        f"{api_base.rstrip('/')}/search?" + urlencode({"track_name": query}))
    rows = payload if isinstance(payload, list) else []
    return [LyricsCandidate(source="lrclib", ref=str(row.get("id", "")),
                            title=str(row.get("trackName", "")),
                            artist=str(row.get("artistName", "")),
                            synced=bool(row.get("syncedLyrics")))
            for row in rows[:_PER_SOURCE_LIMIT]
            if isinstance(row, dict) and not row.get("instrumental")]


def search_candidates(query: str, api_base: str) -> list[LyricsCandidate]:
    """关键词 → 三家并搜的候选 (网易 → QQ → LRCLIB, 各自截断)。"""
    query = query.strip()
    if not query:
        return []
    return (_netease_candidates(query) + _qq_candidates(query)
            + _lrclib_candidates(api_base, query))


def candidate_lyrics(source: str, ref: str, api_base: str) -> str:
    """按选中候选取词 (优先带时间轴的); 任何失败回空串。"""
    if source == "netease":
        return _netease_lyric_by_id(ref)
    if source == "qq":
        return _qq_lyric_by_mid(ref)
    if source == "lrclib":
        payload = _http_json(f"{api_base.rstrip('/')}/get/{ref}")
        if not isinstance(payload, dict):
            return ""
        return str(payload.get("syncedLyrics") or payload.get("plainLyrics")
                   or "")
    return ""
