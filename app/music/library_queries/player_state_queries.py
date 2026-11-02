"""播放现场查询: 每用户的队列 + 进度两半边 (1.8.142 起镜像服务端 ——
浏览器 localStorage 会被 Safari 清掉, 现场得有后端一份)。"""
import json
import time
from typing import Any

from sqlalchemy.orm import Session

from ..library_database import PlayerPosition, PlayerQueue
from ..schemas import (PlayerPositionSnapshot, PlayerQueueRequest,
                       PlayerQueueSnapshot, PlayerStateResponse,
                       PlayerTickRequest)

QUEUE_CAP = 500    # 与客户端 localStorage 现场档同帽 (整库随机队列截断)


def _loads(text: str, fallback: Any) -> Any:
    """JSON 落库字段读回: 坏档 (老行/手改) 当缺省, 不让 500 炸开局回填。"""
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return fallback


def save_player_queue(session: Session, user_uuid: str,
                      body: PlayerQueueRequest) -> None:
    """落现场全量 (队列半边 + 进度半边一笔事务): 队列变了才该走这条 ——
    大行整行重写, 别当 tick 用。tracks 服务端再截一次 QUEUE_CAP 兜底。"""
    row = session.get(PlayerQueue, user_uuid)
    if row is None:
        row = PlayerQueue(user_uuid=user_uuid)
        session.add(row)
    row.tracks_json = json.dumps(body.tracks[:QUEUE_CAP],
                                 ensure_ascii=False, separators=(",", ":"))
    row.order_json = json.dumps(body.order[:QUEUE_CAP],
                                separators=(",", ":"))
    row.shuffle = bool(body.shuffle)
    row.repeat = "one" if body.repeat == "one" else "all"
    row.updated_at = time.time()
    _write_position(session, user_uuid, body.index, body.position, body.time)
    session.commit()


def save_player_position(session: Session, user_uuid: str,
                         body: PlayerTickRequest) -> None:
    """只落进度小行 (5 秒一拍的 tick): 播到队列哪一环的哪一首的哪一秒,
    队列行不动 (SQLite 改一行整行重写, 大行别碰)。"""
    _write_position(session, user_uuid, body.index, body.position, body.time)
    session.commit()


def _write_position(session: Session, user_uuid: str, index: int,
                    position: int, time_sec: float) -> None:
    """进度半边落值 (不提交 —— 全量路与 tick 路共用, 提交给调用方)。"""
    row = session.get(PlayerPosition, user_uuid)
    if row is None:
        row = PlayerPosition(user_uuid=user_uuid)
        session.add(row)
    row.track_index = int(index)
    row.queue_position = int(position)
    row.time_sec = float(time_sec)
    row.updated_at = time.time()


def load_player_state(session: Session, user_uuid: str) -> PlayerStateResponse:
    """读回现场 (开局回填): 两半边各自独立缺省 —— 浏览器清了本地档,
    队列和进度都从这里捞回来。"""
    queue = session.get(PlayerQueue, user_uuid)
    position = session.get(PlayerPosition, user_uuid)
    return PlayerStateResponse(
        queue=None if queue is None else PlayerQueueSnapshot(
            tracks=_loads(queue.tracks_json, []),
            order=_loads(queue.order_json, []),
            shuffle=queue.shuffle,
            repeat=queue.repeat,
            updated_at=queue.updated_at,
        ),
        position=None if position is None else PlayerPositionSnapshot(
            index=position.track_index,
            position=position.queue_position,
            time=position.time_sec,
            updated_at=position.updated_at,
        ),
    )
