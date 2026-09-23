"""1.8 系列的版本条目 · 冻结段 1.8.17–1.8.18 (活跃文件 1.8.23 批又超
200 行硬上限, 第五次分家 —— 按仓里 1_0_to_1_3 / 1_4_to_1_6 的先例,
活跃段只留最新几版, 见 changelog.py 头注)。条目规矩: 用户视角, 一条
一句话。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8_17_TO_1_8_18: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.18", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="播放列表拖着换序, 其他歌会顺滑让位了"),
        ChangelogItem(kind="修复", text="进搜索页输入框不出现的问题修好了"),
        ChangelogItem(kind="改进", text="「添加到播放列表」弹层顶栏改成正在加"
                                       "的那首歌"),
        ChangelogItem(kind="改进", text="左滑出删除键时行尾的时长等小件一起让"
                                       "开, 只留歌名"),
        ChangelogItem(kind="改进", text="已下载页垃圾桶和多选并成右上角一对键, "
                                       "勾歌直接点封面"),
        ChangelogItem(kind="改进", text="分享页歌名和艺人分成两行, 长歌名不再撑"
                                       "爆行"),
        ChangelogItem(kind="改进", text="在设置/搜索的最左子页右划也能退出整个"
                                       "设置层了"),
    ]),
    ChangelogVersion(version="1.8.17", date="2026-09-18", items=[
        ChangelogItem(kind="修复", text="歌词放大偶尔跳行的毛病断根了"),
        ChangelogItem(kind="改进", text="歌词分工更清楚: 正在唱的放大, 马上要唱"
                                       "的清晰, 其余模糊"),
        ChangelogItem(kind="改进", text="分享页播放区改版: 切歌键挪到进度条上, "
                                       "封面左右滑也能切歌"),
        ChangelogItem(kind="改进", text="切到没歌词的歌不再强关歌词页, 垫一句"
                                       "「这首歌没有歌词」"),
        ChangelogItem(kind="改进", text="已下载页改用左滑删除, 「多选」搬到右上"
                                       "角"),
        ChangelogItem(kind="改进", text="设置页拆成通用/歌词/统计/更新四个横滑"
                                       "子页"),
        ChangelogItem(kind="改进", text="「添加到播放列表」选择单按最近用过排, "
                                       "顺手的在最前"),
        ChangelogItem(kind="改进", text="播放列表点名字就能改名, 按住行尾把手拖"
                                       "着换顺序"),
        ChangelogItem(kind="改进", text="搜索框挪到搜索页最顶上, 搜的词升作页"
                                       "标题, 点标题回来改词"),
        ChangelogItem(kind="改进", text="播放页撤掉「作曲」署名 (带「作词」的照"
                                       "旧)"),
        ChangelogItem(kind="改进", text="二级页大标题下移出系统模糊带, 左滑出"
                                       "删除时行尾箭头也藏掉了"),
    ]),
]
