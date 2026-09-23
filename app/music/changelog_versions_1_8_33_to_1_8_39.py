"""1.8 系列的版本条目 · 冻结段 1.8.33–1.8.39 (当年活跃段超 200 行硬上限,
按仓里先例把老段搬出去)。条目规矩: 用户视角, 一条一句话。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8_33_TO_1_8_39: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.39", date="2026-09-20", items=[
        ChangelogItem(kind="新增", text="电脑上能用键盘了 (空格 播放/暂停, 左"
                                       "右箭头切歌, / 直达搜索)"),
        ChangelogItem(kind="改进", text="电脑上鼠标手感一整套 (悬停亮一档、光"
                                       "标变手型、悬停出提示)"),
    ]),
    ChangelogVersion(version="1.8.38", date="2026-09-20", items=[
        ChangelogItem(kind="改进", text="播放页的「继续播放」队列改成歌单同款"
                                       "行, 每行带封面"),
    ]),
    ChangelogVersion(version="1.8.37", date="2026-09-20", items=[
        ChangelogItem(kind="新增", text="分享页播放器加了随机/循环键, 不登录也"
                                       "能轮着听"),
    ]),
    ChangelogVersion(version="1.8.36", date="2026-09-20", items=[
        ChangelogItem(kind="修复", text="搜索歌词结果每行补上歌曲封面"),
        ChangelogItem(kind="改进", text="搜索结果列表上方重复的数量标题撤了"),
    ]),
    ChangelogVersion(version="1.8.35", date="2026-09-20", items=[
        ChangelogItem(kind="新增", text="应用会识别手机还是电脑, 电脑上恢复滚"
                                       "动条"),
    ]),
    ChangelogVersion(version="1.8.34", date="2026-09-20", items=[
        ChangelogItem(kind="新增", text="专辑/列表/艺人页上划时封面收进顶栏, "
                                       "下划放大回原样"),
    ]),
    ChangelogVersion(version="1.8.33", date="2026-09-20", items=[
        ChangelogItem(kind="新增", text="专辑也能分享了 (24 小时有效链接, 微信"
                                       "卡片带封面)"),
        ChangelogItem(kind="改进", text="专辑/艺人页的操作键改成纯图标, 和播放"
                                       "列表同款"),
    ]),
]
