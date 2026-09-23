"""1.8 系列中段的版本条目 (1.8.5–1.8.9, 冻结段)。2026-09-18 从
changelog_versions_1_8.py 分出: 1.8 线又超了 200 行的硬上限 (1.8.15 上线时),
按 1_8_0_to_1_8_4 的先例再分家; 活跃段 (1.8.10 起) 留在原文件。条目规矩:
用户视角, 一条一句话。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8_5_TO_1_8_9: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.9", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="键盘没收起就右划关搜索页, 底部黑带的"
                                       "病根修掉了"),
        ChangelogItem(kind="修复", text="页面万一又被垫矮, 应用自己能察觉并悄"
                                       "悄修回来"),
    ]),
    ChangelogVersion(version="1.8.8", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="重开应用记的是整条来路, 一路返回都能"
                                       "退到主页"),
        ChangelogItem(kind="修复", text="退出搜索页后底部的黑区多复查几遍, 还"
                                       "得再慢也追得上"),
    ]),
    ChangelogVersion(version="1.8.7", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="搜过歌回主页后底部出黑区、页面没充满"
                                       "屏的毛病根治了"),
    ]),
    ChangelogVersion(version="1.8.6", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="搜索的数量对齐了: 标题报真实命中数, "
                                       "列不全的注明共多少"),
        ChangelogItem(kind="修复", text="搜索页退出后马上再进, 输入框不见了的"
                                       "毛病修好了"),
        ChangelogItem(kind="修复", text="继续播放列表顶上的标题和控制键不再发"
                                       "糊"),
        ChangelogItem(kind="修复", text="歌词当前句放大时不再临时换行跳一下"),
        ChangelogItem(kind="新增", text="播放页三个点的菜单里加了「下载」"),
        ChangelogItem(kind="新增", text="已下载页加了「多选」, 一口气删掉好几"
                                       "首"),
        ChangelogItem(kind="修复", text="分享播放页补齐: 点歌词句跳进度、双击"
                                       "不再放大页面、封面也挂上了"),
    ]),
    ChangelogVersion(version="1.8.5", date="2026-09-17", items=[
        ChangelogItem(kind="新增", text="点搜索后底部的三件套让位给搜索框"),
        ChangelogItem(kind="新增", text="分享单曲的播放页和应用里的一样了, 歌"
                                       "词界面也同款"),
        ChangelogItem(kind="改进", text="「待播放」改口「继续播放」, 随机和循"
                                       "环换成两枚图标键"),
        ChangelogItem(kind="改进", text="专辑主页不再显示入库时间, 三件套透明"
                                       "度调回半透明一档"),
        ChangelogItem(kind="修复", text="播放气泡右划返回修好了, 离开搜索页后"
                                       "的黑区也修了"),
        ChangelogItem(kind="修复", text="一堆小的修了: 艺人显示 0 专辑 0 首歌、"
                                       "歌词放大换行、封面闪烁等"),
    ]),
]
