"""My Music 播放流水 + 播放排行测试 (1.8.31 用户点名「每次播放, 你都要在
后台记录谁, 什么时候, 播放了哪首歌」): 聚合计数 (PlayStat) 与一次一行的
流水 (PlayEvent) 双轨, 区间排行 (本周/本月/今年), 账号隔离。
拆自 test_music_endpoints.py (文件超 200 行按域再拆)。"""
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as m
from app import account_store, config
from app.music.library_database import PlayEvent, PlayStat, session_factory
from app.music import library_queries
from tests.music_library_helpers import _seed_library


def test_record_play_counts_and_dedups():
    """查询层: user+track 一行, 重播只加次数; 曲目不在库里不记。
    播一次同时落一行 play_events 流水 (谁/何时/哪首, 排行的原料)。"""
    _seed_library()
    with session_factory()() as session:
        assert library_queries.record_play(session, "u-1", 1) is True
        time.sleep(0.002)
        assert library_queries.record_play(session, "u-1", 2) is True
        time.sleep(0.002)
        assert library_queries.record_play(session, "u-1", 1) is True   # 重播
        assert library_queries.record_play(session, "u-1", 999) is False
        stat = session.execute(select(PlayStat)).scalars().all()
        assert [(s.track_id, s.play_count) for s in stat] == [
            (1, 2), (2, 1)]                    # 聚合行: 重播只加次数
        events = session.execute(
            select(PlayEvent).order_by(PlayEvent.id)).scalars().all()
        assert [(e.user_uuid, e.track_id) for e in events] == [
            ("u-1", 1), ("u-1", 2), ("u-1", 1)]        # 流水: 播几次记几行
        assert events[2].played_at > events[0].played_at  # 时刻跟着播放走
        assert [t.title for t in
                library_queries.recent_plays(session, "u-1")] == ["曲A", "曲B"]
        assert library_queries.recent_plays(session, "u-1")[0].play_count == 2
        assert library_queries.recent_plays(session, "别人") == []


def test_period_start_boundaries():
    """区间起点 (本地时区): 周 = 本周一 00:00, 月 = 本月 1 号, 年 = 元旦;
    周一当天不退到上周。"""
    tz = ZoneInfo("Asia/Shanghai")
    sat = datetime(2026, 9, 19, 15, 30, tzinfo=tz)      # 2026-09-19 是周六
    assert library_queries.period_start("week", sat) == datetime(
        2026, 9, 14, tzinfo=tz).timestamp()             # 周一 00:00
    assert library_queries.period_start("month", sat) == datetime(
        2026, 9, 1, tzinfo=tz).timestamp()
    assert library_queries.period_start("year", sat) == datetime(
        2026, 1, 1, tzinfo=tz).timestamp()
    mon = datetime(2026, 9, 14, 0, 0, tzinfo=tz)       # 周一本身
    assert library_queries.period_start("week", mon) == mon.timestamp()
    # 换环境时区也不漂 (起点的"本地"由 LOCAL_TZ 定, 测试环境默认上海)
    assert library_queries.period_start("week", sat) == datetime(
        2026, 9, 14, tzinfo=config.LOCAL_TZ).timestamp()


def test_top_plays_query_ordering():
    """查询层: 区间内按次数排, 同次数最近播过的在前; 区间外的流水不算,
    账号之间互不可见。"""
    _seed_library()
    now = time.time()
    with session_factory()() as session:
        for track_id, played_ats in ((1, (now - 500, now - 400, now - 300)),
                                     (2, (now - 500, now - 100, now - 50)),
                                     (4, (now - 450,))):
            for played_at in played_ats:
                session.add(PlayEvent(user_uuid="u-1", track_id=track_id,
                                      played_at=played_at))
        session.add(PlayEvent(user_uuid="u-1", track_id=5,
                              played_at=now - 10_000_000))   # 久远: 区间外
        session.add(PlayEvent(user_uuid="别人", track_id=1, played_at=now))
        session.commit()
        top = library_queries.top_plays(session, "u-1", since=now - 600)
        assert [(t.title, t.play_count) for t in top] == [
            ("曲B", 3), ("曲A", 3), ("曲C", 1)]   # 同数, 曲B 最近播过在前
        assert library_queries.top_plays(session, "u-1", since=now) == []
        assert [(t.title, t.play_count) for t in library_queries.top_plays(
            session, "别人", since=now - 600)] == [("曲A", 1)]


def test_play_record_endpoints_per_user(auth, usersdb):
    """播放记录接口: 重播把曲子顶回最前, 账号之间互不可见, 没登录 401。"""
    _seed_library()
    anon = TestClient(m.app)
    assert anon.post("/music/api/plays",
                     json={"track_id": 1}).status_code == 401
    assert anon.get("/music/api/plays/recent").status_code == 401

    assert auth.post("/music/api/plays", json={"track_id": 1}).status_code == 200
    time.sleep(0.002)
    assert auth.post("/music/api/plays", json={"track_id": 2}).status_code == 200
    time.sleep(0.002)
    assert auth.post("/music/api/plays", json={"track_id": 1}).status_code == 200
    assert auth.post("/music/api/plays",
                     json={"track_id": 9999}).status_code == 404
    recent = auth.get("/music/api/plays/recent").json()["tracks"]
    assert [t["title"] for t in recent] == ["曲A", "曲B"]   # 最近那次排前
    assert recent[0]["album_title"] == "甲"
    assert recent[0]["play_count"] == 2                # 1.8.1: 播过几次跟着行走
    assert recent[1]["play_count"] == 1

    # 另一个账号: 各记各的, 看不见管理员的记录
    account_store.create_user(usersdb, "试听乙", "password123")
    yi = TestClient(m.app)
    assert yi.post("/api/login",
                   json={"user": "试听乙", "password": "password123"}
                   ).status_code == 200
    assert yi.get("/music/api/plays/recent").json()["tracks"] == []
    assert yi.post("/music/api/plays", json={"track_id": 3}).status_code == 200
    assert [t["title"] for t in
            yi.get("/music/api/plays/recent").json()["tracks"]] == ["Hello"]
    assert [t["title"] for t in
            auth.get("/music/api/plays/recent").json()["tracks"]] == ["曲A", "曲B"]


def test_play_top_endpoint(auth):
    """排行接口: 默认/三个区间同答, 按区间内次数排; 久远的流水不进榜,
    period 乱写 422, 没登录 401。"""
    _seed_library()
    anon = TestClient(m.app)
    assert anon.get("/music/api/plays/top").status_code == 401
    assert auth.get("/music/api/plays/top",
                    params={"period": "乱写"}).status_code == 422

    assert auth.post("/music/api/plays", json={"track_id": 1}).status_code == 200
    time.sleep(0.002)
    assert auth.post("/music/api/plays", json={"track_id": 2}).status_code == 200
    time.sleep(0.002)
    assert auth.post("/music/api/plays", json={"track_id": 1}).status_code == 200
    with session_factory()() as session:             # 直接插一行远古流水
        user_uuid = session.execute(
            select(PlayEvent.user_uuid)).scalars().first()
        session.add(PlayEvent(user_uuid=user_uuid, track_id=4,
                              played_at=1.0))
        session.commit()
    for period in ("week", "month", "year"):
        data = auth.get("/music/api/plays/top",
                        params={"period": period}).json()
        assert data["period"] == period
        assert [(t["title"], t["play_count"]) for t in data["tracks"]] == [
            ("曲A", 2), ("曲B", 1)]              # 曲C 的远古流水不进榜
        assert data["tracks"][0]["album_title"] == "甲"
    assert auth.get("/music/api/plays/top").json()["period"] == "week"  # 默认周
