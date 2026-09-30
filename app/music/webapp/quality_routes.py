"""My Music 音质参数路由 (1.8.127): 播放页封面下那行的取数口。

单曲采样率/位深/声道/平均码率。索引里有 (扫描顺手入库) 走库, 老行没有
现读文件回填 —— 单独成文件是因为 library_routes 顶满 200 行, 音质这条
线又自成一类 (按需探测 + 回填), 与视口回传 (viewport_routes) 同例。"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ... import database
from .. import library_queries
from ..library_database import get_db
from ..schemas import AudioQuality
from .common import _require_user

router = APIRouter(prefix="/api")


@router.get("/tracks/{track_id}/quality", response_model=AudioQuality)
def music_track_quality(track_id: int, request: Request,
                        users: Session = Depends(database.get_users_db),
                        library: Session = Depends(get_db)) -> AudioQuality:
    """单曲音质参数 (sample_rate=0 = 没读到, 前端藏行)。"""
    _require_user(request, users)
    quality = library_queries.audio_quality_for_track(library, track_id)
    if quality is None:
        raise HTTPException(404, "曲目不存在")
    return quality
