"""1.8 系列中段的版本条目 (1.8.14–1.8.16, 冻结段)。2026-09-18 从
changelog_versions_1_8.py 分出: 1.8 线第四次超 200 行硬上限 (1.8.19 上线时),
按中段分家的先例再分; 活跃段 (1.8.17 起) 留在原文件。条目规矩: 用户视角,
一条一句话。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8_14_TO_1_8_16: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.16", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="追了七个版本的底部黑带治好了, 收起键盘"
                                       "后底部完整如初"),
        ChangelogItem(kind="改进", text="体检窗还留着, 黑带病万一将来复发日志里"
                                       "一眼能认出来"),
    ]),
    ChangelogVersion(version="1.8.15", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="搜索页大重排, 搜索栏住进页面自己的滚动"
                                       "区里"),
        ChangelogItem(kind="改进", text="搜索栏自动贴在键盘上沿, 不用再手动量"),
    ]),
    ChangelogVersion(version="1.8.14", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="键盘弹起前先把搜索框抬到屏幕上部, 从起"
                                       "手掐掉黑带"),
        ChangelogItem(kind="改进", text="体检窗的复原指引换成实测真话了"),
    ]),
]
