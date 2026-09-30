"""1.8 系列的版本条目 · 冻结段 1.8.96–1.8.105 (2026-09-30 活跃文件超 200
行硬上限第十三次分家, 见 changelog.py 头注)。条目规矩: 用户视角, 一条一句
话 (test_music_changelog 有断言把着)。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8_96_TO_1_8_105: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.105", date="2026-09-28", items=[
        ChangelogItem(kind="新增", text="电脑 Chrome 播放页多了画中画键 —— 点开"
                                       "弹一枚总在最前的小窗 (封面/歌名/进度/"
                                       "上下曲/播停), 最小化网页或切去干别的"
                                       "活也能遥控着听; 不支持的浏览器不显示"
                                       "这颗键, 手机触屏端照旧没有"),
    ]),
    ChangelogVersion(version="1.8.104", date="2026-09-28", items=[
        ChangelogItem(kind="改进", text="电脑上播放页的音量条挪到了歌名下方、"
                                       "播放按钮上方, 加长到和进度条一样长 —— "
                                       "原先挤在底部一排的角落里, 太短不好拖"),
        ChangelogItem(kind="改进", text="电脑上鼠标扫过播放列表不再每一行都弹"
                                       "出红色删除按钮了 —— 现在在歌曲上停住"
                                       "半秒才会出现, 一扫而过只亮行背景"),
    ]),
    ChangelogVersion(version="1.8.103", date="2026-09-28", items=[
        ChangelogItem(kind="新增", text="电脑上底部多了一颗音量键 —— 点开在键"
                                       "上方弹出小气泡, 拖滑杆直接调音量, 与播"
                                       "放页音量条和上下方向键三处同源, 手机上"
                                       "不出现 (音量归系统硬件键)"),
        ChangelogItem(kind="改进", text="电脑等大屏上内容不再挤在手机宽度里 —— "
                                       "版面随屏幕加宽, 专辑格更大更饱满"),
        ChangelogItem(kind="改进", text="页面改为按「屏幕大小」和「键鼠/触摸」"
                                       "两条线分开适配 —— 电脑上列表行距收紧一"
                                       "屏多放几行, 之后给电脑加的键鼠优化都不"
                                       "会再波及手机触屏体验"),
    ]),
    ChangelogVersion(version="1.8.102", date="2026-09-28", items=[
        ChangelogItem(kind="修复", text="电脑上打开补齐了键鼠手感 —— 之前点"
                                       "过一次按钮后空格和方向键就全没反应了, "
                                       "现在左右方向键直接快退快进 10 秒, "
                                       "上下调音量 (播放页也加了音量条), 切歌"
                                       "用 Shift 加左右方向键, 音量记住上次"
                                       "调好的"),
    ]),
    ChangelogVersion(version="1.8.101", date="2026-09-28", items=[
        ChangelogItem(kind="修复", text="手机系统悄悄清掉的缓存不再被当成还"
                                       "在 —— 之前索引记着「都缓存好了」, "
                                       "放到那首才发现字节没了、整首重新走"
                                       "流量, 现在回到应用就当场对账出清, "
                                       "并申请把存储固定住不被系统清理, 手"
                                       "机存储吃紧时缓存上限也跟着收紧"),
    ]),
    ChangelogVersion(version="1.8.100", date="2026-09-27", items=[
        ChangelogItem(kind="修复", text="后台连播第二首开始没声音、锁屏进度"
                                       "却还在走, 过一阵锁屏连播放卡片都没"
                                       "了的问题修了 —— 现在趁上一首还响着"
                                       "就把下一首接上, 手机系统冻不住页面"),
    ]),
    ChangelogVersion(version="1.8.99", date="2026-09-27", items=[
        ChangelogItem(kind="修复", text="换了播放列表封面后, 回到所有播放"
                                       "列表页和主页看到的还是旧图的问题修了"
                                       " —— 现在设完封面, 底下的列表当场"
                                       "换上新图, 撤掉封面也一样"),
    ]),
    ChangelogVersion(version="1.8.98", date="2026-09-26", items=[
        ChangelogItem(kind="修复", text="服务器修过的歌手机也认账了 —— 之前音频"
                                       "文件在服务器换新, 手机自动缓存里的旧字节"
                                       "还压着不放, 现在缓存换代自动清旧重新拉"),
    ]),
    ChangelogVersion(version="1.8.97", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="播放页封面轻轻一划也能切歌了 —— 之前"
                                       "要划过小半张封面或甩得够快才切, 滑得短"
                                       "了会被当成没划够放回原位"),
    ]),
    ChangelogVersion(version="1.8.96", date="2026-09-25", items=[
        ChangelogItem(kind="修复", text="修了播放气泡还没滑动就露出下一首封面"
                                       "窄条的问题"),
        ChangelogItem(kind="改进", text="气泡左右滑只管切歌了 —— 第一首往右划、"
                                       "最后一首往左划是拖不动的橡皮筋, 不会再把"
                                       "底下的页面划走退出去"),
        ChangelogItem(kind="改进", text="网络不好歌加载不出来时不再自动跳过这首"
                                       "了 —— 会自己试着把这首加载出来, 想跳过"
                                       "自己划或自己点"),
    ]),
]
