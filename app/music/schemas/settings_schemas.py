"""设置域的接口模型: 设置页状态/更新。"""
from pydantic import BaseModel


class MusicSettingsState(BaseModel):
    """设置页状态: 各字段现值 + 默认值参照 (空 = 用默认)。"""

    music_directory: str = ""
    music_directory_default: str = ""
    lyrics_api_enabled: bool = True
    lyrics_api_base: str = ""
    lyrics_api_default: str = ""


class MusicSettingsUpdate(BaseModel):
    """POST /api/settings 的请求体 (缺字段 = 不动那项)。"""

    music_directory: str | None = None
    lyrics_api_enabled: bool | None = None
    lyrics_api_base: str | None = None
