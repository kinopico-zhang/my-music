"""歌词与来源查询: 单曲歌词 (可联网补) + 作词/作曲标签 + 音质参数 (现读文件)。"""
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..library_database import Album, Track, music_directory
from ..library_lyrics_api import fetch_lyrics
from ..library_tags import (looks_like_synced_lyrics, read_audio_quality,
                            read_track_credits)
from ..schemas import AudioQuality, LyricsResponse, TrackCredits

# 求而不得的负缓存: track_id → 上次外网尝试的时刻。换曲预取 (歌词键置灰)
# 会频繁问没词的曲子, 不拦着就每换一曲打一次外网 (自动模式一miss三四发)。
_lyrics_fetch_misses: dict[int, float] = {}
_LYRICS_MISS_TTL = 24 * 3600


def lyrics_for_track(session: Session, track_id: int,
                     lyrics_api: tuple[bool, str, str] | None = None
                     ) -> LyricsResponse | None:
    """单曲歌词原文 (前端解析时间轴)。

    库里没有且给了歌词取词配置时, 联网求一遍并写回索引 —— 下次离线也有,
    搜索歌词也搜得到; 求不到保持空 (24 小时内不再为同一首打外网)。"""
    track = session.get(Track, track_id)
    if track is None:
        return None
    if not track.lyrics and lyrics_api and lyrics_api[0]:
        # 没求过的 (账上无记录) 立刻放行: monotonic 从开机起算, 若拿默认 0.0
        # 当"上次错过时刻", 开机不满 24 小时的机器 (CI 全新runner / 刚重启的
        # NAS) 会把首求也当"24小时内刚错过"挡掉, 联网补歌词静默失效
        last_miss = _lyrics_fetch_misses.get(track.id)
        if last_miss is None or time.monotonic() - last_miss > _LYRICS_MISS_TTL:
            album_title = session.scalar(
                select(Album.title).where(Album.id == track.album_id)) or ""
            fetched = fetch_lyrics(lyrics_api[1], lyrics_api[2],
                                   track.title, track.artist, album_title)
            if fetched:
                track.lyrics = fetched
                track.lyrics_synced = looks_like_synced_lyrics(fetched)
                session.commit()
                _lyrics_fetch_misses.pop(track.id, None)
            else:
                _lyrics_fetch_misses[track.id] = time.monotonic()
    return LyricsResponse(track_id=track.id, lyrics=track.lyrics,
                          lyrics_synced=track.lyrics_synced)


def credits_for_track(session: Session, track_id: int) -> TrackCredits | None:
    """单曲 作词/作曲 标签 (现读文件, 只有部分歌带; 没标签 = 空串)。"""
    track = session.get(Track, track_id)
    if track is None:
        return None
    lyricist, composer = read_track_credits(
        music_directory() / track.file_path)
    return TrackCredits(lyricist=lyricist, composer=composer)


def audio_quality_for_track(session: Session, track_id: int) -> AudioQuality | None:
    """单曲音质参数 (播放页封面下那行, 1.8.127)。

    索引里有 (扫描顺手入库) 直接用; 老行是 0 (1.8.127 前扫的, 增量重扫
    对没变的文件不读标签) 就现读文件回填 —— 每首最多读一次, 之后走库。
    读不出 (文件没了/格式不认识) 保持 0 不落库, 前端藏行。"""
    track = session.get(Track, track_id)
    if track is None:
        return None
    if not track.sample_rate:
        quality = read_audio_quality(music_directory() / track.file_path)
        if quality is not None:
            track.sample_rate, track.bit_depth, track.channels = quality
            session.commit()
    bitrate = (round(track.file_size * 8 / track.duration_seconds / 1000)
               if track.duration_seconds > 0 and track.file_size > 0 else 0)
    return AudioQuality(file_format=track.file_format,
                        sample_rate=track.sample_rate,
                        bit_depth=track.bit_depth, channels=track.channels,
                        bitrate=bitrate)
