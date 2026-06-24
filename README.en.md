<div align="center">

# 🎬 DJJ — Random Short Video Player

**🎨 TikTok-Style · 📱 PC/Mobile Adaptive · 🔒 Secure Playback · 🐳 One-Click Deploy**

[![Docker Pulls](https://img.shields.io/docker/pulls/lzylipu/djj?style=flat-square&logo=docker&color=%230db7ed)](https://hub.docker.com/r/lzylipu/djj)
[![GitHub License](https://img.shields.io/github/license/lzylipu/djj?style=flat-square)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Arch-amd64%20%7C%20arm64-blue?style=flat-square&logo=linux&logoColor=white)]()

**English | [中文](./README.md)**

</div>

---

> 🎉 Self-hosted, zero-config, random short video player! Local mounts + remote API mix, HMAC-signed secure playback, auto-transcoding for non-H.264 videos, mobile full-screen gestures & PC keyboard shortcuts — one Docker command, up in 30 seconds 🚀

---

## 🌟 Highlights

| 🎯 | Highlight |
|:--:|-----------|
| 🐳 | **One-Click Deploy** — Docker image `lzylipu/djj:latest`, up in 30 seconds |
| 📱 | **Adaptive UI** — TikTok-style interactions, mobile full-screen gestures & PC keyboard shortcuts |
| 🔀 | **Multi-Source** — Local directory mounts + remote APIs (302/JSON/MP4/HTML auto-detected) |
| 🔒 | **Secure Playback** — HMAC-SHA256 signed tokens, real file paths never exposed |
| 🔄 | **Smart Transcoding** — Non-H.264 videos auto-transcoded via ffmpeg in real-time |
| 🐙 | **Multi-Arch** — Supports `linux/amd64` + `linux/arm64` |
| 🎨 | **Zero-Framework Frontend** — Vanilla HTML/CSS/JS, lightweight and fast |

> 📌 Supported video formats: `.mp4` / `.avi` / `.mkv` / `.mov` / `.webm` / `.flv`

---

## 🚀 Quick Start

```bash
docker run -d --name djj \
  -p 8080:8080 \
  -v djj-data:/data \
  -v /your/video/directory:/videos:ro \
  -e API_SECRET=*** \
  lzylipu/djj:latest
```

Open `http://<IP>:8080` 🎉 Auto-adapts to mobile and desktop!

> 💡 Config file `/data/config.yaml` is auto-generated on first start. Edit and restart to apply.

---

## 📋 Deployment

### 🐳 Option 1: Docker Compose (✅ Recommended)

```bash
# 1️⃣ Clone the repo & configure environment
git clone https://github.com/lzylipu/djj.git
cd djj
cp .env.example .env          # Fill in API_SECRET

# 2️⃣ Start the service
docker compose up -d
```

<details>
<summary>📝 View docker-compose.yml</summary>

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
      - API_SECRET=***    # ⚠️ Must change
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

### 🐳 Option 2: Docker Run

```bash
docker run -d \
  --name djj \
  --restart unless-stopped \
  --log-opt max-size=10m --log-opt max-file=3 \
  -e TZ=Asia/Shanghai \
  -e API_SECRET=*** \
  -p 8080:8080 \
  -v /path/to/djj/data:/data \
  -v /path/to/videos:/videos:ro \
  lzylipu/djj:latest
```

### ⚙️ Environment Variables

| Variable | Default | Description |
|:---------|:--------|:------------|
| `API_SECRET` | ⚠️ **Must change** | HMAC signing key. Generate with `openssl rand -hex 16` |
| `PORT` | `8080` | Server listen port |
| `TZ` | — | Timezone, e.g. `Asia/Shanghai` |
| `DJJ_DATA` | `/data` | Config directory (contains `config.yaml`) |

### 📂 Volume Mounts

| Mount Point | Description |
|:------------|:------------|
| `/data` | 🗄️ Config persistence (`config.yaml` auto-generated here) |
| `/videos` | 🎬 Local video directory (recommend `:ro` read-only) |

> 💡 **Multiple local directories** can be mounted as sub-directories: `-v /path/to/dance:/videos/dance:ro`

---

## 🎛 Configuration

Edit `/data/config.yaml`, then **restart the container** to apply:

```yaml
server:
  port: 8080
  secret: change-me-to-random-string   # ⚠️ Equivalent to API_SECRET env var

# Video sources: Source Name: Path or URL
# / prefix = local directory (auto-scans sub-directories)
# http prefix = remote API (auto-detect type)
sources:
  # --- 📁 Local directories (uncomment to enable) ---
  Default: /videos
  # Dance: /videos/dance
  # Funny: /videos/funny

  # --- 🌐 Remote sources (no API key needed, auto-detected) ---
  Girls: https://tmini.net/api/meinv?mp4=json&r=
  Gentleman: https://v.nrzj.vip/video.php
  Random: https://api.yujn.cn/api/zzxjj.php
  HotDance: https://tucdn.wpon.cn/api-girl/index.php?type=video
```

> 💡 **Environment variables take priority over config file**: `API_SECRET` env var overrides `secret` in `config.yaml`.

### 🌐 Remote Source Types (Auto-Detected)

| Type | Detection Method | Example |
|:-----|:-----------------|:--------|
| 🔀 302 Redirect | `Location` header points to mp4 | `v.nrzj.vip` |
| 📦 JSON API | Returns `{url:...}` / `{video_url:...}` / `{data:{link:...}}` | `tmini.net` |
| 🎥 Direct MP4 Stream | Returns `video/*` content | `api.yujn.cn` |
| 📄 HTML Page | Extracts `<video src="...">` | `tucdn.wpon.cn` |

---

## 🎮 Controls

### 📱 Mobile Gestures

| Gesture | Action |
|:--------|:-------|
| 👆 Swipe up | ⏭ Next video |
| 👇 Swipe down | ⏮ Previous video |
| 👆 Single tap | ⏯ Pause / Play |
| 👆👆 Double tap | 🔲 Toggle fullscreen |
| ➡️ Right-side buttons | 🚫 PASS / 🔁 Loop / 🔀 Switch source / ❤️ Favorite |

### 🖥 Desktop Shortcuts

| Shortcut | Action | Shortcut | Action |
|:---------|:-------|:---------|:-------|
| `Space` | ⏯ Pause/Play | `S` | 🔀 Switch source |
| `N` / `↑` | ⏭ Next video | `M` | 🔁 Toggle loop/continuous |
| `P` / `↓` | ⏮ Previous video | `V` | 🔇 Mute toggle |
| `F` | 🔲 Fullscreen | `←` / `→` | ⏪/⏩ Seek back/forward 20s |
| `↑` / `↓` _(outside video)_ | 🔊 Volume | 🖱 Scroll wheel | 🔊 Volume adjustment |

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| [`/api/random?source=name`](./api/server.py) | `GET` | 🎲 Get a random video token |
| [`/api/play?token=xxx`](./api/server.py) | `GET` | ▶️ Play video (local direct / remote proxy stream) |
| [`/api/sources`](./api/server.py) | `GET` | 📊 List all sources with stats |

> 🔐 All playback links use HMAC-SHA256 signing. Tokens are valid for 24 hours. Real file paths are never exposed.

---

## 📁 Project Structure

```
djj/
├── 📂 api/                        # Backend Python module
│   ├── 🔐 __init__.py             # Module init
│   ├── 🔐 auth.py                 # HMAC signing & token management
│   ├── ⚙️  config.py              # Config loader (YAML + env vars)
│   ├── 🔍 scanner.py              # Local video scanner & indexer
│   └── 🌐 server.py              # FastAPI main app (routes/transcode/proxy)
├── 📂 web/                        # Frontend static assets
│   ├── 📄 index.html              # Main page (TikTok-style UI)
│   ├── 📂 css/
│   │   ├── 🎨 style.css           # Stylesheet
│   │   └── 🔢 DS-DIGIT.TTF       # Digital font
│   └── 📂 img/
│       ├── 🖼️ logo.png            # Logo
│       ├── 🖼️ favicon.ico         # Favicon
│       ├── 💖 love.png / love1.png / loves.png  # Favorite animation
│       ├── 🌄 bg.jpg / bg.gif     # Background images
│       └── 📱 ewm.png             # QR code
├── 🐳 Dockerfile                  # Docker image build
├── 🐙 docker-compose.yml         # Docker Compose orchestration
├── 📋 config.example.yaml         # Config file example
├── 🔑 .env.example                # Environment variables example
├── 📦 pyproject.toml              # Python project config (v2.3.0)
├── 🙈 .gitignore                  # Git ignore rules
├── 🙈 .dockerignore               # Docker ignore rules
├── 📂 .github/workflows/         # GitHub Actions CI/CD
│   └── 🔄 docker.yml              # Multi-arch image build & push
├── 📜 LICENSE                     # MIT License
├── 📖 README.md                   # Chinese documentation
└── 📖 README.en.md                # English documentation (this file)
```

---

## 🛠 Tech Stack

| Layer | Technology |
|:------|:-----------|
| ⚙️ **Backend** | Python 3.12 / [FastAPI](https://fastapi.tiangolo.com/) / [uvicorn](https://www.uvicorn.org/) / [httpx](https://www.python-httpx.org/) / [PyYAML](https://pyyaml.org/) |
| 🔄 **Transcoding** | [ffmpeg](https://ffmpeg.org/) — real-time, only triggered for non-H.264 videos (libx264 veryfast preset) |
| 🎨 **Frontend** | Vanilla HTML / CSS / JavaScript, zero frameworks |
| 🐳 **Deployment** | Docker + Docker Compose, multi-arch images (amd64 + arm64) |
| 🔄 **CI/CD** | GitHub Actions → Docker Hub + GHCR multi-arch auto-push |

---

## ❓ FAQ

<details>
<summary>🔐 How to generate a secure API_SECRET?</summary>

```bash
# Recommended method
openssl rand -hex 16

# Or using Python
python3 -c "import secrets; print(secrets.token_hex(16))"
```
</details>

<details>
<summary>📁 How to mount multiple local video directories?</summary>

Mount sub-directories in `docker-compose.yml` or `docker run`:

```bash
# Docker Run
-v /path/to/dance:/videos/dance:ro
-v /path/to/funny:/videos/funny:ro

# Then add sources in config.yaml
sources:
  Dance: /videos/dance
  Funny: /videos/funny
```
</details>

<details>
<summary>🔄 Video won't play — what to do?</summary>

1. Check if the video format is supported (mp4/avi/mkv/mov/webm/flv)
2. Non-H.264 encoded videos are auto-transcoded — ensure ffmpeg is available in the container
3. If remote sources are unreachable, check container DNS and network settings
4. View container logs: `docker logs djj`
</details>

<details>
<summary>⚙️ How to apply config changes?</summary>

After editing `/data/config.yaml`, restart the container:

```bash
docker restart djj
```
</details>

---

## 🤝 Acknowledgements

- Inspired by: [JMWpower/xiaojiejie](https://github.com/JMWpower/xiaojiejie)
- All remote video API providers

---

## 📄 License

This project is licensed under the [MIT License](./LICENSE).

Copyright (c) 2024 lzylipu

<div align="center">

**⭐ If this project helps you, give it a Star! ⭐**

</div>
