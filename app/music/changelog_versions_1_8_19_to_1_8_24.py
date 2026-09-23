"""1.8 系列的版本条目 · 冻结段 1.8.19–1.8.24 (当年活跃段超 200 行硬上限,
按仓里先例把老段搬出去)。条目规矩: 用户视角, 一条一句话。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8_19_TO_1_8_24: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.24", date="2026-09-19", items=[
        ChangelogItem(kind="改进", text="主页改成三段 (最近播放/最新专辑/最近"
                                       "列表), 段标题点开看全部"),
    ]),
    ChangelogVersion(version="1.8.23", date="2026-09-19", items=[
        ChangelogItem(kind="新增", text="主页右划到头有了橡皮筋回弹"),
        ChangelogItem(kind="修复", text="左滑删除时封面不再消失"),
        ChangelogItem(kind="改进", text="分享按钮换成苹果系统的共享图标"),
    ]),
    ChangelogVersion(version="1.8.22", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="播放中的波动图标回到封面正中"),
    ]),
    ChangelogVersion(version="1.8.21", date="2026-09-18", items=[
        ChangelogItem(kind="改进", text="菜单与页标题改口 (已下载 → 下载管理 等)"),
    ]),
    ChangelogVersion(version="1.8.20", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="拖动换序落定那一下让位的行不再抖"),
        ChangelogItem(kind="改进", text="搜索框下方的提示行撤了"),
        ChangelogItem(kind="改进", text="歌词键默认灰着, 确认有词才亮"),
        ChangelogItem(kind="改进", text="歌词页的封面缩略图撤了, 歌词独占整页"),
        ChangelogItem(kind="改进", text="「添加到播放列表」选择单换成列表自己"
                                       "的封面小图"),
        ChangelogItem(kind="改进", text="播放中那行封面上的动条重画成整面纱罩"
                                       "加白色动条"),
    ]),
    ChangelogVersion(version="1.8.19", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="播放列表拖动换序, 被拖的那行不再被黑"
                                       "色空位遮住"),
        ChangelogItem(kind="修复", text="搜索框下移出系统的模糊地带"),
        ChangelogItem(kind="改进", text="歌词页显示歌曲封面 (缩成顶部小图)"),
        ChangelogItem(kind="改进", text="「添加到播放列表」选择单里列表之间的"
                                       "分割线撤了"),
        ChangelogItem(kind="改进", text="分享页滑动封面切歌有了跟手方向的动画"),
        ChangelogItem(kind="改进", text="搜索框/抓手等固定控件统一钉到系统模"
                                       "糊带之下"),
    ]),
]
