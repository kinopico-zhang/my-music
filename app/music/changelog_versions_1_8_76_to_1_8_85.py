"""1.8 系列的版本条目 · 冻结段 1.8.76–1.8.85 (2026-09-28 活跃文件超 200
行硬上限第十一次分家, 见 changelog.py 头注)。条目规矩: 用户视角, 一条一句
话 (test_music_changelog 有断言把着)。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8_76_TO_1_8_85: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.85", date="2026-09-24", items=[
        ChangelogItem(kind="修复", text="被别的 app 的视频打断后, 控制中"
                                       "心点暂停再点播放, 进度条走了却没"
                                       "声音的问题也修了 —— 那种情况下播"
                                       "放器内部其实还卡在「幽灵播放」状"
                                       "态, 现在能识别出来, 再点一次播放"
                                       "就能真正出声"),
    ]),
    ChangelogVersion(version="1.8.84", date="2026-09-24", items=[
        ChangelogItem(kind="修复", text="看完别的 app 的视频后, 锁屏点播"
                                       "放没反应的问题修了 —— 被夺走声音"
                                       "后播放键一被拒就再没下文, 现在"
                                       "会自动换一种方式重试一下; 仍然只"
                                       "在你明确点播放时才出声, 不会自己"
                                       "恢复播放去打断别的 app"),
    ]),
    ChangelogVersion(version="1.8.83", date="2026-09-24", items=[
        ChangelogItem(kind="修复", text="播放列表放着放着就停 (放完一"
                                       "首不续) 的问题修好了 —— 后台每 5"
                                       "分钟自动扫描曲库会把数据库压出"
                                       "成片故障, 下一首加载失败连跳到"
                                       "头; 自动扫描撤了, 数据库也加固"
                                       "了 (临时文件挪去大硬盘、读写不再"
                                       "互相挡、锁等待加到 30 秒)"),
        ChangelogItem(kind="修复", text="切到别的 app 看视频会被这边自"
                                       "动恢复的音乐打断的问题也修了 —"
                                       "— 歌曲被打断后不再自动续播, 想"
                                       "接着播自己点一下 (锁屏键或回 "
                                       "app 点播放)"),
        ChangelogItem(kind="改进", text="曲库不再自动扫描, 全部手动 —"
                                       "— 新加的音乐文件在设置里点「重"
                                       "新扫描曲库」扫进来"),
    ]),
    ChangelogVersion(version="1.8.82", date="2026-09-23", items=[
        ChangelogItem(kind="修复", text="部分新加的专辑不显示封面的问题修好"
                                       "了 —— 文件标签里的封面数据写歪时"
                                       "(图前头混着文件名), 现在能自动剥掉"
                                       "只留图, 剥不出图的按没有封面算"),
        ChangelogItem(kind="修复", text="换过音乐文件后手机上专辑封面一直是"
                                       "旧图的问题也修了 —— 封面地址的版本"
                                       "号改成跟文件内容走, 换完文件扫一遍"
                                       "库就能看到新封面"),
    ]),
    ChangelogVersion(version="1.8.81", date="2026-09-23", items=[
        ChangelogItem(kind="改进", text="主页「最近添加专辑」点查看全部进去, "
                                       "专辑按添加时间倒排 (最新在前), 不再按"
                                       "字母排; 菜单「所有专辑」进去照旧"),
    ]),
    ChangelogVersion(version="1.8.80", date="2026-09-23", items=[
        ChangelogItem(kind="修复", text="删除播放列表后回主页, 主页不再"
                                       "还留着它 (列表页左滑删和详情页删"
                                       "两条路都算)"),
    ]),
    ChangelogVersion(version="1.8.79", date="2026-09-23", items=[
        ChangelogItem(kind="修复", text="新建播放列表连点几下不再连环报"
                                       "「没建起来」—— 之前第一下其实已建成, "
                                       "后面几下全是撞名报错把成功的盖成失败"),
    ]),
    ChangelogVersion(version="1.8.78", date="2026-09-23", items=[
        ChangelogItem(kind="修复", text="来电或微信语音打断播放后, 音乐会在"
                                       "打断结束后自动接着播, 锁屏控制也跟着"
                                       "回来, 不用再打开应用点播放"),
    ]),
    ChangelogVersion(version="1.8.77", date="2026-09-23", items=[
        ChangelogItem(kind="新增", text="播放时自动把下一曲缓存到手机 "
                                       "(上限 2GB, 满了自动清最久没听的), "
                                       "切歌几乎不等加载"),
        ChangelogItem(kind="改进", text="已下载页统计行能看到自动缓存占用"
                                       "了多少, 和手动下载分栏算"),
    ]),
    ChangelogVersion(version="1.8.76", date="2026-09-23", items=[
        ChangelogItem(kind="修复", text="锁屏和后台连播更稳: 切歌不再多等"
                                       "一步读缓存, 音频源当场落定"),
        ChangelogItem(kind="修复", text="歌单里夹着手机播不了的格式 "
                                       "(如 tak/dsf/ape) 时自动跳过接着播, "
                                       "不再连播到那就停住"),
        ChangelogItem(kind="修复", text="在线流播挂了不再停在半路: 先试本地"
                                       "缓存救回原位置接着放, 不行自动续下"
                                       "一首, 连挂三首才停"),
    ]),
]
