"""1.8 系列中段的版本条目 (1.8.10–1.8.13, 冻结段)。2026-09-18 从
changelog_versions_1_8.py 分出: 1.8 线第三次超 200 行硬上限 (1.8.18 上线时),
按中段分家的先例再分; 活跃段 (1.8.14 起) 留在原文件。条目规矩: 用户视角,
一条一句话。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8_10_TO_1_8_13: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.13", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="键盘一收页面就钉在原位陪动画走完, 黑带"
                                       "来不及冒头"),
        ChangelogItem(kind="改进", text="体检窗指引改口: 「划掉重开应用」才是实"
                                       "测真灵的复原法"),
    ]),
    ChangelogVersion(version="1.8.12", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="黑带一露头, 体检窗里多一颗「深度修复」"
                                       "键, 点一下就好 (歌还停在第几秒)"),
        ChangelogItem(kind="改进", text="体检窗瘦身, 没用的招全撤了只留一键深修"),
    ]),
    ChangelogVersion(version="1.8.11", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="收起键盘后自动把页面高度重算回来, 磨砂"
                                       "罩住闪动 (自动的, 不打扰)"),
        ChangelogItem(kind="修复", text="体检不再误诊, 不会把正在用的键盘收掉了"),
    ]),
    ChangelogVersion(version="1.8.10", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="收键盘那一下改等页面高度真正回满才动"
                                       "手, 键盘再磨蹭也陪它等到头"),
        ChangelogItem(kind="新增", text="被垫矮时屏幕角落自己弹红框体检窗, 点一"
                                       "下就好"),
    ]),
]
