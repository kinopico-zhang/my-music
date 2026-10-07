<div align="center">

# 🎵 My Music

**家庭自用 NAS 曲库听歌应用** — 浏览 · 播放 · 歌词 · 离线

[![CI](https://github.com/kinopico-zhang/my-music/actions/workflows/ci.yml/badge.svg)](https://github.com/kinopico-zhang/my-music/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/kinopico-zhang/my-music)](./LICENSE)
![Python](https://img.shields.io/badge/Python-3.13%20%7C%203.14-3776AB?logo=python&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-22-339933?logo=nodedotjs&logoColor=white)
![OS](https://img.shields.io/badge/OS-Linux%20%7C%20Windows%20%7C%20macOS-0078D6)

![pylint](https://img.shields.io/badge/pylint-10.00%2F10-brightgreen)
![mypy](https://img.shields.io/badge/mypy-strict-2A6DB2)
![pytest](https://img.shields.io/badge/pytest-221%20passed-0A9EDC?logo=pytest&logoColor=white)
![coverage](https://img.shields.io/badge/JS%20coverage-95%25%2B-brightgreen)

![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-d71f00?logo=sqlalchemy&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-e92063?logo=pydantic&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![PWA](https://img.shields.io/badge/PWA-Service%20Worker-5A0FC8?logo=pwa&logoColor=white)
![audio](https://img.shields.io/badge/audio-FLAC%20%7C%20DSF%20%7C%20MP3-2EA043)
![frontend](https://img.shields.io/badge/frontend-zero%20deps-61DAFB)

![ESLint](https://img.shields.io/badge/ESLint-passing-4B32C3?logo=eslint&logoColor=white)
![tsc](https://img.shields.io/badge/tsc-checkJS-3178C6?logo=typescript&logoColor=white)
![stylelint](https://img.shields.io/badge/stylelint-passing-263238?logo=stylelint&logoColor=white)
![html-validate](https://img.shields.io/badge/html--validate-passing-brightgreen)

[![stars](https://img.shields.io/github/stars/kinopico-zhang/my-music)](https://github.com/kinopico-zhang/my-music/stargazers)
[![issues](https://img.shields.io/github/issues/kinopico-zhang/my-music)](https://github.com/kinopico-zhang/my-music/issues)
[![last commit](https://img.shields.io/github/last-commit/kinopico-zhang/my-music)](https://github.com/kinopico-zhang/my-music/commits/main)
[![repo size](https://img.shields.io/github/repo-size/kinopico-zhang/my-music)](https://github.com/kinopico-zhang/my-music)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/kinopico-zhang/my-music/pulls)

</div>

> 从 [My Home](https://github.com/kinopico-zhang/my-home) 组合仓拆出来的独立仓:
> 账号体系 (登录/注册/账号管理) 内嵌在 `app/home/`, 单独 clone 本仓即可部署,
> 不需要组合仓。

## ✨ 功能

- 🎵 **曲库扫描** — 扫描 NAS 音乐目录, FLAC / DSF / MP3 等多格式
- 📚 **浏览** — 专辑 / 艺术家视图 · 搜索 · 分页
- ▶️ **播放器** — 播放队列 · 音质选择 · 预取 · MediaSession · 桌面端键盘快捷键 · 画中画
- 🎤 **歌词** — LRC 解析 + 逐行高亮, 可编辑
- 📋 **歌单** — 建歌单, 拖拽排序
- 🔗 **分享** — 歌曲分享链接
- ⬇️ **离线** — Service Worker 离线回源 + 自动缓存 (LRU 2GB, 播放预取顺手落盘) + 手动下载 (带用量统计)
- 📊 **统计** — 曲库统计视图
- 📱 **移动手势** — 面板横划 · 气泡滑动 · 菜单手势

## 🚀 快速开始

需要 Python 3.13+ (venv):

```sh
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env      # 可全留空, 首启走 /setup 引导
mkdir -p /path/to/music   # 曲库目录 (也可进应用后在 设置 页改)
./run.sh                  # 默认 8500; 有证书 HTTPS/HTTP 双开, 没证书明文
```

`run.sh` 有证书时 HTTPS 与 HTTP 双开 (两个端口两个进程): HTTPS 走
`PORT` (默认 8500), HTTP 走 `HTTP_PORT` (默认 8501, 局域网 IP 直连);
没证书只开 `PORT` 的明文 —— HTTPS 是可选的。会话 cookie 是无状态
HMAC 签名, 两个口通用。

打开 `http://<host>:8500/` → 自动进 `/music`。账号库为空时登录页会带去
`/setup` 引导页: 注册第一个管理员就能开始听歌。`.env` 里设 `AUTH_PASS`
是旧口径种子 (只在空库时生效, 设了就不再进引导; 仓库是公开的, 不带
默认口令)。

数据都落在 `data/` (git 忽略): `music.db` 曲库索引 / `users.db` 账号 /
`music-art/` 封面缓存。音乐目录默认 `/share/Media/Music`, 用
`MYTESLA_MUSIC_DIR` 或设置页改。

## ⚙️ 环境变量

完整清单见 [.env.example](.env.example), 常用项:

| 变量 | 默认 | 说明 |
|---|---|---|
| `AUTH_USER` / `AUTH_PASS` | `admin` / 空 | 旧口径首启种子 (不设则走 `/setup` 引导; 只在空账号库时种) |
| `PORT` / `HTTP_PORT` / `HTTP` | `8500` / `8501` | 双端口; `HTTP=1` 强制明文 (调试) |
| `MYTESLA_MUSIC_DB` | `sqlite:///data/music.db` | 曲库索引 (完整 URL 形式) |
| `MYTESLA_MUSIC_DIR` | `/share/Media/Music` | 音乐目录 (设置页里改的优先) |
| `MYHOME_USERS_DB` / `MYHOME_SECRET_FILE` | `data/users.db` / `.session_secret` | 账号库与会话密钥 (组合部署指到共享文件) |

## 🧪 测试与质量门禁

```sh
npm install               # 前端工具链 (eslint/tsc/stylelint/html-validate/c8)
./run_tests.sh            # pylint + mypy + pytest + 前端全套 + 覆盖率门禁
```

门禁全绿才算过: pylint 10.00/10 (app 严检) · mypy 严格模式 · pytest 221 例
(真实 ORM + SQLite 临时库, 不碰真实曲库; 含 e2e 冒烟: 起真 uvicorn
子进程打真 HTTP —— 登录 → 页面 → 静态资源, 与 ./run.sh 生产路径同构) · ESLint / tsc --checkJs /
stylelint / html-validate / node --test · c8 覆盖率 ≥95% (歌词解析 /
队列 / 下载等纯逻辑模块)。CI 在 GitHub Actions 三平台跑同一套门禁。

从 My Home 组合仓的 `apps/my-music` 下跑时不用 npm install —— 脚本会
软链组合仓根的 node_modules。

## 📁 项目结构

```
app/
  music/      听歌应用本体 (扫描 / 查询 / 媒体流 / 分享 / 接口与页面)
  home/       账号层副本 (登录/注册/账号管理页面 + /api 会话接口 + 中间件)
  account_store/  账号库存取 (scrypt 密码 + 注册邀请)
  authentication.py  会话 cookie 签发与校验 (HMAC)
  main.py     独立装配: 账号层挂根, 应用挂 /music
tests/        pytest (真实 ORM + SQLite 临时库) + node --test (纯逻辑模块)
```

账号层的接口与 cookie 配方和 My Home 组合仓完全一致 (`/api/login`、
`/api/me`…): 组合部署时外层把 `MYHOME_USERS_DB` / `MYHOME_SECRET_FILE`
指到共享的账号库与密钥文件, 三个应用就共用同一批账号单点登录。

## 🔗 相关项目

| 仓 | 说明 |
|---|---|
| [My Home](https://github.com/kinopico-zhang/my-home) | 组合仓: 三应用 + 共享账号层, 单点登录 |
| [My Tesla](https://github.com/kinopico-zhang/my-tesla) | TeslaMate 行车数据展示 |
| [My Money](https://github.com/kinopico-zhang/my-money) | 家庭记账 (离线 LWW 同步) |

## 📄 许可证

[MIT](./LICENSE) © 2026 kinopico
