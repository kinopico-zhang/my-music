"""1.8 系列的版本条目 · 冻结段 1.8.67–1.8.75 (2026-09-25 活跃段又超 200 行
硬上限, 按仓里先例把老段搬出去)。条目规矩: 用户视角, 一条一句话。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8_67_TO_1_8_75: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.75", date="2026-09-23", items=[
        ChangelogItem(kind="新增", text="艺人主页加了「刷新元数据」按钮, "
                                       "点一下按盘上现在的标签和海报重读这位"
                                       "艺人的全部信息 —— 换过的头像点完就能"
                                       "看到新图, 不用再等整库重扫"),
    ]),
    ChangelogVersion(version="1.8.74", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="播放页拖完进度条, 剩余时间和进度条"
                                       "不再提前归零, 会一直跟到歌真正播完"),
        ChangelogItem(kind="修复", text="播放页封面恢复正方形, 不再是被裁"
                                       "掉两边的竖长条"),
    ]),
    ChangelogVersion(version="1.8.73", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="在线歌曲放不出来或响几秒就断的问题"
                                       "修好了, 下载过的歌不受影响"),
    ]),
    ChangelogVersion(version="1.8.72", date="2026-09-22", items=[
        ChangelogItem(kind="改进", text="播放页封面下面那行作词署名撤掉了, "
                                       "看着更清爽"),
    ]),
    ChangelogVersion(version="1.8.71", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="被来电或别的应用声音打断后, 锁屏点"
                                       "播放键能接着播了"),
    ]),
    ChangelogVersion(version="1.8.70", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="重启应用后直接点气泡播放, 锁屏上"
                                       "也有上一首/下一首了"),
    ]),
    ChangelogVersion(version="1.8.69", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="iOS 锁屏按键换成上一首/下一首和暂停, "
                                       "不再是 10 秒快退快进"),
    ]),
    ChangelogVersion(version="1.8.68", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="点播放不再误弹「被浏览器拦了」,"
                                       "歌还在缓冲时连点播放键也不会互相掐断"),
    ]),
    ChangelogVersion(version="1.8.67", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="滑动封面切歌时旧封面不再闪一下"
                                       "消失再出现"),
    ]),
]
