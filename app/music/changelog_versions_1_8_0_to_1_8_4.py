"""1.8 系列后半的版本条目 (1.8.0–1.8.4, 冻结段)。2026-09-18 从
changelog_versions_1_8.py 分出: 1.8 一整线塞一个文件超了 200 行的硬上限
(CI pylint 揪的), 按仓里 1_0_to_1_3 / 1_4_to_1_6 的先例分家; 活跃段
(1.8.5 起) 留在原文件。条目规矩: 用户视角, 一条一句话。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8_0_TO_1_8_4: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.4", date="2026-09-17", items=[
        ChangelogItem(kind="新增", text="断网也能翻播放列表/专辑/艺人这些页了 "
                                       "(联网打开过一次就行)"),
        ChangelogItem(kind="改进", text="换账号不串号, 登录失效或退出登录时离"
                                       "线数据自动清空"),
    ]),
    ChangelogVersion(version="1.8.3", date="2026-09-17", items=[
        ChangelogItem(kind="新增", text="打开应用自动回到上次停的那页"),
        ChangelogItem(kind="改进", text="搜索页重排, 输入框挪到底部, 键盘盖上来"
                                       "时自动抬到键盘上沿"),
        ChangelogItem(kind="改进", text="搜索结果分成歌曲/艺人/专辑/歌词四个横"
                                       "滑子页"),
        ChangelogItem(kind="改进", text="搜索结果的歌曲行带上封面了"),
        ChangelogItem(kind="改进", text="底部的播放气泡和两颗圆键调实了一档"),
    ]),
    ChangelogVersion(version="1.8.2", date="2026-09-17", items=[
        ChangelogItem(kind="修复", text="播放页点「进入艺人主页」没反应修好了"),
        ChangelogItem(kind="新增", text="播放页的弹出菜单加了「进入专辑主页」"),
        ChangelogItem(kind="改进", text="播放页下拉收起的命中范围扩到整页"),
        ChangelogItem(kind="改进", text="播放页的专辑名并到艺人名后面, 省出一"
                                       "行空间"),
        ChangelogItem(kind="改进", text="分享页有歌词的歌直接在封面下跟着唱句"
                                       "滚动"),
        ChangelogItem(kind="改进", text="下载进度从百分比文字换成越画越满的圆"
                                       "环"),
    ]),
    ChangelogVersion(version="1.8.1", date="2026-09-17", items=[
        ChangelogItem(kind="新增", text="菜单里加了「最近播放」, 整页听歌记录带"
                                       "每首播过几次"),
        ChangelogItem(kind="改进", text="底部那块空黑区填上了内容, 列表一路铺"
                                       "到三件套底下"),
        ChangelogItem(kind="改进", text="搜索页输入框往下挪, 播放页的抓手也挪"
                                       "出系统磨砂带"),
        ChangelogItem(kind="修复", text="二级页滑进滑出时气泡和圆键不再像透明"
                                       "度在跳"),
        ChangelogItem(kind="改进", text="菜单图标换批: 专辑换回资料库盒、艺人"
                                       "换成三人像"),
    ]),
    ChangelogVersion(version="1.8.0", date="2026-09-17", items=[
        ChangelogItem(kind="新增", text="底部导航重做成三件套: 菜单键/播放气泡/"
                                       "搜索键"),
        ChangelogItem(kind="改进", text="播放气泡收窄了, 长歌名会跑马灯滚动着"
                                       "播"),
        ChangelogItem(kind="改进", text="资料库拆成专辑/艺人/已下载独立页, 首"
                                       "页成了唯一首屏"),
        ChangelogItem(kind="改进", text="点搜索键直接进搜索页, 键盘自动弹出来"),
        ChangelogItem(kind="改进", text="页顶的黑带遮罩撤掉了, 顶部让位交给系"
                                       "统"),
        ChangelogItem(kind="修复", text="下载中/删除在已下载页里即时反映了"),
    ]),
]
