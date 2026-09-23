"""My Music 更新日志数据: 每个版本 = 一批改动的合并, 文案站在使用者视角,
一条一句话 (2026-09-21 用户定的规矩, test_music_changelog 有断言把着)。

不逐提交记版本 (一个版本可以同时含多个修复和多个功能); 版本号 x.y.z ——
x 大改版 · y 新功能 · z 问题修复, 新批次加在最上面 (新→老)。
听歌应用自己的版本线 (2026-09-14 起与 My Tesla 的更新日志各自独立)。
条目按版本段分家: 1.8 前段 (1.8.59 起, 活跃) / 1.8.40–1.8.58 / 1.8.33–1.8.39 /
1.8.25–1.8.32 / 1.8.19–1.8.24 / 1.8.17–1.8.18 / 1.8 中段 (1.8.14–1.8.16、1.8.10–1.8.13 和
1.8.5–1.8.9 三段) / 1.8 后半 (1.8.0–1.8.4) / 1.7 / 1.4–1.6 / 1.0–1.3 各一
个数据文件 (1.8 线 2026-09-18/19/20/23 超重拆了八次)。
"""
from typing import Final

from ..schemas import ChangelogVersion
from .changelog_versions_1_0_to_1_3 import VERSIONS_1_0_TO_1_3
from .changelog_versions_1_4_to_1_6 import VERSIONS_1_4_TO_1_6
from .changelog_versions_1_7 import VERSIONS_1_7
from .changelog_versions_1_8 import VERSIONS_1_8
from .changelog_versions_1_8_40_to_1_8_58 import VERSIONS_1_8_40_TO_1_8_58
from .changelog_versions_1_8_33_to_1_8_39 import VERSIONS_1_8_33_TO_1_8_39
from .changelog_versions_1_8_0_to_1_8_4 import VERSIONS_1_8_0_TO_1_8_4
from .changelog_versions_1_8_10_to_1_8_13 import VERSIONS_1_8_10_TO_1_8_13
from .changelog_versions_1_8_14_to_1_8_16 import VERSIONS_1_8_14_TO_1_8_16
from .changelog_versions_1_8_17_to_1_8_18 import VERSIONS_1_8_17_TO_1_8_18
from .changelog_versions_1_8_19_to_1_8_24 import VERSIONS_1_8_19_TO_1_8_24
from .changelog_versions_1_8_25_to_1_8_32 import VERSIONS_1_8_25_TO_1_8_32
from .changelog_versions_1_8_5_to_1_8_9 import VERSIONS_1_8_5_TO_1_8_9

VERSIONS: Final[list[ChangelogVersion]] = (VERSIONS_1_8
                                           + VERSIONS_1_8_40_TO_1_8_58
                                           + VERSIONS_1_8_33_TO_1_8_39
                                           + VERSIONS_1_8_25_TO_1_8_32
                                           + VERSIONS_1_8_19_TO_1_8_24
                                           + VERSIONS_1_8_17_TO_1_8_18
                                           + VERSIONS_1_8_14_TO_1_8_16
                                           + VERSIONS_1_8_10_TO_1_8_13
                                           + VERSIONS_1_8_5_TO_1_8_9
                                           + VERSIONS_1_8_0_TO_1_8_4
                                           + VERSIONS_1_7
                                           + VERSIONS_1_4_TO_1_6
                                           + VERSIONS_1_0_TO_1_3)


def entries() -> list[ChangelogVersion]:
    """全部版本, 新→老。"""
    return VERSIONS
