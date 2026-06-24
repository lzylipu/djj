# DJJ 🎬 Random Short Video Player

[![Docker](https://img.shields.io/docker/pulls/lzylipu/djj)](https://hub.docker.com/r/lzylipu/djj)
[![License](https://img.shields.io/github/license/lzylipu/djj)](./LICENSE)

Self-hosted, zero-config, PC/mobile adaptive random video player. Local mounts + remote API mix, auto-transcoding, HMAC-signed secure playback.

**English | [中文](./README.zh-CN.md)**

---

## ✨ Features

- 🎯 **One-Click Deploy** — Docker image `lzylipu/djj:latest`, up in 30 seconds
- 📱 **Adaptive UI** — Single frontend adapts to mobile full-screen gestures & PC keyboard shortcuts
- 🔀 **Multi-Source** — Local directory mounts + remote APIs (302/JSON/MP4/HTML auto-detected)
- 🔒 **Secure Playback** — HMAC-signed tokens, real file paths never exposed
- 🔄 **Smart Transcoding** — Non-H.264 videos auto-transcoded via ffmpeg in real-time
- 🐙 **Multi-Arch** — Supports `linux/amd64` + `linux/arm64`

---

## 🚀 Quick Start

```bash
docker run -d --name djj \
  -p 8080:8080 \
  -v djj-data:/data \
  -v /your/video/dir:/videos:ro \
  -e API_SECRET=replace-with-random-secret \
  lzylipu/djj:latest
```

Open `http://<IP>:8080` — auto-adapts to mobile and desktop.

> Config file `/data/config.yaml` is auto-generated on first start. Edit and restart to apply.

---

## 📋 Deployment

### Docker Compose (Recommended)

```bash
cp .env.example .env    # Fill in API_SECRET
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
  -v /path/to/djj/data:/data \
  -v /path/to/videos:/videos:ro \
  lzylipu/djj:latest
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_SECRET` | ⚠️ Must change | HMAC signing key. Generate with `openssl rand -hex 16` |
| `PORT` | `8080` | Server port |
| `TZ` | — | Timezone, e.g. `Asia/Shanghai` |
| `DJJ_DATA` | `/data` | Config directory (contains `config.yaml`) |

### Volume Mounts

| Mount | Description |
|-------|-------------|
| `/data` | Config persistence (`config.yaml` auto-generated here) |
| `/videos` | Local video directory (recommend `:ro` for read-only) |

> Mount sub-directories for multiple local sources: `-v /path/to/dance:/videos/dance:ro`

---

## 🎛 Configuration

Edit `/data/config.yaml`, then restart the container to apply:

```yaml
server:
  port: 8080
  secret: change-me-to-random-string

sources:
  # --- Local directories ---
  Default: /videos
  # Dance: /videos/dance
  # Funny: /videos/funny

  # --- Remote sources (no API key needed, auto-detected) ---
  Girls: https://tmini.net/api/meinv?mp4=json&r=
  Gentleman: https://v.nrzj.vip/video.php
  Random: https://api.yujn.cn/api/zzxjj.php
```

### Remote Source Types (Auto-Detected)

| Type | Detection | Example |
|------|-----------|---------|
| 302 Redirect | `Location` header points to mp4 | `v.nrzj.vip` |
| JSON API | Returns `{url:...}` / `{video_url:...}` / `{data:{link:...}}` | `tmini.net` |
| Direct MP4 Stream | Returns `video/*` content | `api.yujn.cn` |
| HTML Page | Extracts `<video src="...">` | `tucdn.wpon.cn` |

---

## 🎮 Controls

### 📱 Mobile

| Gesture | Action |
|---------|--------|
| Swipe up / down | Next / Previous video |
| Single tap | Pause / Play |
| Double tap | Toggle fullscreen |
| Right-side buttons | PASS / Loop / Switch source / ❤Favorite |

### 🖥 Desktop

| Shortcut | Action |
|----------|--------|
| `Space` | Pause / Play |
| `N` / `↑` | Next video |
| `P` / `↓` | Previous video |
| `F` | Fullscreen |
| `S` | Switch source |
| `M` | Toggle loop / continuous play |
| `V` | Mute toggle |
| `←` / `→` | Seek back / forward 20s |
| `↑` / `↓` (outside video) | Volume |
| Scroll wheel | Volume adjustment |

---

## 🔌 API

| Endpoint | Description |
|----------|-------------|
| `GET /api/random?source=name` | Get a random video token |
| `GET /api/play?token=xxx` | Play video (local file or remote proxy stream) |
| `GET /api/sources` | List all sources with stats |

---

## 🛠 Tech Stack

- **Backend** — Python / FastAPI / uvicorn / httpx / PyYAML
- **Transcoding** — ffmpeg (real-time, only for non-H.264 videos)
- **Frontend** — Vanilla HTML / CSS / JS, zero frameworks
- **CI/CD** — GitHub Actions → Docker Hub + GHCR multi-arch push

---

## 📄 License

[MIT](./LICENSE)
