"""单艺人重扫的采集与落库 (艺人页「刷新元数据」按钮, 1.8.75)。

与整库扫描 (scanner + scanner_index_writer) 同一套收录/写入规则, 两头收窄:
采集只走这一个艺人目录; 落库前先抹这棵子树的汇总级字段 (名字/标题/年份
—— 整库扫描只在空时填, 不抹的话改过的标签永远进不来), 重填重写后,
消失曲目/空行/汇总/检索键的清理都只碰这棵子树, 别的艺人一行不动。
"""
from pathlib import Path

from sqlalchemy import delete, exists, func, select
from sqlalchemy.orm import Session, sessionmaker

from ..library_database import (AUDIO_EXTENSION_FORMATS, POSTER_FILE_NAMES,
                                Album, Artist, Track)
from ..library_search_keys import search_keys
from ..library_tags import album_title_from_directory
from ..schemas import ScannedTrack
from .scanner_index_writer import (ensure_albums, ensure_artists,
                                   existing_track_ids,
                                   refresh_album_aggregates, upsert_track)

_BATCH_SIZE = 500             # 分批提交/删除, 与整库落库同一批大小


def collect_artist_files(music_directory: Path, directory: str
                         ) -> tuple[list[tuple[str, int, float]], str]:
    """走单个艺人目录 → (音频文件 [(相对路径, 大小, mtime)], 海报文件名)。

    收录规则同全库 walk (隐藏文件不收, 海报只在艺人目录这层找);
    目录整个没了就都空 —— 落库按「消失」清干净这棵子树。"""
    candidates: list[tuple[str, int, float]] = []
    poster = ""
    root = music_directory / directory
    if not root.is_dir():
        return candidates, poster
    for subdirectory, subdirectories, file_names in root.walk():
        subdirectories[:] = sorted(
            name for name in subdirectories if not name.startswith("."))
        relative = subdirectory.relative_to(root).as_posix()
        for file_name in sorted(file_names):
            if file_name.startswith("."):
                continue
            if relative == "." and file_name.lower() in POSTER_FILE_NAMES:
                poster = file_name
            if (subdirectory / file_name).suffix.lower() \
                    not in AUDIO_EXTENSION_FORMATS:
                continue
            try:
                stat = (subdirectory / file_name).stat()
            except OSError:
                continue        # 扫描瞬间被删/坏链接: 跳过
            relative_path = (f"{directory}/{file_name}" if relative == "."
                             else f"{directory}/{relative}/{file_name}")
            candidates.append(
                (relative_path, stat.st_size, stat.st_mtime))
    return candidates, poster


def refresh_artist_index(database_sessions: sessionmaker[Session],
                         artist_directory: str, scanned: list[ScannedTrack],
                         live_paths: set[str], poster_file: str) -> None:
    """重扫单个艺人落库: 抹汇总字段 → 按新标签重填重写 (同一个事务, 抹掉的
    名字不会单独被读到) → 清这棵子树里消失的曲目 → 收尾只收这棵子树。"""
    with database_sessions() as session:
        _blank_artist_fields(session, artist_directory)
        artist_ids = ensure_artists(session, scanned)
        album_ids = ensure_albums(session, scanned, artist_ids)
        stored = existing_track_ids(session, scanned)
        for index, track in enumerate(scanned, start=1):
            upsert_track(session, track, album_ids, stored)
            if index % _BATCH_SIZE == 0:
                session.commit()
        session.commit()
    remove_vanished_artist_tracks(database_sessions, artist_directory,
                                  live_paths)
    finalize_artist_index(database_sessions, artist_directory, poster_file)


def _blank_artist_fields(session: Session, artist_directory: str) -> None:
    """抹掉这棵子树的汇总级字段 (名字/排序名/标题/年份), 后面的 ensure 按
    新标签重填 —— 重扫按钮的意义就是「以现在盘上的标签为准」。"""
    artist = session.execute(select(Artist).where(
        Artist.directory == artist_directory)).scalar_one_or_none()
    if artist is not None:
        artist.name = ""
        artist.sort_name = ""
    for album in session.execute(select(Album).join(
            Artist, Album.artist_id == Artist.id).where(
            Artist.directory == artist_directory)).scalars():
        album.title = ""
        album.year = 0


def remove_vanished_artist_tracks(database_sessions: sessionmaker[Session],
                                  artist_directory: str,
                                  live_paths: set[str]) -> int:
    """这棵子树里磁盘上没了的曲目行删掉; 返回删了几行。

    整库版 remove_vanished_tracks 拿全库对账 (live_paths 只给一棵子树会
    把别的艺人全删了), 这里按艺人目录前缀收窄到这棵子树。"""
    with database_sessions() as session:
        stored = {row[0] for row in session.execute(
            select(Track.file_path).where(
                Track.file_path.startswith(f"{artist_directory}/")))}
        vanished = sorted(stored - live_paths)
        for start in range(0, len(vanished), _BATCH_SIZE):
            session.execute(delete(Track).where(Track.file_path.in_(
                vanished[start:start + _BATCH_SIZE])))
        session.commit()
    return len(vanished)


def finalize_artist_index(database_sessions: sessionmaker[Session],
                          artist_directory: str, poster_file: str) -> None:
    """这棵子树的收尾 (整库 finalize_library 收窄到单艺人): 记海报 → 清空
    专辑/空艺人 → 重算旗下专辑汇总 → 目录名兜底 + 检索键。"""
    with database_sessions() as session:
        artist = session.execute(select(Artist).where(
            Artist.directory == artist_directory)).scalar_one_or_none()
        if artist is None:
            return
        session.execute(delete(Album).where(
            Album.artist_id == artist.id,
            ~exists(select(Track.id).where(Track.album_id == Album.id))))
        # 旗下专辑清空后一个不剩 (目录整个没了): 艺人行跟着清掉
        if not session.scalar(select(func.count()).select_from(Album).where(
                Album.artist_id == artist.id)):
            session.delete(artist)
            session.commit()
            return
        artist.poster_file = poster_file
        refresh_album_aggregates(session, artist.id)
        if not artist.name:
            artist.name = artist.directory
        artist_name = artist.name or artist.directory
        for album in session.execute(select(Album).where(
                Album.artist_id == artist.id)).scalars():
            if not album.title:
                album.title = album_title_from_directory(
                    album.directory.split("/")[-1])
            album.search_keys = search_keys(album.title, artist_name)
        artist.search_keys = search_keys(artist.name, artist.sort_name,
                                         artist.directory)
        session.commit()
