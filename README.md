<div align="center">

# 🎬 DJJ — 随机短视频播放站

**🎨 仿抖音风格 · 📱 PC/手机自适应 · 🔒 安全播放 · 🐳 一键部署**

[![Docker Pulls](https://img.shields.io/docker/pulls/lzylipu/djj?style=flat-square&logo=docker&color=%230db7ed)](https://hub.docker.com/r/lzylipu/djj)
[![GitHub License](https://img.shields.io/github/license/lzylipu/djj?style=flat-square)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Arch-amd64%20%7C%20arm64-blue?style=flat-square&logo=linux&logoColor=white)]()

**[English](./README.en.md) | 中文**

</div>

---

> 🎉 自托管、开箱即用的随机短视频播放器！本地挂载 + 远程 API 混合视频源，HMAC 签名安全播放，非 H.264 视频自动转码，手机全屏手势 & PC 键盘快捷键 —— 一个 Docker 命令，30 秒上线 🚀

---

## 🌟 项目亮点

| 🎯 | 亮点 |
|:--:|------|
| 🐳 | **一键部署** — Docker 镜像 `lzylipu/djj:latest`，30 秒上线 |
| 📱 | **自适应 UI** — 仿抖音交互，手机全屏手势 & PC 键盘快捷键完美适配 |
| 🔀 | **多源融合** — 本地目录挂载 + 远程 API（302/JSON/MP4/HTML 自动识别） |
| 🔒 | **安全播放** — HMAC-SHA256 签名 token，不暴露真实文件路径 |
| 🔄 | **智能转码** — 非 H.264 视频自动 ffmpeg 实时转码，兼容所有格式 |
| 🐙 | **多架构** — 支持 `linux/amd64` + `linux/arm64` |
| 🎨 | **零框架前端** — 纯 HTML/CSS/JS，轻量极速加载 |

> 📌 支持视频格式：`.mp4` / `.avi` / `.mkv` / `.mov` / `.webm` / `.flv`

---

## 🚀 快速开始

```bash
docker run -d --name djj \
  -p 8080:8080 \
  -v djj-data:/data \
  -v /你的视频目录:/videos:ro \
  -e API_SECRET=请替换为随机密钥 \
  lzylipu/djj:latest
```

打开 `http://<IP>:8080` 🎉 手机电脑自动适配！

> 💡 配置文件 `/data/config.yaml` 首次启动自动生成，编辑后重启容器生效。

---

## 📋 部署详解

### 🐳 方式一：Docker Compose（✅ 推荐）

```bash
# 1️⃣ 克隆仓库 & 配置环境变量
git clone https://github.com/lzylipu/djj.git
cd djj
cp .env.example .env          # 填写 API_SECRET

# 2️⃣ 启动服务
docker compose up -d
```

<details>
<summary>📝 查看 docker-compose.yml</summary>

```yaml
version: "3.8"
services:
  djj:
    image: lzylipu/djj:latest
    container_name: djj
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    environment:
      - TZ=Asia/Shanghai
      - API_SECRET=请替换为随机密钥    # ⚠️ 必须修改
      - PORT=8080
    ports:
      - "8080:8080"
    volumes:
      - djj-data:/data
      - /srv/videos:/videos:ro

volumes:
  djj-data:
```
</details>

### 🐳 方式二：Docker Run

```bash
docker run -d \
  --name djj \
  --restart unless-stopped \
  --log-opt max-size=10m --log-opt max-file=3 \
  -e TZ=Asia/Shanghai \
  -e API_SECRET=请替换为随机密钥 \
  -p 8080:8080 \
  -v /volume1/docker/djj/data:/data \
  -v /volume1/video:/videos:ro \
  lzylipu/djj:latest
```

### ⚙️ 环境变量

| 变量 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `API_SECRET` | ⚠️ **必须修改** | HMAC 签名密钥，建议用 `openssl rand -hex 16` 生成 |
| `PORT` | `8080` | 服务监听端口 |
| `TZ` | — | 时区，如 `Asia/Shanghai` |
| `DJJ_DATA` | `/data` | 配置文件目录（含 `config.yaml`） |

### 📂 挂载说明

| 挂载点 | 说明 |
|:-------|:-----|
| `/data` | 🗄️ 配置持久化（`config.yaml` 自动生成于此） |
| `/videos` | 🎬 本地视频目录（建议 `:ro` 只读挂载） |

> 💡 **多个本地目录**可挂载子目录：`-v /path/to/舞蹈:/videos/舞蹈:ro`

---

## 🎛 配置说明

编辑 `/data/config.yaml`，修改后 **重启容器** 生效：

```yaml
server:
  port: 8080
  secret: change-me-to-random-string   # ⚠️ 等同于 API_SECRET 环境变量

# 视频源: 源名: 路径或URL
# / 开头 = 本地目录(自动扫描子目录)
# http 开头 = 远程API(自动识别类型)
sources:
  # --- 📁 本地目录(取消注释即可启用) ---
  默认: /videos
  # 舞蹈: /videos/舞蹈
  # 搞笑: /videos/搞笑

  # --- 🌐 远程源(无需API Key, 自动识别类型) ---
  小姐姐: https://tmini.net/api/meinv?mp4=json&r=
  绅士视频: https://v.nrzj.vip/video.php
  随便看: https://api.yujn.cn/api/zzxjj.php
  热舞视频: https://tucdn.wpon.cn/api-girl/index.php?type=video
```

> 💡 **环境变量优先级高于配置文件**：`API_SECRET` 环境变量会覆盖 `config.yaml` 中的 `secret` 字段。

### 🌐 远程源类型（自动识别）

| 类型 | 识别方式 | 示例源 |
|:-----|:---------|:-------|
| 🔀 302 跳转 | `Location` 头指向 mp4 | `v.nrzj.vip` |
| 📦 JSON API | 返回 `{url:...}` / `{video_url:...}` / `{data:{link:...}}` | `tmini.net` |
| 🎥 直接 MP4 流 | 返回 `video/*` 内容 | `api.yujn.cn` |
| 📄 HTML 页面 | 提取 `<video src="...">` | `tucdn.wpon.cn` |

---

## 🎮 操作指引

### 📱 移动端手势

| 操作 | 功能 |
|:-----|:-----|
| 👆 上滑 | ⏭ 下一个视频 |
| 👇 下滑 | ⏮ 上一个视频 |
| 👆 单击 | ⏯ 暂停 / 播放 |
| 👆👆 双击 | 🔲 全屏切换 |
| ➡️ 右侧按钮 | 🚫 PASS / 🔁 循环 / 🔀 换源 / ❤️ 收藏 |

### 🖥 PC 端快捷键

| 快捷键 | 功能 | 快捷键 | 功能 |
|:--------|:-----|:--------|:-----|
| `Space` | ⏯ 暂停/播放 | `S` | 🔀 切换源 |
| `N` / `↑` | ⏭ 下一个 | `M` | 🔁 循环/连播 |
| `P` / `↓` | ⏮ 上一个 | `V` | 🔇 静音开关 |
| `F` | 🔲 全屏 | `←` / `→` | ⏪/⏩ 快退/快进 20s |
| `↑` / `↓` _(非视频时)_ | 🔊 音量 | 🖱 滚轮 | 🔊 音量调节 |

---

## 🔌 API 接口

| 接口 | 方法 | 说明 |
|:-----|:-----|:-----|
| [`/api/random?source=源名`](./api/server.py) | `GET` | 🎲 获取随机视频 token |
| [`/api/play?token=xxx`](./api/server.py) | `GET` | ▶️ 播放视频（本地直接返回 / 远程代理流） |
| [`/api/sources`](./api/server.py) | `GET` | 📊 列出所有源及统计信息 |

> 🔐 所有播放链接使用 HMAC-SHA256 签名，token 有效期 24 小时，真实文件路径永不暴露。

---

## 📁 项目结构

```
djj/
├── 📂 api/                        # 后端 Python 模块
│   ├── 🔐 __init__.py             # 模块初始化
│   ├── 🔐 auth.py                 # HMAC 签名 & token 管理
│   ├── ⚙️  config.py              # 配置加载（YAML + 环境变量）
│   ├── 🔍 scanner.py              # 本地视频扫描 & 索引
│   └── 🌐 server.py              # FastAPI 主服务（路由/转码/代理）
├── 📂 web/                        # 前端静态资源
│   ├── 📄 index.html              # 主页面（仿抖音 UI）
│   ├── 📂 css/
│   │   ├── 🎨 style.css           # 样式表
│   │   └── 🔢 DS-DIGIT.TTF       # 数字字体
│   └── 📂 img/
│       ├── 🖼️ logo.png            # Logo
│       ├── 🖼️ favicon.ico         # 网站图标
│       ├── 💖 love.png / love1.png / loves.png  # 收藏动画
│       ├── 🌄 bg.jpg / bg.gif     # 背景图
│       └── 📱 ewm.png             # 二维码
├── 🐳 Dockerfile                  # Docker 镜像构建
├── 🐙 docker-compose.yml         # Docker Compose 编排
├── 📋 config.example.yaml         # 配置文件示例
├── 🔑 .env.example                # 环境变量示例
├── 📦 pyproject.toml              # Python 项目配置（v2.3.0）
├── 🙈 .gitignore                  # Git 忽略规则
├── 🙈 .dockerignore               # Docker 忽略规则
├── 📂 .github/workflows/         # GitHub Actions CI/CD
│   └── 🔄 docker.yml              # 多架构镜像构建推送
├── 📜 LICENSE                     # MIT 许可证
├── 📖 README.md                   # 中文说明（本文件）
└── 📖 README.en.md                # 英文说明
```

---

## 🛠 技术栈

| 层级 | 技术方案 |
|:-----|:---------|
| ⚙️ **后端** | Python 3.12 / [FastAPI](https://fastapi.tiangolo.com/) / [uvicorn](https://www.uvicorn.org/) / [httpx](https://www.python-httpx.org/) / [PyYAML](https://pyyaml.org/) |
| 🔄 **转码** | [ffmpeg](https://ffmpeg.org/) — 仅非 H.264 视频触发实时转码（libx264 veryfast preset） |
| 🎨 **前端** | 纯 HTML / CSS / JavaScript，零框架依赖 |
| 🐳 **部署** | Docker + Docker Compose，多架构镜像（amd64 + arm64） |
| 🔄 **CI/CD** | GitHub Actions → Docker Hub + GHCR 多架构自动推送 |

---

## ❓ 常见问题

<details>
<summary>🔐 如何生成安全的 API_SECRET？</summary>

```bash
# 推荐方式
openssl rand -hex 16

# 或使用 Python
python3 -c "import secrets; print(secrets.token_hex(16))"
```
</details>

<details>
<summary>📁 如何挂载多个本地视频目录？</summary>

在 `docker-compose.yml` 或 `docker run` 中挂载子目录：

```bash
# Docker Run 方式
-v /path/to/舞蹈:/videos/舞蹈:ro
-v /path/to/搞笑:/videos/搞笑:ro

# 然后在 config.yaml 中添加源
sources:
  舞蹈: /videos/舞蹈
  搞笑: /videos/搞笑
```
</details>

<details>
<summary>🔄 视频无法播放怎么办？</summary>

1. 检查视频文件格式是否为支持的格式（mp4/avi/mkv/mov/webm/flv）
2. 非 H.264 编码的视频会自动转码，确保容器中有 ffmpeg
3. 远程源网络不通时，检查容器 DNS 和网络配置
4. 查看容器日志：`docker logs djj`
</details>

<details>
<summary>⚙️ 配置修改后如何生效？</summary>

编辑 `/data/config.yaml` 后，重启容器即可：

```bash
docker restart djj
```
</details>

---

## 🤝 致谢

- 灵感来源：[JMWpower/xiaojiejie](https://github.com/JMWpower/xiaojiejie)
- 所有远程视频 API 提供者

---

## 📄 许可证

本项目基于 [MIT License](./LICENSE) 开源。

Copyright (c) 2024 lzylipu

<div align="center">

**⭐ 如果这个项目对你有帮助，点个 Star 支持一下！⭐**

</div>
