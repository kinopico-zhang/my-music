"""My Music 播放现场路由 (1.8.142, 拆自 library_routes 的 200 行帽):
队列 + 进度两半边的读 / 全量 / tick, 全在 /api 下 (登录用户)。

localStorage 会被 Safari 清掉, 现场镜像服务端 —— 开局回填走 GET,
客户端队列变了 PUT 全量, 平时 5 秒一拍 PUT tick。"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ... import database
from ...schemas import OkResponse
from .. import library_queries
from ..library_database import get_db
from ..schemas import (PlayerQueueRequest, PlayerStateResponse,
                       PlayerTickRequest)
from .common import _require_user

router = APIRouter(prefix="/api")


@router.get("/player-state", response_model=PlayerStateResponse)
def music_player_state(request: Request,
                       users: Session = Depends(database.get_users_db),
                       library: Session = Depends(get_db)) -> PlayerStateResponse:
    """本人的播放现场 (开局回填): 浏览器清了本地档, 队列和进度从这里捞回。"""
    user = _require_user(request, users)
    return library_queries.load_player_state(library, user.uuid)


@router.put("/player-state", response_model=OkResponse)
def music_save_player_state(body: PlayerQueueRequest, request: Request,
                            users: Session = Depends(database.get_users_db),
                            library: Session = Depends(get_db)) -> OkResponse:
    """落现场全量 (队列 + 进度一笔双写): 客户端队列变了才发, 大行别勤写。"""
    user = _require_user(request, users)
    library_queries.save_player_queue(library, user.uuid, body)
    return OkResponse(ok=True)


@router.put("/player-state/tick", response_model=OkResponse)
def music_save_player_tick(body: PlayerTickRequest, request: Request,
                           users: Session = Depends(database.get_users_db),
                           library: Session = Depends(get_db)) -> OkResponse:
    """落进度小拍 (客户端 5 秒一拍): 播到哪环哪首哪一秒。"""
    user = _require_user(request, users)
    library_queries.save_player_position(library, user.uuid, body)
    return OkResponse(ok=True)
