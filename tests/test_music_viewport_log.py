"""视口体检回传测试 (1.8.10): POST /music/api/viewport-log 把视口医生的
现场流水落盘 —— 排查 iOS 键盘往返后视口冻矮 (底部黑带) 的数据通道,
权限、封顶、落盘格式各验一遍。落盘路径 monkeypatch 进临时目录, 不碰真档。"""
import json

from fastapi.testclient import TestClient

import app.main as m
from app.music.webapp import viewport_routes


def test_viewport_log_writes_events(auth, tmp_path, monkeypatch):
    """登录客户端报一批事件 → 追加落盘 (一行一事件, 带服务器接收时刻)。"""
    log = tmp_path / "viewport-doctor.jsonl"
    monkeypatch.setattr(viewport_routes, "_log_path", lambda: log)
    events = [
        {"t": 1760000000123, "line": "resize i504 v425", "inner": 504,
         "vv": 425, "top": 0, "left": 0, "scrollY": 0},
        {"t": 1760000000999, "line": "冻矮实锤 inner=771", "inner": 771,
         "vv": 771, "top": 0, "left": 0, "scrollY": 0},
    ]
    r = auth.post("/music/api/viewport-log",
                  json={"ua": "iPhone DIY", "events": events})
    assert r.status_code == 200 and r.json() == {"ok": True}
    lines = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 2
    assert lines[0]["line"] == "resize i504 v425" and lines[0]["inner"] == 504
    assert lines[0]["ua"] == "iPhone DIY" and "recv" in lines[0]
    assert lines[1]["line"] == "冻矮实锤 inner=771" and lines[1]["inner"] == 771
    # 追加不覆盖: 再报一批, 旧行还在
    auth.post("/music/api/viewport-log", json={"events": [events[0]]})
    assert len(log.read_text(encoding="utf-8").splitlines()) == 3


def test_viewport_log_limits_and_auth(auth, tmp_path, monkeypatch):
    """未登录 401 且不落盘; 登录后字段灌水 (批次 >64 / 行超长 / 负时间戳)
    422 —— 封顶在请求体模型上, 灌不爆盘。"""
    log = tmp_path / "viewport-doctor.jsonl"
    monkeypatch.setattr(viewport_routes, "_log_path", lambda: log)
    anon = TestClient(m.app)
    assert anon.post("/music/api/viewport-log", json={"events": []}).status_code == 401
    assert not log.exists()                    # 没登录一个字都不落
    # 登录了也不许灌水: 批次超 64 条 / 单行超 200 字 / 时间戳为负
    too_many = [{"t": 1, "line": "x"}] * 65
    assert auth.post("/music/api/viewport-log",
                     json={"events": too_many}).status_code == 422
    assert auth.post("/music/api/viewport-log",
                     json={"events": [{"t": 1, "line": "x" * 201}]}
                     ).status_code == 422
    assert auth.post("/music/api/viewport-log",
                     json={"events": [{"t": -1, "line": "x"}]}
                     ).status_code == 422
    assert not log.exists()                    # 422 的一批整个拒收, 不落半截
