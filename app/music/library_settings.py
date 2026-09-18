"""运行时设置 (曲库路径 / 歌词 API)。

设置恒单行 id=1, 空字段回落 env 默认; 改曲库路径由服务层
(service.apply_music_directory) 换扫描根目录并起全量重扫, 这里只管
存取与校验。(1.8.17 蜂窝流量月账撤了 —— 设置页改版, 没了消费方。)
"""
from pathlib import Path

from sqlalchemy.orm import Session

from .library_database import DEFAULT_MUSIC_DIRECTORY, MusicSetting
from .schemas import MusicSettingsState

# 歌词 API 的默认地址 (LRCLIB: 免费, 兼容 /get?artist_name=…&track_name=…)
LYRICS_API_DEFAULT = "https://lrclib.net/api"


def settings_row(session: Session) -> MusicSetting:
    """取设置行 (没有就建, 恒单行 id=1)。"""
    row = session.get(MusicSetting, 1)
    if row is None:
        row = MusicSetting(id=1)
        session.add(row)
        session.commit()
    return row


def effective_music_directory(session: Session) -> Path:
    """曲库根目录现值: 设置行 > env 默认。"""
    configured = settings_row(session).music_directory.strip()
    return Path(configured or DEFAULT_MUSIC_DIRECTORY)


def effective_lyrics_api(session: Session) -> tuple[bool, str]:
    """歌词 API 现值: (开不开, 地址); 地址空 = 默认 LRCLIB。"""
    row = settings_row(session)
    return (row.lyrics_api_enabled,
            row.lyrics_api_base.strip() or LYRICS_API_DEFAULT)


def settings_state(session: Session) -> MusicSettingsState:
    """设置页状态 (现值 + 默认值参照)。"""
    row = settings_row(session)
    return MusicSettingsState(
        music_directory=row.music_directory,
        music_directory_default=DEFAULT_MUSIC_DIRECTORY,
        lyrics_api_enabled=row.lyrics_api_enabled,
        lyrics_api_base=row.lyrics_api_base,
        lyrics_api_default=LYRICS_API_DEFAULT)


def save_settings(session: Session, music_directory: str | None,
                  lyrics_api_enabled: bool | None,
                  lyrics_api_base: str | None) -> Path | None:
    """保存设置 (None 字段不动); 返回新生效的曲库目录 (路径没变才为 None)。

    曲库路径要求目录真的存在 (连不上的路径扫不了); 歌词 API 地址要带协议头。"""
    row = settings_row(session)
    if lyrics_api_base is not None:
        cleaned = lyrics_api_base.strip()
        if cleaned and not cleaned.startswith(("http://", "https://")):
            raise ValueError(f"歌词 API 地址要以 http:// 或 https:// 开头: {cleaned}")
        row.lyrics_api_base = cleaned
    if lyrics_api_enabled is not None:
        row.lyrics_api_enabled = lyrics_api_enabled
    new_directory: Path | None = None
    if music_directory is not None:
        cleaned = music_directory.strip()
        if cleaned != row.music_directory:
            if cleaned and not Path(cleaned).is_dir():
                raise ValueError(f"曲库目录不存在: {cleaned}")
            row.music_directory = cleaned
            new_directory = effective_music_directory(session)
    session.commit()
    return new_directory
