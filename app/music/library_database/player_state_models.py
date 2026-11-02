"""My Music 的库表结构 · 播放现场两张表 (1.8.142, 拆自 library_models 的
200 行帽): 队列半边 (大行) + 进度半边 (小行)。

播放进度原先只存浏览器 localStorage —— Safari 随时会清掉 (用户 2026-11-02
点名「前端不可靠, 你要保存在后端」), 现场从此镜像服务端: 开局本地档没了
从这捞回, 换台设备登录也接得上。拆两张表: 队列行最大上百 KB, SQLite 改
一行整行重写, 5 秒一拍的进度 tick 只该写 player_positions 那张小行。"""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .library_models import MusicLibraryBase


class PlayerQueue(MusicLibraryBase):
    """播放现场·队列半边 (每用户一行): 上次听着的整张队列。

    曲目对象数组 (同客户端截到 500 首) + 播放顺序 + 洗牌/循环旗;
    消费方见 player_state_queries.save_player_queue。"""

    __tablename__ = "player_queues"

    user_uuid: Mapped[str] = mapped_column(String(32), primary_key=True)
    tracks_json: Mapped[str] = mapped_column(default="[]")
    order_json: Mapped[str] = mapped_column(default="[]")
    shuffle: Mapped[bool] = mapped_column(default=False)
    repeat: Mapped[str] = mapped_column(default="all")       # "all" | "one" (三态, off 已退役)
    updated_at: Mapped[float] = mapped_column(default=0.0)   # epoch 秒


class PlayerPosition(MusicLibraryBase):
    """播放现场·进度半边 (每用户一行): 播到队列哪一环的哪一首的哪一秒。

    字段对齐客户端现场档 (music-player-persistence 的 applySavedState):
    track_index 进 tracks 数组、queue_position 进 order 序。"""

    __tablename__ = "player_positions"

    user_uuid: Mapped[str] = mapped_column(String(32), primary_key=True)
    track_index: Mapped[int] = mapped_column(default=0)
    queue_position: Mapped[int] = mapped_column(default=0)
    time_sec: Mapped[float] = mapped_column(default=0.0)
    updated_at: Mapped[float] = mapped_column(default=0.0)
