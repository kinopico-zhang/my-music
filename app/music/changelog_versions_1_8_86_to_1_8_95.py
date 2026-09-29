"""1.8 系列的版本条目 · 冻结段 1.8.86–1.8.95 (2026-09-29 活跃文件超 200
行硬上限第十二次分家, 见 changelog.py 头注)。条目规矩: 用户视角, 一条一句
话 (test_music_changelog 有断言把着)。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8_86_TO_1_8_95: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.95", date="2026-09-25", items=[
        ChangelogItem(kind="修复", text="修了滑动气泡切歌时封面不跟着换的问题 —— "
                                       "现在手指拖到哪, 相邻那首的封面歌名就跟着"
                                       "从两侧滑进来提前看到, 松手顺势滑满一整张"
                                       "换曲, 新封面无缝接上"),
    ]),
    ChangelogVersion(version="1.8.94", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="播放气泡的上一首/下一首键撤了, 换成左右"
                                       "滑动气泡切歌 —— 封面和歌名跟着手指走, "
                                       "松手顺势滑出、新歌从另一侧滑进来"),
    ]),
    ChangelogVersion(version="1.8.93", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="播放气泡的上一首/下一首图标裁成单个"
                                       "三角形, 三颗按键也收得更紧凑"),
    ]),
    ChangelogVersion(version="1.8.92", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="单曲循环图标里的 \"1\" 缩小了一号, "
                                       "环里留白回来不再发胀"),
        ChangelogItem(kind="改进", text="播放页的气泡提示挪到封面和标题之间, "
                                       "不再盖住歌名"),
    ]),
    ChangelogVersion(version="1.8.91", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="循环模式键的图标缩小一号跟旁边的按键"
                                       "看齐, 线条交叉处不再叠出深色斑点"),
        ChangelogItem(kind="改进", text="循环模式的气泡提示挪到标题行上, "
                                       "整屏居中, 不再压着底部的播放按键"),
    ]),
    ChangelogVersion(version="1.8.90", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="循环模式键的三态图标线条加粗 —— "
                                       "列表/单曲/随机都换成粗描边画法, "
                                       "和旁边按键看着一样有分量"),
    ]),
    ChangelogVersion(version="1.8.89", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="播放页底行的加列表键换成循环模式键 —— "
                                       "点一下在列表循环、单曲循环、随机循环间"
                                       "轮换并气泡报当前模式, 加列表还在 ⋯ 菜单"
                                       "里, 待播放列表头的两枚循环键撤了"),
    ]),
    ChangelogVersion(version="1.8.88", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="播放气泡加回上一首/下一首键 —— "
                                       "路上想切歌不用进全屏页, 点封面文字"
                                       "照旧进全屏页"),
    ]),
    ChangelogVersion(version="1.8.87", date="2026-09-24", items=[
        ChangelogItem(kind="修复", text="开车路上信号断续时连播不再停摆 —— "
                                       "断网挂起的歌就地等信号, 一回到应用"
                                       "就自动接着放, 不跳歌"),
        ChangelogItem(kind="修复", text="缓存到本地的歌也偶发卡在暂停态 —— "
                                       "换用本地缓存源的一瞬把正在起播的请"
                                       "求掐断了, 换完没人再把播放下达回来, "
                                       "现在换完源自己接着放"),
        ChangelogItem(kind="改进", text="连跳 3 首停住只对歌本身坏 (解码不"
                                       "了) 生效 —— 网络断的问题不再跳歌计数"),
    ]),
    ChangelogVersion(version="1.8.86", date="2026-09-24", items=[
        ChangelogItem(kind="修复", text="看长视频回来后, 播放器卡在「看着"
                                       "在播其实没声」的假播放状态 —— 现在"
                                       "一回到应用就会自动纠正, 点一下播放"
                                       "键就从原位置接着听"),
        ChangelogItem(kind="改进", text="看过长视频后控制中心的按钮可能叫"
                                       "不动播放器 —— 那时应用已被系统冻"
                                       "结 (网页应用的限制), 先回到应用点一"
                                       "下就好; 短暂打断不受影响"),
    ]),
]
