"""My Music 后端结构测试: 全仓硬上限 —— app 下源文件 ≤200 行 (与 pyproject
[tool.pylint.main] max-module-lines 同一规矩, 前端那半在
test_music_wiring_library.py 的 test_music_frontend_structure)。
2026-09-18 起加: changelog_versions_1_8.py 长到 215 行, CI 的 pylint 揪出
(C0302), 但本地只看评分会漏 —— convention 类消息不扣分, pylint 照样打
10.00/10 只是退出码非零。这道门禁让本地 pytest 先红, 不等 CI。"""
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app"


def test_music_backend_structure():
    """后端源文件 ≤200 行: 超了按逻辑拆分 (数据文件按版本段分家, 见
    app/music/changelog.py 头注)。"""
    oversize = []
    for path in sorted(APP.rglob("*.py")):
        count = len(path.read_text(encoding="utf-8").splitlines())
        if count > 200:
            oversize.append(f"{path.relative_to(APP.parent)} ({count} 行)")
    assert not oversize, f"超过 200 行的后端文件: {oversize}"
