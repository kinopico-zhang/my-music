"""1.8 系列的版本条目 · 冻结段 1.8.25–1.8.32 (当年活跃段超 200 行硬上限,
按仓里先例把老段搬出去)。条目规矩: 用户视角, 一条一句话。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8_25_TO_1_8_32: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.32", date="2026-09-20", items=[
        ChangelogItem(kind="修复", text="杀掉重开偶尔整屏矮一截, 现在开局自动"
                                       "补回满屏"),
    ]),
    ChangelogVersion(version="1.8.31", date="2026-09-20", items=[
        ChangelogItem(kind="新增", text="播放排行页 (本周/本月/今年三个榜)"),
        ChangelogItem(kind="改进", text="队列和播放列表整行按住就能拖着换序了"),
        ChangelogItem(kind="改进", text="各列表滚到头有了橡皮筋回弹"),
    ]),
    ChangelogVersion(version="1.8.30", date="2026-09-19", items=[
        ChangelogItem(kind="修复", text="主页「最近添加专辑」点卡片进不去的漏"
                                       "跳转补上了"),
        ChangelogItem(kind="改进", text="主页三段重排, 「最近播放列表」提到最"
                                       "前"),
    ]),
    ChangelogVersion(version="1.8.29", date="2026-09-19", items=[
        ChangelogItem(kind="修复", text="播放不了音乐的问题修好了 (上一版启动"
                                       "时的一步抢跑带崩了一串)"),
    ]),
    ChangelogVersion(version="1.8.28", date="2026-09-19", items=[
        ChangelogItem(kind="改进", text="主页「最近播放列表」改成专辑同款网格"
                                       "卡"),
    ]),
    ChangelogVersion(version="1.8.27", date="2026-09-19", items=[
        ChangelogItem(kind="修复", text="主页列表行点不进去的问题修好了"),
        ChangelogItem(kind="新增", text="播放队列的行也能左滑删除了"),
        ChangelogItem(kind="修复", text="左滑删除那片纱的浓淡方向调回来了"),
    ]),
    ChangelogVersion(version="1.8.26", date="2026-09-19", items=[
        ChangelogItem(kind="改进", text="左滑删除那片纱靠近删除钮的一头改成全"
                                       "透"),
    ]),
    ChangelogVersion(version="1.8.25", date="2026-09-19", items=[
        ChangelogItem(kind="改进", text="左滑删除的遮罩不再发红, 换成行底色渐"
                                       "隐"),
        ChangelogItem(kind="改进", text="分享图标换成通用共享符号"),
    ]),
]
