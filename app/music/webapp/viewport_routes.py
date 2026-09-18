"""My Music 视口体检回传路由 (1.8.10): 视口医生的现场流水落盘。

iOS 键盘往返后视口冻矮 (底部黑带) 这条线的排查数据: 手机上复现完,
流水已经在服务器上 (data/viewport-doctor.jsonl, 一行一个事件), 读文件
分析即可, 不用等截图。谁登录都能报 —— 事件字段全部封顶, 灌不爆盘。"""
import json
import time
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ... import database
from ...config import PROJECT_DIR
from ...schemas import OkResponse
from ..schemas import ViewportLogReport
from .common import _require_user

router = APIRouter(prefix="/api")

LOG_LIMIT = 2 * 1024 * 1024     # 超 2MB 滚一份 (.jsonl.1), 别无限长


def _log_path() -> Path:
    """落盘位置 (函数化: 测试 monkeypatch 到临时目录, 不碰真档)。"""
    return PROJECT_DIR / "data" / "viewport-doctor.jsonl"


@router.post("/viewport-log", response_model=OkResponse)
def music_viewport_log(body: ViewportLogReport, request: Request,
                       users: Session = Depends(database.get_users_db)) -> OkResponse:
    """客户端回传一批视口事件, 追加进 data/viewport-doctor.jsonl。"""
    _require_user(request, users)
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > LOG_LIMIT:
        path.replace(path.with_suffix(".jsonl.1"))
    with path.open("a", encoding="utf-8") as fh:
        for event in body.events:
            fh.write(json.dumps(
                {"recv": round(time.time(), 3), "ua": body.ua,
                 **event.model_dump()}, ensure_ascii=False) + "\n")
    return OkResponse(ok=True)
