"""播放列表查询: 清单与详情 (有序曲目; 写操作在 library_playlists)。"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..library_database import (Album, PlayStat, Playlist, PlaylistItem,
                                Track)
from ..library_playlists import playlist_brief
from ..schemas import (PlaylistBrief, PlaylistPage, PlaylistPageList)
from .browse_queries import track_brief


def list_playlists(session: Session) -> PlaylistPageList:
    """播放列表清单 (按同步顺序, 不分页 —— 就十几个)。行模型带 updated_at
    (1.8.17: 选择单按最后编辑排, 主页一段仍按这里的顺序)。"""
    playlists = [playlist_brief(playlist) for playlist in session.execute(
        select(Playlist).order_by(Playlist.position, Playlist.id)).scalars()]
    return PlaylistPageList(playlists=playlists)


def recent_playlists(session: Session, user_uuid: str,
                     limit: int = 10) -> list[PlaylistBrief]:
    """最近播放的播放列表 (1.8.24 主页一段): 按最近用过排 —— 播过旗下曲目
    的看最近那次播放, 没播过的看最后编辑时刻 (刚建/刚改的也在前头)。
    播放按曲目记 (PlayStat, 按人), 列表不单记账: 一首歌进了几个列表,
    几个列表都算最近播过 —— 不加新表, 老播放史直接归位。"""
    played = (
        select(PlaylistItem.playlist_id.label("playlist_id"),
               func.max(PlayStat.last_played_at).label("last_play"))
        .join(PlayStat, PlayStat.track_id == PlaylistItem.track_id)
        .where(PlayStat.user_uuid == user_uuid)
        .group_by(PlaylistItem.playlist_id).subquery())
    recency = func.coalesce(played.c.last_play, Playlist.updated_at)
    playlists = session.execute(
        select(Playlist)
        .outerjoin(played, played.c.playlist_id == Playlist.id)
        .order_by(recency.desc(), Playlist.id)
        .limit(limit)).scalars().all()
    return [playlist_brief(playlist) for playlist in playlists]


def playlist_page(session: Session, playlist_id: int) -> PlaylistPage | None:
    """播放列表详情: 卡片 + 成员曲目 (按列表内顺序)。"""
    playlist = session.get(Playlist, playlist_id)
    if playlist is None:
        return None
    tracks = [track_brief(track, album_title, artist_id)
              for track, album_title, artist_id in session.execute(
                  select(Track, Album.title, Album.artist_id)
                  .join(PlaylistItem, PlaylistItem.track_id == Track.id)
                  .join(Album, Track.album_id == Album.id)
                  .where(PlaylistItem.playlist_id == playlist_id)
                  .order_by(PlaylistItem.position, PlaylistItem.id))]
    return PlaylistPage(playlist=playlist_brief(playlist), tracks=tracks)
