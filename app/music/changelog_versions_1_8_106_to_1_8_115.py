"""1.8 系列的版本条目 · 冻结段 1.8.106–1.8.115 (2026-10-26 活跃文件超 200
行硬上限第十四次分家, 见 changelog.py 头注)。条目规矩: 用户视角, 一条一句
话 (test_music_changelog 有断言把着)。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8_106_TO_1_8_115: Final[list[ChangelogVersion]] = [
ChangelogVersion(version="1.8.115", date="2026-09-29", items=[
    ChangelogItem(kind="改进", text="单曲循环键的「1」徽章从环心挪到 logo 右"
                                   "上角 (圆片盖住折角箭头, 顶杆顺势流入, iOS"
                                   " 角标款)。"),
]),
ChangelogVersion(version="1.8.114", date="2026-09-29", items=[
    ChangelogItem(kind="修复", text="上划收起封面后长专辑名的头一行与艺人名"
                                   "左对齐 (换行的长标题字居中排在标题框"
                                   "里, 原先对的是框不是字, 开头看着空着一"
                                   "小截)。"),
]),
ChangelogVersion(version="1.8.113", date="2026-09-29", items=[
    ChangelogItem(kind="修复", text="上划收起封面时标题和艺人名一开头就左"
                                   "对齐 (原先整个收缩过程两行都还错着一"
                                   "点, 标题看着像前面空了一格)。"),
]),
ChangelogVersion(version="1.8.112", date="2026-09-29", items=[
    ChangelogItem(kind="修复", text="上划收起封面的过程中标题和艺人名一路左"
                                   "对齐 (原先收缩途中两行一直错着, 到顶才"
                                   "对齐)。"),
    ChangelogItem(kind="改进", text="长标题收进顶栏不再缩成小字, 放不下的部"
                                   "分在按钮旁边淡掉。"),
]),
ChangelogVersion(version="1.8.111", date="2026-09-28", items=[
        ChangelogItem(kind="改进", text="随机播放和循环键换了实底新图标 —— "
                                       "列表循环/单曲循环/随机三态和随机播"
                                       "放键同一批换装, 单曲循环的「1」徽章"
                                       "收进环心, 切换循环模式时环纹丝不动"),
    ]),
    ChangelogVersion(version="1.8.110", date="2026-09-28", items=[
        ChangelogItem(kind="改进", text="所有删除都加了二次确认 —— 左滑"
                                       "的红色删除按钮点下去会先问一句 (删哪"
                                       "个列表/哪首歌都点名道姓), 确认了才"
                                       "真删, 反悔了按钮自己缩回去"),
    ]),
    ChangelogVersion(version="1.8.109", date="2026-09-28", items=[
        ChangelogItem(kind="修复", text="修了电脑大屏上菜单弹层离菜单键老"
                                       "远 —— 之前钉死在屏幕左下角, 现在从"
                                       "菜单键正上方长出来"),
    ]),
    ChangelogVersion(version="1.8.108", date="2026-09-28", items=[
        ChangelogItem(kind="改进", text="电脑上播放列表的曲目直接按住鼠标拖"
                                       "动就能换顺序 —— 不用再长按等待, 手机"
                                       "触屏上照旧按住一小会儿再拖"),
    ]),
    ChangelogVersion(version="1.8.107", date="2026-09-28", items=[
        ChangelogItem(kind="修复", text="修电脑上来回切换页面后画中画小窗不"
                                       "再出现 —— Chrome 只许刚点过页面时开"
                                       "窗, 收了就弹不回来; 小窗改长驻 (回到"
                                       "播放页不再自动收), 不想要就点它自己"
                                       "的 ✕, 关过这一页就不会再自动弹"),
    ]),
    ChangelogVersion(version="1.8.106", date="2026-09-28", items=[
        ChangelogItem(kind="改进", text="电脑上播放页的音量条两端加了小/大喇"
                                       "叭图标标明这是音量, 条子也缩短到和进"
                                       "度条一样长 (正好落在进度条正下方)"),
        ChangelogItem(kind="改进", text="电脑 Chrome 的画中画小窗改成自动的"
                                       " —— 播放中切去别的窗口小窗自己弹出"
                                       "来, 回到播放页自己收掉, 底排的画中"
                                       "画按钮撤了 (还是三颗键)"),
    ]),
]
