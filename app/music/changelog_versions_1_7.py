"""1.7 系列的版本条目 (2026-09-16: 底部导航重排 + 分享链接)。
条目规矩: 用户视角, 一条一句话。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_7: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.7.2", date="2026-09-16", items=[
        ChangelogItem(kind="修复", text="资料库换页签翻列表时串页/空白的毛病"
                                       "修好了"),
        ChangelogItem(kind="修复", text="页顶黑带再垫高一些, 不再露糊边"),
        ChangelogItem(kind="改进", text="资料库的页签条和搜索框固定在顶端, 不"
                                       "跟着列表滚走"),
        ChangelogItem(kind="改进", text="底部页签的图标放大回来, 图标和文字上"
                                       "下居中"),
        ChangelogItem(kind="改进", text="资料库的「歌曲」页签撤了 (找歌用搜索"
                                       "更顺手)"),
        ChangelogItem(kind="修复", text="弱网下列表第一页没拉到不再误报「曲库"
                                       "还是空的」"),
    ]),
    ChangelogVersion(version="1.7.1", date="2026-09-16", items=[
        ChangelogItem(kind="修复", text="页顶黑带铺好, 滚进顶部的内容不再被栅"
                                       "糊"),
        ChangelogItem(kind="改进", text="底部页签栏再压矮一档 (图标小了一号)"),
        ChangelogItem(kind="改进", text="播放页的「待播放」列表四边留白和大封"
                                       "面同宽"),
        ChangelogItem(kind="改进", text="专辑名过长不再换行, 单行截断加省略号"),
        ChangelogItem(kind="改进", text="资料库歌曲行和曲目行的编号撤了, 换成"
                                       "封面缩略图"),
        ChangelogItem(kind="改进", text="封面图多存一层更牢的缓存, 看过的下次"
                                       "秒出"),
        ChangelogItem(kind="改进", text="资料库的语种筛选撤掉"),
    ]),
    ChangelogVersion(version="1.7.0", date="2026-09-16", items=[
        ChangelogItem(kind="修复", text="顶栏发糊治好了: 导航搬到屏幕底部, 内"
                                       "容从带子底下开始"),
        ChangelogItem(kind="修复", text="页顶磨砂带是苹果系统的 bug, 应用会识"
                                       "破谎报自己兜高度"),
        ChangelogItem(kind="修复", text="应用图标换回红底白音符 (主屏图标要删"
                                       "掉重加才换新)"),
        ChangelogItem(kind="修复", text="点「搜索」页签页面自己放大一圈的问题"
                                       "修掉了"),
        ChangelogItem(kind="修复", text="捏在底部页签栏上把整个页面捏大的问题"
                                       "修掉了"),
        ChangelogItem(kind="新增", text="歌曲和歌单能分享给任何人了, 链接 24 "
                                       "小时有效, 对方不用登录"),
        ChangelogItem(kind="新增", text="分享出去的页面有了完整播放页, 点封面"
                                       "还能看歌词"),
        ChangelogItem(kind="新增", text="分享链接发到微信, 聊天里能看到封面缩"
                                       "略图和标题"),
        ChangelogItem(kind="新增", text="「待播放」歌单照苹果音乐重排, 按住每"
                                       "行把手拖着换播放顺序"),
        ChangelogItem(kind="新增", text="播放列表里的歌支持左滑删除"),
        ChangelogItem(kind="新增", text="首页的播放列表也能左滑整列删除"),
        ChangelogItem(kind="改进", text="歌单详情页顶部的一排操作键全改成图标"
                                       "站同一行"),
        ChangelogItem(kind="修复", text="开着「待播放」歌单时拖横条关不上播放"
                                       "页的问题修好了"),
        ChangelogItem(kind="修复", text="边缘返回手势被左滑删除抢走、滑一半被"
                                       "弹回来的问题修好了"),
        ChangelogItem(kind="修复", text="进出专辑/艺人/列表时底部冒第二个播放"
                                       "气泡残影的问题修掉了"),
        ChangelogItem(kind="修复", text="点「随机播放」现在是真的随机起播"),
        ChangelogItem(kind="改进", text="顶栏和播放气泡彻底钉死, 滚列表/看歌词"
                                       "时纹丝不动"),
        ChangelogItem(kind="改进", text="整个应用就是一个网址了, 想返回在页面"
                                       "上往右划 (电脑按 Esc)"),
        ChangelogItem(kind="改进", text="专辑/播放列表这些里面页铺满整屏, 内容"
                                       "从气泡底下扫过"),
        ChangelogItem(kind="改进", text="播放页的小横条除了往下拖, 还能往右甩"
                                       "收起整页"),
        ChangelogItem(kind="改进", text="底部的播放气泡换成磨砂玻璃材质"),
        ChangelogItem(kind="改进", text="气泡上的播放/暂停键放大了一号"),
        ChangelogItem(kind="改进", text="电脑浏览器里整个应用都不显示滚动条"
                                       "了"),
        ChangelogItem(kind="改进", text="浏览器标签页的图标和主屏图标统一了"),
        ChangelogItem(kind="改进", text="随机/循环的状态和拖过的播放顺序, 关页"
                                       "面再进还记得"),
    ]),
]
