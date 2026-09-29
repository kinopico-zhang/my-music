"""My Music 播放计数离线补报测试 (1.8.124, 起因用户问「你的播放排行,
数据有丢失过吗」—— 查库无零日, 但断网/服务重启/5xx 窗口里的播放原本
发后不管, 无据可查地丢): 服务端 record_play 收可选 played_at (补报的
真实播放时刻, 越界落回当下; last_played_at 不被晚到的旧账拉回去) +
前端补报队列接线 (play-outbox.js, 队列逻辑另有 node 直测)。"""
import time

from sqlalchemy import select

from app.music.library_database import PlayEvent, PlayStat, session_factory
from app.music import library_queries
from tests.music_static_files import MUSIC_STATIC, music_page_shell
from tests.music_library_helpers import _seed_library


def test_record_play_backfilled_played_at():
    """查询层: 补报带真实时刻 —— play_events 落真实时刻 (排行按它落
    区间, 不按补报时刻); 补报旧账只把 play_count 加一, 不把
    last_played_at 拉回去 (最近播放的次序不被晚到的旧账翻乱);
    越界 (非正 / 超当下 5 分钟) 落回当下。"""
    _seed_library()
    with session_factory()() as session:
        old = time.time() - 86400            # 昨天离线听的一笔
        recent = time.time()
        assert library_queries.record_play(session, "u-1", 1, old) is True
        assert library_queries.record_play(session, "u-1", 1, recent) is True
        # 晚到的旧账 (昨天那笔现在才补报): 次数照加, 最近播放不回退
        assert library_queries.record_play(session, "u-1", 1, old + 60) is True
        stat = session.execute(select(PlayStat)).scalar_one()
        assert stat.play_count == 3
        assert stat.last_played_at >= recent - 1     # 没被旧账拉回去
        events = session.execute(select(PlayEvent).order_by(PlayEvent.id)
                                 ).scalars().all()
        assert [e.played_at for e in events] == [old, recent, old + 60]
        # 越界: 非正 / 远未来 → 都记成当下 (时钟歪了的客户端不产生
        # 远古/未来流水)
        floor = time.time()
        assert library_queries.record_play(session, "u-1", 1, 0) is True
        assert library_queries.record_play(session, "u-1", 1, -5) is True
        assert library_queries.record_play(session, "u-1", 1,
                                           floor + 9999) is True
        clamped = session.execute(select(PlayEvent.played_at)
                                  .order_by(PlayEvent.id)
                                  ).scalars().all()[-3:]
        assert all(floor <= t <= time.time() + 1 for t in clamped)
        # 曲目不在库里照旧 False (带不带 played_at 都一样)
        assert library_queries.record_play(session, "u-1", 999, old) is False


def test_play_endpoint_accepts_played_at(auth):
    """接口: 带不带 played_at 都 200 (旧客户端不带照旧); 带的时刻原样
    落流水 —— 排行区间按真实播放时刻算: 昨天补报的那笔不进「最近一
    小时」榜, 刚播的进。"""
    _seed_library()
    yesterday = int(time.time() - 86400)
    assert auth.post("/music/api/plays",
                     json={"track_id": 1}).status_code == 200
    assert auth.post("/music/api/plays",
                     json={"track_id": 2, "played_at": yesterday}
                     ).status_code == 200
    assert auth.post("/music/api/plays",
                     json={"track_id": 9999, "played_at": yesterday}
                     ).status_code == 404
    with session_factory()() as session:
        times = session.execute(select(PlayEvent.track_id, PlayEvent.played_at)
                                ).all()
        assert dict(times)[2] == yesterday        # 真实时刻原样落流水
        user_uuid = session.execute(
            select(PlayEvent.user_uuid)).scalars().first()
        top = library_queries.top_plays(session, user_uuid,
                                       since=time.time() - 3600)
    assert [t.title for t in top] == ["曲A"]      # 昨天那笔不进近一小时榜


def test_play_outbox_wiring():
    """接线: 纯队列模块 play-outbox.js + 浏览器接线
    music-play-outbox-integration.js 都挂在 audio-events 之前 (全局
    createPlayOutbox / reportPlay 才接得上); 「playing」出声改走补报队列,
    发后不管的老 fetch 撤了; 三个补报时机 —— 开局、回网 (online)、回前台
    (visibilitychange); 队列键 music-play-outbox。"""
    html = music_page_shell()
    events_js = (MUSIC_STATIC / "js" / "music-player-audio-events.js"
                 ).read_text(encoding="utf-8")
    wiring_js = (MUSIC_STATIC / "js" / "music-play-outbox-integration.js"
                 ).read_text(encoding="utf-8")
    outbox_js = (MUSIC_STATIC / "js" / "play-outbox.js").read_text(
        encoding="utf-8")
    assert "function createPlayOutbox" in outbox_js
    assert "module.exports = { createPlayOutbox, PLAY_OUTBOX_CAP }" in outbox_js
    assert "404" in outbox_js                  # 曲目已删: 丢弃不重试
    # 三个文件按依赖序加载: 纯逻辑 → 接线 (reportPlay) → 消费方
    assert html.index("js/play-outbox.js?v=") < \
        html.index("js/music-play-outbox-integration.js?v=") < \
        html.index("js/music-player-audio-events.js?v=")
    assert "const playOutbox = createPlayOutbox({" in wiring_js
    assert '"music-play-outbox"' in wiring_js   # localStorage 队列键
    assert "body: JSON.stringify(entry)" in wiring_js   # 补报带真实时刻
    assert 'window.addEventListener("online", () => { playOutbox.flush(); });' \
        in wiring_js
    assert 'if (document.visibilityState === "visible") playOutbox.flush();' \
        in wiring_js
    assert wiring_js.count("playOutbox.flush();") == 3   # 开局/回网/回前台
    assert "function reportPlay(trackId)" in wiring_js
    assert "playOutbox.report(trackId);" in wiring_js
    # 「playing」出声走 reportPlay; 发后不管的老 fetch 退役
    assert "reportPlay(currentTrack.track_id);" in events_js
    assert "JSON.stringify({ track_id: currentTrack.track_id })" \
        not in events_js
    assert 'fetch("/music/api/plays"' not in events_js
