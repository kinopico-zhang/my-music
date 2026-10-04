"""搜索与播放记录域的接口模型: 搜索四板块 + 记播/最近播放/歌词/来源。"""
from pydantic import BaseModel, Field

from .browse_schemas import AlbumCard, ArtistBrief, TrackBrief


class LyricHit(BaseModel):
    """歌词命中的片段: 哪首歌的哪一行 (不含时间轴)。"""

    track: TrackBrief
    line_text: str = Field(default="")


class SearchResult(BaseModel):
    """一次搜索的四个板块 (关键词同时命中多板块)。"""

    query: str
    language: str = "全部"
    tracks: list[TrackBrief] = Field(default_factory=list)
    albums: list[AlbumCard] = Field(default_factory=list)
    artists: list[ArtistBrief] = Field(default_factory=list)
    lyric_hits: list[LyricHit] = Field(default_factory=list)
    # 各板块命中总数 (1.8.6): 列表按容量截断, 总数不截 —— 板块头/页签
    # 报总数, 截断时列表尾注明 (修「艺人 64 专辑, 专辑板块只有 20 张」)
    track_total: int = 0
    album_total: int = 0
    artist_total: int = 0
    lyric_total: int = 0


class PlayRecordRequest(BaseModel):
    """POST /api/plays 的请求体 (播一次报一次)。1.8.124 起 played_at 可带
    (epoch 秒): 离线补报的真实播放时刻 —— 没带记成当下, 越界也落回当下。"""

    track_id: int
    played_at: int | None = None


class RecentTrackBrief(TrackBrief):
    """最近播放行 (1.8.1): 曲目信息 + 这首播过几次 (页面上替掉时长)。"""

    play_count: int = 0


class RecentPlaysResponse(BaseModel):
    """GET /api/plays/recent 的应答 (本人的最近播放, 每首只一行)。"""

    tracks: list[RecentTrackBrief] = Field(default_factory=list)


class TopPlaysResponse(BaseModel):
    """GET /api/plays/top 的应答 (本人的区间排行, 按区间内次数排)。

    行复用 RecentTrackBrief: play_count 是该区间内的播放次数。"""

    period: str                                        # week | month | year
    tracks: list[RecentTrackBrief] = Field(default_factory=list)


class LyricsResponse(BaseModel):
    """单曲歌词原文 (前端解析时间轴)。"""

    track_id: int
    lyrics: str
    lyrics_synced: bool
    lyrics_offset_ms: int = 0   # 词的对齐微调 (毫秒, 正 = 整体延后; 1.8.133)


class LyricsCandidate(BaseModel):
    """搜索到的候选词: 哪家厂商的哪首 (ref 是厂商内的歌标识)。"""

    source: str                 # netease | qq | lrclib
    ref: str
    title: str = ""
    artist: str = ""
    synced: bool | None = None  # 带不带时间轴 (LRCLIB 搜索即知, 网易/QQ 取词才知)


class LyricsSearchResponse(BaseModel):
    """GET /api/tracks/{id}/lyrics/candidates 的应答: 关键词搜来的候选。"""

    candidates: list[LyricsCandidate] = Field(default_factory=list)


class LyricsApplyRequest(BaseModel):
    """POST /api/tracks/{id}/lyrics/apply 的请求体: 把选中的候选套上这首。"""

    source: str
    ref: str


class LyricsOffsetRequest(BaseModel):
    """POST /api/tracks/{id}/lyrics/offset 的请求体: 词的对齐微调 (毫秒)。"""

    offset_ms: int


class TrackCredits(BaseModel):
    """单曲 作词/作曲 标签 (全屏播放页来源行, 按需现读, 缺标签 = 空串)。"""

    lyricist: str = ""
    composer: str = ""


class AudioQuality(BaseModel):
    """单曲音质参数 (全屏播放页封面下那行, 1.8.127)。

    sample_rate/bit_depth/channels 从索引来 (老行没有按需现读文件回填);
    bitrate 是平均码率 (文件大小/时长算出, 有损无损都适用), kbps。"""

    file_format: str = ""
    sample_rate: int = 0              # Hz
    bit_depth: int = 0                # bit, 有损恒 0
    channels: int = 0
    bitrate: int = 0                  # kbps, 时长/大小缺一算不出 = 0
