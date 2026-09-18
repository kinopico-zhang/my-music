"""播放列表成员管理: 建列 / 改名 / 加歌 / 移歌 / 整表重排 / 删列
(2026-09-15 起应用内自建自管, 不再从 Plex 同步)。

每次编辑 (建 / 改名 / 加歌 / 移歌 / 重排) 都记 updated_at (epoch 秒):
「添加到播放列表」选择单按它排, 最近编辑的在最前 (1.8.17 用户点名)。
自定义封面拆去了 library_playlist_covers (按域分家)。
"""
import time

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from .library_database import Playlist, PlaylistItem, Track
from .schemas import PlaylistBrief


def create_playlist(session: Session, name: str) -> PlaylistBrief:
    """新建空的播放列表 (position=0: 新建的排在已有列表前面)。

    名字撞车报 ValueError, 由路由层转 409。"""
    playlist = Playlist(name=_clean_name(session, None, name), position=0,
                        plex_playlist_id=0, is_local=True,
                        updated_at=time.time())
    session.add(playlist)
    session.commit()
    return playlist_brief(playlist)


def require_playlist(session: Session, playlist_id: int) -> Playlist:
    """取列表; 不在库 KeyError (路由层转 404)。covers 也用, 别再手抄。"""
    playlist = session.get(Playlist, playlist_id)
    if playlist is None:
        raise KeyError(playlist_id)
    return playlist


def commit_playlist_edit(session: Session, playlist: Playlist) -> PlaylistBrief:
    """记一笔编辑时刻 (updated_at, 选择单按它排) 落库, 回列表行形状。"""
    playlist.updated_at = time.time()
    session.commit()
    return playlist_brief(playlist)


def rename_playlist(session: Session, playlist_id: int,
                    name: str) -> PlaylistBrief:
    """改列表名 (1.8.17 用户点名「允许编辑播放列表的标题」)。

    校验与建列表同一套 (_clean_name); 列表不在库 KeyError → 404。"""
    playlist = require_playlist(session, playlist_id)
    playlist.name = _clean_name(session, playlist_id, name)
    return commit_playlist_edit(session, playlist)


def _clean_name(session: Session, playlist_id: int | None,
                name: str) -> str:
    """列表名收边 + 非空 + 不撞名 (撞别人的报 ValueError; playlist_id
    给 None = 建列表, 否则改名时要把自己排除在撞名检查外)。"""
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("播放列表的名字不能是空的")
    query = select(Playlist).where(Playlist.name == cleaned)
    if playlist_id is not None:
        query = query.where(Playlist.id != playlist_id)
    if session.scalar(query) is not None:
        raise ValueError("已经有叫这个名字的播放列表了")
    return cleaned


def add_track_to_playlist(session: Session, playlist_id: int,
                          track_id: int) -> PlaylistBrief:
    """往列表末尾加一首; 已经在列表里的不再加 (同一首只留一份 ——
    重复行会让两行一起亮播放态、连播两遍, 2026-09-15 用户点名)。

    已在列表里报 ValueError, 由路由层转 409。"""
    playlist = require_playlist(session, playlist_id)
    if session.get(Track, track_id) is None:
        raise KeyError(track_id)
    already = session.scalar(select(PlaylistItem.id).where(
        PlaylistItem.playlist_id == playlist_id,
        PlaylistItem.track_id == track_id))
    if already is not None:
        raise ValueError("这首歌已经在列表里了")
    next_position = (session.scalar(select(func.max(PlaylistItem.position))
                                    .where(PlaylistItem.playlist_id
                                           == playlist_id)) or 0) + 1
    session.add(PlaylistItem(playlist_id=playlist_id, track_id=track_id,
                             position=next_position, added_locally=True))
    playlist.track_count += 1
    playlist.updated_at = time.time()
    session.commit()
    _refresh_playlist_aggregates(session)
    session.expire(playlist, ["track_count", "duration_seconds"])
    return playlist_brief(playlist)   # 聚合 SQL 刚更新过, 定向失效取库里的新值


def remove_track_from_playlist(session: Session, playlist_id: int,
                               track_id: int) -> PlaylistBrief:
    """从列表里移出一首 (左滑删除); 列表里没有这首 KeyError → 404。

    position 留洞不补 (查询按 ORDER BY position, 顺序不受影响);
    重排 (reorder_playlist_tracks) 会顺手把洞补平。"""
    playlist = require_playlist(session, playlist_id)
    item = session.scalar(select(PlaylistItem).where(
        PlaylistItem.playlist_id == playlist_id,
        PlaylistItem.track_id == track_id))
    if item is None:
        raise KeyError(track_id)
    session.delete(item)
    playlist.updated_at = time.time()
    session.commit()
    _refresh_playlist_aggregates(session)
    session.expire(playlist, ["track_count", "duration_seconds"])
    return playlist_brief(playlist)


def reorder_playlist_tracks(session: Session, playlist_id: int,
                            track_ids: list[int]) -> PlaylistBrief:
    """整表重排 (1.8.17 用户点名「允许调整列表歌曲的顺序」): 请求体给
    全量曲目 id 的新顺序, 服务端照单重写 position —— 越界/重复/混进
    非成员的一律 ValueError → 409 (客户端列表过期了, 重拉详情再说);
    列表不在库 KeyError → 404。顺手把 position 的洞补平 (1..N 连号)。"""
    playlist = require_playlist(session, playlist_id)
    items = session.scalars(select(PlaylistItem).where(
        PlaylistItem.playlist_id == playlist_id)).all()
    by_track = {item.track_id: item for item in items}
    if (len(track_ids) != len(by_track) or len(set(track_ids)) != len(track_ids)
            or any(track_id not in by_track for track_id in track_ids)):
        raise ValueError("列表内容对不上, 刷新后再试")
    for position, track_id in enumerate(track_ids, start=1):
        by_track[track_id].position = position
    return commit_playlist_edit(session, playlist)


def delete_playlist(session: Session, playlist_id: int) -> None:
    """删掉播放列表 (连成员一起); 封面文件由路由层清场
    (library_playlist_covers.purge_playlist_cover)。"""
    playlist = require_playlist(session, playlist_id)
    session.execute(
        delete(PlaylistItem).where(PlaylistItem.playlist_id == playlist_id))
    session.delete(playlist)
    session.commit()


def playlist_brief(playlist: Playlist) -> PlaylistBrief:
    """列表行/卡片的数据形状 (queries / shares / covers 也用它, 别再手抄这份构造)。"""
    return PlaylistBrief(playlist_id=playlist.id, name=playlist.name,
                         track_count=playlist.track_count,
                         duration_seconds=playlist.duration_seconds,
                         is_local=playlist.is_local,
                         cover_version=playlist.cover_version,
                         updated_at=playlist.updated_at)


def _refresh_playlist_aggregates(session: Session) -> None:
    """列表 计数/总时长 重算 (成员曲目聚合, 与专辑汇总同一套相关子查询写法)。"""
    session.execute(update(Playlist).values(
        track_count=select(func.count()).where(
            PlaylistItem.playlist_id == Playlist.id).scalar_subquery(),
        duration_seconds=select(func.coalesce(
            func.sum(Track.duration_seconds), 0.0)).where(
            PlaylistItem.playlist_id == Playlist.id,
            PlaylistItem.track_id == Track.id).scalar_subquery()))
    session.commit()
