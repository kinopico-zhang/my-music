"""My Music 播放现场测试 (1.8.142 服务端镜像): localStorage 会被 Safari 随时
清掉, 用户点名「每个用户的播放进度你要保存在后端」—— 队列+进度两半边的
落/读/账号隔离, tick 只写小行不碰大行; 每次播放的服务端日志 (用户点名
「每次播放歌曲, 你都需要在后台日志记录」) 与客户端接线钉也在这。
wiring/page_wiring 两文件已满 200 行帽, 新钉全进本文件。"""
import json
import logging
import time

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as m
from app import account_store
from app.music.library_database import (PlayerPosition, PlayerQueue,
                                        session_factory)
from tests.music_library_helpers import _seed_library
from tests.music_static_files import MUSIC_STATIC, music_page_shell

QUEUE = [{"id": 1, "title": "曲A"}, {"id": 2, "title": "曲B"}]


def test_player_state_roundtrip(auth):
    """现场接口: 没存过两半边都 None; PUT 全量双写两表; GET 合并回同形
    (字段名与客户端 localStorage 现场档一字不差, 回填零翻译)。"""
    assert auth.get("/music/api/player-state").json() == {
        "queue": None, "position": None}
    put = auth.put("/music/api/player-state", json={
        "tracks": QUEUE, "order": [1, 0], "index": 1, "position": 0,
        "time": 63.5, "shuffle": True, "repeat": "one"})
    assert put.status_code == 200 and put.json() == {"ok": True}
    state = auth.get("/music/api/player-state").json()
    assert state["queue"]["tracks"] == QUEUE
    assert state["queue"]["order"] == [1, 0]
    assert state["queue"]["shuffle"] is True
    assert state["queue"]["repeat"] == "one"
    assert (state["position"]["index"], state["position"]["position"],
            state["position"]["time"]) == (1, 0, 63.5)
    with session_factory()() as session:          # 两半边各自落表
        queue = session.execute(select(PlayerQueue)).scalars().one()
        position = session.execute(select(PlayerPosition)).scalars().one()
        assert json.loads(queue.tracks_json) == QUEUE
        assert json.loads(queue.order_json) == [1, 0]
        assert queue.shuffle is True and queue.repeat == "one"
        assert (position.track_index, position.queue_position,
                position.time_sec) == (1, 0, 63.5)


def test_player_state_tick_only_small_row(auth):
    """tick 只写进度小行: 队列行 (可达上百 KB 的大行) 原样不动 —— SQLite
    改一行整行重写, 5 秒一拍不能拿大行垫背。"""
    auth.put("/music/api/player-state", json={
        "tracks": QUEUE, "order": [0, 1], "index": 0, "position": 0,
        "time": 10.0, "shuffle": False, "repeat": "all"})
    with session_factory()() as session:
        queue = session.execute(select(PlayerQueue)).scalars().one()
        before = (queue.updated_at, queue.tracks_json)
    time.sleep(0.01)
    assert auth.put("/music/api/player-state/tick",
                    json={"index": 0, "position": 1, "time": 12.25}
                    ).json() == {"ok": True}
    with session_factory()() as session:
        queue = session.execute(select(PlayerQueue)).scalars().one()
        position = session.execute(select(PlayerPosition)).scalars().one()
        assert (queue.updated_at, queue.tracks_json) == before   # 大行没动
        assert (position.queue_position, position.time_sec) == (1, 12.25)
        assert position.updated_at > before[0]
    state = auth.get("/music/api/player-state").json()
    assert state["queue"]["tracks"] == QUEUE          # 队列半边还在
    assert state["position"]["time"] == 12.25


def test_player_state_per_user(auth, usersdb):
    """账号隔离: 各存各的现场, 互相看不见; 没登录 GET/PUT 都 401。"""
    anon = TestClient(m.app)
    assert anon.get("/music/api/player-state").status_code == 401
    assert anon.put("/music/api/player-state",
                    json={"tracks": QUEUE}).status_code == 401
    auth.put("/music/api/player-state", json={
        "tracks": QUEUE, "order": [], "index": 0, "position": 0, "time": 1.0})
    account_store.create_user(usersdb, "试听乙", "password123")
    yi = TestClient(m.app)
    assert yi.post("/api/login",
                   json={"user": "试听乙", "password": "password123"}
                   ).status_code == 200
    assert yi.get("/music/api/player-state").json() == {
        "queue": None, "position": None}              # 看不见管理员的现场
    yi.put("/music/api/player-state", json={
        "tracks": [{"id": 9, "title": "乙曲"}], "order": [0], "index": 0,
        "position": 0, "time": 2.0})
    assert yi.get("/music/api/player-state").json()["queue"]["tracks"] == [
        {"id": 9, "title": "乙曲"}]
    assert auth.get("/music/api/player-state").json()["queue"][
        "tracks"] == QUEUE                            # 也没被串走


def test_player_queue_capped(auth):
    """服务端兜底截断: 客户端该自己截 500, 没截也只落 500 (大行不失控)。"""
    tracks = [{"id": n, "title": f"曲{n}"} for n in range(502)]
    auth.put("/music/api/player-state", json={
        "tracks": tracks, "order": list(range(502)), "index": 0,
        "position": 0, "time": 0.0})
    state = auth.get("/music/api/player-state").json()
    assert len(state["queue"]["tracks"]) == 500
    assert len(state["queue"]["order"]) == 500


def test_record_play_logs_each_play(auth, caplog):
    """每次播放服务端留一笔日志 (2026-11-02 用户点名): 谁在几点听了哪首;
    离线补报的旧账单独标「补报」—— 流水里分不开的, 日志分得开。"""
    _seed_library()
    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        assert auth.post("/music/api/plays",
                         json={"track_id": 1}).status_code == 200
        assert auth.post("/music/api/plays", json={
            "track_id": 2, "played_at": int(time.time()) - 3600
        }).status_code == 200
    lines = [r.message for r in caplog.records if r.message.startswith("播放: ")]
    assert len(lines) == 2                             # 播一次一笔
    assert "曲A" in lines[0] and "曲B" in lines[1]
    assert "补报" not in lines[0] and "补报" in lines[1]


def test_player_state_client_wiring():
    """客户端接线: 本地档之外镜像服务端 —— savePlayerState 尾巴同步 (队列
    变全量 PUT / 平时 4 秒一拍 tick), 开局本地档没了从服务端回填并写回本地;
    单曲循环每圈重报播放 (用户点名「每一次都应该算播放」)。"""
    html = music_page_shell()
    persistence = (MUSIC_STATIC / "js" / "music-player-persistence.js"
                   ).read_text(encoding="utf-8")
    boot = (MUSIC_STATIC / "js" / "music-player-boot.js").read_text(
        encoding="utf-8")
    audio = (MUSIC_STATIC / "js" / "music-player-audio-events.js").read_text(
        encoding="utf-8")
    sw = (MUSIC_STATIC / "sw.js").read_text(encoding="utf-8")
    # ?v= 换内容必换址 (1.8.125 中间态缓存事故的教训)
    assert 'js/music-player-persistence.js?v=6"' in html
    assert 'js/music-player-audio-events.js?v=18"' in html
    assert 'js/music-player-boot.js?v=3"' in html
    assert 'js/music-player-state.js?v=5"' in html
    assert "music-shell-v125" in sw
    # 服务端镜像与开局回填
    assert 'fetchJSON("/music/api/player-state")' in persistence
    assert '"/music/api/player-state/tick"' in persistence
    for frag in ["function syncPlayerState", "function sendPlayerState",
                 "function playerStateServerBackfill",
                 "function applySavedState", "syncPlayerState();",
                 "if (currentTrack) return;", "keepalive"]:
        assert frag in persistence, f"现场镜像缺 {frag}"
    assert "playerStateServerBackfill();" in boot
    assert "localStorage.setItem(PLAYER_STATE_KEY, JSON.stringify(saved))" \
        in persistence      # 回填结果写回本地, 下次开局秒回
    # 单曲循环每圈重报: 重置旗在回开头重播之前 (代码序, 别咬注释)
    assert audio.count("playRecorded = false;") == 1
    assert audio.index("playRecorded = false;") < audio.index(
        "startAudio().catch")
