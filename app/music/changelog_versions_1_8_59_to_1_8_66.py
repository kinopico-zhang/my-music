"""1.8 系列的版本条目 · 冻结段 1.8.59–1.8.66 (2026-09-25 活跃段又超 200 行
硬上限, 按仓里先例把老段搬出去)。条目规矩: 用户视角, 一条一句话。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8_59_TO_1_8_66: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.66", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="切歌不再改变播放状态, 本来暂停的"
                                       "保持暂停, 自然播完的连播照旧"),
        ChangelogItem(kind="改进", text="左右划封面时两侧封面过场张得更开, "
                                       "滚动中不再叠在一起"),
    ]),
    ChangelogVersion(version="1.8.65", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="左右划封面时后侧封面不再突然跳到前面"
                                       "盖过当前封面, 遮盖交接改成平滑的溶解过渡"),
    ]),
    ChangelogVersion(version="1.8.64", date="2026-09-22", items=[
        ChangelogItem(kind="改进", text="播放气泡展开成播放页的水滴动画放慢"
                                       "了, 封面和控件分层一排排浮现"),
    ]),
    ChangelogVersion(version="1.8.63", date="2026-09-22", items=[
        ChangelogItem(kind="改进", text="点播放气泡打开播放页, 面板像水滴"
                                       "一样从气泡原位平滑延展成整页, 不再"
                                       "生硬弹窗"),
    ]),
    ChangelogVersion(version="1.8.62", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="封面 3D 切歌时两张封面互相穿过去"
                                       "的问题修好了"),
    ]),
    ChangelogVersion(version="1.8.61", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="封面 3D 切歌的卡顿修好了, 换曲"
                                       "落定改走系统合成, 主线程再忙也不掉帧"),
    ]),
    ChangelogVersion(version="1.8.60", date="2026-09-21", items=[
        ChangelogItem(kind="新增", text="播放页封面换成 3D 舞台, 上一首下一首"
                                       "斜插在两侧, 左右划跟手转面切歌"),
    ]),
    ChangelogVersion(version="1.8.59", date="2026-09-21", items=[
        ChangelogItem(kind="修复", text="锁屏听歌播着播着自己停的问题修好了"),
    ]),
]
