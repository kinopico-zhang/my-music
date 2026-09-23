"""1.8 系列的版本条目 · 冻结段 1.8.40–1.8.58 (2026-09-23 活跃段又超 200 行
硬上限, 按仓里先例把老段搬出去)。条目规矩: 用户视角, 一条一句话。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8_40_TO_1_8_58: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.58", date="2026-09-21", items=[
        ChangelogItem(kind="修复", text="继续播放列表里正在播的那首, 封面"
                                       "上的跳动动画终于亮出来了"),
    ]),
    ChangelogVersion(version="1.8.57", date="2026-09-21", items=[
        ChangelogItem(kind="新增", text="设置里能改自己的账号名和密码了"),
        ChangelogItem(kind="改进", text="联网补歌词能挑厂商了, 自动会按网"
                                       "易云、QQ、LRCLIB 依次试"),
        ChangelogItem(kind="改进", text="普通账号的设置页不再显示曲库和歌词"
                                       "那些管理员配置"),
    ]),
    ChangelogVersion(version="1.8.56", date="2026-09-21", items=[
        ChangelogItem(kind="改进", text="收进顶栏的换行标题不再缩成小字, 放"
                                       "不下的尾字自动淡出"),
    ]),
    ChangelogVersion(version="1.8.55", date="2026-09-21", items=[
        ChangelogItem(kind="改进", text="标题太长换行的专辑/播放列表, 收进顶"
                                       "栏后只留第一行"),
    ]),
    ChangelogVersion(version="1.8.54", date="2026-09-21", items=[
        ChangelogItem(kind="改进", text="排行榜每行左边带上歌曲封面了"),
    ]),
    ChangelogVersion(version="1.8.53", date="2026-09-21", items=[
        ChangelogItem(kind="修复", text="打开播放页偶尔在封面页上见到「回到当"
                                       "前句」的问题修好了"),
    ]),
    ChangelogVersion(version="1.8.52", date="2026-09-21", items=[
        ChangelogItem(kind="改进", text="按压的 Q 弹只留列表页的操作键和收起后"
                                       "的顶栏键"),
    ]),
    ChangelogVersion(version="1.8.51", date="2026-09-21", items=[
        ChangelogItem(kind="修复", text="收拢顶栏的播放键按下时不再闪一下了"),
    ]),
    ChangelogVersion(version="1.8.50", date="2026-09-21", items=[
        ChangelogItem(kind="改进", text="「下载全部」进行中会变成取消键, 点一"
                                       "下整批停止, 已下好的保留"),
    ]),
    ChangelogVersion(version="1.8.49", date="2026-09-21", items=[
        ChangelogItem(kind="修复", text="按播放键时毛玻璃界面不再跟着闪一下了"),
    ]),
    ChangelogVersion(version="1.8.48", date="2026-09-21", items=[
        ChangelogItem(kind="改进", text="按钮按下有了轻轻压扁再弹回的 Q 弹反馈"),
    ]),
    ChangelogVersion(version="1.8.47", date="2026-09-21", items=[
        ChangelogItem(kind="修复", text="分享到微信等系统分享面板时, 顶上能看"
                                       "到封面了"),
    ]),
    ChangelogVersion(version="1.8.46", date="2026-09-21", items=[
        ChangelogItem(kind="修复", text="收进顶栏的按钮飞行时不再两两叠在一起"),
        ChangelogItem(kind="改进", text="点开 … 出来的那排键间距排匀了"),
        ChangelogItem(kind="改进", text="按钮飞进顶栏的动画顺滑不再掉帧"),
        ChangelogItem(kind="改进", text="点开 … 时没被按钮压到的标题不再被误"
                                       "淡化"),
        ChangelogItem(kind="修复", text="列表滑动的余势里点收拢顶栏的 播放/… "
                                       "立即有响应了"),
    ]),
    ChangelogVersion(version="1.8.45", date="2026-09-20", items=[
        ChangelogItem(kind="改进", text="收缩顶栏改成单行, 播放和 … 两颗键上到"
                                       "封面同一行"),
    ]),
    ChangelogVersion(version="1.8.44", date="2026-09-20", items=[
        ChangelogItem(kind="改进", text="试着修蓝牙车机上不显示封面 (效果要上"
                                       "车才知道)"),
    ]),
    ChangelogVersion(version="1.8.43", date="2026-09-20", items=[
        ChangelogItem(kind="改进", text="出问题时不再弹红框提示, 修复照旧自动"
                                       "完成"),
    ]),
    ChangelogVersion(version="1.8.42", date="2026-09-20", items=[
        ChangelogItem(kind="改进", text="顶栏收缩后标题和副标题改成左对齐"),
    ]),
    ChangelogVersion(version="1.8.41", date="2026-09-20", items=[
        ChangelogItem(kind="修复", text="双指捏合再也不能放大整个应用了"),
        ChangelogItem(kind="改进", text="分享页的歌单列表行换上歌曲封面, 和应"
                                       "用里同款"),
    ]),
    ChangelogVersion(version="1.8.40", date="2026-09-20", items=[
        ChangelogItem(kind="修复", text="往上划页面时整层不再左右晃"),
        ChangelogItem(kind="改进", text="收缩顶栏改成两行, 文字和按键分上下排"
                                       "开"),
        ChangelogItem(kind="修复", text="列表特别短的页, 上划的收拢动画不再中"
                                       "途停住"),
    ]),
]
