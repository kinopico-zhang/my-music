"""播放记录查询: 记一次播放 + 本人的最近播放 + 区间排行。"""
import time
from datetime import datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from ...config import LOCAL_TZ
from ..library_database import Album, PlayEvent, PlayStat, Track
from ..schemas import RecentTrackBrief
from .browse_queries import track_brief


def record_play(session: Session, user_uuid: str, track_id: int,
                played_at: float | None = None) -> bool:
    """记一次播放, 同一事务双写: play_stats 聚合推进 (最近播放的原料)
    + play_events 落一行流水 (谁/何时/哪首, 排行的原料); 曲目不在库里
    False。played_at 是离线补报的真实播放时刻 (1.8.124): 没带用当下,
    越界 (非正 / 超当下 5 分钟) 落回当下; 补报旧账只把 play_count 加一,
    不把 last_played_at 拉回去 —— 最近播放的次序跟着真实时刻走, 不被
    晚到的旧账翻乱。"""
    if session.get(Track, track_id) is None:
        return False
    stat = session.execute(
        select(PlayStat).where(PlayStat.user_uuid == user_uuid,
                               PlayStat.track_id == track_id)
    ).scalar_one_or_none()
    now = time.time()
    when = played_at if played_at is not None and 0 < played_at <= now + 300 \
        else now
    if stat is None:
        session.add(PlayStat(user_uuid=user_uuid, track_id=track_id,
                             last_played_at=when))
    else:
        stat.last_played_at = max(stat.last_played_at, when)
        stat.play_count += 1
    session.add(PlayEvent(user_uuid=user_uuid, track_id=track_id,
                          played_at=when))
    session.commit()
    return True


def recent_plays(session: Session, user_uuid: str, limit: int = 30
                 ) -> list[RecentTrackBrief]:
    """最近播放 (本人的, 时刻倒序; 同一首只一行, 排的是最近那次)。"""
    rows = session.execute(
        select(Track, Album.title, Album.artist_id, PlayStat.play_count)
        .join(PlayStat, PlayStat.track_id == Track.id)
        .join(Album, Track.album_id == Album.id)
        .where(PlayStat.user_uuid == user_uuid)
        .order_by(PlayStat.last_played_at.desc(), PlayStat.track_id)
        .limit(limit))
    return [RecentTrackBrief(
        **track_brief(track, album_title, artist_id).model_dump(),
        play_count=play_count)
        for track, album_title, artist_id, play_count in rows]


def period_start(period: str, now: datetime | None = None) -> float:
    """排行区间的起点 (epoch 秒, 本地时区): 周 = 本周一 00:00,
    月 = 本月 1 号 00:00, 年 = 今年 1 月 1 日 00:00。"""
    now = now or datetime.now(LOCAL_TZ)
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        day -= timedelta(days=now.weekday())
    elif period == "month":
        day = day.replace(day=1)
    else:                                              # year (唯一剩余值)
        day = day.replace(month=1, day=1)
    return day.timestamp()


def top_plays(session: Session, user_uuid: str, since: float,
              limit: int = 100) -> list[RecentTrackBrief]:
    """区间排行 (本人的): since 之后播过的歌按区间内次数排 (次数相同
    最近播过的在前), 行尾带区间次数; 只看 play_events 流水, 老库已有
    的播放没流水就不算 (排行从记流水这天起算)。"""
    rows = session.execute(
        select(PlayEvent.track_id, func.count().label("plays"),
               func.max(PlayEvent.played_at).label("last"))
        .where(PlayEvent.user_uuid == user_uuid,
               PlayEvent.played_at >= since)
        .group_by(PlayEvent.track_id)
        .order_by(desc(func.count()), desc(func.max(PlayEvent.played_at)))
        .limit(limit)).all()
    if not rows:
        return []
    counts = {track_id: plays for track_id, plays, _ in rows}
    found = session.execute(
        select(Track, Album.title, Album.artist_id)
        .join(Album, Track.album_id == Album.id)
        .where(Track.id.in_(counts))).all()
    briefs = {track.id: RecentTrackBrief(
        **track_brief(track, album_title, artist_id).model_dump(),
        play_count=counts[track.id])
        for track, album_title, artist_id in found}
    return [briefs[track_id] for track_id, _, _ in rows
            if track_id in briefs]
