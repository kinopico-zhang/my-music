"""1.0–1.3 系列的版本条目 (应用问世/搜索/下载/长按菜单)。
条目规矩: 用户视角, 一条一句话。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_0_TO_1_3: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.3.0", date="2026-09-15", items=[
        ChangelogItem(kind="新增", text="长按任意一首歌弹出菜单 (播放/进艺人"
                                       "主页/分享/加列表), 电脑上是右键"),
        ChangelogItem(kind="新增", text="添加到播放列表: 能选任何列表或当场新"
                                       "建一个"),
        ChangelogItem(kind="新增", text="「已下载」栏顶部多了统计行, 「全部删"
                                       "除」一键清空"),
        ChangelogItem(kind="改进", text="「已下载」栏每首歌行尾标着占多大, 哪"
                                       "首占地大一眼看出"),
        ChangelogItem(kind="改进", text="Plex 播放列表同步撤了, 播放列表全在"
                                       "应用里管"),
        ChangelogItem(kind="修复", text="播放界面几个控制键的图标歪、暂停切回"
                                       "播放会跳一下的问题摆正了"),
        ChangelogItem(kind="修复", text="下载中的歌点「删除」现在等于取消下"
                                       "载, 行和图标立即清掉"),
    ]),
    ChangelogVersion(version="1.2.1", date="2026-09-14", items=[
        ChangelogItem(kind="新增", text="在家里的 Wi-Fi 下也能离线下载了 (新地"
                                       "址全程加密)"),
        ChangelogItem(kind="改进", text="地址换成固定域名, 家里宽带 IP 变了也"
                                       "照常用"),
        ChangelogItem(kind="修复", text="账号密码改为全程加密过网, 新地址首次"
                                       "要重新登录"),
    ]),
    ChangelogVersion(version="1.2.0", date="2026-09-14", items=[
        ChangelogItem(kind="新增", text="主页: 打开应用先到这一页, 播放列表和"
                                       "最近播放都在这儿"),
        ChangelogItem(kind="新增", text="最近播放: 听过的歌自动记下来 (一家人"
                                       "各记各的)"),
        ChangelogItem(kind="新增", text="离线下载: 整首歌存进手机, 没网也能放"),
        ChangelogItem(kind="新增", text="播放页按 Apple Music 重排, 大封面居中"
                                       "更突出"),
        ChangelogItem(kind="新增", text="歌词页能自由滑动了, 滑开几秒后自动回"
                                       "到当前句"),
        ChangelogItem(kind="改进", text="资料库收窄成 专辑/艺人/歌曲/已下载 四"
                                       "栏, 找东西少翻一层"),
        ChangelogItem(kind="改进", text="下一首提前在后台备好, 接歌几乎无缝"),
        ChangelogItem(kind="改进", text="应用图标换成红色音符标 (重新添加主屏"
                                       "图标后生效)"),
        ChangelogItem(kind="修复", text="锁屏界面点歌曲封面会跳到别的应用的问"
                                       "题修好了"),
        ChangelogItem(kind="修复", text="页面底部偶尔冒出一排多余菜单按钮的问"
                                       "题修掉了"),
    ]),
    ChangelogVersion(version="1.1.0", date="2026-09-14", items=[
        ChangelogItem(kind="新增", text="搜索会认拼音, 打 liudehua 也能搜到刘"
                                       "德华"),
        ChangelogItem(kind="新增", text="简繁互搜, 打简体也搜得到繁体歌名"),
        ChangelogItem(kind="新增", text="Plex 里建的播放列表同步过来了"),
        ChangelogItem(kind="新增", text="每张专辑记下入库时间, 专辑页头多一行"
                                       "入库日期"),
        ChangelogItem(kind="改进", text="界面做减法: 底部标签栏撤掉, 搜索挪到"
                                       "顶栏放大镜"),
        ChangelogItem(kind="修复", text="动过文件的专辑不再被当成新添加冒到最"
                                       "前面"),
    ]),
    ChangelogVersion(version="1.0.0", date="2026-09-14", items=[
        ChangelogItem(kind="新增", text="My Music 问世: 扫描 NAS 曲库建索引, "
                                       "手机上直接串流播放"),
        ChangelogItem(kind="新增", text="播放器: 底部迷你条点开全屏播放页, 锁"
                                       "屏/控制中心能暂停切歌"),
        ChangelogItem(kind="新增", text="歌词: 逐行滚动唱到哪行哪行放大, 点任"
                                       "意一行跳到那句"),
        ChangelogItem(kind="新增", text="搜歌词: 只记得一句词也能找到那首歌"),
        ChangelogItem(kind="新增", text="按语种筛歌, 中文/日文/英文/韩文/俄文"
                                       "一键筛"),
        ChangelogItem(kind="新增", text="资料库按最近添加/专辑/艺人/歌曲四个角"
                                       "度逛曲库"),
        ChangelogItem(kind="新增", text="随机播放/列表循环/单曲循环, 播放队列面"
                                       "板能跳着选"),
        ChangelogItem(kind="新增", text="关掉浏览器再打开接着上次听的那首 (进"
                                       "度也记得)"),
        ChangelogItem(kind="新增", text="统计页: 曲库多少艺人/专辑/歌、各格式"
                                       "多少, 一眼看清"),
        ChangelogItem(kind="新增", text="更新日志页 (本页), 不再混在别的应用日"
                                       "志里"),
        ChangelogItem(kind="改进", text="My Home 门厅三个应用并排, 点卡片就进"),
        ChangelogItem(kind="修复", text="极少数老格式 (TAK/DSD/APE) 播不了的置"
                                       "灰标明, 点了有提示"),
        ChangelogItem(kind="修复", text="迷你条上的暂停/下一首不再误弹全屏播放"
                                       "页"),
        ChangelogItem(kind="修复", text="专辑页里点艺人名没反应的问题修好了"),
    ]),
]
