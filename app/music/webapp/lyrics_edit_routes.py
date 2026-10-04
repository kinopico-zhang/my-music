"""My Music 调整歌词路由 (1.8.133): 播放页 ⋯ 菜单「调整歌词」的后端。

三个口: 关键词搜候选 / 套用选中 / 对齐微调 —— 单独成文件是因为
library_routes 顶满 200 行 (quality_routes 同例)。搜索三家厂商并搜
(设置里的厂商选择只管自动补词的次序, 手动挑词让用户自己来)。"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ... import database
from .. import library_queries, library_settings
from ..library_database import Track, get_db
from ..library_lyrics_search import candidate_lyrics, search_candidates
from ..schemas import (LyricsApplyRequest, LyricsOffsetRequest,
                       LyricsSearchResponse, LyricsResponse)
from .common import _require_user

router = APIRouter(prefix="/api")


@router.get("/tracks/{track_id}/lyrics/candidates",
            response_model=LyricsSearchResponse)
def music_lyrics_candidates(track_id: int, request: Request,
                            q: str = Query(min_length=1, max_length=100),
                            users: Session = Depends(database.get_users_db),
                            library: Session = Depends(get_db)
                            ) -> LyricsSearchResponse:
    """关键词搜歌词候选 (三家并搜, 用户自己挑; 不写库)。"""
    _require_user(request, users)
    if library.get(Track, track_id) is None:
        raise HTTPException(404, "曲目不存在")
    api_base = library_settings.effective_lyrics_api(library)[2]
    return LyricsSearchResponse(
        candidates=search_candidates(q, api_base))


@router.post("/tracks/{track_id}/lyrics/apply",
             response_model=LyricsResponse)
def music_lyrics_apply(track_id: int, body: LyricsApplyRequest,
                       request: Request,
                       users: Session = Depends(database.get_users_db),
                       library: Session = Depends(get_db)) -> LyricsResponse:
    """把选中的候选词套上这首 (换词即换时间轴, 旧微调清零)。"""
    _require_user(request, users)
    api_base = library_settings.effective_lyrics_api(library)[2]
    text = candidate_lyrics(body.source, body.ref, api_base)
    if not text:
        raise HTTPException(502, "这份词没取到, 换一个候选试试")
    lyrics = library_queries.replace_track_lyrics(library, track_id, text)
    if lyrics is None:
        raise HTTPException(404, "曲目不存在")
    return lyrics


@router.post("/tracks/{track_id}/lyrics/offset",
             response_model=LyricsResponse)
def music_lyrics_offset(track_id: int, body: LyricsOffsetRequest,
                        request: Request,
                        users: Session = Depends(database.get_users_db),
                        library: Session = Depends(get_db)) -> LyricsResponse:
    """词的对齐微调 (毫秒, 正 = 整体延后; ±30 秒钳制)。"""
    _require_user(request, users)
    lyrics = library_queries.set_lyrics_offset(library, track_id,
                                               body.offset_ms)
    if lyrics is None:
        raise HTTPException(404, "曲目不存在")
    return lyrics
