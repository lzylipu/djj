# DJJ - Random Video Player

[![Docker](https://img.shields.io/docker/pulls/lzylipu/djj)](https://hub.docker.com/r/lzylipu/djj)

Random video player with TikTok-like mobile UI and desktop sidebar. Self-hosted, zero dependencies.

## Features

- **Adaptive UI**: Mobile (swipe gestures) or PC (keyboard + sidebar), auto-detected
- **Simplified config**: Just `source_name: /path` or `source_name: https://...`
- **Local + Remote**: Mount local video dirs or connect to remote APIs
- **Privacy**: HMAC-signed tokens, no public file paths exposed
- **Docker one-click**: Config auto-generated on first run

## Quick Start

```bash
docker run -d --name djj -p 8080:8080   -v djj-data:/data   -v /your/videos:/videos:ro   lzylipu/djj:latest
```

Open `http://localhost:8080` - done. Config auto-generated at `/data/config.yaml`.

## Add Video Sources

Edit `/data/config.yaml` inside the container, then restart:

```yaml
server:
  port: 8080
  secret: change-me-to-random-string

sources:
  默认: /videos           # /开头 = 本地目录
  舞蹈: /videos/舞蹈       # 自动识别为local
  远程: https://example.com/api/random  # http开头 = 远程API
```

**Rules**: `/` prefix = local path, `http` prefix = remote API URL. No type field needed.

```bash
docker exec djj vi /data/config.yaml
docker restart djj
```

## Docker Compose

```bash
cp .env.example .env   # fill in values
docker compose up -d
```

Mount video directories as read-only:

```yaml
volumes:
  - djj-data:/data
  - /path/to/dance:/videos/舞蹈:ro
```

## Controls

### Mobile
- Swipe up/down: next/prev video
- Swipe left/right: hide/show text
- Single tap: pause/resume
- Double tap: fullscreen

### Desktop
- `Space`: pause | `N` / `Up`: next | `P` / `Down`: prev
- `F`: fullscreen | `S`: switch source | `M`: loop mode

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/random?source=name` | Get random video token |
| `GET /api/play?token=xxx` | Stream video |
| `GET /api/sources` | List sources and stats |

Remote API should return: `{"video_url": "...", "name": "..."}`

## License

[MIT](./LICENSE)
