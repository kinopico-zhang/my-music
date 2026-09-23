"""1.4–1.6 系列的版本条目 (设置页/联网补歌词/自定义封面/队列重排)。
条目规矩: 用户视角, 一条一句话。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_4_TO_1_6: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.6.0", date="2026-09-15", items=[
        ChangelogItem(kind="新增", text="播放队列改成封面原地翻开的歌单, 顶上"
                                       "带随机/循环两枚键"),
        ChangelogItem(kind="新增", text="播放页能用苹果的返回手势收起了 (下拉"
                                       "收起照旧)"),
        ChangelogItem(kind="新增", text="专辑/列表页加了「下载全部」, 一首下完"
                                       "自动接下一首"),
        ChangelogItem(kind="改进", text="更新日志挪进应用里, 看日志不再打断正在"
                                       "听的歌"),
        ChangelogItem(kind="改进", text="底部播放气泡补齐了「上一首」"),
        ChangelogItem(kind="改进", text="上一首/播放/下一首三键站到进度条正上"
                                       "方, 三键一般大"),
        ChangelogItem(kind="修复", text="歌名特别长时弹出的菜单不再被撑得跟屏"
                                       "幕一样宽"),
    ]),
    ChangelogVersion(version="1.5.1", date="2026-09-15", items=[
        ChangelogItem(kind="修复", text="收放太快赶在同一瞬间会卡住的问题修掉"
                                       "了"),
        ChangelogItem(kind="修复", text="长按弹出菜单后, 苹果手机抬手补的那一"
                                       "下点击不再误触正下方的歌"),
        ChangelogItem(kind="修复", text="苹果手机上播放页的进度条点不准、拖不"
                                       "动的问题修好了"),
        ChangelogItem(kind="修复", text="应用内音量条收掉了, 音量统一交给设备"
                                       "的音量键"),
        ChangelogItem(kind="修复", text="封面左右划切歌后封面不再消失"),
        ChangelogItem(kind="修复", text="有时点歌会从一半开始播 (续听进度串了"
                                       "歌) 的问题修好了"),
        ChangelogItem(kind="修复", text="播放列表不再出现重复的歌, 现存的重复"
                                       "也清干净了"),
        ChangelogItem(kind="改进", text="上一首/播放/下一首三键挪到时间进度条"
                                       "那一行, 和下排三键分成两拨"),
        ChangelogItem(kind="改进", text="进专辑/艺人/列表页改成从右边滑进来, "
                                       "跟苹果系统一个手感"),
        ChangelogItem(kind="改进", text="顶栏归成一行: 主页/资料库/搜索三页签 "
                                       "+ 右侧一枚菜单钮"),
        ChangelogItem(kind="新增", text="播放页的封面左右划切歌, 没拖够就松手"
                                       "会弹回去不误切"),
        ChangelogItem(kind="改进", text="主页「最近播放」每行都带上歌自己的封"
                                       "面"),
        ChangelogItem(kind="改进", text="列表行尾的「词」字换成小引号图标, 和"
                                       "播放页歌词键同款"),
        ChangelogItem(kind="改进", text="「已下载」栏每行也带上歌自己的封面了"),
        ChangelogItem(kind="改进", text="歌词页的模糊按远近分级, 自己滑动浏览"
                                       "时整页清晰"),
        ChangelogItem(kind="修复", text="续听的没词的歌「歌词」键打开应用就直"
                                       "接灰掉"),
        ChangelogItem(kind="改进", text="联网补歌词求不到的歌, 一天内不再每次"
                                       "播放都白跑网络"),
        ChangelogItem(kind="改进", text="顶部菜单和各处下拉菜单, 点页面别处就"
                                       "收起"),
        ChangelogItem(kind="改进", text="队列键角上的无损小钻石标撤掉了"),
    ]),
    ChangelogVersion(version="1.5.0", date="2026-09-15", items=[
        ChangelogItem(kind="新增", text="点开歌曲后的整页播放界面重做了, 封面"
                                       "居中 + 背景晕开封面色"),
        ChangelogItem(kind="新增", text="播放页能调音量了, 拖过一次就记住"),
        ChangelogItem(kind="新增", text="无损格式的歌在队列键角上带一颗小钻石"
                                       "标, 播放页底多一行作词/作曲"),
        ChangelogItem(kind="新增", text="播放页加了 ⋯ 菜单 (艺人主页/分享/加"
                                       "列表), ♥ 键也搬到底部"),
        ChangelogItem(kind="改进", text="随机和循环两键挪进「队列」面板, 播放"
                                       "页只留三颗常用键"),
    ]),
    ChangelogVersion(version="1.4.1", date="2026-09-15", items=[
        ChangelogItem(kind="修复", text="长按菜单第一次点不灵、要再点一下才生"
                                       "效的问题修好了"),
        ChangelogItem(kind="修复", text="mp3 等格式歌曲自带的封面裂图修好了"),
        ChangelogItem(kind="修复", text="锁屏和控制中心上的播放进度对不上的问"
                                       "题修好了, 每动一下都同步"),
        ChangelogItem(kind="修复", text="搜索结果页能左右滑动、播放条跟着晃的"
                                       "问题修掉了"),
        ChangelogItem(kind="改进", text="播放列表的大封面点一下就能换图, 长按"
                                       "弹菜单能移除"),
        ChangelogItem(kind="改进", text="搜索框下面的语种筛选去掉, 搜什么语种"
                                       "都能搜出来"),
        ChangelogItem(kind="改进", text="应用图标换成唱片标 (红底白唱片)"),
        ChangelogItem(kind="改进", text="设置页普通账号也能看了 (只读), 改还是"
                                       "要管理员"),
        ChangelogItem(kind="改进", text="播放控制键换了新图标, 和应用图标同一"
                                       "套设计"),
        ChangelogItem(kind="修复", text="播放列表里正在播的那首封面不再消失"),
    ]),
    ChangelogVersion(version="1.4.0", date="2026-09-15", items=[
        ChangelogItem(kind="新增", text="播放列表能换自定义封面了 (PNG/JPG/"
                                       "WebP)"),
        ChangelogItem(kind="新增", text="设置页能改音乐库目录、开关「联网补歌"
                                       "词」(管理员)"),
        ChangelogItem(kind="新增", text="联网补歌词: 没词的歌第一次播放上网求"
                                       "一遍, 求到写回曲库"),
        ChangelogItem(kind="新增", text="每月蜂窝流量记账, 耗了多少自动记在设"
                                       "置页里"),
        ChangelogItem(kind="新增", text="播放列表里每首歌带上自带的封面, 没有"
                                       "的给音符占位"),
        ChangelogItem(kind="改进", text="曲库自动增量扫描, 新拷进来的专辑过一"
                                       "会儿自动出现"),
        ChangelogItem(kind="改进", text="播放界面的控制键照 Apple Music 重新设"
                                       "计"),
        ChangelogItem(kind="改进", text="歌词页正在唱的一句放大变清晰, 滚动换"
                                       "成丝滑动画"),
        ChangelogItem(kind="改进", text="菜单顶部显示当前登录的账号"),
    ]),
]
