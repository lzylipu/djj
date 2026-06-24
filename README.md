# DJJ 🎬 随机短视频播放站

[![Docker](https://img.shields.io/docker/pulls/lzylipu/djj)](https://hub.docker.com/r/lzylipu/djj)
[![License](https://img.shields.io/github/license/lzylipu/djj)](./LICENSE)

自托管、零配置、PC/手机自适应的随机视频播放器。本地挂载 + 远程 API 混合源，智能转码，HMAC 签名安全播放。

**[English](./README.en.md) | 中文**

---

## ✨ 特性

- 🎯 **一键部署** — Docker 镜像 `lzylipu/djj:latest`，30 秒上线
- 📱 **自适应 UI** — 一套前端同时适配手机全屏手势 & PC 键盘快捷键
- 🔀 **多源融合** — 本地目录挂载 + 远程 API（302/JSON/MP4/HTML 自动识别）
- 🔒 **安全播放** — HMAC 签名 token，不暴露真实文件路径
- 🔄 **智能转码** — 非H.264视频自动 ffmpeg 实时转码
- 🐙 **多架构** — 支持 `linux/amd64` + `linux/arm64`

---

## 🚀 快速开始

```bash
docker run -d --name djj \
  -p 8080:8080 \
  -v djj-data:/data \
  -v /你的视频目录:/videos:ro \
  -e API_SECRET=replace-with-random-secret \
  lzylipu/djj:latest
```

打开 `http://<IP>:8080`，手机电脑自动适配。

> 配置文件 `/data/config.yaml` 首次启动自动生成，编辑后重启容器生效。

---

## 📋 部署详解

### Docker Compose（推荐）

```bash
cp .env.example .env    # 填写 API_SECRET
docker compose up -d
```

### Docker Run

```bash
docker run -d \
  --name djj \
  --restart unless-stopped \
  --log-opt max-size=10m --log-opt max-file=3 \
  -e TZ=Asia/Shanghai \
  -e API_SECRET=replace-with-random-secret \
  -p 8080:8080 \
  -v /volume1/docker/djj/data:/data \
  -v /volume1/video:/videos:ro \
  lzylipu/djj:latest
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `API_SECRET` | ⚠️ 必须修改 | HMAC 签名密钥，建议用 `openssl rand -hex 16` 生成 |
| `PORT` | `8080` | 服务端口 |
| `TZ` | — | 时区，如 `Asia/Shanghai` |
| `DJJ_DATA` | `/data` | 配置文件目录（含 `config.yaml`） |

### 挂载说明

| 挂载点 | 说明 |
|--------|------|
| `/data` | 配置持久化（`config.yaml` 自动生成于此） |
| `/videos` | 本地视频目录（建议 `:ro` 只读） |

> 多个本地目录可挂载子目录：`-v /path/to/舞蹈:/videos/舞蹈:ro`

---

## 🎛 配置

编辑 `/data/config.yaml`，修改后重启容器生效：

```yaml
server:
  port: 8080
  secret: change-me-to-random-string

sources:
  # --- 本地目录 ---
  默认: /videos
  # 舞蹈: /videos/舞蹈
  # 搞笑: /videos/搞笑

  # --- 远程源(无需API Key, 自动识别类型) ---
  小姐姐: https://tmini.net/api/meinv?mp4=json&r=
  绅士视频: https://v.nrzj.vip/video.php
  随便看: https://api.yujn.cn/api/zzxjj.php
```

### 远程源类型（自动识别）

| 类型 | 识别方式 | 示例 |
|------|----------|------|
| 302 跳转 | `Location` 头指向 mp4 | `v.nrzj.vip` |
| JSON API | 返回 `{url:...}` / `{video_url:...}` / `{data:{link:...}}` | `tmini.net` |
| 直接 MP4 流 | 返回 `video/*` 内容 | `api.yujn.cn` |
| HTML 页面 | 提取 `<video src="...">` | `tucdn.wpon.cn` |

---

## 🎮 操作

### 📱 移动端

| 操作 | 功能 |
|------|------|
| 上滑 / 下滑 | 下一个 / 上一个视频 |
| 单击 | 暂停 / 播放 |
| 双击 | 全屏切换 |
| 右侧按钮 | PASS / 循环 / 换源 / ❤收藏 |

### 🖥 PC 端

| 快捷键 | 功能 |
|--------|------|
| `Space` | 暂停 / 播放 |
| `N` / `↑` | 下一个 |
| `P` / `↓` | 上一个 |
| `F` | 全屏 |
| `S` | 切换源 |
| `M` | 循环 / 连播 |
| `V` | 静音开关 |
| `←` / `→` | 快退 / 快进 20s |
| `↑` / `↓`（非视频时） | 音量 |
| 滚轮 | 音量调节 |

---

## 🔌 API

| 接口 | 说明 |
|------|------|
| `GET /api/random?source=源名` | 获取随机视频 token |
| `GET /api/play?token=xxx` | 播放视频（本地直接返回 / 远程代理流） |
| `GET /api/sources` | 列出所有源及统计信息 |

---

## 🛠 技术栈

- **后端** — Python / FastAPI / uvicorn / httpx / PyYAML
- **转码** — ffmpeg（仅非 H.264 视频触发实时转码）
- **前端** — 纯 HTML / CSS / JS，零框架
- **CI/CD** — GitHub Actions → Docker Hub + GHCR 多架构推送

---

## 📄 License

[MIT](./LICENSE)
