"""起一个「真实曲库快照」的 my-music 实例给 README 截图用 (临时, 不进数据)。

与 my-tesla 的种子服务器 (假数据) 不同, 本仓截图口径是真实数据
(2026-10-21 用户点名「不涉及隐私, 可以用真实数据截图」): 生产库只读
快照 (sqlite backup API, 连 WAL 一并收进来) + 曲库目录只读挂载, 不造假
数据也不碰生产写路径 —— 截图实例的索引写 (播放计数等) 全落在快照库上。

曲库目录经 $SHOT_MUSIC_DIR 给 (默认 ~/nas-music, 即生产那条 sshfs
挂载; 换任何一份真实曲库目录都能跑)。账号体系也用真实的一份: 复制
生产 users.db + .session_secret 到工作目录 (只读使用), 射手 (shoot.py)
拿同一份密钥给真实管理员 uuid 签会话 cookie —— 最近播放/播放排行都是
按账号记的, 用真实账号才有真实的收听史 (2026-10-21 截图口径: 真实数据,
用户点名「不涉及隐私」)。

快照一次成型: music.db 已在即整库复用直接起服 (重建: 删 SHOTLAB 快照
或 SHOT_RESEED=1)。启动只装配不扫描 (扫描全手动), 不会去扫挂载目录;
截图实例的一切写 (播放计数等) 都落在快照库上, 生产库零写入。

用法: .venv/bin/python shots/real_server.py [端口]   (默认 8906)
环境: SHOTLAB 工作目录 (默认 ~/shotlab, 快照与账号副本落
      $SHOTLAB/music-real/)
      SHOT_MUSIC_DIR 曲库目录 (默认 ~/nas-music)
      SHOT_SOURCE_DB 生产库 (默认组合仓根 data/music.db, 只读)
      SHOT_SOURCE_USERS 生产账号库 (默认组合仓根 data/users.db, 只读)
      SHOT_SOURCE_SECRET 会话密钥 (默认组合仓根 .session_secret, 只读)
      SHOT_RESEED=1 强制重拍快照
"""
import os
import pathlib
import shutil
import sqlite3
import sys
import threading
import time

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.chdir(REPO)

LAB = pathlib.Path(os.environ.get("SHOTLAB",
                                  str(pathlib.Path.home() / "shotlab")))
WORK = LAB / "music-real"
WORK.mkdir(parents=True, exist_ok=True)

_combo_root = REPO.parent.parent                    # 组合仓根 (独立 clone 时不存在)
SOURCE_DB = os.environ.get(
    "SHOT_SOURCE_DB",
    str(_combo_root / "data" / "music.db")
    if (_combo_root / "data" / "music.db").exists() else "")
SOURCE_USERS = os.environ.get(
    "SHOT_SOURCE_USERS",
    str(_combo_root / "data" / "users.db")
    if (_combo_root / "data" / "users.db").exists() else "")
SOURCE_SECRET = os.environ.get(
    "SHOT_SOURCE_SECRET",
    str(_combo_root / ".session_secret")
    if (_combo_root / ".session_secret").exists() else "")
SNAPSHOT = WORK / "music.db"
MUSIC_DIR = os.environ.get("SHOT_MUSIC_DIR",
                           str(pathlib.Path.home() / "nas-music"))


def _need(label: str, path: str) -> str:
    if not path:
        raise SystemExit(
            f"找不到{label}: 组合仓布局外独立 clone 时, 请用环境变量指到"
            f"生产的一份 (只读), 或把副本直接放到 {WORK} 后复用。")
    return path


def make_snapshot() -> None:
    """生产库 → 一致性快照 (backup API 吃 WAL, 只读源库)。"""
    _need("生产库", SOURCE_DB)
    tmp = SNAPSHOT.with_suffix(".db.tmp")
    src = sqlite3.connect(f"file:{SOURCE_DB}?mode=ro", uri=True)
    dst = sqlite3.connect(tmp)
    src.backup(dst)
    dst.close()
    src.close()
    tmp.replace(SNAPSHOT)
    print(f"snapshot ready {SNAPSHOT} ({SNAPSHOT.stat().st_size} bytes)",
          flush=True)


if os.environ.get("SHOT_RESEED") or not SNAPSHOT.exists():
    make_snapshot()
else:
    print(f"snapshot reused {SNAPSHOT}", flush=True)

# ---- 账号副本 (只读使用): 生产 users.db + 会话密钥各复制一份 ----
USERS_DB = WORK / "users.db"
SECRET = WORK / "secret"
if not USERS_DB.exists():
    shutil.copyfile(_need("生产账号库", SOURCE_USERS), USERS_DB)
if not SECRET.exists():
    shutil.copyfile(_need("会话密钥", SOURCE_SECRET), SECRET)
print(f"users copy {USERS_DB} ({USERS_DB.stat().st_size} bytes)", flush=True)

# ---- 封面缓存补拷: music-art 不跟库走, 空着的话每张封面都要从音频文件
# 现提取 (sshfs 直读 NAS 很慢), 截图视口内大量超时 404 = 成片占位灰块
# (2026-10-22 用户点名「很多截图都没有专辑封面」)。生产侧一份 ~630MB,
# 一次性 copytree 几十秒; 已有副本则跳过 (想重拷删掉目录即可)。 ----
ART_DIR = WORK / "music-art"
SOURCE_ART = os.environ.get(
    "SHOT_SOURCE_ART",
    str(pathlib.Path(_need("生产库", SOURCE_DB)).parent / "music-art"))
_cache_hit = ART_DIR.exists() and any(ART_DIR.iterdir())
if not _cache_hit and pathlib.Path(SOURCE_ART).is_dir():
    shutil.copytree(SOURCE_ART, ART_DIR, dirs_exist_ok=True)
    print(f"art cache copied {ART_DIR} "
          f"({sum(1 for _ in ART_DIR.iterdir())} files)", flush=True)
elif _cache_hit:
    print(f"art cache reused {ART_DIR} "
          f"({sum(1 for _ in ART_DIR.iterdir())} files)", flush=True)
else:
    print(f"warn: 生产封面缓存不存在 ({SOURCE_ART}), "
          f"截图可能出现大量占位灰块", flush=True)

os.environ.update({
    "MYHOME_USERS_DB": str(USERS_DB),
    "MYHOME_SECRET_FILE": str(SECRET),
    "MYTESLA_MUSIC_DB": f"sqlite:///{SNAPSHOT.as_posix()}",
    "MYTESLA_MUSIC_DIR": MUSIC_DIR,
})

import uvicorn                                    # noqa: E402
from app import main as app_main                  # noqa: E402

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8906
server = uvicorn.Server(uvicorn.Config(
    app_main.app, host="127.0.0.1", port=PORT, log_level="warning"))
thread = threading.Thread(target=server.run, daemon=True)
thread.start()
while not server.started:
    time.sleep(0.1)

from app.music.library_database import (       # noqa: E402
    Album, Artist, Track, session_factory)

with session_factory()() as db:                  # pylint: disable=not-callable
    print(f"READY artists={db.query(Artist).count()} "
          f"albums={db.query(Album).count()} "
          f"tracks={db.query(Track).count()}", flush=True)

while thread.is_alive():
    time.sleep(1)
