<div align="center">

# 🎬 DJJ — 随机短视频播放站

**🎨 仿抖音风格 · 📱 PC/手机自适应 · 🔒 安全播放 · 🐳 一键部署**

[![Docker Pulls](https://img.shields.io/docker/pulls/lzylipu/djj?style=flat-square&logo=docker&color=%230db7ed)](https://hub.docker.com/r/lzylipu/djj)
[![GitHub License](https://img.shields.io/github/license/lzylipu/djj?style=flat-square)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Arch-amd64%20%7C%20arm64-blue?style=flat-square&logo=linux&logoColor=white)]()

**[English](./README_EN.md) | 中文**

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

## 🔁 拉取最新版本（升级）

```bash
# 1. 拉最新镜像
docker pull lzylipu/djj:latest

# 2a. docker run 方式：先 rm 旧容器再用相同命令重建
docker rm -f djj
# 再执行上面的 docker run ...

# 2b. docker-compose 方式：直接 up -d 会自动重建
docker compose pull && docker compose up -d
```

> 💡 配置文件（`config.yaml` 在 `/data` 挂载里）和本地视频目录在升级时保持不变，无需重新配置。

---

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

**容器首次启动时，`/data/config.yaml` 会自动生成**，含 1 个本地源 + 15 个网络聚合源的完整默认模板，可按需编辑后 **重启容器** 生效。

> 📌 默认模板已带全 15 个 publicly-known 网络源（`yujn/nxux/yx520/aa1dy/lcc8/cunshao/wzapi` 等），无需 API Key，直接可用。

### 视频源格式（v3 list-of-dict）

每个源是一个 YAML dict，有两种完全等价的写法，可混用：

```yaml
# 写法 A — 多行经典缩进 (易读易改)
- name: 抖音精选
  path: /videos/抖音

# 写法 B — 单行行内 flow dict (紧凑)
- {name: 抖音精选, path: /videos/抖音}
```

### 字段说明

| 字段 | 必填 | 说明 |
|:-----|:----:|:-----|
| `name`     | ✅ | 显示名（中英文均可，唯一即可） |
| `path`     | 本地源必填 | 容器内绝对路径，如 `/videos` 或 `/videos/抖音`；需用 `-v` 挂载进去 |
| `url`      | 远程源必填 | API 地址，`http://` 或 `https://` 开头 |
| `group`    | 远程源必填 | 分组名，默认填 `网络`；所有同 group 的远程源合成一个聚合组，前端下拉看见分组名，组内按 `weight` 加权随机 + 失败自动降级 |
| `mode`     | 远程源可选 | 响应类型，默认 `auto` 自动嗅探。详见下表 |
| `json_path`| `mode=json` 必填 | 视频字段在 JSON 中的路径，如 `data.video` 或 `data.list.0.url` |
| `weight`   | 可选 | 整数，默认 1；同组内按权重加权随机被选中 |
| `retry`    | 可选 | 整数，默认 2；连续失败超此次数即熔断此源 60s |

### 远程源 `mode` 类型

| mode | 识别方式 | 示例源 |
|:-----|:---------|:-------|
| 🔄 `auto`（默认） | 后端嗅探 | — |
| 🔀 `302` | API 返回 302 跳转，`Location` 头指向 mp4 直链 | `api.yujn.cn` |
| 📦 `json` | 返回 JSON，需配 `json_path` 取嵌套字段 | `wzapi.com` |
| 🎥 `mp4` | 直接返回 `video/*` 内容流 | — |
| 📄 `html` | 返回 HTML，提取 `<video src="...">` | `tucdn.wpon.cn` |
| 📝 `text_url` | 返回纯文本 URL（如 `https://xxx.mp4`） | `diskgirl.com` |

### 完整 `config.yaml` 示例

```yaml
server:
  port: 8080
  secret: change-me-to-random-string   # ⚠️ 生产环境必须改；或设 API_SECRET 环境变量覆盖

sources:
  # === 🔴 删除不需要的行，复制需要的行改名即可 ===

  # 本地源：只写 name + path，需 docker -v 挂进来
  - {name: 本地视频, path: /videos}
  # 多个本地目录用子目录挂载 + 多条本地源：
  - {name: 抖音精选, path: /videos/抖音}
  - {name: 美好肉体, path: /videos/肉体}

  # 网络聚合组：所有标 group=网络 的源合成一个聚合组，前端下拉只看见"网络"
  - {name: yujn小姐姐, url: "https://api.yujn.cn/api/zzxjj.php",                                group: 网络, mode: 302, weight: 3}
  - {name: yx520,      url: "http://www.yx520.ltd/API/xjj/api.php?msg=xjj",                    group: 网络, mode: 302, weight: 2}
  - {name: lcc8,       url: "https://www.lcc8.com/sv/video.php",                               group: 网络, mode: 302, weight: 3}
  - {name: cunshao,    url: "https://www.cunshao.com/666666/api/web.php",                      group: 网络, mode: 302, weight: 3}
  - {name: wzapi社姐,  url: "https://wzapi.com/api/sjxjjsp?format=json&category=shejie",      group: 网络, mode: json, json_path: "data.video", weight: 3}
  # ... 默认模板共 15 个网络源，详见 /data/config.yaml
```

> 💡 **环境变量优先级高于配置文件**：`API_SECRET` 环境变量会覆盖 `config.yaml` 中的 `secret` 字段。
>
> ⚠️ 本地视频目录需用 `-v` 挂载到容器内绝对路径（通常 `/videos` 或其子目录），scanner 会递归扫描 `mp4/avi/mkv/mov/webm/flv`。

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
└── 📖 README_EN.md                # 英文说明
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
