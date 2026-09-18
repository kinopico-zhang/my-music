"""视口体检的回传请求体 (POST /api/viewport-log, 1.8.10)。

视口医生 (js/music-viewport-doctor.js + music-viewport-hud.js) 把体检窗
里的现场流水批量回传: 谁登录都能报 (复现是全家的事), 字段全部封顶 ——
灌水也灌不爆 (见 Field 上限)。"""
from pydantic import BaseModel, Field


class ViewportEvent(BaseModel):
    """体检流水里的一行: 事件名 + 当刻的视口现场快照。"""

    t: float = Field(ge=0)              # 客户端时间戳 (ms)
    line: str = Field(max_length=200)   # 事件名 (resize / focusout / 冻矮实锤…)
    inner: int = 0                      # window.innerHeight
    vv: float = 0                       # visualViewport.height
    top: float = 0                      # visualViewport.offsetTop
    left: float = 0                     # visualViewport.offsetLeft
    scrollY: float = 0


class ViewportLogReport(BaseModel):
    """一次上报: 上报端 UA + 一批事件 (视口医生的发件箱)。"""

    ua: str = Field(default="", max_length=300)
    events: list[ViewportEvent] = Field(max_length=64)
