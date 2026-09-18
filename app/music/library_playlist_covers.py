"""播放列表自定义封面: 原图直存库文件旁的缓存目录 (playlist-{id}.jpg/png/webp),
库里只记版本号, 换图加一, URL 带 ?v={版本} 长缓存。

2026-09-18 从 library_playlists 拆出 (那边加了改名/重排后超 200 行):
按域分家 —— 这边只管封面资产, 列表成员的建/加/移/改名/重排在 library_playlists。
"""

from sqlalchemy.orm import Session

from .library_database import artwork_cache_directory
from .library_media import playlist_cover_file
from .library_playlists import commit_playlist_edit, require_playlist
from .schemas import PlaylistBrief

_MAX_COVER_BYTES = 10 * 1024 * 1024      # 封面上限 10 MB (手机照片直传够用)


def _sniff_image_extension(data: bytes) -> str | None:
    """字节流魔数 → 扩展名 (认不出返回 None; 文件名/头都不算数, 只信内容)。"""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    return None


def set_playlist_cover(session: Session, playlist_id: int, data: bytes,
                       content_type: str) -> PlaylistBrief:
    """换自定义封面 (内容按魔数认类型, 原图直存; 版本号 +1)。

    列表不在库 KeyError; 不是图片/太大/类型不对 ValueError (路由层转 404/400)。"""
    playlist = require_playlist(session, playlist_id)
    if not (content_type or "").lower().startswith("image/"):
        raise ValueError("封面要传图片文件 (JPG / PNG / WebP)")
    if len(data) > _MAX_COVER_BYTES:
        raise ValueError("封面太大了 (上限 10 MB)")
    extension = _sniff_image_extension(data)
    if extension is None:
        raise ValueError("认不出这张图 (只收 JPG / PNG / WebP)")
    path = artwork_cache_directory() / f"playlist-{playlist_id}{extension}"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = playlist_cover_file(playlist_id)
    if existing is not None and existing != path:
        existing.unlink()          # 旧扩展名的文件别留着 (png 换成 jpg 之类)
    temporary_path = path.with_suffix(".tmp")
    temporary_path.write_bytes(data)
    temporary_path.replace(path)
    playlist.cover_version = max(1, playlist.cover_version + 1)
    # 换封面也是编辑 (updated_at 是选择单的排序原料, 1.8.17)
    return commit_playlist_edit(session, playlist)


def clear_playlist_cover(session: Session, playlist_id: int) -> PlaylistBrief:
    """撤掉自定义封面 (回渐变音符块); 文件删不干净也不挡 (版本已归零)。"""
    playlist = require_playlist(session, playlist_id)
    _unlink_cover(playlist_id)
    playlist.cover_version = 0
    return commit_playlist_edit(session, playlist)


def _unlink_cover(playlist_id: int) -> None:
    """封面文件尽力删 (删不掉就算了, 版本号不再引用它)。"""
    cover = playlist_cover_file(playlist_id)
    if cover is not None:
        try:
            cover.unlink()
        except OSError:
            pass


def purge_playlist_cover(playlist_id: int) -> None:
    """删列表时的清场: 封面文件跟着走 (库里的行归 library_playlists 删)。"""
    _unlink_cover(playlist_id)
