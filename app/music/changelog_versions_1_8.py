"""1.8 系列的版本条目 · 活跃段 (1.8.76 起, 新的 1.8.x 补丁版加在文件顶上)。
更老的 1.8 线全部冻结分家 (1.8.67–1.8.75 / 1.8.59–1.8.66 / 1.8.40–1.8.58 /
1.8.33–1.8.39 / … / 1.8.0–1.8.4 十一个数据文件, 当年一整线塞一个文件超 200
行硬上限, 分了十次家)。条目规矩: 用户视角, 一条一句话 (test_music_changelog
有断言把着)。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8: Final[list[ChangelogVersion]] = [
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
