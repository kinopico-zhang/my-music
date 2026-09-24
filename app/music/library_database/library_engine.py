"""My Music 的库引擎与路径状态 (进程级单例, 测试可整体重置)。

曲库目录 / 封面缓存目录跟着引擎走 (测试注入临时目录, 不碰真曲库);
封面缓存 = 库文件同目录下的 music-art/。默认路径可用环境变量覆盖。
1.8.83 起引擎三道加固 (用户听歌会话实报接口成片 503 的根治):
sqlite 临时文件挪到大硬盘 (/tmp 是 64MB 内存盘, 大扫描的排序临时
文件一撑就 ENOSPC)、WAL (扫描线程写库时读请求不再被挡成 503)、
锁等待 30 秒 (默认 5 秒, 扫描写事务一长读请求就炸)。
"""
import os
from pathlib import Path
from typing import Any, Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .library_models import MusicLibraryBase

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_DATABASE_URL = (os.environ.get("MYTESLA_MUSIC_DB")
                        or f"sqlite:///{PROJECT_DIR / 'data' / 'music.db'}")
DEFAULT_MUSIC_DIRECTORY = (os.environ.get("MYTESLA_MUSIC_DIR")
                           or "/share/Media/Music")
# sqlite 临时文件的家 (排序/索引重建的溢写盘): 默认会去 /tmp —— NAS 上
# 那是 64MB 内存盘, 手动扫一圈大库就把接口成片打成 503; 挪到 data/ 旁
# 的大硬盘。环境变量已设就尊重 (想指到别处的自由保留)。
SQLITE_TMP_DIRECTORY = str(PROJECT_DIR / "data" / "sqlite-tmp")


class _EngineState:
    """进程级引擎持有者 (避免 global 语句)。"""

    engine: Engine | None = None
    session_factory: sessionmaker[Session] | None = None
    database_url: str = ""
    music_directory: Path | None = None
    artwork_cache_directory: Path | None = None


_engine = _EngineState()


def artwork_cache_directory_for(url: str) -> Path:
    """库 URL → 封面缓存目录: SQLite 放库文件旁的 music-art/, 其他库落 data/。"""
    if url.startswith("sqlite:///"):
        return Path(url.removeprefix("sqlite:///")).parent / "music-art"
    return Path("data") / "music-art"


def init_engine(url: str | None = None,
                library_directory: Path | None = None) -> None:
    """创建引擎 (缺省 data/music.db + /share/Media/Music)。"""
    if url is None:
        url = DEFAULT_DATABASE_URL
    if url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(
            parents=True, exist_ok=True)
        # 临时文件挪家在大盘上备好 (sqlite 每次开临时文件都会查这变量)
        Path(SQLITE_TMP_DIRECTORY).mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("SQLITE_TMPDIR", SQLITE_TMP_DIRECTORY)
    _engine.artwork_cache_directory = artwork_cache_directory_for(url)
    _engine.database_url = url
    _engine.music_directory = library_directory or Path(DEFAULT_MUSIC_DIRECTORY)
    _engine.engine = create_engine(url, connect_args={
        "check_same_thread": False,
        "timeout": 30,   # 锁等待上限 (秒): 扫描写库时读请求排队, 别 5 秒就炸
    })
    # WAL: 读不再挡写、写不再挡读 (扫描线程收尾大事务时, 听歌的流/歌词
    # 接口照常答)。journal_mode 是库级持久属性, 幂等。
    if url.startswith("sqlite:///"):
        @event.listens_for(_engine.engine, "connect")
        def _sqlite_wal(dbapi_connection: Any, _record: Any) -> None:   # noqa: W0612 闭包随引擎
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()
    _engine.session_factory = sessionmaker(_engine.engine,
                                           expire_on_commit=False)


def dispose_engine() -> None:
    """释放连接池 (测试隔离也用它)。"""
    if _engine.engine is not None:
        _engine.engine.dispose()
    _engine.engine = None
    _engine.session_factory = None
    _engine.database_url = ""
    _engine.music_directory = None
    _engine.artwork_cache_directory = None


def engine() -> Engine:
    """曲库索引引擎 (启动时建表用)。"""
    if _engine.engine is None:
        raise RuntimeError("曲库引擎未初始化 (init_engine 未调用)")
    return _engine.engine


def database_url() -> str:
    """当前库 URL (换曲库目录时同库重装配用)。"""
    if _engine.engine is None:
        raise RuntimeError("曲库引擎未初始化 (init_engine 未调用)")
    return _engine.database_url


def music_directory() -> Path:
    """曲库根目录 (音频/封面文件都从这里找)。"""
    if _engine.music_directory is None:
        raise RuntimeError("曲库引擎未初始化 (init_engine 未调用)")
    return _engine.music_directory


def artwork_cache_directory() -> Path:
    """封面缓存目录 (库文件同目录的 music-art/)。"""
    if _engine.artwork_cache_directory is None:
        raise RuntimeError("曲库引擎未初始化 (init_engine 未调用)")
    return _engine.artwork_cache_directory


def session_factory() -> sessionmaker[Session]:
    """曲库索引会话工厂。"""
    if _engine.session_factory is None:
        raise RuntimeError("曲库引擎未初始化 (init_engine 未调用)")
    return _engine.session_factory


def get_db() -> Iterator[Session]:
    """FastAPI 依赖: 每请求一个曲库会话, 请求结束自动关闭。"""
    with session_factory()() as session:  # pylint: disable=not-callable
        yield session


def create_all() -> None:
    """建表 (启动时调用)。"""
    MusicLibraryBase.metadata.create_all(engine())
